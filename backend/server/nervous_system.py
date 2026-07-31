"""
ZARA Nervous System — FastAPI WebSocket Server
===============================================
The communication backbone between ZARA's AI brain and any frontend client.

Architecture:
    Brain (RTX 4050) ─── nervous_system.py ─── WebSocket ─── Frontend (iGPU / browser)

Endpoints:
    WS  /ws/brain          Bi-directional brain ↔ UI channel
    GET /status            Health-check / liveness probe (JSON)
    GET /                  Serves frontend/index.html
    GET /frontend/{path}   Serves the Three.js + VRM web UI

Message Protocol:
    Client → Server  {"type": "text",      "content": "hey zara"}
                     {"type": "audio_b64", "content": "<base64 wav>"}
                     {"type": "ping"}

    Server → Client  {"type": "ready",     "version": "4.0"}
                     {"type": "response",  "text": "...", "emotion": "...",
                      "speaking": true,    "audio_b64": "<base64 wav or null>"}
                     {"type": "status",    "mood": "happy", "uptime": 120}
                     {"type": "error",     "message": "..."}
                     {"type": "pong"}
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger("ZARA_NERVOUS_SYSTEM")

# ─── FastAPI & WebSocket ───────────────────────────────────────────────────────
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as e:
    raise ImportError(
        f"FastAPI not installed: {e}\n"
        "Run: pip install fastapi uvicorn[standard]"
    ) from e

# ─── Path setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_ROOT = _HERE.parent
_FRONTEND_DIR = _ROOT / "frontend"
_ASSETS_DIR   = _ROOT / "assets"

# ─── Thread pool for blocking ZARA brain calls ────────────────────────────────
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="zara_brain")

# ─── Startup time ─────────────────────────────────────────────────────────────
_start_time = time.time()


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTION MANAGER
# Holds all active WebSocket connections and broadcasts messages to all of them.
# ══════════════════════════════════════════════════════════════════════════════
class ConnectionManager:
    """Thread-safe WebSocket connection pool with broadcast support."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info(f"[WS] Client connected. Total: {len(self._connections)}")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)
        logger.info(f"[WS] Client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, payload: dict):
        """Broadcast a JSON payload to all connected clients (fire-and-forget per client)."""
        async with self._lock:
            targets = set(self._connections)

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        # Prune dead connections
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    async def send_to(self, ws: WebSocket, payload: dict):
        """Send a JSON payload to a single client."""
        try:
            await ws.send_json(payload)
        except Exception as e:
            logger.warning(f"[WS] Failed to send to client: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO HELPER — pyttsx3 → base64 WAV
# The TTS engine writes to a temp file, we read it back and base64-encode it.
# ══════════════════════════════════════════════════════════════════════════════
def _text_to_audio_b64(text: str) -> Optional[str]:
    """
    Convert text to audio using pyttsx3, return as base64 WAV string.
    Returns None if TTS is unavailable or the text is empty.
    """
    if not text or not text.strip():
        return None
    try:
        import pyttsx3
        import re

        # Clean think-tags and action markers from the text
        clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        clean = re.sub(r"\*[^*]+\*", "", clean).strip()
        if not clean:
            return None

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)  # Female voice
        engine.setProperty("rate", 165)
        engine.save_to_file(clean, tmp_path)
        engine.runAndWait()

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(tmp_path)

        if len(audio_bytes) < 44:  # Too small — pyttsx3 may have failed silently
            return None

        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        logger.warning(f"[TTS] Audio generation failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# EMOTION HELPER
# Extract the dominant emotion from ZARA's running soul/neurochemistry systems.
# Handles Enum types that stringify as 'EnumClass.value' → extracts 'value' only.
# ══════════════════════════════════════════════════════════════════════════════
def _clean_emotion_str(raw) -> str:
    """Convert any emotion value to a plain lowercase string."""
    s = str(raw).strip()
    # Handle 'ClassName.value' or 'ClassName.VALUE' patterns from Python Enums
    if '.' in s:
        s = s.rsplit('.', 1)[-1]
    return s.lower().strip() or 'neutral'


def _get_emotion(zara) -> str:
    """Best-effort emotion extraction from whichever system is available."""
    try:
        if zara.neurochemistry and hasattr(zara.neurochemistry, 'get_mood_vector'):
            vec = zara.neurochemistry.get_mood_vector()
            if isinstance(vec, dict) and vec:
                return _clean_emotion_str(max(vec, key=vec.get))
    except Exception:
        pass
    try:
        if zara.soul and hasattr(zara.soul, 'current_mood') and zara.soul.current_mood:
            return _clean_emotion_str(zara.soul.current_mood)
    except Exception:
        pass
    return 'neutral'


def detect_task_type(text: str) -> str:
    text_lower = text.lower()
    
    # Strong signals (exact phrases)
    if any(p in text_lower for p in ["write a function", "python script", "code for me", "debug this", "write code"]):
        return "code"
    if any(p in text_lower for p in ["cpu usage", "ram usage", "system stats", "how hot is my gpu", "show system"]):
        return "system"
    if any(p in text_lower for p in ["what do you see", "look at my screen", "camera on", "identify this", "describe image"]):
        return "vision"
    
    # Weak signals (single words) — require at least 2 match score
    code_words = ["function", "class", "def ", "import ", "bug", "compile", "syntax"]
    system_words = ["cpu", "ram", "memory", "disk", "process", "temperature"]
    vision_words = ["camera", "screen", "describe image", "snapshot"]
    
    code_score = sum(1 for w in code_words if w in text_lower)
    system_score = sum(1 for w in system_words if w in text_lower)
    vision_score = sum(1 for w in vision_words if w in text_lower)
    
    scores = {"code": code_score, "system": system_score, "vision": vision_score}
    best = max(scores, key=scores.get)
    
    if scores[best] >= 2:
        return best
    return "chat"


# ══════════════════════════════════════════════════════════════════════════════
# BRAIN CALL — runs in thread pool so the event loop stays unblocked
# Also triggers TTS on the pre-existing TTSEngine worker (fast, non-blocking)
# ══════════════════════════════════════════════════════════════════════════════
def _call_brain_sync(zara, text: str) -> tuple[str, str]:
    """
    Call ZaraConsciousness.process_input() synchronously.
    Also triggers the existing TTSEngine speaker (fast — already running).
    Returns (reply_text, emotion_string).
    """
    try:
        reply = zara.process_input(text) or "I'm thinking..."
    except Exception as e:
        logger.error(f"[BRAIN] process_input failed: {e}", exc_info=True)
        reply = "Sorry, I encountered an internal error. Please try again."

    emotion = _get_emotion(zara)

    # Trigger the pre-existing (fast) TTS worker thread — no new engine created
    try:
        if zara.voice and hasattr(zara.voice, 'speak_async'):
            zara.voice.speak_async(reply, mood=emotion)
    except Exception as e:
        logger.debug(f"[TTS] speak_async failed: {e}")

    return reply, emotion


# ══════════════════════════════════════════════════════════════════════════════
# APP FACTORY
# Called by main.py after ZaraConsciousness.start() completes.
# ══════════════════════════════════════════════════════════════════════════════
def build_app(zara) -> FastAPI:
    """
    Build and return the FastAPI application wired to the running ZaraConsciousness.

    Args:
        zara: A fully started ZaraConsciousness instance.

    Returns:
        FastAPI application ready to be passed to uvicorn.
    """
    app = FastAPI(
        title="ZARA Nervous System",
        description="WebSocket bridge between ZARA's brain and the holographic UI",
        version="4.0",
        docs_url=None,   # Disable Swagger in production
        redoc_url=None,
    )

    # Allow CORS for dev (e.g. Vite dev server)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()

    # ── Static Files (frontend assets, VRM model) ─────────────────────────────
    if _FRONTEND_DIR.exists():
        app.mount("/frontend", StaticFiles(directory=str(_FRONTEND_DIR)), name="frontend")
        logger.info(f"[STATIC] Serving frontend from {_FRONTEND_DIR}")

    if _ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")
        logger.info(f"[STATIC] Serving assets from {_ASSETS_DIR}")

    # ── HTTP Routes ───────────────────────────────────────────────────────────

    @app.get("/status")
    async def status():
        """Liveness probe — returns ZARA system health."""
        uptime = int(time.time() - _start_time)
        health = {}
        try:
            if hasattr(zara, "degrader") and zara.degrader:
                health = zara.degrader.get_health_status()
        except Exception:
            pass

        return JSONResponse({
            "status": "ok",
            "version": "4.0",
            "uptime_seconds": uptime,
            "zara_running": getattr(zara, "is_running", False),
            "health": health,
            "ws_clients": len(manager._connections),
        })

    @app.get("/")
    async def index():
        """Serve the holographic VRM frontend."""
        index_path = _FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        # Fallback splash if frontend not built yet
        return JSONResponse(
            {"message": "ZARA Brain online ✓", "ws": "ws://127.0.0.1:8000/ws/brain"},
            status_code=200,
        )

    # ── WebSocket Endpoint ────────────────────────────────────────────────────

    @app.websocket("/ws/brain")
    async def brain_ws(ws: WebSocket):
        """
        Main bi-directional WebSocket channel.

        Client → Server:  {"type": "text",      "content": "..."}
                          {"type": "audio_b64", "content": "<wav b64>"}
                          {"type": "ping"}

        Server → Client:  {"type": "ready",     "version": "4.0"}
                          {"type": "response",  "text": "...", "emotion": "...",
                           "speaking": true,    "audio_b64": "...or null"}
                          {"type": "pong"}
                          {"type": "error",     "message": "..."}
        """
        await manager.connect(ws)

        # Send "ready" handshake
        await manager.send_to(ws, {
            "type": "ready",
            "version": "4.0",
            "emotion": _get_emotion(zara),
            "zara_running": getattr(zara, "is_running", False),
        })

        loop = asyncio.get_event_loop()

        try:
            while True:
                # Wait for the next client message
                try:
                    data = await ws.receive_json()
                except Exception:
                    # JSON parse error — send error and keep connection alive
                    await manager.send_to(ws, {"type": "error", "message": "Malformed JSON"})
                    continue

                msg_type = data.get("type", "text")

                # ── Ping/Pong ──────────────────────────────────────────────
                if msg_type == "ping":
                    await manager.send_to(ws, {"type": "pong"})
                    continue

                # ── Text input (typed or transcribed from mic) ─────────────
                if msg_type in ("text", "chat", "audio_b64"):
                    content = data.get("content") or data.get("text", "")
                    content = content.strip()

                    if msg_type == "audio_b64":
                        content = "[User sent voice message — STT bridging coming soon]"

                    if not content:
                        await manager.send_to(ws, {"type": "error", "message": "Empty input"})
                        continue

                    # Detect and broadcast task morph state
                    task_type = detect_task_type(content)
                    await manager.broadcast({
                        "type": "task_detected",
                        "task": task_type
                    })

                    # Run the brain in a thread so we don't block the event loop
                    reply, emotion = await loop.run_in_executor(
                        _executor, _call_brain_sync, zara, content
                    )

                    # Broadcast immediately — no audio wait
                    await manager.broadcast({
                        "type":      "response",
                        "text":      reply,
                        "emotion":   emotion,
                        "speaking":  True,
                        "audio_b64": None,
                    })

                    # Schedule speaking=False proportional to word count
                    word_count = len(reply.split())
                    speak_delay = max(1.5, min(12.0, word_count * 0.35))
                    async def _done_speaking(delay: float, emo: str) -> None:
                        await asyncio.sleep(delay)
                        await manager.broadcast({
                            "type": "response", "text": "", "emotion": emo,
                            "speaking": False, "audio_b64": None,
                        })
                    asyncio.create_task(_done_speaking(speak_delay, emotion))

                else:
                    await manager.send_to(ws, {
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })

        except WebSocketDisconnect:
            logger.info("[WS] Client disconnected normally.")
        except Exception as e:
            logger.error(f"[WS] Unexpected error: {e}", exc_info=True)
        finally:
            await manager.disconnect(ws)

    # ── Startup / Shutdown events ─────────────────────────────────────────────

    @app.on_event("startup")
    async def on_startup():
        logger.info("[SERVER] ✓ ZARA Nervous System started")
        logger.info(f"[SERVER]   Brain: {'running' if getattr(zara, 'is_running', False) else 'offline'}")
        logger.info(f"[SERVER]   Frontend: {_FRONTEND_DIR}")

        async def _stats_loop():
            try:
                import psutil
                while True:
                    await asyncio.sleep(2)
                    if manager._connections:
                        cpu = psutil.cpu_percent(interval=None)
                        ram = psutil.virtual_memory()
                        ram_gb = round(ram.used / (1024 ** 3), 1)
                        await manager.broadcast({
                            "type": "system_stats",
                            "cpu": f"{int(cpu)}%",
                            "ram": f"{ram_gb}GB"
                        })
            except Exception as e:
                logger.debug(f"Stats loop error: {e}")

        async def _vision_loop():
            while True:
                try:
                    await asyncio.sleep(1)
                    if hasattr(zara, 'vision_queue') and zara.vision_queue and not zara.vision_queue.empty():
                        v_data = zara.vision_queue.get_nowait()
                        if isinstance(v_data, dict) and v_data.get("type") == "vision":
                            await manager.broadcast({
                                "type": "vision_update",
                                "content": v_data.get("content", "")
                            })
                except Exception:
                    pass

        asyncio.create_task(_stats_loop())
        asyncio.create_task(_vision_loop())

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("[SERVER] Nervous System shutting down...")

    return app
