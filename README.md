# Mayson API Login Monitoring with Email Alerts

A simple, resilient **API-only synthetic monitoring framework** for the Mayson AI platform.

This framework continuously validates the Mayson production login OTP authentication flow and dispatches automated **email alerts** upon failure or recovery.

---

## 🏗️ Tech Stack

* **Language**: Python 3.11+
* **Test Runner**: Pytest
* **HTTP Client**: Requests
* **Mailbox Protocol**: IMAP (`imaplib` / `email`) for polling and extracting OTP codes
* **Alert Transmission**: SMTP (`smtplib`) for dispatching failure and recovery alert emails
* **CI/CD**: GitHub Actions (Scheduled every 5 minutes + manual trigger)

---

## ⚡ Synthetic Monitoring Flow

```text
Start
  ↓
Request OTP API  ----------------->  POST /sigma/api/v2/auth/otp/email/login
  ↓
Validate API Response
  ↓
Wait for OTP Email  -------------->  IMAP Polling (Filtered by Sender & Subject)
  ↓
Extract OTP  --------------------->  Regex Parsing (Masked in logs)
  ↓
Verify OTP API   ----------------->  POST /sigma/api/v1/login/otp/verify
  ↓
Validate Auth Response
  ↓
Record Latency Metric
  ↓
PASS / FAIL  --------------------->  Dispatch Email Alert (If failure/recovery state transitioned)
```

---

## 📁 Project Structure

```text
mayson-alert/
│
├── api/
│   ├── api_client.py       # Base HTTP client (Headers, UUID generation, log masking, latency)
│   └── auth_api.py         # Mayson API endpoint definitions (Request OTP & Verify OTP)
│
├── utils/
│   ├── config.py           # Environment variable loader & validator
│   ├── logger.py           # Logging setup with sensitive data redaction filter
│   ├── email_otp.py        # IMAP OTP reader and regex extraction utility
│   └── email_alert.py      # SMTP alert manager with state tracking and anti-spam protection
│
├── tests/
│   └── test_login_monitor.py # Pytest synthetic test suite with single-retry logic
│
├── .github/
│   └── workflows/
│       └── login-monitor.yml # GitHub Actions workflow (Runs every 10 minutes)
│
├── requirements.txt        # Python package dependencies
├── pytest.ini             # Pytest configuration
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore specification
└── README.md               # Framework documentation
```

---

## 🔑 Required Environment Variables & Secrets

The framework requires the following variables defined in `.env` locally or in **GitHub Repository Secrets** for CI/CD:

| Variable Name | Description | Example / Default |
|---|---|---|
| `MAYSON_BASE_URL` | Base URL of Mayson API | `https://cc1fbde45ead-in-south-01.mayson.dev` |
| `MAYSON_EMAIL` | Target monitoring email address | `monitoring@example.com` |
| `MAYSON_CURRENT_IP` | Origin IP header value | `127.0.0.1` |
| `MAIL_HOST` | IMAP server hostname | `imap.example.com` |
| `MAIL_PORT` | IMAP server port | `993` |
| `MAIL_USERNAME` | IMAP login email | `monitoring@example.com` |
| `MAIL_PASSWORD` | IMAP login password | `app_password_here` |
| `MAIL_USE_SSL` | Enable SSL for IMAP connection | `true` |
| `OTP_EMAIL_SENDER` | Filter OTP emails by sender | `noreply@mayson.dev` |
| `OTP_EMAIL_SUBJECT` | Filter OTP emails by subject | `Mayson OTP Login` |
| `OTP_TIMEOUT_SECONDS` | Max timeout to wait for OTP email | `60` |
| `OTP_POLL_INTERVAL_SECONDS` | Interval between IMAP polls | `3` |
| `ALERT_SMTP_HOST` | SMTP server for sending alerts | `smtp.example.com` |
| `ALERT_SMTP_PORT` | SMTP server port | `587` |
| `ALERT_SMTP_USERNAME` | SMTP login username | `alerts@example.com` |
| `ALERT_SMTP_PASSWORD` | SMTP login password | `smtp_password_here` |
| `ALERT_EMAIL_FROM` | Sender address for alert emails | `alerts@example.com` |
| `ALERT_EMAIL_TO` | Recipient address for alert emails | `oncall@example.com` |
| `ALERT_SMTP_USE_SSL` | Enable SSL for SMTP connection | `false` |

---

## 🚀 Local Setup & Execution

### 1. Clone & Setup Virtual Environment

```bash
git clone <repository_url>
cd mayson-alert

python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your target credentials:

```bash
cp .env.example .env
```

### 4. Execute Monitoring Test Suite

Run the synthetic monitor locally using pytest:

```bash
pytest
```

To view verbose log outputs during test execution:

```bash
pytest -v -s
```

---

## 🚨 Email Alerting & Failure Protection

### 1. Retry Protection
If the initial monitoring run fails, the framework automatically waits 5 seconds and **retries the entire flow ONCE**. A failure alert is only triggered if the retry attempt also fails.

### 2. Failure Email Notification
Dispatched when a confirmed monitoring outage occurs.

* **Subject**: `🚨 Mayson Production Login Monitor FAILED`
* **Content**: Includes step-by-step PASS/FAIL statuses, execution duration, and timestamp.
* **Security Guarantee**: OTP codes, passwords, authorization headers, and tokens are **never included** in alert payloads.

### 3. Recovery Email Notification
Dispatched automatically when the system recovers from a previously recorded outage.

* **Subject**: `✅ Mayson Production Login Monitor RECOVERED`

### 4. Anti-Spam Protection
The framework maintains an alert state file (`.state/monitor_status.json`). Repeated scheduled runs during an ongoing outage will **not** spam your inbox with duplicate failure emails.

---

## ⚙️ GitHub Actions CI/CD Integration

The workflow in `.github/workflows/login-monitor.yml` automatically:
1. Triggers every 10 minutes (`*/10 * * * *`).
2. Supports manual triggering via `workflow_dispatch`.
3. Restores monitoring state across runs using `actions/cache`.
4. Uploads test execution logs (`logs/monitor.log`) as workflow artifacts for post-mortem analysis.

### Setting Up GitHub Secrets
Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret** and add all variables listed in the configuration table above.
