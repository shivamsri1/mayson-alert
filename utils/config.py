import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

logger = logging.getLogger(__name__)


def _clean_str(val: str, default: str = "") -> str:
    if not val:
        return default
    return str(val).strip().replace("\r", "").replace("\n", "")


def _get_bool(env_var: str, default: bool = True) -> bool:
    val = os.getenv(env_var)
    if val is None or not str(val).strip():
        return default
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def _get_int(env_var: str, default: int = 993) -> int:
    val = os.getenv(env_var)
    if val is None or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except ValueError:
        logger.warning(f"Invalid integer for {env_var}: {val}. Using default {default}.")
        return default


@dataclass
class Config:
    """Application configuration and credentials retrieved from environment variables."""

    MAYSON_BASE_URL: str = _clean_str(os.getenv("MAYSON_BASE_URL"), "https://mayson.dev").rstrip("/")
    MAYSON_USERNAME: str = _clean_str(os.getenv("MAYSON_USERNAME"), "")
    MAYSON_PASSWORD: str = _clean_str(os.getenv("MAYSON_PASSWORD"), "")

    MAIL_HOST: str = _clean_str(os.getenv("MAIL_HOST"), "imap.gmail.com")
    MAIL_PORT: int = _get_int("MAIL_PORT", 993)
    MAIL_USERNAME: str = _clean_str(os.getenv("MAIL_USERNAME"), "")
    MAIL_PASSWORD: str = _clean_str(os.getenv("MAIL_PASSWORD"), "")
    MAIL_USE_SSL: bool = _get_bool("MAIL_USE_SSL", True) or (_get_int("MAIL_PORT", 993) == 993)

    OTP_EMAIL_SENDER: str = _clean_str(os.getenv("OTP_EMAIL_SENDER"), "")
    OTP_EMAIL_SUBJECT: str = _clean_str(os.getenv("OTP_EMAIL_SUBJECT"), "")


    @classmethod
    def validate(cls) -> "Config":
        """
        Validates that mandatory environment configuration parameters are present.
        Raises ValueError if required settings are missing.
        """
        config = cls()
        missing = []

        if not config.MAYSON_BASE_URL:
            missing.append("MAYSON_BASE_URL")
        if not config.MAYSON_USERNAME:
            missing.append("MAYSON_USERNAME")
        if not config.MAIL_HOST:
            missing.append("MAIL_HOST")
        if not config.MAIL_USERNAME:
            missing.append("MAIL_USERNAME")
        if not config.MAIL_PASSWORD:
            missing.append("MAIL_PASSWORD")

        if missing:
            error_msg = f"Missing required environment variables for synthetic login monitor: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Loaded monitoring config for URL: {config.MAYSON_BASE_URL}")
        logger.info(f"Target login user: {config.MAYSON_USERNAME}")
        logger.info(f"IMAP host: {config.MAIL_HOST}:{config.MAIL_PORT} (SSL: {config.MAIL_USE_SSL})")

        return config
