---
sessionId: session-261106-211019-195a
---

# Project Plan

# Haven AI — Project Plan

## Overview
Haven is a **JARVIS-style local AI assistant** — a web dashboard with an AI brain, voice conversation, memory, games, agent tools, and web search. It runs 100% offline on your PC (except optional web search) and is deployable to TrueNAS via Docker.

## Owner
- **User:** joedog37
- **TrueNAS:** http://192.168.0.140/
- **Local interface:** http://127.0.0.1:8000

---

## Architecture

```
Haven/
├── Model/                          # AI models (persistent)
│   ├── Phi-3-mini-4k-instruct-q4.gguf    # Chat brain (~2.7GB)
│   ├── kokoro/                       # TTS voice models
│   └── vosk-model/                   # Speech recognition
├── Pc/
│   ├── main.py                       # Entry point: loads everything, starts server
│   ├── chat/
│   │   └── repository.py             # AI chat brain (Phi-3 via llama-cpp)
│   ├── memory/
│   │   ├── engine.py                 # Memory management with JSON storage
│   │   └── storage.json              # Persistent memory
│   ├── agent/
│   │   └── tools/
│   │       ├── manager.py            # Agent tools orchestrator
│   │       ├── clock.py              # Time, date, alarm, timer
│   │       ├── device.py             # System info queries
│   │       ├── filesystem.py         # File/directory operations
│   │       ├── network.py            # Network status
│   │       └── weather.py            # Weather lookup
│   ├── server/
│   │   ├── api.py                    # FastAPI backend (29+ endpoints)
│   │   └── link_manager.py           # Device linking
│   ├── voice/
│   │   ├── tts.py                    # Kokoro TTS wrapper
│   │   └── stt.py                    # Vosk speech-to-text
│   ├── games/
│   │   ├── engine.py                 # Basic games: trivia, guessing, wordle, RPS, tic-tac-toe, 20 questions
│   │   ├── dnd_game.py               # DnD Adventure (AI-generated)
│   │   └── oregon_trail.py           # Oregon Trail (AI-generated)
│   ├── web/
│   │   ├── index.html                # JARVIS dashboard (CSS + JS inline)
│   │   ├── avatar_face_circle.png    # Avatar image
│   │   └── app.js                    # (unused, all JS in index.html)
│   ├── web_search/
│   │   └── search.py                 # DuckDuckGo web search
│   ├── utils/
│   │   ├── config.py                 # Configuration
│   │   ├── logger.py                 # Logging
│   │   └── paths.py                  # Path utilities
│   ├── saves/                        # Game saves (persistent)
│   │   ├── dnd_save.json
│   │   └── oregon_save.json
│   ├── logs/                         # Runtime logs
│   ├── gui/                          # Legacy PySide6 GUI (deprecated)
│   ├── model_loader/                 # Legacy model loader (deprecated)
│   └── debug/                        # Debug utilities
├── Dockerfile                        # Docker build for TrueNAS
├── docker-compose.yml                # Docker Compose with volumes & resource limits
├── .dockerignore                     # Docker build exclusions
├── TRUENAS_DEPLOY.md                 # TrueNAS deployment guide
├── requirements.txt                  # Python dependencies
└── requirements-optional.txt         # Optional packages
```

---

## Implemented Features

### ✅ Core AI Chat
- **Ollama** with **llama3.1 (8B)** model — GPU accelerated on RTX 3050
- Real-time chat via WebSocket (`/ws/chat`)
- REST API fallback (`/api/message`)
- System prompt with personality and behavior guidelines
- Repetition penalty and sentence deduplication
- Tool call filtering (strips invalid `[[SPEECH:...]]` patterns)

### ✅ Memory System
- Persistent JSON storage (`storage.json`)
- User profile detection by Windows username
- Conversation history with context awareness
- Memory retrieval for relevant past conversations

### ✅ Voice System
- **TTS (Kokoro)**: Offline text-to-speech with natural female voices
  - Default voice: `af_heart` (warm, sweet)
  - Multiple voices available
  - Audio streamed via WebSocket as base64
- **STT (Vosk)**: Offline speech-to-text
  - Microphone capture via browser
  - Audio sent to server for transcription

### ✅ Agent Tools
- **Clock**: Current time, date, alarms, timers
- **Device**: System information queries
- **Filesystem**: File and directory operations
- **Network**: Network status and connectivity
- **Weather**: Weather lookup for any location
- **YouTube**: Channel scanning, recent videos, title suggestions (RSS-based, no API key)

### ✅ Games
- **Basic Games** (`games/engine.py`):
  - Trivia (15 questions, scoring)
  - Number Guessing (1-100, 7 tries)
  - Wordle (5-letter words, 6 tries)
  - Rock Paper Scissors
  - Tic-Tac-Toe (vs AI)
  - 20 Questions
- **DnD Adventure** (`games/dnd_game.py`):
  - AI-generated fantasy adventures
  - Character creation (name, race, class)
  - Combat, exploration, inventory system
  - Persistent saves
- **Oregon Trail** (`games/oregon_trail.py`):
  - AI-generated journey simulation
  - Profession selection, supply management
  - Travel events, hunting, trading
  - Persistent saves

### ✅ Web Search
- DuckDuckGo integration for internet lookups
- Connected to chat model for knowledge queries
- Graceful fallback when unavailable

### ✅ Web Dashboard
- **JARVIS-style interface** with dark theme and blue accents
- **Awakening animation** on startup
- **Avatar panel**: Circular avatar with glow effects, status indicators
- **Chat area**: Message bubbles, typing indicators, auto-scroll
- **System info**: CPU, RAM, disk usage, model status
- **Voice controls**: Mic button, speaker toggle, auto-play
- **Game UI**: DnD and Oregon Trail buttons, game overlay with choices
- **Read Aloud**: 🔊 button for TTS of game text
- **Status indicators**: Model, memory, TTS, STT, web search

### ✅ Server API (29+ endpoints)
- `/api/status` — system status
- `/api/message` — chat via REST
- `/ws/chat` — real-time WebSocket chat
- `/api/system` — CPU/RAM/disk info
- `/api/tools/*` — agent tool endpoints
- `/api/game/dnd/*` — DnD game endpoints
- `/api/game/oregon/*` — Oregon Trail endpoints
- `/api/games/status` — game health check
- `/api/game/voice` — TTS for game text

### ✅ Docker Deployment
- Multi-stage Dockerfile (Python 3.12)
- Docker Compose with volume mounts for live code updates
- Resource limits (CPU: 4 cores, memory: 8GB)
- Health checks
- TrueNAS deployment guide

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Chat AI | ✅ Complete | Ollama with llama3.1 (8B), GPU accelerated |
| Memory | ✅ Complete | JSON storage, user profiles, fact learning |
| Voice TTS | ✅ Complete | Kokoro, 54 voices, synchronous with chat |
| Voice STT | ✅ Complete | Vosk, offline |
| Agent Tools | ✅ Complete | 6 tools: clock, device, filesystem, network, weather, YouTube |
| Basic Games | ✅ Complete | 6 games |
| DnD Adventure | ✅ Complete | AI-generated, saves |
| Oregon Trail | ✅ Complete | AI-generated, saves |
| Web Search | ✅ Complete | DuckDuckGo |
| Web Dashboard | ✅ Complete | Full JARVIS UI, typing indicator fixed |
| YouTube Tool | ✅ Complete | Channel scanning via RSS, no API key needed |
| Avatar | ✅ Fixed | clip-path circle, PNG images |

---

## Future Roadmap

### Phase 1: Polish & Stability (Next)
- [ ] Game voice narration auto-play during gameplay
- [ ] Better error messages in web UI
- [ ] Chat export/save functionality
- [ ] Theme customization (light/dark toggle)
- [ ] Mobile responsive design

### Phase 2: Enhanced Agent System
- [ ] Code generation tool (with preview)
- [ ] File creation/editing via chat
- [ ] Scheduled tasks and reminders
- [ ] Calendar integration
- [ ] Email notifications

### Phase 3: Advanced Features
- [ ] Multi-user support with authentication
- [ ] Device pairing and remote access
- [ ] Avatar animation (lip sync, gestures)
- [ ] Music playback and control
- [ ] Smart home integration
- [ ] Custom skill/plugins system

### Phase 4: TrueNAS Deployment
- [ ] Complete TrueNAS deployment (blocked by Docker group access)
- [ ] GPU passthrough for faster inference
- [ ] Automatic updates via TrueNAS
- [ ] Resource monitoring dashboard

---

## Dependencies

### Core (requirements.txt)
- **Ollama** — AI model runtime (llama3.1 8B, GPU accelerated) — installed from ollama.com
- `fastapi` + `uvicorn` — Web server
- `kokoro-onnx` + `soundfile` — TTS voice
- `vosk` + `pyaudio` — Speech recognition
- `duckduckgo-search` — Web search
- `psutil` — System monitoring
- `Pillow` + `cryptography` — Image handling, security
- `pydantic`, `orjson`, `aiohttp`, `websockets` — API utilities

### Optional (requirements-optional.txt)
- Additional packages for extended features

---

## Deployment

### Local (PC)
```bash
# First, ensure Ollama is running with llama3.1 model
ollama pull llama3.1

# Then start Haven
G:\Haven\Pc\venv\Scripts\python.exe G:\Haven\Pc\main.py
```
Browser opens to http://127.0.0.1:8000

**Note:** Ollama must be running before starting Haven. Install from https://ollama.com

### Docker (TrueNAS)
```bash
# Build image
docker build -t joedog37/haven-ai:latest .

# Push to Docker Hub
docker push joedog37/haven-ai:latest

# On TrueNAS via SSH
ssh joedog37@192.168.0.140
cd ~/haven
docker compose up -d
```
Access at http://192.168.0.140:8000

See `TRUENAS_DEPLOY.md` for full guide.

---

## Notes
- **Ollama required**: Install from https://ollama.com, run `ollama pull llama3.1` to download the model
- **Voice models optional**: Kokoro in `Model/kokoro/`, Vosk in `Model/vosk-model/`
- **100% offline**: All AI runs locally, no cloud dependencies
- **Web search optional**: Requires internet, uses DuckDuckGo
- **YouTube channel**: Configured as @thunderheadpictures (UCdaLG2eOSy28l-5s31QVKXQ)
- **User**: Joseph Rice (middle name Andrew)


# Delivery Steps

###   Step 1: Create HAVEN_PLAN.md project plan
Create a comprehensive project plan document at the project root that reflects the actual current state of Haven.

- Document all implemented modules: chat (Phi-3), memory (JSON), voice (Kokoro TTS + Vosk STT), agent tools (clock, device, filesystem, network, weather), games (6 basic + DnD + Oregon Trail), web search (DuckDuckGo), web dashboard (JARVIS UI), and server API (29+ endpoints).
- Include the actual file structure with all current directories and files.
- Add a status table showing what's complete vs what's planned.
- Include future roadmap with 4 phases: Polish, Enhanced Agent, Advanced Features, TrueNAS Deployment.
- Document deployment options (local PC + Docker/TrueNAS).
- List all dependencies from requirements.txt.
- Note current blockers (TrueNAS Docker group access).