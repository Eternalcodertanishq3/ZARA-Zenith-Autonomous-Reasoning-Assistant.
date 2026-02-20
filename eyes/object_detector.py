"""
ZARA YOLO26 Object Detection Module
====================================
Uses the latest YOLO26 model for object detection, pose estimation, and segmentation.
Edge-optimized with NMS-free inference.
"""

import logging
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("ZARA_EYES")

# Lazy import
YOLO = None

def _lazy_load():
    global YOLO
    if YOLO is None:
        try:
            from ultralytics import YOLO as UltralyticsYOLO
            YOLO = UltralyticsYOLO
        except ImportError:
            logger.warning("ultralytics not installed. YOLO disabled.")


@dataclass
class DetectedObject:
    """A detected object in the frame."""
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]


class YOLO26Detector:
    """
    YOLO26-based object detector.
    
    Features:
    - NMS-free end-to-end inference
    - Edge-optimized for low-power devices
    - Multi-task: detection, segmentation, pose
    """
    
    # Objects that ZARA should especially notice
    IMPORTANT_OBJECTS = {
        "person", "face", "laptop", "phone", "cell phone", 
        "cup", "bottle", "book", "keyboard", "mouse", 
        "tv", "monitor", "remote", "clock", "chair"
    }
    
    def __init__(self, model_path: str = None):
        _lazy_load()
        
        self.model = None
        self.model_path = model_path or Path("yolo26n.pt")
        self.is_ready = False
        self.last_detections: List[DetectedObject] = []
        self.detection_cache_time = 0
        self.cache_duration = 0.5  # Cache for 500ms
        
    def load(self) -> bool:
        """Load the YOLO26 model."""
        if YOLO is None:
            logger.warning("YOLO not available.")
            return False
        
        try:
            # Check for local model first
            if Path(self.model_path).exists():
                logger.info(f"Loading YOLO26 from: {self.model_path}")
                self.model = YOLO(str(self.model_path))
            else:
                # Download nano model (smallest)
                logger.info("Downloading yolo26n.pt...")
                self.model = YOLO("yolo26n.pt")
            
            self.is_ready = True
            logger.info("✅ YOLO26 loaded successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load YOLO26: {e}")
            return False
    
    def detect(self, frame: np.ndarray, 
               conf_threshold: float = 0.25,
               use_cache: bool = True) -> List[DetectedObject]:
        """
        Detect objects in the frame.
        
        Args:
            frame: BGR image from OpenCV
            conf_threshold: Minimum confidence to report
            use_cache: Use cached results if recent
            
        Returns:
            List of detected objects
        """
        if not self.is_ready or self.model is None:
            return []
        
        # Use cache if recent
        if use_cache and time.time() - self.detection_cache_time < self.cache_duration:
            return self.last_detections
        
        try:
            # Run inference
            results = self.model(frame, verbose=False, conf=conf_threshold)
            
            detections = []
            for result in results:
                if result.boxes is None:
                    continue
                    
                for box in result.boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Get class name and confidence
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    label = result.names[class_id]
                    
                    detections.append(DetectedObject(
                        label=label,
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                        center=(cx, cy)
                    ))
            
            # Update cache
            self.last_detections = detections
            self.detection_cache_time = time.time()
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def get_scene_description(self, detections: List[DetectedObject] = None) -> str:
        """
        Generate a natural language description of detected objects.
        """
        if detections is None:
            detections = self.last_detections
        
        if not detections:
            return "No objects detected."
        
        # Count objects
        counts: Dict[str, int] = {}
        for det in detections:
            counts[det.label] = counts.get(det.label, 0) + 1
        
        # Build description
        parts = []
        for label, count in sorted(counts.items(), key=lambda x: -x[1]):
            if label in self.IMPORTANT_OBJECTS:
                if count == 1:
                    parts.append(f"a {label}")
                else:
                    parts.append(f"{count} {label}s")
        
        if not parts:
            # Include non-important objects if no important ones
            for label, count in list(counts.items())[:3]:
                if count == 1:
                    parts.append(f"a {label}")
                else:
                    parts.append(f"{count} {label}s")
        
        if not parts:
            return "Various objects visible."
        
        if len(parts) == 1:
            return f"I can see {parts[0]}."
        elif len(parts) == 2:
            return f"I can see {parts[0]} and {parts[1]}."
        else:
            return f"I can see {', '.join(parts[:-1])}, and {parts[-1]}."
    
    def get_important_detections(self) -> List[DetectedObject]:
        """Get only important objects (for ZARA to focus on)."""
        return [
            det for det in self.last_detections 
            if det.label.lower() in self.IMPORTANT_OBJECTS
        ]
    
    def is_person_present(self) -> bool:
        """Quick check if a person is in frame."""
        return any(det.label == "person" for det in self.last_detections)
    
    def get_status(self) -> Dict:
        """Get detector status."""
        return {
            "ready": self.is_ready,
            "model": str(self.model_path),
            "last_detection_count": len(self.last_detections),
            "cache_age_ms": int((time.time() - self.detection_cache_time) * 1000)
        }


if __name__ == "__main__":
    import cv2
    logging.basicConfig(level=logging.INFO)
    
    detector = YOLO26Detector()
    detector.load()
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        detections = detector.detect(frame)
        desc = detector.get_scene_description(detections)
        print(f"Scene: {desc}")
        
        # Draw boxes
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{det.label} {det.confidence:.2f}", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow("YOLO26 Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()
