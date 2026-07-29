"""
Manages a single, lazily-initialized Playwright Chromium browser instance per
process.

This app is served by uWSGI with ``lazy-apps = false`` (see ``uwsgi.ini``),
meaning the application module is imported once in the uWSGI master process
before it forks worker processes. A Playwright/Chromium connection created at
import time in the master would be shared (and broken) across all forked
workers, since the underlying OS pipes/sockets don't survive a fork cleanly.

To avoid that, the browser is NOT created at import time. Instead it is
created lazily on the first render request handled by each worker process,
and then reused for all subsequent requests in that same worker to avoid
paying the Chromium startup cost (roughly 300-800ms) on every request.

A new browser context (and page) is still created per request for isolation
between requests, and closed right after use; only the underlying browser
process is kept alive and shared.

Playwright's *sync* API additionally ties the ``Playwright``/``Browser``
objects it returns to the single OS thread that created them: calling into
them from any other thread raises
``greenlet.error: cannot switch to a different thread``. Since ``get_browser``
deliberately keeps one ``Browser`` alive and reused across requests, every
caller -- regardless of which thread the WSGI server dispatches a given
request to (e.g. uWSGI/gunicorn worker threads, or Flask's threaded dev
server) -- must actually touch that ``Browser`` (and any context/page created
from it) from the same dedicated thread. :func:`run_in_browser_thread` is the
single entry point that guarantees this: it runs the given callable on a
lazily-created, single-worker background thread that owns the Playwright
connection for the lifetime of the process.
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright, Browser, Playwright

logger = logging.getLogger(__name__)

# Process-local state. Each uWSGI worker process gets its own copy of these
# module-level globals after fork, so this is safe without cross-process locking.
_playwright: Playwright = None
_browser: Browser = None
_lock = threading.Lock()

# Single-worker executor: the dedicated OS thread that owns the Playwright
# connection/browser for this process. All Playwright calls MUST go through
# ``run_in_browser_thread`` so they always run on this same thread, no matter
# which thread the WSGI server used to handle the incoming request.
_executor: ThreadPoolExecutor = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor

    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="playwright-browser"
                )
    return _executor


def run_in_browser_thread(fn, *args, **kwargs):
    """
    Run ``fn(*args, **kwargs)`` on the single dedicated thread that owns the
    Playwright/Chromium connection for this process, blocking until it
    completes, and return its result (re-raising any exception it raised).

    Any code that calls :func:`get_browser` or otherwise touches Playwright
    objects (creating/using browser contexts, pages, etc.) must do so via
    this function rather than being called directly from a request-handling
    thread, to avoid the cross-thread ``greenlet.error`` described in this
    module's docstring.
    """
    return _get_executor().submit(fn, *args, **kwargs).result()


def get_browser() -> Browser:
    """
    Return a live Chromium ``Browser`` instance for the current process,
    creating (or recreating, if the previous one died/disconnected) it on
    demand.

    Must only be called from the dedicated thread managed by
    :func:`run_in_browser_thread`.
    """
    global _playwright, _browser

    with _lock:
        if _browser is not None and _browser.is_connected():
            return _browser

        if _browser is not None:
            logger.warning("Chromium browser was disconnected, relaunching it")
            _close_locked()

        logger.info("Launching Chromium browser for this worker process")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch()
        return _browser


def _close_locked():
    """Close the current browser/playwright instances. Must hold ``_lock``."""
    global _playwright, _browser

    if _browser is not None:
        try:
            _browser.close()
        except Exception:
            logger.warning("Error closing Chromium browser", exc_info=True)
        _browser = None

    if _playwright is not None:
        try:
            _playwright.stop()
        except Exception:
            logger.warning("Error stopping Playwright", exc_info=True)
        _playwright = None


def close_browser():
    """
    Explicitly close the browser and stop Playwright for the current process.
    Mainly useful for tests and graceful worker shutdown.

    Runs on the dedicated browser thread like every other Playwright call, to
    close it from the same thread that created it.
    """
    if _executor is not None:
        run_in_browser_thread(_close_with_lock)


def _close_with_lock():
    with _lock:
        _close_locked()
