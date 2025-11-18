"""
SMARTII Wake Word Detection Service
Always-on background "Hey SMARTII" detection using Porcupine
"""

import logging
from typing import Callable, Optional
import asyncio
import threading

# Optional imports for wake word detection
try:
    import pvporcupine
    import pyaudio
    import struct
    WAKE_WORD_LIBS_AVAILABLE = True
except ImportError:
    WAKE_WORD_LIBS_AVAILABLE = False
    logging.warning("Wake word libraries not available - feature disabled")

logger = logging.getLogger(__name__)

class WakeWordDetector:
    """
    Always-on wake word detection using Porcupine
    Runs in separate thread, minimal CPU usage in IDLE state
    """
    
    def __init__(self, access_key: Optional[str] = None, sensitivity: float = 0.5):
        """
        Initialize wake word detector
        
        Args:
            access_key: Porcupine access key (get free key from picovoice.ai)
            sensitivity: Detection sensitivity (0.0 - 1.0, higher = more sensitive)
        """
        self.access_key = access_key or self._get_default_key()
        self.sensitivity = sensitivity
        self.is_running = False
        self.detection_callback = None
        self.porcupine = None
        self.audio_stream = None
        self.pyaudio_instance = None
        self.detection_thread = None
        
        logger.info(f"🎤 Wake Word Detector initialized (sensitivity: {sensitivity})")
    
    def _get_default_key(self) -> str:
        """
        Get default Porcupine access key
        IMPORTANT: Replace with your own key from https://console.picovoice.ai/
        """
        # Your Porcupine access key
        return "53zoi6kQds+3XKFq5HSCJ7CQWsT9RVNZ2jcdHrQ1PVG5JhfmMdtv2Q=="
    
    def start(self, callback: Callable):
        """
        Start always-on wake word detection
        
        Args:
            callback: Function to call when wake word is detected
        """
        if self.is_running:
            logger.warning("Wake word detector already running")
            return
        
        self.detection_callback = callback
        self.is_running = True
        
        # Start detection in separate thread to not block
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        logger.info("✅ Wake word detection ACTIVE - Say 'Hey SMARTII'")
    
    def stop(self):
        """Stop wake word detection"""
        logger.info("Stopping wake word detection...")
        self.is_running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        
        self._cleanup()
        logger.info("Wake word detection stopped")
    
    def _detection_loop(self):
        """Main detection loop running in separate thread"""
        if not WAKE_WORD_LIBS_AVAILABLE:
            logger.error("Wake word libraries not available")
            return
            
        try:
            # Initialize Porcupine with custom keyword or built-in
            # For custom "Hey SMARTII" keyword, you need to train it on Picovoice Console
            # For now, we'll use built-in "computer" keyword as substitute
            
            try:
                # Try to use Porcupine with access key
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=["computer"],  # Built-in keyword (substitute for "Hey SMARTII")
                    sensitivities=[self.sensitivity]
                )
            except Exception as e:
                logger.error(f"Failed to initialize Porcupine: {e}")
                logger.info("💡 Get your free access key from https://console.picovoice.ai/")
                logger.info("💡 Or train custom 'Hey SMARTII' keyword on Picovoice Console")
                return
            
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            self.audio_stream = self.pyaudio_instance.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            logger.info("🎙️ Microphone active - Wake word monitoring started")
            logger.info("🔊 Say 'COMPUTER' to wake (substitute for 'Hey SMARTII')")
            
            # Continuous detection loop
            while self.is_running:
                try:
                    # Read audio frame
                    pcm = self.audio_stream.read(
                        self.porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    
                    # Process with Porcupine
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        # WAKE WORD DETECTED!
                        logger.info("🔥 WAKE WORD DETECTED!")
                        
                        # Call callback asynchronously
                        if self.detection_callback:
                            if asyncio.iscoroutinefunction(self.detection_callback):
                                # Schedule async callback
                                asyncio.run_coroutine_threadsafe(
                                    self.detection_callback(),
                                    asyncio.get_event_loop()
                                )
                            else:
                                self.detection_callback()
                
                except Exception as e:
                    if self.is_running:
                        logger.error(f"Error in detection loop: {e}")
        
        except Exception as e:
            logger.error(f"Fatal error in wake word detection: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up audio resources"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            if self.porcupine:
                self.porcupine.delete()
                self.porcupine = None
            
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def set_sensitivity(self, sensitivity: float):
        """
        Adjust detection sensitivity
        
        Args:
            sensitivity: 0.0 (less sensitive) to 1.0 (more sensitive)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        logger.info(f"Wake word sensitivity set to {self.sensitivity}")
        
        # Restart detection with new sensitivity
        if self.is_running:
            callback = self.detection_callback
            self.stop()
            self.start(callback)


class MockWakeWordDetector:
    """Mock wake word detector for environments without libraries"""
    
    def __init__(self, *args, **kwargs):
        self.is_running = False
        self.sensitivity = 0.5
        logger.info("Using mock wake word detector (libraries not available)")
    
    def start(self, callback):
        logger.warning("Wake word detection not available on this platform")
        self.is_running = False
    
    def stop(self):
        self.is_running = False
    
    def set_sensitivity(self, sensitivity):
        self.sensitivity = sensitivity


# Global wake word detector instance
if WAKE_WORD_LIBS_AVAILABLE:
    wake_word_detector = WakeWordDetector(sensitivity=0.5)
else:
    wake_word_detector = MockWakeWordDetector(sensitivity=0.5)
