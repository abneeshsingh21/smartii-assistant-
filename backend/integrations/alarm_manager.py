"""
Alarm & Reminder Manager for SMARTII
Handles alarm creation, reminders, and scheduled tasks using Windows Task Scheduler
"""

import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class AlarmManager:
    """Manages alarms and reminders using Windows Task Scheduler"""
    
    def __init__(self):
        self.data_dir = Path("data/alarms")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.alarms_file = self.data_dir / "alarms.json"
        self.alarms = self._load_alarms()
        
    def _load_alarms(self) -> List[Dict[str, Any]]:
        """Load saved alarms from JSON"""
        if self.alarms_file.exists():
            try:
                with open(self.alarms_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading alarms: {e}")
        return []
    
    def _save_alarms(self):
        """Save alarms to JSON"""
        try:
            with open(self.alarms_file, 'w', encoding='utf-8') as f:
                json.dump(self.alarms, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving alarms: {e}")
    
    def set_alarm(self, time_str: str, date_str: Optional[str] = None, message: str = "Alarm") -> Dict[str, Any]:
        """
        Set an alarm using Windows Task Scheduler
        
        Args:
            time_str: Time in format "HH:MM AM/PM" or "HH:MM"
            date_str: Optional date in format "YYYY-MM-DD" or "MM/DD/YYYY"
            message: Alarm message/label
            
        Returns:
            dict with alarm details
        """
        try:
            # Parse time
            alarm_time = self._parse_time(time_str)
            
            # Parse date (default to today)
            if date_str:
                alarm_date = self._parse_date(date_str)
            else:
                alarm_date = datetime.now().date()
            
            # Combine date and time
            alarm_datetime = datetime.combine(alarm_date, alarm_time)
            
            # If time has passed today, schedule for tomorrow
            if alarm_datetime <= datetime.now():
                alarm_datetime += timedelta(days=1)
            
            # Create unique task name
            task_name = f"SMARTII_Alarm_{alarm_datetime.strftime('%Y%m%d_%H%M%S')}"
            
            # Create Windows notification script
            script_path = self._create_alarm_script(task_name, message, alarm_datetime)
            
            # Schedule task using schtasks
            success = self._schedule_task(task_name, alarm_datetime, script_path)
            
            if success:
                # Save alarm info
                alarm_info = {
                    "id": task_name,
                    "datetime": alarm_datetime.isoformat(),
                    "message": message,
                    "status": "active",
                    "created": datetime.now().isoformat()
                }
                self.alarms.append(alarm_info)
                self._save_alarms()
                
                return {
                    "status": "success",
                    "alarm_time": alarm_datetime.strftime("%I:%M %p"),
                    "alarm_date": alarm_datetime.strftime("%B %d, %Y"),
                    "message": message,
                    "task_name": task_name
                }
            else:
                return {"status": "error", "message": "Failed to schedule alarm"}
                
        except Exception as e:
            logger.error(f"Error setting alarm: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_time(self, time_str: str) -> datetime.time:
        """Parse time string to datetime.time"""
        time_str = time_str.strip().upper()
        
        # Try different formats
        formats = [
            "%I:%M %p",  # 7:10 PM
            "%H:%M",     # 19:10
            "%I %p",     # 7 PM
            "%H",        # 19
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.time()
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse time: {time_str}")
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse date string to datetime.date"""
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%Y-%m-%d",      # 2025-11-18
            "%m/%d/%Y",      # 11/18/2025
            "%d/%m/%Y",      # 18/11/2025
            "%B %d, %Y",     # November 18, 2025
            "%b %d, %Y",     # Nov 18, 2025
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date()
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    def _create_alarm_script(self, task_name: str, message: str, alarm_time: datetime) -> str:
        """Create PowerShell script for alarm notification"""
        script_dir = self.data_dir / "scripts"
        script_dir.mkdir(exist_ok=True)
        
        script_path = script_dir / f"{task_name}.ps1"
        
        # PowerShell script to show notification and play sound
        ps_script = f'''
# SMARTII Alarm Notification
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Speech

$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$notification.BalloonTipTitle = "SMARTII Alarm"
$notification.BalloonTipText = "{message}"
$notification.Visible = $true
$notification.ShowBalloonTip(10000)

# Play notification sound
[console]::beep(800, 500)
[console]::beep(1000, 500)
[console]::beep(800, 500)

# Speak the message
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Speak("Alarm! {message}")

Start-Sleep -Seconds 15
$notification.Dispose()
'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(ps_script)
        
        return str(script_path)
    
    def _schedule_task(self, task_name: str, alarm_time: datetime, script_path: str) -> bool:
        """Schedule task using Windows Task Scheduler"""
        try:
            # Format for schtasks
            date_str = alarm_time.strftime("%m/%d/%Y")
            time_str = alarm_time.strftime("%H:%M")
            
            # Create scheduled task
            cmd = [
                "schtasks",
                "/Create",
                "/TN", task_name,
                "/TR", f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
                "/SC", "ONCE",
                "/SD", date_str,
                "/ST", time_str,
                "/F"  # Force create (overwrite if exists)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                logger.info(f"Alarm scheduled: {task_name} at {alarm_time}")
                return True
            else:
                logger.error(f"Failed to schedule alarm: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error scheduling task: {e}")
            return False
    
    def list_alarms(self) -> List[Dict[str, Any]]:
        """List all active alarms"""
        active_alarms = []
        for alarm in self.alarms:
            if alarm["status"] == "active":
                alarm_time = datetime.fromisoformat(alarm["datetime"])
                if alarm_time > datetime.now():
                    active_alarms.append(alarm)
                else:
                    # Mark as expired
                    alarm["status"] = "expired"
        
        self._save_alarms()
        return active_alarms
    
    def cancel_alarm(self, task_name: str) -> Dict[str, Any]:
        """Cancel an alarm"""
        try:
            # Delete from Task Scheduler
            cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Update alarm status
            for alarm in self.alarms:
                if alarm["id"] == task_name:
                    alarm["status"] = "cancelled"
            
            self._save_alarms()
            
            return {"status": "success", "message": f"Alarm {task_name} cancelled"}
            
        except Exception as e:
            logger.error(f"Error cancelling alarm: {e}")
            return {"status": "error", "message": str(e)}
    
    def set_reminder(self, minutes: int, message: str = "Reminder") -> Dict[str, Any]:
        """Set a reminder after specified minutes"""
        alarm_time = datetime.now() + timedelta(minutes=minutes)
        time_str = alarm_time.strftime("%H:%M")
        return self.set_alarm(time_str, message=message)
