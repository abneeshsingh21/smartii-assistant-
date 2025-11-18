"""
SMARTII Tool Orchestrator - Action Execution and Tool Management
Handles the execution of various tools and actions using the action schema.
Phase 4: Adds plugin registration and home automation (MQTT + Home Assistant) adapters.
Phase 5: Adds proactive intelligence, screen awareness, and smart home scenes.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import os

logger = logging.getLogger(__name__)

try:
    from integrations.home_automation import MQTTClient, HomeAssistantAPI
except Exception:
    MQTTClient = None
    HomeAssistantAPI = None

try:
    from integrations.windows_control import windows_controller
    from integrations.whatsapp_api import whatsapp_api
    from integrations.whatsapp_web import whatsapp_web
except Exception as e:
    logger.warning(f"Windows/WhatsApp integration not available: {e}")
    windows_controller = None
    whatsapp_api = None
    whatsapp_web = None

# Import new features
try:
    from proactive_intelligence import get_proactive_suggestions
    from screen_awareness import analyze_screen, extract_screen_text, find_on_screen
    from smart_home_scenes import activate_scene, get_available_scenes
    from plugin_system import execute_plugin, get_available_plugins, initialize_plugins
    ADVANCED_FEATURES_AVAILABLE = True
except Exception as e:
    logger.warning(f"Advanced features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

# Import alarm manager
try:
    from integrations.alarm_manager import AlarmManager
    alarm_manager = AlarmManager()
except Exception as e:
    logger.warning(f"Alarm manager not available: {e}")
    alarm_manager = None


class ToolOrchestrator:
    """Orchestrates tool execution using the SMARTII action schema."""

    def __init__(self):
        self.available_tools: Dict[str, Any] = {}
        self.running_tasks: Dict[str, Any] = {}
        self.initialize_tools()

    async def initialize(self):
        """Initialize the tool orchestrator."""
        logger.info("Tool orchestrator initialized")
        # In the future: warm up providers, validate external services

    def initialize_tools(self):
        """Initialize all available tools."""
        self.available_tools = {
            # Communications
            "email.send": self.email_send,
            "email.read": self.email_read,
            "sms.send": self.sms_send,
            "whatsapp.send": self.whatsapp_send,
            "telegram.send": self.telegram_send,
            # Productivity
            "calendar.create": self.calendar_create,
            "calendar.list": self.calendar_list,
            "note.create": self.note_create,
            "note.list": self.note_list,
            "reminder.set": self.reminder_set,
            "alarm.set": self.alarm_set_new,
            "alarm.list": self.alarm_list,
            "alarm.cancel": self.alarm_cancel,
            "timer.set": self.timer_set,
            "todo.create": self.todo_create,
            "todo.list": self.todo_list,
            "document.generate": self.document_generate,
            "document.summarize": self.document_summarize,
            # Web / info
            "web.search": self.web_search,
            "weather.get": self.weather_get,
            "news.get": self.news_get,
            "price.track": self.price_track,
            "map.navigate": self.map_navigate,
            # Voice
            "tts.speak": self.tts_speak,
            "stt.listen": self.stt_listen,
            # Home automation
            "device.control": self.device_control,
            "device.state": self.device_state,
            "scene.activate": self.scene_activate,
            "routine.trigger": self.routine_trigger,
            # Files / images
            "file.read": self.file_read,
            "file.write": self.file_write,
            "image.analyze": self.image_analyze,
            "image.generate": self.image_generate,
            "audio.transcribe": self.audio_transcribe,
            "video.summarize": self.video_summarize,
            # Memory / automation / exec
            "memory.save": self.memory_save,
            "memory.query": self.memory_query,
            "automation.create": self.automation_create,
            "python.execute": self.python_execute,
            "system.command": self.system_command,
            "music.play": self.music_play,
            # Windows device control
            "app.open": self.app_open,
            "app.close": self.app_close,
            "settings.open": self.settings_open,
            "whatsapp.open_chat": self.whatsapp_open_chat,
            "whatsapp.call": self.whatsapp_call,
            "website.open": self.website_open,
            # New advanced features
            "suggestions.get": self.get_suggestions,
            "screen.analyze": self.screen_analyze,
            "screen.extract_text": self.screen_extract_text,
            "screen.find": self.screen_find,
            "scene.list": self.list_scenes,
            "plugin.execute": self.plugin_execute,
            "plugin.list": self.list_plugins,
            # RAG and Web Search
            "web.search_rag": self.web_search_rag,
            # Code Execution
            "code.execute": self.code_execute,
            "code.calculate": self.code_execute,
            "code.analyze": self.code_execute,
            # File System
            "file.search": self.file_search,
            "file.organize": self.file_organize,
            "file.find_recent": self.file_find_recent,
            # Clipboard
            "clipboard.get": self.clipboard_get,
            "clipboard.paste": self.clipboard_paste,
            # Translation
            "translate": self.translate_text,
            "language.detect": self.detect_language,
            # Advanced Memory
            "memory.search_conversations": self.memory_search,
            "memory.store_fact": self.memory_store_fact,
        }

        logger.info(f"Initialized {len(self.available_tools)} tools")

    def is_valid_action(self, action_type: str) -> bool:
        """Check if an action type is valid."""
        return action_type in self.available_tools

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action synchronously."""
        try:
            action_id = action.get("id", str(uuid.uuid4()))
            action_type = action.get("type", "")
            params = action.get("params", {})
            confirm = action.get("confirm", False)
            meta = action.get("meta", {})

            # Check if confirmation is required
            if confirm:
                # In a real implementation, this would trigger user confirmation
                logger.info(f"Action {action_id} requires confirmation")

            # Execute the tool
            if action_type in self.available_tools:
                result = await self.available_tools[action_type](params, meta)
                return {
                    "action_id": action_id,
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "action_id": action_id,
                    "status": "error",
                    "error": f"Unknown action type: {action_type}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error executing action {action.get('id', 'unknown')}: {e}")
            return {
                "action_id": action.get("id", "unknown"),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def execute_action_async(self, action: Dict[str, Any]) -> str:
        """Execute an action asynchronously."""
        task_id = str(uuid.uuid4())
        self.running_tasks[task_id] = asyncio.create_task(self._execute_async_task(action, task_id))
        return task_id

    async def _execute_async_task(self, action: Dict[str, Any], task_id: str):
        """Execute an async task and store the result."""
        try:
            result = await self.execute_action(action)
            self.running_tasks[task_id] = result
        except Exception as e:
            self.running_tasks[task_id] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an async task."""
        return self.running_tasks.get(task_id)

    async def close(self):
        """Clean up resources."""
        # Cancel any running tasks
        for task_id, task in self.running_tasks.items():
            if isinstance(task, asyncio.Task) and not task.done():
                task.cancel()

        self.running_tasks.clear()

    # ================= Tool implementations =================

    async def email_send(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email (placeholder)."""
        try:
            to = params.get("to", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            logger.info(f"Sending email to {to}: {subject}")
            return {"status": "sent", "to": to, "subject": subject}
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"status": "error", "message": str(e)}

    async def email_read(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Read emails (placeholder)."""
        try:
            limit = params.get("limit", 10)
            return {"emails": [], "count": 0, "limit": limit}
        except Exception as e:
            logger.error(f"Error reading emails: {e}")
            return {"status": "error", "message": str(e)}

    async def sms_send(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Send an SMS (placeholder)."""
        try:
            to = params.get("to", "")
            message = params.get("message", "")
            logger.info(f"Sending SMS to {to}: {message}")
            return {"status": "sent", "to": to}
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {"status": "error", "message": str(e)}

    async def calendar_create(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event (placeholder)."""
        try:
            title = params.get("title", "")
            start_time = params.get("start_time", "")
            end_time = params.get("end_time", "")
            description = params.get("description", "")
            logger.info(f"Creating calendar event: {title}")
            return {"status": "created", "event_id": str(uuid.uuid4()), "title": title}
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"status": "error", "message": str(e)}

    async def calendar_list(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List calendar events (placeholder)."""
        try:
            date = params.get("date", datetime.now().date().isoformat())
            limit = params.get("limit", 10)
            return {"events": [], "date": date, "limit": limit}
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return {"status": "error", "message": str(e)}

    async def web_search(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a web search via GNews or DuckDuckGo."""
        try:
            query = params.get("query", "")
            limit = params.get("limit", 5)

            gnews_key = os.getenv("G_NEWS_API_KEY")
            if gnews_key:
                try:
                    import requests
                    gnews_url = f"https://gnews.io/api/v4/search?q={query}&token={gnews_key}&max={limit}&lang=en"
                    response = requests.get(gnews_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        results = []
                        for article in data.get("articles", [])[:limit]:
                            results.append({
                                "title": article.get("title", ""),
                                "url": article.get("url", ""),
                                "snippet": article.get("description", ""),
                                "source": article.get("source", {}).get("name", ""),
                                "publishedAt": article.get("publishedAt", "")
                            })
                        return {"query": query, "results": results, "source": "GNews"}
                except Exception as e:
                    logger.warning(f"GNews API failed: {e}")

            # Fallback to DuckDuckGo HTML
            import requests
            from bs4 import BeautifulSoup
            search_url = f"https://duckduckgo.com/html/?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.find_all('a', class_='result__a')[:limit]:
                title = result.get_text()
                url = result.get('href')
                snippet_elem = result.find_next('a', class_='result__snippet')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                results.append({"title": title, "url": url, "snippet": snippet})
            return {"query": query, "results": results, "source": "DuckDuckGo"}
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return {"status": "error", "message": str(e)}

    async def weather_get(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather information via OpenWeatherMap or demo data."""
        try:
            location = params.get("location", "New York")
            import requests
            api_key = os.getenv("OPENWEATHER_API_KEY", "demo_key")
            if api_key == "demo_key":
                return {"location": location, "temperature": 22, "condition": "sunny", "humidity": 65, "wind_speed": 5, "description": "Clear sky"}
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=10)
            data = response.json()
            if response.status_code == 200:
                return {
                    "location": location,
                    "temperature": data["main"]["temp"],
                    "condition": data["weather"][0]["main"].lower(),
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "description": data["weather"][0]["description"]
                }
            else:
                return {"status": "error", "message": "Weather API error"}
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return {"status": "error", "message": str(e)}

    async def tts_speak(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to speech (placeholder)."""
        try:
            text = params.get("text", "")
            voice = params.get("voice", "default")
            logger.info(f"Speaking: {text}")
            return {"status": "spoken", "text": text, "voice": voice}
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return {"status": "error", "message": str(e)}

    async def stt_listen(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Start speech to text (placeholder)."""
        try:
            duration = params.get("duration", 10)
            return {"status": "listening", "duration": duration}
        except Exception as e:
            logger.error(f"Error in STT: {e}")
            return {"status": "error", "message": str(e)}

    async def device_control(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Control smart devices via MQTT or Home Assistant."""
        try:
            provider = params.get("provider", "mqtt")  # mqtt|homeassistant
            if provider == "mqtt":
                if MQTTClient is None:
                    return {"status": "error", "message": "MQTT integration not available"}
                topic = params.get("topic")
                payload = params.get("payload", "")
                host = params.get("host", os.getenv("MQTT_HOST", "localhost"))
                port = int(params.get("port", os.getenv("MQTT_PORT", 1883)))
                username = params.get("username", os.getenv("MQTT_USER"))
                password = params.get("password", os.getenv("MQTT_PASS"))
                tls = bool(params.get("tls", False))
                client = MQTTClient(host, port, username, password, tls)
                ok = client.publish(topic, json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload))
                return {"status": "ok" if ok else "error", "provider": "mqtt", "topic": topic}
            elif provider == "homeassistant":
                if HomeAssistantAPI is None:
                    return {"status": "error", "message": "Home Assistant integration not available"}
                base_url = params.get("base_url", os.getenv("HA_BASE_URL", "http://localhost:8123"))
                token = params.get("token", os.getenv("HA_TOKEN", ""))
                domain = params.get("domain")
                service = params.get("service")
                data = params.get("data", {})
                ha = HomeAssistantAPI(base_url, token)
                return ha.call_service(domain, service, data)
            else:
                # Backward-compatible placeholder
                device_id = params.get("device_id", "")
                action = params.get("action", "")
                value = params.get("value", "")
                logger.info(f"Controlling device {device_id}: {action} = {value}")
                return {"status": "controlled", "device_id": device_id, "action": action, "value": value}
        except Exception as e:
            logger.error(f"Error controlling device: {e}")
            return {"status": "error", "message": str(e)}

    async def device_state(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Query device state via Home Assistant."""
        try:
            if HomeAssistantAPI is None:
                return {"status": "error", "message": "Home Assistant integration not available"}
            base_url = params.get("base_url", os.getenv("HA_BASE_URL", "http://localhost:8123"))
            token = params.get("token", os.getenv("HA_TOKEN", ""))
            entity_id = params.get("entity_id")
            if not entity_id:
                return {"status": "error", "message": "entity_id required"}
            ha = HomeAssistantAPI(base_url, token)
            return ha.get_state(entity_id)
        except Exception as e:
            logger.error(f"Error getting device state: {e}")
            return {"status": "error", "message": str(e)}

    async def file_read(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        try:
            file_path = params.get("path", "")
            if not self._is_safe_path(file_path):
                return {"status": "error", "message": "Access denied"}
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"status": "read", "path": file_path, "content": content}
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return {"status": "error", "message": str(e)}

    async def file_write(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        try:
            file_path = params.get("path", "")
            content = params.get("content", "")
            if not self._is_safe_path(file_path):
                return {"status": "error", "message": "Access denied"}
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "written", "path": file_path}
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return {"status": "error", "message": str(e)}

    async def image_analyze(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an image; basic metadata and optional OCR if available."""
        try:
            image_path = params.get("path", "")
            from PIL import Image
            import os as _os
            if not _os.path.exists(image_path):
                return {"status": "error", "message": "Image file not found"}
            img = Image.open(image_path)
            analysis = {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "filename": _os.path.basename(image_path)
            }
            try:
                import pytesseract
                text = pytesseract.image_to_string(img)
                analysis["extracted_text"] = text.strip() if text.strip() else "No text found"
            except Exception:
                analysis["extracted_text"] = "OCR not available"
            return {"status": "analyzed", "path": image_path, "analysis": analysis}
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"status": "error", "message": str(e)}

    async def memory_save(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Save to memory (placeholder)."""
        try:
            content = params.get("content", "")
            memory_type = params.get("type", "episodic")
            return {"status": "saved", "type": memory_type, "content": content}
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")
            return {"status": "error", "message": str(e)}

    async def memory_query(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Query memory (placeholder)."""
        try:
            query = params.get("query", "")
            return {"query": query, "results": []}
        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return {"status": "error", "message": str(e)}

    async def automation_create(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create an automation (placeholder)."""
        try:
            name = params.get("name", "")
            trigger = params.get("trigger", {})
            actions = params.get("actions", [])
            return {"status": "created", "automation_id": str(uuid.uuid4()), "name": name}
        except Exception as e:
            logger.error(f"Error creating automation: {e}")
            return {"status": "error", "message": str(e)}

    async def python_execute(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code (unsafe placeholder – do not use in production)."""
        try:
            code = params.get("code", "")
            if not self._is_safe_code(code):
                return {"status": "error", "message": "Unsafe code execution blocked"}
            result = eval(code)  # WARNING: unsafe – replace with a sandbox in production
            return {"status": "executed", "result": str(result)}
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return {"status": "error", "message": str(e)}

    async def system_command(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system commands for opening apps, playing music, etc."""
        try:
            command = params.get("command", "")
            if not command:
                return {"status": "error", "message": "No command provided"}

            # Basic safety check - only allow certain commands
            allowed_commands = ["start chrome", "start msedge", "start firefox", "start notepad", "start calc", "start explorer"]
            normalized_command = command.lower().strip()
            # Allow YouTube URLs
            if "youtube.com" in normalized_command or any(allowed in normalized_command for allowed in allowed_commands):
                pass  # Allow the command
            else:
                return {"status": "error", "message": "Command not allowed for security"}

            import subprocess
            import platform

            if platform.system() == "Windows":
                # Use shell=True for Windows to handle 'start' command
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                logger.info(f"Executed command: {command}, returncode: {result.returncode}")
            else:
                # For other systems, split the command
                cmd_parts = command.split()
                result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=10)

            return {
                "status": "executed",
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            logger.error(f"Error executing system command: {e}")
            return {"status": "error", "message": str(e)}

    async def music_play(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Play music using system media player or YouTube."""
        try:
            song_query = params.get("query", "")
            autoplay = params.get("autoplay", True)
            mute = params.get("mute", False)

            if not song_query:
                return {"status": "error", "message": "No song specified"}

            # Search YouTube and get video URL
            from urllib.parse import quote
            import platform
            import requests
            
            try:
                # Search YouTube for the video
                search_url = f"https://www.youtube.com/results?search_query={quote(song_query)}"
                
                # Try to get the first video ID
                try:
                    import re
                    resp = requests.get(search_url, timeout=5, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    # Find first video ID in search results
                    video_ids = re.findall(r'"videoId":"([^"]+)"', resp.text)
                    if video_ids:
                        video_id = video_ids[0]
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        logger.info(f"Found YouTube video: {video_id} for '{song_query}'")
                        
                        # On cloud/web deployment, return URL to frontend
                        # Frontend will handle opening in new tab
                        return {
                            "status": "playing",
                            "song": song_query,
                            "url": video_url,
                            "video_id": video_id,
                            "open_url": True,  # Signal frontend to open URL
                            "message": f"🎵 Playing '{song_query}' on YouTube!"
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch video ID: {e}")
                
                # Fallback: Return search URL
                fallback_url = f"https://www.youtube.com/results?search_query={quote(song_query)}"
                return {
                    "status": "search",
                    "song": song_query,
                    "url": fallback_url,
                    "open_url": True,
                    "message": f"🔍 Search results for '{song_query}' on YouTube"
                }

            except Exception as e:
                logger.error(f"Error searching video: {e}")
                return {"status": "error", "message": f"Could not search YouTube: {str(e)}"}

        except Exception as e:
            logger.error(f"Error playing music: {e}")
            return {"status": "error", "message": str(e)}

    # ================= Utilities and metadata =================

    def _is_safe_path(self, file_path: str) -> bool:
        """Check if a file path is safe to access."""
        dangerous_paths = ["/etc", "/bin", "/usr", "C:\\Windows", "C:\\System32"]
        return not any(dangerous in file_path for dangerous in dangerous_paths)

    def _is_safe_code(self, code: str) -> bool:
        """Check if Python code is safe to execute."""
        dangerous_keywords = ["import os", "import sys", "import subprocess", "eval", "exec"]
        return not any(keyword in code for keyword in dangerous_keywords)

    async def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.available_tools.keys())

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if tool_name not in self.available_tools:
            return None
        return {
            "name": tool_name,
            "description": f"Tool for {tool_name.replace('.', ' ')}",
            "parameters": ["params", "meta"],
            "providers": ["mqtt", "homeassistant"] if tool_name.startswith("device.") else None
        }

    # ================= NEW PRODUCTIVITY TOOLS =================

    async def whatsapp_send(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Send WhatsApp message via API or desktop."""
        try:
            to = params.get("to", "")
            message = params.get("message", "")
            logger.info(f"Sending WhatsApp to {to}: {message}")
            
            # Try WhatsApp Business API first
            if whatsapp_api and whatsapp_api.enabled:
                result = await whatsapp_api.send_message(to, message)
                if result.get("success"):
                    return {"status": "sent", "to": to, "method": "api", "message_id": result.get("message_id")}
            
            # Try WhatsApp Web automation (background sending) - Fixed Chrome issues
            if whatsapp_web:
                try:
                    result = whatsapp_web.send_message(to, message)
                    if result.get("success"):
                        return {"status": "sent", "to": to, "method": "web_background", "auto_sent": True}
                except Exception as e:
                    logger.warning(f"WhatsApp Web failed, falling back to desktop: {e}")
            
            # Fallback to Windows desktop WhatsApp
            if windows_controller:
                result = windows_controller.open_whatsapp_chat(to, message, auto_send=True)
                if result.get("success"):
                    # Check if message was auto-sent
                    if result.get("auto_sent"):
                        return {"status": "sent", "to": to, "method": "desktop", "auto_sent": True}
                    return {"status": "opened", "to": to, "method": "desktop", "auto_sent": False}
                else:
                    return {"status": "error", "message": result.get("error", "Failed to open WhatsApp")}
            
            return {"status": "error", "message": "WhatsApp not configured"}
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {e}")
            return {"status": "error", "message": str(e)}

    async def telegram_send(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Send Telegram message."""
        try:
            to = params.get("to", "")
            message = params.get("message", "")
            logger.info(f"Sending Telegram to {to}: {message}")
            # Placeholder - integrate with Telegram Bot API
            return {"status": "sent", "to": to, "platform": "telegram"}
        except Exception as e:
            logger.error(f"Error sending Telegram: {e}")
            return {"status": "error", "message": str(e)}

    async def note_create(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create a note."""
        try:
            title = params.get("title", "Untitled")
            content = params.get("content", "")
            tags = params.get("tags", [])
            note_id = str(uuid.uuid4())
            logger.info(f"Creating note: {title}")
            return {"status": "created", "note_id": note_id, "title": title}
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return {"status": "error", "message": str(e)}

    async def note_list(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List all notes."""
        try:
            limit = params.get("limit", 20)
            return {"notes": [], "count": 0, "limit": limit}
        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            return {"status": "error", "message": str(e)}

    async def reminder_set(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Set a reminder."""
        try:
            message = params.get("message", "")
            time = params.get("time", "")
            reminder_id = str(uuid.uuid4())
            logger.info(f"Setting reminder: {message} at {time}")
            return {"status": "set", "reminder_id": reminder_id, "message": message, "time": time}
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return {"status": "error", "message": str(e)}

    async def alarm_set(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Set an alarm."""
        try:
            time = params.get("time", "")
            label = params.get("label", "Alarm")
            alarm_id = str(uuid.uuid4())
            logger.info(f"Setting alarm: {label} at {time}")
            return {"status": "set", "alarm_id": alarm_id, "time": time, "label": label}
        except Exception as e:
            logger.error(f"Error setting alarm: {e}")
            return {"status": "error", "message": str(e)}

    async def timer_set(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Set a timer."""
        try:
            duration = params.get("duration", 60)  # seconds
            label = params.get("label", "Timer")
            timer_id = str(uuid.uuid4())
            logger.info(f"Setting timer: {label} for {duration} seconds")
            return {"status": "set", "timer_id": timer_id, "duration": duration, "label": label}
        except Exception as e:
            logger.error(f"Error setting timer: {e}")
            return {"status": "error", "message": str(e)}

    async def todo_create(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create a to-do item."""
        try:
            task = params.get("task", "")
            priority = params.get("priority", "medium")
            due_date = params.get("due_date", None)
            todo_id = str(uuid.uuid4())
            logger.info(f"Creating to-do: {task}")
            return {"status": "created", "todo_id": todo_id, "task": task, "priority": priority}
        except Exception as e:
            logger.error(f"Error creating to-do: {e}")
            return {"status": "error", "message": str(e)}

    async def todo_list(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List all to-do items."""
        try:
            filter_status = params.get("status", "all")  # all, pending, completed
            return {"todos": [], "count": 0, "filter": filter_status}
        except Exception as e:
            logger.error(f"Error listing to-dos: {e}")
            return {"status": "error", "message": str(e)}

    async def document_generate(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a document (PDF, text, spreadsheet)."""
        try:
            doc_type = params.get("type", "text")  # text, pdf, spreadsheet
            content = params.get("content", "")
            filename = params.get("filename", "document")
            logger.info(f"Generating {doc_type} document: {filename}")
            return {"status": "generated", "filename": filename, "type": doc_type, "path": f"/documents/{filename}.{doc_type}"}
        except Exception as e:
            logger.error(f"Error generating document: {e}")
            return {"status": "error", "message": str(e)}

    async def document_summarize(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a document."""
        try:
            file_path = params.get("path", "")
            max_length = params.get("max_length", 500)
            logger.info(f"Summarizing document: {file_path}")
            return {"status": "summarized", "path": file_path, "summary": "Document summary placeholder"}
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {"status": "error", "message": str(e)}

    async def news_get(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Get news headlines."""
        try:
            category = params.get("category", "general")
            limit = params.get("limit", 10)
            logger.info(f"Fetching {category} news")
            return {"category": category, "articles": [], "count": 0}
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return {"status": "error", "message": str(e)}

    async def price_track(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Track product price."""
        try:
            product_url = params.get("url", "")
            target_price = params.get("target_price", None)
            logger.info(f"Tracking price for: {product_url}")
            return {"status": "tracking", "url": product_url, "current_price": None, "target_price": target_price}
        except Exception as e:
            logger.error(f"Error tracking price: {e}")
            return {"status": "error", "message": str(e)}

    async def map_navigate(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Get navigation directions."""
        try:
            origin = params.get("from", "")
            destination = params.get("to", "")
            mode = params.get("mode", "driving")  # driving, walking, transit
            logger.info(f"Getting directions from {origin} to {destination}")
            return {"status": "ok", "from": origin, "to": destination, "mode": mode, "directions": []}
        except Exception as e:
            logger.error(f"Error getting navigation: {e}")
            return {"status": "error", "message": str(e)}

    async def scene_activate(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a smart home scene."""
        try:
            scene_name = params.get("scene", "")
            provider = params.get("provider", "homeassistant")
            logger.info(f"Activating scene: {scene_name}")
            return {"status": "activated", "scene": scene_name, "provider": provider}
        except Exception as e:
            logger.error(f"Error activating scene: {e}")
            return {"status": "error", "message": str(e)}

    async def routine_trigger(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a smart home routine."""
        try:
            routine_name = params.get("routine", "")
            logger.info(f"Triggering routine: {routine_name}")
            return {"status": "triggered", "routine": routine_name}
        except Exception as e:
            logger.error(f"Error triggering routine: {e}")
            return {"status": "error", "message": str(e)}

    # ================= WINDOWS DEVICE CONTROL TOOLS =================

    async def app_open(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application on Windows."""
        try:
            app_name = params.get("app", "")
            if not windows_controller:
                return {"status": "error", "message": "This feature is only available on Windows devices running SMARTII locally. It's not supported on the web version."}
            
            result = windows_controller.open_app(app_name)
            return result
        except Exception as e:
            logger.error(f"Error opening app: {e}")
            return {"status": "error", "message": str(e)}

    async def app_close(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Close an application on Windows."""
        try:
            app_name = params.get("app", "")
            if not windows_controller:
                return {"status": "error", "message": "This feature is only available on Windows devices running SMARTII locally. It's not supported on the web version."}
            
            result = windows_controller.close_app(app_name)
            return result
        except Exception as e:
            logger.error(f"Error closing app: {e}")
            return {"status": "error", "message": str(e)}

    async def settings_open(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Open Windows settings."""
        try:
            setting_type = params.get("type", None)
            if not windows_controller:
                return {"status": "error", "message": "Windows control not available"}
            
            result = windows_controller.open_settings(setting_type)
            return result
        except Exception as e:
            logger.error(f"Error opening settings: {e}")
            return {"status": "error", "message": str(e)}

    async def whatsapp_open_chat(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Open WhatsApp chat on desktop."""
        try:
            phone = params.get("phone", "")
            message = params.get("message", None)
            if not windows_controller:
                return {"status": "error", "message": "Windows control not available"}
            
            result = windows_controller.open_whatsapp_chat(phone, message)
            return result
        except Exception as e:
            logger.error(f"Error opening WhatsApp: {e}")
            return {"status": "error", "message": str(e)}
    
    async def whatsapp_call(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Make WhatsApp voice or video call."""
        try:
            to = params.get("to", "")
            video = params.get("video", False)
            if not windows_controller:
                return {
                    "status": "error", 
                    "message": "WhatsApp calling is only available on Windows devices running SMARTII locally. This feature requires WhatsApp Desktop to be installed and cannot work on the web version."
                }
            
            result = windows_controller.whatsapp_call(to, video)
            if result.get("success"):
                return {"status": "calling", "to": to, "video": video, "call_type": result.get("call_type")}
            return {"status": "error", "message": result.get("error", "Failed to initiate call")}
        except Exception as e:
            logger.error(f"Error making WhatsApp call: {e}")
            return {"status": "error", "message": str(e)}

    async def website_open(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Open a website in default browser."""
        try:
            url = params.get("url", "")
            if not windows_controller:
                return {"status": "error", "message": "Windows control not available"}
            
            result = windows_controller.open_website(url)
            return result
        except Exception as e:
            logger.error(f"Error opening website: {e}")
            return {"status": "error", "message": str(e)}

    async def image_generate(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using AI."""
        try:
            prompt = params.get("prompt", "")
            style = params.get("style", "realistic")
            logger.info(f"Generating image: {prompt}")
            return {"status": "generated", "prompt": prompt, "style": style, "url": "placeholder_image_url"}
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {"status": "error", "message": str(e)}

    async def audio_transcribe(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file."""
        try:
            file_path = params.get("path", "")
            language = params.get("language", "en")
            logger.info(f"Transcribing audio: {file_path}")
            return {"status": "transcribed", "path": file_path, "transcription": "Audio transcription placeholder"}
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {"status": "error", "message": str(e)}

    async def video_summarize(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a video."""
        try:
            file_path = params.get("path", "")
            max_length = params.get("max_length", 500)
            logger.info(f"Summarizing video: {file_path}")
            return {"status": "summarized", "path": file_path, "summary": "Video summary placeholder"}
        except Exception as e:
            logger.error(f"Error summarizing video: {e}")
            return {"status": "error", "message": str(e)}

    # ============= New Advanced Features =============
    
    async def get_suggestions(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Get proactive suggestions based on context."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Proactive intelligence not available"}
            
            user_data = params.get("context", {})
            suggestions = await get_proactive_suggestions(user_data)
            return {"status": "success", "suggestions": suggestions}
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return {"status": "error", "message": str(e)}
    
    async def screen_analyze(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze screen content."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Screen awareness not available"}
            
            task = params.get("task", "summarize")
            result = await analyze_screen(task)
            return {"status": "success", "analysis": result}
        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return {"status": "error", "message": str(e)}
    
    async def screen_extract_text(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from screen."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Screen awareness not available"}
            
            region = params.get("region", None)
            text = await extract_screen_text(region)
            return {"status": "success", "text": text}
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {"status": "error", "message": str(e)}
    
    async def screen_find(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Find text on screen."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Screen awareness not available"}
            
            search_term = params.get("text", "")
            result = await find_on_screen(search_term)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Error finding text: {e}")
            return {"status": "error", "message": str(e)}
    
    async def list_scenes(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List available smart home scenes."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Smart home scenes not available"}
            
            scenes = get_available_scenes()
            return {"status": "success", "scenes": scenes}
        except Exception as e:
            logger.error(f"Error listing scenes: {e}")
            return {"status": "error", "message": str(e)}
    
    async def plugin_execute(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin command."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Plugin system not available"}
            
            plugin_name = params.get("plugin", "")
            command = params.get("command", "")
            plugin_params = params.get("params", {})
            
            result = await execute_plugin(plugin_name, command, plugin_params)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Error executing plugin: {e}")
            return {"status": "error", "message": str(e)}
    
    async def list_plugins(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List available plugins."""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return {"status": "error", "message": "Plugin system not available"}
            
            plugins = get_available_plugins()
            return {"status": "success", "plugins": plugins}
        except Exception as e:
            logger.error(f"Error listing plugins: {e}")
            return {"status": "error", "message": str(e)}

    # ===== NEW ADVANCED FEATURES =====
    
    async def web_search_rag(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Search web with RAG (Retrieval Augmented Generation)."""
        try:
            from integrations.web_search import get_web_search_engine
            
            query = params.get("query", "")
            search_type = params.get("type", "general")  # general, news, images
            
            web_search = get_web_search_engine()
            
            if search_type == "news":
                results = web_search.search_news(query)
                return {"status": "success", "results": results, "type": "news"}
            elif search_type == "images":
                results = web_search.search_images(query)
                return {"status": "success", "results": results, "type": "images"}
            elif search_type == "rag":
                # Answer question using RAG
                answer = web_search.answer_question_with_rag(query)
                return {"status": "success", "answer": answer}
            else:
                results = web_search.search(query)
                return {"status": "success", "results": results, "type": "web"}
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def code_execute(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code safely."""
        try:
            from integrations.code_executor import get_code_executor
            
            code = params.get("code", "")
            operation = params.get("operation", "execute")  # execute, calculate, analyze
            
            executor = get_code_executor()
            
            if operation == "calculate":
                result = executor.calculate(code)
            elif operation == "analyze":
                data = params.get("data", [])
                analysis_type = params.get("analysis_type", "stats")
                result = executor.analyze_data(data, analysis_type)
            else:
                result = executor.execute_python(code)
            
            return {"status": "success", **result}
            
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def file_search(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files."""
        try:
            from integrations.file_system import get_file_system_manager
            
            query = params.get("query", "")
            location = params.get("location", None)
            file_type = params.get("file_type", None)
            limit = params.get("limit", 50)
            
            fs_manager = get_file_system_manager()
            results = fs_manager.search_files(query, location, file_type, limit)
            
            return {"status": "success", "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"File search error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def file_organize(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Organize files in a folder."""
        try:
            from integrations.file_system import get_file_system_manager
            
            folder_path = params.get("folder", "")
            organize_by = params.get("by", "type")  # type, date, size
            
            fs_manager = get_file_system_manager()
            result = fs_manager.organize_folder(folder_path, organize_by)
            
            return result
            
        except Exception as e:
            logger.error(f"File organization error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def file_find_recent(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Find recently modified files."""
        try:
            from integrations.file_system import get_file_system_manager
            
            location = params.get("location", "downloads")
            hours = params.get("hours", 24)
            limit = params.get("limit", 20)
            
            fs_manager = get_file_system_manager()
            results = fs_manager.find_recent_files(location, hours, limit)
            
            return {"status": "success", "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"Error finding recent files: {e}")
            return {"status": "error", "message": str(e)}
    
    async def clipboard_get(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Get clipboard history."""
        try:
            from integrations.clipboard_manager import get_clipboard_manager
            
            limit = params.get("limit", 10)
            content_type = params.get("type", None)
            
            clipboard = get_clipboard_manager()
            history = clipboard.get_history(limit, content_type)
            
            return {"status": "success", "history": history, "count": len(history)}
            
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def clipboard_paste(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Paste from clipboard history."""
        try:
            from integrations.clipboard_manager import get_clipboard_manager
            
            index = params.get("index", 0)
            
            clipboard = get_clipboard_manager()
            result = clipboard.paste_from_history(index)
            
            return result
            
        except Exception as e:
            logger.error(f"Clipboard paste error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def translate_text(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Translate text to another language."""
        try:
            from integrations.translator import get_language_translator
            
            text = params.get("text", "")
            target_lang = params.get("target", "en")
            source_lang = params.get("source", "auto")
            
            translator = get_language_translator()
            result = translator.translate(text, target_lang, source_lang)
            
            return result
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def detect_language(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Detect language of text."""
        try:
            from integrations.translator import get_language_translator
            
            text = params.get("text", "")
            
            translator = get_language_translator()
            result = translator.detect_language(text)
            
            return result
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def memory_search(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Search conversation memory."""
        try:
            from integrations.advanced_memory import get_advanced_memory
            
            query = params.get("query", "")
            client_id = params.get("client_id", "default")
            limit = params.get("limit", 5)
            
            memory = get_advanced_memory()
            results = memory.search_conversations(query, client_id, limit)
            
            return {"status": "success", "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def memory_store_fact(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Store a fact in memory."""
        try:
            from integrations.advanced_memory import get_advanced_memory
            
            fact = params.get("fact", "")
            category = params.get("category", "general")
            client_id = params.get("client_id", "default")
            
            memory = get_advanced_memory()
            memory.store_fact(fact, category, client_id)
            
            return {"status": "success", "message": "Fact stored"}
            
        except Exception as e:
            logger.error(f"Memory storage error: {e}")
            return {"status": "error", "message": str(e)}

    # Alarm Management
    async def alarm_set_new(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Set an alarm with Windows Task Scheduler."""
        if not alarm_manager:
            return {"status": "error", "message": "Alarm manager not available"}
        
        try:
            time_str = params.get("time", "")
            date_str = params.get("date", None)
            message = params.get("message", "Alarm")
            
            if not time_str:
                return {"status": "error", "message": "Time is required"}
            
            result = alarm_manager.set_alarm(time_str, date_str, message)
            return result
            
        except Exception as e:
            logger.error(f"Alarm set error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def alarm_list(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """List all active alarms."""
        if not alarm_manager:
            return {"status": "error", "message": "Alarm manager not available"}
        
        try:
            alarms = alarm_manager.list_alarms()
            return {"status": "success", "alarms": alarms, "count": len(alarms)}
            
        except Exception as e:
            logger.error(f"Alarm list error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def alarm_cancel(self, params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an alarm."""
        if not alarm_manager:
            return {"status": "error", "message": "Alarm manager not available"}
        
        try:
            task_name = params.get("task_name", "")
            if not task_name:
                return {"status": "error", "message": "Task name is required"}
            
            result = alarm_manager.cancel_alarm(task_name)
            return result
            
        except Exception as e:
            logger.error(f"Alarm cancel error: {e}")
            return {"status": "error", "message": str(e)}

    # Plugin registration API
    def register_tool(self, name: str, handler, description: str = "", params_schema: Optional[Dict[str, Any]] = None, permissions: Optional[List[str]] = None):
        """Register a new tool (for plugins)."""
        if name in self.available_tools:
            logger.warning(f"Tool {name} already exists; overwriting")
        self.available_tools[name] = handler
        logger.info(f"Registered plugin tool: {name} - {description}")
