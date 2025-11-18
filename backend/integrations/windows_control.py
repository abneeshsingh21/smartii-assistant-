"""
Windows Device Control Integration
Allows SMARTII to control Windows desktop applications and settings
"""

import subprocess
import os
import re
import logging
from typing import Dict, Any, Optional, List
import winreg
import psutil
import json

logger = logging.getLogger(__name__)

class WindowsController:
    """Controls Windows desktop applications and settings"""
    
    def __init__(self):
        self.installed_apps = self._get_installed_apps()
        self.contacts_cache = {}
        logger.info(f"Windows Controller initialized - Found {len(self.installed_apps)} apps")
    
    def search_contact(self, name: str) -> Optional[str]:
        """
        Search for contact by name in Windows People/Outlook contacts
        Returns phone number if found
        """
        try:
            # Clean the search name - remove common filler words
            search_name = name.lower().strip()
            filler_words = ['to', 'message', 'send', 'whatsapp', 'on', 'via', 'using', 'the', 'a', 'an']
            for word in filler_words:
                # Remove word if it's at the start or standalone
                search_name = re.sub(rf'\b{word}\b\s*', '', search_name, flags=re.IGNORECASE).strip()
            
            if not search_name:
                logger.warning(f"Contact name empty after cleaning: {name}")
                return None
            
            logger.info(f"Searching for contact: '{name}' -> cleaned: '{search_name}'")
            
            # Try to read from Windows People (People app uses SQLite)
            import sqlite3
            people_db_path = os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.People_8wekyb3d8bbwe\LocalState\ContactStore.db")
            
            if os.path.exists(people_db_path):
                conn = sqlite3.connect(people_db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DisplayName, PhoneNumber FROM Contacts 
                    WHERE DisplayName LIKE ? COLLATE NOCASE
                """, (f"%{search_name}%",))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    logger.info(f"Found contact in Windows People: {result[0]} -> {result[1]}")
                    return result[1]  # phone number
            
            # Fallback: Try reading from CSV export or cached contacts
            contacts_file = os.path.join(os.path.dirname(__file__), "contacts.json")
            if os.path.exists(contacts_file):
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                    # Try exact match first
                    for contact in contacts:
                        contact_name = contact.get('name', '').lower()
                        if search_name == contact_name:
                            logger.info(f"Found exact match: {contact.get('name')} -> {contact.get('phone')}")
                            return contact.get('phone')
                    
                    # Try partial match
                    for contact in contacts:
                        contact_name = contact.get('name', '').lower()
                        if search_name in contact_name or contact_name in search_name:
                            logger.info(f"Found partial match: {contact.get('name')} -> {contact.get('phone')}")
                            return contact.get('phone')
            
            logger.warning(f"Contact not found: '{name}' (searched as: '{search_name}')")
            return None
            
        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return None
    
    def add_contact_manually(self, name: str, phone: str):
        """Add contact to manual cache (fallback)"""
        try:
            contacts_file = os.path.join(os.path.dirname(__file__), "contacts.json")
            contacts = []
            
            if os.path.exists(contacts_file):
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
            
            contacts.append({"name": name, "phone": phone})
            
            with open(contacts_file, 'w', encoding='utf-8') as f:
                json.dump(contacts, f, indent=2)
            
            logger.info(f"Added contact: {name} - {phone}")
            return True
        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            return False
    
    def _get_installed_apps(self) -> Dict[str, str]:
        """Get list of installed applications with their paths"""
        apps = {}
        
        # Common app locations
        common_apps = {
            "whatsapp": r"C:\Users\{}\AppData\Local\WhatsApp\WhatsApp.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "settings": "ms-settings:",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "wordpad": "write.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "snipping tool": "snippingtool.exe",
            "spotify": r"C:\Users\{}\AppData\Local\Microsoft\WindowsApps\Spotify.exe",
            "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        }
        
        username = os.getenv("USERNAME")
        for app_name, path in common_apps.items():
            if "{}" in path:
                path = path.format(username)
            apps[app_name] = path
        
        # Scan Windows Registry for installed apps
        try:
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in registry_paths:
                try:
                    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(registry_key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(registry_key, i)
                            subkey = winreg.OpenKey(registry_key, subkey_name)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                install_location = None
                                
                                try:
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                except:
                                    pass
                                
                                # Try to get executable path
                                try:
                                    display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                    if display_icon and display_icon.endswith(".exe"):
                                        app_key = display_name.lower()
                                        if app_key not in apps:
                                            apps[app_key] = display_icon.split(',')[0]  # Remove icon index if present
                                except:
                                    pass
                                
                                winreg.CloseKey(subkey)
                            except:
                                pass
                        except:
                            continue
                    winreg.CloseKey(registry_key)
                except:
                    continue
        except Exception as e:
            logger.warning(f"Could not scan registry for apps: {e}")
        
        logger.info(f"Found {len(apps)} installed applications")
        return apps
    
    def open_app(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application by name
        
        Args:
            app_name: Name of the app (e.g., "whatsapp", "chrome", "notepad", "spotify")
        
        Returns:
            Result dictionary with success status
        """
        try:
            app_name_lower = app_name.lower().strip()
            logger.info(f"Attempting to open app: {app_name_lower}")
            
            # Special handling for WhatsApp (Store app)
            if "whatsapp" in app_name_lower:
                try:
                    subprocess.Popen(["explorer.exe", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
                    logger.info(f"Opened WhatsApp via Store protocol")
                    return {"success": True, "message": "Opened WhatsApp", "app": "whatsapp"}
                except Exception as e:
                    logger.error(f"WhatsApp launch failed: {e}")
                    return {"success": False, "error": f"Failed to open WhatsApp: {str(e)}"}
            
            # Strategy 1: Check if app is in our registry
            if app_name_lower in self.installed_apps:
                path = self.installed_apps[app_name_lower]
                
                # Handle Windows settings URLs
                if path.startswith("ms-settings:"):
                    os.startfile(path)
                    logger.info(f"Opened settings: {app_name_lower}")
                    return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
                
                # Check if file exists
                if os.path.exists(path):
                    os.startfile(path)
                    logger.info(f"Opened app from path: {path}")
                    return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
                else:
                    # Try with shell for system commands
                    subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
                    logger.info(f"Opened app via cmd: {path}")
                    return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
            
            # Strategy 2: Search installed apps by partial name match
            for installed_app, path in self.installed_apps.items():
                if app_name_lower in installed_app or installed_app in app_name_lower:
                    try:
                        if path.startswith("ms-settings:") or os.path.exists(path):
                            os.startfile(path)
                        else:
                            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
                        logger.info(f"Opened app via partial match: {installed_app}")
                        return {"success": True, "message": f"Opened {installed_app}", "app": installed_app}
                    except:
                        continue
            
            # Strategy 3: Try as Windows Store app
            try:
                # Clean app name for Store protocol
                store_app_name = app_name_lower.replace(" ", "").replace("-", "").replace("_", "")
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{store_app_name}!App"])
                logger.info(f"Opened Store app: {app_name_lower}")
                return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
            except:
                pass
            
            # Strategy 4: Try as executable name
            try:
                os.startfile(app_name_lower + ".exe")
                logger.info(f"Opened as executable: {app_name_lower}.exe")
                return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
            except:
                pass
            
            # Strategy 5: Try with Windows start command (works for many apps)
            try:
                # Use cmd /c start for better compatibility without taskbar flash
                subprocess.Popen(["cmd", "/c", "start", "", app_name_lower], shell=False)
                logger.info(f"Opened via cmd start: {app_name_lower}")
                return {"success": True, "message": f"Opened {app_name}", "app": app_name_lower}
            except:
                pass
            
            # Strategy 6: Try to open as Windows protocol/URL
            if ":" in app_name or app_name.startswith("http"):
                os.startfile(app_name)
                return {"success": True, "message": f"Opened {app_name}"}
            
            logger.warning(f"Could not find app: {app_name_lower}")
            return {
                "success": False,
                "error": f"App '{app_name}' not found. Try saying the exact app name or checking if it's installed."
            }
            
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def open_website(self, url: str) -> Dict[str, Any]:
        """Open a website in default browser"""
        try:
            if not url.startswith("http"):
                url = "https://" + url
            
            subprocess.Popen(["start", url], shell=True)
            return {"success": True, "message": f"Opened {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_whatsapp_chat(self, phone_or_name: str, message: Optional[str] = None, auto_send: bool = True) -> Dict[str, Any]:
        """
        Open WhatsApp chat with optional pre-filled message
        
        Args:
            phone_or_name: Phone number with country code OR contact name
            message: Optional pre-filled message
            auto_send: If True, automatically press Enter to send (default: True)
        """
        try:
            # Check if it's a phone number or contact name
            phone_number = phone_or_name
            
            # If not a phone number (no digits or too short), search contacts
            if not phone_or_name.replace("+", "").replace(" ", "").isdigit():
                found_phone = self.search_contact(phone_or_name)
                if found_phone:
                    phone_number = found_phone
                    logger.info(f"Found contact {phone_or_name}: {phone_number}")
                else:
                    return {
                        "success": False,
                        "error": f"Contact '{phone_or_name}' not found. Use phone number like +911234567890"
                    }
            
            # Clean phone number
            phone_number = phone_number.replace(" ", "").replace("-", "")
            
            # Open WhatsApp chat using deep link (without pre-filled message)
            url = f"whatsapp://send?phone={phone_number}"
            
            try:
                # First open WhatsApp app
                subprocess.Popen(["explorer.exe", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
                # Wait a moment for app to initialize
                import time
                time.sleep(0.7)  # Reduced from 1.0
                # Then open the chat
                subprocess.Popen(["start", url], shell=True)
                logger.info(f"Opened WhatsApp desktop chat: {phone_number}")
                
                # Auto-type and send message if provided
                if message and auto_send:
                    # Wait for WhatsApp to load the chat
                    time.sleep(1.5)  # Reduced from 2.0
                    try:
                        import pyautogui
                        import pygetwindow as gw
                        
                        # Focus WhatsApp window
                        try:
                            whatsapp_windows = gw.getWindowsWithTitle('WhatsApp')
                            if whatsapp_windows:
                                whatsapp_windows[0].activate()
                                time.sleep(0.2)  # Reduced from 0.3
                        except Exception as e:
                            logger.warning(f"Could not focus WhatsApp window: {e}")
                        
                        # Click on the message input area (bottom of window)
                        # This ensures focus is in the text box
                        pyautogui.click()  # Click at current position (should be WhatsApp)
                        time.sleep(0.15)  # Reduced from 0.2
                        
                        # Type the message faster
                        pyautogui.write(message, interval=0.01)  # Reduced from 0.02
                        time.sleep(0.15)  # Reduced from 0.2
                        
                        # Press Enter to send
                        pyautogui.press('enter')
                        logger.info(f"Auto-typed and sent message to {phone_number}")
                        return {
                            "success": True,
                            "message": f"WhatsApp message sent to {phone_or_name}",
                            "phone": phone_number,
                            "auto_sent": True
                        }
                    except Exception as e:
                        logger.warning(f"Failed to auto-send: {e}")
                        return {
                            "success": True,
                            "message": f"Opened WhatsApp chat with {phone_or_name}, please type and send manually",
                            "phone": phone_number,
                            "auto_sent": False,
                            "error": str(e)
                        }
                
            except Exception as e:
                # Fallback to browser if desktop app fails
                logger.error(f"Desktop app failed: {e}")
                from urllib.parse import quote
                browser_url = f"https://wa.me/{phone_number}"
                if message:
                    browser_url += f"?text={quote(message)}"
                subprocess.Popen(["start", browser_url], shell=True)
                logger.warning(f"Fell back to browser for WhatsApp")
            
            return {
                "success": True,
                "message": f"Opened WhatsApp chat with {phone_or_name}",
                "phone": phone_number
            }
        except Exception as e:
            logger.error(f"WhatsApp chat open failed: {e}")
            return {"success": False, "error": str(e)}
    
    def whatsapp_call(self, phone_or_name: str, video: bool = False) -> Dict[str, Any]:
        """
        Make a WhatsApp voice or video call
        
        Args:
            phone_or_name: Phone number with country code OR contact name
            video: If True, make video call; if False, make voice call
        """
        try:
            # Check if it's a phone number or contact name
            phone_number = phone_or_name
            
            # If not a phone number, search contacts
            if not phone_or_name.replace("+", "").replace(" ", "").isdigit():
                found_phone = self.search_contact(phone_or_name)
                if found_phone:
                    phone_number = found_phone
                    logger.info(f"Found contact {phone_or_name}: {phone_number}")
                else:
                    return {
                        "success": False,
                        "error": f"Contact '{phone_or_name}' not found"
                    }
            
            # Clean phone number
            phone_number = phone_number.replace(" ", "").replace("-", "")
            
            # WhatsApp call deep link
            call_type = "video" if video else "voice"
            url = f"whatsapp://call?phone={phone_number}&video={str(video).lower()}"
            
            try:
                import time
                # First open WhatsApp app
                subprocess.Popen(["explorer.exe", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
                time.sleep(1.5)
                
                # Open the call using deep link
                subprocess.Popen(["start", url], shell=True)
                
                logger.info(f"Initiated WhatsApp {call_type} call to {phone_number}")
                return {
                    "success": True,
                    "message": f"WhatsApp {call_type} call initiated to {phone_or_name}",
                    "phone": phone_number,
                    "call_type": call_type
                }
            except Exception as e:
                logger.error(f"Failed to initiate call: {e}")
                return {
                    "success": False,
                    "error": f"Failed to initiate call: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"WhatsApp call failed: {e}")
            return {"success": False, "error": str(e)}
    
    def open_settings(self, setting_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Open Windows Settings
        
        Args:
            setting_type: Specific setting page (wifi, bluetooth, apps, etc.)
        """
        try:
            settings_urls = {
                "wifi": "ms-settings:network-wifi",
                "bluetooth": "ms-settings:bluetooth",
                "apps": "ms-settings:appsfeatures",
                "battery": "ms-settings:batterysaver",
                "display": "ms-settings:display",
                "sound": "ms-settings:sound",
                "notifications": "ms-settings:notifications",
                "privacy": "ms-settings:privacy",
                "update": "ms-settings:windowsupdate",
            }
            
            if setting_type and setting_type.lower() in settings_urls:
                url = settings_urls[setting_type.lower()]
            else:
                url = "ms-settings:"
            
            subprocess.Popen(["start", url], shell=True)
            return {"success": True, "message": f"Opened settings"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Run a PowerShell command (with user consent)
        
        Args:
            command: PowerShell command to execute
        """
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_running_apps(self) -> Dict[str, Any]:
        """Get list of currently running applications"""
        try:
            apps = []
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and not proc.info['name'].startswith('System'):
                        apps.append({
                            "name": proc.info['name'],
                            "pid": proc.info['pid']
                        })
                except:
                    continue
            
            return {"success": True, "apps": apps[:50]}  # Limit to 50
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close_app(self, app_name: str) -> Dict[str, Any]:
        """Close an application by name"""
        try:
            # Kill process by name
            subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"], 
                         capture_output=True)
            return {"success": True, "message": f"Closed {app_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
windows_controller = WindowsController()
