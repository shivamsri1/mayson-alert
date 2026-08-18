import time
from datetime import datetime, timezone
from typing import Dict, Tuple

import pytest

from api.api_client import APIClient
from api.auth_api import AuthAPI
from utils.config import Config
from utils.email_alert import EmailAlertManager
from utils.email_otp import EmailOTPFetcher
from utils.logger import logger


def run_login_monitoring_flow() -> Tuple[bool, Dict[str, str], float]:
    """Executes the full synthetic monitoring flow once and returns (success, step_statuses, duration)."""
    start_time = datetime.now(timezone.utc)
    flow_start_tick = time.time()

    step_statuses = {
        "Request OTP API": "FAIL",
        "OTP Email": "FAIL",
        "Verify OTP API": "FAIL",
    }

    # Validate target email configuration
    Config.validate_api_config()
    email_id = Config.MAYSON_EMAIL

    logger.info("==================================================")
    logger.info(f"Starting Mayson Login Monitoring Flow for email: {email_id}")
    logger.info("==================================================")

    # Initialize Clients
    api_client = APIClient(base_url=Config.MAYSON_BASE_URL)
    auth_api = AuthAPI(client=api_client)

    # ------------------------------------------------------------------
    # Step 1: Request OTP API
    # ------------------------------------------------------------------
    logger.info("--- Step 1: Request OTP API ---")
    req_otp_res = auth_api.request_otp(email_id=email_id)

    if not req_otp_res.is_success:
        msg = f"Request OTP API failed with HTTP {req_otp_res.status_code}. Response: {req_otp_res.text}"
        logger.error(msg)
        raise AssertionError(msg)

    # Validate Response format
    logger.info(f"Request OTP API succeeded in {req_otp_res.elapsed_sec}s with status {req_otp_res.status_code}")
    step_statuses["Request OTP API"] = "PASS"

    # ------------------------------------------------------------------
    # Step 2: Read OTP Email
    # ------------------------------------------------------------------
    logger.info("--- Step 2: Read OTP Email via IMAP ---")
    otp_fetcher = EmailOTPFetcher()
    otp_code = otp_fetcher.fetch_latest_otp(start_timestamp=start_time)

    if not otp_code:
        msg = "Failed to extract valid OTP code from received email."
        logger.error(msg)
        raise AssertionError(msg)

    logger.info("OTP Email received and OTP extracted successfully.")
    step_statuses["OTP Email"] = "PASS"

    # ------------------------------------------------------------------
    # Step 3: Verify OTP API
    # ------------------------------------------------------------------
    logger.info("--- Step 3: Verify OTP API ---")
    verify_res = auth_api.verify_otp(email_id=email_id, otp=otp_code)

    if not verify_res.is_success:
        msg = f"Verify OTP API failed with HTTP {verify_res.status_code}. Response: {verify_res.text}"
        logger.error(msg)
        raise AssertionError(msg)

    logger.info(f"Verify OTP API succeeded in {verify_res.elapsed_sec}s with status {verify_res.status_code}")
    step_statuses["Verify OTP API"] = "PASS"

    total_duration = round(time.time() - flow_start_tick, 2)
    logger.info("==================================================")
    logger.info(f"Mayson Login Monitoring Flow Completed successfully in {total_duration}s")
    logger.info("==================================================")

    return True, step_statuses, total_duration


def test_mayson_login_flow():
    """Pytest test case for Mayson Login OTP Monitoring with single-retry protection."""
    alert_manager = EmailAlertManager()
    step_statuses = {
        "Request OTP API": "FAIL",
        "OTP Email": "FAIL",
        "Verify OTP API": "FAIL",
    }
    total_duration = 0.0

    # First Attempt
    try:
        success, step_statuses, total_duration = run_login_monitoring_flow()
        if success:
            alert_manager.send_recovery_alert(elapsed_time_sec=total_duration)
            return
    except Exception as first_err:
        logger.warning(f"Monitoring attempt 1 encountered failure: {first_err}")
        logger.info("Retrying monitoring flow once before declaring incident...")
        time.sleep(5)

    # Second Attempt (Retry once on failure)
    try:
        success, step_statuses, total_duration = run_login_monitoring_flow()
        if success:
            logger.info("Monitoring flow succeeded on retry attempt.")
            alert_manager.send_recovery_alert(elapsed_time_sec=total_duration)
            return
    except Exception as retry_err:
        logger.error(f"Monitoring retry attempt also failed: {retry_err}")
        # Send failure alert (with state check to avoid spam)
        alert_manager.send_failure_alert(
            step_statuses=step_statuses,
            elapsed_time_sec=total_duration,
        )
        pytest.fail(f"Mayson Login OTP Monitoring failed after retry attempt. Error: {retry_err}")
