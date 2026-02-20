"""
ZARA TTS Engine - Enhanced Voice Synthesis
"""
import os
import re
import threading
import queue
import logging
import numpy as np

logger = logging.getLogger("ZARA_SOUL")

# Lazy imports
torch = None
sd = None
TTS = None

def _lazy_load():
    global torch, sd, TTS
    if torch is None:
        try:
            import torch as _torch
            torch = _torch
        except ImportError:
            pass
            
    if sd is None:
        try:
            import sounddevice as _sd
            sd = _sd
        except ImportError:
            pass
    
    if TTS is None:
        try:
            from TTS.api import TTS as _TTS
            TTS = _TTS
        except ImportError:
            pass


class TTSEngine:
    """
    Advanced Text-to-Speech Engine using Coqui XTTS v2.
    Enhanced with:
    - Better Hinglish detection
    - Emotion-based speed adjustment
    - Action filtering
    - Async playback queue
    """
    
    HINDI_KEYWORDS = [
        "arrey", "yaar", "na", "kya", "hai", "ho", "haan", "nahi", "acha", "theek",
        "baat", "dekho", "suno", "jaan", "baby", "ruko", "chalo", "karo", "bolo"
    ]
    
    def __init__(self):
        _lazy_load()
        
        self.tts = None
        self.is_loaded = False
        self.lock = threading.Lock()
        self.playback_queue = queue.Queue()
        self.playback_thread = None
        
        # Config
        try:
            from config import MODELS, SOUL_DIR
            conf = MODELS.get("tts", {})
            self.ref_audio = conf.get("speaker_wav") or str(SOUL_DIR / "voice_samples" / "reference.wav")
        except ImportError:
            self.ref_audio = "soul/voice_samples/reference.wav"
        
        self._load_model()
        self._start_playback_thread()

    def _load_model(self):
        if TTS is None or torch is None:
            logger.warning("TTS or torch not installed. Voice disabled.")
            return
        
        try:
            device = "cpu"  # Force CPU — save VRAM for Brain (Ollama)
            logger.info(f"Loading XTTS v2 on {device}...")
            
            # Temporarily patch torch.load for Coqui TTS compatibility
            # (PyTorch 2.6+ blocks legacy loading by default)
            _original_load = torch.load
            def _tts_safe_load(*args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return _original_load(*args, **kwargs)
            torch.load = _tts_safe_load
            
            try:
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
                self.is_loaded = True
                logger.info("XTTS v2 Online.")
            finally:
                # Restore original torch.load
                torch.load = _original_load
                
        except Exception as e:
            logger.warning(f"TTS Init Failed: {e}")
            logger.warning("Attempting to continue without Voice...")
            self.tts = None
            self.is_loaded = False

    def _start_playback_thread(self):
        """Background thread for non-blocking audio playback."""
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()

    def _playback_loop(self):
        while True:
            try:
                audio_np, sample_rate = self.playback_queue.get()
                if sd:
                    sd.play(audio_np, samplerate=sample_rate)
                    sd.wait()
            except Exception as e:
                logger.error(f"Playback Error: {e}")

    def speak(self, text: str, mood: str = "neutral", blocking: bool = True):
        """
        Speak the text.
        blocking: If True, waits for audio to finish.
        """
        if not self.is_loaded:
            logger.info(f"[Silent] ZARA ({mood}): {text}")
            return
        
        # Clean text
        clean_text = self._clean_text(text)
        if not clean_text:
            return
        
        if blocking:
            self._synthesize_and_play(clean_text, mood)
        else:
            threading.Thread(
                target=self._synthesize_and_play,
                args=(clean_text, mood),
                daemon=True
            ).start()

    def _clean_text(self, text: str) -> str:
        """Remove action descriptions and clean text for TTS."""
        # Remove *actions*
        text = re.sub(r'\*[^*]+\*', '', text)
        # Remove (parentheticals)
        text = re.sub(r'\([^)]+\)', '', text)
        # Remove emojis (basic)
        text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _detect_language(self, text: str) -> str:
        """Detect if text is Hindi/Hinglish or English."""
        text_lower = text.lower()
        hindi_count = sum(1 for word in self.HINDI_KEYWORDS if word in text_lower)
        return "hi" if hindi_count >= 2 else "en"

    def _get_speed_for_mood(self, mood: str) -> float:
        """Adjust speaking speed based on mood."""
        speeds = {
            "excited": 1.15,
            "happy": 1.1,
            "neutral": 1.0,
            "sad": 0.9,
            "tired": 0.85,
            "concerned": 0.95,
            "focus": 1.05
        }
        # Convert MoodState enum to string if needed
        mood_str = mood.value if hasattr(mood, 'value') else str(mood)
        return speeds.get(mood_str.lower(), 1.0)

    def _synthesize_and_play(self, text: str, mood: str):
        """Synthesize speech and play audio."""
        with self.lock:
            try:
                lang = self._detect_language(text)
                ref = self.ref_audio if os.path.exists(self.ref_audio) else None
                
                if ref is None:
                    logger.warning("Reference audio missing. Using default speaker.")
                
                # Generate speech
                if ref:
                    wav = self.tts.tts(
                        text=text,
                        speaker_wav=ref,
                        language=lang
                    )
                else:
                    # Use built-in speaker when no reference audio
                    wav = self.tts.tts(
                        text=text,
                        speaker="Claribel Dervla",
                        language=lang
                    )
                
                audio_np = np.array(wav, dtype=np.float32)
                
                # Apply speed adjustment
                speed = self._get_speed_for_mood(mood)
                if speed != 1.0:
                    audio_np = self._adjust_speed(audio_np, speed)
                
                # Play
                if sd:
                    sd.play(audio_np, samplerate=24000)
                    sd.wait()
                
            except Exception as e:
                logger.error(f"TTS Error: {e}")

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Simple speed adjustment via resampling."""
        from scipy.ndimage import zoom
        return zoom(audio, 1.0 / speed)

    def speak_async(self, text: str, mood: str = "neutral"):
        """Queue text for async playback (non-blocking)."""
        if not self.is_loaded:
            return
        
        clean_text = self._clean_text(text)
        if clean_text:
            threading.Thread(
                target=self._synthesize_and_queue,
                args=(clean_text, mood),
                daemon=True
            ).start()

    def _synthesize_and_queue(self, text: str, mood: str):
        """Synthesize and add to playback queue."""
        with self.lock:
            try:
                lang = self._detect_language(text)
                ref = self.ref_audio if os.path.exists(self.ref_audio) else None
                
                if ref:
                    wav = self.tts.tts(text=text, speaker_wav=ref, language=lang)
                else:
                    wav = self.tts.tts(text=text, speaker="Claribel Dervla", language=lang)
                    
                audio_np = np.array(wav, dtype=np.float32)
                
                self.playback_queue.put((audio_np, 24000))
                
            except Exception as e:
                logger.error(f"TTS Queue Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = TTSEngine()
    tts.speak("Hello Vivaan! Aaj kaisa raha din?", mood="happy")
