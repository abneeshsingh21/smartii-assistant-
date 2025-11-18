"""
SMARTII Desktop Service
Runs SMARTII backend as a Windows service that starts on boot
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time
from pathlib import Path

class SMARTIIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SMARTII"
    _svc_display_name_ = "SMARTII AI Assistant"
    _svc_description_ = "Intelligent AI assistant running 24/7"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.backend_process = None
        
        # Get SMARTII directory
        self.smartii_dir = Path(__file__).parent.parent
        self.backend_dir = self.smartii_dir / "backend"

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.backend_process:
            self.backend_process.terminate()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        """Main service loop"""
        while True:
            # Start backend
            try:
                os.chdir(str(self.backend_dir))
                self.backend_process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                servicemanager.LogInfoMsg("SMARTII backend started")
                
                # Wait for stop event or process exit
                while True:
                    rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                    if rc == win32event.WAIT_OBJECT_0:
                        # Stop requested
                        break
                    
                    # Check if backend is still running
                    if self.backend_process.poll() is not None:
                        # Backend crashed, restart
                        servicemanager.LogErrorMsg("SMARTII backend crashed, restarting...")
                        time.sleep(5)
                        break
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error running SMARTII: {e}")
                time.sleep(10)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SMARTIIService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SMARTIIService)
