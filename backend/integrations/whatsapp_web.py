"""
WhatsApp Web Automation using Selenium
Background message sending without opening WhatsApp desktop app
"""

import os
import time
import logging
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class WhatsAppWeb:
    """WhatsApp Web automation for background messaging"""
    
    def __init__(self):
        self.driver = None
        self.session_file = os.path.join(os.path.dirname(__file__), "whatsapp_session")
        self.initialized = False
        
    def start_session(self, headless: bool = True):
        """Start WhatsApp Web session"""
        try:
            chrome_options = Options()
            
            # Only use user-data-dir if not headless (avoid conflicts)
            if not headless:
                chrome_options.add_argument(f"user-data-dir={self.session_file}")
            
            # Headless mode options
            if headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
            
            # Essential stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Reduce verbosity
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(30)
            except Exception as driver_error:
                logger.error(f"Chrome driver failed: {driver_error}")
                # Fallback: Try without remote debugging port
                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                if headless:
                    chrome_options.add_argument("--headless")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Open WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            logger.info("WhatsApp Web session started")
            
            # Wait for WhatsApp to load
            time.sleep(5)
            
            # Check if QR code is present (first time setup)
            try:
                qr_code = self.driver.find_element(By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']")
                logger.warning("QR code detected - please scan QR code to login")
                self.initialized = False
                return {"success": False, "message": "QR code scan required", "qr_present": True}
            except:
                # Already logged in
                logger.info("WhatsApp Web already authenticated")
                self.initialized = True
                return {"success": True, "message": "Session ready"}
                
        except Exception as e:
            logger.error(f"Failed to start WhatsApp Web session: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return {"success": False, "error": str(e)}
    
    def send_message(self, phone_or_name: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message via web interface"""
        try:
            if not self.driver or not self.initialized:
                result = self.start_session(headless=True)
                if not result.get("success"):
                    return result
            
            # Resolve contact name to phone number
            phone = phone_or_name
            if not phone_or_name.replace("+", "").replace(" ", "").replace("-", "").isdigit():
                # Import here to avoid circular dependency
                try:
                    from .windows_control import windows_controller
                    found_phone = windows_controller.search_contact(phone_or_name)
                    if found_phone:
                        phone = found_phone
                        logger.info(f"Resolved {phone_or_name} to {phone}")
                    else:
                        return {"success": False, "error": f"Contact '{phone_or_name}' not found"}
                except Exception as e:
                    logger.warning(f"Could not resolve contact: {e}")
                    return {"success": False, "error": f"Contact '{phone_or_name}' not found"}
            
            # Clean phone number
            phone = phone.replace(" ", "").replace("-", "").replace("+", "")
            
            # Open chat via URL
            from urllib.parse import quote
            chat_url = f"https://web.whatsapp.com/send?phone={phone}&text={quote(message)}"
            self.driver.get(chat_url)
            
            # Wait for message box to load
            try:
                message_box = WebDriverWait(self.driver, 10).until(  # Reduced from 15
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                )
                
                # Wait for message to pre-fill and send button to appear
                time.sleep(0.5)  # Reduced from 0.8 seconds
                
                # Try multiple selectors for send button (WhatsApp updates their UI frequently)
                send_button = None
                selectors = [
                    '//button[@aria-label="Send"]',
                    '//span[@data-icon="send"]',
                    '//button[contains(@class, "send")]//span[@data-icon="send"]',
                    '//div[@role="button" and @aria-label="Send"]'
                ]
                
                for selector in selectors:
                    try:
                        send_button = WebDriverWait(self.driver, 3).until(  # Reduced from 5
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue
                
                if send_button:
                    send_button.click()
                    time.sleep(0.5)  # Reduced from 1 second
                    logger.info(f"Message sent to {phone_or_name}")
                    return {
                        "success": True,
                        "message": f"Message sent to {phone_or_name}",
                        "method": "whatsapp_web"
                    }
                else:
                    # Fallback: press Enter key
                    message_box.send_keys('\n')
                    time.sleep(0.5)  # Reduced from 1 second
                    logger.info(f"Message sent to {phone_or_name} (via Enter key)")
                    return {
                        "success": True,
                        "message": f"Message sent to {phone_or_name}",
                        "method": "whatsapp_web"
                    }
                
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                return {
                    "success": False,
                    "error": f"Contact not found or message failed: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"WhatsApp Web error: {e}")
            return {"success": False, "error": str(e)}
    
    def close_session(self):
        """Close WhatsApp Web session"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.initialized = False
                logger.info("WhatsApp Web session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")


# Global instance
whatsapp_web = WhatsAppWeb()
