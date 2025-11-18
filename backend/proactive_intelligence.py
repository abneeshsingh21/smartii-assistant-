"""
SMARTII Proactive Intelligence System
Anticipates user needs and provides contextual suggestions
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProactiveIntelligence:
    def __init__(self):
        self.routines = {}
        self.suggestions = []
        self.context = {}
        self.learning_data = {
            "daily_patterns": [],
            "location_history": [],
            "app_usage": [],
            "preferences": {}
        }
        
    async def analyze_context(self, user_data: Dict) -> List[Dict]:
        """Analyze current context and generate proactive suggestions"""
        suggestions = []
        current_time = datetime.now()
        
        # Time-based suggestions
        suggestions.extend(self._get_time_based_suggestions(current_time))
        
        # Routine-based suggestions
        suggestions.extend(self._get_routine_suggestions(current_time))
        
        # Context-aware suggestions
        suggestions.extend(self._get_contextual_suggestions(user_data))
        
        return suggestions
    
    def _get_time_based_suggestions(self, current_time: datetime) -> List[Dict]:
        """Generate suggestions based on time of day"""
        suggestions = []
        hour = current_time.hour
        
        # Morning suggestions (6 AM - 9 AM)
        if 6 <= hour < 9:
            suggestions.append({
                "type": "morning_routine",
                "message": "Good morning! Would you like me to read today's schedule and weather?",
                "priority": "high",
                "actions": ["read_schedule", "get_weather"]
            })
            
        # Workday start (9 AM - 10 AM)
        elif 9 <= hour < 10:
            suggestions.append({
                "type": "work_mode",
                "message": "Starting work soon? Should I activate work mode? (Focus music, turn on desk lamp)",
                "priority": "medium",
                "actions": ["activate_work_mode"]
            })
            
        # Lunch time (12 PM - 1 PM)
        elif 12 <= hour < 13:
            suggestions.append({
                "type": "lunch_reminder",
                "message": "It's lunch time! Want me to order your usual meal?",
                "priority": "low",
                "actions": ["order_food"]
            })
            
        # Afternoon coffee (3 PM - 4 PM)
        elif 15 <= hour < 16:
            suggestions.append({
                "type": "coffee_break",
                "message": "Time for your afternoon coffee? Should I remind you to take a break?",
                "priority": "low",
                "actions": ["set_break_reminder"]
            })
            
        # Evening wind-down (7 PM - 9 PM)
        elif 19 <= hour < 21:
            suggestions.append({
                "type": "evening_routine",
                "message": "Evening routine? I can dim the lights and prepare your relaxation playlist.",
                "priority": "medium",
                "actions": ["activate_evening_mode"]
            })
            
        # Bedtime (10 PM - 11 PM)
        elif 22 <= hour < 23:
            suggestions.append({
                "type": "sleep_mode",
                "message": "Getting late! Should I activate sleep mode? (Lock doors, turn off lights, set alarm)",
                "priority": "high",
                "actions": ["activate_sleep_mode"]
            })
            
        return suggestions
    
    def _get_routine_suggestions(self, current_time: datetime) -> List[Dict]:
        """Generate suggestions based on learned routines"""
        suggestions = []
        
        # Check learned routines
        day_of_week = current_time.strftime("%A")
        time_slot = f"{current_time.hour:02d}:00"
        
        routine_key = f"{day_of_week}_{time_slot}"
        if routine_key in self.routines:
            routine = self.routines[routine_key]
            suggestions.append({
                "type": "routine",
                "message": f"You usually {routine['action']} around this time. Want me to help?",
                "priority": "medium",
                "actions": [routine['action']]
            })
            
        return suggestions
    
    def _get_contextual_suggestions(self, user_data: Dict) -> List[Dict]:
        """Generate context-aware suggestions"""
        suggestions = []
        
        # Battery low suggestion
        if user_data.get("battery_level", 100) < 20:
            suggestions.append({
                "type": "battery_warning",
                "message": "Your phone battery is low ({}%). Should I remind you to charge it?".format(
                    user_data.get("battery_level")
                ),
                "priority": "high",
                "actions": ["set_charge_reminder"]
            })
            
        # Calendar event upcoming
        if user_data.get("next_meeting"):
            meeting = user_data["next_meeting"]
            time_until = meeting.get("minutes_until", 0)
            
            if 10 <= time_until <= 15:
                suggestions.append({
                    "type": "meeting_reminder",
                    "message": f"Meeting with {meeting['attendees']} in {time_until} minutes. Need any preparation?",
                    "priority": "high",
                    "actions": ["prepare_meeting"]
                })
                
        # Traffic alert
        if user_data.get("has_commute") and user_data.get("traffic_heavy"):
            suggestions.append({
                "type": "traffic_alert",
                "message": "Heavy traffic detected! Leave now to reach on time, or should I reschedule?",
                "priority": "high",
                "actions": ["start_navigation", "reschedule_meeting"]
            })
            
        # Weather-based suggestions
        if user_data.get("weather"):
            weather = user_data["weather"]
            if weather.get("rain_expected"):
                suggestions.append({
                    "type": "weather_alert",
                    "message": "Rain expected today. Don't forget your umbrella!",
                    "priority": "medium",
                    "actions": ["add_reminder"]
                })
                
        return suggestions
    
    async def learn_routine(self, action: str, timestamp: datetime):
        """Learn user routines from repeated actions"""
        day_of_week = timestamp.strftime("%A")
        time_slot = f"{timestamp.hour:02d}:00"
        routine_key = f"{day_of_week}_{time_slot}"
        
        if routine_key not in self.routines:
            self.routines[routine_key] = {
                "action": action,
                "count": 1,
                "last_performed": timestamp.isoformat()
            }
        else:
            self.routines[routine_key]["count"] += 1
            self.routines[routine_key]["last_performed"] = timestamp.isoformat()
            
        # Save to persistent storage
        self._save_routines()
        
    def _save_routines(self):
        """Save learned routines to file"""
        try:
            with open("data/routines.json", "w") as f:
                json.dump(self.routines, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save routines: {e}")
            
    def _load_routines(self):
        """Load learned routines from file"""
        try:
            with open("data/routines.json", "r") as f:
                self.routines = json.load(f)
        except FileNotFoundError:
            logger.info("No saved routines found")
        except Exception as e:
            logger.error(f"Failed to load routines: {e}")
            
    async def get_smart_suggestions(self, query: str, context: Dict) -> List[str]:
        """Get smart suggestions based on query and context"""
        suggestions = []
        query_lower = query.lower()
        
        # Meeting-related suggestions
        if "meeting" in query_lower:
            suggestions.extend([
                "Would you like me to check everyone's availability?",
                "Should I prepare the meeting agenda?",
                "Need me to send calendar invites?"
            ])
            
        # Food-related suggestions
        elif "food" in query_lower or "order" in query_lower:
            suggestions.extend([
                "Should I order from your favorite restaurant?",
                "Want me to reorder your last meal?",
                "Check for nearby restaurants with deals?"
            ])
            
        # Travel-related suggestions
        elif "travel" in query_lower or "flight" in query_lower:
            suggestions.extend([
                "Should I compare flight prices?",
                "Need hotel recommendations?",
                "Want me to check visa requirements?"
            ])
            
        # Work-related suggestions
        elif "work" in query_lower or "email" in query_lower:
            suggestions.extend([
                "Should I draft a response?",
                "Need me to summarize unread emails?",
                "Want to schedule focus time?"
            ])
            
        return suggestions

# Global instance
proactive_intelligence = ProactiveIntelligence()

async def get_proactive_suggestions(user_data: Dict = None) -> List[Dict]:
    """Get proactive suggestions for current context"""
    if user_data is None:
        user_data = {}
        
    return await proactive_intelligence.analyze_context(user_data)
