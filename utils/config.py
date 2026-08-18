import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env file if present in project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_str(var_name: str, default: str = "") -> str:
    """Retrieve string environment variable."""
    val = os.getenv(var_name)
    if val is None or val.strip() == "":
        return default
    return val.strip()


def get_int(var_name: str, default: int) -> int:
    """Retrieve integer environment variable."""
    val = os.getenv(var_name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def get_bool(var_name: str, default: bool) -> bool:
    """Retrieve boolean environment variable."""
    val = os.getenv(var_name)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")


class Config:
    """Centralized framework configuration loaded from environment variables."""

    # Mayson API Target Settings
    MAYSON_BASE_URL: str = get_str(
        "MAYSON_BASE_URL", "https://cc1fbde45ead-in-south-01.mayson.dev"
    ).rstrip("/")
    MAYSON_EMAIL: str = get_str("MAYSON_EMAIL", "")
    MAYSON_CURRENT_IP: str = get_str("MAYSON_CURRENT_IP", "127.0.0.1")

    # IMAP Mailbox Settings (Reading OTP Email)
    MAIL_HOST: str = get_str("MAIL_HOST", "")
    MAIL_PORT: int = get_int("MAIL_PORT", 993)
    MAIL_USERNAME: str = get_str("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = get_str("MAIL_PASSWORD", "")
    MAIL_USE_SSL: bool = get_bool("MAIL_USE_SSL", True)

    # OTP Email Polling Settings
    OTP_EMAIL_SENDER: str = get_str("OTP_EMAIL_SENDER", "")
    OTP_EMAIL_SUBJECT: str = get_str("OTP_EMAIL_SUBJECT", "")
    OTP_TIMEOUT_SECONDS: int = get_int("OTP_TIMEOUT_SECONDS", 60)
    OTP_POLL_INTERVAL_SECONDS: int = get_int("OTP_POLL_INTERVAL_SECONDS", 3)

    # SMTP Alert Settings (Sending Failure & Recovery Alerts)
    ALERT_SMTP_HOST: str = get_str("ALERT_SMTP_HOST", "")
    ALERT_SMTP_PORT: int = get_int("ALERT_SMTP_PORT", 587)
    ALERT_SMTP_USERNAME: str = get_str("ALERT_SMTP_USERNAME", "")
    ALERT_SMTP_PASSWORD: str = get_str("ALERT_SMTP_PASSWORD", "")
    ALERT_EMAIL_FROM: str = get_str("ALERT_EMAIL_FROM", "")
    ALERT_EMAIL_TO: str = get_str("ALERT_EMAIL_TO", "")
    ALERT_SMTP_USE_SSL: bool = get_bool("ALERT_SMTP_USE_SSL", False)

    @classmethod
    def validate_api_config(cls) -> None:
        """Ensure critical API environment variables are defined."""
        missing = []
        if not cls.MAYSON_BASE_URL:
            missing.append("MAYSON_BASE_URL")
        if not cls.MAYSON_EMAIL:
            missing.append("MAYSON_EMAIL")
        if missing:
            raise ValueError(f"Missing required API configuration environment variables: {', '.join(missing)}")

    @classmethod
    def validate_mail_config(cls) -> None:
        """Ensure IMAP mailbox configuration environment variables are defined."""
        missing = []
        if not cls.MAIL_HOST:
            missing.append("MAIL_HOST")
        if not cls.MAIL_USERNAME:
            missing.append("MAIL_USERNAME")
        if not cls.MAIL_PASSWORD:
            missing.append("MAIL_PASSWORD")
        if missing:
            raise ValueError(f"Missing required IMAP environment variables: {', '.join(missing)}")

    @classmethod
    def validate_alert_config(cls) -> None:
        """Ensure SMTP alert configuration environment variables are defined."""
        missing = []
        if not cls.ALERT_SMTP_HOST:
            missing.append("ALERT_SMTP_HOST")
        if not cls.ALERT_EMAIL_FROM:
            missing.append("ALERT_EMAIL_FROM")
        if not cls.ALERT_EMAIL_TO:
            missing.append("ALERT_EMAIL_TO")
        if missing:
            raise ValueError(f"Missing required SMTP Alert environment variables: {', '.join(missing)}")
