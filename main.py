"""
ZARA Omni-Architecture v4.0 - Autonomous Digital Consciousness
===============================================================
The complete 7-Phase, 35-Layer autonomous AI companion with:
- Advanced Multimodal Perception
- Dream Processing & Memory Consolidation
- Voice Emotion Detection
- Autonomous Goals & Initiative
- Self-Learning Consciousness

Hardware Distribution:
- NVIDIA RTX 4050 (6GB): Brain + Vision + Voice
- Intel iGPU: Avatar Rendering
- CPU: STT, Wake Word, Background Tasks

Author: Vivaan
"""
import os
import sys
import time
import threading
import logging
import signal
from datetime import datetime
from typing import Optional

# 🚀 NEW: True Multiprocessing Imports
from multiprocessing import Process, Queue, Event
import queue  # For queue.Empty exception handling

# Configure logging before imports
logging.basicConfig(
    format='%(asctime)s | %(name)-15s | %(levelname)-7s | %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/zara.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("ZARA_MAIN")

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# CRITICAL: Pre-import ctranslate2 BEFORE httpx (loaded by ollama)
# On Windows, importing ctranslate2 AFTER httpx causes a hard
# C-level crash (DLL conflict). Loading ctranslate2 first is safe.
# ═══════════════════════════════════════════════════════════════════
try:
    import ctranslate2  # noqa: F401
    logger.debug("[PRE-IMPORT] ctranslate2 loaded (DLL conflict prevention)")
except ImportError:
    logger.debug("[PRE-IMPORT] ctranslate2 not installed — STT will be disabled")

# ═══════════════════════════════════════════════════════════════════
# PRE-WARM: Initialize Ollama connection (GPU inference backend)
# ═══════════════════════════════════════════════════════════════════
_ollama_ready = False
try:
    import ollama
    models = ollama.list()
    if models.get('models'):
        logger.info("[PRE-WARM] ✅ Ollama connected - GPU inference ready!")
        _ollama_ready = True
    else:
        logger.warning("[PRE-WARM] Ollama running but no models. Run: ollama create zara-brain -f brain/Modelfile")
except Exception as e:
    logger.warning(f"[PRE-WARM] Ollama not available: {e}. Brain will use simulation mode.")

# Core imports
from config import (
    DEBUG_MODE, print_banner, ROOT_DIR, 
    MODEL_FILE, PROMPT_FILE, HARDWARE, ACTIONS_DIR
)

# Phase imports (Keep for Reconnection Anchors, though initialization is bypassed)
from brain.cognitive_core import CognitiveCore, get_mind
from brain.emotional_anchor import EmotionalAnchor
from utils.resilience import get_degrader, GracefulDegrader

# 🚀 ISOLATED SENSORY WORKERS (Bypassed in Isolation Mode)
def isolated_audio_worker(audio_queue: Queue, stop_event: Event): pass
def isolated_vision_worker(vision_queue: Queue, stop_event: Event): pass

class ZaraConsciousness:
    """
    ZARA Unified Autonomous Consciousness - Barebones Isolated Mode.
    Only the Cognitive Core is active. All other systems are bypassed.
    """
    
    def __init__(self):
        self.is_running = False
        self.is_authenticated = False
        
        logger.info("═" * 60)
        logger.info("🌟 ZARA CORE ISOLATION MODE v1.0 🌟")
        logger.info("═" * 60)
        
        # Core Cognitive Link
        self.brain = None
        self.emotion = None
        self.degrader = get_degrader()

        # Bypassed Subsystems (Initialised as None for Stability)
        self.consciousness = None
        self.soul = None
        self.knowledge = None
        self.goals = None
        self.dreams = None
        self.resources = None
        self.heartbeat = None
        self.fusion = None
        self.voice = None
        self.ears = None
        self.eyes = None
        self.vision_process = None
        self.audio_process = None
        
        # Shared State
        self.audio_queue = Queue()
        self.vision_queue = Queue()
        self.stop_event = Event()
        
        logger.info("⏳ Initialized in BAREBONES ISOLATION state.")

    def start(self):
        """Start ONLY the Cognitive Core."""
        self.is_running = True
        import gc
        
        logger.info("⏳ [ISOLATION] Loading Cognitive Core (Ollama GPU)...")
        try:
            self.brain = get_mind()
            logger.info("  ✓ Brain online (Isolated Mode)")
        except Exception as e:
            logger.error(f"  ✗ Brain failed: {e}")
            self.brain = CognitiveCore()
        
        self.emotion = EmotionalAnchor()
        
        # ═══════════════════════════════════════════════════════════
        # PHASE B: TEARDOWN BYPASS
        # ═══════════════════════════════════════════════════════════
        logger.info("⏳ [ISOLATION] Bypassing non-core systems...")
        
        def _silent_init(name: str):
            logger.info(f"  💤 {name}: BYPASSED (Interaction Isolation)")
            return None

        # [RECONNECTION ANCHORS]
        self.memory = _silent_init("memory")
        self.fusion = _silent_init("fusion")
        self.consciousness = _silent_init("consciousness")
        self.soul = _silent_init("soul")
        self.knowledge = _silent_init("knowledge")
        self.goals = _silent_init("goals")
        self.dreams = _silent_init("dreams")
        self.voice = _silent_init("voice")
        self.heartbeat = _silent_init("heartbeat")
        self.guardian = _silent_init("guardian")
        
        logger.info("🔓 Biometric auth and background threads disabled")
        logger.info("🌟 ZARA BRAIN IS NOW BAREBONES ISOLATED 🌟")
        logger.info("✓ Startup complete")

    def stop(self):
        """Shutdown the core."""
        logger.info("Initiating hibernation...")
        self.is_running = False
        self.stop_event.set()
        logger.info("💤 ZARA is now SLEEPING.")

    def process_input(self, user_input: str) -> str:
        """Isolated Brain Link: Streams response directly to terminal."""
        try:
            full_response = ""
            print(f"\n🧠 [THINKING]...", end="", flush=True)
            
            for token in self.brain.think(user_input):
                full_response += token
                print(token, end="", flush=True)
            
            print("\n")
            return full_response
            
        except Exception as e:
            logger.error(f"Isolated Processing error: {e}")
            return "Cognitive link failed. Check Ollama."

    def run_interactive(self):
        """Barebones Terminal Loop."""
        self.start()
        print("\n" + "═"*60)
        print("✨ [ZARA BAREBONES CORE ONLINE] - Terminal Mode")
        print("   Direct Cognitive Link - All Sensory Subsystems: DISCONNECTED")
        print("═"*60 + "\n")
        
        while self.is_running:
            try:
                user_input = input("👤 YOU: ").strip()
                if not user_input: continue
                if user_input.lower() in ['exit', 'quit', 'sleep']:
                    self.stop()
                    break
                self.process_input(user_input)
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break
            except Exception as e:
                logger.error(f"Error in terminal loop: {e}")

    def run_gui(self): self.run_interactive()
    def run_server_mode(self): self.run_interactive()
    def get_status(self) -> dict: return {"status": "isolated"}

# Alias
ZaraOmniSystem = ZaraConsciousness

def main():
    try:
        from utils.logger import setup_logging
        setup_logging(log_level=logging.INFO)
    except: pass
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    zara = ZaraConsciousness()
    zara.run_interactive()

if __name__ == "__main__":
    main()