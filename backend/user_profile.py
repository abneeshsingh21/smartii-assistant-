"""
User Profile Management
Handles user information, preferences, and authentication
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserProfileManager:
    """Manages user profiles and personalization"""
    
    def __init__(self):
        self.profiles_dir = Path(__file__).parent / "data" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"User profiles directory: {self.profiles_dir}")
    
    def get_profile_path(self, user_id: str) -> Path:
        """Get path to user's profile file"""
        return self.profiles_dir / f"{user_id}.json"
    
    def create_profile(self, user_id: str, name: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user profile"""
        profile = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "preferences": {
                "voice_type": "female",
                "language": "en-US",
                "theme": "dark"
            },
            "stats": {
                "total_sessions": 1,
                "total_interactions": 0,
                "favorite_commands": []
            }
        }
        
        self.save_profile(user_id, profile)
        logger.info(f"Created new profile for {name} ({user_id})")
        return profile
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        profile_path = self.get_profile_path(user_id)
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Update last seen
            profile["last_seen"] = datetime.now().isoformat()
            profile["stats"]["total_sessions"] = profile["stats"].get("total_sessions", 0) + 1
            self.save_profile(user_id, profile)
            
            return profile
        except Exception as e:
            logger.error(f"Error loading profile {user_id}: {e}")
            return None
    
    def save_profile(self, user_id: str, profile: Dict[str, Any]):
        """Save user profile"""
        profile_path = self.get_profile_path(user_id)
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving profile {user_id}: {e}")
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        profile = self.get_profile(user_id)
        
        if not profile:
            return None
        
        profile.update(updates)
        self.save_profile(user_id, profile)
        return profile
    
    def get_greeting(self, user_id: str) -> str:
        """Get personalized greeting for user"""
        profile = self.get_profile(user_id)
        
        if not profile:
            return "Hello! I'm SMARTII, your AI assistant. May I know your name?"
        
        name = profile.get("name", "friend")
        hour = datetime.now().hour
        
        # Time-based greetings
        if 5 <= hour < 12:
            greeting = f"Good morning, {name}!"
        elif 12 <= hour < 17:
            greeting = f"Good afternoon, {name}!"
        elif 17 <= hour < 22:
            greeting = f"Good evening, {name}!"
        else:
            greeting = f"Hello, {name}!"
        
        # Add personalized touch based on usage
        sessions = profile["stats"].get("total_sessions", 1)
        if sessions == 1:
            greeting += " It's great to see you again for the first time! How can I help you today?"
        elif sessions < 5:
            greeting += " Welcome back! What can I do for you?"
        else:
            greeting += " Always a pleasure! What's on your mind?"
        
        return greeting
    
    def increment_interaction(self, user_id: str):
        """Increment user's interaction count"""
        profile = self.get_profile(user_id)
        if profile:
            profile["stats"]["total_interactions"] = profile["stats"].get("total_interactions", 0) + 1
            self.save_profile(user_id, profile)


# Global instance
user_profile_manager = UserProfileManager()
