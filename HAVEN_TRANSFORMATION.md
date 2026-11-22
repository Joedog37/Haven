---
sessionId: session-261106-184200-bt6r
---

# Requirements

## Overview
Transform Haven from a scattered PySide6 desktop app into a **JARVIS-style web dashboard** with:
- A FastAPI backend serving the AI brain, memory, and all logic
- An HTML/CSS/JS web frontend with a dashboard layout (avatar, chat, system info, voice controls, games)
- Full voice conversation: Haven listens to your voice and replies with a natural female voice
- Text and mini-games playable in the chat
- 100% offline operation (except optional web search)
- Future-ready for NAS deployment

## Goals
1. **Clean architecture** — organized code, reliable startup, no scattered files
2. **Web interface** — accessible from browser on your PC (and later NAS)
3. **Voice interaction** — speech-to-text listening + text-to-speech responses with a sweet, natural female voice
4. **Games and fun** — word games, trivia, and mini-games in the interface
5. **JARVIS feel** — dashboard with system info, avatar, and a command-center aesthetic

## Out of Scope (for now)
- NAS deployment (architecture will support it later)
- Multi-device pairing and authentication
- Avatar animation (static image for now)
- Internet search integration

## Key Decisions
- **Kokoro TTS** for voice — free, offline, natural-sounding, ~330MB model, Apache 2.0 license. Female voices like `af_heart` sound warm and sweet.
- **Vosk** for speech recognition — fully offline, free, reliable. Requires downloading an English model (~90MB) once.
- **FastAPI + WebSockets** for real-time chat and voice streaming
- **Static HTML/JS frontend** — no build tools needed, simple and portable


# Technical Design

## Current State
- `main.py` and `chat_repository.py` at project root, scattered with `gui/`, `memory/`, `server/`, `model_loader/`, `utils/`, `debug/` folders
- `model_loader/loader.py` has hardcoded path `F:\Haven\Model` (wrong)
- PySide6 GUI with chat panel and avatar panel
- FastAPI server on `127.0.0.1:8000` with `/api/message` and `/api/status`
- Memory engine with JSON storage (`storage.json`)
- No voice capabilities, no games

## Proposed Architecture
```
Haven/
├── Model/                    # AI models (GGUF, Kokoro TTS, Vosk STT)
│   ├── Phi-3-mini-4k-instruct-q4.gguf
│   ├── kokoro/               # Kokoro TTS model files
│   └── vosk-model/           # Vosk speech recognition model
├── Pc/
│   ├── main.py               # Entry point: starts FastAPI + Uvicorn
│   ├── chat/
│   │   └── repository.py     # AI chat brain (moved from root)
│   ├── memory/
│   │   ├── engine.py         # Memory management
│   │   └── storage.json      # Persistent memory
│   ├── agent/                # Agent system for code & file operations
│   │   ├── manager.py        # Agent orchestrator, approval workflow
│   │   ├── tools/            # Safe tool implementations
│   │   │   ├── file_tool.py  # Read, create, modify files
│   │   │   ├── code_tool.py  # Generate and format code
│   │   │   └── exec_tool.py  # Execute code in sandbox
│   │   ├── approval.py       # Approval request/confirmation system
│   │   └── activity_log.py   # Log all agent actions
│   ├── server/
│   │   ├── api.py            # FastAPI endpoints (enhanced)
│   │   └── websocket.py      # Real-time chat via WebSockets
│   ├── voice/
│   │   ├── tts.py            # Kokoro TTS wrapper
│   │   └── stt.py            # Vosk speech-to-text wrapper
│   ├── games/
│   │   ├── manager.py        # Game dispatcher
│   │   ├── trivia.py         # Trivia game
│   │   ├── word_games.py     # Word games (20 questions, hangman)
│   │   └── storytelling.py   # Interactive storytelling
│   ├── utils/
│   │   ├── config.py         # Configuration
│   │   ├── paths.py          # Path utilities
│   │   └── logger.py         # Logging
│   ├── web/                  # Static web frontend
│   │   ├── index.html        # Main dashboard page
│   │   ├── style.css         # JARVIS-style dark theme
│   │   └── app.js            # Frontend logic (chat, voice, games, agent)
│   └── logs/                 # Runtime logs
├── requirements.txt          # Updated with Kokoro, Vosk, PyAudio
└── HAVEN_PLAN.md             # Updated roadmap
```

## Key Components

### 1. Backend Restructure
- Move `chat_repository.py` into `Pc/chat/repository.py`
- Enhance `server/api.py` with WebSocket support for real-time chat
- Add `server/websocket.py` for WebSocket handlers
- Keep existing REST endpoints for compatibility

### 2. Voice System (`voice/`)
- **TTS (`voice/tts.py`)**: Wraps Kokoro TTS, generates audio from text, returns WAV/MP3
- **STT (`voice/stt.py`)**: Wraps Vosk, captures microphone input, returns transcribed text
- Both run offline, models stored in `Model/kokoro/` and `Model/vosk-model/`

### 3. Game System (`games/`)
- **Manager (`games/manager.py`)**: Detects game commands, routes to the right game
- **Trivia**: Questions and answers, scoring
- **Word games**: 20 Questions, Hangman, Word chain
- **Storytelling**: Collaborative story building with the AI

### 4. Web Frontend (`web/`)
- **JARVIS-style dashboard** with:
  - Left panel: Haven's avatar with status indicator
  - Center: Chat area with message bubbles
  - Right panel: System info (CPU, RAM, model status) with collapsible sections
  - Bottom: Text input + voice buttons (mic, speaker)
  - Game area: Overlay or sidebar for active games
  - **Agent panel**: Shows pending approval requests with accept/deny buttons
  - **Activity log**: Viewable panel showing all agent actions with filters
  - **Kill switch**: Prominent toggle to enable/disable all agent tools
- **Dark theme** with blue accents (JARVIS aesthetic)
- **WebSocket connection** for real-time messaging and approval notifications
- **Voice controls**: Record button, play audio, auto-speak responses
- **Agent UI components**:
  - Approval cards showing what Haven wants to do (file path, action type, preview)
  - Code preview with syntax highlighting for generated code
  - Activity timeline with search and filter by action type
  - Agent status indicator (enabled/disabled)

### 5. Agent System (`agent/`)
**This is the key feature that lets Haven design and write code like an AI assistant.**

- **Manager (`agent/manager.py`)**: Orchestrates agent actions, interprets user requests, and routes to appropriate tools
- **Tools (`agent/tools/`)**: Safe, approval-based operations:
  - **File Tool**: Read, create, and modify files within allowed directories
  - **Code Tool**: Generate code in various languages with proper formatting
  - **Execute Tool**: Run code in a sandboxed environment with resource limits
- **Approval System (`agent/approval.py`)**: Every action requires user confirmation before execution
  - Haven proposes an action with details (what file, what change, why)
  - User approves or denies via the web interface
  - Denied actions are logged but not executed
- **Activity Log (`agent/activity_log.py`)**: Records all agent actions, approvals, and denials
  - Stored in `logs/agent_activity.json`
  - Viewable and searchable in the web dashboard
  - Includes timestamps, action type, files affected, and outcome
- **Emergency Kill Switch**: Global setting to disable all agent tools immediately
  - Accessible from the dashboard and via command (`/agent off`)
  - When disabled, Haven can still chat but cannot perform any actions

**Safety Constraints:**
- File operations limited to configured directories (e.g., `Pc/`, `Projects/`)
- No automatic downloads or external network calls without approval
- Code execution sandboxed with time and memory limits
- All changes are reversible via activity log

### 6. Startup Flow
1. `main.py` starts
2. Loads config, ensures directories
3. Loads Phi-3 model via `ChatRepository`
4. Initializes voice engines (TTS + STT) — graceful fallback if models missing
5. Initializes agent system with approved tools
6. Starts FastAPI + Uvicorn on `127.0.0.1:8000`
7. Opens browser to `http://127.0.0.1:8000`

## Data Flow
```
User speaks → Browser mic → WebSocket → Vosk STT → Text
Text → ChatRepository (Phi-3) → Reply text
Reply → Kokoro TTS → Audio → WebSocket → Browser speaker
Reply → MemoryEngine → storage.json
```

## Dependencies to Add
- `kokoro-onnx` + `soundfile` — Kokoro TTS engine
- `vosk` — Speech recognition
- `pyaudio` — Microphone capture (needs pre-built wheel on Windows)
- `websockets` — Already included with FastAPI


# Testing

## Approach
After each stage, verify that the app starts and the new functionality works. Test via the web interface.

## Key Scenarios
1. **Startup**: App loads, model initializes, browser opens to dashboard
2. **Chat**: User types a message, receives a reply from Haven
3. **Voice**: User clicks mic, speaks, Haven transcribes and replies with voice
4. **Games**: User types "/trivia", plays a round of trivia
5. **Memory**: Haven remembers facts across sessions

## Edge Cases
- Model file missing → show error in dashboard, don't crash
- Voice models not downloaded yet → disable voice buttons, show message
- Microphone not available → show error, fallback to text
- No internet → all features work offline

## Test Changes
- Manual testing via browser for each feature
- No automated tests initially — focus on getting the foundation working


# Delivery Steps

### ✓ Step 1: Reorganize project structure and fix startup
Move scattered files into a clean structure and make startup reliable
- Move `chat_repository.py` to `Pc/chat/repository.py`
- Fix `model_loader/loader.py` hardcoded path (`F:\Haven\Model`) to use relative paths
- Update `main.py` to use the new structure
- Ensure all imports work with the reorganized layout
- Make startup graceful: if model fails to load, show error but don't crash
- Update `requirements.txt` with new dependencies: `kokoro-onnx`, `soundfile`, `vosk`, `pyaudio`

### ✓ Step 2: Build the FastAPI backend with WebSocket support
Enhance the server to serve the web frontend and handle real-time chat
- Update `server/api.py` to serve static files from `web/` directory
- Add `server/websocket.py` with WebSocket endpoints for real-time chat
- Create `/ws/chat` WebSocket endpoint for bidirectional messaging
- Create `/api/voice/tts` endpoint: text → audio (Kokoro TTS)
- Create `/api/voice/stt` endpoint: audio → text (Vosk STT)
- Create `/api/game/play` endpoint: handle game commands
- Keep existing `/api/message` and `/api/status` for compatibility

### ✓ Step 3: Implement voice system (TTS + STT)
Add offline voice capabilities with Kokoro TTS and Vosk STT
- Create `voice/tts.py`: wrap Kokoro TTS, generate audio from text, return WAV bytes
- Create `voice/stt.py`: wrap Vosk, capture microphone input, return transcribed text
- Download Kokoro model files to `Model/kokoro/` (kokoro-v1.0.onnx + voices-v1.0.bin, ~330MB)
- Download Vosk English model to `Model/vosk-model/` (~90MB)
- Add voice initialization to `main.py` with graceful fallback if models missing
- Configure Kokoro with a sweet female voice (`af_heart` or similar)

### ✓ Step 4: Create the JARVIS-style web dashboard
Build the HTML/CSS/JS frontend with a command-center aesthetic
- Create `web/index.html`: dashboard layout with avatar, chat, system info, voice controls
- Create `web/style.css`: dark theme with blue accents, JARVIS-style panels
- Create `web/app.js`: WebSocket connection, chat logic, voice recording, audio playback
- Left panel: Haven's avatar with online/offline status indicator
- Center: Chat area with message bubbles (user right, Haven left)
- Right panel: System info (CPU, RAM, model status, memory stats)
- Bottom: Text input field + mic button + speaker toggle button
- Auto-scroll chat, typing indicators, and connection status

### ✓ Step 5: Integrate voice into the application
Wire voice engines into the running application — backend and frontend
- Initialize TTS and STT in `main.py` with graceful fallback if models missing
- Add voice API endpoints: `/api/voice/tts` (text → audio), `/api/voice/stt` (audio → text), `/api/voice/voices` (list voices)
- Update WebSocket chat to include base64-encoded Kokoro audio with every reply
- Update `/api/status` to report TTS/STT loaded state and current voice
- Update STT wrapper to handle browser-recorded audio (WebM) via ffmpeg conversion
- Update web frontend: play Kokoro audio from WebSocket, send recorded audio to server for Vosk STT
- Add voice status indicators (TTS/STT) to dashboard right panel
- Auto-enable speaker when TTS loads, enable mic when STT loads
- Fallback to browser speech APIs if server-side voice is unavailable

###   Step 6: Implement game system
Add text-based games that Haven can play with the user
- Create `games/manager.py`: detect game commands (`/trivia`, `/hangman`, `/20questions`, `/story`), route to games
- Create `games/trivia.py`: trivia questions with categories and scoring
- Create `games/word_games.py`: Hangman and Word Chain games
- Create `games/storytelling.py`: collaborative story building with AI
- Integrate games into the chat flow: user types `/trivia` to start
- Show game state in chat bubbles with special styling
- Add a game overlay in the web frontend for visual games (like Hangman)

###   Step 7: Implement the agent system
Add the approval-based agent that lets Haven design code and perform safe actions
- Create `agent/manager.py`: interpret user requests, determine which tool to use, and initiate approval workflow
- Create `agent/tools/file_tool.py`: read, create, and modify files within allowed directories
- Create `agent/tools/code_tool.py`: generate code with proper formatting and syntax highlighting
- Create `agent/tools/exec_tool.py`: execute code in a sandboxed environment with time/memory limits
- Create `agent/approval.py`: manage approval requests, store pending actions, handle accept/deny
- Create `agent/activity_log.py`: log all agent actions with timestamps, store in `logs/agent_activity.json`
- Add API endpoints: `/api/agent/request` (submit action for approval), `/api/agent/approve` (confirm action), `/api/agent/deny` (reject action), `/api/agent/log` (view activity log)
- Add WebSocket events for real-time approval notifications
- Implement emergency kill switch in config and API (`/api/agent/disable`)
- Add agent UI to web frontend: approval cards, code preview, activity timeline, kill switch toggle
- Integrate agent with chat: when user asks Haven to create code or modify files, trigger approval workflow
- Test all agent tools with various scenarios: file creation, code generation, safe execution

###   Step 8: Integrate everything and polish
Connect all components, test the full flow, and polish the experience
- Wire up `main.py` to initialize all systems: model, memory, voice, games, agent, server
- Auto-open browser to `http://127.0.0.1:8000` on startup
- Test full voice conversation: speak → transcribe → AI reply → speak reply
- Test all games via chat commands
- Test memory persistence across sessions
- Test agent workflow: request action → approval → execution → activity log
- Add system info endpoint (`/api/system`) for CPU/RAM display
- Polish the dashboard: animations, loading states, error messages
- Update `HAVEN_PLAN.md` with new roadmap status