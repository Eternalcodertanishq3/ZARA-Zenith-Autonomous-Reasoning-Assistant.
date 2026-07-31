"""
ZARA Avatar Renderer - Enhanced Procedural Animation
"""
import cv2
import numpy as np
import time
import math
import random
import logging
from pathlib import Path

logger = logging.getLogger("ZARA_AVATAR")

# Config import with fallback
try:
    from config import AVATAR_DIR
except ImportError:
    AVATAR_DIR = Path("avatar")


class AvatarRenderer:
    """
    Advanced Procedural Avatar Renderer.
    Enhanced with:
    - Smooth breathing animation
    - Emotion-based expressions
    - Hair/facial detail
    - Dynamic blush intensity
    - Smoother eye tracking
    """
    
    EXPRESSIONS = ["idle", "happy", "sad", "surprised", "serious", "blush", "sleepy"]
    
    def __init__(self):
        self.width = 512
        self.height = 512
        self.model_dir = AVATAR_DIR / "model_v3"
        self.images = {}
        self.current_state = "idle"
        self.current_expression = "idle"
        
        # Blink state
        self.last_blink = time.time()
        self.blink_interval = 3.0
        self.is_blinking = False
        self.blink_progress = 0.0  # 0-1 for smooth blink
        
        # Breathing state
        self.breath_phase = 0.0
        
        # Gaze tracking (smooth)
        self.target_look = (0, 0)
        self.current_look = (0.0, 0.0)
        self.last_look_change = time.time()
        
        # Emotion
        self.blush_intensity = 0.0  # 0-1
        
        # Ensure directory
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._load_assets()
        
        logger.info("Avatar Renderer initialized.")

    def _load_assets(self):
        """Load sprite assets if available."""
        states = ["idle", "blink", "open", "happy", "sad", "surprised"]
        self.assets_ready = True
        
        for s in states:
            path = self.model_dir / f"{s}.png"
            if path.exists():
                img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
                if img is not None:
                    self.images[s] = img
                    logger.debug(f"Loaded sprite: {s}")
            else:
                self.assets_ready = False
        
        if not self.assets_ready:
            logger.info("Sprites missing. Using procedural rendering.")

    def set_expression(self, expression: str):
        """Set the current expression."""
        if expression in self.EXPRESSIONS:
            self.current_expression = expression
            
            # Trigger blush for appropriate emotions
            if expression in ["blush", "happy"]:
                self.blush_intensity = 0.8
            elif expression == "surprised":
                self.blush_intensity = 0.3
            else:
                self.blush_intensity = max(0, self.blush_intensity - 0.1)

    def get_next_frame(self, audio_level: float = 0.0) -> np.ndarray:
        """Generate next animation frame."""
        now = time.time()
        
        # Update physics
        self._update_breathing(now)
        self._update_blink(now)
        self._update_gaze(now)
        self._decay_blush()
        
        # Render
        if self.assets_ready:
            frame = self._render_sprite(audio_level)
        else:
            frame = self._render_procedural(audio_level)
        
        # Apply breathing transform
        frame = self._apply_breathing(frame)
        
        return frame

    def _update_breathing(self, now: float):
        """Update breathing animation phase."""
        self.breath_phase = (now * 1.5) % (2 * math.pi)

    def _update_blink(self, now: float):
        """Update blink animation with smooth transition."""
        if not self.is_blinking:
            if now - self.last_blink > self.blink_interval:
                self.is_blinking = True
                self.last_blink = now
                self.blink_interval = random.uniform(2.5, 5.0)
                self.blink_progress = 0.0
        else:
            self.blink_progress += 0.15  # Speed of blink
            if self.blink_progress >= 1.0:
                self.is_blinking = False
                self.blink_progress = 0.0

    def _update_gaze(self, now: float):
        """Update smooth gaze movement."""
        if now - self.last_look_change > random.uniform(1.5, 4.0):
            self.target_look = (random.randint(-4, 4), random.randint(-3, 3))
            self.last_look_change = now
        
        # Smooth interpolation
        lerp = 0.1
        self.current_look = (
            self.current_look[0] + (self.target_look[0] - self.current_look[0]) * lerp,
            self.current_look[1] + (self.target_look[1] - self.current_look[1]) * lerp
        )

    def _decay_blush(self):
        """Gradually reduce blush intensity."""
        self.blush_intensity = max(0, self.blush_intensity - 0.005)

    def _apply_breathing(self, frame: np.ndarray) -> np.ndarray:
        """Apply breathing offset to frame."""
        offset_y = math.sin(self.breath_phase) * 4.0
        scale = 1.0 + math.sin(self.breath_phase) * 0.003
        
        # Translation matrix
        M = np.float32([[1, 0, 0], [0, 1, offset_y]])
        frame = cv2.warpAffine(frame, M, (self.width, self.height))
        
        return frame

    def _render_sprite(self, audio_level: float) -> np.ndarray:
        """Render from sprite assets."""
        # Select appropriate sprite
        if self.is_blinking and "blink" in self.images:
            key = "blink"
        elif audio_level > 0.05 and "open" in self.images:
            key = "open"
        elif self.current_expression in self.images:
            key = self.current_expression
        else:
            key = "idle"
        
        base = self.images.get(key, self.images.get("idle"))
        
        if base is None:
            return self._render_procedural(audio_level)
        
        # Resize if needed
        if base.shape[:2] != (self.height, self.width):
            base = cv2.resize(base, (self.width, self.height))
        
        # Handle alpha channel
        if base.shape[2] == 4:
            canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            canvas[:] = (25, 25, 30)
            alpha = base[:, :, 3] / 255.0
            for c in range(3):
                canvas[:, :, c] = base[:, :, c] * alpha + canvas[:, :, c] * (1 - alpha)
            return canvas
        
        return base[:, :, :3]

    def _render_procedural(self, audio_level: float) -> np.ndarray:
        """Render procedural anime face."""
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        canvas[:] = (25, 25, 30)  # Dark background
        
        cx, cy = self.width // 2, self.height // 2
        
        # Face shape (softer oval)
        face_color = (235, 218, 210)  # Warm skin tone
        cv2.ellipse(canvas, (cx, cy + 10), (140, 160), 0, 0, 360, face_color, -1)
        
        # Ears
        cv2.ellipse(canvas, (cx - 130, cy), (15, 25), 20, 0, 360, face_color, -1)
        cv2.ellipse(canvas, (cx + 130, cy), (15, 25), -20, 0, 360, face_color, -1)
        
        # Hair (simplified anime style)
        hair_color = (50, 30, 20)  # Dark brown
        # Top hair
        cv2.ellipse(canvas, (cx, cy - 100), (160, 100), 0, 180, 360, hair_color, -1)
        # Side bangs
        pts_left = np.array([[cx - 120, cy - 100], [cx - 160, cy + 20], [cx - 100, cy + 40], [cx - 100, cy - 50]])
        pts_right = np.array([[cx + 120, cy - 100], [cx + 160, cy + 20], [cx + 100, cy + 40], [cx + 100, cy - 50]])
        cv2.fillPoly(canvas, [pts_left], hair_color)
        cv2.fillPoly(canvas, [pts_right], hair_color)
        # Front bangs
        for i in range(-3, 4):
            x_offset = i * 30
            pt1 = (cx + x_offset - 20, cy - 120)
            pt2 = (cx + x_offset + 20, cy - 120)
            pt3 = (cx + x_offset, cy - 40 + abs(i) * 5)
            cv2.fillPoly(canvas, [np.array([pt1, pt2, pt3])], hair_color)
        
        # Blush (dynamic)
        if self.blush_intensity > 0:
            blush_alpha = int(self.blush_intensity * 120)
            blush_color = (blush_alpha, blush_alpha, 255)
            cv2.circle(canvas, (cx - 80, cy + 30), 20, blush_color, -1)
            cv2.circle(canvas, (cx + 80, cy + 30), 20, blush_color, -1)
        
        # Eyes
        eye_y = cy - 10
        look_x, look_y = int(self.current_look[0]), int(self.current_look[1])
        
        if self.is_blinking or self.current_expression == "sleepy":
            # Closed eyes
            progress = math.sin(self.blink_progress * math.pi) if self.is_blinking else 0.8
            squish = int(40 * (1 - progress))
            cv2.ellipse(canvas, (cx - 55, eye_y), (30, max(5, squish)), 0, 0, 180, (60, 50, 50), 3)
            cv2.ellipse(canvas, (cx + 55, eye_y), (30, max(5, squish)), 0, 0, 180, (60, 50, 50), 3)
        else:
            # Open eyes
            eye_white = (255, 255, 255)
            iris_color = (255, 130, 200) if self.current_expression == "happy" else (255, 120, 120)
            
            for side in [-1, 1]:
                ex = cx + side * 55
                
                # White
                cv2.ellipse(canvas, (ex, eye_y), (32, 42), 0, 0, 360, eye_white, -1)
                
                # Iris
                cv2.circle(canvas, (ex + look_x, eye_y + look_y), 18, iris_color, -1)
                cv2.circle(canvas, (ex + look_x, eye_y + look_y), 10, (150, 60, 60), -1)  # Pupil
                
                # Highlights
                cv2.circle(canvas, (ex - 8, eye_y - 12), 6, (255, 255, 255), -1)
                cv2.circle(canvas, (ex + 4, eye_y - 5), 3, (255, 255, 255), -1)
                
                # Top eyelid shadow
                cv2.ellipse(canvas, (ex, eye_y - 10), (35, 20), 0, 180, 360, (200, 180, 175), 3)
        
        # Eyebrows
        brow_y = eye_y - 55
        if self.current_expression == "sad":
            cv2.line(canvas, (cx - 80, brow_y + 10), (cx - 30, brow_y), (50, 40, 40), 4)
            cv2.line(canvas, (cx + 30, brow_y), (cx + 80, brow_y + 10), (50, 40, 40), 4)
        elif self.current_expression == "surprised":
            cv2.line(canvas, (cx - 80, brow_y - 10), (cx - 30, brow_y - 10), (50, 40, 40), 4)
            cv2.line(canvas, (cx + 30, brow_y - 10), (cx + 80, brow_y - 10), (50, 40, 40), 4)
        else:
            cv2.line(canvas, (cx - 80, brow_y), (cx - 30, brow_y - 5), (50, 40, 40), 4)
            cv2.line(canvas, (cx + 30, brow_y - 5), (cx + 80, brow_y), (50, 40, 40), 4)
        
        # Mouth
        mouth_y = cy + 65
        mouth_open = int(audio_level * 80)
        
        if self.current_expression == "happy" or mouth_open < 8:
            # Smile
            cv2.ellipse(canvas, (cx, mouth_y), (25, 12), 0, 0, 180, (80, 50, 50), 3)
        elif self.current_expression == "surprised":
            # O mouth
            cv2.ellipse(canvas, (cx, mouth_y + 5), (15, 20), 0, 0, 360, (100, 60, 60), -1)
        else:
            # Speaking
            cv2.ellipse(canvas, (cx, mouth_y), (25 + mouth_open // 4, 8 + mouth_open), 0, 0, 180, (100, 60, 60), -1)
        
        # Status overlay
        cv2.putText(canvas, f"ZARA v3.0 [{self.current_expression.upper()}]", 
                    (15, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 180, 80), 1)
        
        return canvas


if __name__ == "__main__":
    renderer = AvatarRenderer()
    
    while True:
        # Simulate audio
        audio = abs(math.sin(time.time() * 5)) * 0.5
        
        # Test expressions
        if int(time.time()) % 8 < 2:
            renderer.set_expression("happy")
        elif int(time.time()) % 8 < 4:
            renderer.set_expression("sad")
        elif int(time.time()) % 8 < 6:
            renderer.set_expression("surprised")
        else:
            renderer.set_expression("idle")
        
        frame = renderer.get_next_frame(audio)
        cv2.imshow("ZARA Avatar Test", frame)
        
        if cv2.waitKey(16) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
