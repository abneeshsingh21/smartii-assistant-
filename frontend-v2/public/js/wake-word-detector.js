/**
 * SMARTII Browser-Based Wake Word Detection
 * No external API keys needed - uses Chrome's built-in speech recognition
 */

class BrowserWakeWordDetector {
    constructor() {
        this.isActive = false;
        this.recognition = null;
        this.wakeWords = ['hey smartii', 'hey smart', 'smartii', 'computer'];
        this.onWakeWordCallback = null;
        this.sensitivity = 0.7; // Threshold for fuzzy matching
        
        console.log('🎤 Browser Wake Word Detector initialized');
    }
    
    /**
     * Initialize wake word detection
     */
    initialize() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('❌ Speech recognition not supported in this browser');
            return false;
        }
        
        // Create always-on recognition instance
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;  // Keep listening
        this.recognition.interimResults = true;  // Get partial results
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 3;
        
        // Handle results
        this.recognition.onresult = (event) => {
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                const transcript = result[0].transcript.toLowerCase().trim();
                
                // Check if wake word detected
                if (this._isWakeWord(transcript)) {
                    console.log('🔥 Wake word detected:', transcript);
                    
                    if (this.onWakeWordCallback) {
                        this.onWakeWordCallback(transcript);
                    }
                    
                    // Brief pause to avoid re-triggering
                    this.stop();
                    setTimeout(() => {
                        if (this.isActive) {
                            this.start();
                        }
                    }, 1000);
                }
            }
        };
        
        // Handle errors
        this.recognition.onerror = (event) => {
            if (event.error === 'no-speech') {
                // Normal - just silence, restart
                return;
            }
            
            if (event.error === 'aborted') {
                // Restarting, ignore
                return;
            }
            
            console.warn('Wake word recognition error:', event.error);
            
            // Auto-restart on most errors
            if (this.isActive && event.error !== 'not-allowed') {
                setTimeout(() => {
                    if (this.isActive) {
                        try {
                            this.recognition.start();
                        } catch (e) {
                            // Already started
                        }
                    }
                }, 1000);
            }
        };
        
        // Auto-restart when it stops
        this.recognition.onend = () => {
            if (this.isActive) {
                console.log('🔄 Restarting wake word detection...');
                setTimeout(() => {
                    if (this.isActive) {
                        try {
                            this.recognition.start();
                        } catch (e) {
                            // Already started
                        }
                    }
                }, 500);
            }
        };
        
        this.recognition.onstart = () => {
            console.log('✅ Wake word detection ACTIVE');
        };
        
        return true;
    }
    
    /**
     * Start wake word detection
     */
    start() {
        if (!this.recognition) {
            console.error('Recognition not initialized');
            return false;
        }
        
        if (this.isActive) {
            console.warn('Wake word detection already active');
            return false;
        }
        
        this.isActive = true;
        
        try {
            this.recognition.start();
            console.log('🎙️ Wake word listening started - Say "Hey SMARTII"');
            return true;
        } catch (e) {
            console.error('Failed to start wake word detection:', e);
            return false;
        }
    }
    
    /**
     * Stop wake word detection
     */
    stop() {
        if (!this.isActive) {
            return;
        }
        
        this.isActive = false;
        
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                // Already stopped
            }
        }
        
        console.log('🛑 Wake word detection stopped');
    }
    
    /**
     * Check if text contains wake word
     */
    _isWakeWord(text) {
        text = text.toLowerCase().trim();
        
        // Direct match
        for (const wakeWord of this.wakeWords) {
            if (text.includes(wakeWord)) {
                return true;
            }
        }
        
        // Fuzzy match for similar phrases
        const fuzzyPatterns = [
            /hey\s+smart/i,
            /hello\s+smart/i,
            /hi\s+smart/i,
            /okay\s+smart/i,
            /computer/i
        ];
        
        for (const pattern of fuzzyPatterns) {
            if (pattern.test(text)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Set wake word callback
     */
    onWakeWord(callback) {
        this.onWakeWordCallback = callback;
    }
    
    /**
     * Add custom wake word
     */
    addWakeWord(word) {
        if (!this.wakeWords.includes(word.toLowerCase())) {
            this.wakeWords.push(word.toLowerCase());
            console.log(`Added wake word: ${word}`);
        }
    }
    
    /**
     * Set sensitivity (not used in browser implementation, kept for compatibility)
     */
    setSensitivity(value) {
        this.sensitivity = Math.max(0, Math.min(1, value));
        console.log(`Wake word sensitivity: ${this.sensitivity}`);
    }
}

// Export for use
window.BrowserWakeWordDetector = BrowserWakeWordDetector;
