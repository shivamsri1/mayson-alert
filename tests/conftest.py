import os
import time
import logging
import pytest
from playwright.sync_api import Page, BrowserContext

logger = logging.getLogger(__name__)

# Ensure artifact output directories exist
SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots")
TRACES_DIR = os.path.join(os.getcwd(), "traces")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(TRACES_DIR, exist_ok=True)


@pytest.fixture(autouse=True)
def configure_tracing(context: BrowserContext, request: pytest.Item):
    """
    Enables Playwright tracing for test execution.
    On failure, saves the trace file into traces/ directory.
    """
    test_name = request.node.name
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield

    # Determine if the test failed during call phase
    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

    if failed:
        timestamp = int(time.time())
        trace_path = os.path.join(TRACES_DIR, f"trace_{test_name}_{timestamp}.zip")
        try:
            context.tracing.stop(path=trace_path)
            logger.info(f"Playwright failure trace saved to: {trace_path}")
        except Exception as e:
            logger.error(f"Failed to save Playwright trace: {e}")
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def capture_failure_screenshot(page: Page, request: pytest.Item):
    """
    Captures a screenshot automatically if the test fails.
    """
    yield

    # Check if call phase failed
    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

    if failed:
        timestamp = int(time.time())
        test_name = request.node.name
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"failure_{test_name}_{timestamp}.png")
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Failure screenshot captured and saved to: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to capture failure screenshot: {e}")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook to attach test execution status to test items for fixtures.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
