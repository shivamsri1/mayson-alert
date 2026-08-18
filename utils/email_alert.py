import json
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict

from utils.config import Config
from utils.logger import logger

STATE_FILE = Path(".state/monitor_status.json")


class EmailAlertManager:
    """Utility to send failure and recovery alerts via SMTP with state tracking to avoid alert spam."""

    def __init__(self):
        self.host = Config.ALERT_SMTP_HOST
        self.port = Config.ALERT_SMTP_PORT
        self.username = Config.ALERT_SMTP_USERNAME
        self.password = Config.ALERT_SMTP_PASSWORD
        self.from_addr = Config.ALERT_EMAIL_FROM
        self.to_addr = Config.ALERT_EMAIL_TO
        self.use_ssl = Config.ALERT_SMTP_USE_SSL

    def _read_state(self) -> Dict[str, str]:
        """Reads current state from local json file."""
        if not STATE_FILE.exists():
            return {"last_status": "PASS", "last_updated": ""}
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read state file: {e}")
            return {"last_status": "PASS", "last_updated": ""}

    def _write_state(self, status: str) -> None:
        """Writes current monitoring status to local json file."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state_data = {
                "last_status": status,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not write state file: {e}")

    def _send_email(self, subject: str, body: str) -> bool:
        """Sends an email notification via SMTP."""
        if not self.host or not self.from_addr or not self.to_addr:
            logger.warning("SMTP alert configuration incomplete. Skipping email alert transmission.")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = self.to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            logger.info(f"Connecting to SMTP server {self.host}:{self.port} to send alert email...")

            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
            server.quit()

            logger.info(f"Alert email successfully sent to {self.to_addr} with subject: '{subject}'")
            return True
        except Exception as err:
            logger.error(f"Failed to send alert email via SMTP: {err}")
            return False

    def send_failure_alert(
        self,
        step_statuses: Dict[str, str],
        elapsed_time_sec: float,
        environment: str = "Production",
    ) -> bool:
        """Sends failure alert email if status transitioned to FAIL or on initial failure.

        Suppresses repeat failure alerts during an ongoing outage.
        """
        state = self._read_state()
        last_status = state.get("last_status", "PASS")

        if last_status == "FAIL":
            logger.info("Failure alert suppressed: An alert was already sent for the ongoing incident.")
            return False

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        req_otp_status = step_statuses.get("Request OTP API", "UNKNOWN")
        otp_email_status = step_statuses.get("OTP Email", "UNKNOWN")
        verify_otp_status = step_statuses.get("Verify OTP API", "UNKNOWN")

        subject = "🚨 Mayson Production Login Monitor FAILED"
        body = (
            "Mayson Login OTP monitoring has failed.\n\n"
            f"Request OTP API: {req_otp_status}\n"
            f"OTP Email: {otp_email_status}\n"
            f"Verify OTP API: {verify_otp_status}\n\n"
            f"Environment: {environment}\n"
            f"Time: {now_str}\n"
            f"Response Time: {elapsed_time_sec:.2f}s\n\n"
            "Please check the monitoring logs for full execution details."
        )

        sent = self._send_email(subject, body)
        self._write_state("FAIL")
        return sent

    def send_recovery_alert(self, elapsed_time_sec: float, environment: str = "Production") -> bool:
        """Sends recovery alert email if status transitioned from FAIL back to PASS."""
        state = self._read_state()
        last_status = state.get("last_status", "PASS")

        if last_status != "FAIL":
            # Normal passing run, update timestamp only
            self._write_state("PASS")
            return False

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = "✅ Mayson Production Login Monitor RECOVERED"
        body = (
            "Mayson Login OTP monitoring is working normally again.\n\n"
            "Current Status: PASS\n"
            f"Environment: {environment}\n"
            f"Time: {now_str}\n"
            f"Total Flow Latency: {elapsed_time_sec:.2f}s\n"
        )

        sent = self._send_email(subject, body)
        self._write_state("PASS")
        return sent
