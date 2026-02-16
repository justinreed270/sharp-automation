# Sharp Printer SMTP Configuration Automation

Python-based automation tool for configuring Sharp MX-B468F network printers using Selenium WebDriver. Designed to safely test printer provisioning scripts against an emulator before deploying to production hardware.

## Problem Statement

**Challenge:** IT teams need to configure SMTP settings on dozens of Sharp network printers, but:
- Manual configuration is time-consuming and error-prone
- Testing on production printers risks disrupting operations
- No sandbox environment exists for validating provisioning scripts

**Solution:** This automation script, combined with the Sharp printer emulator, provides:
- Safe testing in a sandboxed environment
- Automated configuration deployment
- Screenshot-based verification
- Support for both development (emulator) and production (real printers) workflows

## Features

- **Automated Web Interface Interaction**: Uses Selenium to replicate manual configuration steps
- **YAML-based Configuration**: Easy-to-modify settings stored in version-controlled format
- **Dual-mode Operation**: Supports both emulator testing and real printer deployment
- **Screenshot Documentation**: Captures evidence of each configuration step
- **Error Handling**: Graceful failure with detailed logging
- **Command-line Flexibility**: Multiple modes for different use cases

## Architecture

### Technology Stack
- **Language**: Python 3.11+
- **Web Automation**: Selenium WebDriver with Chrome
- **Configuration**: YAML (human-readable, supports comments)
- **Dependencies**: Minimal (selenium, pyyaml, requests)

### Workflow
```
1. Load config.yaml → Parse SMTP settings
2. Initialize WebDriver → Launch Chrome browser
3. Navigate to printer → Login with credentials
4. Fill SMTP form → Populate all required fields
5. Test connection (optional) → Validate settings work
6. Submit configuration → Apply changes
7. Screenshot & log → Document the process
```

## Installation

### Prerequisites
- Python 3.11 or higher
- Google Chrome browser
- ChromeDriver (matching your Chrome version)

### Setup
```bash
# Clone the repository
git clone https://github.com/justinreed270/sharp-automation.git
cd sharp-automation

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Git Bash:
source .venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Create your configuration file
cp config.example.yaml config.yaml

# Edit config.yaml with your settings
# (Use your favorite text editor)
```

## Configuration

### config.yaml Structure
```yaml
# Target printer/emulator settings
target:
  url: "http://localhost:5173"  # Emulator or printer IP
  username: "admin"              # Web interface login
  password: "admin"              # Web interface password

# SMTP settings to configure
smtp:
  gateway: "smtp.gmail.com"      # SMTP server address
  port: 587                       # SMTP port (25, 465, 587, 2525)
  reply_address: "printer@example.com"
  use_ssl: "negotiate"            # none, negotiate, ssl, tls
  auth_method: "login-plain"      # none, login-plain, cram-md5

# Device credentials for SMTP authentication
credentials:
  userid: "printer@example.com"
  password: "your-app-password"   # Use app-specific passwords

# Script behavior settings
settings:
  headless: false                 # true = run browser in background
  screenshot_on_success: true
  screenshot_on_failure: true
  wait_timeout: 10                # seconds to wait for elements
```

### Security Considerations

**CRITICAL:** Never commit `config.yaml` to version control!

The `.gitignore` file already excludes it. Only `config.example.yaml` (template with no real credentials) should be committed.

**Best Practices:**
- Use app-specific passwords (not your main email password)
- Store production credentials in environment variables or secrets manager
- Restrict file permissions on `config.yaml` (`chmod 600` on Linux/Mac)
- Use separate test accounts for development

## Usage

### Basic Usage (Test Against Emulator)
```bash
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Run with default settings (uses config.yaml)
python scripts/configure_printer.py
```

This will:
1. Log in to the printer/emulator
2. Fill in SMTP configuration
3. Test the connection (validates credentials)
4. Submit the configuration if test passes

### Advanced Usage

**Test Mode (Don't Submit):**
```bash
python scripts/configure_printer.py --test-only
```
Use this to verify configuration without making changes.

**Production Mode (Skip Test):**
```bash
python scripts/configure_printer.py --skip-test
```
Use this for real Sharp printers that don't have a test button.

**Custom Config File:**
```bash
python scripts/configure_printer.py --config production-config.yaml
```

**Headless Mode:**
Edit `config.yaml` and set `headless: true` to run without visible browser.

## Project Structure
```
sharp-automation/
├── .venv/                       # Virtual environment (gitignored)
├── screenshots/                 # Auto-generated screenshots (gitignored)
│   ├── 01_logged_in_*.png
│   ├── 02_config_filled_*.png
│   ├── 03_test_success_*.png
│   └── 04_submitted_*.png
├── scripts/
│   └── configure_printer.py     # Main automation script
├── config.example.yaml          # Template configuration (safe to commit)
├── config.yaml                  # Your configuration (gitignored)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Protects secrets
└── README.md                    # This file
```

## How It Works (Technical Deep Dive)

### 1. Configuration Loading
```python
def _load_config(self, config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```
- Reads YAML file
- Validates structure
- Fails fast if config missing

### 2. WebDriver Initialization
```python
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
self.driver = webdriver.Chrome(options=options)
```
- Configures Chrome for automation
- Sets window size for consistent screenshots
- Handles headless mode if configured

### 3. Element Selection Strategy
The script uses multiple CSS selector strategies for robustness:
- **Placeholder text**: `input[placeholder='smtp.gmail.com']`
- **Input types**: `input[type='text']`, `input[type='password']`
- **Button text matching**: Searches for buttons containing "submit" or "test"

This approach handles minor UI variations between printer models.

### 4. Password Field Detection
```python
all_password_fields = self.driver.find_elements(...)
if len(all_password_fields) >= 2:
    password_field = all_password_fields[-1]  # Use last field
elif len(all_password_fields) == 1:
    password_field = all_password_fields[0]   # Use only field
```
**Why this logic?**
- After login, the login password field disappears
- The device password field is what remains
- Script handles both 1 and 2+ password field scenarios

### 5. Screenshot Documentation
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{name}_{timestamp}.png"
self.driver.save_screenshot(filename)
```
Every major step is documented with timestamped screenshots for:
- Troubleshooting failures
- Audit trails
- Demonstrating successful execution

## Troubleshooting

### Common Issues

**"ChromeDriver not found"**
- Install ChromeDriver: https://chromedriver.chromium.org/
- Ensure it matches your Chrome version
- Add to system PATH or place in project directory

**"Element not found"**
- Increase `wait_timeout` in config.yaml
- Check if printer UI differs from expected
- Review screenshots to see what browser sees

**"Login failed"**
- Verify URL is correct (emulator: localhost:5173, printer: IP address)
- Check username/password in config.yaml
- Ensure printer web interface is accessible

**"Test connection failed"**
- Verify SMTP credentials are correct
- For Gmail, use app-specific password (not your account password)
- Check firewall isn't blocking SMTP ports

## Development Workflow

### Testing Against Emulator
```bash
# Terminal 1: Start the emulator
cd path/to/sharp-emulator
docker-compose up

# Terminal 2: Run automation
cd path/to/sharp-automation
.venv\Scripts\Activate.ps1
python scripts/configure_printer.py
```

### Deploying to Real Printers

1. Update `config.yaml` with printer's IP address
2. Use `--skip-test` flag (real printers lack test button)
3. Verify with actual test scan after configuration
```bash
python scripts/configure_printer.py --skip-test
```

## Use Cases

### IT Operations
- Bulk configuration of new printer deployments
- Standardizing SMTP settings across fleet
- Migrating printers to new email servers

### Testing & QA
- Validating configuration scripts before production
- Regression testing after firmware updates
- Training new IT staff on printer configuration

### DevOps Integration
- CI/CD pipelines for infrastructure as code
- Automated provisioning in cloud environments
- Configuration management alongside tools like Ansible

## Future Enhancements

Potential improvements for future versions:
- [ ] Support for additional printer models (Canon, HP, Ricoh)
- [ ] REST API wrapper for remote execution
- [ ] Bulk configuration from CSV file
- [ ] Integration with configuration management tools
- [ ] Slack/email notifications on completion
- [ ] Network discovery and automatic printer detection

## Contributing

This project is currently a personal portfolio piece. If you find it useful and want to extend it, feel free to fork and modify.

## License

MIT License - See LICENSE file for details

## Author

Built to demonstrate:
- Python automation capabilities
- Security-conscious development practices
- Infrastructure as Code principles
- Professional software engineering workflows

## Related Projects

This automation tool is designed to work with the [Sharp Printer Emulator](https://github.com/justinreed270/sharp-printer-emulator) for safe testing before production deployment.