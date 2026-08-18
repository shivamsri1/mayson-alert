from typing import Optional
from api.api_client import APIClient, APIResponse
from utils.config import Config


class AuthAPI:
    """Mayson Authentication API endpoints."""

    # Endpoints specified in Mayson API documentation
    REQUEST_OTP_ENDPOINT = "/sigma/api/v2/auth/otp/email/login"
    VERIFY_OTP_ENDPOINT = "/sigma/api/v1/login/otp/verify"

    def __init__(self, client: Optional[APIClient] = None):
        self.client = client or APIClient(base_url=Config.MAYSON_BASE_URL)

    def request_otp(self, email_id: str, timeout: int = 30) -> APIResponse:
        """Triggers API 1: Request OTP for specified email address."""
        payload = {"email_id": email_id}
        return self.client.post(self.REQUEST_OTP_ENDPOINT, json_payload=payload, timeout=timeout)

    def verify_otp(self, email_id: str, otp: str, timeout: int = 30) -> APIResponse:
        """Triggers API 2: Verify OTP for specified email address and OTP code."""
        payload = {
            "email_id": email_id,
            "otp": otp,
        }
        return self.client.post(self.VERIFY_OTP_ENDPOINT, json_payload=payload, timeout=timeout)
