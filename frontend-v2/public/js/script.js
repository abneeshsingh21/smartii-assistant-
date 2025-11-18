/**
 * SMARTII - AI Voice Assistant Frontend
 * Premium, Futuristic UI with Voice Interaction
 */

// ============= Configuration =============
// Get or create persistent client ID
function getClientId() {
    let clientId = localStorage.getItem('smartii_client_id');
    if (!clientId) {
        clientId = 'client_' + Math.random().toString(36).substring(7) + '_' + Date.now();
        localStorage.setItem('smartii_client_id', clientId);
    }
    return clientId;
}

const CONFIG = {
    // Backend URL - Change this when deploying to production
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000' 
        : 'https://smartii.onrender.com',  // Your actual backend URL
    BACKEND_WS_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'ws://localhost:8000/ws'
        : 'wss://smartii.onrender.com/ws',  // Your actual backend URL
    ANIMATION_ENABLED: true,
    AUTO_SCROLL: true,
    CLIENT_ID: getClientId()  // Now persistent across sessions
};

// ============= State Management =============
const state = {
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    isRecognitionActive: false,
    continuousListening: false,  // New: continuous mode
    recognition: null,
    synthesis: window.speechSynthesis,
    waveformAnimation: null,
    messages: [],
    websocket: null,
    audioEngine: null,
    currentState: 'IDLE',  // Voice engine state
    settings: {
        theme: 'dark',
        voiceType: 'female',
        speechRate: 1.0,
        voiceEnabled: true,
        alwaysListening: true,
        animations: true,
        language: 'en',
        wakeWordEnabled: true,
        vadSensitivity: 0.5
    }
};

// ============= DOM Elements =============
const elements = {
    micButton: document.getElementById('micButton'),
    listeningText: document.getElementById('listeningText'),
    transcriptionBox: document.getElementById('transcriptionBox'),
    transcriptionText: document.getElementById('transcriptionText'),
    waveformContainer: document.getElementById('waveformContainer'),
    waveformCanvas: document.getElementById('waveformCanvas'),
    chatMessages: document.getElementById('chatMessages'),
    textInput: document.getElementById('textInput'),
    sendButton: document.getElementById('sendButton'),
    clearChat: document.getElementById('clearChat'),
    typingIndicator: document.getElementById('typingIndicator'),
    statusIndicator: document.getElementById('statusIndicator'),
    themeToggle: document.getElementById('themeToggle'),
    menuToggle: document.getElementById('menuToggle')
};

// ============= Speech Recognition Setup =============
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported');
        updateStatus('Speech recognition not available', 'warning');
        return;
    }
    
    // Main recognition for commands
    state.recognition = new SpeechRecognition();
    state.recognition.continuous = true;  // Keep listening
    state.recognition.interimResults = true;
    state.recognition.maxAlternatives = 3;
    state.recognition.lang = state.settings.language || 'en-US';
    
    // No separate wake word recognition - just use button activation
    
    state.recognition.onstart = () => {
        console.log('✅ Speech recognition started successfully');
        console.log('📢 Speak now! The browser is listening for your voice...');
        state.isListening = true;
        state.isRecognitionActive = true;
        
        // Removed haptic feedback to prevent collision/fast sounds
        
        elements.micButton.classList.add('listening');
        elements.waveformContainer.classList.add('active');
        elements.listeningText.textContent = 'Listening... Speak now!';
        startWaveformAnimation();
        updateStatus('🎤 Listening - Speak now!', 'success');
        
        // Activate holographic sphere
        if (holographicSphere) {
            holographicSphere.setActive(true);
        }
    };
    
    state.recognition.onresult = (event) => {
        console.log('🎯 Speech detected!', event.results);
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Show interim results
        if (interimTranscript) {
            elements.transcriptionText.textContent = interimTranscript;
            elements.transcriptionBox.classList.add('active');
            console.log('👂 Hearing: ' + interimTranscript);
        }
        
        // Process final results
        if (finalTranscript) {
            console.log('✅ Final transcript: ' + finalTranscript);
            elements.transcriptionText.textContent = finalTranscript;
            
            // Stop recognition in single-shot mode
            if (!state.continuousListening) {
                stopListening();
            }
            
            // Process the message
            setTimeout(() => {
                processUserMessage(finalTranscript);
            }, 200);
        }
    };
    
    state.recognition.onerror = (event) => {
        console.log('Speech recognition error:', event.error);
        
        // Reset state
        state.isRecognitionActive = false;
        
        // Ignore aborted errors (normal when stopping)
        if (event.error === 'aborted') {
            return;
        }
        
        // Handle "no-speech" error - keep listening in continuous mode
        if (event.error === 'no-speech') {
            console.log('⚠️ No speech detected, but keeping microphone active...');
            
            // In continuous mode, just restart
            if (state.continuousListening && state.isListening) {
                console.log('🔄 Continuous mode: Restarting after no-speech...');
                setTimeout(() => {
                    if (state.continuousListening && state.isListening) {
                        try {
                            state.recognition.start();
                        } catch (e) {
                            console.error('Restart failed:', e);
                        }
                    }
                }, 300);
            } else {
                // In single-shot mode, show message but keep listening
                updateStatus('🎤 Still listening - Speak now!', 'success');
                setTimeout(() => {
                    if (state.isListening && !state.continuousListening) {
                        try {
                            state.recognition.start();
                        } catch (e) {
                            console.error('Restart failed:', e);
                        }
                    }
                }, 300);
            }
            return;
        }
        
        // Handle other errors
        stopListening();
        
        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
            updateStatus('Microphone access denied. Please allow microphone access.', 'error');
            alert('SMARTII needs microphone access to work. Please allow microphone permissions in your browser settings.');
        } else {
            updateStatus('Error: ' + event.error, 'error');
        }
    };
    
    state.recognition.onend = () => {
        console.log('👂 Recognition ended. Listening state:', state.isListening);
        state.isRecognitionActive = false;
        
        // Restart if still supposed to be listening (both continuous and single-shot mode)
        if (state.isListening && !state.isSpeaking) {
            try {
                console.log('🔄 Restarting recognition to keep listening...');
                setTimeout(() => {
                    if (state.isListening && !state.isRecognitionActive) {
                        state.recognition.start();
                    }
                }, 100);  // Quick restart
            } catch (error) {
                console.error('Failed to restart recognition:', error);
            }
        } else {
            // Really stopping: clean up UI
            console.log('🛑 Stopping recognition completely');
            elements.micButton.classList.remove('listening');
            elements.waveformContainer.classList.remove('active');
            stopWaveformAnimation();
        }
        
        // Deactivate holographic sphere
        if (holographicSphere) {
            holographicSphere.setActive(false);
        }
    };
}

// ============= Waveform Animation =============
function startWaveformAnimation() {
    const canvas = elements.waveformCanvas;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    const centerX = canvas.width / (2 * window.devicePixelRatio);
    const centerY = canvas.height / (2 * window.devicePixelRatio);
    const bars = 60;
    const radius = 100;
    
    function animate() {
        if (!state.isListening) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const time = Date.now() * 0.001;
        
        for (let i = 0; i < bars; i++) {
            const angle = (i / bars) * Math.PI * 2;
            const height = Math.sin(time * 2 + i * 0.5) * 30 + 40;
            
            const x1 = centerX + Math.cos(angle) * radius;
            const y1 = centerY + Math.sin(angle) * radius;
            const x2 = centerX + Math.cos(angle) * (radius + height);
            const y2 = centerY + Math.sin(angle) * (radius + height);
            
            const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
            gradient.addColorStop(0, 'rgba(0, 217, 255, 0.5)');
            gradient.addColorStop(1, 'rgba(0, 102, 255, 0.8)');
            
            ctx.strokeStyle = gradient;
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        
        state.waveformAnimation = requestAnimationFrame(animate);
    }
    
    animate();
}

function stopWaveformAnimation() {
    if (state.waveformAnimation) {
        cancelAnimationFrame(state.waveformAnimation);
        state.waveformAnimation = null;
    }
    
    const canvas = elements.waveformCanvas;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// ============= Voice Control =============
function toggleListening() {
    if (state.isListening) {
        stopListening();
    } else {
        // Check if mobile device
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // On mobile, default to continuous mode for better UX
        startListening(isMobile);
    }
}

function startListening(continuous = false) {
    if (!state.recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    console.log('🎤 startListening called - continuous:', continuous);
    console.log('Current state:', {
        isListening: state.isListening,
        isRecognitionActive: state.isRecognitionActive,
        continuousListening: state.continuousListening
    });
    
    // Stop any existing recognition first
    if (state.isRecognitionActive) {
        console.warn('Recognition already active, stopping first');
        try {
            state.recognition.stop();
        } catch (e) {
            console.log('Error stopping existing recognition:', e);
        }
        // Wait a bit before restarting
        setTimeout(() => {
            startListening(continuous);
        }, 300);
        return;
    }
    
    // Set continuous mode
    state.continuousListening = continuous;
    state.isListening = true;
    
    console.log(`🎤 Starting recognition - Continuous: ${continuous}, isListening: ${state.isListening}`);
    
    // Update UI immediately
    elements.micButton.classList.add('listening');
    elements.waveformContainer.classList.add('active');
    startWaveformAnimation();
    
    if (continuous) {
        elements.listeningText.textContent = '🔴 Continuous Listening';
        updateStatus('🔴 Continuous mode - Always listening', 'success');
    } else {
        elements.listeningText.textContent = 'Listening... Speak now!';
        updateStatus('🎤 Listening - Speak now!', 'success');
    }
    
    // Start recognition
    try {
        console.log(`🚀 Calling recognition.start()... Browser: ${navigator.userAgent.includes('Chrome') ? 'Chrome' : navigator.userAgent.includes('Edge') ? 'Edge' : 'Other'}`);
        state.recognition.start();
        state.isRecognitionActive = true;
        console.log('✅ Recognition start() called successfully');
        console.log('⏳ Waiting for onstart event...');
    } catch (error) {
        console.error('❌ Failed to start recognition:', error);
        console.error('Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        
        // Reset UI on error
        elements.micButton.classList.remove('listening');
        elements.waveformContainer.classList.remove('active');
        stopWaveformAnimation();
        state.isListening = false;
        state.isRecognitionActive = false;
        
        // Check if it's a permission issue
        if (error.message && error.message.includes('permission')) {
            updateStatus('Microphone access denied', 'error');
            alert('SMARTII needs microphone access. Please allow microphone permissions in your browser.');
        } else if (error.message && error.message.includes('already started')) {
            console.warn('Recognition already started, retrying...');
            // Force retry
            setTimeout(() => {
                state.isRecognitionActive = false;
                startListening(continuous);
            }, 500);
        } else {
            updateStatus('Failed to start: ' + error.message, 'error');
            alert('Voice recognition error: ' + error.message + '\n\nPlease check:\n1. Microphone is connected\n2. Browser has mic permission\n3. Using Chrome/Edge/Safari');
        }
    }
}

function stopListening() {
    state.isListening = false;
    state.isRecognitionActive = false;
    state.continuousListening = false;  // Stop continuous mode
    elements.micButton.classList.remove('listening');
    elements.waveformContainer.classList.remove('active');
    elements.listeningText.textContent = 'Tap to speak';
    stopWaveformAnimation();
    updateStatus('Ready', 'success');
    
    if (state.recognition) {
        try {
            state.recognition.stop();
        } catch (error) {
            // Ignore errors when stopping
        }
    }
    
    // Hide transcription box after delay
    setTimeout(() => {
        elements.transcriptionBox.classList.remove('active');
    }, 3000);
}

// ============= Message Processing =============
async function processUserMessage(text) {
    if (!text.trim()) return;
    
    // Stop listening immediately to prevent hearing our own response
    if (state.recognition && state.isListening) {
        try {
            state.recognition.stop();
            state.isListening = false;
            state.isRecognitionActive = false;
        } catch (e) {
            // Ignore errors
        }
    }
    
    // Check for stop/deactivate commands
    const lowerText = text.toLowerCase();
    if (lowerText.includes('stop listening') || lowerText.includes('deactivate') || lowerText.includes('go to sleep')) {
        addMessage(text, 'user');
        addMessage('Stopped listening. Click the microphone button when you want to talk again.', 'assistant');
        if (state.settings.voiceEnabled) {
            speakText('Stopped listening. Click the microphone button when you want to talk again.');
        }
        state.settings.alwaysListening = false;
        stopListening();
        return;
    }
    
    // Add user message to chat
    addMessage(text, 'user');
    
    // Clear input
    elements.textInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Update status
    updateStatus('Processing...', 'info');
    
    try {
        // Send to backend (mock for now, integrate with real backend later)
        const response = await sendMessageToBackend(text);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Add assistant response
        addMessage(response.text, 'assistant');
        
        // Handle special actions (like opening URLs)
        if (response.url && response.open_url) {
            // Open YouTube or other URLs in new tab
            window.open(response.url, '_blank');
        }
        
        // Speak response if TTS is enabled
        if (state.settings.voiceEnabled) {
            speakText(response.text);
        }
        
        updateStatus('Ready', 'success');
    } catch (error) {
        console.error('Error processing message:', error);
        hideTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        updateStatus('Error occurred', 'error');
    }
}

async function sendMessageToBackend(text) {
    // Connect to real backend API
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: text,
                client_id: CONFIG.CLIENT_ID
            })
        });
        
        if (!response.ok) {
            throw new Error('Backend request failed');
        }
        
        const data = await response.json();
        console.log('Backend response:', data);  // Debug log
        return {
            text: data.response || data.text || 'I received your message.',
            actions: data.actions || [],
            url: data.url,  // Pass through URL
            open_url: data.open_url,  // Pass through flag
            video_id: data.video_id  // YouTube video ID
        };
    } catch (error) {
        console.error('Error connecting to backend:', error);
        // Return friendly error message
        return {
            text: 'I\'m having trouble connecting to my brain right now. Please check if the backend is running on port 8000.',
            actions: []
        };
    }
}

// ============= Chat UI =============
function addMessage(text, sender) {
    const message = {
        id: Date.now(),
        text,
        sender,
        timestamp: new Date()
    };
    
    state.messages.push(message);
    
    const messageEl = createMessageElement(message);
    elements.chatMessages.appendChild(messageEl);
    
    // Auto-scroll to bottom
    if (CONFIG.AUTO_SCROLL) {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = message.sender === 'assistant' 
        ? '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v12M6 12h12" stroke="currentColor" stroke-width="2"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="5" stroke="currentColor" stroke-width="2"/><path d="M20 21a8 8 0 10-16 0" stroke="currentColor" stroke-width="2"/></svg>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = message.text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(message.timestamp);
    
    content.appendChild(textDiv);
    content.appendChild(timeDiv);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

function showTypingIndicator() {
    elements.typingIndicator.classList.add('active');
}

function hideTypingIndicator() {
    elements.typingIndicator.classList.remove('active');
}

function clearChat() {
    if (confirm('Clear all messages?')) {
        state.messages = [];
        elements.chatMessages.innerHTML = '';
        
        // Add welcome message back
        addMessage('Hello! I\'m SMARTII, your AI assistant. How can I help you today?', 'assistant');
    }
}

// ============= Text-to-Speech =============
function speakText(text) {
    if (!state.synthesis) return;
    
    // CRITICAL: Stop ALL audio input to prevent feedback loop
    
    // Stop wake word detection
    if (wakeWordDetector && wakeWordDetector.isActive) {
        wakeWordDetector.stop();
        console.log('🛑 Wake word stopped during speech');
    }
    
    // Stop recognition to prevent hearing our own voice
    if (state.recognition && state.isListening) {
        try {
            state.recognition.stop();
            state.isListening = false;
            state.isRecognitionActive = false;
        } catch (e) {
            // Ignore
        }
    }
    
    state.isSpeaking = true;
    
    // Cancel any ongoing speech
    state.synthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = state.settings.speechRate || 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Select voice based on settings
    const voices = state.synthesis.getVoices();
    const selectedVoice = voices.find(voice => 
        voice.name.toLowerCase().includes(state.settings.voiceType)
    ) || voices[0];
    
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }
    
    // Restart listening after speech ends (only if continuous mode is on)
    utterance.onend = () => {
        console.log('🔊 Speech finished');
        state.isSpeaking = false;
        
        if (state.settings.alwaysListening) {
            setTimeout(() => {
                console.log('🔄 Restarting listening after speech...');
                startListening();
                
                // Restart wake word detection
                if (wakeWordDetector && !wakeWordDetector.isActive) {
                    wakeWordDetector.start();
                    console.log('✅ Wake word detection resumed');
                }
            }, 2000);
        }
    };
    
    utterance.onerror = (event) => {
        console.error('🔊 Speech error:', event);
        state.isSpeaking = false;
        
        if (state.settings.alwaysListening) {
            setTimeout(() => {
                startListening();
                if (wakeWordDetector && !wakeWordDetector.isActive) {
                    wakeWordDetector.start();
                }
            }, 1500);
        }
    };
    
    state.synthesis.speak(utterance);
}

// ============= Theme Management =============
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark-mode');
    
    if (isDark) {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        state.settings.theme = 'light';
    } else {
        body.classList.add('dark-mode');
        body.classList.remove('light-mode');
        state.settings.theme = 'dark';
    }
    
    // Save to localStorage
    localStorage.setItem('smartii-theme', state.settings.theme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('smartii-theme') || 'dark';
    state.settings.theme = savedTheme;
    
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
    }
}

// ============= Settings Management =============
function updateSettings() {
    console.log('🔧 Initializing settings controls...');
    
    // Voice type
    const voiceType = document.getElementById('voiceType');
    if (voiceType) {
        voiceType.value = state.settings.voiceType;
        voiceType.addEventListener('change', (e) => {
            state.settings.voiceType = e.target.value;
            localStorage.setItem('smartii-voice-type', e.target.value);
            console.log('✅ Voice type changed to:', e.target.value);
            addMessage(`Voice type changed to ${e.target.value}`, 'assistant');
        });
    }
    
    // Speech rate
    const speechRate = document.getElementById('speechRate');
    if (speechRate) {
        speechRate.value = state.settings.speechRate;
        const valueDisplay = speechRate.nextElementSibling;
        if (valueDisplay) {
            valueDisplay.textContent = state.settings.speechRate + 'x';
        }
        speechRate.addEventListener('input', (e) => {
            state.settings.speechRate = parseFloat(e.target.value);
            const valueDisplay = e.target.nextElementSibling;
            if (valueDisplay) {
                valueDisplay.textContent = e.target.value + 'x';
            }
            localStorage.setItem('smartii-speech-rate', e.target.value);
            console.log('✅ Speech rate changed to:', e.target.value);
        });
    }
    
    // Always listening
    const alwaysListening = document.getElementById('alwaysListening');
    if (alwaysListening) {
        alwaysListening.checked = state.settings.alwaysListening;
        alwaysListening.addEventListener('change', (e) => {
            state.settings.alwaysListening = e.target.checked;
            localStorage.setItem('smartii-always-listening', e.target.checked);
            console.log('✅ Always listening:', e.target.checked);
            
            if (e.target.checked) {
                state.settings.alwaysListening = true;
                updateStatus('Continuous mode activated', 'success');
                addMessage('Continuous conversation mode ON! Click microphone once, then keep talking without clicking again.', 'assistant');
            } else {
                state.settings.alwaysListening = false;
                updateStatus('Continuous mode disabled', 'info');
                addMessage('Continuous mode OFF. You need to click microphone for each question.', 'assistant');
            }
        });
    }
    
    // Animations toggle
    const animations = document.getElementById('animations');
    if (animations) {
        animations.checked = state.settings.animations;
        animations.addEventListener('change', (e) => {
            state.settings.animations = e.target.checked;
            document.body.classList.toggle('no-animations', !e.target.checked);
            localStorage.setItem('smartii-animations', e.target.checked);
            updateStatus(e.target.checked ? 'Animations enabled' : 'Animations disabled', 'info');
            console.log('✅ Animations:', e.target.checked);
        });
    }
    
    // Language selector
    const language = document.getElementById('language');
    if (language) {
        language.value = state.settings.language;
        language.addEventListener('change', (e) => {
            state.settings.language = e.target.value;
            localStorage.setItem('smartii-language', e.target.value);
            
            // Update speech recognition language
            if (state.recognition) {
                const langMap = {
                    'en': 'en-US',
                    'es': 'es-ES',
                    'fr': 'fr-FR',
                    'de': 'de-DE',
                    'ja': 'ja-JP',
                    'zh': 'zh-CN'
                };
                state.recognition.lang = langMap[e.target.value] || 'en-US';
            }
            
            console.log('✅ Language changed to:', e.target.value);
            addMessage(`Language changed to ${e.target.value}`, 'assistant');
        });
    }
    
    // Auto-detect language toggle
    const autoDetect = document.getElementById('autoDetect');
    if (autoDetect) {
        autoDetect.checked = state.settings.autoDetectLanguage || false;
        autoDetect.addEventListener('change', (e) => {
            state.settings.autoDetectLanguage = e.target.checked;
            localStorage.setItem('smartii-auto-detect', e.target.checked);
            updateStatus(e.target.checked ? 'Auto language detection ON' : 'Auto language detection OFF', 'info');
            console.log('✅ Auto-detect language:', e.target.checked);
        });
    }
    
    // Memory section buttons
    document.querySelectorAll('.memory-action').forEach(button => {
        button.addEventListener('click', (e) => {
            const card = e.target.closest('.memory-card');
            const title = card.querySelector('h3').textContent;
            handleMemoryAction(title);
        });
    });
    
    // Theme options
    document.querySelectorAll('.theme-option').forEach(option => {
        option.addEventListener('click', (e) => {
            const theme = e.currentTarget.dataset.theme;
            document.querySelectorAll('.theme-option').forEach(opt => opt.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            if (theme === 'dark') {
                document.body.classList.add('dark-mode');
                document.body.classList.remove('light-mode');
            } else {
                document.body.classList.remove('dark-mode');
                document.body.classList.add('light-mode');
            }
            
            state.settings.theme = theme;
            localStorage.setItem('smartii-theme', theme);
        });
    });
}

function loadSettings() {
    // Load saved settings from localStorage
    const savedVoiceType = localStorage.getItem('smartii-voice-type');
    const savedSpeechRate = localStorage.getItem('smartii-speech-rate');
    const savedLanguage = localStorage.getItem('smartii-language');
    const savedAlwaysListening = localStorage.getItem('smartii-always-listening');
    const savedAnimations = localStorage.getItem('smartii-animations');
    const savedAutoDetect = localStorage.getItem('smartii-auto-detect');
    
    if (savedVoiceType) {
        state.settings.voiceType = savedVoiceType;
        const voiceTypeEl = document.getElementById('voiceType');
        if (voiceTypeEl) voiceTypeEl.value = savedVoiceType;
    }
    
    if (savedSpeechRate) {
        state.settings.speechRate = parseFloat(savedSpeechRate);
        const speechRateEl = document.getElementById('speechRate');
        if (speechRateEl) speechRateEl.value = savedSpeechRate;
    }
    
    if (savedLanguage) {
        state.settings.language = savedLanguage;
        const languageEl = document.getElementById('language');
        if (languageEl) languageEl.value = savedLanguage;
    }
    
    if (savedAlwaysListening !== null) {
        state.settings.alwaysListening = savedAlwaysListening === 'true';
        const alwaysListeningEl = document.getElementById('alwaysListening');
        if (alwaysListeningEl) alwaysListeningEl.checked = state.settings.alwaysListening;
    }
    
    if (savedAnimations !== null) {
        state.settings.animations = savedAnimations === 'true';
        const animationsEl = document.getElementById('animations');
        if (animationsEl) animationsEl.checked = state.settings.animations;
        // Apply animations setting
        document.body.classList.toggle('no-animations', !state.settings.animations);
    }
    
    if (savedAutoDetect !== null) {
        state.settings.autoDetectLanguage = savedAutoDetect === 'true';
        const autoDetectEl = document.getElementById('autoDetect');
        if (autoDetectEl) autoDetectEl.checked = state.settings.autoDetectLanguage;
    }
}

// ============= Continuous Listening Mode =============
function startContinuousListening() {
    // TODO: Implement wake word detection
    console.log('Continuous listening mode started');
    updateStatus('Always listening (wake word: "Hey Smartii")', 'info');
}

function stopContinuousListening() {
    console.log('Continuous listening mode stopped');
    updateStatus('Ready', 'success');
}

// ============= Memory Management =============
function handleMemoryAction(type) {
    updateStatus(`Loading ${type.toLowerCase()}...`, 'info');
    
    switch(type.toLowerCase()) {
        case 'routines':
            addMessage(`📊 Viewing learned routines and patterns. This will show your daily habits and preferences.`, 'assistant');
            // TODO: Connect to backend memory API
            fetchMemoryData('routines');
            break;
        case 'preferences':
            addMessage(`⚙️ Managing your saved preferences. You can view and edit what I've learned about you.`, 'assistant');
            // TODO: Connect to backend memory API
            fetchMemoryData('preferences');
            break;
        case 'tasks':
            addMessage(`✅ Viewing task history. Here's a summary of completed tasks and actions.`, 'assistant');
            // TODO: Connect to backend memory API
            fetchMemoryData('tasks');
            break;
        default:
            console.warn('Unknown memory action:', type);
    }
}

async function fetchMemoryData(type) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/memory/${type}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch memory data');
        }
        
        const data = await response.json();
        console.log(`Memory data (${type}):`, data);
        
        // Display the data in chat
        if (data && data.items && data.items.length > 0) {
            const summary = `Found ${data.items.length} ${type}:\n${data.items.slice(0, 5).map(item => `• ${item.name || item.title}`).join('\n')}`;
            addMessage(summary, 'assistant');
        } else {
            addMessage(`No ${type} data available yet. Keep using SMARTII to build your memory!`, 'assistant');
        }
    } catch (error) {
        console.error('Error fetching memory:', error);
        addMessage(`Memory feature coming soon! Backend integration in progress.`, 'assistant');
    }
}

// ============= Status Updates =============
function updateStatus(text, type = 'info') {
    const statusIndicator = elements.statusIndicator;
    const statusText = statusIndicator.querySelector('.status-text');
    const statusDot = statusIndicator.querySelector('.status-dot');
    
    if (statusText) statusText.textContent = text;
    
    // Update dot color
    if (statusDot) {
        statusDot.style.background = {
            'success': 'var(--success)',
            'warning': 'var(--warning)',
            'error': 'var(--error)',
            'info': 'var(--accent-primary)'
        }[type] || 'var(--success)';
    }
}

// ============= Utility Functions =============
function formatTime(date) {
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return date.toLocaleDateString();
}

// ============= Event Listeners =============
function setupEventListeners() {
    // Microphone button
    if (elements.micButton) {
        elements.micButton.addEventListener('click', () => {
            // Removed vibration from here - will vibrate only when recognition actually starts
            toggleListening();
        });
    }
    
    // Text input
    if (elements.textInput) {
        elements.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const text = elements.textInput.value;
                processUserMessage(text);
            }
        });
    }
    
    // Send button
    if (elements.sendButton) {
        elements.sendButton.addEventListener('click', () => {
            // Haptic feedback
            if (navigator.vibrate) {
                navigator.vibrate(30);
            }
            const text = elements.textInput.value;
            processUserMessage(text);
        });
    }
    
    // Clear chat button
    if (elements.clearChat) {
        elements.clearChat.addEventListener('click', clearChat);
    }
    
    // Theme toggle
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Menu toggle (mobile)
    if (elements.menuToggle) {
        elements.menuToggle.addEventListener('click', () => {
            const navMenu = document.querySelector('.nav-menu');
            if (navMenu) {
                navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
            }
        });
    }
    
    // Smooth scroll for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// ============= Initialization =============
async function requestMicrophonePermission() {
    try {
        console.log('🎤 Requesting microphone permission...');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('✅ Microphone permission granted!');
        // Stop the stream immediately, we just needed permission
        stream.getTracks().forEach(track => track.stop());
        return true;
    } catch (error) {
        console.error('❌ Microphone permission denied:', error);
        updateStatus('Microphone access denied. Please allow microphone in browser settings.', 'error');
        addMessage('⚠️ I need microphone permission to listen for "Hey SMARTII". Please click the microphone icon in your browser address bar and allow access.', 'assistant');
        return false;
    }
}

// ============= 3D Visualization =============
let holographicSphere = null;

function init3DVisualization() {
    try {
        if (typeof HolographicSphere !== 'undefined') {
            holographicSphere = new HolographicSphere('holographicSphere');
            console.log('✅ 3D Holographic Sphere initialized');
        } else {
            console.warn('⚠️ HolographicSphere not loaded - 3D visualization disabled');
        }
    } catch (error) {
        console.error('Failed to initialize 3D visualization:', error);
    }
}

// ============= Wake Word Detection =============
let wakeWordDetector = null;

function initWakeWordDetection() {
    if (typeof BrowserWakeWordDetector === 'undefined') {
        console.warn('Wake word detector not loaded');
        return;
    }
    
    wakeWordDetector = new BrowserWakeWordDetector();
    
    if (!wakeWordDetector.initialize()) {
        console.error('Failed to initialize wake word detection');
        return;
    }
    
    // Set callback
    wakeWordDetector.onWakeWord((wakeWord) => {
        console.log('🔥 Wake word triggered:', wakeWord);
        
        // Visual feedback
        updateStatus('Wake word detected!', 'success');
        elements.transcriptionText.textContent = `"${wakeWord}" detected`;
        elements.transcriptionBox.classList.add('active');
        
        // Stop wake word detection temporarily
        wakeWordDetector.stop();
        
        // Wait a moment to ensure wake word recognition fully stopped
        setTimeout(() => {
            // Only start command listening if not already active
            if (!state.isListening && !state.isRecognitionActive) {
                startListening();
            }
        }, 500);
    });
    
    // Start if always listening is enabled
    if (state.settings.alwaysListening) {
        setTimeout(() => {
            wakeWordDetector.start();
            console.log('🎙️ Always-on wake word detection enabled');
            updateStatus('Say "Hey SMARTII" to wake', 'success');
            addMessage('👋 Always-on mode active! Say "Hey SMARTII" anytime to wake me up.', 'assistant');
        }, 1500);
    }
}

// ============= User Greeting & Profile =============
async function checkUserGreeting() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/greeting`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: CONFIG.CLIENT_ID })
        });
        
        const data = await response.json();
        
        if (data.is_new_user) {
            // Show welcome modal for first-time users
            showWelcomeModal();
        } else {
            // Show personalized greeting
            addMessage(data.greeting, 'assistant');
            speak(data.greeting);
        }
    } catch (error) {
        console.error('Error getting greeting:', error);
        addMessage('Hello! I\'m SMARTII, your AI assistant. How can I help you today?', 'assistant');
    }
}

function showWelcomeModal() {
    const modal = document.getElementById('welcomeModal');
    if (!modal) return;
    
    modal.style.display = 'flex';
    
    // Setup event listeners
    const saveNameButton = document.getElementById('saveNameButton');
    const gmailLoginButton = document.getElementById('gmailLoginButton');
    const skipWelcomeButton = document.getElementById('skipWelcomeButton');
    const userNameInput = document.getElementById('userNameInput');
    
    // Save name and close modal
    saveNameButton.addEventListener('click', async () => {
        const name = userNameInput.value.trim();
        
        if (!name) {
            alert('Please enter your name');
            return;
        }
        
        await saveUserName(name);
        modal.style.display = 'none';
    });
    
    // Gmail login
    gmailLoginButton.addEventListener('click', async () => {
        await initiateGmailLogin();
    });
    
    // Skip welcome
    skipWelcomeButton.addEventListener('click', () => {
        modal.style.display = 'none';
        addMessage('Hello! I\'m SMARTII, your AI assistant. Feel free to ask me anything!', 'assistant');
    });
    
    // Enter key to save name
    userNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            saveNameButton.click();
        }
    });
}

async function saveUserName(name) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/set-name`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                client_id: CONFIG.CLIENT_ID,
                name: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage(data.message, 'assistant');
            speak(data.message);
        }
    } catch (error) {
        console.error('Error saving name:', error);
        addMessage(`Nice to meet you, ${name}! I'll remember your name.`, 'assistant');
    }
}

async function initiateGmailLogin() {
    // This is a simplified version - for production, you'd use OAuth2
    const email = prompt('Please enter your Gmail address:');
    
    if (!email || !email.includes('@')) {
        alert('Please enter a valid email address');
        return;
    }
    
    const name = document.getElementById('userNameInput').value.trim() || email.split('@')[0];
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/gmail-login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                client_id: CONFIG.CLIENT_ID,
                email: email,
                name: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('welcomeModal').style.display = 'none';
            addMessage(data.message, 'assistant');
            speak(`Welcome back, ${name}! Your profile is now synced with ${email}`);
        }
    } catch (error) {
        console.error('Error with Gmail login:', error);
        alert('Could not connect to Gmail. Please try again.');
    }
}

async function init() {
    console.log('🚀 SMARTII UI Initializing...');
    
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Show appropriate hint based on device
    if (isMobile) {
        const mobileHint = document.getElementById('mobileHint');
        if (mobileHint) mobileHint.style.display = 'block';
        console.log('📱 Mobile device detected - optimized for touch');
    } else {
        const shortcutsHint = document.getElementById('shortcutsHint');
        if (shortcutsHint) shortcutsHint.style.display = 'block';
        console.log('💻 Desktop detected - keyboard shortcuts enabled');
    }
    
    // Load theme
    loadTheme();
    
    // Load settings
    loadSettings();
    
    // Initialize 3D visualization
    init3DVisualization();
    
    // Request microphone permission first
    const hasMicPermission = await requestMicrophonePermission();
    
    // Setup speech recognition
    initSpeechRecognition();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup settings listeners
    updateSettings();
    
    // Load voices for TTS
    if (state.synthesis) {
        state.synthesis.addEventListener('voiceschanged', () => {
            console.log('Voices loaded:', state.synthesis.getVoices().length);
        });
    }
    
    // Check for user greeting
    await checkUserGreeting();
    
    // Update status
    updateStatus('Ready to assist', 'success');
    
    // Setup modal handlers
    setupModalHandlers();
    
    // Initialize wake word detection
    if (hasMicPermission) {
        initWakeWordDetection();
    } else {
        console.warn('⚠️ Cannot start wake word - no microphone permission');
        addMessage('⚠️ Microphone permission required for wake word detection', 'assistant');
    }
    
    console.log('✅ SMARTII UI Ready!');
}

// ============= Modal Handlers =============
function setupModalHandlers() {
    // Privacy modal
    const privacyLink = document.getElementById('privacyLink');
    const privacyModal = document.getElementById('privacyModal');
    
    // Terms modal
    const termsLink = document.getElementById('termsLink');
    const termsModal = document.getElementById('termsModal');
    
    // Docs modal
    const docsLink = document.getElementById('docsLink');
    const docsModal = document.getElementById('docsModal');
    
    // Open modals
    if (privacyLink) {
        privacyLink.addEventListener('click', (e) => {
            e.preventDefault();
            privacyModal.classList.add('active');
        });
    }
    
    if (termsLink) {
        termsLink.addEventListener('click', (e) => {
            e.preventDefault();
            termsModal.classList.add('active');
        });
    }
    
    if (docsLink) {
        docsLink.addEventListener('click', (e) => {
            e.preventDefault();
            docsModal.classList.add('active');
        });
    }
    
    // Close modals
    document.querySelectorAll('.modal-close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            const modalId = closeBtn.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Close modal when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
            });
        }
        
        // Spacebar to toggle microphone (if not typing in input)
        if (e.code === 'Space' && e.target !== elements.textInput) {
            e.preventDefault();
            toggleListening();
        }
        
        // Ctrl+Shift+L for continuous listening mode
        if (e.ctrlKey && e.shiftKey && e.key === 'L') {
            e.preventDefault();
            if (state.continuousListening) {
                stopListening();
                addMessage('Continuous listening disabled', 'assistant');
            } else {
                startListening(true);  // Enable continuous mode
                addMessage('Continuous listening enabled - I\'ll keep listening after each response', 'assistant');
            }
        }
    });
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// ============= Export for backend integration =============
window.SMARTII = {
    processUserMessage,
    addMessage,
    updateStatus,
    startListening,
    stopListening,
    state,
    CONFIG
};
