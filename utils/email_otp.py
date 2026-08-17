import imaplib
import email
from email.header import decode_header
import re
import time
import logging
from typing import Optional
from utils.config import Config

logger = logging.getLogger(__name__)


class EmailOTPFetcher:
    """
    IMAP-based Email OTP Retrieval Utility.
    Polls the configured mailbox for incoming verification emails and extracts the OTP code.
    """

    def __init__(self, config: Config):
        self.config = config

    def _connect(self) -> imaplib.IMAP4:
        """Establishes IMAP connection based on SSL setting."""
        try:
            if self.config.MAIL_USE_SSL:
                mail = imaplib.IMAP4_SSL(self.config.MAIL_HOST, self.config.MAIL_PORT)
            else:
                mail = imaplib.IMAP4(self.config.MAIL_HOST, self.config.MAIL_PORT)

            mail.login(self.config.MAIL_USERNAME, self.config.MAIL_PASSWORD)
            logger.info("IMAP authentication successful.")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect/authenticate with IMAP server {self.config.MAIL_HOST}: {e}")
            raise

    def _decode_str(self, header_value) -> str:
        """Decodes email headers safely."""
        if not header_value:
            return ""
        decoded_list = decode_header(header_value)
        result = []
        for content, encoding in decoded_list:
            if isinstance(content, bytes):
                try:
                    result.append(content.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    result.append(content.decode("latin-1", errors="replace"))
            else:
                result.append(str(content))
        return "".join(result)

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extracts text/plain or text/html body from email message object."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type in ("text/plain", "text/html") and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            body += payload.decode(charset, errors="replace") + "\n"
                        except Exception:
                            body += payload.decode("latin-1", errors="replace") + "\n"
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    body = payload.decode(charset, errors="replace")
                except Exception:
                    body = payload.decode("latin-1", errors="replace")
        return body

    def _extract_otp_from_text(self, text: str) -> Optional[str]:
        """
        Extracts 4 to 8 digit numerical OTP code from text using targeted regex patterns.
        """
        if not text:
            return None

        # Clean HTML tags if present
        clean_text = re.sub(r"<[^>]+>", " ", text)

        # Contextual regex patterns ordered by specificity
        patterns = [
            r"(?:code|otp|verification code|verify code|login code|pin)[:\s]+([0-9]{4,8})\b",
            r"\b([0-9]{4,8})\b\s*(?:is your verification code|is your OTP|is your code)",
            r"\b([0-9]{6})\b",  # Standard 6-digit code fallback
            r"\b([0-9]{4,8})\b", # General 4 to 8 digit numbers
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                logger.info("OTP pattern match found (Code masked: ***masked***).")
                return code

        return None

    def fetch_latest_otp(
        self,
        sent_after_timestamp: Optional[float] = None,
        timeout: int = 60,
        poll_interval: int = 5,
    ) -> str:
        """
        Polls the inbox until a matching OTP email is retrieved or timeout expires.

        :param sent_after_timestamp: Epoch timestamp after which the email must have arrived.
        :param timeout: Maximum seconds to poll.
        :param poll_interval: Sleep seconds between polling attempts.
        :return: Extracted OTP code string.
        :raises TimeoutError: If no valid OTP email arrives within timeout.
        """
        logger.info(f"Polling inbox for OTP email (Timeout: {timeout}s, Interval: {poll_interval}s)...")
        start_time = time.time()
        attempt = 0

        while (time.time() - start_time) < timeout:
            attempt += 1
            logger.info(f"IMAP poll attempt #{attempt}...")
            mail = None

            try:
                mail = self._connect()
                mail.select("INBOX")

                # Always retrieve ALL message IDs to ensure newest emails are inspected
                status, messages = mail.search(None, "ALL")
                msg_ids = messages[0].split() if (status == "OK" and messages[0]) else []

                # Limit inspection to the last 15 newest emails for performance
                recent_ids = msg_ids[-15:] if len(msg_ids) > 15 else msg_ids

                # Iterate through messages from newest to oldest
                for msg_id in reversed(recent_ids):
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            subject = self._decode_str(msg.get("Subject"))
                            sender = self._decode_str(msg.get("From"))

                            # Filter subject if configured
                            if self.config.OTP_EMAIL_SUBJECT and self.config.OTP_EMAIL_SUBJECT.lower() not in subject.lower():
                                continue

                            # Filter sender if configured
                            if self.config.OTP_EMAIL_SENDER and self.config.OTP_EMAIL_SENDER.lower() not in sender.lower():
                                continue

                            # Check timestamp with 300s (5-minute) clock skew tolerance for CI runners
                            if sent_after_timestamp:
                                date_hdr = msg.get("Date")
                                if date_hdr:
                                    try:
                                        msg_date_tuple = email.utils.parsedate_to_datetime(date_hdr)
                                        msg_timestamp = msg_date_tuple.timestamp()
                                        if msg_timestamp < (sent_after_timestamp - 300):
                                            continue
                                    except Exception:
                                        pass  # Proceed to check body if date header parse is uncertain


                            body = self._extract_body(msg)
                            otp_code = self._extract_otp_from_text(body)

                            if otp_code:
                                logger.info("Matching OTP email processed successfully.")
                                return otp_code

            except Exception as e:
                logger.warning(f"Error during IMAP poll attempt #{attempt}: {e}")
            finally:
                if mail:
                    try:
                        mail.close()
                        mail.logout()
                    except Exception:
                        pass

            time.sleep(poll_interval)

        error_msg = f"Timed out after {timeout} seconds waiting for OTP email."
        logger.error(error_msg)
        raise TimeoutError(error_msg)
