"""
SMARTII Smart Home Scenes & Automation
Pre-configured scenes for different scenarios
"""

import asyncio
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class SmartHomeScenes:
    def __init__(self):
        self.scenes = {
            "movie": {
                "name": "Movie Mode",
                "description": "Perfect for watching movies",
                "actions": [
                    {"device": "lights", "action": "dim", "value": 20},
                    {"device": "tv", "action": "turn_on"},
                    {"device": "sound_system", "action": "turn_on"},
                    {"device": "sound_system", "action": "set_volume", "value": 60},
                    {"device": "curtains", "action": "close"}
                ],
                "icon": "🎬"
            },
            "sleep": {
                "name": "Sleep Mode",
                "description": "Good night routine",
                "actions": [
                    {"device": "lights", "action": "turn_off"},
                    {"device": "doors", "action": "lock"},
                    {"device": "alarm", "action": "set", "value": "07:00"},
                    {"device": "thermostat", "action": "set_temperature", "value": 22},
                    {"device": "white_noise", "action": "turn_on"}
                ],
                "icon": "😴"
            },
            "work": {
                "name": "Work Mode",
                "description": "Focus and productivity",
                "actions": [
                    {"device": "desk_lamp", "action": "turn_on"},
                    {"device": "desk_lamp", "action": "set_brightness", "value": 100},
                    {"device": "notifications", "action": "mute"},
                    {"device": "music", "action": "play_focus_music"},
                    {"device": "coffee_maker", "action": "start"}
                ],
                "icon": "💼"
            },
            "party": {
                "name": "Party Mode",
                "description": "Let's celebrate!",
                "actions": [
                    {"device": "lights", "action": "set_color", "value": "rainbow"},
                    {"device": "lights", "action": "set_effect", "value": "pulse"},
                    {"device": "music", "action": "play_party_music"},
                    {"device": "sound_system", "action": "set_volume", "value": 80},
                    {"device": "disco_ball", "action": "turn_on"}
                ],
                "icon": "🎉"
            },
            "romantic": {
                "name": "Romantic Mode",
                "description": "Set the mood",
                "actions": [
                    {"device": "lights", "action": "set_color", "value": "warm_white"},
                    {"device": "lights", "action": "dim", "value": 30},
                    {"device": "candles", "action": "turn_on"},
                    {"device": "music", "action": "play_romantic_music"},
                    {"device": "sound_system", "action": "set_volume", "value": 40},
                    {"device": "fireplace", "action": "turn_on"}
                ],
                "icon": "💕"
            },
            "morning": {
                "name": "Good Morning",
                "description": "Start your day right",
                "actions": [
                    {"device": "lights", "action": "turn_on"},
                    {"device": "lights", "action": "set_brightness", "value": 100},
                    {"device": "curtains", "action": "open"},
                    {"device": "coffee_maker", "action": "start"},
                    {"device": "news", "action": "play_briefing"},
                    {"device": "thermostat", "action": "set_temperature", "value": 23}
                ],
                "icon": "🌅"
            },
            "reading": {
                "name": "Reading Mode",
                "description": "Perfect lighting for reading",
                "actions": [
                    {"device": "reading_lamp", "action": "turn_on"},
                    {"device": "reading_lamp", "action": "set_brightness", "value": 85},
                    {"device": "background_lights", "action": "dim", "value": 30},
                    {"device": "music", "action": "play_ambient"},
                    {"device": "sound_system", "action": "set_volume", "value": 20}
                ],
                "icon": "📚"
            },
            "gaming": {
                "name": "Gaming Mode",
                "description": "Optimized for gaming",
                "actions": [
                    {"device": "rgb_lights", "action": "set_color", "value": "red"},
                    {"device": "rgb_lights", "action": "set_effect", "value": "breathe"},
                    {"device": "gaming_pc", "action": "enable_performance_mode"},
                    {"device": "notifications", "action": "gaming_mode"},
                    {"device": "rgb_keyboard", "action": "set_profile", "value": "gaming"}
                ],
                "icon": "🎮"
            },
            "relaxation": {
                "name": "Relaxation Mode",
                "description": "Unwind and destress",
                "actions": [
                    {"device": "lights", "action": "set_color", "value": "soft_blue"},
                    {"device": "lights", "action": "dim", "value": 40},
                    {"device": "music", "action": "play_meditation"},
                    {"device": "sound_system", "action": "set_volume", "value": 30},
                    {"device": "diffuser", "action": "turn_on"},
                    {"device": "thermostat", "action": "set_temperature", "value": 22}
                ],
                "icon": "🧘"
            },
            "away": {
                "name": "Away Mode",
                "description": "Security when you're not home",
                "actions": [
                    {"device": "lights", "action": "turn_off_all"},
                    {"device": "doors", "action": "lock_all"},
                    {"device": "windows", "action": "close_all"},
                    {"device": "security_system", "action": "arm"},
                    {"device": "cameras", "action": "enable_recording"},
                    {"device": "thermostat", "action": "set_eco_mode"}
                ],
                "icon": "🏠"
            }
        }
        
    async def activate_scene(self, scene_name: str) -> Dict:
        """Activate a pre-configured scene"""
        scene_name = scene_name.lower()
        
        if scene_name not in self.scenes:
            available_scenes = ", ".join(self.scenes.keys())
            return {
                "success": False,
                "error": f"Scene '{scene_name}' not found",
                "available_scenes": available_scenes
            }
            
        scene = self.scenes[scene_name]
        results = []
        
        logger.info(f"Activating scene: {scene['name']}")
        
        # Execute all actions in the scene
        for action in scene["actions"]:
            try:
                result = await self._execute_action(action)
                results.append(result)
                await asyncio.sleep(0.5)  # Small delay between actions
            except Exception as e:
                logger.error(f"Failed to execute action {action}: {e}")
                results.append({
                    "device": action["device"],
                    "success": False,
                    "error": str(e)
                })
                
        return {
            "success": True,
            "scene": scene_name,
            "description": scene["description"],
            "icon": scene["icon"],
            "actions_executed": len(results),
            "results": results
        }
        
    async def _execute_action(self, action: Dict) -> Dict:
        """Execute a single device action"""
        device = action["device"]
        action_type = action["action"]
        value = action.get("value")
        
        # Import home automation controller
        try:
            from integrations.home_automation import execute_device_action
            result = await execute_device_action(device, action_type, value)
            return result
        except ImportError:
            # Mock execution if home automation not available
            logger.warning(f"Home automation not available - mocking action: {device}.{action_type}")
            return {
                "device": device,
                "action": action_type,
                "value": value,
                "success": True,
                "mock": True
            }
            
    def get_all_scenes(self) -> List[Dict]:
        """Get list of all available scenes"""
        return [
            {
                "id": scene_id,
                "name": scene["name"],
                "description": scene["description"],
                "icon": scene["icon"],
                "action_count": len(scene["actions"])
            }
            for scene_id, scene in self.scenes.items()
        ]
        
    def get_scene_details(self, scene_name: str) -> Dict:
        """Get detailed information about a specific scene"""
        scene_name = scene_name.lower()
        
        if scene_name not in self.scenes:
            return {"error": f"Scene '{scene_name}' not found"}
            
        return self.scenes[scene_name]
        
    async def create_custom_scene(self, name: str, actions: List[Dict], description: str = "") -> Dict:
        """Create a custom scene"""
        scene_id = name.lower().replace(" ", "_")
        
        self.scenes[scene_id] = {
            "name": name,
            "description": description or f"Custom scene: {name}",
            "actions": actions,
            "icon": "⚡",
            "custom": True
        }
        
        return {
            "success": True,
            "scene_id": scene_id,
            "message": f"Custom scene '{name}' created successfully"
        }
        
    async def modify_scene(self, scene_name: str, actions: List[Dict]) -> Dict:
        """Modify an existing scene"""
        scene_name = scene_name.lower()
        
        if scene_name not in self.scenes:
            return {"success": False, "error": f"Scene '{scene_name}' not found"}
            
        self.scenes[scene_name]["actions"] = actions
        
        return {
            "success": True,
            "message": f"Scene '{scene_name}' updated successfully"
        }

# Global instance
smart_home_scenes = SmartHomeScenes()

async def activate_scene(scene_name: str) -> Dict:
    """Activate a smart home scene"""
    return await smart_home_scenes.activate_scene(scene_name)

def get_available_scenes() -> List[Dict]:
    """Get all available scenes"""
    return smart_home_scenes.get_all_scenes()
