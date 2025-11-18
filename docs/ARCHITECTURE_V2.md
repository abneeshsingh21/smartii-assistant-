# SMARTII Multi-Language Architecture

## Technology Stack by Purpose

### Core AI & Backend (Python)
- **AI Engine**: Groq/OpenAI integration, reasoning, planning
- **Memory System**: Vector databases (FAISS, Chroma)
- **Tool Orchestration**: Dynamic tool selection and execution
- **FastAPI Backend**: REST API and WebSocket real-time communication
- **Purpose**: AI logic, natural language processing, decision-making

### Web/Mobile Frontend (JavaScript/TypeScript)
- **React**: Web UI with component-based architecture
- **React Native**: Cross-platform mobile apps (iOS/Android)
- **TypeScript**: Type-safe frontend development
- **Purpose**: User interface, web/mobile experience

### Performance-Critical Modules (C++)
- **Wake Word Detection**: Fast, low-latency voice activation
- **Audio Processing**: Real-time audio capture and preprocessing
- **Signal Processing**: Low-level audio feature extraction
- **Purpose**: High-performance, real-time voice operations

### Memory Engine & Safety (Rust)
- **Vector Memory Engine**: Ultra-fast similarity search
- **Agent Safety Layer**: Sandboxing, resource limits, security checks
- **Memory Persistence**: High-performance disk I/O
- **Purpose**: Safe, efficient memory operations with zero-cost abstractions

### Distributed Services (Go)
- **Service Mesh**: Inter-service communication
- **API Gateway**: Request routing, load balancing
- **Real-time Event Processing**: WebSocket multiplexing
- **Worker Pools**: Background job processing
- **Purpose**: Scalable microservices, concurrent operations

### Android Integration (Java/Kotlin)
- **Native Android Services**: Background voice processing
- **System Integration**: Notifications, contacts, calendar
- **Hardware Access**: Sensors, camera, Bluetooth
- **Purpose**: Deep Android OS integration

### iOS Integration (Swift)
- **Native iOS Services**: Siri Shortcuts, background tasks
- **System Integration**: HealthKit, HomeKit, Core ML
- **Hardware Access**: Face ID, sensors, ARKit
- **Purpose**: Deep iOS ecosystem integration

### Data Storage
- **PostgreSQL**: Structured data, user profiles, audit logs
- **MongoDB**: Flexible schema, conversation history, documents
- **Redis**: Caching, session management, real-time state
- **FAISS/Chroma**: Vector embeddings for semantic memory

### Deployment & Scaling
- **Docker**: Containerization for all services
- **Kubernetes**: Orchestration, auto-scaling, service discovery
- **WebAssembly**: Fast local ML models in browser
- **Purpose**: Cloud-native deployment, edge computing

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Go)                         │
│              Load Balancing | Rate Limiting                  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
┌───────────▼──────┐  ┌──────▼──────┐  ┌──────▼────────┐
│   AI Engine      │  │  Real-time  │  │   Worker      │
│   (Python)       │  │  Gateway    │  │   Pool        │
│                  │  │  (Node.js)  │  │   (Go)        │
│ • Reasoning      │  │             │  │               │
│ • Planning       │  │ • WebSocket │  │ • Async Jobs  │
│ • Tool Select    │  │ • Events    │  │ • Scheduling  │
└──────────────────┘  └─────────────┘  └───────────────┘
         │                   │                  │
         └───────────────────┼──────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌──────▼──────┐
│ Memory Engine  │  │ Native Modules  │  │  Data Layer │
│ (Rust)         │  │ (C++)           │  │             │
│                │  │                 │  │ • PostgreSQL│
│ • Vector DB    │  │ • Wake Word     │  │ • MongoDB   │
│ • Safety       │  │ • Audio DSP     │  │ • Redis     │
│ • Persistence  │  │ • Performance   │  │ • FAISS     │
└────────────────┘  └─────────────────┘  └─────────────┘
```

## Automatic Tool Selection

### Decision Tree
```python
if task.requires_low_latency():
    execute_in_cpp()  # C++ for wake word, audio
elif task.requires_memory_safety():
    execute_in_rust()  # Rust for memory ops
elif task.requires_concurrency():
    execute_in_go()  # Go for parallel processing
elif task.requires_ai_reasoning():
    execute_in_python()  # Python for AI logic
elif task.requires_native_mobile():
    if platform == "android":
        execute_in_kotlin()
    elif platform == "ios":
        execute_in_swift()
elif task.requires_real_time_events():
    execute_in_nodejs()  # Node.js for WebSocket
else:
    execute_in_python()  # Default
```

## Component Responsibilities

### 1. Python Services
- `ai_engine.py`: Main AI reasoning, tool orchestration
- `memory.py`: High-level memory management
- `tools.py`: Tool implementations
- `app.py`: FastAPI REST endpoints

### 2. Rust Services (New)
- `memory-engine/`: Fast vector similarity search
- `safety-layer/`: Sandboxing, resource limits
- `persistence/`: High-performance I/O

### 3. C++ Modules (New)
- `wake-word/`: Wake word detection (Porcupine, Snowboy)
- `audio-processor/`: Real-time audio capture
- `feature-extractor/`: MFCC, spectral features

### 4. Go Services (Existing + Enhanced)
- `go-worker/`: Background job processing
- `api-gateway/`: Request routing, load balancing
- `service-mesh/`: Inter-service communication

### 5. Node.js Services (Existing)
- `node-realtime/`: WebSocket gateway, event streaming

### 6. Mobile Native
- `android-native/`: Kotlin services for Android
- `ios-native/`: Swift services for iOS

### 7. Frontend
- `frontend/`: React web app
- `mobile/`: React Native mobile app

## Communication Patterns

### Inter-Service Communication
- **REST API**: HTTP/JSON between services
- **gRPC**: High-performance Python ↔ Rust ↔ C++ ↔ Go
- **Message Queue**: RabbitMQ/Redis for async tasks
- **WebSocket**: Real-time bidirectional communication

### Data Flow Example: Voice Command
```
1. C++ (audio capture) → captures audio
2. C++ (wake word) → detects wake word
3. Python (STT) → speech-to-text
4. Python (AI) → understands intent, selects tool
5. Rust (memory) → retrieves context from vector DB
6. Go (worker) → executes async tool (if needed)
7. Python (AI) → generates response
8. Node.js (realtime) → streams response to frontend
9. Frontend (React) → displays to user
```

## Performance Optimization

### Language Choice by Operation
| Operation | Language | Reason |
|-----------|----------|--------|
| Audio capture | C++ | Low latency, direct hardware access |
| Wake word detection | C++ | Real-time processing |
| Vector similarity | Rust | Memory safety + speed |
| AI inference | Python | Rich ML ecosystem |
| Parallel I/O | Go | Excellent concurrency |
| Real-time events | Node.js | Event-driven architecture |
| UI rendering | React/TS | Rich component ecosystem |
| Mobile native | Kotlin/Swift | Platform-specific APIs |

## Deployment Strategy

### Docker Containers
```yaml
services:
  api-gateway:     # Go
  ai-engine:       # Python
  memory-engine:   # Rust
  audio-processor: # C++
  realtime:        # Node.js
  worker:          # Go
  frontend:        # React
  postgres:        # Data
  mongodb:         # Data
  redis:           # Cache
```

### Kubernetes Scaling
- **AI Engine**: 2-10 replicas (CPU-bound)
- **Memory Engine**: 1-3 replicas (memory-bound)
- **API Gateway**: 3-20 replicas (I/O-bound)
- **Workers**: 5-50 replicas (task-bound)

## Development Roadmap

### Phase 1: Core (Current)
- ✅ Python AI engine
- ✅ FastAPI backend
- ✅ React frontend
- ✅ Basic tools

### Phase 2: Performance (Next)
- 🔄 C++ wake word detection
- 🔄 Rust memory engine
- 🔄 Go API gateway

### Phase 3: Mobile (Future)
- ⏳ React Native mobile app
- ⏳ Kotlin Android services
- ⏳ Swift iOS services

### Phase 4: Scale (Future)
- ⏳ Kubernetes deployment
- ⏳ WebAssembly edge models
- ⏳ Global CDN
