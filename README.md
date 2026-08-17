# Mayson AI - Login + Email OTP Synthetic Monitoring Automation Framework

A production-ready, lightweight synthetic monitoring framework built with **Python**, **Playwright**, **Pytest**, and **GitHub Actions**.

This framework continuously validates the complete Mayson AI authentication pipeline by executing real end-to-end user logins with automated IMAP Email OTP retrieval every 10 minutes.

---

## 🎯 Objective

This monitoring system answers one simple production question:

> **"Can a real Mayson user successfully log in with Email OTP and reach the dashboard right now?"**

* **If YES** → Output `LOGIN MONITOR → PASS`
* **If NO** → Output `LOGIN MONITOR → FAIL` + automatically capture Playwright Trace, Failure Screenshots, and trigger alert via GitHub Actions failure.

---

## 📐 Architecture & Login Flow

```text
Open Mayson Base URL
        ↓
   Login Page
        ↓
   Enter Email (MAYSON_USERNAME)
        ↓
   Request OTP
        ↓
   IMAP Mailbox Polling (utilizing timeouts & timestamp filtering)
        ↓
   Extract 4-8 Digit OTP Code
        ↓
   Enter OTP into Mayson Form
        ↓
   Submit & Verify OTP
        ↓
   Dashboard Navigation
        ↓
   Verify Dashboard Loaded
        ↓
   PASS / FAIL
```

---

## 📁 Project Structure

```text
mayson-alert/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures, tracing, and screenshot hooks
│   └── test_login.py        # End-to-end synthetic monitoring test
├── pages/
│   ├── __init__.py
│   ├── base_page.py         # Base Page Object with Playwright locators & waits
│   ├── login_page.py        # Page Object for Mayson Email & OTP screens
│   └── dashboard_page.py    # Page Object for Post-Login Dashboard
├── utils/
│   ├── __init__.py
│   ├── config.py            # Environment configuration & credential loader
│   └── email_otp.py         # IMAP OTP retriever with polling, regex & masking
├── .github/
│   └── workflows/
│       └── login-monitor.yml# GitHub Actions workflow (every 10 min & manual)
├── .env.example             # Environment configuration template
├── .gitignore               # Ignored files (secrets, cache, traces, reports)
├── pytest.ini               # Pytest execution configuration
├── requirements.txt         # Python dependencies
└── README.md                # Framework documentation & guide
```

---

## 🔐 Environment Variables & GitHub Secrets

Configure these parameters in your local `.env` file or in **GitHub Secrets** (`Settings -> Secrets and variables -> Actions`):

| Variable Name | Description | Example / Default |
| :--- | :--- | :--- |
| `MAYSON_BASE_URL` | Mayson application target URL | `https://mayson.dev` |
| `MAYSON_USERNAME` | Test user login email | `shivam.srivastava@novostack.com` |
| `MAYSON_PASSWORD` | Optional password credential | `Optional` |
| `MAIL_HOST` | IMAP mail server hostname | `imap.gmail.com` |
| `MAIL_PORT` | IMAP mail server port | `993` |
| `MAIL_USERNAME` | Monitoring mailbox login email | `monitor-user@example.com` |
| `MAIL_PASSWORD` | Monitoring mailbox password / App password | `xxxx-xxxx-xxxx-xxxx` |
| `MAIL_USE_SSL` | Enable SSL for IMAP connection | `true` |
| `OTP_EMAIL_SENDER` | Sender email filter for OTP email | `no-reply@mayson.dev` |
| `OTP_EMAIL_SUBJECT`| Subject filter for OTP email | `Your Mayson Verification Code` |

> **Security Note:** Credentials and OTP codes are strictly masked in logs and output streams (`***masked***`). Never commit plain-text credentials or `.env` files to git repositories.

---

## 🚀 Local Setup & Execution Guide

### Prerequisites
* Python 3.10 or higher
* Pip package manager

### 1. Clone & Setup Virtual Environment

```bash
git clone <your-repository-url>
cd mayson-alert

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies & Playwright Browsers

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

### 3. Create Local `.env` Configuration File

Copy `.env.example` to `.env` and fill in your monitoring mailbox and Mayson test account credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
MAYSON_BASE_URL=https://mayson.dev
MAYSON_USERNAME=shivam.srivastava@novostack.com

MAIL_HOST=imap.gmail.com
MAIL_PORT=993
MAIL_USERNAME=shivam.srivastava@novostack.com
MAIL_PASSWORD=your_app_password
MAIL_USE_SSL=true
```

### 4. Run the Synthetic Monitoring Test

Execute pytest locally:

```bash
pytest
```

To run in headed browser mode (visible browser window):

```bash
pytest --headed
```

To view stdout logging in real-time:

```bash
pytest -s
```

---

## 🔍 Failure Artifacts & Debugging

When a test failure occurs (e.g., OTP delivery timeout or dashboard render failure):

1. **Failure Screenshots**: Automatically saved to `screenshots/failure_<test_name>_<timestamp>.png`.
2. **Playwright Traces**: Detailed interaction trace zips saved to `traces/trace_<test_name>_<timestamp>.zip`.
3. **HTML Test Report**: Accessible at `report.html`.

### How to View Playwright Traces

You can inspect full DOM snapshots, network calls, and action timelines by viewing the trace zip file:

```bash
npx playwright show-trace traces/trace_test_mayson_login_otp_flow_<timestamp>.zip
```

---

## ⚙️ GitHub Actions CI/CD Integration

The GitHub Actions workflow `.github/workflows/login-monitor.yml` runs automatically:
* **Cron Schedule**: Executes every 10 minutes (`*/10 * * * *`).
* **Manual Execution**: Can be triggered manually via `Workflow Dispatch` in the GitHub Actions UI.

### Failure Artifact Downloads in GitHub Actions
If a monitoring run fails:
1. GitHub Actions flags the run as **FAILED**.
2. Download the attached `failure-artifacts` zip from the workflow run summary to inspect screenshots, traces, and HTML reports.
