# SMARTII API Documentation

## Overview

SMARTII uses a hybrid REST/WebSocket API architecture designed for both real-time interaction and traditional request-response patterns.

**Base URL**: `http://localhost:8000`  
**WebSocket URL**: `ws://localhost:8000/ws/{client_id}`

---

## Authentication

*Currently in development mode - no authentication required for local deployment.*

Future: JWT-based authentication will be implemented for production deployments.

---

## Core Endpoints

### Health Check

```http
GET /health
```

Returns system health status.

**Response**:
```json
{
  "status": "healthy"
}
```

---

## Chat & Conversation

### Send Message (v1)

```http
POST /v1/chat
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "What's the weather like?",
  "client_id": "user123",
  "developer_mode": false,
  "secure_mode": false
}
```

**Response**:
```json
{
  "reply": "The weather in New York is sunny at 22°C.",
  "client_id": "user123",
  "audio": "base64_encoded_audio",
  "actions": [],
  "events": []
}
```

---

## Action Execution

### Execute Action

```http
POST /v1/actions
Content-Type: application/json
```

**Request Body**:
```json
{
  "id": "action-uuid",
  "type": "weather.get",
  "params": {
    "location": "London"
  },
  "confirm": false,
  "async": false,
  "meta": {
    "user_id": "user123"
  }
}
```

**Response** (Sync):
```json
{
  "status": "completed",
  "result": {
    "location": "London",
    "temperature": 18,
    "condition": "cloudy"
  },
  "action_id": "action-uuid"
}
```

**Response** (Async):
```json
{
  "status": "accepted",
  "job_id": "job-uuid",
  "action_id": "action-uuid"
}
```

### Get Job Status

```http
GET /v1/jobs/{job_id}
```

**Response**:
```json
{
  "id": "job-uuid",
  "status": "completed",
  "result": { ... }
}
```

---

## Available Tools

### List All Tools

```http
GET /v1/tools
```

**Response**:
```json
{
  "tools": [
    "email.send",
    "weather.get",
    "device.control",
    ...
  ]
}
```

### Get Tool Info

```http
GET /v1/tools?name=weather.get
```

**Response**:
```json
{
  "name": "weather.get",
  "description": "Get weather information",
  "parameters": ["params", "meta"]
}
```

---

## Memory Management

### Save Memory

```http
POST /v1/memory
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "save",
  "item": {
    "kind": "preference",
    "user_id": "user123",
    "content": "User prefers morning reminders",
    "tags": ["reminder", "preference"]
  }
}
```

### Query Memory

```http
POST /v1/memory
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "query",
  "query": "What are my reminder preferences?",
  "user_id": "user123"
}
```

**Response**:
```json
{
  "results": [
    {
      "content": "User prefers morning reminders",
      "metadata": { ... },
      "similarity": 0.95
    }
  ]
}
```

### Delete Memory

```http
POST /v1/memory
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "delete",
  "criteria": {
    "user_id": "user123",
    "tags": ["old_data"]
  }
}
```

---

## Proactive Intelligence

### Get Suggestions

```http
GET /v1/suggestions?client_id=user123
```

**Response**:
```json
{
  "suggestion": "Good morning! Would you like me to check the weather and your calendar?",
  "predicted_action": {
    "pattern": "Monday_9_check_calendar",
    "count": 15,
    "last_occurrence": "2025-11-17T09:00:00"
  },
  "timestamp": "2025-11-17T09:05:00"
}
```

### Get User Routines

```http
GET /v1/routines/{user_id}
```

**Response**:
```json
{
  "user_id": "user123",
  "routines": [
    {
      "action": "check_weather",
      "time": "07:00",
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "timestamp": "2025-11-01T07:00:00"
    }
  ],
  "count": 1
}
```

### Save Routine

```http
POST /v1/routines/{user_id}
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "check_email",
  "time": "08:00",
  "days": ["Monday", "Wednesday", "Friday"]
}
```

---

## Task History

### Get Task History

```http
GET /v1/tasks/{user_id}?limit=20
```

**Response**:
```json
{
  "user_id": "user123",
  "tasks": [
    {
      "task": "Send email to team",
      "completed_at": "2025-11-17T10:30:00",
      "success": true
    }
  ],
  "count": 1
}
```

---

## Mode Management

### Set Modes

```http
POST /v1/mode
Content-Type: application/json
```

**Request Body**:
```json
{
  "developer": true,
  "secure": false
}
```

**Response**:
```json
{
  "developer": true,
  "secure": false
}
```

---

## Voice Settings

### Update Voice Settings

```http
POST /v1/voice/settings/{client_id}
Content-Type: application/json
```

**Request Body**:
```json
{
  "whispering": true,
  "always_listening": false,
  "language": "en-US"
}
```

**Response**:
```json
{
  "status": "updated",
  "results": {
    "whispering": true,
    "always_listening": false,
    "language": true
  }
}
```

---

## Voice Processing

### Upload Voice

```http
POST /voice
Content-Type: multipart/form-data
```

**Form Data**:
- `audio`: Audio file (WAV, MP3)
- `client_id`: Client identifier

**Response**:
```json
{
  "transcription": "What's the weather like?",
  "response": "The weather is sunny at 22°C.",
  "audio": "base64_encoded_audio",
  "client_id": "user123"
}
```

---

## Plugin Management

### List Loaded Plugins

```http
GET /v1/plugins
```

**Response**:
```json
{
  "plugins": ["example_plugin"]
}
```

### Register Dynamic Tool

```http
POST /v1/tools/register
Content-Type: application/json
```

*Requires developer mode enabled*

**Request Body**:
```json
{
  "name": "custom.tool",
  "description": "My custom tool",
  "kind": "echo"
}
```

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');
```

### Events

#### Client → Server

**Start Listening**:
```json
{
  "type": "voice_start"
}
```

**Stop Listening**:
```json
{
  "type": "voice_stop"
}
```

**Audio Stream**:
```json
{
  "type": "audio_stream",
  "audio": "base64_encoded_audio_chunk"
}
```

**Send Message**:
```json
{
  "type": "message",
  "text": "Hello Smartii"
}
```

#### Server → Client

**Listening Started**:
```json
{
  "type": "listening_started"
}
```

**Audio Processed**:
```json
{
  "type": "audio_processed",
  "wake_word_detected": true,
  "voice_activity": true,
  "transcription": "Hello",
  "emotion": {
    "happy": 0.7,
    "neutral": 0.3
  },
  "command_detected": false
}
```

**Response**:
```json
{
  "type": "response",
  "text": "Hello! How can I help?",
  "audio": "base64_encoded_audio"
}
```

---

## Action Types

### Communication
- `email.send`
- `email.read`
- `sms.send`
- `whatsapp.send`
- `telegram.send`

### Productivity
- `calendar.create`
- `calendar.list`
- `note.create`
- `note.list`
- `reminder.set`
- `alarm.set`
- `timer.set`
- `todo.create`
- `todo.list`
- `document.generate`
- `document.summarize`

### Information
- `web.search`
- `weather.get`
- `news.get`
- `price.track`
- `map.navigate`

### Smart Home
- `device.control`
- `device.state`
- `scene.activate`
- `routine.trigger`

### Media
- `music.play`
- `tts.speak`
- `stt.listen`

### Files & Analysis
- `file.read`
- `file.write`
- `image.analyze`
- `image.generate`
- `audio.transcribe`
- `video.summarize`

### Memory & Automation
- `memory.save`
- `memory.query`
- `automation.create`
- `python.execute`
- `system.command`

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

**Common Status Codes**:
- `400` - Bad Request (invalid parameters)
- `403` - Forbidden (developer mode required)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Rate Limiting

*Not implemented yet - planned for production*

Future: 100 requests per minute per client_id

---

## Examples

### Complete Workflow: Smart Home Control

1. **Check device state**:
```http
POST /v1/actions
{
  "type": "device.state",
  "params": {
    "provider": "homeassistant",
    "entity_id": "light.living_room"
  }
}
```

2. **Control device**:
```http
POST /v1/actions
{
  "type": "device.control",
  "params": {
    "provider": "homeassistant",
    "domain": "light",
    "service": "turn_on",
    "data": {
      "entity_id": "light.living_room",
      "brightness": 255
    }
  }
}
```

### Complete Workflow: Voice Interaction

1. **Connect WebSocket**
2. **Send audio stream**
3. **Receive transcription & response**
4. **Play audio response**

---

*This API is continuously evolving. Check the repository for the latest updates.*
