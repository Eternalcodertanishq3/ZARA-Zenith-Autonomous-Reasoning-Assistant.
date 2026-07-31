"""
ZARA Omni-Architecture - Central Configuration
==============================================
All paths, hardware settings, and tunable parameters.
"""
from pathlib import Path
import os

# ============================================================================
# CORE PATHS
# ============================================================================
ROOT_DIR = Path(__file__).parent.resolve()

# Model Directories
BRAIN_DIR = ROOT_DIR / "brain"
EYES_DIR = ROOT_DIR / "eyes"
EARS_DIR = ROOT_DIR / "ears"
SOUL_DIR = ROOT_DIR / "soul"
AVATAR_DIR = ROOT_DIR / "avatar"
IDENTITY_DIR = ROOT_DIR / "identity"
MEMORY_DIR = ROOT_DIR / "memory"
EVOLUTION_DIR = ROOT_DIR / "evolution"
AGENCY_DIR = ROOT_DIR / "agency"
GUARDIAN_DIR = ROOT_DIR / "guardian"
SYSTEM_DIR = ROOT_DIR / "system"
PULSE_DIR = ROOT_DIR / "pulse"
ACTIONS_DIR = ROOT_DIR / "actions"  # The Armory
LOGS_DIR = ROOT_DIR / "logs"
GHOST_DIR = ROOT_DIR / "ghost"  # Sandbox directory

# Model Files
MODEL_FILE = BRAIN_DIR / "Qwen3-4B-Q5_K_M.gguf"
PROMPT_FILE = BRAIN_DIR / "system_prompt.txt"

# Ensure Directories Exist
for dir_path in [BRAIN_DIR, EYES_DIR, EARS_DIR, SOUL_DIR, AVATAR_DIR, 
                 IDENTITY_DIR, MEMORY_DIR, AGENCY_DIR,
                 GUARDIAN_DIR, SYSTEM_DIR, LOGS_DIR,
                 EYES_DIR / "snapshots", IDENTITY_DIR / "authorized_faces",
                 SOUL_DIR / "voice_samples", AVATAR_DIR / "model_v3",
                 MEMORY_DIR / "chroma_db"]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# HARDWARE CONFIGURATION
# ============================================================================
HARDWARE = {
    # NVIDIA GPU Settings
    "nvidia": {
        "enabled": True,
        "vram_limit_gb": 6.0,
        "buffer_gb": 0.5,
        "n_gpu_layers": 20,  # Reduced from 35 to fit in 6GB VRAM
    },
    
    # Intel iGPU Settings
    "intel_igpu": {
        "enabled": True,
        "for_avatar": True,
        "for_depth": False,
    },
    
    # Feature Toggles (VRAM-constrained devices)
    "features": {
        "depth_mapper": False,   # Disabled to save ~500MB VRAM
        "scene_encoder": False,  # Lazy load only when needed
    },
    
    # CPU Settings
    "cpu": {
        "threads": os.cpu_count() or 4,
        "for_stt": True,
        "for_tts": True,
    },
    
    # Camera Settings
    "camera": {
        "device_index": 0,
        "width": 1280,
        "height": 720,
        "fps": 30,
    },
    
    # Audio Settings
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "chunk_size": 1024,
    }
}

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
MODELS = {
    "brain": {
        "ollama_model": "qwen2.5:3b",
        "path": str(MODEL_FILE),
        "n_ctx": 8192,
        "n_gpu_layers": 20,  # Reduced from 35 to fit in 6GB VRAM
        "chat_format": "chatml",
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1024,
    },
    
    "vision": {
        "enabled": True,  # Re-enabled with smaller Florence-2-base model
        "model_id": "microsoft/Florence-2-base",  # ~450MB (was Florence-2-Large ~1.5GB)
        "device": "cpu",  # Run on CPU to save VRAM for Brain
        "quantization": "none",
        "trust_remote_code": True,
    },
    
    "stt": {
        "enabled": True,  # Re-enabled: runs on CPU (no VRAM conflict)
        "model_size": "tiny",  # Use tiny — 'small' crashes ctranslate2 on CPU
        "language": "hi",  # Hinglish detection
        "device": "cpu",   # Use CPU to save VRAM for Brain
    },
    
    "tts": {
        "model_id": "tts_models/multilingual/multi-dataset/xtts_v2",
        "language": "hi",
        "speaker_wav": str(SOUL_DIR / "voice_samples" / "reference.wav"),
    },
    
    "rvc": {
        "enabled": False,  # Model files not available yet
        "model_path": str(SOUL_DIR / "voice_samples" / "anime_voice.pth"),
        "index_path": str(SOUL_DIR / "voice_samples" / "anime_voice.index"),
    },
    
    "wake_word": {
        "phrases": ["zara", "listen", "hey zara", "zara sun"],
        "threshold": 0.6,
    }
}

# ============================================================================
# PERSONA CONFIGURATION
# ============================================================================
PERSONA = {
    "name": "ZARA",
    "role": "Life Partner & Intelligent Desktop Companion",
    "owner": "Vivaan",
    
    # Language preferences
    "primary_language": "hinglish",  # English + Hindi blend
    "hinglish_ratio": 0.3,  # 30% Hindi words
    
    # Personality traits (0-1)
    "warmth": 0.8,
    "playfulness": 0.6,
    "assertiveness": 0.5,
    "technical_depth": 0.7,
    
    # Voice characteristics
    "voice_pitch": "high",
    "voice_speed": 1.0,
    "voice_emotion": True,
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================
SECURITY = {
    "face_recognition": {
        "enabled": True,
        "min_confidence": 0.6,
        "authorized_faces_dir": str(IDENTITY_DIR / "authorized_faces"),
    },
    
    "voice_recognition": {
        "enabled": False,  # Future feature
    },
    
    "encryption": {
        "enabled": True,
        "algorithm": "AES-256",
    },
    
    "firewall": {
        "enabled": True,
        "threat_monitoring": True,
    }
}

# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================
MEMORY_CONFIG = {
    "vector_db": {
        "collection_name": "zara_soul",
        "persist_directory": str(MEMORY_DIR / "chroma_db"),
    },
    
    "compression": {
        "enabled": True,
        "age_threshold_days": 30,
    },
    
    "max_context_tokens": 2000,
}

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================
SYSTEM = {
    "heartbeat_interval": 5.0,  # seconds
    "idle_timeout": 120,  # seconds before power saving
    "sleep_timeout": 600,  # seconds before sleep mode
    
    "logging": {
        "level": "INFO",
        "file": str(LOGS_DIR / "zara.log"),
        "max_size_mb": 10,
    },
    
    "sandbox": {
        "timeout_seconds": 30,
        "max_output_lines": 100,
    }
}

# ============================================================================
# DEBUG & DEVELOPMENT
# ============================================================================
DEBUG_MODE = os.environ.get("ZARA_DEBUG", "0") == "1"
SIMULATION_MODE = os.environ.get("ZARA_SIMULATE", "0") == "1"

# ============================================================================
# BANNER
# ============================================================================
def print_banner():
    """Print ZARA startup banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     ███████╗ █████╗ ██████╗  █████╗                              ║
║     ╚══███╔╝██╔══██╗██╔══██╗██╔══██╗                             ║
║       ███╔╝ ███████║██████╔╝███████║                             ║
║      ███╔╝  ██╔══██║██╔══██╗██╔══██║                             ║
║     ███████╗██║  ██║██║  ██║██║  ██║                             ║
║     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝                             ║
║                                                                   ║
║     AUTONOMOUS CONSCIOUSNESS v4.0 | 12 PHASES | 57 LAYERS        ║
║     "Your Life Partner in the Digital Realm"                     ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  🧠 Brain: Qwen3-4B (Ollama GPU) │  👁️ Vision: Florence-2-base (CPU) ║
║  🗣️ Voice: XTTS v2 (CPU)        │  👂 STT: Whisper tiny (CPU)       ║
║  💾 Memory: ChromaDB            │  🛡️ Security: AES-256 + FaceID    ║
║  🎮 GPU: NVIDIA RTX 4050 6GB    │  🧑‍💻 Avatar: Procedural           ║
╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate configuration on startup."""
    errors = []
    warnings = []
    
    # Check model file
    if not MODEL_FILE.exists():
        warnings.append(f"Brain model not found: {MODEL_FILE}")
    
    # Check VRAM budget (only Brain uses GPU now)
    total_vram = (
        2.9 +  # Brain (Ollama GPU)
        0.5    # Buffer
    )
    if total_vram > HARDWARE["nvidia"]["vram_limit_gb"]:
        warnings.append(f"VRAM budget tight: {total_vram}GB needed, {HARDWARE['nvidia']['vram_limit_gb']}GB available")
    
    return errors, warnings


if __name__ == "__main__":
    print_banner()
    errors, warnings = validate_config()
    
    if warnings:
        print("\n⚠️ WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    
    if errors:
        print("\n❌ ERRORS:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n✅ Configuration valid!")
