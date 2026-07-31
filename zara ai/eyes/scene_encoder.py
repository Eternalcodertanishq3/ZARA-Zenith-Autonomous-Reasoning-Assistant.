"""
ZARA InternViT Scene Understanding Module
==========================================
Lightweight vision encoder for scene understanding.
Uses InternViT-300M-448px (~600MB, fits in low VRAM).
"""

import logging
import time
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger("ZARA_EYES")

# Lazy imports
torch = None
AutoModel = None
AutoProcessor = None
Image = None


def _lazy_load():
    global torch, AutoModel, AutoProcessor, Image
    if torch is None:
        try:
            import torch as _torch
            from transformers import AutoModel as _AutoModel, AutoProcessor as _AutoProcessor
            from PIL import Image as _Image
            torch = _torch
            AutoModel = _AutoModel
            AutoProcessor = _AutoProcessor
            Image = _Image
        except ImportError as e:
            logger.warning(f"InternViT dependencies not available: {e}")


@dataclass
class SceneUnderstanding:
    """Result of scene understanding analysis."""
    embedding: Optional[np.ndarray]
    description: str
    features: Dict[str, float]
    timestamp: float


class InternViTEncoder:
    """
    InternViT-300M-448px Vision Encoder.
    
    Lightweight alternative to full VLMs.
    Outputs embeddings that can be used for:
    - Scene similarity
    - Visual features for LLM
    - Object/scene classification
    """
    
    MODEL_ID = "OpenGVLab/InternViT-300M-448px"
    
    def __init__(self):
        _lazy_load()
        
        self.model = None
        self.processor = None
        self.is_ready = False
        self.device = "cpu"
        
        # Cache
        self.last_embedding = None
        self.last_features = {}
        self.cache_time = 0
        self.cache_duration = 1.0  # Cache for 1 second
        
    def load(self, device: str = None) -> bool:
        """Load the InternViT model."""
        # Check config first
        try:
            from config import HARDWARE
            if not HARDWARE.get("features", {}).get("scene_encoder", True):
                logger.info("InternViT disabled in config (VRAM optimization).")
                return False
        except ImportError:
            pass
        
        if torch is None or AutoModel is None:
            logger.warning("InternViT dependencies not available.")
            return False
        
        try:
            # Determine device
            if device is None:
                if torch.cuda.is_available():
                    self.device = "cuda"
                else:
                    self.device = "cpu"
            else:
                self.device = device
            
            logger.info(f"Loading InternViT-300M-448px on {self.device}...")
            
            # Load model and processor
            self.processor = AutoProcessor.from_pretrained(
                self.MODEL_ID,
                trust_remote_code=True
            )
            self.model = AutoModel.from_pretrained(
                self.MODEL_ID,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            
            self.model.eval()
            self.is_ready = True
            
            logger.info("✅ InternViT-300M loaded successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load InternViT: {e}")
            return False
    
    def encode(self, frame: np.ndarray, use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Encode an image frame to embedding.
        
        Args:
            frame: BGR image from OpenCV
            use_cache: Use cached embedding if recent
            
        Returns:
            Embedding vector (768-dim for 300M model)
        """
        if not self.is_ready:
            return None
        
        # Use cache if recent
        if use_cache and time.time() - self.cache_time < self.cache_duration:
            return self.last_embedding
        
        try:
            # Convert BGR to RGB
            rgb_frame = frame[:, :, ::-1]
            
            # Convert to PIL
            pil_image = Image.fromarray(rgb_frame)
            
            # Process
            inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Get pooled output or CLS token
                if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    embedding = outputs.pooler_output
                else:
                    embedding = outputs.last_hidden_state[:, 0, :]  # CLS token
            
            # Convert to numpy
            self.last_embedding = embedding.cpu().numpy().flatten()
            self.cache_time = time.time()
            
            return self.last_embedding
            
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            return None
    
    def get_scene_features(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Extract interpretable features from scene.
        Uses embedding similarity to predefined concepts.
        """
        embedding = self.encode(frame)
        if embedding is None:
            return {}
        
        # For now, return basic computed features
        # In a full implementation, these would be compared to concept embeddings
        features = {
            "brightness": float(np.mean(frame) / 255.0),
            "contrast": float(np.std(frame) / 128.0),
            "complexity": float(np.var(embedding) * 10),  # Embedding variance as proxy
        }
        
        self.last_features = features
        return features
    
    def get_understanding(self, frame: np.ndarray) -> SceneUnderstanding:
        """Get complete scene understanding."""
        embedding = self.encode(frame)
        features = self.get_scene_features(frame)
        
        # Generate basic description from features
        brightness_desc = "bright" if features.get("brightness", 0.5) > 0.5 else "dim"
        complexity_desc = "detailed" if features.get("complexity", 0) > 0.5 else "simple"
        
        description = f"A {brightness_desc}, {complexity_desc} scene."
        
        return SceneUnderstanding(
            embedding=embedding,
            description=description,
            features=features,
            timestamp=time.time()
        )
    
    def get_status(self) -> Dict:
        """Get encoder status."""
        return {
            "ready": self.is_ready,
            "model": self.MODEL_ID,
            "device": self.device,
            "cache_age_ms": int((time.time() - self.cache_time) * 1000)
        }


if __name__ == "__main__":
    import cv2
    logging.basicConfig(level=logging.INFO)
    
    encoder = InternViTEncoder()
    encoder.load()
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        understanding = encoder.get_understanding(frame)
        print(f"Scene: {understanding.description}")
        print(f"Features: {understanding.features}")
        
        cv2.imshow("InternViT Scene Understanding", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()
