"""
Unit tests for nau.course.certificate.browser_manager.

get_browser()'s launch/reuse/relaunch logic and run_in_browser_thread()'s
thread-dispatch behaviour are tested here with Playwright's sync_playwright()
mocked out, so no real Chromium browser is launched. (Rendering against a
real browser is instead covered by tests/test_certificate_renderer.py.)
"""
import threading
from unittest.mock import MagicMock, patch

import pytest

import nau.course.certificate.browser_manager as browser_manager


@pytest.fixture(autouse=True)
def _reset_module_state():
    """
    Reset browser_manager's process-local globals before and after each test,
    so tests don't leak launched-browser/executor state into each other.
    """
    browser_manager.close_browser()
    browser_manager._playwright = None
    browser_manager._browser = None
    browser_manager._executor = None
    yield
    browser_manager.close_browser()
    browser_manager._playwright = None
    browser_manager._browser = None
    browser_manager._executor = None


def _mock_sync_playwright(mock_browser):
    """Build a mock replacing sync_playwright() that returns mock_browser."""
    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium.launch.return_value = mock_browser
    mock_context_manager = MagicMock()
    mock_context_manager.start.return_value = mock_playwright_instance
    return mock_context_manager


class TestGetBrowser:
    def test_launches_a_browser_on_first_call(self):
        mock_browser = MagicMock(is_connected=MagicMock(return_value=True))
        with patch.object(
            browser_manager, "sync_playwright", return_value=_mock_sync_playwright(mock_browser)
        ) as mock_sync_playwright:
            result = browser_manager.get_browser()

        assert result is mock_browser
        mock_sync_playwright.assert_called_once()

    def test_reuses_the_same_browser_while_connected(self):
        mock_browser = MagicMock(is_connected=MagicMock(return_value=True))
        with patch.object(
            browser_manager, "sync_playwright", return_value=_mock_sync_playwright(mock_browser)
        ) as mock_sync_playwright:
            first = browser_manager.get_browser()
            second = browser_manager.get_browser()

        assert first is second is mock_browser
        # sync_playwright() (and therefore chromium.launch()) must only be
        # called once: the second get_browser() call should just reuse it.
        mock_sync_playwright.assert_called_once()

    def test_relaunches_a_new_browser_when_the_old_one_disconnected(self):
        old_browser = MagicMock(is_connected=MagicMock(return_value=True))
        new_browser = MagicMock(is_connected=MagicMock(return_value=True))

        with patch.object(
            browser_manager, "sync_playwright", return_value=_mock_sync_playwright(old_browser)
        ):
            first = browser_manager.get_browser()

        assert first is old_browser

        # Simulate the browser process dying/disconnecting between requests.
        old_browser.is_connected.return_value = False

        with patch.object(
            browser_manager, "sync_playwright", return_value=_mock_sync_playwright(new_browser)
        ) as mock_sync_playwright:
            second = browser_manager.get_browser()

        assert second is new_browser
        assert second is not first
        # The stale browser must be closed before a new one is launched.
        old_browser.close.assert_called_once()
        mock_sync_playwright.assert_called_once()


class TestRunInBrowserThread:
    def test_runs_the_callable_and_returns_its_result(self):
        result = browser_manager.run_in_browser_thread(lambda x, y: x + y, 2, 3)

        assert result == 5

    def test_reraises_exceptions_from_the_callable(self):
        def _boom():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            browser_manager.run_in_browser_thread(_boom)

    def test_always_runs_on_the_same_dedicated_thread(self):
        thread_ids = {
            browser_manager.run_in_browser_thread(threading.get_ident) for _ in range(5)
        }

        assert len(thread_ids) == 1
        # And it must not be the thread running the test itself.
        assert thread_ids != {threading.get_ident()}


class TestCloseBrowser:
    def test_is_a_no_op_when_no_browser_was_ever_launched(self):
        # Must not raise even though get_browser() was never called.
        browser_manager.close_browser()

    def test_closes_the_launched_browser_and_stops_playwright(self):
        mock_browser = MagicMock(is_connected=MagicMock(return_value=True))
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_context_manager = MagicMock()
        mock_context_manager.start.return_value = mock_playwright_instance

        with patch.object(browser_manager, "sync_playwright", return_value=mock_context_manager):
            # get_browser() must go through run_in_browser_thread (per its
            # documented contract) so the executor -- which close_browser()
            # relies on to know a browser might exist -- actually gets created.
            browser_manager.run_in_browser_thread(browser_manager.get_browser)
            browser_manager.close_browser()

        mock_browser.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()
