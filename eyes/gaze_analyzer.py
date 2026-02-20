"""
ZARA Gaze & Micro-Expression Analyzer
Enhanced with fatigue detection, micro-expression tracking, and head pose estimation.
"""
import cv2
import numpy as np
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
from enum import Enum
from collections import deque

logger = logging.getLogger("ZARA_GAZE")

# Lazy import
mp = None
mp_face_mesh = None

def _lazy_load():
    global mp, mp_face_mesh
    if mp is None:
        try:
            import mediapipe as _mp
            mp = _mp
            # Handle different mediapipe versions
            if hasattr(mp, 'solutions'):
                mp_face_mesh = mp.solutions.face_mesh
            else:
                logger.warning("MediaPipe version incompatible (no solutions). Gaze disabled.")
                mp_face_mesh = None
        except (ImportError, AttributeError) as e:
            logger.warning(f"MediaPipe load failed: {e}")
            mp = None
            mp_face_mesh = None


class EmotionalState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    STRESSED = "stressed"
    FOCUSED = "focused"
    CONFUSED = "confused"
    EXCITED = "excited"
    TIRED = "tired"
    ANGRY = "angry"
    SURPRISED = "surprised"


@dataclass
class GazeData:
    """Comprehensive gaze analysis result."""
    looking_at_screen: bool
    eye_aspect_ratio: float
    blink_rate: float  # blinks per minute
    estimated_emotion: EmotionalState
    attention_score: float  # 0-1
    head_pose: Tuple[float, float, float]  # yaw, pitch, roll
    fatigue_level: float  # 0-1
    is_drowsy: bool
    micro_expressions: List[str] = field(default_factory=list)


class GazeAnalyzer:
    """
    Advanced gaze and micro-expression analyzer using MediaPipe Face Mesh.
    Enhanced with:
    - Head pose estimation (yaw, pitch, roll)
    - Fatigue/drowsiness detection
    - Micro-expression tracking
    - Emotion history for stability
    - PERCLOS (eye closure percentage) for drowsiness
    """
    
    # MediaPipe face mesh indices
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    LEFT_IRIS = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]
    
    # Head pose landmarks
    FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
    
    def __init__(self):
        _lazy_load()
        
        self.face_mesh = None
        self.is_active = False
        
        # Blink tracking
        self.blink_timestamps = deque(maxlen=100)
        self.ear_history = deque(maxlen=30)
        self.ear_threshold = 0.21
        self.was_eye_closed = False
        
        # PERCLOS tracking (Percentage of Eye Closure)
        self.perclos_window = deque(maxlen=300)  # ~10 seconds at 30fps
        
        # Emotion stability
        self.emotion_history = deque(maxlen=10)
        
        # Fatigue tracking
        self.yawn_timestamps = deque(maxlen=20)
        self.head_drop_count = 0
        
        self._initialize()
    
    def _initialize(self):
        """Initialize MediaPipe Face Mesh."""
        if mp_face_mesh is None:
            logger.warning("MediaPipe not installed. Gaze analysis disabled.")
            return
        
        try:
            self.face_mesh = mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.is_active = True
            logger.info("Gaze Analyzer initialized with MediaPipe.")
        except Exception as e:
            logger.error(f"Gaze init failed: {e}")
    
    def _calculate_ear(self, landmarks, eye_indices: List[int]) -> float:
        """Calculate Eye Aspect Ratio for blink/drowsiness detection."""
        def get_point(idx):
            return np.array([landmarks[idx].x, landmarks[idx].y])
        
        # Vertical distances
        v1 = np.linalg.norm(get_point(eye_indices[1]) - get_point(eye_indices[5]))
        v2 = np.linalg.norm(get_point(eye_indices[2]) - get_point(eye_indices[4]))
        
        # Horizontal distance
        h = np.linalg.norm(get_point(eye_indices[0]) - get_point(eye_indices[3]))
        
        return (v1 + v2) / (2.0 * h) if h > 0 else 0
    
    def _estimate_head_pose(self, landmarks, frame_shape: Tuple[int, int]) -> Tuple[float, float, float]:
        """
        Estimate head pose (yaw, pitch, roll) using key facial landmarks.
        """
        h, w = frame_shape[:2]
        
        # 3D model points (generic face model)
        model_points = np.array([
            (0.0, 0.0, 0.0),       # Nose tip
            (0.0, -330.0, -65.0),  # Chin
            (-225.0, 170.0, -135.0),  # Left eye corner
            (225.0, 170.0, -135.0),   # Right eye corner
            (-150.0, -150.0, -125.0), # Left mouth corner
            (150.0, -150.0, -125.0)   # Right mouth corner
        ], dtype=np.float64)
        
        # 2D image points
        image_points = np.array([
            (landmarks[1].x * w, landmarks[1].y * h),    # Nose tip
            (landmarks[152].x * w, landmarks[152].y * h), # Chin
            (landmarks[33].x * w, landmarks[33].y * h),   # Left eye
            (landmarks[263].x * w, landmarks[263].y * h), # Right eye
            (landmarks[61].x * w, landmarks[61].y * h),   # Left mouth
            (landmarks[291].x * w, landmarks[291].y * h)  # Right mouth
        ], dtype=np.float64)
        
        # Camera matrix (approximate)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        
        dist_coeffs = np.zeros((4, 1))
        
        try:
            success, rotation_vec, translation_vec = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs
            )
            
            if success:
                rotation_mat, _ = cv2.Rodrigues(rotation_vec)
                pose_mat = cv2.hconcat([rotation_mat, translation_vec])
                _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
                
                yaw = euler_angles[1, 0]
                pitch = euler_angles[0, 0]
                roll = euler_angles[2, 0]
                
                return (yaw, pitch, roll)
        except:
            pass
        
        return (0.0, 0.0, 0.0)
    
    def _detect_micro_expressions(self, landmarks) -> List[str]:
        """Detect subtle facial micro-expressions."""
        expressions = []
        
        # Eyebrow raise
        left_brow = landmarks[107]
        right_brow = landmarks[336]
        left_eye_top = landmarks[159]
        right_eye_top = landmarks[386]
        
        brow_raise = abs(left_brow.y - left_eye_top.y) + abs(right_brow.y - right_eye_top.y)
        if brow_raise > 0.08:
            expressions.append("eyebrow_raise")
        
        # Lip tightening
        top_lip = landmarks[13]
        bottom_lip = landmarks[14]
        lip_distance = abs(bottom_lip.y - top_lip.y)
        if lip_distance < 0.01:
            expressions.append("lip_press")
        
        # Nose wrinkle (disgust)
        nose_tip = landmarks[1]
        nose_bridge = landmarks[6]
        if abs(nose_tip.y - nose_bridge.y) < 0.03:
            expressions.append("nose_wrinkle")
        
        return expressions
    
    def _infer_emotion(self, landmarks, ear: float, blink_rate: float) -> EmotionalState:
        """Infer emotional state from multiple facial cues."""
        # Mouth analysis
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]
        top_lip = landmarks[13]
        bottom_lip = landmarks[14]
        
        mouth_width = abs(right_mouth.x - left_mouth.x)
        mouth_height = abs(bottom_lip.y - top_lip.y)
        smile_ratio = mouth_width / max(mouth_height, 0.001)
        
        # Eyebrow analysis
        left_brow = landmarks[107]
        right_brow = landmarks[336]
        left_eye = landmarks[159]
        right_eye = landmarks[386]
        
        brow_furrow = (left_brow.x - right_brow.x)
        brow_height = ((left_brow.y - left_eye.y) + (right_brow.y - right_eye.y)) / 2
        
        # Decision tree
        if ear < 0.18 and blink_rate < 10:
            return EmotionalState.TIRED
        elif smile_ratio > 4.0 and mouth_height > 0.02:
            return EmotionalState.HAPPY
        elif mouth_height > 0.06:
            return EmotionalState.SURPRISED
        elif brow_height < -0.02:
            if smile_ratio < 2.5:
                return EmotionalState.ANGRY
            return EmotionalState.STRESSED
        elif blink_rate > 25:
            return EmotionalState.STRESSED
        elif abs(brow_furrow) > 0.15:
            return EmotionalState.CONFUSED
        else:
            return EmotionalState.NEUTRAL
    
    def _calculate_perclos(self) -> float:
        """Calculate PERCLOS (percentage of eye closure) for drowsiness."""
        if len(self.perclos_window) < 30:
            return 0.0
        
        closed_frames = sum(1 for ear in self.perclos_window if ear < self.ear_threshold)
        return closed_frames / len(self.perclos_window)
    
    def _get_stable_emotion(self, current: EmotionalState) -> EmotionalState:
        """Stabilize emotion output by considering history."""
        self.emotion_history.append(current)
        
        if len(self.emotion_history) < 5:
            return current
        
        # Vote among recent emotions
        emotion_counts: Dict[EmotionalState, int] = {}
        for e in self.emotion_history:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        return max(emotion_counts.keys(), key=lambda x: emotion_counts[x])
    
    def analyze(self, frame: np.ndarray) -> Optional[GazeData]:
        """Analyze a video frame for comprehensive gaze and expression data."""
        if not self.is_active:
            return None
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        if not results.multi_face_landmarks:
            return None
        
        landmarks = results.multi_face_landmarks[0].landmark
        current_time = time.time()
        
        # Calculate EAR
        left_ear = self._calculate_ear(landmarks, self.LEFT_EYE)
        right_ear = self._calculate_ear(landmarks, self.RIGHT_EYE)
        avg_ear = (left_ear + right_ear) / 2
        
        self.ear_history.append(avg_ear)
        self.perclos_window.append(avg_ear)
        
        # Blink detection
        is_eye_closed = avg_ear < self.ear_threshold
        if is_eye_closed and not self.was_eye_closed:
            self.blink_timestamps.append(current_time)
        self.was_eye_closed = is_eye_closed
        
        # Calculate blink rate (last 60 seconds)
        recent_blinks = [t for t in self.blink_timestamps if current_time - t < 60]
        blink_rate = len(recent_blinks)
        
        # Head pose
        head_pose = self._estimate_head_pose(landmarks, frame.shape)
        
        # Looking at screen check
        yaw, pitch, roll = head_pose
        looking_at_screen = abs(yaw) < 20 and abs(pitch) < 20
        
        # Attention score
        attention = 1.0 if looking_at_screen else max(0, 1 - (abs(yaw) + abs(pitch)) / 60)
        
        # Fatigue detection
        perclos = self._calculate_perclos()
        avg_ear_recent = np.mean(list(self.ear_history)) if self.ear_history else 0.25
        
        fatigue = min(1.0, perclos * 2 + (0.25 - avg_ear_recent) * 2)
        is_drowsy = perclos > 0.3 or fatigue > 0.6
        
        # Micro-expressions
        micro_expressions = self._detect_micro_expressions(landmarks)
        
        # Emotion
        raw_emotion = self._infer_emotion(landmarks, avg_ear, blink_rate)
        stable_emotion = self._get_stable_emotion(raw_emotion)
        
        return GazeData(
            looking_at_screen=looking_at_screen,
            eye_aspect_ratio=avg_ear,
            blink_rate=blink_rate,
            estimated_emotion=stable_emotion,
            attention_score=attention,
            head_pose=head_pose,
            fatigue_level=fatigue,
            is_drowsy=is_drowsy,
            micro_expressions=micro_expressions
        )
    
    def reset(self):
        """Reset all tracking history."""
        self.blink_timestamps.clear()
        self.ear_history.clear()
        self.perclos_window.clear()
        self.emotion_history.clear()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = GazeAnalyzer()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        data = analyzer.analyze(frame)
        if data:
            info = [
                f"Emotion: {data.estimated_emotion.value}",
                f"Attention: {data.attention_score:.2f}",
                f"Fatigue: {data.fatigue_level:.2f}",
                f"Drowsy: {data.is_drowsy}",
                f"Blinks/min: {data.blink_rate}",
            ]
            for i, text in enumerate(info):
                cv2.putText(frame, text, (10, 30 + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Gaze Analysis", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
