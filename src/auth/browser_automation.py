"""
Automated browser login for Zerodha Kite Connect.

⚠️ SECURITY WARNING ⚠️
This module handles sensitive credentials and performs automated login.
Use with extreme caution and ensure your .env file is properly secured.
"""

import time
import pyotp
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
from ..utils.config import config


class ZerodhaAutomatedLogin:
    """
    Handles fully automated Zerodha login using Selenium and TOTP.
    
    ⚠️ SECURITY RISK: This class stores and uses sensitive credentials.
    Only use in secure environments and ensure proper credential management.
    """
    
    def __init__(self):
        """Initialize the automated login handler."""
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
        # Validate full automation credentials
        if not config.validate_full_automation():
            raise ValueError("Full automation credentials not configured. Check your .env file.")
        
        self.username = config.zerodha_username
        self.password = config.zerodha_password
        self.pin = config.zerodha_pin
        self.totp_secret = config.zerodha_totp_secret
        self.headless = config.headless_browser
        self.timeout = config.browser_timeout
        
        logger.info("ZerodhaAutomatedLogin initialized")
    
    def _setup_browser(self) -> webdriver.Chrome:
        """
        Set up Chrome browser with appropriate options.
        
        Returns:
            Configured Chrome WebDriver instance.
        """
        try:
            # Chrome options
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Additional options for stability
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            # Don't disable JavaScript as Zerodha needs it
            
            # User agent to avoid detection
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Set up Chrome driver with WebDriver Manager
            try:
                # Get the driver path and ensure it's the correct executable
                driver_path = ChromeDriverManager().install()
                
                # Fix path if it points to wrong file (common issue on Mac)
                if "THIRD_PARTY_NOTICES" in driver_path or not driver_path.endswith("chromedriver"):
                    import os
                    driver_dir = os.path.dirname(driver_path)
                    actual_driver = os.path.join(driver_dir, "chromedriver")
                    if os.path.exists(actual_driver):
                        driver_path = actual_driver
                        # Make sure it's executable
                        os.chmod(driver_path, 0o755)
                    else:
                        # Try to find chromedriver in the same directory
                        for file in os.listdir(driver_dir):
                            if file == "chromedriver":
                                driver_path = os.path.join(driver_dir, file)
                                os.chmod(driver_path, 0o755)
                                break
                
                logger.info(f"Using Chrome driver: {driver_path}")
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
            except Exception as e:
                logger.error(f"Failed to setup Chrome driver with WebDriver Manager: {e}")
                # Fallback: try system chromedriver
                logger.info("Trying system chromedriver...")
                driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation indicators
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set up wait
            self.wait = WebDriverWait(driver, self.timeout)
            
            logger.info("Browser setup completed successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            raise
    
    def _generate_totp(self) -> str:
        """
        Generate TOTP code for 2FA authentication.
        
        Returns:
            6-digit TOTP code.
        """
        try:
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            logger.info("TOTP code generated successfully")
            return code
        except Exception as e:
            logger.error(f"Failed to generate TOTP: {e}")
            raise
    
    def _wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for an element to be present and visible.
        
        Args:
            by: Selenium By locator type.
            value: Locator value.
            timeout: Custom timeout (uses default if None).
            
        Returns:
            True if element found, False otherwise.
        """
        try:
            wait_time = timeout or self.timeout
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            logger.warning(f"Element not found: {by}={value}")
            return False
    
    def _fill_login_form(self) -> bool:
        """
        Fill the Zerodha login form with credentials.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.info("Filling login form...")
            
            # Wait for the page to load completely
            time.sleep(3)
            
            # Wait for and fill username using the correct XPath
            try:
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="userid"]'))
                )
                logger.info("Found username field using XPath")
            except Exception as e:
                logger.error(f"Username field not found with XPath: {e}")
                return False
            
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(self.username)
            logger.info("Username entered")
            
            # Fill password using XPath
            try:
                password_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
                )
                logger.info("Found password field using XPath")
            except Exception as e:
                logger.error(f"Password field not found with XPath: {e}")
                return False
            
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(self.password)
            logger.info("Password entered")
            
            # Wait a bit before clicking login
            time.sleep(1)
            
            # Click login button using XPath (try common login button XPaths)
            login_xpaths = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Login')]",
                "//*[@class='button-orange']",
                "//form//button[1]"  # First button in form
            ]
            
            login_button = None
            for xpath in login_xpaths:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"Found login button using XPath: {xpath}")
                    break
                except:
                    continue
            
            if not login_button:
                logger.error("Login button not found with any XPath")
                return False
            
            login_button.click()
            logger.info("Login button clicked")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill login form: {e}")
            return False
    
    def _handle_2fa(self) -> bool:
        """
        Handle 2FA authentication using TOTP.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.info("Handling 2FA authentication...")
            
            # Wait for page transition (reduced by 50% for faster login)
            logger.info("Waiting for 2FA page to load completely...")
            time.sleep(4)  # Reduced from 8 to 4 seconds
            
            # Try to find TOTP field using XPaths (exact XPath first)
            totp_xpaths = [
                '/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input',  # Exact XPath provided by user
                '//*[@id="totp"]',
                '//*[@name="totp"]', 
                '//input[@placeholder="TOTP"]',
                '//input[contains(@placeholder, "TOTP")]',
                '//input[contains(@placeholder, "OTP")]',
                '//input[contains(@placeholder, "authenticator")]',
                '//input[@type="text" and contains(@class, "totp")]',
                '//input[@type="password" and contains(@class, "totp")]',
                '//form//input[@type="text"][2]',  # Second text input (after username)
                '//div[contains(@class, "twofa")]//input'
            ]
            
            # Store the successful XPath for reuse
            successful_totp_xpath = None
            max_wait_time = 15  # Reasonable wait time
            
            for xpath in totp_xpaths:
                try:
                    logger.info(f"Trying TOTP XPath: {xpath}")
                    totp_field = WebDriverWait(self.driver, max_wait_time).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"Found TOTP field with XPath: {xpath}")
                    successful_totp_xpath = xpath
                    break
                except Exception as e:
                    logger.debug(f"XPath {xpath} failed: {e}")
                    continue
            
            if not successful_totp_xpath:
                logger.warning("TOTP field not found after trying all XPaths")
                # Take screenshot for debugging
                try:
                    self.driver.save_screenshot("totp_page_debug.png")
                    logger.info("Screenshot saved as totp_page_debug.png")
                except:
                    pass
                return self._handle_pin()
            
            # Generate TOTP with retry logic
            max_totp_attempts = 3
            for attempt in range(max_totp_attempts):
                try:
                    totp_code = self._generate_totp()
                    logger.info(f"Generated TOTP code (attempt {attempt + 1}): {totp_code}")
                    
                    # Re-find the element to avoid stale element issues
                    totp_field = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, successful_totp_xpath))
                    )
                    
                    # Clear field and wait
                    totp_field.clear()
                    time.sleep(0.5)  # Reduced from 1 to 0.5 seconds
                    
                    # Enter TOTP character by character for better reliability
                    for char in totp_code:
                        totp_field.send_keys(char)
                        time.sleep(0.025)  # Reduced by another 50% to 0.025 seconds
                    
                    logger.info("TOTP code entered successfully")
                    
                    # Wait before clicking continue
                    time.sleep(1)  # Reduced from 2 to 1 second
                    
                    # Find and click continue button with XPaths
                    continue_xpaths = [
                        "//button[@type='submit']",
                        "//input[@type='submit']",
                        "//button[contains(text(), 'Continue')]",
                        "//input[@value='Continue']",
                        "//*[@class='button-orange']",
                        "//form//button",
                        "//div[contains(@class, 'twofa')]//button",
                        "//button[1]"  # First button on page
                    ]
                    
                    continue_button = None
                    for xpath in continue_xpaths:
                        try:
                            continue_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xpath))
                            )
                            logger.info(f"Found continue button with XPath: {xpath}")
                            break
                        except:
                            continue
                    
                    if not continue_button:
                        logger.error("Continue button not found")
                        if attempt < max_totp_attempts - 1:
                            logger.info("Retrying TOTP entry...")
                            continue
                        return False
                    
                    # Click continue button
                    continue_button.click()
                    logger.info("2FA continue button clicked")
                    
                    # Wait for page transition and check for callback
                    time.sleep(2)  # Wait 2 seconds to check for callback
                    
                    # Check if we moved to next page (success) or still on TOTP page (retry needed)
                    current_url = self.driver.current_url
                    if "totp" not in current_url.lower() and "2fa" not in current_url.lower():
                        logger.info("Successfully moved past 2FA page")
                        return True
                    else:
                        logger.warning(f"Still on 2FA page (attempt {attempt + 1}), URL: {current_url}")
                        if attempt < max_totp_attempts - 1:
                            logger.info("TOTP may be incorrect or expired, generating new one...")
                            time.sleep(1)  # Reduced from 2 to 1 second
                            continue
                    
                except Exception as e:
                    logger.error(f"TOTP attempt {attempt + 1} failed: {e}")
                    if attempt < max_totp_attempts - 1:
                        time.sleep(1)  # Reduced from 2 to 1 second
                        continue
                    return False
            
            logger.error("All TOTP attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"Failed to handle 2FA: {e}")
            return False
    
    def _handle_pin(self) -> bool:
        """
        Handle PIN entry (if required).
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.info("Handling PIN entry...")
            
            # Wait for page transition
            time.sleep(3)
            
            # Try to find PIN field with XPaths
            pin_xpaths = [
                '//*[@id="pin"]',
                '//*[@name="pin"]', 
                '//input[@placeholder="PIN"]',
                '//input[contains(@placeholder, "PIN")]',
                '//input[@type="password" and contains(@placeholder, "pin")]',
                '//input[@type="password"][last()]'  # Last password field
            ]
            
            pin_field = None
            
            for xpath in pin_xpaths:
                try:
                    pin_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    logger.info(f"Found PIN field with XPath: {xpath}")
                    break
                except:
                    continue
            
            if not pin_field:
                logger.info("No PIN field found - may not be required")
                return True
            
            # Enter PIN
            pin_field.clear()
            time.sleep(0.5)
            pin_field.send_keys(self.pin)
            logger.info("PIN entered")
            
            # Wait a bit before clicking continue
            time.sleep(1)
            
            # Click continue button with multiple selectors
            continue_selectors = [
                "button[type='submit']",
                ".button-orange",
                "[value='Continue']",
                "button:contains('Continue')",
                ".pin-form button"
            ]
            
            continue_button = None
            for selector in continue_selectors:
                try:
                    continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not continue_button:
                logger.error("Continue button not found")
                return False
            
            continue_button.click()
            logger.info("PIN continue button clicked")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle PIN: {e}")
            return False
    
    def _wait_for_callback(self, callback_url_base: str) -> Optional[str]:
        """
        Wait for redirect to callback URL and extract request token.
        
        Args:
            callback_url_base: Base callback URL to wait for.
            
        Returns:
            Full callback URL if successful, None otherwise.
        """
        try:
            logger.info("Waiting for callback URL...")
            
            # Check if we're already on callback page
            current_url = self.driver.current_url
            if callback_url_base in current_url and "request_token=" in current_url:
                logger.info("Already on callback URL!")
                return current_url
            
            # Wait for URL to change to callback with longer timeout
            start_time = time.time()
            extended_timeout = self.timeout + 30  # Add extra 30 seconds
            
            while time.time() - start_time < extended_timeout:
                current_url = self.driver.current_url
                logger.debug(f"Current URL: {current_url}")
                
                # Check for callback URL
                if callback_url_base in current_url and "request_token=" in current_url:
                    logger.info("Callback URL received successfully")
                    return current_url
                
                # Check if we're on an error page
                if "error" in current_url.lower():
                    logger.error(f"Error page detected: {current_url}")
                    try:
                        self.driver.save_screenshot("error_page_debug.png")
                        logger.info("Error page screenshot saved")
                    except:
                        pass
                    return None
                
                # Check for common success indicators
                if any(indicator in current_url.lower() for indicator in ['success', 'authorized', 'complete']):
                    logger.info(f"Possible success page detected: {current_url}")
                    # Continue waiting for actual callback
                
                time.sleep(1)  # Increased check interval
            
            logger.error(f"Callback URL timeout after {extended_timeout} seconds")
            logger.error(f"Final URL: {current_url}")
            
            # Take final screenshot for debugging
            try:
                self.driver.save_screenshot("callback_timeout_debug.png")
                logger.info("Timeout screenshot saved")
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to wait for callback: {e}")
            return None
    
    def perform_automated_login(self, login_url: str, callback_url_base: str) -> Optional[str]:
        """
        Perform complete automated login flow.
        
        Args:
            login_url: Kite Connect login URL.
            callback_url_base: Expected callback URL base.
            
        Returns:
            Callback URL with request token if successful, None otherwise.
        """
        try:
            logger.info("Starting automated login process")
            
            # Setup browser
            self.driver = self._setup_browser()
            
            # Navigate to login URL
            logger.info(f"Navigating to login URL: {login_url}")
            self.driver.get(login_url)
            
            # Fill login form
            if not self._fill_login_form():
                raise Exception("Failed to fill login form")
            
            # Handle 2FA
            logger.info("Waiting for 2FA page...")
            time.sleep(4)  # Reduced from 8 to 4 seconds
            if not self._handle_2fa():
                logger.warning("2FA handling failed, continuing to PIN check...")
            
            # Handle PIN (if required)
            logger.info("Checking for PIN page...")
            time.sleep(2.5)  # Reduced from 5 to 2.5 seconds
            if not self._handle_pin():
                logger.warning("PIN handling failed, continuing to callback check...")
            
            # Wait for callback URL
            callback_url = self._wait_for_callback(callback_url_base)
            
            if callback_url:
                logger.info("Automated login completed successfully")
                return callback_url
            else:
                raise Exception("Failed to receive callback URL")
                
        except Exception as e:
            logger.error(f"Automated login failed: {e}")
            return None
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Browser cleanup failed: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self._cleanup()
