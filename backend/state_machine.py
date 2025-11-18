"""
SMARTII State Machine Controller
Manages the full duplex voice engine states with instant transitions
"""

from enum import Enum
from typing import Optional, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class State(Enum):
    """Voice engine states"""
    IDLE = "idle"  # Background wake word listening only
    WAKEWORD_DETECTED = "wakeword_detected"  # Wake word just detected
    LISTENING = "listening"  # Active STT streaming
    THINKING = "thinking"  # LLM processing
    SPEAKING = "speaking"  # TTS playback active
    INTERRUPTED = "interrupted"  # User interrupted, switching to listening
    ERROR_RECOVERY = "error_recovery"  # Fallback state

class VoiceStateMachine:
    """Full duplex state machine with interruption support"""
    
    def __init__(self):
        self.state = State.IDLE
        self.previous_state = None
        self.listeners = []
        self.lock = asyncio.Lock()
        
        # State flags for thread coordination
        self.is_speaking = False
        self.is_listening = False
        self.is_interrupted = False
        self.wakeword_active = True  # Always active in background
        
        logger.info("🎙️ Voice State Machine initialized - Starting in IDLE state")
    
    async def transition(self, new_state: State, reason: str = ""):
        """Thread-safe state transition with event broadcasting"""
        async with self.lock:
            if self.state == new_state:
                return
            
            self.previous_state = self.state
            self.state = new_state
            
            # Update flags based on state
            self._update_flags()
            
            logger.info(f"🔄 State: {self.previous_state.value} → {new_state.value} ({reason})")
            
            # Notify all listeners
            await self._notify_listeners(new_state, reason)
    
    def _update_flags(self):
        """Update coordination flags based on current state"""
        self.is_listening = self.state in [State.LISTENING, State.WAKEWORD_DETECTED]
        self.is_speaking = self.state == State.SPEAKING
        self.is_interrupted = self.state == State.INTERRUPTED
        
        # Wake word is always active (background process)
        self.wakeword_active = True
    
    async def handle_wakeword(self):
        """Handle wake word detection - immediate transition"""
        if self.state == State.SPEAKING:
            # CRITICAL: Stop TTS immediately
            logger.info("⚡ Wake word during speech - INTERRUPTING")
            await self.transition(State.INTERRUPTED, "wake word during speech")
        else:
            await self.transition(State.WAKEWORD_DETECTED, "wake word detected")
        
        # Auto-transition to listening
        await asyncio.sleep(0.1)  # 100ms for audio cleanup
        await self.transition(State.LISTENING, "auto-start after wake word")
    
    async def handle_speech_start(self):
        """Handle user starting to speak"""
        if self.state in [State.IDLE, State.WAKEWORD_DETECTED]:
            await self.transition(State.LISTENING, "user speech detected")
        elif self.state == State.SPEAKING:
            # User is interrupting
            await self.transition(State.INTERRUPTED, "user interrupted")
            await asyncio.sleep(0.05)  # 50ms for TTS stop
            await self.transition(State.LISTENING, "listening after interrupt")
    
    async def handle_speech_end(self):
        """Handle user finished speaking"""
        if self.state == State.LISTENING:
            await self.transition(State.THINKING, "processing user input")
    
    async def handle_llm_start(self):
        """Handle LLM processing start"""
        if self.state in [State.THINKING, State.LISTENING]:
            await self.transition(State.THINKING, "LLM generating response")
    
    async def handle_tts_start(self):
        """Handle TTS playback start"""
        if self.state in [State.THINKING, State.LISTENING]:
            await self.transition(State.SPEAKING, "speaking response")
    
    async def handle_tts_end(self):
        """Handle TTS playback end - return to listening"""
        if self.state == State.SPEAKING:
            await self.transition(State.LISTENING, "finished speaking, ready for next")
            
            # Auto-timeout to IDLE after 10 seconds of silence
            await asyncio.sleep(10)
            if self.state == State.LISTENING:
                await self.transition(State.IDLE, "timeout - returning to background")
    
    async def handle_error(self, error: str):
        """Handle error state"""
        await self.transition(State.ERROR_RECOVERY, f"error: {error}")
        
        # Recovery: Try to return to IDLE
        await asyncio.sleep(2)
        await self.transition(State.IDLE, "recovered from error")
    
    async def force_interrupt(self):
        """Force immediate interruption (emergency stop)"""
        logger.warning("🛑 FORCE INTERRUPT triggered")
        await self.transition(State.INTERRUPTED, "force interrupt")
        await asyncio.sleep(0.05)
        await self.transition(State.LISTENING, "listening after force interrupt")
    
    def add_listener(self, callback: Callable):
        """Add state change listener"""
        self.listeners.append(callback)
    
    async def _notify_listeners(self, new_state: State, reason: str):
        """Notify all listeners of state change"""
        for callback in self.listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(new_state, reason)
                else:
                    callback(new_state, reason)
            except Exception as e:
                logger.error(f"Error in state listener: {e}")
    
    def get_state(self) -> State:
        """Get current state (thread-safe read)"""
        return self.state
    
    def can_speak(self) -> bool:
        """Check if TTS can start"""
        return self.state in [State.THINKING, State.LISTENING] and not self.is_interrupted
    
    def can_listen(self) -> bool:
        """Check if STT can start"""
        return self.state in [State.IDLE, State.WAKEWORD_DETECTED, State.LISTENING, State.INTERRUPTED]
    
    def should_stop_tts(self) -> bool:
        """Check if TTS should stop immediately"""
        return self.state in [State.INTERRUPTED, State.LISTENING, State.WAKEWORD_DETECTED]


# Global state machine instance
voice_state = VoiceStateMachine()
