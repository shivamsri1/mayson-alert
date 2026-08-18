import email
import email.utils
import imaplib
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

from utils.config import Config
from utils.logger import logger


class EmailOTPFetcher:
    """IMAP utility for polling, filtering, and extracting OTP codes from emails."""

    def __init__(self):
        Config.validate_mail_config()
        self.host = Config.MAIL_HOST
        self.port = Config.MAIL_PORT
        self.username = Config.MAIL_USERNAME
        self.password = Config.MAIL_PASSWORD
        self.use_ssl = Config.MAIL_USE_SSL
        self.sender_filter = Config.OTP_EMAIL_SENDER
        self.subject_filter = Config.OTP_EMAIL_SUBJECT
        self.timeout = Config.OTP_TIMEOUT_SECONDS
        self.poll_interval = Config.OTP_POLL_INTERVAL_SECONDS

    def _connect(self) -> imaplib.IMAP4:
        """Establishes IMAP connection."""
        if self.use_ssl:
            client = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            client = imaplib.IMAP4(self.host, self.port)
        client.login(self.username, self.password)
        client.select("INBOX")
        return client

    def _decode_header_str(self, header_val: str) -> str:
        """Decodes MIME encoded headers."""
        if not header_val:
            return ""
        decoded_parts = email.header.decode_header(header_val)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or "utf-8", errors="ignore"))
            else:
                result.append(str(part))
        return "".join(result)

    def _extract_body(self, msg: Any) -> str:
        """Extracts text or html body content from email message."""
        if msg.is_multipart():
            text_body = ""
            html_body = ""
            for part in msg.walk():
                content_type = part.get_content_type()
                disp = str(part.get("Content-Disposition", ""))
                if "attachment" in disp:
                    continue
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        text_body += payload.decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body += payload.decode("utf-8", errors="ignore")
            return text_body if text_body else html_body
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode("utf-8", errors="ignore")
        return ""

    def _extract_otp_from_text(self, text: str) -> Optional[str]:
        """Extracts numeric OTP using regex without logging the code value."""
        if not text:
            return None

        # Clean HTML tags and normalize whitespace
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)

        # Pattern 1: Keywords BEFORE number (e.g. 'verification code is 123456' or 'OTP: 1234')
        kw_before = re.compile(
            r'(?:code|otp|verification code|one-time password|passcode|pin|verification)[^\d]{0,30}?(\d{4,8})\b',
            re.IGNORECASE,
        )
        match = kw_before.search(clean_text)
        if match:
            return match.group(1)

        # Pattern 2: Keywords AFTER number (e.g. 'Use 123456 as your Mayson OTP')
        kw_after = re.compile(
            r'\b(\d{4,8})[^\d]{0,30}?(?:code|otp|verification code|one-time password|passcode|pin|verification)',
            re.IGNORECASE,
        )
        match = kw_after.search(clean_text)
        if match:
            return match.group(1)

        # Pattern 3: Standalone 6-digit number (most common for OTPs)
        match_6digit = re.search(r'\b(\d{6})\b', clean_text)
        if match_6digit:
            return match_6digit.group(1)

        # Pattern 4: Standalone 4 to 8 digit number (excluding common years 2020-2030)
        matches = re.findall(r'\b(\d{4,8})\b', clean_text)
        for num in matches:
            if num not in [str(y) for y in range(2020, 2031)]:
                return num

        return None

    def fetch_latest_otp(self, start_timestamp: datetime) -> str:
        """Polls IMAP mailbox for emails received after start_timestamp and extracts the OTP code.

        Never logs the OTP code itself.
        """
        logger.info(
            f"Polling IMAP mailbox '{self.username}' at {self.host}:{self.port} "
            f"for OTP email (Timeout: {self.timeout}s, Poll Interval: {self.poll_interval}s)..."
        )

        poll_start = time.time()

        # Ensure start_timestamp has timezone info (UTC fallback)
        if start_timestamp.tzinfo is None:
            start_timestamp = start_timestamp.replace(tzinfo=timezone.utc)

        # Allow a 15-second clock skew buffer for mail server date headers
        from datetime import timedelta
        effective_start = start_timestamp - timedelta(seconds=15)

        while time.time() - poll_start < self.timeout:
            client = None
            try:
                client = self._connect()
                status, data = client.search(None, "ALL")

                if status == "OK" and data and data[0]:
                    msg_ids = data[0].split()
                    # Reverse loop to check newest emails first (limit to last 25)
                    for msg_id in reversed(msg_ids[-25:]):
                        res, msg_data = client.fetch(msg_id, "(RFC822)")
                        if res != "OK" or not msg_data or not msg_data[0]:
                            continue

                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        # Check Date header
                        date_header = msg.get("Date")
                        if date_header:
                            try:
                                msg_dt = email.utils.parsedate_to_datetime(date_header)
                                if msg_dt.tzinfo is None:
                                    msg_dt = msg_dt.replace(tzinfo=timezone.utc)

                                # Ignore emails received before test start (with clock skew tolerance)
                                if msg_dt < effective_start:
                                    continue
                            except Exception as e:
                                logger.debug(f"Failed to parse email Date header '{date_header}': {e}")

                        # Check Sender filter
                        from_header = self._decode_header_str(msg.get("From", ""))
                        if self.sender_filter and self.sender_filter.lower() not in from_header.lower():
                            continue

                        # Check Subject filter
                        subject_header = self._decode_header_str(msg.get("Subject", ""))
                        if self.subject_filter and self.subject_filter.lower() not in subject_header.lower():
                            continue

                        # Extract Body and OTP
                        body = self._extract_body(msg)
                        otp = self._extract_otp_from_text(body)

                        if otp:
                            elapsed = round(time.time() - poll_start, 2)
                            logger.info(f"Successfully received OTP email and extracted OTP code in {elapsed}s.")
                            return otp

            except Exception as err:
                logger.warning(f"IMAP poll error encountered: {err}")
            finally:
                if client:
                    try:
                        client.logout()
                    except Exception:
                        pass

            time.sleep(self.poll_interval)

        elapsed = round(time.time() - poll_start, 2)
        logger.error(f"OTP email polling timed out after {elapsed} seconds.")
        raise TimeoutError(f"OTP email was not received within {self.timeout} seconds.")
