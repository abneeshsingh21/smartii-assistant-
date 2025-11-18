"""
WhatsApp Business API Integration
Allows SMARTII to send WhatsApp messages programmatically
"""

import logging
from typing import Dict, Any, Optional, List
import aiohttp
import os

logger = logging.getLogger(__name__)

class WhatsAppAPI:
    """WhatsApp Business API integration"""
    
    def __init__(self):
        # WhatsApp Business API credentials (user needs to configure)
        self.api_key = os.getenv("WHATSAPP_API_KEY", "")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_ID", "")
        self.base_url = "https://graph.facebook.com/v18.0"
        self.enabled = bool(self.api_key and self.phone_number_id)
        
        if not self.enabled:
            logger.warning("WhatsApp API not configured - set WHATSAPP_API_KEY and WHATSAPP_PHONE_ID")
    
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Business API
        
        Args:
            to: Phone number with country code (e.g., "911234567890")
            message: Message text
        
        Returns:
            Result dictionary
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "WhatsApp API not configured",
                "fallback": "desktop"
            }
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "message_id": data.get("messages", [{}])[0].get("id"),
                            "method": "api"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"WhatsApp API error: {error_text}")
                        return {"success": False, "error": error_text}
        
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_media(self, to: str, media_url: str, media_type: str = "image") -> Dict[str, Any]:
        """Send media via WhatsApp API"""
        if not self.enabled:
            return {"success": False, "error": "WhatsApp API not configured"}
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: {"link": media_url}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "message_id": data.get("messages", [{}])[0].get("id")}
                    else:
                        return {"success": False, "error": await response.text()}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_setup_instructions(self) -> Dict[str, Any]:
        """Get instructions for setting up WhatsApp Business API"""
        return {
            "instructions": [
                "1. Create Meta (Facebook) Business Account at business.facebook.com",
                "2. Go to developers.facebook.com and create an app",
                "3. Add 'WhatsApp' product to your app",
                "4. Get permanent access token from WhatsApp > API Setup",
                "5. Get Phone Number ID from WhatsApp > API Setup",
                "6. Set environment variables:",
                "   - WHATSAPP_API_KEY=<your_access_token>",
                "   - WHATSAPP_PHONE_ID=<your_phone_number_id>",
                "7. Restart SMARTII backend"
            ],
            "documentation": "https://developers.facebook.com/docs/whatsapp/cloud-api/get-started",
            "pricing": "First 1000 conversations/month are free"
        }


# Global instance
whatsapp_api = WhatsAppAPI()
