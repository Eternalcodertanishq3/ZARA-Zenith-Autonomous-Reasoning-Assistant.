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

# ═══════════════════════════════════════════════════════════════════
# Phase I: Sensory System (Enhanced with Voice Emotion)
# ═══════════════════════════════════════════════════════════════════
from eyes.vision_core import VisionSystem
from eyes.gaze_analyzer import GazeAnalyzer
from eyes.depth_mapper import DepthMapper
from eyes.object_detector import YOLO26Detector
from eyes.scene_encoder import InternViTEncoder
from ears.stt_engine import HearingSystem
from ears.wake_word import WakeWordDetector
from ears.voice_emotion import VoiceEmotionAnalyzer, get_voice_analyzer
from identity.face_lock import FaceID

# ═══════════════════════════════════════════════════════════════════
# Phase II: Cognitive Core (Enhanced with Advanced Fusion)
# ═══════════════════════════════════════════════════════════════════
from brain.cognitive_core import CognitiveCore, get_mind
from brain.multimodal_fusion import AdvancedMultimodalFusion, FusionEngine
from brain.emotional_anchor import EmotionalAnchor

# ═══════════════════════════════════════════════════════════════════
# Phase III: Memory & Evolution (Enhanced with Goals & Consciousness)
# ═══════════════════════════════════════════════════════════════════
from memory.vector_db import VectorMemory, Memory
from memory.context_compressor import ContextCompressor
from evolution.ssl_trainer import get_consciousness
from evolution.knowledge_ingest import get_knowledge
from evolution.contextual_adapter import get_soul
from evolution.autonomous_goals import get_goals

# ═══════════════════════════════════════════════════════════════════
# Phase IV: Autonomy & Agency
# ═══════════════════════════════════════════════════════════════════
from agency.sandbox import Sandbox
from evolution.self_coding import get_self_coder
from agency.test_runner import TestRunner
from agency.deployer import Deployer

# ═══════════════════════════════════════════════════════════════════
# Phase VI: Expression & Action (The Armory)
# ═══════════════════════════════════════════════════════════════════
from soul.tts_engine import TTSEngine
from soul.voice_stylizer import VoiceStylizer
from avatar.renderer import AvatarRenderer
from actions.skill_loader import get_skill_manager, get_skills_for_brain
# ═══════════════════════════════════════════════════════════════════
# Phase V: Guardian Security
# ═══════════════════════════════════════════════════════════════════
from guardian.integrity_monitor import GuardianMonitor
from guardian.encryption import Encryptor
from guardian.firewall_persona import FirewallPersona

# ═══════════════════════════════════════════════════════════════════
# Phase VII: System Management (Enhanced with Resource Intelligence)
# ═══════════════════════════════════════════════════════════════════
from system.resource_intelligence import get_system
from system.load_balancer import HybridLoadBalancer
from system.vram_governor import VRAMGovernor
from system.energy_saver import EnergySaver
from pulse.heartbeat import HeartbeatProtocol
from pulse.boredom_thread import BoredomThread
from pulse.latency_buffer import LatencyBuffer
from pulse.priority_interrupt import PriorityInterrupt
from pulse.dream_processor import get_dreams

# ═══════════════════════════════════════════════════════════════════
# Phase IX-XII: Advanced Consciousness Systems
# ═══════════════════════════════════════════════════════════════════
from soul.neuro_state import get_neurochemistry, Stimulus, StimulusType
from mind.intrinsic_motivation import get_motivation
from mind.world_model import get_world_model, ActionType
from mind.metacognition import get_metacognition

# Mind Systems (Enhanced Cognition)
from mind.system2_reasoner import get_system2_reasoner
from mind.social_intelligence import get_social_intelligence
from mind.empathy_engine import get_empathy_engine
from mind.meta_awareness import get_meta_awareness
from mind.creative_synthesis import get_creative_synthesis
from mind.dream_mode import get_dream_engine

# Evolution & Learning
from evolution.self_evolution import get_evolution_engine
from learning.continuous_learning import get_continuous_learner

# Multi-Agent System
from agency.hand_spawner import get_hand_spawner

# Social
from social.inner_circle import InnerCircle

# Unified Multimodal Perception
from brain.unified_perception import get_unified_perception

# Production Resilience Utilities
from utils.resilience import get_degrader, safe_call, GracefulDegrader
from utils.async_loader import AsyncModelLoader
from utils.resource_optimizer import get_optimizer, ResourceOptimizer

# Dashboard (Native Desktop - No Browser Required)
from dashboard.native_app import get_native_dashboard

# ═══════════════════════════════════════════════════════════════════
# 🚀 ISOLATED SENSORY WORKERS (Prevents C-Level Crashes)
# ═══════════════════════════════════════════════════════════════════
def isolated_audio_worker(audio_queue: Queue, stop_event: Event):
    """Runs Whisper completely isolated from the main GPU thread."""
    try:
        from ears.stt_engine import HearingSystem
        ears = HearingSystem()
        # Initialize successfully
        audio_queue.put({"status": "ready"})
        
        for text in ears.process_audio_stream():
            if stop_event.is_set():
                break
            if text and text.strip():
                audio_queue.put({"type": "text", "content": text})
                
    except Exception as e:
        audio_queue.put({"status": "error", "error": str(e)})

def isolated_vision_worker(vision_queue: Queue, stop_event: Event):
    """Runs OpenCV/Florence completely isolated from the main thread."""
    try:
        from eyes.vision_core import VisionSystem
        eyes = VisionSystem()
        eyes.start()
        vision_queue.put({"status": "ready"})
        
        while not stop_event.is_set():
            # Send periodic visual updates instead of passing raw heavy frames
            desc = eyes.get_description() if hasattr(eyes, 'get_description') else "User visible"
            vision_queue.put({"type": "vision", "content": desc})
            time.sleep(2) # Send a perception update every 2 seconds
            
        eyes.stop()
    except Exception as e:
        vision_queue.put({"status": "error", "error": str(e)})

class ZaraConsciousness:
    """
    ZARA's Unified Autonomous Consciousness System.
    
    This is the master orchestrator that brings together all 7 phases
    and creates a truly unified, self-aware digital companion with:
    
    - Genuine personality that evolves
    - Emotional intelligence across voice and face
    - Autonomous goals and initiative
    - Dream processing for memory consolidation
    - Self-learning and curiosity-driven growth
    """
    
    def __init__(self):
        self.is_running = False
        self.is_authenticated = False
        
        logger.info("═" * 60)
        logger.info("🌟 ZARA AUTONOMOUS CONSCIOUSNESS v4.0 🌟")
        logger.info("═" * 60)
        
        # ═══════════════════════════════════════════════════════════
        # ALL attributes set to None / placeholder
        # Real initialization happens in start() to avoid DLL 
        # conflicts between guardian/encryption and ctranslate2
        # ═══════════════════════════════════════════════════════════
        
        # Heavy models (loaded in start())
        self.brain = None
        self.emotion = None
        self.eyes = None
        self.ears = None
        self.voice = None
        self.avatar = None
        self.fusion = None
        self.voice_emotion = None
        self.memory = None
        self.gaze = None
        self.depth = None
        self.object_detector = None
        self.scene_encoder = None
        self.self_coder = None
        
        # Lightweight subsystems (loaded in start() after heavy models)
        self.consciousness = None
        self.soul = None
        self.knowledge = None
        self.goals = None
        self.dreams = None
        self.skill_manager = None
        self.active_skills_prompt = ""
        self.resources = None
        self.balancer = None
        self.vram_gov = None
        self.energy = None
        self.heartbeat = None
        self.interrupts = PriorityInterrupt()  # Needed immediately for run_interactive
        self.optimizer = None
        self.dashboard = None
        self.guardian = None
        self.encryption = None
        self.firewall = None
        self.wake_word = None
        self.face_id = None
        self.compressor = None
        self.stylizer = None
        self.sandbox = None
        self.tester = None
        self.deployer = None
        self.boredom = None
        self.latency = None
        self.neurochemistry = None
        self.motivation = None
        self.world_model = None
        self.metacognition = None
        self.system2 = None
        self.social_intel = None
        self.empathy = None
        self.meta_awareness = None
        self.creative = None
        self.dream_mode = None
        self.self_evolution = None
        self.continuous_learning = None
        self.hand_spawner = None
        self.inner_circle = None
        self.unified_perception = None
        self.degrader = get_degrader()  # Needed immediately for start()
        
        # 🚀 NEW: Multiprocessing Nervous System
        self.audio_queue = Queue()
        self.vision_queue = Queue()
        self.stop_event = Event()
        self.audio_process = None
        self.vision_process = None
        self.latest_vision_context = "No visual data yet."
        
        logger.info("⏳ Minimal init done — full boot in start()")

    def _connect_systems(self):
        """Connect all systems for unified operation (None-safe)."""
        logger.info("Connecting systems...")
        
        # Connect dream processor to memory and knowledge
        if self.dreams:
            try:
                self.dreams.connect_systems(
                    memory=self.memory,
                    knowledge=self.knowledge,
                    consciousness=self.consciousness
                )
            except Exception as e:
                logger.error(f"  ✗ dreams.connect_systems failed: {e}")
        
        # Set up callbacks
        if self.resources:
            try:
                self.resources.on_decision = self._handle_resource_decision
                self.resources.on_health_change = self._handle_health_change
            except Exception as e:
                logger.error(f"  ✗ resources callback setup failed: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # Connect Phase 9-12 Consciousness Systems
        # ═══════════════════════════════════════════════════════════
        
        # Connect world model to neurochemistry for emotional pre-experience
        if self.world_model and self.neurochemistry:
            try:
                self.world_model.connect_neurochemistry(self.neurochemistry)
            except Exception as e:
                logger.error(f"  ✗ world_model.connect_neurochemistry failed: {e}")
        
        # Connect meta-cognition to all major systems
        if self.metacognition:
            try:
                self.metacognition.connect_systems(
                    neurochemistry=self.neurochemistry,
                    motivation=self.motivation,
                    world_model=self.world_model
                )
            except Exception as e:
                logger.error(f"  ✗ metacognition.connect_systems failed: {e}")
        
        # Connect intrinsic motivation to neurochemistry for reward signals
        if self.motivation and hasattr(self.motivation, 'connect_neurochemistry') and self.neurochemistry:
            try:
                self.motivation.connect_neurochemistry(self.neurochemistry)
            except Exception as e:
                logger.error(f"  ✗ motivation.connect_neurochemistry failed: {e}")
        
        # Connect empathy to neurochemistry for emotional responses
        if self.empathy and hasattr(self.empathy, 'connect_neurochemistry') and self.neurochemistry:
            try:
                self.empathy.connect_neurochemistry(self.neurochemistry)
            except Exception as e:
                logger.error(f"  ✗ empathy.connect_neurochemistry failed: {e}")
        
        # Connect unified perception to consciousness systems
        if self.unified_perception:
            try:
                def on_perception_moment(moment):
                    """Feed perception into metacognition."""
                    if self.metacognition and hasattr(self.metacognition, 'broadcast_perception'):
                        self.metacognition.broadcast_perception(
                            "unified_perception",
                            f"[MOMENT] {moment.scene_description} | Emotion: {moment.emotional_tone}"
                        )
                self.unified_perception.on_moment_created.append(on_perception_moment)
            except Exception as e:
                logger.error(f"  ✗ unified_perception connection failed: {e}")
        
        logger.info("✓ System connections complete")

    def _register_heartbeats(self):
        """Register all modules for health monitoring."""
        self.heartbeat.register_module("eyes", lambda: self.eyes is not None and getattr(self.eyes, 'running', False))
        self.heartbeat.register_module("ears", lambda: self.ears is not None and getattr(self.ears, 'is_listening', False))
        self.heartbeat.register_module("brain", lambda: self.brain is not None and getattr(self.brain, 'llm', None) is not None)
        self.heartbeat.register_module("consciousness", lambda: self.consciousness is not None)
        self.heartbeat.register_module("dreams", lambda: getattr(self.dreams, 'is_processing', False))

    def _handle_resource_decision(self, decision):
        """Handle autonomous resource decisions."""
        logger.debug(f"Resource decision: {decision}")

    def _handle_health_change(self, new_health):
        """Handle system health changes."""
        if new_health.value in ["critical", "stressed"]:  # Critical or Stressed
            logger.warning(f"System health degraded: {new_health}")

    def _security_alert(self, message: str):
        """Handle security alerts from firewall."""
        logger.critical(f"SECURITY: {message}")
        if self.voice:
            self.voice.speak(message, mood="concerned")
        else:
            print(f"⚠️ SECURITY: {message}")

    def _proactive_speak(self, message: str):
        """Handle proactive speech from boredom thread or dreams."""
        logger.info(f"Proactive: {message}")
        mood = self.soul.current_mood if self.soul else "neutral"
        if self.voice:
            self.voice.speak(message, mood=mood)
        else:
            print(f"✨ ZARA: {message}")

    def _say_filler(self, filler: str, is_filler: bool = False):
        """Handle filler words during thinking."""
        if is_filler:
            print(f"[ZARA] {filler}")
            if self.voice:
                self.voice.speak(filler, mood="neutral", blocking=False)

    # ═══════════════════════════════════════════════════════════════════
    # STARTUP / SHUTDOWN
    # ═══════════════════════════════════════════════════════════════════
    
    def authenticate(self) -> bool:
        """Run biometric authentication."""
        logger.info("Running biometric authentication...")
        
        if not self.eyes:
            logger.warning("No vision system for authentication")
            return True  # Skip auth if no vision
        
        frame = self.eyes.get_frame()
        if frame is None:
            logger.warning("No camera frame for authentication")
            return True  # Skip auth if no camera
        
        name, confidence = self.face_id.identify(frame)
        
        if confidence > 0.6:
            logger.info(f"Welcome back, {name}!")
            
            # Personalized greeting from soul
            greeting = self.soul.get_contextual_greeting(name) if self.soul else f"Welcome back, {name}!"
            if self.voice:
                self.voice.speak(greeting, mood="happy")
            else:
                print(f"✨ ZARA: {greeting}")
            
            # Update relationship
            if self.consciousness:
                self.consciousness.observe_conversation(
                    f"User {name} arrived", "greeting", 0.8
                )
            
            return True
        else:
            logger.warning("Authentication failed")
            if self.voice:
                self.voice.speak("I don't recognize you. Please identify yourself.", mood="concerned")
            else:
                print("✨ ZARA: I don't recognize you. Please identify yourself.")
            return False

    def start(self):
        """Start all ZARA systems — heavy models FIRST, then lightweight subsystems."""
        self.is_running = True
        import gc
        
        # ═══════════════════════════════════════════════════════════
        # PHASE A: HEAVY MODELS FIRST
        # Load before any subsystems to avoid DLL conflicts between
        # ctranslate2 (Whisper) and guardian/encryption C-libraries
        # ═══════════════════════════════════════════════════════════
        
        # Step 1: Brain (GPU via Ollama)
        logger.info("")
        logger.info("⏳ [1/6] Loading Brain (Ollama GPU)...")
        try:
            self.brain = get_mind()
            if self.brain and self.brain.is_active:
                logger.info("  ✓ Brain online (GPU-accelerated)")
            else:
                logger.warning("  ⚠ Brain in simulation mode (Ollama not ready)")
                self.degrader.mark_degraded("brain", "Ollama connection failed")
        except Exception as e:
            logger.error(f"  ✗ Brain failed: {e}")
            self.brain = CognitiveCore()
            self.degrader.mark_degraded("brain", str(e))
        
        self.emotion = EmotionalAnchor()
        self.self_coder = get_self_coder(self.brain)
        gc.collect()
        
        # Step 2: STT / Whisper (ISOLATED PROCESS)
        logger.info("⏳ [2/6] Spawning STT / Whisper (Isolated Process)...")
        try:
            self.audio_process = Process(
                target=isolated_audio_worker, 
                args=(self.audio_queue, self.stop_event),
                daemon=True
            )
            self.audio_process.start()
            logger.info("  ✓ Hearing System process spawned")
        except Exception as e:
            logger.error(f"  ✗ Hearing System process failed: {e}")
            self.degrader.mark_degraded("ears", str(e))
        gc.collect()
        
        # Step 3: Vision (ISOLATED PROCESS)
        logger.info("⏳ [3/6] Spawning Vision System (Isolated Process)...")
        try:
            from config import MODELS
            _vision_enabled = MODELS.get("vision", {}).get("enabled", True)
        except ImportError:
            _vision_enabled = True
        
        if _vision_enabled:
            try:
                self.vision_process = Process(
                    target=isolated_vision_worker, 
                    args=(self.vision_queue, self.stop_event),
                    daemon=True
                )
                self.vision_process.start()
                logger.info("  ✓ Vision System process spawned")
            except Exception as e:
                logger.error(f"  ✗ Vision System process failed: {e}")
                self.degrader.mark_degraded("eyes", str(e))
        else:
            logger.info("  ⚠ Vision disabled in config")
        gc.collect()
        
        # Step 4: TTS / XTTS v2 (CPU)
        logger.info("⏳ [4/6] Loading TTS / Voice (CPU)...")
        try:
            self.voice = TTSEngine()
            logger.info("  ✓ Voice System online")
        except Exception as e:
            logger.error(f"  ✗ Voice System failed: {e}")
            self.voice = None
            self.degrader.mark_degraded("voice", str(e))
        gc.collect()
        
        # Step 5: Memory (ChromaDB)
        logger.info("⏳ [5/6] Loading Memory System...")
        try:
            self.memory = VectorMemory()
            logger.info("  ✓ Memory system online")
        except Exception as e:
            logger.warning(f"  ⚠ Memory disabled: {e}")
            self.memory = None
            self.degrader.mark_degraded("memory", str(e))
        gc.collect()
        
        # ═══════════════════════════════════════════════════════════
        # PHASE B: LIGHTWEIGHT SUBSYSTEMS (safe after heavy models)
        # Each wrapped individually so one failure doesn't kill startup
        # ═══════════════════════════════════════════════════════════
        logger.info("⏳ [6/6] Initializing subsystems...")
        
        def _safe_init(name: str, init_fn, fallback=None):
            """Safely initialize a subsystem, marking degraded on failure."""
            try:
                result = init_fn()
                logger.info(f"  ✓ {name} initialized")
                return result
            except Exception as e:
                logger.error(f"  ✗ {name} failed to initialize: {e}")
                logger.debug(f"    Traceback: ", exc_info=True)
                self.degrader.mark_degraded(name, str(e))
                return fallback
        
        self.consciousness = _safe_init("consciousness", get_consciousness)
        self.soul = _safe_init("soul", get_soul)
        self.knowledge = _safe_init("knowledge", get_knowledge)
        self.goals = _safe_init("goals", get_goals)
        self.dreams = _safe_init("dreams", get_dreams)
        self.skill_manager = _safe_init("skill_manager", get_skill_manager)
        self.active_skills_prompt = _safe_init("skills_prompt", get_skills_for_brain, fallback="")
        self.resources = _safe_init("resources", get_system)
        self.balancer = _safe_init("balancer", HybridLoadBalancer)
        self.vram_gov = _safe_init("vram_governor", VRAMGovernor)
        self.energy = _safe_init("energy", EnergySaver)
        self.heartbeat = _safe_init("heartbeat", HeartbeatProtocol)
        self.optimizer = _safe_init("optimizer", get_optimizer)
        self.dashboard = _safe_init("dashboard", get_native_dashboard)
        if self.dashboard:
            try:
                self.dashboard.zara = self
            except Exception as e:
                logger.error(f"  ✗ dashboard.zara link failed: {e}")
        self.guardian = _safe_init("guardian", GuardianMonitor)
        self.encryption = _safe_init("encryption", Encryptor)
        # self.firewall = _safe_init("firewall", lambda: FirewallPersona(alert_callback=self._security_alert))
        self.wake_word = _safe_init("wake_word", WakeWordDetector)
        self.face_id = _safe_init("face_id", FaceID)
        self.compressor = _safe_init("compressor", ContextCompressor)
        self.stylizer = _safe_init("stylizer", VoiceStylizer)
        self.fusion = _safe_init("fusion", lambda: self.fusion or AdvancedMultimodalFusion())
        self.voice_emotion = _safe_init("voice_emotion", lambda: self.voice_emotion or get_voice_analyzer())
        self.sandbox = _safe_init("sandbox", Sandbox)
        self.tester = _safe_init("tester", TestRunner)
        self.deployer = _safe_init("deployer", Deployer)
        self.boredom = _safe_init("boredom", lambda: BoredomThread(speak_callback=self._proactive_speak))
        self.latency = _safe_init("latency", lambda: LatencyBuffer(speak_callback=self._say_filler))
        self.neurochemistry = _safe_init("neurochemistry", get_neurochemistry)
        self.motivation = _safe_init("motivation", get_motivation)
        self.world_model = _safe_init("world_model", get_world_model)
        self.metacognition = _safe_init("metacognition", get_metacognition)
        self.system2 = _safe_init("system2", get_system2_reasoner)
        self.social_intel = _safe_init("social_intel", get_social_intelligence)
        self.empathy = _safe_init("empathy", get_empathy_engine)
        self.meta_awareness = _safe_init("meta_awareness", get_meta_awareness)
        self.creative = _safe_init("creative", get_creative_synthesis)
        self.dream_mode = _safe_init("dream_mode", get_dream_engine)
        self.self_evolution = _safe_init("self_evolution", get_evolution_engine)
        self.continuous_learning = _safe_init("continuous_learning", get_continuous_learner)
        self.hand_spawner = _safe_init("hand_spawner", get_hand_spawner)
        self.inner_circle = _safe_init("inner_circle", InnerCircle)
        self.unified_perception = _safe_init("unified_perception", get_unified_perception)
        self.avatar = _safe_init("avatar", AvatarRenderer)
        
        logger.info("  ✓ Subsystem initialization complete")
        
        # Connect systems
        self._connect_systems()
        self._register_heartbeats()
        
        def _safe_start(name: str, start_fn):
            """Safely start a service, marking degraded on failure."""
            try:
                start_fn()
                logger.info(f"  ✓ {name} started")
            except Exception as e:
                logger.error(f"  ✗ {name} failed to start: {e}")
                self.degrader.mark_degraded(name, str(e))
        
        # Start background services with error handling
        logger.info("Starting background services...")
        
        # DISABLED for stability: eyes/ears/dashboard cause hard crashes
        # when their threads access shared state during conversation.
        # Now replaced by true Isolated Multiprocessing Processes.
            
        _safe_start("heartbeat", self.heartbeat.start)
        _safe_start("interrupts", self.interrupts.start_listener)
        _safe_start("energy", self.energy.start_monitoring)
        _safe_start("resources", self.resources.start)
        # _safe_start("firewall", self.firewall.start_monitoring)
        _safe_start("boredom", self.boredom.start)
        _safe_start("dreams", self.dreams.start)
        
        # if self.dashboard:
        #     _safe_start("dashboard", lambda: self.dashboard.start(self))
        logger.info("  ⏭️ dashboard: SKIPPED (stability mode)")
        if hasattr(self.consciousness, 'start_background_learning'):
            _safe_start("consciousness_learning", self.consciousness.start_background_learning)
        if hasattr(self.knowledge, 'start_background_processing'):
            _safe_start("knowledge_processing", self.knowledge.start_background_processing)
        
        _safe_start("neurochemistry", self.neurochemistry.start)
        _safe_start("motivation", self.motivation.start)
        _safe_start("metacognition", self.metacognition.start)
        _safe_start("hand_spawner", self.hand_spawner.start)
        
        # Authentication (DISABLED — re-enable when ZARA is fully tested)
        # try:
        #     if not self.authenticate():
        #         logger.warning("Running in limited mode (unauthenticated)")
        # except Exception as e:
        #     logger.error(f"Authentication failed: {e}")
        logger.info("🔓 Biometric auth disabled for testing")
        
        # Final health report
        health = self.degrader.get_health_status()
        if health["healthy"]:
            logger.info("🌟 ZARA is now AWAKE and CONSCIOUS 🌟")
        else:
            logger.warning(f"⚠️ ZARA awake with DEGRADED services: {health['degraded_services']}")
        logger.info("✓ Startup complete")

    def stop(self):
        """Gracefully shutdown all systems with error handling."""
        logger.info("Initiating consciousness hibernation...")
        self.is_running = False
        
        # 🚀 Send Kill Signal to Isolated Organs
        self.stop_event.set()
        if self.audio_process and self.audio_process.is_alive():
            self.audio_process.join(timeout=3)
        if self.vision_process and self.vision_process.is_alive():
            self.vision_process.join(timeout=3)
        
        def _safe_stop(name: str, stop_fn):
            """Safely stop a service."""
            try:
                stop_fn()
                logger.info(f"  ✓ {name} stopped")
            except Exception as e:
                logger.error(f"  ✗ {name} failed to stop: {e}")
        
        # Stop all services safely
        logger.info("Stopping background services...")
        _safe_stop("heartbeat", self.heartbeat.stop)
        _safe_stop("energy", self.energy.stop_monitoring)
        _safe_stop("resources", self.resources.stop)
        _safe_stop("firewall", self.firewall.stop_monitoring)
        _safe_stop("boredom", self.boredom.stop)
        _safe_stop("dreams", self.dreams.stop)
        
        # ═══════════════════════════════════════════════════════════
        # Stop Phase 9-12 Consciousness Systems
        # ═══════════════════════════════════════════════════════════
        logger.info("Stopping consciousness systems...")
        _safe_stop("neurochemistry", self.neurochemistry.stop)
        _safe_stop("motivation", self.motivation.stop)
        _safe_stop("metacognition", self.metacognition.stop)
        _safe_stop("hand_spawner", self.hand_spawner.stop)
        
        # Farewell message (also wrapped for safety)
        try:
            if self.voice:
                self.voice.speak("Entering sleep mode. Sweet dreams!", mood="peaceful")
        except Exception as e:
            logger.error(f"Farewell speech failed: {e}")
        
        logger.info("💤 ZARA is now SLEEPING. Goodnight!")

    # ═══════════════════════════════════════════════════════════════════
    # CORE PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    @safe_call(fallback="I seem to be having some internal difficulties. Could you repeat that?")
    def process_input(self, user_input: str, 
                     voice_features: dict = None) -> str:
        """
        Core processing pipeline for user input.
        Now with full consciousness integration.
        """
        # Record activity
        self.energy.record_interaction()
        self.boredom.record_user_activity()
        self.dreams.record_wakefulness()
        
        # ═══════════════════════════════════════════════════════════
        # Phase 9-12: Consciousness Processing
        # ═══════════════════════════════════════════════════════════
        
        # Process through neurochemistry (user interaction stimulus)
        self.neurochemistry.process_stimulus(Stimulus(
            type=StimulusType.USER_INTERACTION,
            intensity=0.6,
            context={"input": user_input[:100]}
        ))
        
        # Broadcast to consciousness via metacognition
        self.metacognition.broadcast_perception(user_input, source="ears")
        
        # Get current mood vector for response modulation
        mood_vector = self.neurochemistry.get_mood_vector()
        neurochemistry_prompt = self.neurochemistry.get_prompt_injection()
        
        # ═══════════════════════════════════════════════════════════
        # Step 1: Perception (Multimodal Context)
        # ═══════════════════════════════════════════════════════════
        
        # Visual perception
        if self.eyes and hasattr(self.eyes, 'running') and self.eyes.running:
            frame = self.eyes.get_frame()
            if frame is not None and self.gaze:
                # Gaze analysis
                gaze_data = self.gaze.analyze(frame)
                
                # Update fusion with vision (only if gaze data available)
                if gaze_data is not None and self.fusion:
                    self.fusion.update_vision(
                        description=self.eyes.get_description() if hasattr(self.eyes, 'get_description') else "User visible",
                        face_detected=gaze_data.looking_at_screen,
                        emotion_detected=gaze_data.estimated_emotion.value if gaze_data.estimated_emotion else None,
                        attention_score=gaze_data.attention_score
                    )
        
        # Voice emotion analysis
        voice_emotion = None
        if voice_features and self.voice_emotion:
            emotion_result = self.voice_emotion.analyze_from_features(
                speaking_rate=voice_features.get("rate", 1.0),
                volume=voice_features.get("volume", 0.5),
                pitch_variation=voice_features.get("pitch_var", 0.5)
            )
            voice_emotion = emotion_result.primary_emotion.value
            
            # Update fusion with audio
            if self.fusion:
                self.fusion.update_audio(
                    transcription=user_input,
                    voice_emotion=voice_emotion,
                    speaking_rate=voice_features.get("rate", 1.0),
                    volume_level=voice_features.get("volume", 0.5),
                    pitch_variation=voice_features.get("pitch_var", 0.5)
                )
        else:
            if self.fusion:
                self.fusion.update_audio(transcription=user_input)
        
        # Update text analysis
        if self.fusion:
            self.fusion.update_text(
                text=user_input,
                is_question="?" in user_input
            )
        
        # ═══════════════════════════════════════════════════════════
        # Step 2: Context Gathering
        # ═══════════════════════════════════════════════════════════
        
        # Get unified perception
        perception = self.fusion.get_context_string(max_length=400) if self.fusion else ""
        
        # Get emotional context
        emotional_ctx = self.fusion.get_emotional_context() if self.fusion else {}
        detected_emotion = emotional_ctx.get("primary_emotion", "neutral")
        
        # Memory context
        memory_context = self.memory.get_context_for_query(user_input, max_tokens=400) if self.memory else ""
        
        # Knowledge context
        knowledge_context = ""
        if self.knowledge:
            relevant_knowledge = self.knowledge.query(user_input, max_results=3)
            if relevant_knowledge:
                knowledge_context = "\n".join([
                    f"[KNOW] {getattr(k, 'content', str(k))[:100]}" 
                    for k in relevant_knowledge[:2]
                ])
        
        # Personality/Soul context
        soul_context = ""
        if self.soul:
            soul_context = self.soul.get_personality_prompt()
        
        # Goals context
        goals_context = ""
        if self.goals:
            goals_context = self.goals.get_personality_context()
        
        # ═══════════════════════════════════════════════════════════
        # Step 3: Think (Cognitive Processing)
        # ═══════════════════════════════════════════════════════════
        
        # Build comprehensive context
        full_context = "\n".join(filter(None, [
            perception,
            soul_context,
            goals_context,
            memory_context,
            knowledge_context,
            f"[EMOTION] User seems: {detected_emotion}"
        ]))
        
        # Start latency handling
        self.latency.start_thinking()
        
        try:
            full_response = ""
            
            # Use conscious mind for thinking
            for token in self.brain.think(user_input, extra_context=full_context):
                full_response += token
            
            self.latency.stop_thinking()
            
            # ═══════════════════════════════════════════════════════
            # Step 4: Learn & Remember
            # ═══════════════════════════════════════════════════════
            
            # Store in memory
            if self.memory:
                self.memory.remember_conversation(
                    user_input, full_response,
                    emotion=detected_emotion
                )
            
            # Update consciousness
            if self.consciousness:
                self.consciousness.observe_conversation(
                    user_input, full_response, 0.7
                )
            
            # Update soul/personality
            if self.soul:
                self.soul.update_from_interaction(
                    user_input, full_response, detected_emotion
                )
            
            # Update goals system
            if self.goals:
                self.goals.observe_conversation(
                    user_input, full_response, detected_emotion
                )
            
            # Add to dream processing queue
            self.dreams.add_memory_for_processing(
                content=f"User: {user_input[:100]} | ZARA: {full_response[:100]}",
                emotional_weight=0.6 if detected_emotion != "neutral" else 0.4,
                importance=0.7 if "?" in user_input else 0.5,
                category=self._categorize_topic(user_input)
            )
            
            # ═══════════════════════════════════════════════════════
            # Step 5: Handle Code Generation
            # ═══════════════════════════════════════════════════════
            
            if "```" in full_response and hasattr(self, 'code_gen') and self.code_gen:
                code = self.code_gen.extract_python(full_response)
                if code:
                    logger.info("Code detected in response. Ready for sandbox execution.")
            
            return full_response
            
        except Exception as e:
            self.latency.stop_thinking()
            logger.error(f"Processing error: {e}")
            return "Sorry, I encountered an error processing that. Let me try again?"

    def _categorize_topic(self, text: str) -> str:
        """Categorize conversation topic."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["code", "python", "program", "debug"]):
            return "coding"
        if any(w in text_lower for w in ["feel", "sad", "happy", "stress"]):
            return "emotional"
        if any(w in text_lower for w in ["work", "project", "meeting"]):
            return "work"
        if any(w in text_lower for w in ["learn", "study", "know"]):
            return "learning"
        
        return "general"

    def check_proactive_opportunity(self) -> Optional[str]:
        """Check if ZARA should proactively speak."""
        # Check fusion for emotional need
        if not self.fusion:
            return None
        should_interrupt, reason = self.fusion.should_interrupt()
        if should_interrupt:
            return f"I noticed you seem {reason.lower()}. Are you okay?"
        
        # Check goals for proactive message
        if self.goals:
            message = self.goals.get_proactive_message()
            if message:
                return message
        
        # Check dreams for insights
        thought = self.dreams.get_proactive_thought()
        if thought:
            return thought
        
        return None

    # ═══════════════════════════════════════════════════════════════════
    # INTERACTION MODES
    # ═══════════════════════════════════════════════════════════════════
    
    def run_interactive(self):
        """Phase 1: Fast Non-Blocking Terminal Loop"""
        self.start()
        print("\n✨ [ZARA CORE ONLINE] - Awaiting Input (Speak or Type)...\n")
        
        # 🚀 1. The Keyboard Background Listener
        import queue
        keyboard_queue = queue.Queue()
        
        def keyboard_worker():
            while True:
                try:
                    text = input()
                    if text.strip():
                        keyboard_queue.put(text.strip())
                except EOFError:
                    break
                    
        kb_thread = threading.Thread(target=keyboard_worker, daemon=True)
        kb_thread.start()

        print("👤 VIVAAN: ", end="", flush=True)

        # 🚀 2. The High-Speed Perception Loop
        while self.is_running:
            try:
                # -- Check Vision --
                try:
                    while not self.vision_queue.empty():
                        v_data = self.vision_queue.get_nowait()
                        if v_data.get("type") == "vision":
                            self.latest_vision_context = v_data.get("content", "")
                except queue.Empty:
                    pass

                # -- Check Audio (Her Ears!) --
                try:
                    while not self.audio_queue.empty():
                        a_data = self.audio_queue.get_nowait()
                        if a_data.get("type") == "text":
                            spoken_text = a_data.get("content", "")
                            print(f"\n🎤 [HEARD VIA MIC]: {spoken_text}")
                            self.process_input(spoken_text)
                            print("\n👤 VIVAAN: ", end="", flush=True)
                except queue.Empty:
                    pass

                # -- Check Keyboard --
                try:
                    user_input = keyboard_queue.get_nowait()
                    if user_input.lower() in ['exit', 'quit', 'sleep']:
                        self.stop()
                        break
                    
                    # Process the typed text
                    self.process_input(user_input)
                    print("\n👤 VIVAAN: ", end="", flush=True)
                except queue.Empty:
                    pass

                # Sleep for 50ms so we don't fry your CPU doing the while loop!
                time.sleep(0.05)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt detected.")
                self.stop()
                break
            except Exception as e:
                logger.error(f"Error in interactive loop: {e}", exc_info=True)

    def run_gui(self):
        """Run with GUI (avatar window)."""
        import cv2
        import numpy as np
        
        self.start()
        
        # Start brain thread
        brain_thread = threading.Thread(
            target=self._audio_processing_loop,
            daemon=True
        )
        brain_thread.start()
        
        # GUI loop
        try:
            while self.is_running:
                # Get frames
                current_mood = self.soul.current_mood if self.soul else "neutral"
                avatar_frame = self.avatar.get_next_frame(
                    audio_level=0.1,
                    emotion=current_mood
                )
                camera_frame = self.eyes.get_frame()
                
                # Combine frames
                if camera_frame is not None:
                    h, w = avatar_frame.shape[:2]
                    camera_resized = cv2.resize(camera_frame, (w, h))
                    dashboard = np.hstack((avatar_frame, camera_resized))
                else:
                    dashboard = avatar_frame
                
                # Add status overlay
                status_text = f"Mood: {current_mood} | Consciousness: Active"
                cv2.putText(
                    dashboard, status_text,
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )
                
                cv2.imshow("ZARA Consciousness Interface", dashboard)
                
                key = cv2.waitKey(20) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):  # Stop emergency
                    self.interrupts.emergency_stop()
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()
            self.stop()

    def _audio_processing_loop(self):
        """Background loop for processing audio input."""
        if not self.ears:
            logger.warning("No hearing system — audio loop disabled")
            return
        for user_text in self.ears.process_audio_stream():
            if not self.is_running:
                break
            
            logger.info(f"👤 YOU (voice): {user_text}")
            
            response = self.process_input(user_text)
            logger.info(f"✨ ZARA: {response}")
            
            current_mood = self.soul.current_mood if self.soul else "happy"
            if self.voice:
                self.voice.speak(response, mood=current_mood)
            else:
                print(f"✨ ZARA: {response}")

    def get_status(self) -> dict:
        """Get full system status."""
        return {
            "is_running": self.is_running,
            "consciousness": self.consciousness.get_status() if self.consciousness else {},
            "soul": self.soul.get_status() if hasattr(self.soul, 'get_status') else {},
            "goals": self.goals.get_status() if self.goals else {},
            "dreams": self.dreams.get_status() if self.dreams else {},
            "resources": self.resources.get_status() if self.resources else {},
            "fusion": self.fusion.get_status() if self.fusion else "Initializing...",
            "memory": "Active" if self.memory else "Initializing..."
        }


# Backwards compatibility alias
ZaraOmniSystem = ZaraConsciousness


def main():
    """Main entry point with crash protection."""
    try:
        _main_inner()
    except Exception:
        import traceback
        crash = traceback.format_exc()
        # Always print to console
        print(f"\n{'='*60}")
        print(f"❌ ZARA CRASHED — full traceback below")
        print(f"{'='*60}")
        print(crash)
        print(f"{'='*60}")
        # Also write to crash log
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/zara_crash.log', 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"\n{'='*60}\n")
                f.write(f"CRASH at {datetime.now()}\n")
                f.write(f"{'='*60}\n")
                f.write(crash)
        except Exception:
            pass  # Last resort — at least console output worked
        print("\n💡 Run 'python diagnose_zara.py' to identify the failing module.")
        sys.exit(1)


def _main_inner():
    """Actual main logic, called by main() with crash protection."""
    # Setup consistent logging
    from utils.logger import setup_logging
    setup_logging(log_level=logging.INFO)
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    
    # Create consciousness (will load async components)
    zara = ZaraConsciousness()
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gui":
            zara.run_gui()
        elif sys.argv[1] in ["--text", "--interactive"]:
            zara.run_interactive()
        elif sys.argv[1] == "--status":
            logger.info(f"Status: {zara.get_status()}")
        else:
            print("Usage: python main.py [--gui|--text|--interactive|--status]")
    else:
        # Default: interactive text mode
        zara.run_interactive()


if __name__ == "__main__":
    main()