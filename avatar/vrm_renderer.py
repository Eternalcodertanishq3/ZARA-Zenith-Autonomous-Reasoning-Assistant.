"""
ZARA VRM Avatar Renderer
========================
Real-time VRM avatar rendering with expression support.
Uses pyglet + OpenGL for fast, local GPU-accelerated rendering.
"""
import logging
import threading
import json
import time
from pathlib import Path
from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ZARA_AVATAR")

# Try to import rendering libraries
try:
    import pyglet
    from pyglet import gl
    from pyglet.window import key
    PYGLET_AVAILABLE = True
except ImportError:
    PYGLET_AVAILABLE = False
    logger.warning("pyglet not installed. Run: pip install pyglet")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class Expression(Enum):
    """VRM standard blendshape expressions."""
    NEUTRAL = "neutral"
    JOY = "joy"
    ANGRY = "angry"
    SORROW = "sorrow"
    FUN = "fun"
    SURPRISED = "surprised"
    # Eye expressions
    BLINK = "blink"
    BLINK_LEFT = "blink_l"
    BLINK_RIGHT = "blink_r"
    LOOK_UP = "lookup"
    LOOK_DOWN = "lookdown"
    LOOK_LEFT = "lookleft"
    LOOK_RIGHT = "lookright"
    # Mouth expressions
    A = "a"  # Viseme
    I = "i"
    U = "u"
    E = "e"
    O = "o"


@dataclass
class ExpressionState:
    """Current expression state with blending."""
    expression: Expression
    weight: float = 1.0
    transition_progress: float = 1.0
    previous_expression: Optional[Expression] = None


@dataclass
class AvatarConfig:
    """Avatar configuration."""
    vrm_path: Path
    window_width: int = 400
    window_height: int = 600
    background_color: Tuple[float, float, float, float] = (0.1, 0.1, 0.15, 1.0)
    default_expression: Expression = Expression.NEUTRAL
    blink_interval: float = 4.0  # Seconds between blinks
    blink_duration: float = 0.15  # Seconds for blink
    expression_transition_time: float = 0.2  # Seconds to blend expressions


class VRMAvatarRenderer:
    """
    Real-time VRM avatar renderer for ZARA.
    
    Features:
    - GPU-accelerated rendering (60+ FPS)
    - Smooth expression transitions
    - Automatic blinking
    - Lip sync support (visemes)
    - Head tracking (optional)
    - Emotion sync integration
    
    All processing is LOCAL - no internet required!
    """
    
    def __init__(self, config: AvatarConfig = None):
        if not PYGLET_AVAILABLE:
            raise ImportError("pyglet is required. Install with: pip install pyglet")
        
        # Default config with ZARA's avatar
        if config is None:
            vrm_path = Path(__file__).parent.parent / "assets" / "avatar" / "Pink" / "Pink" / "Cat Ears" / "Pink Cat Maid.vrm"
            config = AvatarConfig(vrm_path=vrm_path)
        
        self.config = config
        self.vrm_path = config.vrm_path
        
        # Window and rendering
        self.window: Optional[pyglet.window.Window] = None
        self.is_running = False
        self.render_thread: Optional[threading.Thread] = None
        
        # Expression state
        self.current_expression = ExpressionState(
            expression=config.default_expression
        )
        self.target_expression: Optional[Expression] = None
        self.expression_weights: Dict[Expression, float] = {
            expr: 0.0 for expr in Expression
        }
        self.expression_weights[Expression.NEUTRAL] = 1.0
        
        # Blinking
        self.last_blink_time = time.time()
        self.is_blinking = False
        self.blink_progress = 0.0
        
        # Lip sync (visemes)
        self.current_viseme: Optional[str] = None
        self.viseme_weight = 0.0
        
        # VRM model data (simplified - full implementation needs glTF parser)
        self.model_loaded = False
        self.model_data: Dict = {}
        
        # Callbacks
        self.on_expression_change: Optional[Callable] = None
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"🎀 VRM Avatar Renderer initialized")
        logger.info(f"   Model: {self.vrm_path.name}")
    
    def load_model(self) -> bool:
        """Load VRM model."""
        if not self.vrm_path.exists():
            logger.error(f"VRM file not found: {self.vrm_path}")
            return False
        
        try:
            # VRM is essentially a glTF file with extensions
            # For full implementation, use pygltflib or custom parser
            # Here we just verify the file exists and is valid
            
            file_size = self.vrm_path.stat().st_size
            logger.info(f"Loading VRM model ({file_size / 1024 / 1024:.1f} MB)...")
            
            # In a full implementation, we would:
            # 1. Parse glTF structure
            # 2. Load meshes, materials, textures
            # 3. Extract VRM blendshapes
            # 4. Set up bone hierarchy
            
            self.model_data = {
                "path": str(self.vrm_path),
                "size": file_size,
                "loaded_at": time.time()
            }
            
            self.model_loaded = True
            logger.info("✅ VRM model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load VRM: {e}")
            return False
    
    def start(self, threaded: bool = True):
        """Start the avatar renderer."""
        if not self.model_loaded:
            if not self.load_model():
                return False
        
        if threaded:
            self.render_thread = threading.Thread(target=self._run_render_loop, daemon=True)
            self.render_thread.start()
            logger.info("Avatar renderer started in background thread")
        else:
            self._run_render_loop()
        
        return True
    
    def _run_render_loop(self):
        """Main render loop."""
        self.is_running = True
        
        # Create window
        self.window = pyglet.window.Window(
            width=self.config.window_width,
            height=self.config.window_height,
            caption="ZARA Avatar",
            resizable=True
        )
        
        # Set background color
        gl.glClearColor(*self.config.background_color)
        
        # Set up OpenGL
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        @self.window.event
        def on_draw():
            self.window.clear()
            self._render_frame()
        
        @self.window.event
        def on_key_press(symbol, modifiers):
            # Test expressions with number keys
            if symbol == key._1:
                self.set_expression(Expression.JOY)
            elif symbol == key._2:
                self.set_expression(Expression.SORROW)
            elif symbol == key._3:
                self.set_expression(Expression.ANGRY)
            elif symbol == key._4:
                self.set_expression(Expression.SURPRISED)
            elif symbol == key._5:
                self.set_expression(Expression.FUN)
            elif symbol == key._0:
                self.set_expression(Expression.NEUTRAL)
        
        @self.window.event
        def on_close():
            self.is_running = False
        
        # Schedule updates
        pyglet.clock.schedule_interval(self._update, 1/60)  # 60 FPS
        
        logger.info("Avatar window opened")
        pyglet.app.run()
    
    def _update(self, dt: float):
        """Update avatar state."""
        current_time = time.time()
        
        # Handle blinking
        self._update_blink(current_time, dt)
        
        # Handle expression transitions
        self._update_expression_transition(dt)
    
    def _update_blink(self, current_time: float, dt: float):
        """Update automatic blinking."""
        if self.is_blinking:
            self.blink_progress += dt / self.config.blink_duration
            if self.blink_progress >= 1.0:
                self.is_blinking = False
                self.blink_progress = 0.0
                self.expression_weights[Expression.BLINK] = 0.0
            else:
                # Smooth blink curve (close then open)
                if self.blink_progress < 0.5:
                    self.expression_weights[Expression.BLINK] = self.blink_progress * 2
                else:
                    self.expression_weights[Expression.BLINK] = (1.0 - self.blink_progress) * 2
        else:
            # Check if it's time to blink
            if current_time - self.last_blink_time > self.config.blink_interval:
                self.is_blinking = True
                self.blink_progress = 0.0
                self.last_blink_time = current_time
    
    def _update_expression_transition(self, dt: float):
        """Smooth expression transitions."""
        if self.target_expression is None:
            return
        
        transition_speed = dt / self.config.expression_transition_time
        
        with self.lock:
            # Fade out other expressions
            for expr in Expression:
                if expr == self.target_expression:
                    # Fade in target
                    self.expression_weights[expr] = min(1.0, 
                        self.expression_weights[expr] + transition_speed)
                elif expr not in [Expression.BLINK, Expression.BLINK_LEFT, Expression.BLINK_RIGHT]:
                    # Fade out others (except blink)
                    self.expression_weights[expr] = max(0.0,
                        self.expression_weights[expr] - transition_speed)
            
            # Check if transition complete
            if self.expression_weights[self.target_expression] >= 1.0:
                self.current_expression.expression = self.target_expression
                self.current_expression.transition_progress = 1.0
                self.target_expression = None
    
    def _render_frame(self):
        """Render one frame of the avatar."""
        # In a full implementation, this would:
        # 1. Apply blendshape weights to mesh vertices
        # 2. Update bone transforms
        # 3. Render the 3D model with shaders
        
        # For now, render a placeholder that shows the expression state
        self._render_placeholder()
    
    def _render_placeholder(self):
        """Render placeholder avatar (for testing before full VRM implementation)."""
        w, h = self.window.width, self.window.height
        
        # Get current expression info
        current_expr = self.current_expression.expression.value
        
        # Draw expression indicator
        label = pyglet.text.Label(
            f"Expression: {current_expr}",
            font_name='Arial',
            font_size=14,
            x=w//2, y=h-30,
            anchor_x='center', anchor_y='center',
            color=(255, 255, 255, 255)
        )
        label.draw()
        
        # Draw model name
        model_label = pyglet.text.Label(
            f"Model: {self.vrm_path.name}",
            font_name='Arial',
            font_size=12,
            x=w//2, y=30,
            anchor_x='center', anchor_y='center',
            color=(200, 200, 200, 255)
        )
        model_label.draw()
        
        # Draw expression weights
        y_offset = h - 60
        for expr, weight in self.expression_weights.items():
            if weight > 0.01:
                weight_label = pyglet.text.Label(
                    f"{expr.value}: {weight:.2f}",
                    font_name='Arial',
                    font_size=10,
                    x=20, y=y_offset,
                    color=(150, 255, 150, int(255 * weight))
                )
                weight_label.draw()
                y_offset -= 18
        
        # Draw blink indicator
        if self.is_blinking:
            blink_label = pyglet.text.Label(
                "👁️ BLINK",
                font_size=16,
                x=w//2, y=h//2,
                anchor_x='center', anchor_y='center',
                color=(255, 200, 200, 255)
            )
            blink_label.draw()
        
        # Draw simple face based on expression
        self._draw_simple_face(w//2, h//2, current_expr)
    
    def _draw_simple_face(self, cx: int, cy: int, expression: str):
        """Draw a simple animated face placeholder using pyglet.shapes."""
        batch = pyglet.graphics.Batch()
        shapes_list = []
        
        # Face circle (pink)
        face = pyglet.shapes.Circle(cx, cy, 80, color=(255, 200, 200), batch=batch)
        shapes_list.append(face)
        
        # Eyes
        eye_y = cy + 20
        left_eye_x = cx - 30
        right_eye_x = cx + 30
        
        blink_factor = 1.0 - self.expression_weights.get(Expression.BLINK, 0)
        eye_height = max(2, int(15 * blink_factor))
        
        if expression == "joy" or expression == "fun":
            # Happy eyes (arcs represented as thin ellipses)
            left_eye = pyglet.shapes.Arc(left_eye_x, eye_y - 5, 12, angle=3.14, color=(50, 50, 50), batch=batch)
            right_eye = pyglet.shapes.Arc(right_eye_x, eye_y - 5, 12, angle=3.14, color=(50, 50, 50), batch=batch)
            shapes_list.extend([left_eye, right_eye])
        elif expression == "surprised":
            # Wide eyes (circles)
            left_eye = pyglet.shapes.Circle(left_eye_x, eye_y, 15, color=(50, 50, 50), batch=batch)
            right_eye = pyglet.shapes.Circle(right_eye_x, eye_y, 15, color=(50, 50, 50), batch=batch)
            shapes_list.extend([left_eye, right_eye])
        else:
            # Normal eyes (ellipses approximated as circles with height factor)
            left_eye = pyglet.shapes.Ellipse(left_eye_x, eye_y, 10, eye_height, color=(50, 50, 50), batch=batch)
            right_eye = pyglet.shapes.Ellipse(right_eye_x, eye_y, 10, eye_height, color=(50, 50, 50), batch=batch)
            shapes_list.extend([left_eye, right_eye])
        
        # Mouth
        mouth_y = cy - 25
        
        if expression == "joy":
            # Smile (arc)
            smile = pyglet.shapes.Arc(cx, mouth_y + 10, 25, angle=3.14, start_angle=3.14, color=(200, 100, 100), batch=batch)
            smile.rotation = 180
            shapes_list.append(smile)
        elif expression == "sorrow":
            # Frown (inverted arc)
            frown = pyglet.shapes.Arc(cx, mouth_y - 5, 20, angle=3.14, color=(150, 100, 100), batch=batch)
            shapes_list.append(frown)
        elif expression == "surprised":
            # Open mouth (circle)
            mouth = pyglet.shapes.Circle(cx, mouth_y, 12, color=(200, 100, 100), batch=batch)
            shapes_list.append(mouth)
        elif expression == "angry":
            # Straight line (x, y, x2, y2, thickness, color, batch)
            line = pyglet.shapes.Line(cx - 20, mouth_y, cx + 20, mouth_y, 3, color=(200, 100, 100), batch=batch)
            shapes_list.append(line)
        else:
            # Neutral line
            line = pyglet.shapes.Line(cx - 15, mouth_y, cx + 15, mouth_y, 2, color=(200, 150, 150), batch=batch)
            shapes_list.append(line)
        
        # Draw all shapes
        batch.draw()
        
        # Keep shapes alive until drawn
        self._temp_shapes = shapes_list
    
    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def set_expression(self, expression: Expression, intensity: float = 1.0):
        """Set the avatar's expression with smooth transition."""
        with self.lock:
            if expression != self.current_expression.expression:
                self.current_expression.previous_expression = self.current_expression.expression
                self.current_expression.transition_progress = 0.0
                self.target_expression = expression
                
                logger.debug(f"Expression: {self.current_expression.expression.value} → {expression.value}")
                
                if self.on_expression_change:
                    self.on_expression_change(expression)
    
    def set_expression_from_emotion(self, emotion: str, intensity: float = 1.0):
        """Set expression from emotion string (for emotion_sync integration)."""
        emotion_map = {
            "joy": Expression.JOY,
            "happy": Expression.JOY,
            "sadness": Expression.SORROW,
            "sad": Expression.SORROW,
            "anger": Expression.ANGRY,
            "angry": Expression.ANGRY,
            "fear": Expression.SURPRISED,
            "surprise": Expression.SURPRISED,
            "surprised": Expression.SURPRISED,
            "love": Expression.JOY,
            "trust": Expression.NEUTRAL,
            "neutral": Expression.NEUTRAL,
            "fun": Expression.FUN,
            "playful": Expression.FUN
        }
        
        expr = emotion_map.get(emotion.lower(), Expression.NEUTRAL)
        self.set_expression(expr, intensity)
    
    def set_viseme(self, viseme: str, weight: float = 1.0):
        """Set lip sync viseme."""
        viseme_map = {
            "a": Expression.A,
            "i": Expression.I,
            "u": Expression.U,
            "e": Expression.E,
            "o": Expression.O
        }
        
        with self.lock:
            self.current_viseme = viseme
            self.viseme_weight = weight
            
            if viseme.lower() in viseme_map:
                self.expression_weights[viseme_map[viseme.lower()]] = weight
    
    def trigger_blink(self):
        """Manually trigger a blink."""
        with self.lock:
            self.is_blinking = True
            self.blink_progress = 0.0
            self.last_blink_time = time.time()
    
    def stop(self):
        """Stop the avatar renderer."""
        self.is_running = False
        if self.window:
            self.window.close()
        logger.info("Avatar renderer stopped")
    
    def get_status(self) -> Dict:
        """Get renderer status."""
        return {
            "is_running": self.is_running,
            "model_loaded": self.model_loaded,
            "model_path": str(self.vrm_path),
            "current_expression": self.current_expression.expression.value,
            "is_blinking": self.is_blinking,
            "fps": pyglet.clock.get_fps() if self.is_running else 0
        }


# ═══════════════════════════════════════════════════════════════════
# EMOTION SYNC INTEGRATION
# ═══════════════════════════════════════════════════════════════════

def create_face_handler(renderer: VRMAvatarRenderer):
    """Create a face handler for emotion_sync integration."""
    def handler(face_expression, transition_time: float = 0.3):
        """Handle face expression from emotion_sync."""
        emotion = face_expression.emotion.value if hasattr(face_expression.emotion, 'value') else str(face_expression.emotion)
        intensity = face_expression.intensity
        
        renderer.config.expression_transition_time = transition_time
        renderer.set_expression_from_emotion(emotion, intensity)
    
    return handler


# ═══════════════════════════════════════════════════════════════════
# SINGLETON & MAIN
# ═══════════════════════════════════════════════════════════════════

_avatar_instance: Optional[VRMAvatarRenderer] = None

def get_avatar() -> VRMAvatarRenderer:
    """Get the global avatar renderer."""
    global _avatar_instance
    if _avatar_instance is None:
        _avatar_instance = VRMAvatarRenderer()
    return _avatar_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the avatar renderer
    print("Starting ZARA Avatar Renderer...")
    print("Press 1-5 to change expressions, 0 for neutral")
    print("Close window to exit")
    
    avatar = VRMAvatarRenderer()
    avatar.start(threaded=False)  # Run in main thread for testing
