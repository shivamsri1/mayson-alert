import logging
from playwright.sync_api import Page, Locator, expect

logger = logging.getLogger(__name__)


class BasePage:
    """Base Page Object class encapsulating common Playwright interactions."""

    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, url: str, timeout: float = 30000.0):
        """Navigates to a given URL and waits for page DOM load."""
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    def find(self, selector_or_locator, timeout: float = 10000.0) -> Locator:
        """Finds element with explicit timeout wait."""
        if isinstance(selector_or_locator, str):
            loc = self.page.locator(selector_or_locator)
        else:
            loc = selector_or_locator
        loc.first.wait_for(state="visible", timeout=timeout)
        return loc

    def fill_input(self, selector: str, value: str, mask_log: bool = False):
        """Fills input field after ensuring visibility."""
        log_val = "***masked***" if mask_log else value
        logger.info(f"Filling input '{selector}' with value '{log_val}'")
        element = self.page.locator(selector).first
        element.wait_for(state="visible")
        element.fill(value)

    def click_element(self, selector: str):
        """Clicks element after ensuring enablement and visibility."""
        logger.info(f"Clicking element '{selector}'")
        element = self.page.locator(selector).first
        element.wait_for(state="visible")
        element.click()

    def get_title(self) -> str:
        """Returns the page title."""
        return self.page.title()
