"""
ZARA Wake Word Detector - Enhanced Activation System
"""
import logging
import time
import threading
import numpy as np
from typing import Optional, Callable, List
from dataclasses import dataclass

logger = logging.getLogger("ZARA_WAKE")

# Lazy imports
openwakeword = None

def _lazy_load():
    global openwakeword
    if openwakeword is None:
        try:
            from openwakeword.model import Model
            openwakeword = Model
        except ImportError:
            pass


@dataclass
class WakeEvent:
    """Wake word detection event."""
    detected: bool
    keyword: str
    confidence: float
    timestamp: float


class WakeWordDetector:
    """
    Advanced wake word detection with:
    - Multiple wake phrase support
    - Adaptive sensitivity
    - Debouncing (prevent double triggers)
    - Callback system
    - Fallback keyword detection
    """
    
    # Custom wake phrases (fallback keywords)
    WAKE_PHRASES = [
        "zara", "hey zara", "zara listen", "okay zara",
        "jarvis", "hey jarvis",  # For testing with default models
    ]
    
    def __init__(self, sensitivity: float = 0.5):
        _lazy_load()
        
        self.model = None
        self.sensitivity = sensitivity
        self.is_active = False
        self.is_listening = False
        
        # Debouncing
        self.last_wake_time = 0
        self.debounce_seconds = 2.0
        
        # Callbacks
        self.on_wake: Optional[Callable[[WakeEvent], None]] = None
        
        # Statistics
        self.total_detections = 0
        self.detection_history: List[WakeEvent] = []
        
        self._load_model()

    def _load_model(self):
        """Load OpenWakeWord model."""
        if openwakeword is None:
            logger.warning("openwakeword not installed. Using fallback mode.")
            return
        
        try:
            # Load default models (hey_jarvis, alexa, etc.)
            # Custom 'zara' model would be loaded here if trained
            self.model = openwakeword(inference_framework="onnx")
            self.is_active = True
            logger.info("Wake Word Model Loaded (ONNX backend).")
        except Exception as e:
            logger.warning(f"Wake Word Init Failed: {e}")

    def detect(self, audio_chunk: np.ndarray) -> Optional[WakeEvent]:
        """
        Process audio chunk for wake word detection.
        
        Args:
            audio_chunk: numpy array (int16 or float32, typically 1280 samples for 80ms)
        
        Returns:
            WakeEvent if detected, None otherwise
        """
        current_time = time.time()
        
        # Debounce check
        if current_time - self.last_wake_time < self.debounce_seconds:
            return None
        
        if self.is_active and self.model:
            return self._detect_with_model(audio_chunk, current_time)
        else:
            return self._detect_fallback(audio_chunk, current_time)

    def _detect_with_model(self, audio_chunk: np.ndarray, current_time: float) -> Optional[WakeEvent]:
        """Detection using OpenWakeWord model."""
        try:
            predictions = self.model.predict(audio_chunk)
            
            for model_name, score in predictions.items():
                if score > self.sensitivity:
                    event = WakeEvent(
                        detected=True,
                        keyword=model_name,
                        confidence=float(score),
                        timestamp=current_time
                    )
                    self._handle_detection(event)
                    return event
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return None

    def _detect_fallback(self, audio_chunk: np.ndarray, current_time: float) -> Optional[WakeEvent]:
        """
        Fallback detection using energy-based approach.
        Note: This is a placeholder - real implementation would use
        a simple keyword spotting algorithm.
        """
        # Energy-based voice activity (placeholder)
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk
        
        energy = np.sqrt(np.mean(audio_float ** 2))
        
        # Simple threshold (not actual keyword detection)
        if energy > 0.1:
            # In real implementation, this would do actual keyword matching
            pass
        
        return None

    def _handle_detection(self, event: WakeEvent):
        """Handle a successful wake word detection."""
        self.last_wake_time = event.timestamp
        self.total_detections += 1
        self.detection_history.append(event)
        
        # Keep history limited
        if len(self.detection_history) > 100:
            self.detection_history = self.detection_history[-100:]
        
        logger.info(f"Wake Word Detected: {event.keyword} ({event.confidence:.2f})")
        
        # Fire callback
        if self.on_wake:
            try:
                self.on_wake(event)
            except Exception as e:
                logger.error(f"Wake callback error: {e}")

    def set_sensitivity(self, sensitivity: float):
        """Adjust detection sensitivity (0.0 - 1.0)."""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        logger.info(f"Wake sensitivity set to {self.sensitivity:.2f}")

    def start_listening(self):
        """Mark detector as actively listening."""
        self.is_listening = True
        logger.info("Wake word listening started.")

    def stop_listening(self):
        """Stop listening for wake words."""
        self.is_listening = False
        logger.info("Wake word listening stopped.")

    def reset_model(self):
        """Reset model state (clears internal buffers)."""
        if self.model and hasattr(self.model, 'reset'):
            self.model.reset()
            logger.info("Wake model reset.")

    def get_stats(self) -> dict:
        """Get detection statistics."""
        return {
            "active": self.is_active,
            "listening": self.is_listening,
            "sensitivity": self.sensitivity,
            "total_detections": self.total_detections,
            "recent_detections": len(self.detection_history),
            "last_wake_time": self.last_wake_time
        }


class ContinuousWakeListener:
    """
    Background thread that continuously listens for wake words.
    Integrates with the audio input stream.
    """
    
    def __init__(self, detector: WakeWordDetector, on_wake: Callable):
        self.detector = detector
        self.detector.on_wake = on_wake
        self.is_running = False
        self.thread = None

    def start(self, audio_stream_callback: Callable):
        """
        Start continuous listening.
        audio_stream_callback: Function that returns audio chunks
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._listen_loop,
            args=(audio_stream_callback,),
            daemon=True
        )
        self.thread.start()

    def stop(self):
        """Stop listening."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _listen_loop(self, audio_callback: Callable):
        """Main listening loop."""
        self.detector.start_listening()
        
        while self.is_running:
            try:
                audio_chunk = audio_callback()
                if audio_chunk is not None:
                    self.detector.detect(audio_chunk)
            except Exception as e:
                logger.error(f"Listen loop error: {e}")
                time.sleep(0.1)
        
        self.detector.stop_listening()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    detector = WakeWordDetector()
    print("Wake Detector Stats:", detector.get_stats())
