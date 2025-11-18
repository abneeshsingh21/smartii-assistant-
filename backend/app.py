"""
SMARTII Backend - Main Application
FastAPI application serving as the core backend for SMARTII voice assistant.
"""

import uuid
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import json
import logging
import base64
import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from ai_engine import SmartiiAIEngine
from memory import MemoryEngine
from voice import VoiceProcessor
from conversation import ConversationHandler
from tools import ToolOrchestrator
from state_machine import voice_state, State
from user_profile import user_profile_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for local-only features
try:
    from wake_word import wake_word_detector
    WAKE_WORD_AVAILABLE = True
except ImportError:
    logger.warning("Wake word detection not available - using mock implementation")
    wake_word_detector = None
    WAKE_WORD_AVAILABLE = False

app = FastAPI(title="SMARTII Backend", version="1.0.0")

# CORS middleware for frontend communication
# Allow both local development and production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.herokuapp.com",
        "https://*.netlify.app",
        "*"  # Allow all origins for easier deployment (consider restricting in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
ai_engine = SmartiiAIEngine()
memory_engine = MemoryEngine()
voice_processor = VoiceProcessor()
conversation_handler = ConversationHandler(memory_engine)
tool_orchestrator = ToolOrchestrator()

# Plugin loading support
loaded_plugins: List[str] = []

def load_plugins():
    try:
        root = Path(__file__).resolve().parents[1]
        plugins_dir = root / "plugins"
        if not plugins_dir.exists():
            logger.info("No plugins directory found")
            return
        for entry in plugins_dir.iterdir():
            if entry.is_dir():
                plugin_py = entry / "plugin.py"
                if plugin_py.exists():
                    spec = importlib.util.spec_from_file_location(f"smartii_plugin_{entry.name}", str(plugin_py))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "register"):
                            try:
                                module.register(tool_orchestrator)
                                loaded_plugins.append(entry.name)
                                logger.info(f"Loaded plugin: {entry.name}")
                            except Exception as e:
                                logger.error(f"Plugin '{entry.name}' registration failed: {e}")
        if not loaded_plugins:
            logger.info("No plugins loaded")
    except Exception as e:
        logger.error(f"Plugin loading failed: {e}")

# WebSocket connection manager with full duplex support
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_states: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_states[client_id] = {
            "listening": False,
            "speaking": False,
            "interrupted": False,
            "audio_buffer": []
        }
        logger.info(f"🔌 Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_states:
            del self.client_states[client_id]
        logger.info(f"🔌 Client {client_id} disconnected")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
    
    async def broadcast_state_change(self, state: State, reason: str):
        """Broadcast state machine changes to all clients"""
        message = json.dumps({
            "type": "state_change",
            "state": state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        await self.broadcast(message)
    
    def get_client_state(self, client_id: str) -> Optional[Dict[str, Any]]:
        return self.client_states.get(client_id)
    
    def update_client_state(self, client_id: str, updates: Dict[str, Any]):
        if client_id in self.client_states:
            self.client_states[client_id].update(updates)

manager = ConnectionManager()

# ===== Pydantic models: Smartii contracts =====
class ActionModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False
    async_: bool = Field(False, alias="async")
    meta: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True

class EventModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    ts: str
    source: str
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    level: str = "info"

class MemoryItemModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: str = Field("episodic", description="episodic|semantic|preference|task|routine")
    user_id: str = "default"
    content: Any
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    sensitivity: str = "public"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class JobModel(BaseModel):
    id: str
    action_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    retries: int = 0

class ConversationTurnModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: Any
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[ActionModel] = Field(default_factory=list)
    events: List[EventModel] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

# Compatibility/request models
class ActionRequest(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    confirm: bool = False
    async_: bool = False
    meta: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    text: str
    client_id: str
    voice_data: Optional[bytes] = None

class MemoryRequest(BaseModel):
    action: str  # save, query, delete
    data: Optional[Dict[str, Any]] = None
    query: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    client_id: str
    developer_mode: Optional[bool] = None
    secure_mode: Optional[bool] = None

class ModeRequest(BaseModel):
    developer: Optional[bool] = None
    secure: Optional[bool] = None

class ToolRegisterRequest(BaseModel):
    name: str
    description: Optional[str] = None
    kind: Optional[str] = "echo"  # echo returns params; future: http/script

# ===== Routes =====
@app.get("/")
async def root():
    return {"message": "SMARTII Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# New: Smartii standardized chat endpoint
@app.post("/v1/chat")
async def v1_chat(request: ChatRequest):
    try:
        if request.developer_mode is not None:
            ai_engine.set_mode("developer", request.developer_mode)
        if request.secure_mode is not None:
            ai_engine.set_mode("secure", request.secure_mode)

        context = await conversation_handler.get_context(request.client_id)
        response = await ai_engine.process_message(request.message, context, request.client_id)
        await conversation_handler.update_conversation(request.client_id, request.message, response)
        audio_response = await voice_processor.generate_audio_response(response, request.client_id)
        return {
            "reply": response,
            "client_id": request.client_id,
            "audio": audio_response,
            "actions": [],
            "events": []
        }
    except Exception as e:
        logger.error(f"/v1/chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User profile endpoints
@app.post("/greeting")
async def get_greeting(request: dict):
    """Get personalized greeting for user"""
    client_id = request.get("client_id", "default")
    
    greeting = user_profile_manager.get_greeting(client_id)
    profile = user_profile_manager.get_profile(client_id)
    
    return {
        "greeting": greeting,
        "is_new_user": profile is None,
        "profile": profile
    }

@app.post("/set-name")
async def set_user_name(request: dict):
    """Set user's name after first interaction"""
    client_id = request.get("client_id", "default")
    name = request.get("name", "")
    
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    profile = user_profile_manager.get_profile(client_id)
    
    if profile:
        # Update existing profile
        profile = user_profile_manager.update_profile(client_id, {"name": name})
    else:
        # Create new profile
        profile = user_profile_manager.create_profile(client_id, name)
    
    return {
        "success": True,
        "message": f"Great to meet you, {name}! I'll remember your name from now on.",
        "profile": profile
    }

@app.post("/gmail-login")
async def gmail_login(request: dict):
    """Associate Gmail account with user profile"""
    client_id = request.get("client_id", "default")
    email = request.get("email", "")
    name = request.get("name", "")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    profile = user_profile_manager.get_profile(client_id)
    
    if profile:
        # Update existing profile with email
        profile = user_profile_manager.update_profile(client_id, {"email": email})
    else:
        # Create new profile with email
        profile = user_profile_manager.create_profile(client_id, name or "User", email)
    
    return {
        "success": True,
        "message": f"Successfully linked {email} to your profile!",
        "profile": profile
    }

# Simple chat endpoint for frontend
@app.post("/chat")
async def chat(request: dict):
    """Simple chat endpoint compatible with frontend"""
    try:
        message = request.get("message", "")
        client_id = request.get("client_id", "default")
        
        context = await conversation_handler.get_context(client_id)
        
        # Process message
        response = await ai_engine.process_message(message, context, client_id)
        await conversation_handler.update_conversation(client_id, message, response)
        
        # Increment user interaction count
        user_profile_manager.increment_interaction(client_id)
        
        # Check if any tool event has a URL to open (music, video, etc.)
        url_to_open = None
        video_id = None
        should_open = False
        
        events = ai_engine.get_last_tool_events()
        for event in events:
            result = event.get("result", {})
            if isinstance(result, dict):
                # Check nested result
                nested_result = result.get("result", {})
                if isinstance(nested_result, dict):
                    if nested_result.get("url") and nested_result.get("open_url"):
                        url_to_open = nested_result.get("url")
                        video_id = nested_result.get("video_id")
                        should_open = True
                        logger.info(f"Found URL in nested result: {url_to_open}")
                        break
                # Check direct result
                elif result.get("url") and result.get("open_url"):
                    url_to_open = result.get("url")
                    video_id = result.get("video_id")
                    should_open = True
                    logger.info(f"Found URL in direct result: {url_to_open}")
                    break
        
        return {
            "response": response,
            "text": response,
            "client_id": client_id,
            "url": url_to_open,
            "open_url": should_open,
            "video_id": video_id
        }
    except Exception as e:
        logger.error(f"/chat error: {e}")
        return {"response": "I'm having trouble processing that right now.", "error": str(e)}

# Backward-compatible message endpoint
@app.post("/message")
async def handle_message(request: MessageRequest):
    """Handle text/voice messages and return AI response"""
    try:
        # Process voice data if provided
        if request.voice_data:
            text = await voice_processor.speech_to_text(request.voice_data)
        else:
            text = request.text

        # Get conversation context
        context = await conversation_handler.get_context(request.client_id)

        # Process with AI engine
        response = await ai_engine.process_message(text, context, request.client_id)

        # Update conversation memory
        await conversation_handler.update_conversation(request.client_id, text, response)

        return {"response": response, "client_id": request.client_id}

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Voice endpoint for audio processing
@app.post("/voice")
async def handle_voice(audio: UploadFile = File(...), client_id: str = Form(...)):
    """Handle voice audio upload and return transcription and response"""
    try:
        # Read audio data
        audio_data = await audio.read()

        # Process speech to text
        transcription = await voice_processor.speech_to_text(audio_data)

        if not transcription:
            return {"error": "Could not transcribe audio"}

        # Get conversation context
        context = await conversation_handler.get_context(client_id)

        # Process with AI engine
        response = await ai_engine.process_message(transcription, context, client_id)

        # Update conversation memory
        await conversation_handler.update_conversation(client_id, transcription, response)

        # Generate audio response
        audio_response = await voice_processor.generate_audio_response(response, client_id)

        return {
            "transcription": transcription,
            "response": response,
            "audio": audio_response,
            "client_id": client_id
        }

    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        raise HTTPException(status_code=500, detail="Voice processing failed")

# New: Smartii standardized action execution
@app.post("/v1/actions")
async def v1_actions(action: ActionModel):
    try:
        if not tool_orchestrator.is_valid_action(action.type):
            raise HTTPException(status_code=400, detail="Invalid action type")

        action_dict = action.dict(by_alias=True)
        if action.async_:
            task_id = await tool_orchestrator.execute_action_async(action_dict)
            return {"status": "accepted", "job_id": task_id, "action_id": action.id}
        else:
            result = await tool_orchestrator.execute_action(action_dict)
            return {"status": "completed", "result": result, "action_id": action.id}
    except Exception as e:
        logger.error(f"/v1/actions error: {e}")
        raise HTTPException(status_code=500, detail="Action execution failed")

# Backward-compatible action endpoint
@app.post("/action")
async def execute_action(request: ActionRequest):
    """Execute a tool action"""
    try:
        # Validate action
        if not tool_orchestrator.is_valid_action(request.type):
            raise HTTPException(status_code=400, detail="Invalid action type")

        # Check if confirmation is required
        if request.confirm:
            # In a real implementation, this would send a confirmation request
            # For now, we'll assume confirmation is granted
            pass

        # Execute action
        if request.async_:
            # Run asynchronously
            asyncio.create_task(tool_orchestrator.execute_action_async(request.dict()))
            return {"status": "accepted", "action_id": request.id}
        else:
            # Run synchronously
            result = await tool_orchestrator.execute_action(request.dict())
            return {"result": result, "action_id": request.id}

    except Exception as e:
        logger.error(f"Error executing action: {e}")
        raise HTTPException(status_code=500, detail="Action execution failed")

# New: Jobs status endpoint
@app.get("/v1/jobs/{job_id}")
async def v1_job_status(job_id: str):
    try:
        status = tool_orchestrator.get_task_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")
        # Normalize running task
        if isinstance(status, asyncio.Task):
            return {"id": job_id, "status": "running"}
        # Completed dict from orchestrator
        return {"id": job_id, **status}
    except Exception as e:
        logger.error(f"/v1/jobs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")

# New: Tools listing/introspection
@app.get("/v1/tools")
async def v1_tools(name: Optional[str] = Query(None)):
    try:
        if name:
            info = await tool_orchestrator.get_tool_info(name)
            if not info:
                raise HTTPException(status_code=404, detail="Tool not found")
            return info
        tools = await tool_orchestrator.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"/v1/tools error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tools")

# Developer: list loaded plugins
@app.get("/v1/plugins")
async def v1_plugins():
    return {"plugins": loaded_plugins}

# Developer: register a simple tool dynamically (echo kind)
@app.post("/v1/tools/register")
async def v1_tools_register(req: ToolRegisterRequest):
    # Gate on developer mode
    if not ai_engine.developer_mode:
        raise HTTPException(status_code=403, detail="Developer mode required")

    def echo_handler(params: Dict[str, Any], meta: Dict[str, Any]):
        return {"status": "ok", "params": params, "meta": meta}

    handler = echo_handler
    tool_orchestrator.register_tool(req.name, handler, description=req.description or "dynamic tool")
    return {"status": "registered", "name": req.name}

# New: Mode toggles
@app.post("/v1/mode")
async def v1_mode(mode: ModeRequest):
    try:
        if mode.developer is not None:
            ai_engine.set_mode("developer", mode.developer)
        if mode.secure is not None:
            ai_engine.set_mode("secure", mode.secure)
        return {"developer": ai_engine.developer_mode, "secure": ai_engine.secure_mode}
    except Exception as e:
        logger.error(f"/v1/mode error: {e}")
        raise HTTPException(status_code=500, detail="Failed to set mode")

# New: Proactive suggestions endpoint
@app.get("/v1/suggestions")
async def v1_suggestions(client_id: str):
    """Get proactive suggestions for the user based on context and learned patterns."""
    try:
        context = await conversation_handler.get_context(client_id)
        suggestion = await ai_engine.generate_proactive_suggestion(context, client_id)
        
        # Also check for predicted next action
        predicted_action = await memory_engine.predict_next_action(client_id)
        
        return {
            "suggestion": suggestion,
            "predicted_action": predicted_action,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"/v1/suggestions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

# New: Routines management endpoint
@app.get("/v1/routines/{user_id}")
async def get_user_routines(user_id: str):
    """Get user's learned routines and habits."""
    try:
        routines = await memory_engine.get_routines(user_id)
        return {"user_id": user_id, "routines": routines, "count": len(routines)}
    except Exception as e:
        logger.error(f"/v1/routines error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get routines")

@app.post("/v1/routines/{user_id}")
async def save_user_routine(user_id: str, routine: Dict[str, Any]):
    """Save a new routine for the user."""
    try:
        result = await memory_engine.save_routine(user_id, routine)
        return result
    except Exception as e:
        logger.error(f"/v1/routines save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save routine")

# New: Task history endpoint
@app.get("/v1/tasks/{user_id}")
async def get_task_history(user_id: str, limit: int = 20):
    """Get user's task completion history."""
    try:
        tasks = await memory_engine.get_task_history(user_id, limit)
        return {"user_id": user_id, "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"/v1/tasks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task history")

# New: Voice settings endpoint
class VoiceSettingsRequest(BaseModel):
    whispering: Optional[bool] = None
    always_listening: Optional[bool] = None
    language: Optional[str] = None

@app.post("/v1/voice/settings/{client_id}")
async def update_voice_settings(client_id: str, settings: VoiceSettingsRequest):
    """Update voice processing settings."""
    try:
        results = {}
        
        if settings.whispering is not None:
            if settings.whispering:
                results["whispering"] = await voice_processor.enable_whispering_mode(client_id)
            else:
                results["whispering"] = await voice_processor.disable_whispering_mode(client_id)
        
        if settings.always_listening is not None:
            if settings.always_listening:
                results["always_listening"] = await voice_processor.enable_always_listening(client_id)
            else:
                results["always_listening"] = await voice_processor.disable_always_listening(client_id)
        
        if settings.language:
            results["language"] = await voice_processor.set_language(settings.language)
        
        return {"status": "updated", "results": results}
    except Exception as e:
        logger.error(f"/v1/voice/settings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update voice settings")

# New: User correction endpoint for learning
class CorrectionRequest(BaseModel):
    original_message: str
    correction: str
    client_id: str

@app.post("/v1/correct")
async def handle_correction(request: CorrectionRequest):
    """Handle user corrections to improve AI responses."""
    try:
        response = await ai_engine.handle_user_correction(
            request.original_message,
            request.correction,
            request.client_id
        )
        return {"status": "learned", "response": response}
    except Exception as e:
        logger.error(f"/v1/correct error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process correction")

# New: Performance metrics endpoint
@app.get("/v1/metrics")
async def get_metrics():
    """Get AI engine performance metrics."""
    try:
        metrics = await ai_engine.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"/v1/metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# New: Self-optimization endpoint
@app.post("/v1/optimize")
async def optimize_system():
    """Trigger self-optimization analysis."""
    try:
        if not ai_engine.developer_mode:
            raise HTTPException(status_code=403, detail="Developer mode required")
        
        optimization_results = await ai_engine.optimize_self()
        return optimization_results
    except Exception as e:
        logger.error(f"/v1/optimize error: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize")

# New: Smartii memory endpoint (v1)
class V1MemoryRequest(BaseModel):
    action: str  # save|query|delete
    item: Optional[MemoryItemModel] = None
    query: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

@app.post("/v1/memory")
async def v1_memory(req: V1MemoryRequest):
    try:
        if req.action == "save":
            if not req.item:
                raise HTTPException(status_code=400, detail="Memory item required")
            payload = {
                "id": req.item.id,
                "type": req.item.kind if req.item.kind in ("episodic", "semantic", "preference") else "episodic",
                "content": req.item.content,
                "metadata": {**req.item.metadata, "tags": req.item.tags, "sensitivity": req.item.sensitivity, "created_at": req.item.created_at},
                "user_id": req.item.user_id,
            }
            result = await memory_engine.save_memory(payload)
            return result
        elif req.action == "query":
            if not req.query:
                raise HTTPException(status_code=400, detail="Query required")
            user_id = req.user_id or "default"
            results = await memory_engine.query_memory(req.query, user_id)
            return {"results": results}
        elif req.action == "delete":
            criteria = req.criteria or {}
            result = await memory_engine.delete_memory(criteria)
            return result
        else:
            raise HTTPException(status_code=400, detail="Invalid memory action")
    except Exception as e:
        logger.error(f"/v1/memory error: {e}")
        raise HTTPException(status_code=500, detail="Memory operation failed")

# Backward-compatible memory endpoint
@app.post("/memory")
async def handle_memory(request: MemoryRequest):
    """Handle memory operations"""
    try:
        if request.action == "save":
            if not request.data:
                raise HTTPException(status_code=400, detail="Data required for save action")
            result = await memory_engine.save_memory(request.data)
        elif request.action == "query":
            if not request.query:
                raise HTTPException(status_code=400, detail="Query required for query action")
            result = await memory_engine.query_memory(request.query)
        elif request.action == "delete":
            result = await memory_engine.delete_memory(request.data or {})
        else:
            raise HTTPException(status_code=400, detail="Invalid memory action")

        return {"result": result}

    except Exception as e:
        logger.error(f"Error handling memory operation: {e}")
        raise HTTPException(status_code=500, detail="Memory operation failed")

# WebSocket endpoint for real-time full duplex communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # Register state change listener
    async def state_listener(new_state: State, reason: str):
        await manager.send_personal_message(json.dumps({
            "type": "state_change",
            "state": new_state.value,
            "reason": reason,
            "is_speaking": voice_state.is_speaking,
            "is_listening": voice_state.is_listening,
            "timestamp": datetime.now().isoformat()
        }), client_id)
    
    voice_state.add_listener(state_listener)
    
    # Wake word callback
    async def on_wake_word_detected():
        logger.info(f"🔥 Wake word detected for client {client_id}")
        
        # Update state machine
        await voice_state.handle_wakeword()
        
        # Notify client
        await manager.send_personal_message(json.dumps({
            "type": "wake_word_detected",
            "timestamp": datetime.now().isoformat()
        }), client_id)
        
        # If SMARTII is speaking, interrupt immediately
        if voice_state.is_speaking:
            await manager.send_personal_message(json.dumps({
                "type": "interrupt",
                "reason": "wake_word_during_speech"
            }), client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            msg_type = message_data.get("type")

            # FULL DUPLEX: Handle voice activity detection
            if msg_type == "vad_detected":
                # User started speaking
                logger.info(f"👄 Voice activity detected for {client_id}")
                await voice_state.handle_speech_start()
                
                # If currently speaking, interrupt immediately
                if voice_state.is_speaking:
                    await manager.send_personal_message(json.dumps({
                        "type": "interrupt",
                        "reason": "user_speaking"
                    }), client_id)

            elif msg_type == "audio_stream":
                # Handle continuous audio streaming for wake word detection
                audio_bytes = base64.b64decode(message_data.get("audio", ""))
                result = await voice_processor.process_audio_stream(client_id, audio_bytes)

                # Send results back to client
                response_data = {
                    "type": "audio_processed",
                    "wake_word_detected": result.get("wake_word_detected", False),
                    "voice_activity": result.get("voice_activity", False),
                    "transcription": result.get("transcription", ""),
                    "emotion": result.get("emotion", {}),
                    "command_detected": result.get("command_detected", False),
                    "state": voice_state.get_state().value
                }

                # If there's a transcription and should respond, process it
                if result.get("should_respond") and result.get("transcription"):
                    # Update state to THINKING
                    await voice_state.handle_llm_start()
                    
                    context = await conversation_handler.get_context(client_id)
                    ai_response = await ai_engine.process_message(result["transcription"], context, client_id)
                    await conversation_handler.update_conversation(client_id, result["transcription"], ai_response)

                    # Update state to SPEAKING
                    await voice_state.handle_tts_start()
                    
                    # Generate audio response
                    audio_response = await voice_processor.generate_audio_response(ai_response, client_id)

                    response_data.update({
                        "ai_response": ai_response,
                        "audio_response": audio_response
                    })
                    
                    # When TTS ends, handle state transition
                    asyncio.create_task(voice_state.handle_tts_end())

                await manager.send_personal_message(json.dumps(response_data), client_id)

            elif msg_type == "message":
                # Process text message with state management
                await voice_state.handle_llm_start()
                
                context = await conversation_handler.get_context(client_id)
                response = await ai_engine.process_message(message_data["text"], context, client_id)
                await conversation_handler.update_conversation(client_id, message_data["text"], response)

                # Update state to SPEAKING
                await voice_state.handle_tts_start()
                
                # Generate audio response for voice interface
                audio_response = await voice_processor.generate_audio_response(response, client_id)

                await manager.send_personal_message(json.dumps({
                    "type": "response",
                    "text": response,
                    "audio": audio_response,
                    "state": voice_state.get_state().value
                }), client_id)
                
                # Handle TTS end
                asyncio.create_task(voice_state.handle_tts_end())
            
            elif msg_type == "tts_ended":
                # Client notifies TTS playback finished
                await voice_state.handle_tts_end()
            
            elif msg_type == "interrupt":
                # Force interrupt
                logger.warning(f"⚡ Force interrupt requested by {client_id}")
                await voice_state.force_interrupt()
                
                await manager.send_personal_message(json.dumps({
                    "type": "interrupted",
                    "state": voice_state.get_state().value
                }), client_id)
            
            elif msg_type == "wake_word_enable":
                # Enable wake word detection
                if WAKE_WORD_AVAILABLE and wake_word_detector:
                    sensitivity = message_data.get("sensitivity", 0.5)
                    wake_word_detector.set_sensitivity(sensitivity)
                    
                    if not wake_word_detector.is_running:
                        wake_word_detector.start(on_wake_word_detected)
                    
                    await manager.send_personal_message(json.dumps({
                        "type": "wake_word_status",
                        "enabled": True,
                        "sensitivity": sensitivity
                    }), client_id)
                else:
                    await manager.send_personal_message(json.dumps({
                        "type": "wake_word_status",
                        "enabled": False,
                        "error": "Wake word detection not available"
                    }), client_id)
            
            elif msg_type == "wake_word_disable":
                # Disable wake word detection
                if WAKE_WORD_AVAILABLE and wake_word_detector:
                    wake_word_detector.stop()
                
                await manager.send_personal_message(json.dumps({
                    "type": "wake_word_status",
                    "enabled": False
                }), client_id)
            
            elif msg_type == "get_state":
                # Get current state
                await manager.send_personal_message(json.dumps({
                    "type": "state_info",
                    "state": voice_state.get_state().value,
                    "is_speaking": voice_state.is_speaking,
                    "is_listening": voice_state.is_listening,
                    "wakeword_active": voice_state.wakeword_active
                }), client_id)

            elif msg_type == "voice_start":
                await voice_processor.start_listening(client_id)
                await voice_state.handle_speech_start()
                await manager.send_personal_message(json.dumps({"type": "listening_started"}), client_id)

            elif msg_type == "voice_stop":
                audio_data = await voice_processor.stop_listening(client_id)
                text = await voice_processor.speech_to_text(audio_data)
                await voice_state.handle_speech_end()
                await manager.send_personal_message(json.dumps({"type": "transcription", "text": text}), client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await voice_state.handle_error(str(e))
        manager.disconnect(client_id)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("SMARTII Backend starting up...")
    # Load environment
    try:
        load_dotenv()
        logger.info("Environment loaded from .env")
    except Exception as e:
        logger.warning(f".env load failed or not present: {e}")
    # Initialize components
    await memory_engine.initialize()
    await tool_orchestrator.initialize()
    # Load plugins
    load_plugins()
    # Initialize new advanced features
    try:
        from plugin_system import initialize_plugins
        await initialize_plugins()
        logger.info("Advanced plugins initialized")
    except Exception as e:
        logger.warning(f"Could not initialize advanced plugins: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("SMARTII Backend shutting down...")
    # Cleanup
    await memory_engine.close()
    await tool_orchestrator.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
