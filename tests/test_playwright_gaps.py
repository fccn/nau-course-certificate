"""
Covers a handful of Playwright-rendering edge cases not already exercised by
test_certificate_renderer.py / test_browser_manager.py:

- extra HTTP headers (e.g. the LMS auth header) are actually sent to the server;
- a navigation failure (unreachable URL) surfaces as an exception rather than
  hanging or silently returning empty output;
- a `zoom` meta value of "0" is treated the same as "no zoom" (falsy check in
  render_image), not as a zero-sized/broken output;
- concurrent get_browser() calls from multiple request threads don't race and
  launch more than one Chromium browser;
- rendering triggered from a thread other than the main one still works,
  regression-testing the cross-thread `greenlet.error` this module's design
  avoids (see browser_manager.py's docstring).
"""
import io
import threading

import pytest
from playwright.sync_api import Error as PlaywrightError
from PIL import Image

from nau.course.certificate.browser_manager import (
    close_browser,
    get_browser,
    run_in_browser_thread,
)
from nau.course.certificate.certificate_renderer import render_image, render_pdf

_FIXTURE_URL = None  # set by the `_http_server` fixture per test


@pytest.fixture(autouse=True)
def _close_browser_after_each_test():
    yield
    close_browser()


@pytest.fixture
def http_server():
    """
    Serve tests/fixtures over real HTTP (not file://) on 127.0.0.1, on a
    background thread, so tests can inspect the headers Playwright actually
    sent -- `file://` URLs never receive custom HTTP headers, so the header
    propagation test needs a real server.
    """
    import functools
    import http.server
    import pathlib

    fixtures_dir = pathlib.Path(__file__).parent / "fixtures"
    received_headers = {}

    class _CapturingHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            received_headers.clear()
            received_headers.update(dict(self.headers.items()))
            super().do_GET()

        def log_message(self, format, *args):
            pass  # keep test output clean

    handler = functools.partial(_CapturingHandler, directory=str(fixtures_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}/sample_certificate.html", received_headers
    finally:
        server.shutdown()
        thread.join(timeout=5)


class TestHttpHeaderPropagation:
    def test_custom_headers_are_sent_to_the_server(self, http_server):
        url, received_headers = http_server

        render_pdf(
            url,
            {"custom-header": [("Authorization", "Bearer test-token"), ("X-Custom", "value")]},
        )

        assert received_headers.get("Authorization") == "Bearer test-token"
        assert received_headers.get("X-Custom") == "value"


class TestNavigationFailure:
    def test_unreachable_url_raises_instead_of_hanging_or_returning_empty(self):
        # Port 1 is a reserved/unassigned port, guaranteed to refuse the
        # connection immediately rather than needing to wait for a timeout.
        with pytest.raises(PlaywrightError):
            render_pdf("http://127.0.0.1:1/unreachable", {})


class TestZoomZero:
    def test_zoom_of_zero_is_treated_as_no_zoom(self, http_server):
        url, _ = http_server

        # get_zoom_factor("0") == 0.0, which is falsy, so render_image's
        # `zoom_factor if zoom_factor and zoom_factor != 1.0 else None` check
        # deliberately treats it the same as "no zoom" (device_scale_factor
        # left at Playwright's own default) rather than as an invalid/zero
        # output size. This pins that current behaviour as a regression test.
        default_image = render_image(url, {})
        zoom_zero_image = render_image(url, {"zoom": "0"})

        default_size = Image.open(io.BytesIO(default_image)).size
        zoom_zero_size = Image.open(io.BytesIO(zoom_zero_image)).size
        assert zoom_zero_size == default_size


class TestConcurrentGetBrowser:
    def test_concurrent_calls_do_not_launch_more_than_one_browser(self):
        browsers = []
        barrier = threading.Barrier(5)

        def _call():
            barrier.wait(timeout=5)
            browsers.append(run_in_browser_thread(get_browser))

        threads = [threading.Thread(target=_call) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(browsers) == 5
        # All calls, even when raced from multiple request threads, must
        # observe the very same Browser instance: get_browser()/
        # run_in_browser_thread() together guarantee a single dedicated
        # background thread handles every call, so there's no possibility of
        # launching Chromium twice.
        assert len(set(id(b) for b in browsers)) == 1


class TestRenderingFromANonMainThread:
    def test_render_pdf_works_when_called_from_a_background_thread(self, http_server):
        url, _ = http_server
        result = {}

        def _render():
            try:
                result["pdf_bytes"] = render_pdf(url, {})
            except Exception as exc:  # pragma: no cover - surfaced via assertion below
                result["error"] = exc

        # Calling render_pdf() (and therefore Playwright) from a thread that
        # is neither the test's main thread nor browser_manager's own
        # dedicated thread must not raise `greenlet.error: cannot switch to a
        # different thread` -- run_in_browser_thread() is what protects
        # against that regardless of which thread the caller is on.
        thread = threading.Thread(target=_render)
        thread.start()
        thread.join(timeout=30)

        assert "error" not in result, result.get("error")
        assert result["pdf_bytes"].startswith(b"%PDF-")
