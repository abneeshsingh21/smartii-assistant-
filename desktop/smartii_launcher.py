"""
SMARTII Desktop - Complete Standalone Application
One-click launcher that starts everything automatically
No VS Code or manual commands needed!
"""

import sys
import os
import time
import subprocess
import threading
import webbrowser
from pathlib import Path
import psutil
import socket

# ANSI color codes for terminal
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SMARTIILauncher:
    def __init__(self):
        self.smartii_dir = Path(__file__).parent.parent
        self.backend_dir = self.smartii_dir / "backend"
        self.frontend_dir = self.smartii_dir / "frontend-v2"
        self.desktop_dir = self.smartii_dir / "desktop"
        
        self.backend_process = None
        self.frontend_process = None
        self.tray_process = None
        
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("=" * 60)
        print("  ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗██╗██╗")
        print("  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██║██║")
        print("  ███████╗██╔████╔██║███████║██████╔╝   ██║   ██║██║")
        print("  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██║██║")
        print("  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ██║██║")
        print("  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝")
        print("=" * 60)
        print(f"  Your Intelligent AI Assistant - Desktop Edition{Colors.END}")
        print()

    def check_port(self, port):
        """Check if port is available"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0

    def kill_existing_processes(self):
        """Kill any existing SMARTII processes"""
        print(f"{Colors.YELLOW}🔍 Checking for existing SMARTII processes...{Colors.END}")
        
        killed_any = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('smartii' in str(cmd).lower() for cmd in cmdline):
                    if proc.pid != os.getpid():  # Don't kill ourselves
                        print(f"   Stopping process: {proc.info['name']} (PID: {proc.pid})")
                        proc.kill()
                        killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed_any:
            time.sleep(2)
            print(f"{Colors.GREEN}✅ Cleaned up existing processes{Colors.END}")
        else:
            print(f"{Colors.GREEN}✅ No existing processes found{Colors.END}")

    def start_backend(self):
        """Start backend server"""
        print(f"\n{Colors.CYAN}🚀 Starting Backend Server...{Colors.END}")
        
        if self.check_port(8000):
            print(f"{Colors.GREEN}✅ Backend already running on port 8000{Colors.END}")
            return True
        
        try:
            os.chdir(str(self.backend_dir))
            self.backend_process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Wait for backend to start
            print(f"   Waiting for backend to initialize...", end="", flush=True)
            for i in range(30):
                if self.check_port(8000):
                    print(f"\n{Colors.GREEN}✅ Backend running at http://localhost:8000{Colors.END}")
                    return True
                time.sleep(0.5)
                print(".", end="", flush=True)
            
            print(f"\n{Colors.RED}❌ Backend failed to start{Colors.END}")
            return False
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error starting backend: {e}{Colors.END}")
            return False

    def start_frontend(self):
        """Start frontend server"""
        print(f"\n{Colors.CYAN}🌐 Starting Web Interface...{Colors.END}")
        
        if self.check_port(3000):
            print(f"{Colors.GREEN}✅ Frontend already running on port 3000{Colors.END}")
            return True
        
        try:
            os.chdir(str(self.frontend_dir))
            
            # Check if node_modules exists
            if not (self.frontend_dir / "node_modules").exists():
                print(f"   Installing dependencies (one-time setup)...")
                install = subprocess.run(
                    ["npm", "install"],
                    capture_output=True,
                    text=True
                )
                if install.returncode != 0:
                    print(f"{Colors.YELLOW}⚠️ npm install had issues, continuing anyway...{Colors.END}")
            
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Wait for frontend to start
            print(f"   Waiting for web interface...", end="", flush=True)
            for i in range(60):
                if self.check_port(3000):
                    print(f"\n{Colors.GREEN}✅ Web interface running at http://localhost:3000{Colors.END}")
                    return True
                time.sleep(0.5)
                print(".", end="", flush=True)
            
            print(f"\n{Colors.YELLOW}⚠️ Frontend may take longer to start{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Frontend start issue: {e}{Colors.END}")
            print(f"   You can still use voice commands!")
            return True

    def start_voice_assistant(self):
        """Start voice assistant with system tray"""
        print(f"\n{Colors.CYAN}🎤 Starting Voice Assistant...{Colors.END}")
        
        try:
            os.chdir(str(self.desktop_dir))
            self.tray_process = subprocess.Popen(
                [sys.executable, "smartii_tray.py"],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            time.sleep(2)
            print(f"{Colors.GREEN}✅ Voice assistant active (system tray){Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error starting voice assistant: {e}{Colors.END}")
            return False

    def open_browser(self):
        """Open web interface in browser"""
        time.sleep(3)
        try:
            webbrowser.open('http://localhost:3000')
            print(f"{Colors.GREEN}✅ Opened web interface in browser{Colors.END}")
        except:
            print(f"{Colors.YELLOW}⚠️ Please open http://localhost:3000 manually{Colors.END}")

    def show_usage(self):
        """Show usage instructions"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}═══════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}  SMARTII is now running!{Colors.END}")
        print(f"{Colors.CYAN}═══════════════════════════════════════════════════════{Colors.END}\n")
        
        print(f"{Colors.BOLD}🎤 Voice Activation:{Colors.END}")
        print(f"   • Say {Colors.CYAN}'Hey SMARTII'{Colors.END} to wake up")
        print(f"   • Press {Colors.CYAN}Ctrl+Space{Colors.END} for manual activation")
        print()
        
        print(f"{Colors.BOLD}🌐 Web Interface:{Colors.END}")
        print(f"   • {Colors.CYAN}http://localhost:3000{Colors.END}")
        print()
        
        print(f"{Colors.BOLD}🎯 System Tray:{Colors.END}")
        print(f"   • Look for cyan icon in bottom-right")
        print(f"   • Right-click for options")
        print(f"   • Green = listening, Cyan = idle")
        print()
        
        print(f"{Colors.BOLD}💡 Try These Commands:{Colors.END}")
        print(f"   • 'Hey SMARTII, what's the weather?'")
        print(f"   • 'Hey SMARTII, play Despacito'")
        print(f"   • 'Hey SMARTII, open Chrome'")
        print(f"   • 'Hey SMARTII, search for Python tutorials'")
        print()
        
        print(f"{Colors.BOLD}🔒 Works When Locked:{Colors.END}")
        print(f"   • Lock your screen (Windows+L)")
        print(f"   • SMARTII still listens and responds!")
        print()
        
        print(f"{Colors.CYAN}═══════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.END}\n")

    def monitor_processes(self):
        """Monitor and restart crashed processes"""
        while True:
            try:
                # Check backend
                if self.backend_process and self.backend_process.poll() is not None:
                    print(f"{Colors.RED}⚠️ Backend crashed, restarting...{Colors.END}")
                    self.start_backend()
                
                # Check voice assistant
                if self.tray_process and self.tray_process.poll() is not None:
                    print(f"{Colors.RED}⚠️ Voice assistant crashed, restarting...{Colors.END}")
                    self.start_voice_assistant()
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break

    def cleanup(self):
        """Clean up all processes"""
        print(f"\n{Colors.YELLOW}🛑 Shutting down SMARTII...{Colors.END}")
        
        processes = [
            ("Backend", self.backend_process),
            ("Frontend", self.frontend_process),
            ("Voice Assistant", self.tray_process)
        ]
        
        for name, proc in processes:
            if proc and proc.poll() is None:
                print(f"   Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print(f"{Colors.GREEN}✅ SMARTII stopped successfully{Colors.END}")
        print(f"{Colors.CYAN}See you later! 👋{Colors.END}\n")

    def run(self):
        """Main run method"""
        try:
            # Clean up any existing processes
            self.kill_existing_processes()
            
            # Start all components
            if not self.start_backend():
                print(f"{Colors.RED}Failed to start backend. Exiting.{Colors.END}")
                return
            
            self.start_frontend()
            
            if not self.start_voice_assistant():
                print(f"{Colors.YELLOW}Voice assistant failed, but you can use web interface{Colors.END}")
            
            # Open browser
            threading.Thread(target=self.open_browser, daemon=True).start()
            
            # Show usage
            self.show_usage()
            
            # Monitor processes
            self.monitor_processes()
            
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

if __name__ == "__main__":
    launcher = SMARTIILauncher()
    launcher.run()
