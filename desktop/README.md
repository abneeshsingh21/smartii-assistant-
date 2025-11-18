# SMARTII Desktop Installation Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Requirements
```powershell
cd C:\Users\lenovo\Desktop\smartii\desktop
pip install -r requirements.txt
```

### Step 2: Setup Auto-Start
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_autostart.ps1
```

### Step 3: Start SMARTII
```powershell
powershell -ExecutionPolicy Bypass -File .\start_smartii.ps1
```

---

## ✨ Features

### 🎤 Always Listening
- Works even when **screen is locked**
- Say "Hey SMARTII" anytime to activate
- Press **Ctrl+Space** for manual activation

### 🔧 System Tray Integration
- Lives in your system tray (bottom-right)
- Right-click icon for quick access
- Green icon = listening, Cyan = idle

### 🚀 Auto-Start on Boot
- Starts automatically when Windows boots
- Backend runs in background 24/7
- No need to manually start

### 🎯 Full System Control
- Open any application
- Control system volume/brightness
- Search the web
- Play music/videos
- Send messages
- And much more!

---

## 📋 Usage

### Voice Commands
```
"Hey SMARTII, what's the weather?"
"Hey SMARTII, play Despacito"
"Hey SMARTII, open Chrome"
"Hey SMARTII, search for Python tutorials"
"Hey SMARTII, send a message to John"
```

### Keyboard Shortcut
Press **Ctrl+Space** anywhere to activate SMARTII

### System Tray Menu
Right-click SMARTII icon:
- **Activate** - Manual voice activation
- **Wake Word ON/OFF** - Toggle always-listening
- **Settings** - Open web interface
- **Exit** - Close SMARTII

---

## 🔒 Works When Locked

SMARTII uses Windows audio APIs that work even when your screen is locked:
- Microphone stays active
- Wake word detection continues
- Commands are processed normally
- Responses are spoken

**Security Note:** You can disable wake word and use Ctrl+Space only for better privacy.

---

## 🛠️ Troubleshooting

### Microphone Not Working
1. Check Windows microphone permissions
2. Run as Administrator once
3. Test microphone in Windows settings

### Backend Not Starting
```powershell
# Start backend manually first
cd C:\Users\lenovo\Desktop\smartii\backend
python app.py
```

### Voice Not Recognized
- Speak clearly and closer to microphone
- Reduce background noise
- Adjust microphone sensitivity in Windows

---

## 🔧 Advanced Configuration

### Change Wake Word
Edit `smartii_tray.py` line 110:
```python
wake_words = ['hey smartii', 'smartii', 'computer', 'jarvis']
```

### Change Hotkey
Edit `smartii_tray.py` line 45:
```python
keyboard.add_hotkey('ctrl+alt+s', self.manual_activate)
```

### Backend URL
If running backend on different port:
Edit `smartii_tray.py` line 21:
```python
BACKEND_URL = "http://localhost:YOUR_PORT"
```

---

## 📊 System Requirements

- **OS:** Windows 10/11
- **Python:** 3.8 or higher
- **RAM:** 2GB minimum
- **Microphone:** Required
- **Internet:** Required for AI processing

---

## 🎉 You're All Set!

SMARTII is now your personal desktop assistant!

Say **"Hey SMARTII"** or press **Ctrl+Space** to start using it.
