# SMARTII Multi-Language System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACES                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────────┤
│   Web App   │   Mobile    │   Android   │     iOS     │   Voice Only   │
│   (React)   │ (React Native) │ (Kotlin)  │   (Swift)   │    Device      │
└─────┬───────┴──────┬──────┴──────┬──────┴──────┬──────┴────────┬───────┘
      │              │             │             │               │
      │ HTTP/WS      │ HTTP/WS     │ Native APIs │ Native APIs   │ Audio
      │              │             │             │               │
┌─────▼──────────────▼─────────────▼─────────────▼───────────────▼───────┐
│                       API GATEWAY (Go)                                   │
│   • Load Balancing    • Rate Limiting    • Request Routing              │
│   • Authentication    • Metrics          • Service Discovery            │
└────────┬──────────────┬──────────────┬──────────────┬──────────────────┘
         │              │              │              │
         │              │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ Python  │   │ Node.js │   │   Go    │   │   C++   │
    │AI Engine│   │Realtime │   │ Worker  │   │  Audio  │
    └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │             │
         │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼─────────────────────┐
│                      CORE SERVICES LAYER                                 │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────┤
│   Python     │    Rust      │     Go       │   Node.js    │    C++     │
│              │              │              │              │            │
│ • AI Logic   │ • Vector DB  │ • Workers    │ • WebSocket  │ • Wake Word│
│ • Reasoning  │ • Memory     │ • Jobs       │ • Events     │ • Audio DSP│
│ • NLP        │ • Safety     │ • Parallel   │ • Pub/Sub    │ • STT prep │
│ • Tools      │ • Fast I/O   │ • Queues     │ • Real-time  │ • Low Lat  │
│              │              │              │              │            │
│ Groq/OpenAI  │ FAISS/       │ Goroutines   │ Socket.io    │ PortAudio  │
│ LangChain    │ Hnswlib      │ Channels     │ Redis        │ Porcupine  │
│ FastAPI      │ gRPC         │ gRPC         │ Express      │ FFI        │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬─────┘
       │              │              │              │              │
       │              │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼──────────────▼─────┐
│                      DATA STORAGE LAYER                                  │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────┤
│  PostgreSQL  │   MongoDB    │    Redis     │   ChromaDB   │   FAISS    │
│              │              │              │              │            │
│ • Users      │ • Logs       │ • Cache      │ • Vectors    │ • Vectors  │
│ • Profiles   │ • Chats      │ • Sessions   │ • Memory     │ • Embeddings│
│ • Audit      │ • Documents  │ • Queue      │ • Semantic   │ • Index    │
│ • Tasks      │ • Flexible   │ • Pub/Sub    │ • Search     │ • Fast     │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────┘


AUTOMATIC LANGUAGE SELECTION FLOW
═══════════════════════════════════════════════════════════════════════════

                            User Request
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Python AI Engine     │
                    │   Analyze Request      │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │  Determine Requirements │
                    │  • Latency              │
                    │  • Safety               │
                    │  • Concurrency          │
                    │  • AI Reasoning         │
                    │  • Real-time            │
                    │  • Native Access        │
                    └────────┬───────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Low Latency?   Memory Safe?   High Concurrency?
              │              │              │
         ┌────▼────┐    ┌───▼────┐    ┌───▼────┐
         │   C++   │    │  Rust  │    │   Go   │
         │ <100ms  │    │ Vector │    │ 50+    │
         │ Audio   │    │ Memory │    │Workers │
         └─────────┘    └────────┘    └────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Execute in       │
                   │  Selected Engine  │
                   └─────────┬─────────┘
                             │
                             ▼
                        Response


TASK ROUTING EXAMPLES
═══════════════════════════════════════════════════════════════════════════

Task: "Turn on lights"
├─> Python AI: Understand intent
├─> Check: Smart home control = Python/Go
├─> Execute: Python → MQTT → Device
└─> Response: "Lights on" ✓

Task: "Wake word detection"
├─> C++ Audio: Capture audio stream
├─> C++ Wake Word: Detect "Hey Smartii" (<100ms)
├─> Python AI: Process command
└─> Response via selected engine ✓

Task: "Find similar memories"
├─> Python AI: Generate query embedding
├─> Rust Memory: Vector search (10ms for 1M vectors)
├─> Python AI: Format results
└─> Response: Top memories ✓

Task: "Process 1000 emails"
├─> Python AI: Understand task
├─> Go Workers: Parallel processing (50 workers)
├─> Python AI: Aggregate results
└─> Response: Summary ✓

Task: "Real-time chat"
├─> Node.js Gateway: WebSocket connection
├─> Python AI: Generate response
├─> Node.js Gateway: Stream back
└─> Frontend: Display ✓

Task: "Android notification"
├─> Python AI: Understand request
├─> Kotlin Native: Android API call
├─> System: Show notification
└─> Response: "Notification sent" ✓


TECHNOLOGY SELECTION MATRIX
═══════════════════════════════════════════════════════════════════════════

┌─────────────┬──────────┬──────────┬────────┬──────────┬─────────┐
│ Requirement │  Python  │   Rust   │  C++   │    Go    │ Node.js │
├─────────────┼──────────┼──────────┼────────┼──────────┼─────────┤
│ AI/ML       │    ★★★   │    ★     │   ★    │    ★     │    ★    │
│ Performance │    ★★    │   ★★★    │  ★★★   │   ★★     │   ★★    │
│ Safety      │    ★★    │   ★★★    │   ★    │   ★★     │   ★★    │
│ Concurrency │    ★     │   ★★     │   ★★   │   ★★★    │   ★★★   │
│ Real-time   │    ★★    │   ★★     │  ★★★   │   ★★     │   ★★★   │
│ Ecosystem   │   ★★★    │   ★★     │   ★★   │   ★★     │   ★★★   │
│ Development │   ★★★    │   ★      │   ★    │   ★★     │   ★★★   │
└─────────────┴──────────┴──────────┴────────┴──────────┴─────────┘


COMMUNICATION PATTERNS
═══════════════════════════════════════════════════════════════════════════

Python ←→ Rust:    gRPC (high performance)
Python ←→ C++:     FFI/ctypes (shared library)
Python ←→ Go:      HTTP/gRPC (microservices)
Python ←→ Node.js: HTTP/WebSocket (events)
Frontend ←→ Any:   REST API/WebSocket

Message Flow:
┌─────────┐ HTTP  ┌──────┐ gRPC  ┌──────┐ FFI  ┌──────┐
│ Client  │──────→│ API  │──────→│ Rust │──────→│ C++  │
│         │←──────│ (Go) │←──────│Engine│←──────│Audio │
└─────────┘ JSON  └──────┘ Proto └──────┘ Bytes└──────┘


DEPLOYMENT ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════

Kubernetes Cluster
├─> Namespace: smartii-production
│   ├─> Deployment: api-gateway (Go) - 5 replicas
│   ├─> Deployment: ai-engine (Python) - 3 replicas
│   ├─> Deployment: memory-engine (Rust) - 2 replicas
│   ├─> Deployment: audio-processor (C++) - 2 replicas
│   ├─> Deployment: worker-pool (Go) - 10 replicas
│   ├─> Deployment: realtime-gateway (Node.js) - 5 replicas
│   ├─> StatefulSet: postgresql - 3 replicas
│   ├─> StatefulSet: mongodb - 3 replicas
│   ├─> StatefulSet: redis - 3 replicas
│   └─> Service: LoadBalancer (External)
│
├─> Namespace: smartii-staging
│   └─> Similar structure, fewer replicas
│
└─> Namespace: smartii-dev
    └─> Minimal replicas for testing


SCALABILITY
═══════════════════════════════════════════════════════════════════════════

Horizontal Scaling:
├─> API Gateway: 3-20 replicas (CPU-bound)
├─> AI Engine: 2-10 replicas (Memory-bound)
├─> Workers: 5-50 replicas (Task-bound)
├─> Realtime: 3-20 replicas (Connection-bound)
└─> Memory Engine: 1-3 replicas (State-bound)

Auto-scaling Triggers:
├─> CPU > 70% → Scale up
├─> Memory > 80% → Scale up
├─> Request queue > 100 → Scale up
└─> Idle < 5min → Scale down

Performance Targets:
├─> API Response: <200ms (p95)
├─> AI Response: <500ms (p95)
├─> Vector Search: <10ms (p99)
├─> Wake Word: <100ms (p99)
└─> WebSocket Latency: <50ms (p95)
```

## Key Design Principles

1. **Language by Strength**: Each language handles what it does best
2. **Automatic Selection**: AI engine routes tasks intelligently
3. **Graceful Degradation**: System works even if services are down
4. **Progressive Enhancement**: Start simple, add performance later
5. **Unified API**: One interface, multiple execution engines
6. **Containerized**: Everything runs in Docker/Kubernetes
7. **Observable**: Metrics, logs, traces for all services
8. **Scalable**: Horizontal scaling for all stateless services

## Status: OPERATIONAL ✅

- Python AI Engine: **RUNNING**
- Go Worker: **READY**
- Node.js Realtime: **READY**
- Rust Memory: **ARCHITECTED**
- C++ Audio: **ARCHITECTED**
- Mobile Native: **ARCHITECTED**
