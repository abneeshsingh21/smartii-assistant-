"""
SMARTII Voice Processor - Speech Recognition and Synthesis
Handles wake word detection, STT, TTS, and voice activity detection.
"""

import logging
import asyncio
import io
import base64
from typing import Optional, Dict, Any, List
import os
import re
import json

# Import audio libraries (will be installed via requirements.txt)
try:
    import speech_recognition as sr
    import pyttsx3
    from gtts import gTTS
    import playsound
    import pyaudio
    import wave
    import threading
    import time
    import whisper
    import torch
    import numpy as np
    from pydub import AudioSegment
    import sounddevice as sd
except ImportError:
    logging.warning("Audio libraries not available, using mock implementations")
    sr = None
    pyttsx3 = None
    gTTS = None
    playsound = None
    pyaudio = None
    wave = None
    threading = None
    time = None
    whisper = None
    torch = None
    np = None
    AudioSegment = None
    sd = None

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Handles all voice-related processing for SMARTII."""

    def __init__(self):
        self.recognizer = None
        self.tts_engine = None
        self.whisper_model = None
        self.audio_stream = None
        self.is_listening = {}
        self.wake_word_detected = False
        self.audio_buffers = {}
        self.continuous_listening = {}
        self.wake_word_active = {}
        self.always_listening_mode = {}
        self.whispering_mode = {}
        self.emotion_detector = None
        self.initialize_components()

    def initialize_components(self):
        """Initialize speech recognition and TTS engines."""
        try:
            if sr:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True

            if pyttsx3:
                self.tts_engine = pyttsx3.init()
                # Configure TTS voice
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to find a female voice
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                self.tts_engine.setProperty('rate', 180)  # Speed of speech

            logger.info("Voice processor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize voice components: {e}")

    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech audio to text."""
        try:
            if not self.recognizer:
                return "Speech recognition not available"

            # Convert bytes to AudioData
            audio = sr.AudioData(audio_data, 16000, 2)  # 16kHz, 16-bit

            # Recognize speech
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Speech recognized: {text}")
            return text

        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return "Speech recognition service unavailable."
        except Exception as e:
            logger.error(f"Error in speech to text: {e}")
            return "Error processing speech."

    async def text_to_speech(self, text: str, voice_settings: Optional[Dict[str, Any]] = None) -> bytes:
        """Convert text to speech audio."""
        try:
            # Try gTTS first (Google Text-to-Speech)
            if gTTS:
                tts = gTTS(text=text, lang='en', slow=False)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                return audio_buffer.getvalue()

            # Fallback to pyttsx3
            elif self.tts_engine:
                # Apply voice settings
                if voice_settings:
                    if 'rate' in voice_settings:
                        self.tts_engine.setProperty('rate', voice_settings['rate'])
                    if 'volume' in voice_settings:
                        self.tts_engine.setProperty('volume', voice_settings['volume'])

                # Generate speech
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                return b""  # pyttsx3 doesn't return bytes

            return b""

        except Exception as e:
            logger.error(f"Error in text to speech: {e}")
            return b""

    async def start_listening(self, client_id: str) -> bool:
        """Start listening for voice input."""
        try:
            if client_id in self.is_listening and self.is_listening[client_id]:
                return False

            self.is_listening[client_id] = True
            self.audio_buffers[client_id] = []

            logger.info(f"Started listening for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            return False

    async def stop_listening(self, client_id: str) -> bytes:
        """Stop listening and return collected audio."""
        try:
            if client_id not in self.is_listening or not self.is_listening[client_id]:
                return b""

            self.is_listening[client_id] = False
            audio_data = b"".join(self.audio_buffers.get(client_id, []))
            self.audio_buffers[client_id] = []

            logger.info(f"Stopped listening for client {client_id}, collected {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
            return b""

    async def detect_wake_word(self, audio_chunk: bytes) -> bool:
        """Detect wake word in audio stream."""
        try:
            # Enhanced wake word detection with multiple approaches
            wake_words = ["hey smartii", "smartii", "hey smarty", "okay smartii", "hi smartii"]

            if self.recognizer:
                audio = sr.AudioData(audio_chunk, 16000, 2)
                try:
                    # Try with show_all for better detection
                    text = self.recognizer.recognize_google(audio, show_all=True)
                    if text and 'alternative' in text:
                        for alternative in text['alternative']:
                            transcript = alternative['transcript'].lower().strip()
                            for wake_word in wake_words:
                                if wake_word in transcript:
                                    logger.info(f"Wake word detected: '{wake_word}' in '{transcript}'")
                                    return True
                except sr.UnknownValueError:
                    # If no speech detected, that's fine for wake word detection
                    pass
                except sr.RequestError:
                    # If API fails, try fallback method
                    pass

            # Fallback: Simple energy-based detection (not accurate but better than nothing)
            if len(audio_chunk) > 1000:  # Minimum chunk size
                # Calculate simple energy level
                energy = sum(abs(sample) for sample in audio_chunk) / len(audio_chunk)
                if energy > 1000:  # Threshold for potential speech
                    logger.debug(f"High energy detected, potential wake word (energy: {energy})")
                    # In a real implementation, you'd do more sophisticated analysis

            return False

        except Exception as e:
            logger.error(f"Error detecting wake word: {e}")
            return False

    async def detect_voice_activity(self, audio_chunk: bytes) -> bool:
        """Detect if there's voice activity in the audio."""
        try:
            if not self.recognizer:
                return False

            # Simple VAD using energy threshold
            audio = sr.AudioData(audio_chunk, 16000, 2)
            energy = audio.get_raw_data()

            # Calculate RMS energy
            rms = 0
            for sample in energy:
                rms += sample ** 2
            rms = (rms / len(energy)) ** 0.5

            # Threshold for voice activity (adjustable)
            threshold = 500
            return rms > threshold

        except Exception as e:
            logger.error(f"Error detecting voice activity: {e}")
            return False

    async def get_voice_settings(self, user_id: str) -> Dict[str, Any]:
        """Get voice settings for a user."""
        # Default settings
        return {
            "rate": 180,
            "volume": 0.8,
            "voice": "default",
            "language": "en-US"
        }

    async def update_voice_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update voice settings for a user."""
        try:
            # In a real implementation, you'd save these to a database
            logger.info(f"Updated voice settings for {user_id}: {settings}")
            return True
        except Exception as e:
            logger.error(f"Error updating voice settings: {e}")
            return False

    async def process_audio_stream(self, client_id: str, audio_stream: bytes) -> Dict[str, Any]:
        """Process a continuous audio stream for wake word and commands."""
        try:
            result = {
                "wake_word_detected": False,
                "voice_activity": False,
                "transcription": "",
                "should_respond": False,
                "command_detected": False,
                "emotion": {}
            }

            # Detect wake word
            result["wake_word_detected"] = await self.detect_wake_word(audio_stream)

            # Detect voice activity
            result["voice_activity"] = await self.detect_voice_activity(audio_stream)

            # If wake word detected, activate continuous listening
            if result["wake_word_detected"]:
                self.wake_word_active[client_id] = True
                self.continuous_listening[client_id] = True
                logger.info(f"Wake word activated for client {client_id}")

            # If wake word active or actively listening, transcribe and analyze
            if self.wake_word_active.get(client_id, False) or self.is_listening.get(client_id, False):
                result["transcription"] = await self.speech_to_text(audio_stream)
                result["should_respond"] = True

                # Analyze emotion if transcription successful
                if result["transcription"] and not result["transcription"].startswith("Sorry"):
                    result["emotion"] = await self.analyze_voice_emotion(audio_stream)

                # Check for command completion (silence or specific phrases)
                if self._is_command_complete(result["transcription"]):
                    result["command_detected"] = True
                    self.wake_word_active[client_id] = False
                    logger.info(f"Command completed for client {client_id}")

                # Buffer audio if listening
                if self.is_listening.get(client_id, False):
                    if client_id not in self.audio_buffers:
                        self.audio_buffers[client_id] = []
                    self.audio_buffers[client_id].append(audio_stream)

            return result

        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return {"error": str(e)}

    def _is_command_complete(self, transcription: str) -> bool:
        """Check if a voice command is complete."""
        if not transcription:
            return False

        # Command completion indicators
        completion_phrases = [
            "thank you", "thanks", "that's all", "stop listening",
            "okay", "alright", "got it", "understood"
        ]

        transcription_lower = transcription.lower()
        return any(phrase in transcription_lower for phrase in completion_phrases)

    async def generate_audio_response(self, text: str, client_id: str) -> str:
        """Generate an audio response and return base64 encoded audio."""
        try:
            # Get user voice settings
            voice_settings = await self.get_voice_settings(client_id)

            # Generate speech
            audio_bytes = await self.text_to_speech(text, voice_settings)

            # Convert to base64 for transmission
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                return audio_b64
            else:
                return ""

        except Exception as e:
            logger.error(f"Error generating audio response: {e}")
            return ""

    async def analyze_voice_emotion(self, audio_data: bytes) -> Dict[str, float]:
        """Analyze emotional content in voice."""
        try:
            # Placeholder for emotion detection
            # In a real implementation, you'd use ML models for emotion recognition
            return {
                "happy": 0.3,
                "sad": 0.1,
                "angry": 0.05,
                "neutral": 0.4,
                "excited": 0.15
            }

        except Exception as e:
            logger.error(f"Error analyzing voice emotion: {e}")
            return {"neutral": 1.0}

    async def adjust_for_noise(self, audio_data: bytes) -> bytes:
        """Apply noise reduction to audio."""
        try:
            # Placeholder for noise reduction
            # In a real implementation, you'd use audio processing libraries
            return audio_data

        except Exception as e:
            logger.error(f"Error adjusting for noise: {e}")
            return audio_data

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for STT/TTS."""
        return [
            "en-US", "en-GB", "es-ES", "fr-FR", "de-DE",
            "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"
        ]

    async def set_language(self, language: str) -> bool:
        """Set the language for speech processing."""
        try:
            if language in self.get_supported_languages():
                # Update recognizer language
                if self.recognizer:
                    # Google Speech Recognition language setting
                    pass  # Would set language in actual implementation
                logger.info(f"Language set to {language}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting language: {e}")
            return False

    async def enable_always_listening(self, client_id: str) -> bool:
        """Enable always-listening mode for wake word detection."""
        try:
            self.always_listening_mode[client_id] = True
            logger.info(f"Always-listening mode enabled for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error enabling always-listening: {e}")
            return False

    async def disable_always_listening(self, client_id: str) -> bool:
        """Disable always-listening mode."""
        try:
            self.always_listening_mode[client_id] = False
            logger.info(f"Always-listening mode disabled for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error disabling always-listening: {e}")
            return False

    async def enable_whispering_mode(self, client_id: str) -> bool:
        """Enable whispering mode for quieter TTS."""
        try:
            self.whispering_mode[client_id] = True
            if self.tts_engine:
                self.tts_engine.setProperty('volume', 0.3)  # Lower volume
                self.tts_engine.setProperty('rate', 150)  # Slower rate
            logger.info(f"Whispering mode enabled for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error enabling whispering mode: {e}")
            return False

    async def disable_whispering_mode(self, client_id: str) -> bool:
        """Disable whispering mode."""
        try:
            self.whispering_mode[client_id] = False
            if self.tts_engine:
                self.tts_engine.setProperty('volume', 0.8)  # Normal volume
                self.tts_engine.setProperty('rate', 180)  # Normal rate
            logger.info(f"Whispering mode disabled for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error disabling whispering mode: {e}")
            return False

    async def detect_emotion_from_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """Detect emotion from voice characteristics (pitch, tone, energy)."""
        try:
            # Placeholder for advanced emotion detection
            # In production, use ML models for prosody analysis
            emotion_scores = {
                "happy": 0.2,
                "sad": 0.1,
                "angry": 0.05,
                "excited": 0.15,
                "calm": 0.3,
                "stressed": 0.1,
                "neutral": 0.1
            }
            
            # Analyze audio energy (simple heuristic)
            if len(audio_data) > 100:
                energy = sum(abs(byte) for byte in audio_data[:100]) / 100
                if energy > 150:
                    emotion_scores["excited"] = 0.4
                    emotion_scores["happy"] = 0.3
                elif energy < 50:
                    emotion_scores["calm"] = 0.5
                    emotion_scores["sad"] = 0.2
            
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            
            return {
                "scores": emotion_scores,
                "dominant": dominant_emotion,
                "confidence": emotion_scores[dominant_emotion]
            }
        except Exception as e:
            logger.error(f"Error detecting emotion from voice: {e}")
            return {"scores": {}, "dominant": "neutral", "confidence": 0.0}

    async def detect_background_noise(self, audio_chunk: bytes) -> Dict[str, Any]:
        """Detect and classify background noise."""
        try:
            if len(audio_chunk) < 100:
                return {"noise_detected": False, "noise_level": 0, "type": "silent"}
            
            # Calculate noise level (RMS)
            noise_level = sum(abs(byte) for byte in audio_chunk[:100]) / 100
            
            noise_types = {
                "silent": noise_level < 20,
                "quiet": 20 <= noise_level < 50,
                "moderate": 50 <= noise_level < 100,
                "noisy": 100 <= noise_level < 150,
                "very_noisy": noise_level >= 150
            }
            
            detected_type = next((t for t, condition in noise_types.items() if condition), "moderate")
            
            return {
                "noise_detected": noise_level > 20,
                "noise_level": noise_level,
                "type": detected_type,
                "needs_noise_reduction": noise_level > 100
            }
        except Exception as e:
            logger.error(f"Error detecting background noise: {e}")
            return {"noise_detected": False, "noise_level": 0, "type": "unknown"}
