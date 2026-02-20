# Sharp Printer SMTP Configuration Automation

A Python automation script that configures Sharp MX-B468F network printers by driving their web management interface with Selenium WebDriver — the same clicks a technician would make, executed programmatically and documented with screenshots at every step.

## Why This Exists

Configuring SMTP settings on a fleet of Sharp printers is a manual, repetitive, error-prone process. A technician navigates to each printer's web interface, logs in, fills out the same form fields, tests the connection, and submits — then repeats that for every device. At scale, that's not a workflow, it's a liability. One wrong field and scan-to-email breaks for an entire building.

This script eliminates the manual process. Configuration lives in a version-controlled YAML file. The script handles the rest — login, form population, connection testing, submission, and screenshot documentation. The same config runs against the [Sharp Printer Emulator](https://github.com/justinreed270/sharp-printer-emulator) for safe validation before it ever touches a production device.

## Architecture Decision — Why Selenium

The Sharp printer web interface has no API. There's no REST endpoint to POST configuration to, no CLI, no remote management protocol beyond the web UI. Selenium is the right tool here because it replicates exactly what a human technician does — navigate, click, type, submit — which means the script works against both the emulator and real hardware without modification.

**Why not use requests or BeautifulSoup?**

Those tools parse HTML and submit forms directly, bypassing JavaScript rendering. The Sharp web interface relies on JavaScript for form validation and state management. A raw HTTP approach would either fail silently or produce unpredictable results. Selenium drives a real browser, so what you see in the script is what actually happens on screen.

## How It Works

```
config.yaml → Load settings
     ↓
Chrome WebDriver → Launch browser
     ↓
Navigate to printer URL → Login
     ↓
Populate SMTP form fields
     ↓
Test connection (optional) → Real SMTP auth attempt
     ↓
Submit if test passes
     ↓
Screenshot each step → Audit trail
```

**The test-before-submit pattern is intentional.** The script won't submit a configuration that fails its own connection test. This prevents a bad config from being applied to a printer that was previously working — a safeguard that manual configuration doesn't have.

## Operating Modes

Three modes to handle the difference between emulator and production environments:

| Mode | Command | Use Case |
|------|---------|----------|
| Normal | `python scripts/configure_printer.py` | Emulator — test then submit if test passes |
| Test Only | `--test-only` | Validate config without making any changes |
| Skip Test | `--skip-test` | Real printers — submit directly (no test button on hardware) |

**Why does skip-test exist?**

Real Sharp printers don't have a "Test Connection" button in their web interface — that's a feature of the emulator. When deploying to production hardware, you skip the automated test and verify manually by sending a test scan after configuration. The flag makes this workflow explicit rather than hiding it.

## Security Design

**Credentials are never in the code.** All sensitive values live in `config.yaml`, which is excluded from version control via `.gitignore`. The repo only contains `config.example.yaml` — a template with placeholder values and no real credentials. This is the correct pattern for any automation tool that handles authentication.

**The `.gitignore` is intentional and important:**
```
config.yaml        # Your real credentials — never committed
screenshots/*      # May contain sensitive UI state
.env               # Environment files
```

**Production credential handling.** For production deployments, `config.yaml` credentials should be sourced from a secrets manager or environment variables rather than a static file. The YAML approach is appropriate for development and sandboxed testing — not for a CI/CD pipeline running against live infrastructure.

**Screenshot audit trail.** Every major step produces a timestamped screenshot. This serves two purposes: troubleshooting failures, and creating an evidence trail that configuration was applied correctly. In enterprise IT, documentation isn't optional.

## Installation

### Prerequisites
- Python 3.11+
- Google Chrome
- ChromeDriver (must match your Chrome version)

### Setup
```bash
git clone https://github.com/justinreed270/sharp-automation.git
cd sharp-automation

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Git Bash / Mac / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

### Why a Virtual Environment

Dependencies are pinned to specific versions in `requirements.txt`. A virtual environment ensures those exact versions are installed without conflicting with other Python projects on the same machine. It also makes the project portable — anyone who clones the repo gets the same environment.

## Configuration

```yaml
# Target — emulator or real printer IP
target:
  url: "http://localhost:5173"   # Emulator
  # url: "http://192.168.1.100" # Real printer
  username: "admin"
  password: "admin"

# SMTP settings to apply
smtp:
  gateway: "smtp.gmail.com"
  port: 587
  reply_address: "printer@example.com"
  use_ssl: "negotiate"           # none, negotiate, ssl, tls
  auth_method: "login-plain"     # none, login-plain, cram-md5

# Credentials for SMTP authentication
credentials:
  userid: "printer@example.com"
  password: "your-app-password"  # Use app-specific passwords, not account passwords

# Script behavior
settings:
  headless: false                # true = run without visible browser window
  screenshot_on_success: true
  screenshot_on_failure: true
  wait_timeout: 10               # seconds to wait for page elements
```

## Usage

```bash
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Standard run — test then submit
python scripts/configure_printer.py

# Test only — no changes made
python scripts/configure_printer.py --test-only

# Production mode — skip test, submit directly
python scripts/configure_printer.py --skip-test

# Custom config file
python scripts/configure_printer.py --config production-config.yaml
```

## Development Workflow

```bash
# Terminal 1 — start the emulator
cd path/to/sharp-printer-emulator
docker-compose up

# Terminal 2 — run automation against it
cd path/to/sharp-automation
.venv\Scripts\Activate.ps1
python scripts/configure_printer.py
```

Screenshots land in `screenshots/` with timestamps:
```
screenshots/
├── 01_logged_in_20260220_143022.png
├── 02_config_filled_20260220_143031.png
├── 03_test_success_20260220_143045.png
└── 04_submitted_20260220_143047.png
```

## Project Structure

```
sharp-automation/
├── .venv/                    # Virtual environment (gitignored)
├── screenshots/              # Auto-generated audit trail (gitignored)
├── scripts/
│   └── configure_printer.py # Main automation script
├── config.example.yaml       # Template — safe to commit
├── config.yaml               # Your config — never committed
├── requirements.txt          # Pinned dependencies
├── .gitignore                # Protects credentials
└── README.md
```

## Troubleshooting

**"ChromeDriver not found"** — ChromeDriver version must match your installed Chrome version exactly. Download from https://chromedriver.chromium.org and add to your system PATH.

**"Element not found"** — Increase `wait_timeout` in config.yaml. Review the error screenshots to see what the browser was seeing at the point of failure.

**"Login failed"** — Verify the URL in config.yaml. Emulator runs at `localhost:5173`. Real printers use their IP address. Confirm credentials match the target.

**"Test connection failed"** — For Gmail, use an app-specific password, not your account password. Verify the SMTP gateway and port are correct for your mail provider.

## Companion Project

This script is designed to run against the [Sharp Printer Emulator](https://github.com/justinreed270/sharp-printer-emulator) — a Dockerized full-stack application that replicates the Sharp web interface and performs real SMTP validation against live mail servers.

The two projects together demonstrate a complete provisioning pipeline:

```
Automation Script → Emulator (safe validation) → Production Printer
```

## Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Automation | Python + Selenium WebDriver | Only viable option for a JavaScript-rendered web interface with no API |
| Browser | Google Chrome (headless capable) | Most compatible with Sharp printer web interface rendering |
| Configuration | YAML | Human-readable, supports comments, version-control friendly |
| Dependencies | Virtual environment + pinned requirements.txt | Reproducible installs, no dependency conflicts |

## License

MIT