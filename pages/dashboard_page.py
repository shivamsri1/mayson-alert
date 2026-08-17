import logging
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """
    Page Object Model representing the Mayson AI Post-Login Dashboard.
    """

    DASHBOARD_ELEMENT_SELECTORS = [
        "[data-testid='dashboard']",
        "#dashboard",
        ".dashboard",
        "h1:has-text('Dashboard')",
        "h1:has-text('Welcome')",
        "nav",
        "header",
        ".user-profile",
        ".sidebar",
        "main",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    def is_dashboard_loaded(self, timeout: float = 20000.0) -> bool:
        """
        Verifies if the post-login dashboard has loaded by inspecting page URL and DOM indicators.
        """
        logger.info(f"Waiting for dashboard to load (timeout: {timeout}ms)...")

        # 1. Check URL path
        try:
            self.page.wait_for_url(
                lambda url: any(p in url.lower() for p in ["/dashboard", "/app", "/home", "/projects", "/overview"]),
                timeout=timeout / 2,
            )
            logger.info(f"Dashboard URL navigation confirmed: {self.page.url}")
            return True
        except Exception:
            logger.info("URL check passed timeout limit, falling back to DOM selector verification...")

        # 2. Check for dashboard DOM elements
        for selector in self.DASHBOARD_ELEMENT_SELECTORS:
            try:
                self.page.locator(selector).first.wait_for(state="visible", timeout=3000.0)
                logger.info(f"Dashboard element confirmed visible: '{selector}'")
                return True
            except Exception:
                continue

        return False

    def verify_dashboard(self, timeout: float = 20000.0):
        """
        Asserts that the user has successfully reached the dashboard after login.
        Raises AssertionError if the dashboard is not verified.
        """
        assert self.is_dashboard_loaded(timeout=timeout), (
            f"Dashboard verification failed! Current URL: {self.page.url}"
        )
        logger.info("DASHBOARD VERIFICATION SUCCESSFUL.")
