import logging
import os
import re
from pathlib import Path

# Common patterns for sensitive fields to redact
SENSITIVE_PATTERNS = [
    (re.compile(r'("otp"\s*:\s*")[^"]+(")'), r'\1***REDACTED***\2'),
    (re.compile(r'("password"\s*:\s*")[^"]+(")'), r'\1***REDACTED***\2'),
    (re.compile(r'("access_token"\s*:\s*")[^"]+(")'), r'\1***REDACTED***\2'),
    (re.compile(r'("token"\s*:\s*")[^"]+(")'), r'\1***REDACTED***\2'),
    (re.compile(r'(Authorization\s*:\s*)[^\s,]+', re.IGNORECASE), r'\1***REDACTED***'),
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter to automatically redact sensitive information like OTPs, tokens, and passwords."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in SENSITIVE_PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        return True


def setup_logger(name: str = "mayson_monitor") -> logging.Logger:
    """Configures and returns a centralized logger with sensitive data masking."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.addFilter(SensitiveDataFilter())

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "monitor.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
