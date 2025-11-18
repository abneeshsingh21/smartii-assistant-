"""
Multi-Language Translation Support for SMARTII
Provides translation between multiple languages
"""

import logging
from typing import Dict, Any, Optional
from googletrans import Translator

logger = logging.getLogger(__name__)


class LanguageTranslator:
    """Multi-language translation support"""
    
    def __init__(self):
        try:
            self.translator = Translator()
            self.enabled = True
            
            # Supported languages
            self.languages = {
                'en': 'English',
                'hi': 'Hindi',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh-cn': 'Chinese (Simplified)',
                'ar': 'Arabic'
            }
            
            logger.info("Language translator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            self.enabled = False
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> Dict[str, Any]:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_lang: Target language code (en, hi, es, etc.)
            source_lang: Source language code (auto for auto-detection)
            
        Returns:
            Translation result with detected source language
        """
        try:
            if not self.enabled:
                return {
                    "success": False,
                    "error": "Translation service not available"
                }
            
            logger.info(f"Translating '{text[:50]}...' to {target_lang}")
            
            # Normalize language codes
            target_lang = target_lang.lower().strip()
            
            # Translate
            result = self.translator.translate(text, dest=target_lang, src=source_lang)
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": result.text,
                "source_language": result.src,
                "source_language_name": self.languages.get(result.src, result.src),
                "target_language": target_lang,
                "target_language_name": self.languages.get(target_lang, target_lang),
                "pronunciation": result.pronunciation if hasattr(result, 'pronunciation') else None
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": f"Translation failed: {str(e)}"
            }
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text"""
        try:
            if not self.enabled:
                return {
                    "success": False,
                    "error": "Translation service not available"
                }
            
            result = self.translator.detect(text)
            
            return {
                "success": True,
                "language": result.lang,
                "language_name": self.languages.get(result.lang, result.lang),
                "confidence": result.confidence
            }
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.languages


# Global instance
_language_translator = None


def get_language_translator() -> LanguageTranslator:
    """Get or create global translator instance"""
    global _language_translator
    if _language_translator is None:
        _language_translator = LanguageTranslator()
    return _language_translator
