"""
ZARA Vision System - Enhanced Visual Perception
"""
import cv2
import threading
import time
import queue
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger("ZARA_EYES")

# Lazy imports
torch = None
Image = None
AutoModel = None
AutoTokenizer = None

def _lazy_load():
    global torch, Image, AutoModel, AutoTokenizer
    if torch is None:
        try:
            import torch as _torch
            torch = _torch
        except ImportError:
            pass
    
    if Image is None:
        try:
            from PIL import Image as _Image
            Image = _Image
        except ImportError:
            pass
    
    if AutoModel is None:
        try:
            from transformers import AutoModel as _AM, AutoTokenizer as _AT
            AutoModel = _AM
            AutoTokenizer = _AT
        except ImportError:
            pass


@dataclass
class VisualContext:
    """Structured visual analysis result."""
    description: str
    objects_detected: List[str]
    faces_count: int
    dominant_colors: List[str]
    brightness: str  # "dark", "normal", "bright"
    motion_detected: bool
    timestamp: float


class VisionSystem:
    """
    Advanced vision system with InternVL integration.
    Enhanced with:
    - Motion detection
    - Face detection (OpenCV)
    - Color analysis
    - Brightness estimation
    - Caching and rate limiting
    - Frame interpolation
    """
    
    def __init__(self, model_path: str = None):
        _lazy_load()
        
        # State (Initialize first to prevent AttributeError on early return)
        self.running = False
        self.cap = None
        self.lock = threading.Lock()
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.latest_frame = None
        self.frame_id = 0
        self.capture_thread = None
        
        # Essential Processing Queues
        self.frame_buffer = queue.Queue(maxsize=10)
        self.analysis_cache: Optional[VisualContext] = None
        self.last_analysis_time = 0
        
        # Config
        try:
            from config import MODELS, HARDWARE
            conf = MODELS.get("vision", {})
            self.enabled = conf.get("enabled", True)
            
            if not self.enabled:
                logger.warning("Vision System disabled in config.")
                return

            cam_conf = HARDWARE.get("camera", {})
            self.model_id = conf.get("model_id", "OpenGVLab/InternVL2-4B-AWQ")
            self.camera_index = cam_conf.get("device_index", 0)
            self.camera_width = cam_conf.get("width", 1280)
            self.camera_height = cam_conf.get("height", 720)
            self.target_fps = cam_conf.get("fps", 30)
        except ImportError:
            self.model_id = "OpenGVLab/InternVL2-4B-AWQ"
            self.camera_index = 0
            self.camera_width = 1280
            self.camera_height = 720
            self.target_fps = 30
        self.cache_ttl = 2.0  # seconds
        
        # Motion detection
        self.prev_gray = None
        self.motion_threshold = 5000
        
        # Face detection
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except:
            pass
        
        logger.info(f"Vision System initialized. Camera: {self.camera_index}")

    def load_model(self):
        """Load vision model (Florence-2-base or similar)."""
        if torch is None:
            logger.warning("PyTorch not available. Vision model disabled.")
            return
        
        logger.info(f"Loading Vision Model: {self.model_id}...")
        
        # Read device preference from config
        try:
            from config import MODELS
            conf = MODELS.get("vision", {})
            device = conf.get("device", "cpu")
        except ImportError:
            device = "cpu"
        
        try:
            # Florence-2 models use AutoModelForCausalLM + AutoProcessor
            if "florence" in self.model_id.lower():
                from transformers import AutoModelForCausalLM, AutoProcessor
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float32 if device == "cpu" else torch.float16,
                    trust_remote_code=True,
                ).to(device).eval()
                
                self.tokenizer = AutoProcessor.from_pretrained(
                    self.model_id,
                    trust_remote_code=True,
                )
            else:
                # Fallback for other models (InternVL2, etc.)
                self.model = AutoModel.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True,
                    device_map=device
                ).eval()
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_id,
                    trust_remote_code=True,
                    use_fast=False
                )
            
            self.model_loaded = True
            logger.info(f"Vision Model loaded on {device}.")
            
        except Exception as e:
            logger.error(f"Vision Model load failed: {e}")

    def start(self):
        """Start video capture thread."""
        if self.running or not self.enabled:
            return
        
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Vision system started.")

    def stop(self):
        """Stop video capture."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        logger.info("Vision system stopped.")

    def _capture_loop(self):
        """Continuous frame capture."""
        frame_interval = 1.0 / self.target_fps
        
        while self.running:
            start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            with self.lock:
                self.latest_frame = frame
                self.frame_id += 1
            
            # Update buffer
            if self.frame_buffer.full():
                try:
                    self.frame_buffer.get_nowait()
                except queue.Empty:
                    pass
            self.frame_buffer.put(frame)
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)

    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    def get_frame_id(self) -> int:
        """Get current frame counter."""
        with self.lock:
            return self.frame_id

    def analyze_scene(self, custom_prompt: str = None) -> str:
        """
        Analyze current scene using vision model.
        """
        frame = self.get_frame()
        if frame is None:
            return "I can't see anything right now."
        
        if not self.model_loaded:
            # Fallback to basic analysis
            context = self._basic_analysis(frame)
            return self._format_basic_analysis(context)
        
        try:
            pil_image = self._preprocess_image(frame)
            
            prompt = custom_prompt or "<image>\nDescribe what you see briefly and naturally."
            
            generation_config = {
                'max_new_tokens': 256,
                'do_sample': False
            }
            
            response = self.model.chat(self.tokenizer, pil_image, prompt, generation_config)
            
            logger.debug(f"Vision: {response[:80]}...")
            return response
            
        except Exception as e:
            logger.error(f"Vision inference error: {e}")
            return "My vision blurred for a moment."

    def get_visual_context(self) -> VisualContext:
        """Get structured visual analysis."""
        # Check cache
        if self.analysis_cache and (time.time() - self.last_analysis_time) < self.cache_ttl:
            return self.analysis_cache
        
        frame = self.get_frame()
        if frame is None:
            return VisualContext(
                description="No visual input",
                objects_detected=[],
                faces_count=0,
                dominant_colors=[],
                brightness="unknown",
                motion_detected=False,
                timestamp=time.time()
            )
        
        context = self._basic_analysis(frame)
        self.analysis_cache = context
        self.last_analysis_time = time.time()
        
        return context

    def _basic_analysis(self, frame: np.ndarray) -> VisualContext:
        """Perform basic vision analysis without neural model."""
        # Brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 50:
            brightness = "dark"
        elif mean_brightness > 180:
            brightness = "bright"
        else:
            brightness = "normal"
        
        # Face detection
        faces_count = 0
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            faces_count = len(faces)
        
        # Motion detection
        motion_detected = self._detect_motion(gray)
        
        # Dominant colors
        dominant_colors = self._extract_colors(frame)
        
        # Basic description
        objects = []
        if faces_count > 0:
            objects.append(f"{faces_count} person(s)")
        
        return VisualContext(
            description=f"Scene with {brightness} lighting",
            objects_detected=objects,
            faces_count=faces_count,
            dominant_colors=dominant_colors,
            brightness=brightness,
            motion_detected=motion_detected,
            timestamp=time.time()
        )

    def _detect_motion(self, gray: np.ndarray) -> bool:
        """Detect motion between frames."""
        if self.prev_gray is None:
            self.prev_gray = gray
            return False
        
        diff = cv2.absdiff(self.prev_gray, gray)
        motion_score = np.sum(diff)
        
        self.prev_gray = gray
        
        return motion_score > self.motion_threshold

    def _extract_colors(self, frame: np.ndarray, k: int = 3) -> List[str]:
        """Extract dominant colors."""
        try:
            # Resize for speed
            small = cv2.resize(frame, (50, 50))
            pixels = small.reshape(-1, 3).astype(np.float32)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
            
            colors = []
            for center in centers:
                b, g, r = int(center[0]), int(center[1]), int(center[2])
                color_name = self._rgb_to_name(r, g, b)
                colors.append(color_name)
            
            return colors
        except:
            return []

    def _rgb_to_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to color name."""
        if r > 200 and g > 200 and b > 200:
            return "white"
        if r < 50 and g < 50 and b < 50:
            return "black"
        if r > g and r > b:
            return "red" if r > 150 else "dark red"
        if g > r and g > b:
            return "green" if g > 150 else "dark green"
        if b > r and b > g:
            return "blue" if b > 150 else "dark blue"
        return "mixed"

    def _preprocess_image(self, frame: np.ndarray):
        """Preprocess frame for InternVL."""
        if Image is None:
            return None
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _format_basic_analysis(self, context: VisualContext) -> str:
        """Format basic analysis as natural language."""
        parts = [f"I see a scene with {context.brightness} lighting."]
        
        if context.faces_count > 0:
            parts.append(f"There {'is' if context.faces_count == 1 else 'are'} {context.faces_count} person(s) visible.")
        
        if context.motion_detected:
            parts.append("I detect movement.")
        
        if context.dominant_colors:
            parts.append(f"Dominant colors: {', '.join(context.dominant_colors[:3])}.")
        
        return " ".join(parts)

    def get_status(self) -> Dict:
        """Get vision system status."""
        return {
            "running": self.running,
            "model_loaded": self.model_loaded,
            "frame_id": self.frame_id,
            "cache_valid": self.analysis_cache is not None and (time.time() - self.last_analysis_time) < self.cache_ttl
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    vision = VisionSystem()
    vision.start()
    
    time.sleep(1)
    
    context = vision.get_visual_context()
    print("Visual Context:", context)
    
    vision.stop()
