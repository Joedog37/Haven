# File: main.py
# Haven - JARVIS-style web dashboard entry point
# Starts FastAPI + Uvicorn, loads the AI model, and opens the browser.

import sys
import os
import signal
import importlib.util
import threading
import webbrowser

# Stable paths, regardless of the folder from which Haven is launched.
APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(APP_FOLDER)

# Support environment variable overrides for Docker / TrueNAS deployments.
# When running in a container, these point to mounted volumes.
MODEL_FOLDER = os.environ.get("HAVEN_MODEL_PATH") or os.path.join(PROJECT_FOLDER, "Model")
SAVE_FOLDER = os.environ.get("HAVEN_SAVE_PATH") or os.path.join(APP_FOLDER, "saves")
MEMORY_FOLDER = os.environ.get("HAVEN_MEMORY_PATH") or os.path.join(APP_FOLDER, "memory")

# ---------------------------------------------------------
# GLOBALS
# ---------------------------------------------------------
chat_repo = None
memory_engine = None
tts_engine = None
stt_engine = None
web_search = None
agent_tools = None
game_engine = None
dnd_game = None
oregon_game = None

# ---------------------------------------------------------
# CTRL+C / CLEAN EXIT
# ---------------------------------------------------------
def handle_exit(signum, frame):
    print("\n[Haven] Shutting down cleanly...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


# ---------------------------------------------------------
# DEPENDENCY CHECK (never downloads or installs)
# ---------------------------------------------------------
def ensure_packages():
    """Report missing packages without downloading or changing the system."""
    package_modules = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "aiohttp": "aiohttp",
        "orjson": "orjson",
        "Pillow": "PIL",
        "cryptography": "cryptography",
        "psutil": "psutil",
        "kokoro-onnx": "kokoro_onnx",
        "soundfile": "soundfile",
        "vosk": "vosk",
    }
    missing = [
        package for package, module in package_modules.items()
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        print("[Haven] Missing required packages: " + ", ".join(missing))
        print("[Haven] Install them manually:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
    return missing


# ---------------------------------------------------------
# AUTO-CREATE FOLDERS
# ---------------------------------------------------------
def ensure_folders():
    """Ensure all required directories exist."""
    required_dirs = [
        MODEL_FOLDER,
        MEMORY_FOLDER,
        SAVE_FOLDER,
        os.path.join(APP_FOLDER, "logs"),
        os.path.join(APP_FOLDER, "web"),
    ]

    for d in required_dirs:
        if not os.path.exists(d):
            print(f"[Haven] Creating missing folder: {d}")
            os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------------
def load_model(memory=None, agent_tools=None, game_engine=None, web_search=None):
    """Load the AI model via Ollama with graceful fallback."""
    from chat.repository import ChatRepository

    try:
        repo = ChatRepository(
            memory_engine=memory, 
            web_search=web_search,
            agent_tools=agent_tools,
            game_engine=game_engine,
        )
        print("[Haven] Phi-3 model loaded successfully.")
        return repo
    except Exception as e:
        print(f"[Haven] Failed to load Phi-3 model: {e}")
        return None


# ---------------------------------------------------------
# DETECT USER
# ---------------------------------------------------------
def detect_user() -> str:
    """Detect the current user by Windows username."""
    try:
        username = os.getlogin()
        print(f"[Haven] Detected user: {username}")
        return username
    except Exception as e:
        print(f"[Haven] Could not detect user: {e}")
        return None


# ---------------------------------------------------------
# LOAD MEMORY
# ---------------------------------------------------------
def load_memory(profile_id=None):
    """Load the memory engine with optional user profile."""
    from memory.engine import MemoryEngine

    memory_path = os.path.join(MEMORY_FOLDER, "storage.json")
    memory = MemoryEngine(path=memory_path, profile_id=profile_id)
    print(f"[Haven] Memory loaded from: {memory_path}")
    if profile_id:
        print(f"[Haven] User profile: {profile_id}")
    return memory


# ---------------------------------------------------------
# LOAD WEB SEARCH
# ---------------------------------------------------------
def load_web_search():
    """Load the web search engine with graceful fallback."""
    global web_search

    try:
        from web_search.search import WebSearch
        web_search = WebSearch()
        if web_search.available:
            print("[Haven] Web search ready — Haven can look up information online.")
        else:
            print("[Haven] WARNING: Web search not available — duckduckgo-search not installed.")
    except Exception as e:
        print(f"[Haven] WARNING: Web search failed to load: {e}")
        web_search = None


# ---------------------------------------------------------
# LOAD AGENT TOOLS
# ---------------------------------------------------------
def load_agent_tools():
    """Load the agent tools system."""
    global agent_tools
    try:
        from agent.tools.manager import AgentTools
        agent_tools = AgentTools()
        print("[Haven] Agent tools loaded — clock, device, files, network, weather.")
    except Exception as e:
        print(f"[Haven] WARNING: Agent tools failed to load: {e}")
        agent_tools = None


# ---------------------------------------------------------
# LOAD GAMES
# ---------------------------------------------------------
def load_games():
    """Load the game engines."""
    global game_engine, dnd_game, oregon_game
    
    # Load basic game engine
    try:
        from games.engine import GameEngine
        game_engine = GameEngine()
        print("[Haven] Game engine loaded — trivia, guessing, wordle, RPS, tic-tac-toe, 20 questions.")
    except Exception as e:
        print(f"[Haven] WARNING: Game engine failed to load: {e}")
        game_engine = None
    
    # Load DnD game
    try:
        from games.dnd_game import DnDGame
        dnd_game = DnDGame(save_dir=SAVE_FOLDER)
        print("[Haven] DnD game engine loaded — AI-generated adventures with persistent saves.")
    except Exception as e:
        print(f"[Haven] WARNING: DnD game failed to load: {e}")
        dnd_game = None
    
    # Load Oregon Trail game
    try:
        from games.oregon_trail import OregonTrailGame
        oregon_game = OregonTrailGame(save_dir=SAVE_FOLDER)
        print("[Haven] Oregon Trail game engine loaded — AI-generated journey with persistent saves.")
    except Exception as e:
        print(f"[Haven] WARNING: Oregon Trail game failed to load: {e}")
        oregon_game = None


# ---------------------------------------------------------
# LOAD VOICE (TTS + STT)
# ---------------------------------------------------------
def load_voice():
    """Load voice engines with graceful fallback."""
    global tts_engine, stt_engine

    # Resolve model paths
    kokoro_model = os.path.join(MODEL_FOLDER, "kokoro", "kokoro-v1.0.onnx")
    kokoro_voices = os.path.join(MODEL_FOLDER, "kokoro", "voices-v1.0.bin")
    vosk_model = os.path.join(MODEL_FOLDER, "vosk-model", "vosk-model-en-us-0.21")

    # Load TTS (Kokoro)
    try:
        from voice.tts import TTS
        if os.path.exists(kokoro_model) and os.path.exists(kokoro_voices):
            tts_engine = TTS(model_path=kokoro_model, voices_path=kokoro_voices)
        else:
            print(f"[Haven] WARNING: Kokoro models not found at {kokoro_model}")
            tts_engine = TTS()
        if tts_engine.loaded:
            voices = tts_engine.get_available_voices()
            print(f"[Haven] TTS ready — {len(voices)} voices available (default: {tts_engine.voice_name})")
        else:
            print("[Haven] WARNING: TTS not loaded — Kokoro models missing or failed.")
    except Exception as e:
        print(f"[Haven] WARNING: TTS failed to load: {e}")
        tts_engine = None

    # Load STT (Vosk)
    try:
        from voice.stt import STT
        if os.path.exists(vosk_model):
            stt_engine = STT(model_path=vosk_model)
        else:
            print(f"[Haven] WARNING: Vosk model not found at {vosk_model}")
            stt_engine = STT()
        if stt_engine.loaded:
            print("[Haven] STT ready — Vosk model loaded.")
        else:
            print("[Haven] WARNING: STT not loaded — Vosk model missing or failed.")
    except Exception as e:
        print(f"[Haven] WARNING: STT failed to load: {e}")
        stt_engine = None


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------
def start_server():
    """Start the FastAPI server in a background thread."""
    from server.api import configure_services, start_api_server

    configure_services(chat_repo, memory_engine, tts_engine, stt_engine, web_search, agent_tools, game_engine, dnd_game, oregon_game)
    print("[Haven] Starting API server on 0.0.0.0:8000 (accessible from network)...")
    start_api_server()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    global chat_repo, memory_engine, tts_engine, stt_engine

    print("=" * 50)
    print("[Haven] Starting JARVIS Web Dashboard...")
    print("=" * 50)

    # Check dependencies
    missing_packages = ensure_packages()
    if missing_packages:
        print("[Haven] Cannot start — missing packages. Please install them first.")
        sys.exit(1)

    # Ensure directories
    ensure_folders()

    # Detect current user
    print("[Haven] Detecting user...")
    current_user = detect_user()

    # Load memory first so we can pass it to the model
    print("[Haven] Loading memory...")
    memory_engine = load_memory(profile_id=current_user)

    # Load web search before model so it can be passed to the chat repo
    print("[Haven] Loading web search...")
    load_web_search()

    # Load agent tools and games before model
    print("[Haven] Loading agent tools...")
    load_agent_tools()
    
    print("[Haven] Loading games...")
    load_games()

    # Load model with memory, web search, agent tools, and games
    print("[Haven] Loading AI model...")
    chat_repo = load_model(memory=memory_engine, agent_tools=agent_tools, game_engine=game_engine, web_search=web_search)
    if chat_repo is None:
        print("[Haven] WARNING: Model failed to load. Chat will not work.")

    # Load voice
    print("[Haven] Loading voice engines...")
    load_voice()

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Open browser
    print("[Haven] Opening browser to dashboard...")
    webbrowser.open("http://localhost:8000")

    # Get local network IP for display
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"[Haven] Dashboard is running on your local network at http://{local_ip}:8000")
        print("[Haven] Other devices on your network can access it using that address.")
    except Exception:
        print("[Haven] Dashboard is running at http://localhost:8000")
    print("[Haven] Press Ctrl+C to stop.\n")

    # Keep the main thread alive
    try:
        while True:
            signal.pause() if hasattr(signal, 'pause') else threading.Event().wait(1)
    except KeyboardInterrupt:
        handle_exit(None, None)


if __name__ == "__main__":
    main()
