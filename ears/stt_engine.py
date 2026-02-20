"""
ZARA Hearing System - Enhanced STT with WebRTC VAD
"""
import os
import threading
import queue
import time
import logging
import numpy as np

logger = logging.getLogger("ZARA_EARS")

# Lazy imports for robustness
sd = None
webrtcvad = None
WhisperModel = None

def _lazy_load_deps():
    global sd, webrtcvad, WhisperModel
    if sd is None:
        try:
            import sounddevice as _sd
            sd = _sd
        except ImportError:
            logger.warning("sounddevice not installed")
    
    if webrtcvad is None:
        try:
            import webrtcvad as _vad
            webrtcvad = _vad
        except ImportError:
            pass
    
    if WhisperModel is None:
        try:
            from faster_whisper import WhisperModel as _wm
            WhisperModel = _wm
        except ImportError:
            pass


class HearingSystem:
    """
    Advanced Hearing System with WebRTC VAD and Faster-Whisper.
    Enhanced with:
    - Robust lazy loading
    - Noise gate
    - Utterance buffering fix
    - Graceful degradation
    """
    
    def __init__(self, model_size=None, model_path=None):
        _lazy_load_deps()
        
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.stream = None
        
        # Config
        try:
            from config import MODELS
            conf = MODELS.get("stt", {})
        except ImportError:
            conf = {}
        
        self.enabled = conf.get("enabled", True)
        self.model_size = model_size or conf.get("model_size", "medium")
        self.device = conf.get("device", "cpu")
        
        if not self.enabled:
            logger.warning("STT System disabled in config.")
            self.transcriber = None
            return
        
        self.transcriber = None
        self.vad = None
        
        # Audio settings
        self.sample_rate = 16000
        self.frame_duration_ms = 30
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # State machine
        self.is_speaking = False
        self.silence_frames = 0
        self.max_silence_frames = int(1.5 * 1000 / self.frame_duration_ms)  # 1.5s
        self.noise_floor = 0.005  # Adaptive noise gate
        
        logger.info("Initializing Hearing System...")
        self._init_vad()
        self._load_model()

    def _init_vad(self):
        if webrtcvad:
            try:
                self.vad = webrtcvad.Vad(2)  # Mode 2: Balanced
                logger.info("WebRTC VAD initialized (mode 2).")
            except Exception as e:
                logger.warning(f"VAD init failed: {e}")
        else:
            logger.warning("webrtcvad not installed. Using energy-based detection.")

    @staticmethod
    def _probe_whisper_subprocess(model_size: str, device: str, compute_type: str) -> bool:
        """
        Test-load Whisper in a subprocess to detect C-level crashes (segfaults).
        Returns True if Whisper loads safely, False if the subprocess dies.
        """
        import subprocess, sys
        probe_code = f"""
import sys
try:
    from faster_whisper import WhisperModel
    m = WhisperModel("{model_size}", device="{device}", compute_type="{compute_type}")
    print("OK")
    sys.exit(0)
except Exception as e:
    print(f"ERR:{{e}}")
    sys.exit(1)
"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", probe_code],
                capture_output=True, text=True, timeout=120,
                cwd=os.getcwd()
            )
            if result.returncode == 0 and "OK" in result.stdout:
                return True
            else:
                logger.warning(f"Whisper probe failed (exit={result.returncode}): {result.stdout.strip()} {result.stderr.strip()[-200:]}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Whisper probe timed out (120s)")
            return False
        except Exception as e:
            logger.warning(f"Whisper probe error: {e}")
            return False

    def _load_model(self):
        if WhisperModel is None:
            logger.warning("faster-whisper not installed. STT disabled.")
            return
        
        # MUST use float32 on CPU — int8/auto crashes ctranslate2 on this system
        compute_type = "float16" if self.device == "cuda" else "float32"
        
        # Try preferred model first, then fallback chain
        attempts = [
            (self.model_size, self.device, compute_type),
            ("tiny", "cpu", "float32"),
        ]
        # Deduplicate if already tiny+cpu
        if self.model_size == "tiny" and self.device == "cpu":
            attempts = [attempts[0]]
        
        for model_size, device, ct in attempts:
            logger.info(f"Loading Whisper ({model_size}) on {device} [compute={ct}]...")
            
            # Probe in subprocess first to detect C-level crashes
            logger.info(f"  Probing Whisper safety in subprocess...")
            if not self._probe_whisper_subprocess(model_size, device, ct):
                logger.error(f"  ❌ Whisper ({model_size}) causes C-level crash — skipping")
                continue
            
            # Safe to load in main process
            try:
                self.transcriber = WhisperModel(model_size, device=device, compute_type=ct)
                self.device = device
                self.model_size = model_size
                logger.info(f"  ✅ Whisper ({model_size}) loaded on {device}")
                return
            except Exception as e:
                logger.error(f"  ❌ Whisper ({model_size}) Python error: {e}")
                continue
        
        logger.critical("❌ All Whisper models failed. STT disabled — voice input unavailable.")
        self.transcriber = None

    @property
    def running(self):
        """Backward compatibility property."""
        return self.is_listening

    def start_listening(self):
        if self.is_listening or sd is None or not self.enabled:
            return
        
        self.is_listening = True
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                blocksize=self.frame_size,
                dtype='float32'
            )
            self.stream.start()
            logger.info("Ears Open.")
        except Exception as e:
            logger.critical(f"Mic Error: {e}")
            self.is_listening = False

    def stop_listening(self):
        self.is_listening = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
        logger.info("Ears Closed.")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.debug(f"Audio status: {status}")
        if self.is_listening:
            self.audio_queue.put(indata.copy())

    def process_audio_stream(self):
        """Generator that yields transcribed text."""
        accumulated_audio = []
        
        while self.is_listening:
            try:
                indata = self.audio_queue.get(timeout=1.0)
                
                # Convert to PCM16 for WebRTC VAD
                pcm_data = (indata.flatten() * 32768).astype(np.int16).tobytes()
                
                is_speech = self._detect_speech(indata, pcm_data)
                
                if is_speech:
                    if not self.is_speaking:
                        logger.debug("Speech started...")
                        self.is_speaking = True
                    
                    self.silence_frames = 0
                    accumulated_audio.append(indata)
                
                elif self.is_speaking:
                    self.silence_frames += 1
                    accumulated_audio.append(indata)  # Include trailing silence
                    
                    if self.silence_frames > self.max_silence_frames:
                        # End of utterance - transcribe
                        if accumulated_audio:
                            text = self._transcribe_audio(accumulated_audio)
                            if text:
                                yield text
                        
                        # Reset state
                        self.is_speaking = False
                        accumulated_audio = []
                        self.silence_frames = 0
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                continue

    def _detect_speech(self, indata, pcm_data):
        """Detect if current frame contains speech."""
        if self.vad:
            try:
                return self.vad.is_speech(pcm_data, self.sample_rate)
            except:
                pass
        
        # Energy-based fallback
        rms = np.sqrt(np.mean(indata.flatten() ** 2))
        return rms > self.noise_floor

    def _transcribe_audio(self, audio_chunks):
        """Transcribe accumulated audio."""
        if not self.transcriber:
            return "Simulation Audio Input"
        
        try:
            # Concatenate and normalize
            audio_np = np.concatenate([c.flatten() for c in audio_chunks])
            
            # Transcribe with auto language detection
            segments, info = self.transcriber.transcribe(
                audio_np,
                beam_size=5,
                language=None,  # Auto-detect
                vad_filter=True
            )
            
            text = " ".join([s.text for s in segments]).strip()
            
            if text:
                detected_lang = info.language if hasattr(info, 'language') else 'unknown'
                logger.info(f"Heard ({detected_lang}): {text}")
                return text
            
        except Exception as e:
            logger.error(f"Transcription Error: {e}")
        
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ears = HearingSystem(model_size="small")
    ears.start_listening()
    
    try:
        for text in ears.process_audio_stream():
            print(f">> {text}")
    except KeyboardInterrupt:
        ears.stop_listening()
