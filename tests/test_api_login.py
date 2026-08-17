import uuid
import time
import logging
import requests
import pytest
from utils.config import Config
from utils.email_otp import EmailOTPFetcher

logger = logging.getLogger(__name__)


def test_mayson_api_otp_login_flow():
    """
    API Synthetic Monitoring Test: Direct Mayson API Login + OTP Verification.
    
    Validates API endpoints:
    1. POST /sigma/api/v2/auth/otp/email/login -> Requests OTP email.
    2. IMAP Poll -> Retrieves OTP code.
    3. POST /sigma/api/v1/login/otp/verify -> Verifies OTP code.
    """
    logger.info("Starting Mayson API Synthetic Login Monitoring Test...")
    config = Config.validate()
    test_start_time = time.time()

    api_base_url = "https://cc1fbde45ead-in-south-01.mayson.dev"
    otp_login_endpoint = f"{api_base_url}/sigma/api/v2/auth/otp/email/login"
    otp_verify_endpoint = f"{api_base_url}/sigma/api/v1/login/otp/verify"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://mayson.dev/",
        "M-Current-ip": "14.99.33.46",
    }

    # Step 1: Request OTP via API
    headers["Idempotency-Key"] = str(uuid.uuid4())
    logger.info(f"Posting OTP request to API: {otp_login_endpoint}")
    resp_login = requests.post(
        otp_login_endpoint,
        headers=headers,
        json={"email_id": config.MAYSON_USERNAME},
        timeout=15,
    )

    logger.info(f"OTP Request API response status: {resp_login.status_code}")
    assert resp_login.status_code in (200, 201, 202), f"API OTP request failed with status {resp_login.status_code}: {resp_login.text}"

    # Step 2: Retrieve OTP from Mailbox via IMAP
    otp_fetcher = EmailOTPFetcher(config)
    otp_code = otp_fetcher.fetch_latest_otp(
        sent_after_timestamp=test_start_time,
        timeout=60,
        poll_interval=5,
    )
    assert otp_code, "Failed to retrieve OTP code from mailbox."

    # Step 3: Verify OTP via API
    headers["Idempotency-Key"] = str(uuid.uuid4())
    logger.info(f"Posting OTP verification to API: {otp_verify_endpoint}")
    resp_verify = requests.post(
        otp_verify_endpoint,
        headers=headers,
        json={"email_id": config.MAYSON_USERNAME, "otp": otp_code},
        timeout=15,
    )

    logger.info(f"OTP Verify API response status: {resp_verify.status_code}")
    assert resp_verify.status_code in (200, 201), f"API OTP verification failed with status {resp_verify.status_code}: {resp_verify.text}"

    logger.info("========================================")
    logger.info("      API LOGIN MONITOR → PASS          ")
    logger.info("========================================")
