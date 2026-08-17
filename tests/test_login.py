import time
import logging
import pytest
from playwright.sync_api import Page
from utils.config import Config
from utils.email_otp import EmailOTPFetcher
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

logger = logging.getLogger(__name__)


def test_mayson_login_otp_flow(page: Page):
    """
    Synthetic Monitoring Test: Complete Mayson Login + Email OTP Verification Flow.

    Flow:
    1. Load configuration from environment variables.
    2. Open Mayson Base URL & verify Login page.
    3. Enter username email & request OTP.
    4. Poll IMAP mailbox for latest OTP email.
    5. Extract and enter OTP into Mayson form.
    6. Submit OTP verification.
    7. Verify redirect to post-login Dashboard.
    8. Log PASS result upon success.
    """
    logger.info("Starting Mayson Synthetic Login + Email OTP Monitoring Test...")

    # Step 1: Validate environment credentials and configuration
    config = Config.validate()

    # Capture start epoch timestamp for OTP email matching
    test_start_timestamp = time.time()

    login_page = LoginPage(page, config.MAYSON_BASE_URL)
    dashboard_page = DashboardPage(page)
    otp_fetcher = EmailOTPFetcher(config)

    try:
        # Step 2: Open Mayson production URL and verify login page
        logger.info("[STEP 1/7] Opening Mayson base URL and verifying login page...")
        login_page.navigate()

        # Step 3: Enter test email address
        logger.info("[STEP 2/7] Entering test email into login form...")
        login_page.enter_email(config.MAYSON_USERNAME)

        # Step 4: Request OTP
        logger.info("[STEP 3/7] Requesting OTP email...")
        login_page.request_otp()

        # Step 5: Poll mailbox and extract OTP code
        logger.info("[STEP 4/7] Polling IMAP mailbox for incoming OTP email...")
        otp_code = otp_fetcher.fetch_latest_otp(
            sent_after_timestamp=test_start_timestamp,
            timeout=60,
            poll_interval=5,
        )

        assert otp_code, "Failed to retrieve a valid OTP code from mailbox."
        logger.info("OTP retrieval successful. Code extracted safely.")

        # Step 6: Enter OTP code and submit verification
        logger.info("[STEP 5/7] Entering OTP code into Mayson login page...")
        login_page.enter_otp(otp_code)

        logger.info("[STEP 6/7] Submitting OTP verification form...")
        login_page.submit_otp()

        # Step 7: Wait for dashboard and verify successful load
        logger.info("[STEP 7/7] Verifying user reaches Mayson Dashboard...")
        dashboard_page.verify_dashboard(timeout=25000.0)

        # Monitor Success Outcome
        logger.info("========================================")
        logger.info("        LOGIN MONITOR → PASS            ")
        logger.info("========================================")

    except Exception as e:
        logger.error("========================================")
        logger.error("        LOGIN MONITOR → FAIL            ")
        logger.error(f"Reason: {str(e)}")
        logger.error("========================================")
        raise
