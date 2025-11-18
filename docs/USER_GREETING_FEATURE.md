# User Greeting & Profile System

## Overview
SMARTII now features a personalized greeting system that remembers your name and greets you warmly every time you visit!

## Features

### 1. **First-Time Welcome Modal**
When you open SMARTII for the first time, you'll see a beautiful welcome screen asking:
- **"What's your name?"** - Simply enter your name to get started
- **Gmail Sign-in Option** - Link your Gmail for enhanced memory across devices
- **Skip Option** - Start using SMARTII immediately without setup

### 2. **Personalized Greetings**
Once SMARTII knows your name, you'll receive time-based personalized greetings:
- **Morning (5 AM - 12 PM)**: "Good morning, [Your Name]!"
- **Afternoon (12 PM - 5 PM)**: "Good afternoon, [Your Name]!"
- **Evening (5 PM - 10 PM)**: "Good evening, [Your Name]!"
- **Night (10 PM - 5 AM)**: "Hello, [Your Name]!"

### 3. **Usage-Based Messages**
SMARTII tracks your sessions and adds personality:
- **First visit**: "It's great to see you again for the first time!"
- **Early visits (2-4 sessions)**: "Welcome back! What can I do for you?"
- **Frequent user (5+ sessions)**: "Always a pleasure! What's on your mind?"

### 4. **Persistent Memory**
- Your name is **never forgotten** - stored locally in your profile
- Profile includes:
  - Name
  - Email (if Gmail login used)
  - Created date
  - Last seen timestamp
  - Total sessions count
  - Total interactions count
  - Preferences (voice type, language, theme)

### 5. **Gmail Integration** (Optional)
Benefits of linking your Gmail:
- **Cross-device sync** - Access your profile from any device
- **Enhanced memory** - Better context for personalized responses
- **Future features** - Calendar integration, email commands, etc.

## Technical Implementation

### Backend Endpoints

#### 1. `/greeting` (POST)
Get personalized greeting for user
```json
Request: {
  "client_id": "client_abc123"
}

Response: {
  "greeting": "Good morning, John!",
  "is_new_user": false,
  "profile": {
    "user_id": "client_abc123",
    "name": "John",
    "email": "john@gmail.com",
    "created_at": "2025-01-15T10:30:00",
    "last_seen": "2025-01-16T09:15:00",
    "stats": {
      "total_sessions": 5,
      "total_interactions": 42
    }
  }
}
```

#### 2. `/set-name` (POST)
Set user's name
```json
Request: {
  "client_id": "client_abc123",
  "name": "John"
}

Response: {
  "success": true,
  "message": "Great to meet you, John! I'll remember your name from now on.",
  "profile": { ... }
}
```

#### 3. `/gmail-login` (POST)
Link Gmail account to profile
```json
Request: {
  "client_id": "client_abc123",
  "email": "john@gmail.com",
  "name": "John"
}

Response: {
  "success": true,
  "message": "Successfully linked john@gmail.com to your profile!",
  "profile": { ... }
}
```

### Data Storage
User profiles are stored in: `backend/data/profiles/{client_id}.json`

Example profile:
```json
{
  "user_id": "client_abc123",
  "name": "John",
  "email": "john@gmail.com",
  "created_at": "2025-01-15T10:30:00.000000",
  "last_seen": "2025-01-16T09:15:00.000000",
  "preferences": {
    "voice_type": "female",
    "language": "en-US",
    "theme": "dark"
  },
  "stats": {
    "total_sessions": 5,
    "total_interactions": 42,
    "favorite_commands": []
  }
}
```

## User Experience Flow

### New User Flow
1. User opens SMARTII for the first time
2. Welcome modal appears: "Hello! I'm SMARTII. May I know your name?"
3. User enters name "John" → Clicks "Let's Get Started!"
4. SMARTII responds: "Great to meet you, John! I'll remember your name from now on."
5. Profile created and saved

### Returning User Flow
1. User opens SMARTII
2. Backend checks for existing profile
3. SMARTII greets: "Good morning, John! Welcome back! What can I do for you?"
4. Session count increments automatically

### Gmail Login Flow
1. User clicks "Sign in with Google" on welcome modal
2. Enters Gmail address (simplified - full OAuth2 for production)
3. Profile linked with email
4. SMARTII: "Welcome back, John! Your profile is now synced with john@gmail.com"

## Privacy & Security

- **Local-first**: Profiles stored locally on your device by default
- **Optional cloud sync**: Gmail login is completely optional
- **No password storage**: Email is only for identification
- **Transparent**: All profile data is visible and under your control

## Future Enhancements

1. **Full OAuth2 Gmail Integration** - Secure Google sign-in
2. **Profile Export/Import** - Move profiles between devices
3. **Multiple profiles** - Family sharing
4. **Advanced preferences** - Custom wake words, voice cloning
5. **Usage analytics** - Insights on most-used features
6. **Personalized AI personality** - Learns your communication style

## Testing

To test locally:
1. Clear browser data to simulate first-time user
2. Open SMARTII - Welcome modal should appear
3. Enter your name and click "Let's Get Started!"
4. Reload page - You should see personalized greeting
5. Check `backend/data/profiles/` for your profile JSON

## Deployment

Changes have been pushed to GitHub and will auto-deploy to:
- **Backend**: Render (https://smartii.onrender.com)
- **Frontend**: Vercel (https://smartii-assistant-lhftzbzcp-abneesh-singhs-projects-b0cc760e.vercel.app)

Wait ~2 minutes for deployment, then test live!

---

**Created by**: Abneesh Singh  
**Date**: January 2025  
**Version**: 2.1.0
