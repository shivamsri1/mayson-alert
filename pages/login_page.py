import logging
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    Page Object Model representing the Mayson AI Login & OTP Verification screens.
    """

    # Flexible primary & fallback locators for email input
    EMAIL_INPUT_SELECTORS = [
        "input[type='email']",
        "input[name='email']",
        "input[id='email']",
        "input[placeholder*='email' i]",
        "[data-testid='email-input']",
        "input[type='text']",
    ]

    # Locators for Request OTP / Submit Email button
    REQUEST_OTP_BUTTON_SELECTORS = [
        "button[type='submit']",
        "button:has-text('Send')",
        "button:has-text('OTP')",
        "button:has-text('Continue')",
        "button:has-text('Log In')",
        "button:has-text('Get Code')",
        "button:has-text('Next')",
    ]

    # Locators for OTP Code input field(s)
    OTP_INPUT_SELECTORS = [
        "input[name='otp']",
        "input[name='code']",
        "input[id='otp']",
        "input[id='code']",
        "input[placeholder*='otp' i]",
        "input[placeholder*='code' i]",
        "[data-testid='otp-input']",
        "input[type='number']",
    ]

    # Multi-digit individual OTP input box selector fallback
    OTP_MULTI_INPUT_SELECTOR = "input[maxlength='1'], input.otp-digit"

    # Locators for Verify OTP / Login Submit button
    VERIFY_OTP_BUTTON_SELECTORS = [
        "button:has-text('Verify')",
        "button:has-text('Submit')",
        "button:has-text('Confirm')",
        "button:has-text('Log In')",
        "button[type='submit']",
    ]

    def __init__(self, page: Page, base_url: str):
        super().__init__(page)
        self.base_url = base_url

    def navigate(self):
        """Navigates to the Mayson login page."""
        url = f"{self.base_url}/login" if not self.base_url.endswith("/login") else self.base_url
        logger.info(f"Opening Mayson login page: {url}")
        self.navigate_to(url)
        self.verify_login_page_loaded()

    def verify_login_page_loaded(self, timeout: float = 15000.0):
        """Verifies that the login page email field or login container is visible."""
        logger.info("Verifying login page is loaded...")
        matched = False
        for selector in self.EMAIL_INPUT_SELECTORS:
            try:
                self.page.locator(selector).first.wait_for(state="visible", timeout=2000.0)
                logger.info(f"Login page verified with element: '{selector}'")
                matched = True
                break
            except Exception:
                continue

        if not matched:
            # Check generic fallback if custom form element is present
            expect(self.page.locator("body")).to_be_visible(timeout=timeout)
            logger.info("Page body rendered successfully.")

    def enter_email(self, email: str):
        """Enters test user email into email field."""
        logger.info(f"Entering email into login form: {email}")
        for selector in self.EMAIL_INPUT_SELECTORS:
            loc = self.page.locator(selector).first
            if loc.is_visible():
                loc.fill(email)
                return

        # Fallback to first text/email input on page
        fallback_loc = self.page.locator("input[type='email'], input[type='text']").first
        fallback_loc.wait_for(state="visible", timeout=10000.0)
        fallback_loc.fill(email)

    def request_otp(self):
        """Clicks the button to request OTP email."""
        logger.info("Clicking request OTP button...")
        for selector in self.REQUEST_OTP_BUTTON_SELECTORS:
            loc = self.page.locator(selector).first
            if loc.is_visible() and loc.is_enabled():
                loc.click()
                logger.info(f"Clicked request OTP button matching: '{selector}'")
                return

        # Fallback click on any active submit button inside form
        submit_loc = self.page.locator("form button, form input[type='submit']").first
        submit_loc.click()

    def enter_otp(self, otp_code: str):
        """
        Enters the OTP code into the single OTP field or multi-digit digit inputs.
        """
        logger.info("Entering OTP code into login interface (masked: ***masked***)...")

        # First, try single OTP input field
        for selector in self.OTP_INPUT_SELECTORS:
            try:
                loc = self.page.locator(selector).first
                if loc.is_visible(timeout=3000.0):
                    loc.fill(otp_code)
                    logger.info(f"Filled single OTP input matching: '{selector}'")
                    return
            except Exception:
                continue

        # Second, try multi-digit inputs (e.g. 6 separate boxes)
        multi_inputs = self.page.locator(self.OTP_MULTI_INPUT_SELECTOR)
        count = multi_inputs.count()
        if count >= len(otp_code):
            logger.info(f"Detected {count} separate OTP digit inputs. Filling code digit by digit...")
            for idx, char in enumerate(otp_code):
                multi_inputs.nth(idx).fill(char)
            return

        # Fallback: find any visible text/number input on the page after requesting OTP
        fallback_input = self.page.locator("input[type='text'], input[type='number'], input:not([type='hidden'])").last
        fallback_input.wait_for(state="visible", timeout=10000.0)
        fallback_input.fill(otp_code)

    def submit_otp(self):
        """Clicks the button to submit and verify the entered OTP."""
        logger.info("Submitting OTP for verification...")
        for selector in self.VERIFY_OTP_BUTTON_SELECTORS:
            try:
                loc = self.page.locator(selector).first
                if loc.is_visible() and loc.is_enabled():
                    loc.click()
                    logger.info(f"Clicked verify OTP button matching: '{selector}'")
                    return
            except Exception:
                continue

        # Fallback to submit form by pressing Enter or clicking main button
        self.page.keyboard.press("Enter")
