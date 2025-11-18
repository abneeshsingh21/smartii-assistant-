/**
 * SMARTII Full Duplex Audio Engine
 * Handles simultaneous listening and speaking with instant interruption
 */

class FullDuplexAudioEngine {
    constructor(websocket) {
        this.ws = websocket;
        this.audioContext = null;
        this.microphone = null;
        this.processor = null;
        
        // Dual thread simulation with separate states
        this.playbackState = {
            isPlaying: false,
            currentUtterance: null,
            audioElement: null
        };
        
        this.captureState = {
            isCapturing: false,
            stream: null,
            vadDetected: false
        };
        
        // State flags
        this.isSpeaking = false;
        this.isListening = false;
        this.isInterrupted = false;
        
        // VAD (Voice Activity Detection) settings
        this.vadThreshold = 0.01;  // Amplitude threshold
        this.vadConsecutiveFrames = 3;  // Frames needed to trigger
        this.vadFrameCount = 0;
        
        // Interruption callbacks
        this.onInterruptCallbacks = [];
        this.onWakeWordCallbacks = [];
        this.onVADCallbacks = [];
        
        console.log('🎙️ Full Duplex Audio Engine initialized');
    }
    
    /**
     * Initialize audio system
     */
    async initialize() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });
            
            // Create microphone source
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            
            // Create script processor for audio analysis
            const bufferSize = 2048;
            this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            // VAD detection on audio frames
            this.processor.onaudioprocess = (e) => {
                if (!this.isListening) return;
                
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Calculate RMS (root mean square) for VAD
                const rms = this._calculateRMS(inputData);
                
                // Voice activity detection
                if (rms > this.vadThreshold) {
                    this.vadFrameCount++;
                    
                    if (this.vadFrameCount >= this.vadConsecutiveFrames) {
                        this._onVoiceActivityDetected();
                        this.vadFrameCount = 0;  // Reset
                    }
                } else {
                    this.vadFrameCount = 0;
                }
                
                // Send audio to backend for wake word detection (if enabled)
                this._sendAudioToBackend(inputData);
            };
            
            // Connect audio graph
            this.microphone.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            
            this.captureState.stream = stream;
            this.captureState.isCapturing = true;
            
            console.log('✅ Audio system initialized - Full duplex ready');
            return true;
            
        } catch (error) {
            console.error('❌ Audio initialization failed:', error);
            return false;
        }
    }
    
    /**
     * Start listening (capture thread)
     */
    startListening() {
        if (!this.audioContext) {
            console.error('Audio context not initialized');
            return false;
        }
        
        if (this.isListening) {
            console.warn('Already listening');
            return false;
        }
        
        this.isListening = true;
        this.vadFrameCount = 0;
        
        // Resume audio context if suspended
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        console.log('🎤 Listening started - VAD active');
        return true;
    }
    
    /**
     * Stop listening
     */
    stopListening() {
        this.isListening = false;
        this.vadFrameCount = 0;
        console.log('🎤 Listening stopped');
    }
    
    /**
     * Start speaking (playback thread)
     * @param {string} text - Text to speak
     * @param {function} onEnd - Callback when speech ends
     */
    startSpeaking(text, onEnd) {
        if (!text) return;
        
        // Stop any ongoing speech
        this.stopSpeaking();
        
        this.isSpeaking = true;
        this.isInterrupted = false;
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Select voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.name.toLowerCase().includes('female')) || voices[0];
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        utterance.onstart = () => {
            console.log('🔊 Speaking started');
            this.playbackState.isPlaying = true;
            
            // Send TTS start event to backend
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'tts_started'
                }));
            }
        };
        
        utterance.onend = () => {
            console.log('🔊 Speaking ended');
            this.isSpeaking = false;
            this.playbackState.isPlaying = false;
            this.playbackState.currentUtterance = null;
            
            // Notify backend TTS ended
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'tts_ended'
                }));
            }
            
            if (onEnd && !this.isInterrupted) {
                onEnd();
            }
        };
        
        utterance.onerror = (event) => {
            console.error('🔊 Speech error:', event);
            this.isSpeaking = false;
            this.playbackState.isPlaying = false;
        };
        
        this.playbackState.currentUtterance = utterance;
        window.speechSynthesis.speak(utterance);
        
        console.log('🔊 Speaking:', text.substring(0, 50) + '...');
    }
    
    /**
     * Stop speaking immediately (CRITICAL for interruptions)
     */
    stopSpeaking() {
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        
        this.isSpeaking = false;
        this.playbackState.isPlaying = false;
        this.playbackState.currentUtterance = null;
        
        console.log('🛑 Speaking STOPPED');
    }
    
    /**
     * Handle interruption (user started speaking while SMARTII talks)
     */
    interrupt(reason = 'user_interrupt') {
        console.warn(`⚡ INTERRUPT: ${reason}`);
        
        this.isInterrupted = true;
        
        // STOP TTS IMMEDIATELY (< 100ms)
        this.stopSpeaking();
        
        // Notify backend
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'interrupt',
                reason: reason
            }));
        }
        
        // Call all interrupt callbacks
        this.onInterruptCallbacks.forEach(cb => cb(reason));
        
        // Switch to listening mode
        this.startListening();
    }
    
    /**
     * Voice Activity Detection callback
     */
    _onVoiceActivityDetected() {
        if (!this.captureState.vadDetected) {
            this.captureState.vadDetected = true;
            
            console.log('👄 Voice activity detected');
            
            // If SMARTII is speaking, INTERRUPT
            if (this.isSpeaking) {
                this.interrupt('vad_detected');
            }
            
            // Notify backend
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'vad_detected'
                }));
            }
            
            // Call VAD callbacks
            this.onVADCallbacks.forEach(cb => cb());
            
            // Reset after 1 second
            setTimeout(() => {
                this.captureState.vadDetected = false;
            }, 1000);
        }
    }
    
    /**
     * Calculate RMS for VAD
     */
    _calculateRMS(buffer) {
        let sum = 0;
        for (let i = 0; i < buffer.length; i++) {
            sum += buffer[i] * buffer[i];
        }
        return Math.sqrt(sum / buffer.length);
    }
    
    /**
     * Send audio to backend for wake word detection
     */
    _sendAudioToBackend(audioData) {
        // Throttle: Only send every 100ms
        if (!this._lastSendTime || Date.now() - this._lastSendTime > 100) {
            this._lastSendTime = Date.now();
            
            // Convert Float32Array to base64
            const int16Array = new Int16Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                int16Array[i] = Math.max(-32768, Math.min(32767, audioData[i] * 32768));
            }
            
            const audioBase64 = this._arrayBufferToBase64(int16Array.buffer);
            
            // Send to backend via WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'audio_stream',
                    audio: audioBase64
                }));
            }
        }
    }
    
    /**
     * Convert ArrayBuffer to base64
     */
    _arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
    
    /**
     * Register callbacks
     */
    onInterrupt(callback) {
        this.onInterruptCallbacks.push(callback);
    }
    
    onWakeWord(callback) {
        this.onWakeWordCallbacks.push(callback);
    }
    
    onVAD(callback) {
        this.onVADCallbacks.push(callback);
    }
    
    /**
     * Set VAD sensitivity
     * @param {number} sensitivity - 0.0 (less sensitive) to 1.0 (more sensitive)
     */
    setVADSensitivity(sensitivity) {
        // Invert: higher sensitivity = lower threshold
        this.vadThreshold = 0.02 * (1 - sensitivity);
        console.log(`🎚️ VAD sensitivity set to ${sensitivity} (threshold: ${this.vadThreshold.toFixed(4)})`);
    }
    
    /**
     * Cleanup
     */
    destroy() {
        this.stopListening();
        this.stopSpeaking();
        
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        
        if (this.microphone) {
            this.microphone.disconnect();
            this.microphone = null;
        }
        
        if (this.captureState.stream) {
            this.captureState.stream.getTracks().forEach(track => track.stop());
            this.captureState.stream = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        console.log('🔌 Audio engine destroyed');
    }
}

// Export for use in main script
window.FullDuplexAudioEngine = FullDuplexAudioEngine;
