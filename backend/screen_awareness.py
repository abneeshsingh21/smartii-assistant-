"""
SMARTII Screen Content Awareness
Uses OCR and Vision AI to understand what's on screen
"""

import os
import base64
from typing import Dict, List, Optional
import logging
from PIL import ImageGrab, Image
import io

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available - OCR features disabled")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python not available - image processing limited")


class ScreenAwareness:
    def __init__(self):
        self.last_screenshot = None
        self.screenshot_history = []
        self.max_history = 10
        
    async def capture_screen(self, region: Optional[tuple] = None) -> Image.Image:
        """Capture screenshot of entire screen or specific region"""
        try:
            if region:
                # Capture specific region (x, y, width, height)
                screenshot = ImageGrab.grab(bbox=region)
            else:
                # Capture entire screen
                screenshot = ImageGrab.grab()
                
            self.last_screenshot = screenshot
            self._add_to_history(screenshot)
            
            return screenshot
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
            
    def _add_to_history(self, screenshot: Image.Image):
        """Add screenshot to history (for comparison)"""
        self.screenshot_history.append({
            "timestamp": datetime.now().isoformat(),
            "image": screenshot
        })
        
        # Keep only last N screenshots
        if len(self.screenshot_history) > self.max_history:
            self.screenshot_history.pop(0)
            
    async def extract_text_from_screen(self, region: Optional[tuple] = None) -> str:
        """Extract text from screen using OCR"""
        if not TESSERACT_AVAILABLE:
            return "OCR not available. Install pytesseract: pip install pytesseract"
            
        try:
            screenshot = await self.capture_screen(region)
            if not screenshot:
                return ""
                
            # Perform OCR
            text = pytesseract.image_to_string(screenshot)
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return f"Error extracting text: {str(e)}"
            
    async def analyze_screen_content(self, task: str) -> Dict:
        """Analyze screen content based on specific task"""
        screenshot = await self.capture_screen()
        
        if not screenshot:
            return {"error": "Failed to capture screen"}
            
        result = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }
        
        if task == "summarize":
            text = await self.extract_text_from_screen()
            result["analysis"]["text"] = text
            result["analysis"]["summary"] = self._generate_summary(text)
            
        elif task == "find_errors":
            text = await self.extract_text_from_screen()
            errors = self._detect_errors(text)
            result["analysis"]["errors"] = errors
            
        elif task == "extract_data":
            text = await self.extract_text_from_screen()
            data = self._extract_structured_data(text)
            result["analysis"]["data"] = data
            
        elif task == "read_code":
            text = await self.extract_text_from_screen()
            code_analysis = self._analyze_code(text)
            result["analysis"]["code"] = code_analysis
            
        return result
        
    def _generate_summary(self, text: str) -> str:
        """Generate summary of text"""
        if not text:
            return "No text found on screen"
            
        # Simple extractive summary (first few sentences)
        sentences = text.split('.')[:3]
        summary = '. '.join(sentences).strip()
        
        return summary if summary else "Unable to generate summary"
        
    def _detect_errors(self, text: str) -> List[str]:
        """Detect potential errors in text"""
        errors = []
        error_keywords = [
            'error', 'exception', 'failed', 'warning',
            'traceback', 'syntax error', 'undefined',
            'null pointer', 'segmentation fault'
        ]
        
        text_lower = text.lower()
        for keyword in error_keywords:
            if keyword in text_lower:
                # Find lines containing errors
                lines = text.split('\n')
                for line in lines:
                    if keyword in line.lower():
                        errors.append(line.strip())
                        
        return errors if errors else ["No errors detected"]
        
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract structured data (numbers, dates, emails, etc.)"""
        import re
        
        data = {
            "numbers": [],
            "emails": [],
            "dates": [],
            "urls": []
        }
        
        # Extract numbers (currency, percentages, etc.)
        numbers = re.findall(r'\$?[\d,]+\.?\d*%?', text)
        data["numbers"] = numbers[:10]  # Limit to 10
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        data["emails"] = emails
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        data["urls"] = urls
        
        # Extract dates
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)
        data["dates"] = dates
        
        return data
        
    def _analyze_code(self, text: str) -> Dict:
        """Analyze code on screen"""
        analysis = {
            "language": "unknown",
            "line_count": 0,
            "has_functions": False,
            "has_classes": False,
            "imports": []
        }
        
        lines = text.split('\n')
        analysis["line_count"] = len(lines)
        
        # Detect language
        if 'def ' in text or 'import ' in text:
            analysis["language"] = "Python"
        elif 'function ' in text or 'const ' in text or 'let ' in text:
            analysis["language"] = "JavaScript"
        elif 'public class' in text or 'private ' in text:
            analysis["language"] = "Java"
            
        # Detect functions
        analysis["has_functions"] = 'def ' in text or 'function ' in text
        
        # Detect classes
        analysis["has_classes"] = 'class ' in text
        
        # Extract imports (Python)
        import_lines = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
        analysis["imports"] = import_lines[:5]  # First 5 imports
        
        return analysis
        
    async def find_on_screen(self, search_term: str) -> Dict:
        """Find specific text or element on screen"""
        text = await self.extract_text_from_screen()
        
        if search_term.lower() in text.lower():
            # Find context around the search term
            lines = text.split('\n')
            matches = []
            
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Get surrounding context (previous and next line)
                    context = []
                    if i > 0:
                        context.append(lines[i-1])
                    context.append(line)
                    if i < len(lines) - 1:
                        context.append(lines[i+1])
                        
                    matches.append({
                        "line_number": i + 1,
                        "context": '\n'.join(context)
                    })
                    
            return {
                "found": True,
                "matches": matches,
                "total_matches": len(matches)
            }
        else:
            return {
                "found": False,
                "message": f"'{search_term}' not found on screen"
            }
            
    async def get_active_window_info(self) -> Dict:
        """Get information about active window"""
        try:
            if os.name == 'nt':  # Windows
                import win32gui
                import win32process
                import psutil
                
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                
                return {
                    "window_title": window_title,
                    "process_name": process.name(),
                    "pid": pid
                }
            else:
                return {"error": "Active window detection only supported on Windows"}
                
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return {"error": str(e)}
            
    def screenshot_to_base64(self, screenshot: Image.Image) -> str:
        """Convert screenshot to base64 string"""
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

from datetime import datetime

# Global instance
screen_awareness = ScreenAwareness()

async def analyze_screen(task: str = "summarize") -> Dict:
    """Analyze current screen content"""
    return await screen_awareness.analyze_screen_content(task)

async def extract_screen_text(region: Optional[tuple] = None) -> str:
    """Extract text from screen"""
    return await screen_awareness.extract_text_from_screen(region)

async def find_on_screen(search_term: str) -> Dict:
    """Find text on screen"""
    return await screen_awareness.find_on_screen(search_term)
