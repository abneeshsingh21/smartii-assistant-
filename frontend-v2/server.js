/**
 * SMARTII Frontend Server
 * Node.js + Express server to serve the UI and provide API endpoints
 */

const express = require('express');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 3000;

// ============= Middleware =============
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/css', express.static(path.join(__dirname, 'public/css')));
app.use('/js', express.static(path.join(__dirname, 'public/js')));
app.use('/assets', express.static(path.join(__dirname, 'public/assets')));

// Logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// ============= API Routes =============

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

/**
 * Start recording endpoint
 * TODO: Integrate with actual voice recording service
 */
app.post('/api/start-recording', (req, res) => {
    console.log('Starting recording...');
    
    // Mock response - replace with actual implementation
    res.json({
        success: true,
        message: 'Recording started',
        sessionId: generateSessionId()
    });
    
    /* INTEGRATION GUIDE:
     * 1. Initialize audio recording
     * 2. Start capturing microphone input
     * 3. Return session ID for tracking
     * 4. Stream audio to backend for processing
     */
});

/**
 * Stop recording endpoint
 * TODO: Integrate with actual voice recording service
 */
app.post('/api/stop-recording', (req, res) => {
    const { sessionId } = req.body;
    console.log('Stopping recording for session:', sessionId);
    
    // Mock response - replace with actual implementation
    res.json({
        success: true,
        message: 'Recording stopped',
        audioUrl: '/audio/recording-' + sessionId + '.wav'
    });
    
    /* INTEGRATION GUIDE:
     * 1. Stop audio recording
     * 2. Save audio file
     * 3. Send to backend for speech-to-text
     * 4. Return transcription result
     */
});

/**
 * Process text message endpoint
 * TODO: Connect to SMARTII backend AI engine
 */
app.post('/api/process-text', async (req, res) => {
    try {
        const { text } = req.body;
        
        if (!text) {
            return res.status(400).json({
                success: false,
                error: 'Text is required'
            });
        }
        
        console.log('Processing text:', text);
        
        // Mock AI response - replace with actual backend call
        const response = await processWithSmartiiBackend(text);
        
        res.json({
            success: true,
            text: response.text,
            actions: response.actions || [],
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Error processing text:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to process text'
        });
    }
});

/**
 * Get AI suggestions endpoint
 */
app.get('/api/suggestions', async (req, res) => {
    try {
        // Mock suggestions - replace with actual backend call
        const suggestions = [
            {
                id: 1,
                text: 'Would you like me to check your calendar for today?',
                action: 'calendar.check',
                priority: 'high'
            },
            {
                id: 2,
                text: 'It\'s time for your daily standup meeting.',
                action: 'meeting.reminder',
                priority: 'medium'
            },
            {
                id: 3,
                text: 'You have 3 unread emails from your boss.',
                action: 'email.check',
                priority: 'medium'
            }
        ];
        
        res.json({
            success: true,
            suggestions,
            timestamp: new Date().toISOString()
        });
        
        /* INTEGRATION GUIDE:
         * Connect to: http://localhost:8000/v1/suggestions
         * const response = await fetch('http://localhost:8000/v1/suggestions');
         * const data = await response.json();
         * return data.suggestions;
         */
        
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch suggestions'
        });
    }
});

/**
 * Get memory/routines endpoint
 */
app.get('/api/memory/routines', async (req, res) => {
    try {
        // Mock routines - replace with actual backend call
        const routines = [
            {
                id: 1,
                name: 'Morning routine',
                time: '08:00',
                actions: ['Check weather', 'Read news', 'Check calendar'],
                frequency: 'daily'
            },
            {
                id: 2,
                name: 'Evening routine',
                time: '20:00',
                actions: ['Set alarm', 'Check tomorrow\'s schedule', 'Turn off lights'],
                frequency: 'daily'
            }
        ];
        
        res.json({
            success: true,
            routines,
            count: routines.length
        });
        
        /* INTEGRATION GUIDE:
         * Connect to: http://localhost:8000/v1/routines
         */
        
    } catch (error) {
        console.error('Error fetching routines:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch routines'
        });
    }
});

/**
 * Get settings endpoint
 */
app.get('/api/settings', (req, res) => {
    // Return default settings
    res.json({
        success: true,
        settings: {
            theme: 'dark',
            voiceType: 'female',
            speechRate: 1.0,
            language: 'en',
            alwaysListening: false,
            animations: true
        }
    });
});

/**
 * Update settings endpoint
 */
app.put('/api/settings', (req, res) => {
    const settings = req.body;
    console.log('Updating settings:', settings);
    
    // Save settings (in real app, save to database)
    res.json({
        success: true,
        message: 'Settings updated successfully',
        settings
    });
    
    /* INTEGRATION GUIDE:
     * Connect to: http://localhost:8000/v1/voice/settings
     * for voice-specific settings
     */
});

// ============= Helper Functions =============

/**
 * Process text with SMARTII backend
 * TODO: Replace with actual backend API call
 */
async function processWithSmartiiBackend(text) {
    // Connect to real SMARTII backend
    try {
        const response = await fetch('http://localhost:8000/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                client_id: 'user-123'
            })
        });
        
        if (!response.ok) {
            console.error('Backend request failed:', response.status);
            throw new Error('Backend request failed');
        }
        
        const data = await response.json();
        console.log('Backend response:', data);
        
        return {
            text: data.reply || data.response || data.message || 'I received your message.',
            actions: data.actions || []
        };
    } catch (error) {
        console.error('Error connecting to backend:', error);
        
        // Fallback to basic responses if backend unavailable
        const lowerText = text.toLowerCase();
        
        if (lowerText.includes('weather')) {
            return {
                text: 'The weather today is sunny with a high of 75°F. (Backend offline)',
                actions: []
            };
        }
        
        return {
            text: 'I\'m sorry, I\'m having trouble connecting to my brain right now. Please make sure the backend server is running on port 8000.',
            actions: []
        };
    }
    
    /* REAL BACKEND INTEGRATION:
     * 
     * const fetch = require('node-fetch');
     * 
     * const response = await fetch('http://localhost:8000/v1/chat', {
     *     method: 'POST',
     *     headers: {
     *         'Content-Type': 'application/json'
     *     },
     *     body: JSON.stringify({
     *         message: text,
     *         user_id: 'user-123'
     *     })
     * });
     * 
     * if (!response.ok) {
     *     throw new Error('Backend request failed');
     * }
     * 
     * const data = await response.json();
     * return {
     *     text: data.response,
     *     actions: data.actions || []
     * };
     */
}

/**
 * Generate unique session ID
 */
function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// ============= Serve Frontend =============

// Main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

// Error handler
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// ============= Start Server =============

app.listen(PORT, () => {
    console.log('╔════════════════════════════════════════════════╗');
    console.log('║                                                ║');
    console.log('║         SMARTII Frontend Server               ║');
    console.log('║                                                ║');
    console.log('╚════════════════════════════════════════════════╝');
    console.log('');
    console.log(`🚀 Server running on: http://localhost:${PORT}`);
    console.log(`📡 API endpoint: http://localhost:${PORT}/api`);
    console.log(`🎨 Frontend: http://localhost:${PORT}`);
    console.log('');
    console.log('📝 Integration notes:');
    console.log('   - Replace mock responses with real SMARTII backend calls');
    console.log('   - Backend should be running on: http://localhost:8000');
    console.log('   - Update API endpoints in script.js CONFIG object');
    console.log('');
    console.log('✨ Ready to assist!');
    console.log('');
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    server.close(() => {
        console.log('HTTP server closed');
    });
});
