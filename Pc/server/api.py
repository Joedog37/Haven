# file: server/api.py
# Haven FastAPI backend - serves the web frontend and handles API requests

import os
import psutil
import base64
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import uvicorn
import json

# These will be injected from main.py
MODEL = None
MEMORY = None
TTS = None
STT = None
WEB_SEARCH = None
AGENT_TOOLS = None
GAME_ENGINE = None
DND_GAME = None
OREGON_GAME = None

app = FastAPI(title="Haven JARVIS Dashboard")

# -----------------------------
# STATIC FILES - Web Frontend
# -----------------------------
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gui", "assets")

if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Serve avatar from assets directory
if os.path.exists(ASSETS_DIR):
    app.mount("/static/avatar", StaticFiles(directory=os.path.join(ASSETS_DIR, "avatar")), name="avatar")


def configure_services(model, memory, tts=None, stt=None, web_search=None, agent_tools=None, game_engine=None, dnd_game=None, oregon_game=None):
    """Connect local services before the server accepts requests."""
    global MODEL, MEMORY, TTS, STT, WEB_SEARCH, AGENT_TOOLS, GAME_ENGINE, DND_GAME, OREGON_GAME
    MODEL = model
    MEMORY = memory
    TTS = tts
    STT = stt
    WEB_SEARCH = web_search
    AGENT_TOOLS = agent_tools
    GAME_ENGINE = game_engine
    DND_GAME = dnd_game
    OREGON_GAME = oregon_game

    # Log game engine status for troubleshooting
    if DND_GAME is not None:
        print("[Haven] DnD game engine registered — /api/game/dnd/* endpoints active")
    else:
        print("[Haven] WARNING: DnD game engine NOT loaded — /api/game/dnd/* endpoints will return 503")
    if OREGON_GAME is not None:
        print("[Haven] Oregon Trail game engine registered — /api/game/oregon/* endpoints active")
    else:
        print("[Haven] WARNING: Oregon Trail game engine NOT loaded — /api/game/oregon/* endpoints will return 503")


# -----------------------------
# Request / Response Models
# -----------------------------
class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    reply: str
    audio_url: str | None = None


class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0


class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5


class GameVoiceRequest(BaseModel):
    """Request to read game text aloud via TTS."""
    text: str


class GameVoiceResponse(BaseModel):
    """Response with TTS audio for game text."""
    audio_url: str | None = None
    available: bool = False


class UserProfileRequest(BaseModel):
    name: str


# -----------------------------
# WEB FRONTEND ROUTES
# -----------------------------
@app.get("/")
def index():
    """Serve the main dashboard page."""
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Web frontend not found. Create Pc/web/index.html"}


# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.post("/api/message", response_model=MessageResponse)
def message_endpoint(data: MessageRequest):
    """
    Main endpoint for chat communication.
    """
    if MODEL is None or MEMORY is None:
        raise HTTPException(status_code=503, detail="Haven is still starting.")

    user_text = data.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")

    # Process through memory engine
    processed = MEMORY.process(user_text)

    # Generate model reply
    reply = MODEL.send_message(processed)

    # Save to memory
    MEMORY.add_history(user_text, reply)

    # Return text immediately — no wait for TTS
    return MessageResponse(reply=reply, audio_url=None)


@app.get("/api/status")
def status():
    """Status check for the dashboard."""
    return {
        "status": "online" if MODEL is not None and MEMORY is not None else "starting",
        "network_mode": "local_only",
        "model_loaded": MODEL is not None,
        "memory_loaded": MEMORY is not None,
        "tts_loaded": TTS is not None and TTS.loaded if TTS else False,
        "stt_loaded": STT is not None and STT.loaded if STT else False,
        "tts_voice": TTS.voice_name if TTS and TTS.loaded else None,
        "web_search_available": WEB_SEARCH is not None and WEB_SEARCH.available if WEB_SEARCH else False,
        "agent_tools_loaded": AGENT_TOOLS is not None,
        "game_engine_loaded": GAME_ENGINE is not None,
    }


# -----------------------------
# AGENT TOOLS ENDPOINTS
# -----------------------------
@app.get("/api/tools/status")
def tools_status():
    """Return status of all agent tools."""
    if AGENT_TOOLS is None:
        raise HTTPException(status_code=503, detail="Agent tools not loaded.")
    return AGENT_TOOLS.get_status()


@app.get("/api/tools/clock")
def clock_status():
    """Return clock/alarm/timer status."""
    if AGENT_TOOLS is None:
        raise HTTPException(status_code=503, detail="Agent tools not loaded.")
    return AGENT_TOOLS.clock.get_status()


@app.get("/api/tools/games")
def games_status():
    """Return game engine status."""
    if GAME_ENGINE is None:
        raise HTTPException(status_code=503, detail="Game engine not loaded.")
    return GAME_ENGINE.get_status()


@app.post("/api/tools/weather")
def get_weather(data: MessageRequest):
    """Get weather for a location."""
    if AGENT_TOOLS is None:
        raise HTTPException(status_code=503, detail="Agent tools not loaded.")
    location = data.text.strip()
    result = AGENT_TOOLS.weather.get_weather(location if location else None)
    return {"weather": result}


@app.post("/api/tools/time")
def get_time():
    """Get current time."""
    if AGENT_TOOLS is None:
        raise HTTPException(status_code=503, detail="Agent tools not loaded.")
    return {"time": AGENT_TOOLS.clock.get_current_time()}


@app.post("/api/tools/date")
def get_date():
    """Get current date."""
    if AGENT_TOOLS is None:
        raise HTTPException(status_code=503, detail="Agent tools not loaded.")
    return {"date": AGENT_TOOLS.clock.get_current_date()}


@app.get("/api/system")
def system_info():
    """System info for the dashboard right panel."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "disk_free_gb": round(disk.free / (1024**3), 2),
    }


# -----------------------------
# GAMES HEALTH CHECK
# -----------------------------
@app.get("/api/games/status")
def games_status():
    """Return the status of all game engines for troubleshooting."""
    return {
        "dnd": DND_GAME is not None,
        "oregon": OREGON_GAME is not None,
        "game_engine": GAME_ENGINE is not None,
    }


# -----------------------------
# DND GAME ENDPOINTS
# -----------------------------
@app.get("/api/game/dnd/status")
def dnd_status():
    """Return DnD game status."""
    if DND_GAME is None:
        raise HTTPException(status_code=503, detail="DnD game not loaded.")
    return DND_GAME.get_status()


@app.post("/api/game/dnd/new")
def dnd_new_game(data: MessageRequest):
    """Start a new DnD game."""
    if DND_GAME is None:
        raise HTTPException(status_code=503, detail="DnD game not loaded.")
    
    # Parse character info from text
    parts = data.text.split("|")
    player_name = parts[0].strip() if len(parts) > 0 else "Hero"
    char_class = parts[1].strip() if len(parts) > 1 else "warrior"
    char_race = parts[2].strip() if len(parts) > 2 else "human"
    
    return DND_GAME.new_game(player_name, char_class, char_race)


@app.post("/api/game/dnd/choice")
def dnd_choice(data: MessageRequest):
    """Make a choice in DnD game."""
    if DND_GAME is None:
        raise HTTPException(status_code=503, detail="DnD game not loaded.")
    
    # Parse choice index and custom input
    parts = data.text.split("|")
    try:
        choice_index = int(parts[0].strip())
    except (ValueError, IndexError):
        choice_index = -1
    custom_input = parts[1].strip() if len(parts) > 1 else None
    
    return DND_GAME.make_choice(choice_index, custom_input)


@app.post("/api/game/dnd/action")
def dnd_action(data: MessageRequest):
    """Perform an action in DnD game."""
    if DND_GAME is None:
        raise HTTPException(status_code=503, detail="DnD game not loaded.")
    
    action = data.text.strip().lower()
    if action == "attack":
        return DND_GAME.attack()
    elif action == "rest":
        return DND_GAME.rest()
    elif action == "save":
        return DND_GAME.save_game()
    elif action == "load":
        return DND_GAME.load_game()
    else:
        # Try to use item
        if action.startswith("use "):
            item_name = action[4:]
            return DND_GAME.use_item(item_name)
        return {"type": "error", "message": f"Unknown action: {action}"}


@app.post("/api/game/dnd/load")
def dnd_load():
    """Load a saved DnD game."""
    if DND_GAME is None:
        raise HTTPException(status_code=503, detail="DnD game not loaded.")
    return DND_GAME.load_game()


# -----------------------------
# OREGON TRAIL ENDPOINTS
# -----------------------------
@app.get("/api/game/oregon/status")
def oregon_status():
    """Return Oregon Trail game status."""
    if OREGON_GAME is None:
        raise HTTPException(status_code=503, detail="Oregon Trail game not loaded.")
    return OREGON_GAME.get_status()


@app.post("/api/game/oregon/new")
def oregon_new_game(data: MessageRequest):
    """Start a new Oregon Trail game."""
    if OREGON_GAME is None:
        raise HTTPException(status_code=503, detail="Oregon Trail game not loaded.")
    
    # Parse player info from text
    parts = data.text.split("|")
    player_name = parts[0].strip() if len(parts) > 0 else "Pioneer"
    profession = parts[1].strip() if len(parts) > 1 else "farmer"
    
    return OREGON_GAME.new_game(player_name, profession)


@app.post("/api/game/oregon/choice")
def oregon_choice(data: MessageRequest):
    """Make a choice in Oregon Trail game."""
    if OREGON_GAME is None:
        raise HTTPException(status_code=503, detail="Oregon Trail game not loaded.")
    
    # Parse choice index and custom input
    parts = data.text.split("|")
    try:
        choice_index = int(parts[0].strip())
    except (ValueError, IndexError):
        choice_index = -1
    custom_input = parts[1].strip() if len(parts) > 1 else None
    
    return OREGON_GAME.make_choice(choice_index, custom_input)


@app.post("/api/game/oregon/action")
def oregon_action(data: MessageRequest):
    """Perform an action in Oregon Trail game."""
    if OREGON_GAME is None:
        raise HTTPException(status_code=503, detail="Oregon Trail game not loaded.")
    
    action = data.text.strip().lower()
    if action == "travel":
        return OREGON_GAME.travel()
    elif action == "rest":
        return OREGON_GAME.rest()
    elif action == "hunt":
        return OREGON_GAME.hunt()
    elif action == "trade":
        return OREGON_GAME.trade()
    elif action == "save":
        return OREGON_GAME.save_game()
    elif action == "load":
        return OREGON_GAME.load_game()
    elif action.startswith("buy "):
        item = action[4:]
        return OREGON_GAME.buy_item(item)
    return {"type": "error", "message": f"Unknown action: {action}"}


@app.post("/api/game/oregon/load")
def oregon_load():
    """Load a saved Oregon Trail game."""
    if OREGON_GAME is None:
        raise HTTPException(status_code=503, detail="Oregon Trail game not loaded.")
    return OREGON_GAME.load_game()


# -----------------------------
# WEBSOCKET - Real-time Chat
# -----------------------------
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Real-time chat via WebSocket with optional TTS audio."""
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Parse JSON message
            try:
                message = json.loads(data)
                user_text = message.get("text", "").strip()
            except json.JSONDecodeError:
                user_text = data.strip()

            if not user_text:
                continue

            if MODEL is None or MEMORY is None:
                await websocket.send_json({
                    "type": "error",
                    "text": "Haven is still starting. Please wait..."
                })
                continue

            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "text": ""
            })

            # Process through memory engine
            processed = MEMORY.process(user_text)

            # Generate model reply
            reply = MODEL.send_message(processed)

            # Save to memory
            MEMORY.add_history(user_text, reply)

            # Generate TTS audio synchronously and send with the message
            audio_b64 = None
            if TTS and TTS.loaded:
                try:
                    audio_bytes = TTS.generate(reply)
                    if audio_bytes:
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        print(f"[Haven] TTS generated {len(audio_bytes)} bytes")
                except Exception as e:
                    print(f"[Haven] TTS error: {e}")

            # Send reply with audio included
            await websocket.send_json({
                "type": "message",
                "role": "haven",
                "text": reply,
                "audio": audio_b64
            })

    except WebSocketDisconnect:
        print("[Haven] Client disconnected from chat")
    except Exception as e:
        print(f"[Haven] WebSocket error: {e}")


# -----------------------------
# VOICE ENDPOINTS
# -----------------------------
@app.post("/api/voice/tts")
def voice_tts(data: TTSRequest):
    """Convert text to speech using Kokoro TTS."""
    if TTS is None or not TTS.loaded:
        raise HTTPException(status_code=503, detail="TTS engine not loaded.")

    # Change voice if requested
    if data.voice != "af_heart":
        TTS.set_voice(data.voice)

    audio_bytes = TTS.generate(data.text, speed=data.speed)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate audio.")

    return Response(content=audio_bytes, media_type="audio/wav")


@app.post("/api/voice/stt")
async def voice_stt(file: UploadFile = File(...)):
    """Convert speech audio to text using Vosk STT."""
    if STT is None or not STT.loaded:
        raise HTTPException(status_code=503, detail="STT engine not loaded.")

    try:
        audio_data = await file.read()
        
        # Recognize speech from audio bytes
        text = STT.recognize(audio_data)
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")


@app.get("/api/voice/voices")
def voice_list():
    """List available TTS voices."""
    if TTS is None or not TTS.loaded:
        raise HTTPException(status_code=503, detail="TTS engine not loaded.")
    return {"voices": TTS.get_available_voices(), "current": TTS.voice_name}


# -----------------------------
# MEMORY ENDPOINTS
# -----------------------------
@app.get("/api/memory/stats")
def memory_stats():
    """Return memory statistics for the dashboard."""
    if MEMORY is None:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    return MEMORY.get_stats()


@app.get("/api/memory/context")
def memory_context():
    """Return the memory context summary for the dashboard."""
    if MEMORY is None:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    summary = MEMORY.get_context_summary()
    return {"summary": summary}


# -----------------------------
# USER PROFILE ENDPOINTS
# -----------------------------
@app.get("/api/user/profile")
def user_profile():
    """Return the current user profile information."""
    if MEMORY is None:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    
    # Detect current system user
    try:
        system_user = os.getlogin()
    except Exception:
        system_user = None
    
    return {
        "name": MEMORY.data["user"]["name"],
        "profile_id": MEMORY.profile_id,
        "system_user": system_user,
    }


@app.post("/api/user/profile")
def set_user_profile(data: UserProfileRequest):
    """Set the user's display name that Haven uses."""
    if MEMORY is None:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    
    MEMORY.data["user"]["name"] = name
    MEMORY._save()
    print(f"[Haven] User name set to: {name}")
    
    return {"name": name, "message": f"Haven will now address you as {name}"}


# -----------------------------
# GAME VOICE ENDPOINT
# -----------------------------
@app.post("/api/game/voice")
def game_voice_endpoint(data: GameVoiceRequest):
    """Read game text aloud using TTS engine."""
    text = data.text.strip()
    if not text:
        return GameVoiceResponse(available=TTS is not None and TTS.loaded if TTS else False)

    if TTS is None or not TTS.loaded:
        return GameVoiceResponse(available=False)

    try:
        audio_bytes = TTS.generate(text)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            return GameVoiceResponse(audio_url=audio_b64, available=True)
    except Exception as e:
        print(f"[Haven] Game TTS error: {e}")

    return GameVoiceResponse(available=True)


# -----------------------------
# WEB SEARCH ENDPOINTS
# -----------------------------
@app.post("/api/web/search")
def web_search_endpoint(data: WebSearchRequest):
    """Search the web for information."""
    if WEB_SEARCH is None or not WEB_SEARCH.available:
        raise HTTPException(status_code=503, detail="Web search not available.")

    results = WEB_SEARCH.search(data.query, max_results=data.max_results)
    return {"query": data.query, "results": results}


@app.get("/api/web/search/status")
def web_search_status():
    """Check if web search is available."""
    return {
        "available": WEB_SEARCH is not None and WEB_SEARCH.available if WEB_SEARCH else False,
    }


# -----------------------------
# START SERVER
# -----------------------------
def start_api_server():
    """
    Run FastAPI on all network interfaces so it can be reached from other devices
    on the local network or via Tailscale.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)
