"""
Sharp Printer SMTP Configuration Automation Script

This script automates the configuration of Sharp MX-B468F printers
by interacting with their web management interface using Selenium.
"""

import yaml
import time
import argparse
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class SharpPrinterConfigurator:
    """Automates SMTP configuration for Sharp printers"""
    
    def __init__(self, config_path="config.yaml"):
        """Initialize configurator with settings from YAML file"""
        self.config = self._load_config(config_path)
        self.driver = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[ERROR] Config file not found: {config_path}")
            print("[INFO] Copy config.example.yaml to config.yaml and customize it")
            exit(1)
    
    def _take_screenshot(self, name):
        """Save screenshot with timestamp"""
        if self.driver:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.screenshots_dir / f"{name}_{timestamp}.png"
            self.driver.save_screenshot(str(filename))
            print(f"[SCREENSHOT] Saved: {filename}")
    
    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        
        if self.config['settings'].get('headless', False):
            options.add_argument('--headless')
            
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(self.config['settings'].get('wait_timeout', 10))
            print("[SUCCESS] WebDriver initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            print("[INFO] Make sure Chrome and ChromeDriver are installed")
            exit(1)
    
    def login(self):
        """Log in to printer web interface"""
        try:
            url = self.config['target']['url']
            print(f"[INFO] Navigating to {url}")
            self.driver.get(url)
            
            # Wait for login page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            # Find and fill username
            username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            username_field.clear()
            username_field.send_keys(self.config['target']['username'])
            
            # Find and fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(self.config['target']['password'])
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(2)
            
            print("[SUCCESS] Logged in successfully")
            self._take_screenshot("01_logged_in")
            
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            self._take_screenshot("error_login_failed")
            raise
    
    def configure_smtp(self):
        """Fill in SMTP configuration form"""
        try:
            print("[INFO] Configuring SMTP settings...")
            
            smtp = self.config['smtp']
            creds = self.config['credentials']
            
            # Primary SMTP Gateway
            gateway_field = self.driver.find_element(By.CSS_SELECTOR, 
                "input[placeholder='smtp.gmail.com'], input[placeholder='smtp.example.com']")
            gateway_field.clear()
            gateway_field.send_keys(smtp['gateway'])
            print(f"  [OK] Gateway: {smtp['gateway']}")
            
            # Port
            port_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for field in port_fields:
                if field.get_attribute('value') in ['25', '587', '465']:
                    field.clear()
                    field.send_keys(str(smtp['port']))
                    print(f"  [OK] Port: {smtp['port']}")
                    break
            
            # Reply Address
            reply_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            reply_field.clear()
            reply_field.send_keys(smtp['reply_address'])
            print(f"  [OK] Reply Address: {smtp['reply_address']}")
            
            # SSL/TLS Dropdown
            ssl_selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
            if ssl_selects:
                ssl_select = Select(ssl_selects[0])
                ssl_select.select_by_value(smtp['use_ssl'])
                print(f"  [OK] SSL/TLS: {smtp['use_ssl']}")
            
            # Authentication Dropdown
            if len(ssl_selects) > 1:
                auth_select = Select(ssl_selects[1])
                auth_select.select_by_value(smtp['auth_method'])
                print(f"  [OK] Auth Method: {smtp['auth_method']}")
            
            # Device Userid
            userid_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for field in userid_fields:
                placeholder = field.get_attribute('placeholder')
                if placeholder and '@' in placeholder:
                    field.clear()
                    field.send_keys(creds['userid'])
                    print(f"  [OK] Device Userid: {creds['userid']}")
                    break
            
            # Device Password
            try:
                password_field = None
                all_password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                
                # Skip the first one (login password), use the last one (device password)
                if len(all_password_fields) >= 2:
                    password_field = all_password_fields[-1]
                elif len(all_password_fields) == 1:
                    # If only one password field after login, it's the device password
                    password_field = all_password_fields[0]
                
                if password_field:
                    password_field.clear()
                    password_field.send_keys(creds['password'])
                    print(f"  [OK] Device Password: {'*' * len(creds['password'])}")
                else:
                    print(f"  [WARNING] Could not find device password field")
                    
            except Exception as e:
                print(f"  [WARNING] Could not set device password: {e}")
            
            self._take_screenshot("02_config_filled")
            print("[SUCCESS] SMTP configuration filled")
            
        except Exception as e:
            print(f"[ERROR] Configuration failed: {e}")
            self._take_screenshot("error_config_failed")
            raise
    
    def test_connection(self):
        """Click Test Connection button and wait for results"""
        try:
            print("[INFO] Testing SMTP connection...")
            
            # Find and click Test Connection button
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if "test" in button.text.lower():
                    button.click()
                    break
            
            # Wait for test results
            time.sleep(3)
            
            # Check for success or failure
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            if "ALL TESTS PASSED" in body_text or "SUCCESSFUL" in body_text:
                print("[SUCCESS] SMTP connection test PASSED")
                self._take_screenshot("03_test_success")
                return True
            elif "FAILED" in body_text or "error" in body_text.lower():
                print("[ERROR] SMTP connection test FAILED")
                self._take_screenshot("03_test_failed")
                return False
            else:
                print("[WARNING] Test results unclear")
                self._take_screenshot("03_test_unknown")
                return None
                
        except Exception as e:
            print(f"[ERROR] Test connection failed: {e}")
            self._take_screenshot("error_test_failed")
            return False
    
    def submit_configuration(self):
        """Submit the configuration"""
        try:
            print("[INFO] Submitting configuration...")
            
            # Find and click Submit button
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if "submit" in button.text.lower():
                    button.click()
                    break
            
            time.sleep(2)
            self._take_screenshot("04_submitted")
            print("[SUCCESS] Configuration submitted successfully")
            
        except Exception as e:
            print(f"[ERROR] Submit failed: {e}")
            self._take_screenshot("error_submit_failed")
            raise
    
    def run(self, test_only=False, skip_test=False):
        """Execute the full configuration workflow"""
        try:
            print("\n" + "="*60)
            print("Sharp Printer SMTP Configuration Automation")
            print("="*60 + "\n")
            
            self.setup_driver()
            self.login()
            self.configure_smtp()
            
            if test_only:
                print("\n[TEST MODE] Testing connection without submitting")
                self.test_connection()
            elif skip_test:
                print("\n[WARNING] Skipping test (real printer mode)")
                self.submit_configuration()
                print("\n" + "="*60)
                print("[SUCCESS] CONFIGURATION SUBMITTED (without test)")
                print("[INFO] Verify SMTP works by sending a test scan")
                print("="*60)
            else:
                test_result = self.test_connection()
                
                if test_result:
                    self.submit_configuration()
                    print("\n" + "="*60)
                    print("[SUCCESS] CONFIGURATION COMPLETED SUCCESSFULLY")
                    print("="*60)
                else:
                    print("\n" + "="*60)
                    print("[WARNING] Configuration filled but NOT submitted due to test failure")
                    print("[INFO] Review the test results and try again")
                    print("="*60)
        
        except Exception as e:
            print(f"\n[ERROR] Automation failed: {e}")
            if self.config['settings'].get('screenshot_on_failure', True):
                self._take_screenshot("error_final")
        
        finally:
            if self.driver:
                time.sleep(2)
                self.driver.quit()
                print("\n[INFO] Browser closed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automate Sharp printer SMTP configuration"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Test connection without submitting configuration'
    )
    parser.add_argument(
        '--skip-test',
        action='store_true',
        help='Skip SMTP test (for real printers without test button)'
    )
    
    args = parser.parse_args()
    
    configurator = SharpPrinterConfigurator(args.config)
    configurator.run(test_only=args.test_only, skip_test=args.skip_test)


if __name__ == "__main__":
    main()