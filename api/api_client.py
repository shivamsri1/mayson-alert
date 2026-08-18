import time
import uuid
from typing import Any, Dict, Optional

import requests

from utils.config import Config
from utils.logger import logger


class APIResponse:
    """Standardized wrapper for API responses."""

    def __init__(
        self,
        status_code: int,
        json_data: Optional[Any],
        text: str,
        elapsed_sec: float,
        url: str,
    ):
        self.status_code = status_code
        self.json = json_data
        self.text = text
        self.elapsed_sec = elapsed_sec
        self.url = url

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class APIClient:
    """Base HTTP client handling headers, dynamic UUID generation, timing, and log masking."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or Config.MAYSON_BASE_URL).rstrip("/")
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Generates required Mayson headers with a fresh UUID Idempotency-Key for every request."""
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": "https://mayson.dev/",
            "M-Current-ip": Config.MAYSON_CURRENT_IP,
            "Idempotency-Key": str(uuid.uuid4()),
        }

    def post(self, endpoint: str, json_payload: Optional[Dict[str, Any]] = None, timeout: int = 30) -> APIResponse:
        """Executes HTTP POST request with automatic header injection and metric recording."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        # Mask payload for logging
        masked_payload = None
        if json_payload:
            masked_payload = {
                k: ("***REDACTED***" if k in ("otp", "password", "token") else v)
                for k, v in json_payload.items()
            }

        logger.info(f"Sending POST {url} | Idempotency-Key: {headers['Idempotency-Key']} | Payload: {masked_payload}")

        start_time = time.time()
        try:
            res = self.session.post(url, json=json_payload, headers=headers, timeout=timeout)
            elapsed_sec = round(time.time() - start_time, 3)

            json_data = None
            try:
                json_data = res.json()
            except Exception:
                json_data = None

            logger.info(f"Received Response {res.status_code} from {url} in {elapsed_sec}s")

            return APIResponse(
                status_code=res.status_code,
                json_data=json_data,
                text=res.text,
                elapsed_sec=elapsed_sec,
                url=url,
            )

        except requests.exceptions.Timeout:
            elapsed_sec = round(time.time() - start_time, 3)
            logger.error(f"HTTP POST request to {url} timed out after {elapsed_sec}s")
            raise TimeoutError(f"Request to {url} timed out after {timeout} seconds.")
        except requests.exceptions.RequestException as exc:
            logger.error(f"HTTP POST request to {url} failed with error: {exc}")
            raise
