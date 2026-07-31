"""
ZARA Proactive Environmental Awareness v1.0
=============================================
Unified perception system that combines:
- Vision (objects, scene understanding)
- Gaze analysis (micro-expressions, emotions, fatigue)
- Depth mapping (spatial awareness)
- Room context (activity, time of day, environment type)

This enables ZARA to PROACTIVELY respond to:
- User appearing tired → "You look tired, should we take a break?"
- Room getting dark → "It's getting dark, want me to adjust lights?"
- Detecting work context → "I see you're coding, want some focus music?"
- Noticing emotions → "You seem stressed, want to talk about it?"
"""

import logging
import threading
import time
import json
import numpy as np
import cv2
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_AWARENESS")


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class RoomType(Enum):
    """Detected room/environment types."""
    UNKNOWN = "unknown"
    BEDROOM = "bedroom"
    OFFICE = "office"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    OUTDOOR = "outdoor"
    VEHICLE = "vehicle"


class ActivityType(Enum):
    """Detected user activities."""
    IDLE = "idle"
    WORKING = "working"          # At computer, typing
    READING = "reading"          # Book/document
    CONVERSING = "conversing"    # Multiple faces
    EATING = "eating"
    EXERCISING = "exercising"
    RESTING = "resting"          # Eyes closed, relaxed
    GAMING = "gaming"
    WATCHING = "watching"        # Passive viewing


class LightingCondition(Enum):
    """Lighting conditions."""
    DARK = "dark"
    DIM = "dim"
    NORMAL = "normal"
    BRIGHT = "bright"
    HARSH = "harsh"


class TimeContext(Enum):
    """Time-of-day context."""
    LATE_NIGHT = "late_night"    # 00:00-05:00
    EARLY_MORNING = "early_morning"  # 05:00-08:00
    MORNING = "morning"          # 08:00-12:00
    AFTERNOON = "afternoon"      # 12:00-17:00
    EVENING = "evening"          # 17:00-21:00
    NIGHT = "night"              # 21:00-24:00


# ═══════════════════════════════════════════════════════════════════════════
# DETECTED OBJECTS
# ═══════════════════════════════════════════════════════════════════════════

class ObjectCategory(Enum):
    """High-level object categories."""
    PERSON = "person"
    FACE = "face"
    ELECTRONIC = "electronic"
    FURNITURE = "furniture"
    FOOD = "food"
    DRINK = "drink"
    BOOK = "book"
    ANIMAL = "animal"
    PLANT = "plant"
    VEHICLE = "vehicle"
    TOOL = "tool"


@dataclass
class DetectedObject:
    """A detected object in the scene."""
    label: str
    category: ObjectCategory
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    center: Tuple[int, int]


# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class UserState:
    """Current state of the user."""
    is_present: bool = False
    face_visible: bool = False
    emotion: str = "neutral"
    attention_score: float = 1.0  # 0-1, how focused
    fatigue_level: float = 0.0    # 0-1, how tired
    is_drowsy: bool = False
    is_looking_at_camera: bool = False
    micro_expressions: List[str] = field(default_factory=list)
    blink_rate: float = 0.0
    head_pose: Tuple[float, float, float] = (0, 0, 0)


@dataclass
class EnvironmentState:
    """Current state of the environment."""
    room_type: RoomType = RoomType.UNKNOWN
    lighting: LightingCondition = LightingCondition.NORMAL
    motion_level: float = 0.0      # 0-1, how much movement
    noise_level: float = 0.0       # 0-1, ambient noise (if audio available)
    people_count: int = 0
    dominant_colors: List[str] = field(default_factory=list)


@dataclass
class ObjectContext:
    """Objects detected in the scene."""
    objects: List[DetectedObject] = field(default_factory=list)
    has_electronics: bool = False
    has_food_drink: bool = False
    has_books: bool = False
    has_animals: bool = False
    has_plants: bool = False
    scene_description: str = ""


@dataclass
class EnvironmentalContext:
    """Complete environmental awareness context."""
    timestamp: float = 0.0
    time_context: TimeContext = TimeContext.MORNING
    
    # User state
    user: UserState = field(default_factory=UserState)
    
    # Environment
    environment: EnvironmentState = field(default_factory=EnvironmentState)
    
    # Objects
    objects: ObjectContext = field(default_factory=ObjectContext)
    
    # Activity
    activity: ActivityType = ActivityType.IDLE
    activity_duration_seconds: float = 0.0
    
    # Proactive triggers
    needs_attention: bool = False
    suggested_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "time_context": self.time_context.value,
            "user": {
                "is_present": self.user.is_present,
                "emotion": self.user.emotion,
                "attention_score": self.user.attention_score,
                "fatigue_level": self.user.fatigue_level,
                "is_drowsy": self.user.is_drowsy,
                "micro_expressions": self.user.micro_expressions
            },
            "environment": {
                "room_type": self.environment.room_type.value,
                "lighting": self.environment.lighting.value,
                "motion_level": self.environment.motion_level,
                "people_count": self.environment.people_count
            },
            "activity": self.activity.value,
            "needs_attention": self.needs_attention,
            "suggested_actions": self.suggested_actions
        }


# ═══════════════════════════════════════════════════════════════════════════
# OBJECT DETECTOR (YOLO-based)
# ═══════════════════════════════════════════════════════════════════════════

class ObjectDetector:
    """
    Real-time object detection using YOLO or fallback to OpenCV DNN.
    Maps detected objects to semantic categories.
    """
    
    # COCO class mappings to our categories
    COCO_TO_CATEGORY = {
        # People
        0: ("person", ObjectCategory.PERSON),
        # Vehicles
        1: ("bicycle", ObjectCategory.VEHICLE),
        2: ("car", ObjectCategory.VEHICLE),
        3: ("motorcycle", ObjectCategory.VEHICLE),
        5: ("bus", ObjectCategory.VEHICLE),
        7: ("truck", ObjectCategory.VEHICLE),
        # Animals
        14: ("bird", ObjectCategory.ANIMAL),
        15: ("cat", ObjectCategory.ANIMAL),
        16: ("dog", ObjectCategory.ANIMAL),
        17: ("horse", ObjectCategory.ANIMAL),
        # Furniture
        56: ("chair", ObjectCategory.FURNITURE),
        57: ("couch", ObjectCategory.FURNITURE),
        58: ("potted plant", ObjectCategory.PLANT),
        59: ("bed", ObjectCategory.FURNITURE),
        60: ("dining table", ObjectCategory.FURNITURE),
        61: ("toilet", ObjectCategory.FURNITURE),
        # Electronics
        62: ("tv", ObjectCategory.ELECTRONIC),
        63: ("laptop", ObjectCategory.ELECTRONIC),
        64: ("mouse", ObjectCategory.ELECTRONIC),
        65: ("remote", ObjectCategory.ELECTRONIC),
        66: ("keyboard", ObjectCategory.ELECTRONIC),
        67: ("cell phone", ObjectCategory.ELECTRONIC),
        # Kitchen/Food
        39: ("bottle", ObjectCategory.DRINK),
        40: ("wine glass", ObjectCategory.DRINK),
        41: ("cup", ObjectCategory.DRINK),
        42: ("fork", ObjectCategory.TOOL),
        43: ("knife", ObjectCategory.TOOL),
        44: ("spoon", ObjectCategory.TOOL),
        45: ("bowl", ObjectCategory.FOOD),
        46: ("banana", ObjectCategory.FOOD),
        47: ("apple", ObjectCategory.FOOD),
        48: ("sandwich", ObjectCategory.FOOD),
        49: ("orange", ObjectCategory.FOOD),
        50: ("broccoli", ObjectCategory.FOOD),
        51: ("carrot", ObjectCategory.FOOD),
        52: ("hot dog", ObjectCategory.FOOD),
        53: ("pizza", ObjectCategory.FOOD),
        54: ("donut", ObjectCategory.FOOD),
        55: ("cake", ObjectCategory.FOOD),
        # Books
        73: ("book", ObjectCategory.BOOK),
    }
    
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.last_detection: List[DetectedObject] = []
        self.detection_interval = 0.5  # seconds
        self.last_detection_time = 0
        self.model_name = "unknown"
        
        # Try to load YOLO
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model - prefers YOLO26 (latest) for edge optimization."""
        try:
            from ultralytics import YOLO
            
            # Try models in order of preference (newest first)
            # YOLO26 = Latest edge-optimized, NMS-free, improved small objects
            # YOLO11 = Previous generation
            # YOLOv8 = Fallback
            model_priorities = [
                ("yolo26n.pt", "YOLO26n (Edge-Optimized)"),
                ("yolo11n.pt", "YOLO11n"),
                ("yolov8n.pt", "YOLOv8n (Fallback)"),
            ]
            
            for model_file, model_desc in model_priorities:
                try:
                    self.model = YOLO(model_file)
                    self.model_name = model_desc
                    self.is_ready = True
                    logger.info(f"🎯 Object Detector: {model_desc} loaded")
                    return
                except Exception:
                    continue
            
            # If all else fails, use default
            self.model = YOLO("yolov8n.pt")
            self.model_name = "YOLOv8n (Default)"
            self.is_ready = True
            logger.info(f"🎯 Object Detector: {self.model_name} loaded")
            
        except Exception as e:
            logger.warning(f"YOLO not available: {e}. Object detection disabled.")
            self.is_ready = False
    
    def detect(self, frame: np.ndarray) -> List[DetectedObject]:
        """Detect objects in frame."""
        now = time.time()
        
        # Rate limiting
        if now - self.last_detection_time < self.detection_interval:
            return self.last_detection
        
        self.last_detection_time = now
        
        if not self.is_ready or self.model is None:
            return []
        
        try:
            # Run YOLO inference
            results = self.model(frame, verbose=False, conf=0.3)
            
            objects = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls_id in self.COCO_TO_CATEGORY:
                        label, category = self.COCO_TO_CATEGORY[cls_id]
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        obj = DetectedObject(
                            label=label,
                            category=category,
                            confidence=conf,
                            bbox=(x1, y1, x2-x1, y2-y1),
                            center=((x1+x2)//2, (y1+y2)//2)
                        )
                        objects.append(obj)
            
            self.last_detection = objects
            return objects
            
        except Exception as e:
            logger.debug(f"Detection error: {e}")
            return self.last_detection


# ═══════════════════════════════════════════════════════════════════════════
# ROOM CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════

class RoomClassifier:
    """
    Classifies the current room/environment based on detected objects
    and scene features.
    """
    
    # Object patterns for room classification
    ROOM_PATTERNS = {
        RoomType.BEDROOM: ["bed", "pillow", "blanket"],
        RoomType.OFFICE: ["laptop", "keyboard", "mouse", "monitor", "desk"],
        RoomType.LIVING_ROOM: ["couch", "tv", "remote", "sofa"],
        RoomType.KITCHEN: ["bottle", "cup", "fork", "knife", "spoon", "bowl"],
        RoomType.OUTDOOR: ["car", "bicycle", "bird", "tree"],
        RoomType.VEHICLE: ["car", "steering wheel", "seatbelt"],
    }
    
    def __init__(self):
        self.room_history: deque = deque(maxlen=30)  # 30 frames for stability
        self.current_room = RoomType.UNKNOWN
    
    def classify(self, objects: List[DetectedObject], 
                 lighting: LightingCondition) -> RoomType:
        """Classify room based on objects."""
        object_labels = [obj.label for obj in objects]
        
        # Score each room type
        scores = {}
        for room_type, patterns in self.ROOM_PATTERNS.items():
            score = sum(1 for p in patterns if p in object_labels)
            if score > 0:
                scores[room_type] = score
        
        # Get highest scoring room
        if scores:
            detected_room = max(scores, key=scores.get)
        else:
            detected_room = RoomType.UNKNOWN
        
        # Add to history for stability
        self.room_history.append(detected_room)
        
        # Return most common in history
        from collections import Counter
        room_counts = Counter(self.room_history)
        self.current_room = room_counts.most_common(1)[0][0]
        
        return self.current_room


# ═══════════════════════════════════════════════════════════════════════════
# ACTIVITY INFERRER
# ═══════════════════════════════════════════════════════════════════════════

class ActivityInferrer:
    """
    Infers user activity from objects, gaze, and motion.
    """
    
    def __init__(self):
        self.current_activity = ActivityType.IDLE
        self.activity_start_time = time.time()
        self.activity_history: deque = deque(maxlen=60)
    
    def infer(self, objects: List[DetectedObject], 
              user_state: UserState,
              motion_level: float) -> Tuple[ActivityType, float]:
        """
        Infer activity and return (activity, duration_seconds).
        """
        object_labels = set(obj.label for obj in objects)
        
        # Determine activity
        activity = ActivityType.IDLE
        
        # Working - electronics visible + focused
        if any(l in object_labels for l in ["laptop", "keyboard", "mouse"]):
            if user_state.attention_score > 0.5:
                activity = ActivityType.WORKING
        
        # Reading
        if "book" in object_labels and user_state.is_looking_at_camera == False:
            activity = ActivityType.READING
        
        # Gaming - keyboard/mouse + high motion + focused
        if "keyboard" in object_labels and motion_level > 0.3:
            if user_state.attention_score > 0.7:
                activity = ActivityType.GAMING
        
        # Eating/Drinking
        if any(l in object_labels for l in ["cup", "bottle", "fork", "spoon", "bowl"]):
            activity = ActivityType.EATING
        
        # Conversing - multiple people
        people_count = sum(1 for obj in objects if obj.category == ObjectCategory.PERSON)
        if people_count > 1:
            activity = ActivityType.CONVERSING
        
        # Resting - low attention, drowsy
        if user_state.is_drowsy or user_state.fatigue_level > 0.7:
            activity = ActivityType.RESTING
        
        # Watching - low motion, face visible, eyes open
        if motion_level < 0.1 and user_state.face_visible and not user_state.is_drowsy:
            if "tv" in object_labels:
                activity = ActivityType.WATCHING
        
        # Update activity tracking
        if activity != self.current_activity:
            self.current_activity = activity
            self.activity_start_time = time.time()
        
        duration = time.time() - self.activity_start_time
        
        return activity, duration


# ═══════════════════════════════════════════════════════════════════════════
# PROACTIVE TRIGGER ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ProactiveTriggerEngine:
    """
    Generates proactive suggestions based on context.
    """
    
    def __init__(self):
        self.last_suggestions: Dict[str, float] = {}  # type -> last_time
        self.suggestion_cooldown = 300  # 5 minutes between same suggestions
    
    def generate_triggers(self, context: EnvironmentalContext) -> List[str]:
        """Generate proactive suggestions."""
        suggestions = []
        now = time.time()
        
        # Fatigue detection
        if context.user.fatigue_level > 0.6:
            if self._can_suggest("fatigue", now):
                suggestions.append("You look tired. Want to take a 5-minute break?")
        
        # Drowsiness warning
        if context.user.is_drowsy:
            if self._can_suggest("drowsy", now):
                suggestions.append("You seem drowsy. Maybe stretch or get some fresh air?")
        
        # Stress detection
        if context.user.emotion in ["stressed", "angry"]:
            if self._can_suggest("stress", now):
                suggestions.append("You seem stressed. Want me to play some calming music?")
        
        # Dark room warning
        if context.environment.lighting == LightingCondition.DARK:
            if context.time_context not in [TimeContext.LATE_NIGHT, TimeContext.NIGHT]:
                if self._can_suggest("lighting", now):
                    suggestions.append("It's quite dark. Should I suggest turning on lights?")
        
        # Late night working
        if context.time_context == TimeContext.LATE_NIGHT:
            if context.activity == ActivityType.WORKING:
                if self._can_suggest("late_work", now):
                    suggestions.append("It's very late. Consider wrapping up for the night?")
        
        # Long work session
        if context.activity == ActivityType.WORKING:
            if context.activity_duration_seconds > 7200:  # 2 hours
                if self._can_suggest("work_break", now):
                    hours = context.activity_duration_seconds / 3600
                    suggestions.append(f"You've been working for {hours:.1f} hours. Time for a break?")
        
        # Focus enhancement
        if context.user.attention_score < 0.4:
            if context.activity == ActivityType.WORKING:
                if self._can_suggest("focus", now):
                    suggestions.append("Seems like focus is drifting. Want some focus music?")
        
        # Happy observation
        if context.user.emotion == "happy":
            if self._can_suggest("happy", now):
                suggestions.append("You seem to be in a good mood! That's wonderful!")
        
        # Eating reminder
        if context.time_context == TimeContext.AFTERNOON:
            if context.activity == ActivityType.WORKING:
                if not context.objects.has_food_drink:
                    if self._can_suggest("lunch", now):
                        suggestions.append("It's afternoon - have you had lunch yet?")
        
        return suggestions
    
    def _can_suggest(self, suggestion_type: str, now: float) -> bool:
        """Check if we can make this suggestion (cooldown)."""
        last = self.last_suggestions.get(suggestion_type, 0)
        if now - last > self.suggestion_cooldown:
            self.last_suggestions[suggestion_type] = now
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════
# ENVIRONMENTAL AWARENESS ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class EnvironmentalAwareness:
    """
    Main environmental awareness engine.
    Combines all perception systems into unified context.
    """
    
    def __init__(self):
        # Vision system
        self._vision = None
        self._gaze = None
        
        # Sub-systems
        self.object_detector = ObjectDetector()
        self.room_classifier = RoomClassifier()
        self.activity_inferrer = ActivityInferrer()
        self.trigger_engine = ProactiveTriggerEngine()
        
        # State
        self.is_running = False
        self.update_thread = None
        self.current_context = EnvironmentalContext()
        self.context_history: deque = deque(maxlen=100)
        self.context_callbacks: List[Callable] = []
        
        # Timing
        self.update_interval = 0.5  # Update every 500ms
        self.last_update = 0
        
        # Persistence
        self.state_file = Path("memory/awareness_state.json")
        
        logger.info("🌍 Environmental Awareness Engine initialized")
    
    def _get_vision(self):
        """Get vision system lazily."""
        if self._vision is None:
            try:
                from eyes.vision_core import VisionSystem
                self._vision = VisionSystem()
            except Exception as e:
                logger.warning(f"Vision system unavailable: {e}")
        return self._vision
    
    def _get_gaze(self):
        """Get gaze analyzer lazily."""
        if self._gaze is None:
            try:
                from eyes.gaze_analyzer import GazeAnalyzer
                self._gaze = GazeAnalyzer()
            except Exception as e:
                logger.warning(f"Gaze analyzer unavailable: {e}")
        return self._gaze
    
    def start(self):
        """Start continuous awareness updates."""
        if self.is_running:
            return
        
        # Start vision
        vision = self._get_vision()
        if vision:
            vision.start()
        
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("🌍 Environmental Awareness started")
    
    def stop(self):
        """Stop awareness updates."""
        self.is_running = False
        
        # Stop vision
        if self._vision:
            self._vision.stop()
        
        if self.update_thread:
            self.update_thread.join(timeout=2)
        
        logger.info("🌍 Environmental Awareness stopped")
    
    def _update_loop(self):
        """Continuous context update loop."""
        while self.is_running:
            try:
                now = time.time()
                if now - self.last_update >= self.update_interval:
                    self._update_context()
                    self.last_update = now
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Awareness update error: {e}")
    
    def _update_context(self):
        """Update environmental context."""
        context = EnvironmentalContext(timestamp=time.time())
        
        # Time context
        context.time_context = self._get_time_context()
        
        # Get frame from vision
        frame = None
        vision = self._get_vision()
        if vision:
            frame = vision.get_frame()
        
        if frame is not None:
            # Analyze user (gaze, emotion)
            gaze = self._get_gaze()
            if gaze:
                gaze_data = gaze.analyze(frame)
                if gaze_data:
                    context.user = UserState(
                        is_present=True,
                        face_visible=True,
                        emotion=gaze_data.estimated_emotion.value if hasattr(gaze_data.estimated_emotion, 'value') else str(gaze_data.estimated_emotion),
                        attention_score=gaze_data.attention_score,
                        fatigue_level=gaze_data.fatigue_level,
                        is_drowsy=gaze_data.is_drowsy,
                        is_looking_at_camera=gaze_data.looking_at_screen,
                        micro_expressions=gaze_data.micro_expressions,
                        blink_rate=gaze_data.blink_rate,
                        head_pose=gaze_data.head_pose
                    )
            
            # Detect objects
            detected_objects = self.object_detector.detect(frame)
            context.objects.objects = detected_objects
            
            # Categorize objects
            for obj in detected_objects:
                if obj.category == ObjectCategory.ELECTRONIC:
                    context.objects.has_electronics = True
                elif obj.category in [ObjectCategory.FOOD, ObjectCategory.DRINK]:
                    context.objects.has_food_drink = True
                elif obj.category == ObjectCategory.BOOK:
                    context.objects.has_books = True
                elif obj.category == ObjectCategory.ANIMAL:
                    context.objects.has_animals = True
                elif obj.category == ObjectCategory.PLANT:
                    context.objects.has_plants = True
            
            # Lighting analysis
            context.environment.lighting = self._analyze_lighting(frame)
            
            # Motion analysis
            context.environment.motion_level = self._analyze_motion(frame)
            
            # People count
            context.environment.people_count = sum(
                1 for obj in detected_objects 
                if obj.category == ObjectCategory.PERSON
            )
            context.user.is_present = context.environment.people_count > 0
            
            # Room classification
            context.environment.room_type = self.room_classifier.classify(
                detected_objects, context.environment.lighting
            )
            
            # Activity inference
            context.activity, context.activity_duration_seconds = self.activity_inferrer.infer(
                detected_objects, context.user, context.environment.motion_level
            )
        
        # Generate proactive triggers
        suggestions = self.trigger_engine.generate_triggers(context)
        context.suggested_actions = suggestions
        context.needs_attention = len(suggestions) > 0
        
        # Update current context
        self.current_context = context
        self.context_history.append(context)
        
        # Notify callbacks
        if context.needs_attention:
            for callback in self.context_callbacks:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def _get_time_context(self) -> TimeContext:
        """Get current time context."""
        hour = datetime.now().hour
        
        if 0 <= hour < 5:
            return TimeContext.LATE_NIGHT
        elif 5 <= hour < 8:
            return TimeContext.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeContext.MORNING
        elif 12 <= hour < 17:
            return TimeContext.AFTERNOON
        elif 17 <= hour < 21:
            return TimeContext.EVENING
        else:
            return TimeContext.NIGHT
    
    def _analyze_lighting(self, frame: np.ndarray) -> LightingCondition:
        """Analyze lighting from frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        if brightness < 40:
            return LightingCondition.DARK
        elif brightness < 80:
            return LightingCondition.DIM
        elif brightness < 170:
            return LightingCondition.NORMAL
        elif brightness < 220:
            return LightingCondition.BRIGHT
        else:
            return LightingCondition.HARSH
    
    def _analyze_motion(self, frame: np.ndarray) -> float:
        """Analyze motion level 0-1."""
        if not hasattr(self, '_prev_gray') or self._prev_gray is None:
            self._prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return 0.0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(self._prev_gray, gray)
        motion = np.sum(diff) / (frame.shape[0] * frame.shape[1] * 255)
        
        self._prev_gray = gray
        return min(1.0, motion * 10)  # Normalize
    
    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def get_context(self) -> EnvironmentalContext:
        """Get current environmental context."""
        return self.current_context
    
    def get_user_state(self) -> UserState:
        """Get current user state."""
        return self.current_context.user
    
    def get_suggestions(self) -> List[str]:
        """Get current proactive suggestions."""
        return self.current_context.suggested_actions
    
    def add_callback(self, callback: Callable[[EnvironmentalContext], None]):
        """Add callback for context updates with suggestions."""
        self.context_callbacks.append(callback)
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary."""
        ctx = self.current_context
        
        lines = []
        lines.append(f"Time: {ctx.time_context.value}")
        
        if ctx.user.is_present:
            lines.append(f"User: {ctx.user.emotion}, attention {ctx.user.attention_score:.0%}")
            if ctx.user.fatigue_level > 0.3:
                lines.append(f"  Fatigue: {ctx.user.fatigue_level:.0%}")
            if ctx.user.micro_expressions:
                lines.append(f"  Micro-expressions: {', '.join(ctx.user.micro_expressions)}")
        else:
            lines.append("User: Not visible")
        
        lines.append(f"Room: {ctx.environment.room_type.value}, {ctx.environment.lighting.value}")
        lines.append(f"Activity: {ctx.activity.value} ({ctx.activity_duration_seconds/60:.1f} min)")
        
        if ctx.objects.objects:
            obj_names = [o.label for o in ctx.objects.objects[:5]]
            lines.append(f"Objects: {', '.join(obj_names)}")
        
        if ctx.suggested_actions:
            lines.append(f"💡 {ctx.suggested_actions[0]}")
        
        return "\n".join(lines)
    
    def one_shot_analyze(self, frame: np.ndarray = None) -> EnvironmentalContext:
        """Perform single-shot analysis without continuous updates."""
        if frame is None:
            vision = self._get_vision()
            if vision:
                vision.start()
                time.sleep(0.5)
                frame = vision.get_frame()
                vision.stop()
        
        if frame is None:
            return EnvironmentalContext()
        
        # Perform all analysis
        self._update_context()
        return self.current_context


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_awareness = None

def get_environmental_awareness() -> EnvironmentalAwareness:
    """Get the global environmental awareness instance."""
    global _awareness
    if _awareness is None:
        _awareness = EnvironmentalAwareness()
    return _awareness


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🌍 ZARA Environmental Awareness v1.0\n")
    print("=" * 60)
    
    awareness = EnvironmentalAwareness()
    
    # Test time context
    print(f"\n⏰ Time Context: {awareness._get_time_context().value}")
    
    # Test object detector
    print(f"\n🎯 Object Detector: {'Ready' if awareness.object_detector.is_ready else 'Not available'}")
    
    # Add callback
    def on_suggestion(ctx):
        print(f"💡 {ctx.suggested_actions}")
    
    awareness.add_callback(on_suggestion)
    
    # Start awareness
    print("\n🚀 Starting awareness (5 seconds)...")
    awareness.start()
    
    time.sleep(5)
    
    # Print context
    print("\n📊 Current Context:")
    print(awareness.get_context_summary())
    
    awareness.stop()
    
    print("\n" + "=" * 60)
    print("✅ Environmental Awareness ready!\n")
