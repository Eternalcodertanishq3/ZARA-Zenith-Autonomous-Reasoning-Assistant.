"""
ZARA Monocular Depth Mapper
Environment depth estimation using MiDaS or similar models.
"""
import cv2
import numpy as np
import logging
import warnings
from dataclasses import dataclass
from typing import Optional, Tuple
import threading

# Suppress timm warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="timm.models.layers")

logger = logging.getLogger("ZARA_DEPTH")

@dataclass
class DepthData:
    depth_map: np.ndarray  # Normalized 0-1 depth values
    avg_distance: float    # Estimated average distance in meters
    closest_point: Tuple[int, int]  # (x, y) of closest object
    farthest_point: Tuple[int, int]
    room_depth: float      # Estimated room depth

class DepthMapper:
    """
    Monocular depth estimation for understanding 3D space.
    Uses MiDaS or falls back to simple stereo assumptions.
    """
    
    def __init__(self):
        self.model = None
        self.transform = None
        self.device = "cpu"
        self.is_active = False
        self.lock = threading.Lock()
        
        self._load_model()
    
    def _load_model(self):
        """Load MiDaS depth estimation model."""
        # Check config first
        try:
            from config import HARDWARE
            if not HARDWARE.get("features", {}).get("depth_mapper", True):
                logger.info("DepthMapper disabled in config (VRAM optimization).")
                self.is_active = False
                return
        except ImportError:
            pass
        
        try:
            import torch
            
            # Check for GPU
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load MiDaS small model (faster, less VRAM)
            self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            self.model.to(self.device)
            self.model.eval()
            
            # Load transforms
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = midas_transforms.small_transform
            
            self.is_active = True
            logger.info(f"Depth Mapper initialized on {self.device}")
            
        except Exception as e:
            logger.warning(f"MiDaS not available: {e}. Using simple depth estimation.")
            self.is_active = False
    
    def _simple_depth_estimate(self, frame: np.ndarray) -> np.ndarray:
        """
        Fallback depth estimation using simple heuristics.
        Assumes objects at bottom of frame are closer.
        """
        h, w = frame.shape[:2]
        depth = np.zeros((h, w), dtype=np.float32)
        
        # Gradient: top is far (0), bottom is close (1)
        for y in range(h):
            depth[y, :] = y / h
        
        # Enhance with edge detection (edges = closer objects)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges_normalized = edges.astype(np.float32) / 255
        
        # Combine
        depth = depth * 0.7 + edges_normalized * 0.3
        
        return depth
    
    def estimate_depth(self, frame: np.ndarray) -> Optional[DepthData]:
        """
        Estimate depth from a single RGB frame.
        """
        with self.lock:
            if self.is_active and self.model is not None:
                return self._midas_depth(frame)
            else:
                return self._fallback_depth(frame)
    
    def _midas_depth(self, frame: np.ndarray) -> DepthData:
        """Full MiDaS inference."""
        import torch
        
        # Preprocess
        input_batch = self.transform(frame).to(self.device)
        
        with torch.no_grad():
            prediction = self.model(input_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=frame.shape[:2],
                mode="bicubic",
                align_corners=False
            ).squeeze()
        
        depth_map = prediction.cpu().numpy()
        
        # Normalize to 0-1
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-8)
        
        return self._create_depth_data(depth_map)
    
    def _fallback_depth(self, frame: np.ndarray) -> DepthData:
        """Fallback when MiDaS is not available."""
        depth_map = self._simple_depth_estimate(frame)
        return self._create_depth_data(depth_map)
    
    def _create_depth_data(self, depth_map: np.ndarray) -> DepthData:
        """Package depth map into DepthData structure."""
        # Find closest and farthest points
        min_idx = np.unravel_index(np.argmin(depth_map), depth_map.shape)
        max_idx = np.unravel_index(np.argmax(depth_map), depth_map.shape)
        
        return DepthData(
            depth_map=depth_map,
            avg_distance=float(np.mean(depth_map)) * 5,  # Scale to ~meters
            closest_point=(int(min_idx[1]), int(min_idx[0])),
            farthest_point=(int(max_idx[1]), int(max_idx[0])),
            room_depth=float(np.max(depth_map) - np.min(depth_map)) * 10
        )
    
    def visualize_depth(self, depth_data: DepthData) -> np.ndarray:
        """Create a colorized depth visualization."""
        depth_colored = cv2.applyColorMap(
            (depth_data.depth_map * 255).astype(np.uint8),
            cv2.COLORMAP_MAGMA
        )
        return depth_colored

if __name__ == "__main__":
    mapper = DepthMapper()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        depth_data = mapper.estimate_depth(frame)
        if depth_data:
            viz = mapper.visualize_depth(depth_data)
            combined = np.hstack((frame, viz))
            cv2.imshow("RGB + Depth", combined)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
