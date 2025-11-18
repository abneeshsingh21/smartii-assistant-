# SMARTII Frontend - Premium AI Voice Assistant UI

A stunning, production-ready user interface for the SMARTII AI voice assistant. Built with modern web technologies featuring glassmorphism design, smooth animations, and a premium user experience comparable to Apple Siri, Amazon Alexa, and Google Assistant.

## 🎨 Features

### Visual Design
- **Futuristic Glassmorphism**: Blur effects, transparency, and premium aesthetics
- **Gradient Backgrounds**: Animated neon blue/cyan glows
- **Smooth Animations**: CSS transitions and keyframe animations
- **Dark/Light Mode**: Toggle between themes with smooth transitions
- **Responsive Design**: Perfect on mobile, tablet, and desktop
- **Neon Borders & Glows**: Modern SaaS-grade visual effects

### Voice Interface
- **Microphone Activation**: Large, animated button with pulse effects
- **Live Waveform**: Real-time audio visualization during listening
- **Speech Recognition**: Browser-based voice input (Chrome, Edge, Safari)
- **Text-to-Speech**: AI responses read aloud with customizable voice
- **Transcription Display**: Real-time speech-to-text display

### Chat Interface
- **Chat Bubbles**: Clean, modern message display
- **Typing Indicator**: Animated dots while AI processes
- **Auto-scroll**: Automatic scrolling to latest messages
- **Message History**: Persistent conversation log
- **Clear Chat**: One-click conversation reset

### Settings & Customization
- **Voice Settings**: Male/Female/Neutral voice selection
- **Speech Rate**: Adjustable TTS speed (0.5x - 2x)
- **Always Listening**: Wake word mode (optional)
- **Language Selection**: Multi-language support
- **Theme Toggle**: Dark/Light mode with preferences saved
- **Animations Toggle**: Enable/disable animations

### Memory & Learning
- **Routines Display**: View learned behavioral patterns
- **Preferences**: Manage saved user preferences
- **Task History**: Track completed tasks
- **Statistics**: Visual representation of AI learning

## 📁 Folder Structure

```
frontend-v2/
├── server.js                 # Node.js Express server
├── package.json              # Dependencies and scripts
├── README.md                 # This file
├── public/
│   ├── index.html           # Main HTML file
│   ├── css/
│   │   └── style.css        # Complete styling (glassmorphism, animations)
│   ├── js/
│   │   └── script.js        # Frontend logic (voice, chat, UI)
│   └── assets/
│       └── icons/           # Icon assets (optional)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ installed
- Modern browser (Chrome, Edge, Safari recommended for voice features)
- SMARTII backend running on `http://localhost:8000` (optional for full features)

### Installation

1. **Navigate to frontend directory**:
```bash
cd frontend-v2
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the server**:
```bash
npm start
```

4. **Open in browser**:
```
http://localhost:3000
```

### Development Mode

For auto-reload during development:
```bash
npm run dev
```

## 🔧 Configuration

### API Integration

Edit `public/js/script.js` to configure backend connection:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:3000/api',
    BACKEND_WS_URL: 'ws://localhost:8000/ws',
    ANIMATION_ENABLED: true,
    AUTO_SCROLL: true
};
```

### Connect to Real SMARTII Backend

The frontend includes mock responses. To connect to your real SMARTII backend:

1. **Update `server.js`**:

```javascript
// Replace mock function with real API call
async function processWithSmartiiBackend(text) {
    const fetch = require('node-fetch');
    
    const response = await fetch('http://localhost:8000/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            user_id: 'user-123'
        })
    });
    
    const data = await response.json();
    return {
        text: data.response,
        actions: data.actions || []
    };
}
```

2. **Update API endpoints** in `script.js`:

```javascript
// Change sendMessageToBackend() function
async function sendMessageToBackend(text) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    
    const data = await response.json();
    return data;
}
```

## 🎯 API Endpoints

The frontend server provides the following endpoints:

### Health Check
```
GET /api/health
```

### Process Text Message
```
POST /api/process-text
Body: { "text": "Your message" }
Response: { "success": true, "text": "AI response", "actions": [] }
```

### Start Recording
```
POST /api/start-recording
Response: { "success": true, "sessionId": "..." }
```

### Stop Recording
```
POST /api/stop-recording
Body: { "sessionId": "..." }
Response: { "success": true, "audioUrl": "..." }
```

### Get Suggestions
```
GET /api/suggestions
Response: { "success": true, "suggestions": [...] }
```

### Get Routines
```
GET /api/memory/routines
Response: { "success": true, "routines": [...] }
```

### Settings
```
GET /api/settings
PUT /api/settings
```

## 🎨 Customization

### Change Colors

Edit CSS variables in `public/css/style.css`:

```css
:root {
    --accent-primary: #00d9ff;      /* Main accent color */
    --accent-secondary: #0066ff;    /* Secondary accent */
    --bg-primary: #0a0e27;          /* Background color */
    --text-primary: #ffffff;        /* Text color */
}
```

### Modify Animations

Animations are controlled via CSS:

```css
@keyframes micPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

/* Disable all animations */
* { animation: none !important; }
```

### Change Fonts

Update Google Fonts import in `index.html`:

```html
<link href="https://fonts.googleapis.com/css2?family=Your+Font&display=swap" rel="stylesheet">
```

Then update CSS:

```css
:root {
    --font-primary: 'Your Font', sans-serif;
}
```

## 🌐 Browser Support

| Browser | Voice Recognition | Text-to-Speech | UI |
|---------|------------------|----------------|-----|
| Chrome 90+ | ✅ | ✅ | ✅ |
| Edge 90+ | ✅ | ✅ | ✅ |
| Safari 14+ | ✅ | ✅ | ✅ |
| Firefox 90+ | ❌ | ✅ | ✅ |

**Note**: Firefox doesn't support Web Speech API. Voice features won't work.

## 📱 Responsive Breakpoints

- **Mobile**: < 480px
- **Tablet**: 481px - 768px
- **Laptop**: 769px - 1024px
- **Desktop**: 1025px - 1440px
- **Ultrawide**: > 1440px

## 🔊 Voice Features

### Speech Recognition
- Powered by Web Speech API
- Supports continuous and interim results
- Real-time transcription display
- Error handling and retry logic

### Text-to-Speech
- Multiple voice options
- Adjustable speech rate (0.5x - 2x)
- Volume control
- Voice selection (male/female/neutral)

### Always Listening Mode
- Wake word detection (planned feature)
- Background voice processing
- Low power consumption

## 🛠️ Development

### File Overview

**index.html**
- Semantic HTML5 structure
- Accessible ARIA labels
- SEO meta tags
- External CSS/JS references

**style.css**
- CSS variables for theming
- Glassmorphism effects
- Responsive grid layouts
- Smooth animations
- Dark/Light mode support

**script.js**
- State management
- Speech recognition setup
- Waveform animation (Canvas)
- Chat functionality
- Settings management
- API communication

**server.js**
- Express.js backend
- Static file serving
- API endpoint routing
- Mock responses (replace with real backend)
- Error handling

### Adding New Features

1. **Add UI Component** in `index.html`
2. **Style Component** in `style.css`
3. **Add Logic** in `script.js`
4. **Create API Endpoint** in `server.js`
5. **Connect to Backend** (optional)

## 🐛 Troubleshooting

### Voice Recognition Not Working
- Check browser compatibility (Chrome/Edge/Safari)
- Ensure HTTPS (required for mic access)
- Grant microphone permissions
- Check console for errors

### Waveform Not Displaying
- Canvas rendering requires listening state
- Check browser console for errors
- Ensure animations are enabled

### API Errors
- Verify backend is running on `http://localhost:8000`
- Check CORS settings
- Review server logs
- Confirm endpoint URLs in CONFIG

### Styling Issues
- Clear browser cache
- Check CSS variable values
- Verify theme class on body element
- Inspect element in DevTools

## 📦 Deployment

### Production Build

1. **Optimize assets**:
```bash
# Minify CSS
npm install -g clean-css-cli
cleancss -o public/css/style.min.css public/css/style.css

# Minify JS
npm install -g uglify-js
uglifyjs public/js/script.js -o public/js/script.min.js
```

2. **Update references** in `index.html`:
```html
<link rel="stylesheet" href="/css/style.min.css">
<script src="/js/script.min.js"></script>
```

3. **Set production environment**:
```bash
export NODE_ENV=production
npm start
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t smartii-frontend .
docker run -p 3000:3000 smartii-frontend
```

### Cloud Deployment

**Heroku**:
```bash
heroku create smartii-frontend
git push heroku main
heroku open
```

**Vercel**:
```bash
vercel deploy
```

**AWS/Azure/GCP**: Use Docker container or Node.js runtime

## 🔐 Security

- **Input Validation**: All user inputs are sanitized
- **CORS**: Configured for specific origins
- **HTTPS**: Required for voice features in production
- **API Keys**: Store in environment variables
- **Rate Limiting**: Implement on production server

## 📄 License

MIT License - Feel free to use in your projects

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Enhanced waveform visualizations
- More animation options
- Additional voice features
- Better mobile UX
- Accessibility improvements

## 📞 Support

For issues or questions:
- Check documentation
- Review browser console
- Verify backend connection
- Test in different browsers

## 🎉 Credits

- Design inspired by Apple Siri, Alexa, and Google Assistant
- Built with vanilla JavaScript (no frameworks)
- Icons: SVG inline
- Fonts: Google Fonts (Inter, Space Grotesk)

---

**Built with ❤️ for SMARTII - Your JARVIS-level AI Assistant**
