"""
Smart Clipboard Manager for SMARTII
Tracks clipboard history and enables intelligent paste operations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pyperclip
import time
import threading
import json
import os

logger = logging.getLogger(__name__)


class ClipboardManager:
    """Smart clipboard manager with history tracking"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history = []
        self.current_clipboard = ""
        self.is_monitoring = False
        self.monitor_thread = None
        self.history_file = "./data/clipboard_history.json"
        
        # Create data directory
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        # Load existing history
        self._load_history()
    
    def _load_history(self):
        """Load clipboard history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                logger.info(f"Loaded {len(self.history)} clipboard entries")
        except Exception as e:
            logger.error(f"Error loading clipboard history: {e}")
            self.history = []
    
    def _save_history(self):
        """Save clipboard history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving clipboard history: {e}")
    
    def start_monitoring(self):
        """Start monitoring clipboard changes"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
            self.monitor_thread.start()
            logger.info("Clipboard monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring clipboard"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Clipboard monitoring stopped")
    
    def _monitor_clipboard(self):
        """Monitor clipboard for changes"""
        try:
            self.current_clipboard = pyperclip.paste()
            
            while self.is_monitoring:
                try:
                    clipboard_content = pyperclip.paste()
                    
                    # Check if clipboard changed
                    if clipboard_content and clipboard_content != self.current_clipboard:
                        self.current_clipboard = clipboard_content
                        self._add_to_history(clipboard_content)
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    logger.debug(f"Clipboard monitoring error: {e}")
                    time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Fatal clipboard monitoring error: {e}")
            self.is_monitoring = False
    
    def _add_to_history(self, content: str):
        """Add item to clipboard history"""
        try:
            # Don't add empty or very long content
            if not content or len(content) > 10000:
                return
            
            # Don't add duplicates of the most recent item
            if self.history and self.history[0]["content"] == content:
                return
            
            entry = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "length": len(content),
                "type": self._detect_content_type(content)
            }
            
            # Add to beginning
            self.history.insert(0, entry)
            
            # Limit history size
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]
            
            # Save to file
            self._save_history()
            
            logger.debug(f"Added clipboard entry: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error adding to clipboard history: {e}")
    
    def _detect_content_type(self, content: str) -> str:
        """Detect type of clipboard content"""
        try:
            content_lower = content.lower().strip()
            
            # URL
            if content_lower.startswith(('http://', 'https://', 'www.')):
                return "url"
            
            # Email
            if '@' in content and '.' in content.split('@')[1] if '@' in content else False:
                return "email"
            
            # Phone number
            if any(char.isdigit() for char in content) and len(content.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
                digits_only = ''.join(filter(str.isdigit, content))
                if 10 <= len(digits_only) <= 15:
                    return "phone"
            
            # Code (has brackets, semicolons, etc.)
            code_indicators = ['{', '}', '()', ';', 'function', 'def ', 'class ', 'import ', 'const ', 'let ', 'var ']
            if any(indicator in content for indicator in code_indicators):
                return "code"
            
            # Path
            if '\\' in content or ('/' in content and not ' ' in content):
                return "path"
            
            # JSON
            if content.strip().startswith(('{', '[')):
                try:
                    json.loads(content)
                    return "json"
                except:
                    pass
            
            # Default to text
            return "text"
            
        except:
            return "text"
    
    def get_history(self, limit: int = 10, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get clipboard history"""
        try:
            history = self.history
            
            # Filter by type
            if content_type:
                history = [entry for entry in history if entry.get("type") == content_type]
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting clipboard history: {e}")
            return []
    
    def get_item_by_index(self, index: int) -> Optional[str]:
        """Get clipboard item by index (0 = most recent)"""
        try:
            if 0 <= index < len(self.history):
                return self.history[index]["content"]
            return None
        except Exception as e:
            logger.error(f"Error getting clipboard item: {e}")
            return None
    
    def copy_to_clipboard(self, content: str) -> Dict[str, Any]:
        """Copy content to clipboard"""
        try:
            pyperclip.copy(content)
            self.current_clipboard = content
            
            return {
                "success": True,
                "message": "Content copied to clipboard",
                "length": len(content)
            }
            
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def paste_from_history(self, index: int) -> Dict[str, Any]:
        """Paste item from history"""
        try:
            content = self.get_item_by_index(index)
            
            if content:
                pyperclip.copy(content)
                self.current_clipboard = content
                
                return {
                    "success": True,
                    "message": f"Pasted item from {index + 1} items ago",
                    "content": content
                }
            else:
                return {
                    "success": False,
                    "error": "Item not found in history"
                }
                
        except Exception as e:
            logger.error(f"Error pasting from history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search clipboard history"""
        try:
            query_lower = query.lower()
            results = []
            
            for entry in self.history:
                if query_lower in entry["content"].lower():
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching clipboard history: {e}")
            return []
    
    def clear_history(self) -> Dict[str, Any]:
        """Clear clipboard history"""
        try:
            self.history = []
            self._save_history()
            
            return {
                "success": True,
                "message": "Clipboard history cleared"
            }
            
        except Exception as e:
            logger.error(f"Error clearing clipboard history: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
_clipboard_manager = None


def get_clipboard_manager() -> ClipboardManager:
    """Get or create global clipboard manager instance"""
    global _clipboard_manager
    if _clipboard_manager is None:
        _clipboard_manager = ClipboardManager()
        _clipboard_manager.start_monitoring()
    return _clipboard_manager
