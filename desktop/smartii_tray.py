"""
SMARTII System Tray Application
Always-on voice assistant with system tray icon
Works even when screen is locked
"""

import sys
import os
import threading
import json
import requests
import keyboard
import pystray
from PIL import Image, ImageDraw
from pathlib import Path
import speech_recognition as sr
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import win32gui
import win32con
import ctypes

# Get SMARTII directory
SMARTII_DIR = Path(__file__).parent.parent
BACKEND_URL = "http://localhost:8000"

class SMARTIITray:
    def __init__(self):
        self.listening = False
        self.wake_word_active = True
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configure recognizer for better performance
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        print("🎤 SMARTII Desktop Assistant Starting...")
        
        # Setup system tray
        self.icon = None
        self.create_icon()
        
        # Start voice listener thread
        self.voice_thread = threading.Thread(target=self.voice_listener, daemon=True)
        self.voice_thread.start()
        
        # Register global hotkey (Ctrl+Space)
        keyboard.add_hotkey('ctrl+space', self.manual_activate)
        
        print("✅ SMARTII is running! Say 'Hey SMARTII' or press Ctrl+Space")

    def create_icon(self):
        """Create system tray icon"""
        # Create icon image
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'black')
        dc = ImageDraw.Draw(image)
        dc.ellipse([10, 10, 54, 54], fill='cyan', outline='white')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem('SMARTII', self.show_status, default=True),
            pystray.MenuItem('Activate (Ctrl+Space)', self.manual_activate),
            pystray.MenuItem('Wake Word: ON', self.toggle_wake_word, checked=lambda item: self.wake_word_active),
            pystray.MenuItem('Settings', self.open_settings),
            pystray.MenuItem('Exit', self.exit_app)
        )
        
        self.icon = pystray.Icon("SMARTII", image, "SMARTII Assistant", menu)

    def voice_listener(self):
        """Always-on voice listener (works even when locked)"""
        with self.microphone as source:
            print("🎧 Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Voice listener active")
        
        while True:
            try:
                if not self.wake_word_active and not self.listening:
                    continue
                
                with self.microphone as source:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                
                try:
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"👂 Heard: {text}")
                    
                    # Check for wake word
                    if not self.listening and any(wake in text for wake in ['hey smartii', 'smartii', 'hey smart']):
                        print("🔥 Wake word detected!")
                        self.update_icon_listening(True)
                        self.listening = True
                        self.speak("Yes, I'm listening")
                        continue
                    
                    # Process command if listening
                    if self.listening:
                        self.process_command(text)
                        self.listening = False
                        self.update_icon_listening(False)
                
                except sr.UnknownValueError:
                    # Speech not recognized
                    if self.listening:
                        self.listening = False
                        self.update_icon_listening(False)
                except sr.RequestError as e:
                    print(f"❌ Recognition error: {e}")
            
            except Exception as e:
                print(f"⚠️ Voice listener error: {e}")
                continue

    def process_command(self, text):
        """Send command to SMARTII backend"""
        try:
            print(f"💬 Processing: {text}")
            
            # Send to backend
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": text, "client_id": "desktop"},
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                reply = data.get("text", "I didn't understand that")
                print(f"🤖 SMARTII: {reply}")
                
                # Speak response
                self.speak(reply)
                
                # Handle special actions (open URLs, etc.)
                if data.get("open_url") and data.get("url"):
                    os.startfile(data["url"])
            else:
                self.speak("Sorry, I'm having trouble connecting to my brain")
        
        except requests.Timeout:
            self.speak("Sorry, that took too long")
        except requests.ConnectionError:
            self.speak("Backend is not running. Please start it first")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.speak("Sorry, something went wrong")

    def speak(self, text):
        """Text-to-speech using Windows"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
        except:
            # Fallback to system speech
            os.system(f'powershell -c "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{text}\')"')

    def manual_activate(self):
        """Manually activate SMARTII with hotkey"""
        print("🎤 Manual activation (Ctrl+Space)")
        self.listening = True
        self.update_icon_listening(True)
        self.speak("Yes?")

    def toggle_wake_word(self):
        """Toggle wake word detection"""
        self.wake_word_active = not self.wake_word_active
        status = "enabled" if self.wake_word_active else "disabled"
        print(f"🔊 Wake word {status}")
        self.speak(f"Wake word {status}")

    def update_icon_listening(self, is_listening):
        """Update tray icon to show listening state"""
        if self.icon:
            color = 'lime' if is_listening else 'cyan'
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), 'black')
            dc = ImageDraw.Draw(image)
            dc.ellipse([10, 10, 54, 54], fill=color, outline='white')
            self.icon.icon = image

    def show_status(self):
        """Show status notification"""
        print("ℹ️ SMARTII Status:")
        print(f"  Wake Word: {'ON' if self.wake_word_active else 'OFF'}")
        print(f"  Listening: {'YES' if self.listening else 'NO'}")
        print(f"  Hotkey: Ctrl+Space")

    def open_settings(self):
        """Open SMARTII web interface"""
        os.startfile("http://localhost:3000")

    def exit_app(self):
        """Exit application"""
        print("👋 Shutting down SMARTII...")
        self.icon.stop()
        sys.exit(0)

    def run(self):
        """Run the system tray application"""
        self.icon.run()

if __name__ == "__main__":
    # Prevent screen lock from stopping microphone
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    
    app = SMARTIITray()
    app.run()
