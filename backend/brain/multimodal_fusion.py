"""
ZARA Advanced Multimodal Perception Engine
A sophisticated sensory integration system that creates unified
world understanding from multiple input modalities.
"""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import deque
from enum import Enum
import statistics

logger = logging.getLogger("ZARA_PERCEPTION")


class ModalityType(Enum):
    """Types of sensory modalities."""
    VISION = "vision"
    AUDIO = "audio"
    TEXT = "text"
    EMOTION = "emotion"
    CONTEXT = "context"
    MEMORY = "memory"


class AttentionLevel(Enum):
    """Levels of attention/importance."""
    CRITICAL = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    BACKGROUND = 1


class PerceptionState(Enum):
    """Current perception state."""
    PASSIVE = "passive"        # Background awareness
    ATTENTIVE = "attentive"    # Normal conversation
    FOCUSED = "focused"        # Intense interaction
    ALERT = "alert"            # Something important detected


@dataclass
class SensoryInput:
    """A single sensory input with metadata."""
    modality: ModalityType
    content: Any
    timestamp: float
    confidence: float = 1.0
    attention_level: AttentionLevel = AttentionLevel.NORMAL
    source: str = "unknown"
    metadata: Dict = field(default_factory=dict)


@dataclass
class EmotionalSignal:
    """Detected emotional signal from any modality."""
    emotion: str
    intensity: float  # 0-1
    source_modality: ModalityType
    timestamp: float
    indicators: List[str] = field(default_factory=list)


@dataclass
class PerceptionSnapshot:
    """Complete snapshot of current perception."""
    timestamp: float
    visual_scene: str
    audio_content: str
    detected_emotions: List[EmotionalSignal]
    user_attention: float  # 0-1, is user engaged?
    environmental_state: Dict
    cross_modal_insights: List[str]
    attention_focus: str
    overall_mood: str


class AdvancedMultimodalFusion:
    """
    ZARA's integrated perception system.
    
    This creates a unified understanding of the world by:
    - Temporally aligning inputs from different senses
    - Detecting cross-modal patterns (voice + face = emotional state)
    - Maintaining environmental awareness
    - Tracking user attention and engagement
    - Generating holistic perception snapshots
    """
    
    def __init__(self, temporal_window_ms: float = 2000):
        self.temporal_window = temporal_window_ms / 1000  # Convert to seconds
        self.lock = threading.RLock()
        
        # Sensory buffers (time-ordered)
        self.visual_buffer: deque = deque(maxlen=30)
        self.audio_buffer: deque = deque(maxlen=30)
        self.text_buffer: deque = deque(maxlen=20)
        self.emotion_buffer: deque = deque(maxlen=50)
        
        # Current state
        self.perception_state = PerceptionState.PASSIVE
        self.attention_focus = "general"
        self.user_presence = False
        self.user_engaged = 0.5
        
        # Environment model
        self.environment = {
            "lighting": "normal",
            "activity_level": 0.5,
            "noise_level": 0.3,
            "people_count": 0,
            "time_of_day_context": "day"
        }
        
        # Cross-modal insights
        self.recent_insights: deque = deque(maxlen=20)
        
        # Emotional convergence tracking
        self.converged_emotion: Optional[EmotionalSignal] = None
        
        # History for pattern detection
        self.perception_history: deque = deque(maxlen=100)
        
        # Callbacks
        self.on_important_change: Optional[Callable] = None
        self.on_emotion_detected: Optional[Callable] = None
        
        logger.info("🎯 Advanced Multimodal Fusion initialized")

    # ═══════════════════════════════════════════════════════════════════
    # SENSORY INPUT
    # ═══════════════════════════════════════════════════════════════════
    
    def update_vision(self, description: str, 
                     face_detected: bool = False,
                     emotion_detected: Optional[str] = None,
                     attention_score: float = 0.5,
                     objects: List[str] = None,
                     metadata: Dict = None):
        """
        Update with new visual information.
        
        Args:
            description: Natural language description of visual scene
            face_detected: Whether a face is visible
            emotion_detected: Facial emotion if detected
            attention_score: How much user appears attentive (0-1)
            objects: Detected objects in scene
            metadata: Additional visual metadata
        """
        now = time.time()
        
        sensory_input = SensoryInput(
            modality=ModalityType.VISION,
            content=description,
            timestamp=now,
            confidence=0.8 if face_detected else 0.5,
            attention_level=self._calculate_visual_attention(face_detected, attention_score),
            source="vision_system",
            metadata={
                "face_detected": face_detected,
                "objects": objects or [],
                "attention_score": attention_score,
                **(metadata or {})
            }
        )
        
        with self.lock:
            self.visual_buffer.append(sensory_input)
            self.user_presence = face_detected
            self.user_engaged = attention_score
        
        # Handle facial emotion
        if emotion_detected:
            self._add_emotional_signal(
                emotion=emotion_detected,
                intensity=0.7,
                source=ModalityType.VISION,
                indicators=["facial_expression"]
            )
        
        # Cross-modal analysis
        self._analyze_cross_modal()

    def update_audio(self, transcription: str,
                    voice_emotion: Optional[str] = None,
                    speaking_rate: float = 1.0,
                    volume_level: float = 0.5,
                    pitch_variation: float = 0.5,
                    is_user_speaking: bool = True):
        """
        Update with new audio information.
        
        Args:
            transcription: What was said
            voice_emotion: Detected emotion from voice
            speaking_rate: Relative speaking rate (1.0 = normal)
            volume_level: Volume (0-1)
            pitch_variation: How much pitch varies (monotone=0, animated=1)
            is_user_speaking: Whether this is the user speaking
        """
        now = time.time()
        
        # Calculate attention from audio features
        attention = self._calculate_audio_attention(
            speaking_rate, volume_level, pitch_variation
        )
        
        sensory_input = SensoryInput(
            modality=ModalityType.AUDIO,
            content=transcription,
            timestamp=now,
            confidence=0.9 if transcription else 0.3,
            attention_level=attention,
            source="audio_system",
            metadata={
                "speaking_rate": speaking_rate,
                "volume": volume_level,
                "pitch_variation": pitch_variation,
                "is_user": is_user_speaking
            }
        )
        
        with self.lock:
            self.audio_buffer.append(sensory_input)
            if is_user_speaking:
                self.user_engaged = min(1.0, self.user_engaged + 0.2)
        
        # Voice emotion
        if voice_emotion:
            # Voice emotion is strong signal
            self._add_emotional_signal(
                emotion=voice_emotion,
                intensity=0.8,
                source=ModalityType.AUDIO,
                indicators=[
                    f"speaking_rate_{self._rate_descriptor(speaking_rate)}",
                    f"pitch_{self._pitch_descriptor(pitch_variation)}",
                    f"volume_{self._volume_descriptor(volume_level)}"
                ]
            )
        
        # Infer emotion from audio features if not explicit
        if not voice_emotion and transcription:
            inferred = self._infer_emotion_from_audio_features(
                speaking_rate, volume_level, pitch_variation
            )
            if inferred:
                self._add_emotional_signal(
                    emotion=inferred,
                    intensity=0.4,  # Lower confidence for inference
                    source=ModalityType.AUDIO,
                    indicators=["audio_feature_inference"]
                )
        
        self._analyze_cross_modal()

    def update_text(self, text: str, 
                   text_sentiment: float = 0.5,
                   topics: List[str] = None,
                   is_question: bool = False):
        """
        Update with text content analysis.
        
        Args:
            text: The text content
            text_sentiment: Sentiment score (0=negative, 1=positive)
            topics: Detected topics
            is_question: Whether text is a question
        """
        now = time.time()
        
        attention = AttentionLevel.HIGH if is_question else AttentionLevel.NORMAL
        
        sensory_input = SensoryInput(
            modality=ModalityType.TEXT,
            content=text,
            timestamp=now,
            confidence=0.95,
            attention_level=attention,
            source="text_analysis",
            metadata={
                "sentiment": text_sentiment,
                "topics": topics or [],
                "is_question": is_question
            }
        )
        
        with self.lock:
            self.text_buffer.append(sensory_input)
        
        # Infer emotion from text sentiment
        if text_sentiment < 0.3:
            self._add_emotional_signal("negative", 0.5 - text_sentiment, 
                                       ModalityType.TEXT, ["text_sentiment"])
        elif text_sentiment > 0.7:
            self._add_emotional_signal("positive", text_sentiment - 0.5,
                                       ModalityType.TEXT, ["text_sentiment"])
        
        self._analyze_cross_modal()

    def _add_emotional_signal(self, emotion: str, intensity: float,
                             source: ModalityType, indicators: List[str]):
        """Add an emotional signal to the buffer."""
        signal = EmotionalSignal(
            emotion=emotion,
            intensity=min(1.0, max(0.0, intensity)),
            source_modality=source,
            timestamp=time.time(),
            indicators=indicators
        )
        
        with self.lock:
            self.emotion_buffer.append(signal)
        
        if self.on_emotion_detected:
            self.on_emotion_detected(signal)

    # ═══════════════════════════════════════════════════════════════════
    # CROSS-MODAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    def _analyze_cross_modal(self):
        """Perform cross-modal analysis to find patterns."""
        now = time.time()
        
        with self.lock:
            # Get recent inputs from each modality
            recent_visual = self._get_recent(self.visual_buffer, now)
            recent_audio = self._get_recent(self.audio_buffer, now)
            recent_emotions = self._get_recent(self.emotion_buffer, now)
        
        # Emotional convergence analysis
        self._analyze_emotional_convergence(recent_emotions)
        
        # Pattern detection
        insights = []
        
        # Check for emotional mismatch (saying positive, looking sad)
        if recent_emotions:
            modality_emotions = {}
            for e in recent_emotions:
                if e.source_modality not in modality_emotions:
                    modality_emotions[e.source_modality] = []
                modality_emotions[e.source_modality].append(e)
            
            # Compare visual vs audio emotion
            if ModalityType.VISION in modality_emotions and ModalityType.AUDIO in modality_emotions:
                visual_emo = modality_emotions[ModalityType.VISION][-1].emotion
                audio_emo = modality_emotions[ModalityType.AUDIO][-1].emotion
                
                if self._emotions_conflict(visual_emo, audio_emo):
                    insights.append(f"Emotional mismatch: appears {visual_emo} but sounds {audio_emo}")
        
        # Check engagement patterns
        if recent_visual:
            latest_visual = recent_visual[-1]
            attention = latest_visual.metadata.get("attention_score", 0.5)
            face = latest_visual.metadata.get("face_detected", False)
            
            if face and attention < 0.3:
                insights.append("User present but distracted")
            elif not face and recent_audio:
                insights.append("User speaking but not visible")
        
        # Store insights
        for insight in insights:
            self.recent_insights.append({
                "timestamp": now,
                "insight": insight
            })

    def _analyze_emotional_convergence(self, recent_emotions: List[EmotionalSignal]):
        """Find converged emotion across modalities."""
        if not recent_emotions:
            return
        
        # Group by emotion type
        emotion_votes = {}
        for e in recent_emotions:
            if e.emotion not in emotion_votes:
                emotion_votes[e.emotion] = []
            emotion_votes[e.emotion].append(e.intensity)
        
        # Find strongest converged emotion
        best_emotion = None
        best_score = 0
        
        for emotion, intensities in emotion_votes.items():
            # Score = average intensity * number of modalities
            score = statistics.mean(intensities) * len(intensities)
            if score > best_score:
                best_score = score
                best_emotion = emotion
        
        if best_emotion and best_score > 0.5:
            self.converged_emotion = EmotionalSignal(
                emotion=best_emotion,
                intensity=best_score / 3,  # Normalize
                source_modality=ModalityType.EMOTION,
                timestamp=time.time(),
                indicators=["cross_modal_convergence"]
            )

    def _get_recent(self, buffer: deque, now: float) -> List:
        """Get items within temporal window."""
        return [item for item in buffer 
                if now - item.timestamp <= self.temporal_window]

    def _emotions_conflict(self, emotion1: str, emotion2: str) -> bool:
        """Check if two emotions are conflicting."""
        conflicts = {
            ("happy", "sad"), ("sad", "happy"),
            ("positive", "negative"), ("negative", "positive"),
            ("excited", "tired"), ("tired", "excited"),
            ("angry", "calm"), ("calm", "angry")
        }
        return (emotion1.lower(), emotion2.lower()) in conflicts

    # ═══════════════════════════════════════════════════════════════════
    # ATTENTION & IMPORTANCE
    # ═══════════════════════════════════════════════════════════════════
    
    def _calculate_visual_attention(self, face_detected: bool, 
                                   attention_score: float) -> AttentionLevel:
        """Calculate attention level from visual cues."""
        if not face_detected:
            return AttentionLevel.BACKGROUND
        if attention_score > 0.8:
            return AttentionLevel.HIGH
        if attention_score > 0.5:
            return AttentionLevel.NORMAL
        return AttentionLevel.LOW

    def _calculate_audio_attention(self, rate: float, volume: float,
                                  pitch_var: float) -> AttentionLevel:
        """Calculate attention from audio characteristics."""
        # Urgent = fast + loud + varied pitch
        urgency = (rate - 1.0) + volume + pitch_var
        
        if urgency > 1.5:
            return AttentionLevel.CRITICAL
        if urgency > 1.0:
            return AttentionLevel.HIGH
        if urgency > 0.5:
            return AttentionLevel.NORMAL
        return AttentionLevel.LOW

    def _infer_emotion_from_audio_features(self, rate: float, volume: float,
                                          pitch_var: float) -> Optional[str]:
        """Infer emotion from audio characteristics."""
        # Fast + loud + high pitch variation = excited/stressed
        if rate > 1.3 and volume > 0.6 and pitch_var > 0.6:
            return "excited"
        
        # Slow + quiet + monotone = sad/tired
        if rate < 0.8 and volume < 0.4 and pitch_var < 0.3:
            return "tired"
        
        # Fast + loud = frustrated
        if rate > 1.2 and volume > 0.7:
            return "frustrated"
        
        # Normal with high pitch variation = engaged
        if 0.9 <= rate <= 1.1 and pitch_var > 0.5:
            return "engaged"
        
        return None

    # ═══════════════════════════════════════════════════════════════════
    # PERCEPTION OUTPUT
    # ═══════════════════════════════════════════════════════════════════
    
    def get_perception_snapshot(self) -> PerceptionSnapshot:
        """Get current unified perception."""
        now = time.time()
        
        with self.lock:
            # Get latest from each modality
            latest_visual = self.visual_buffer[-1] if self.visual_buffer else None
            latest_audio = self.audio_buffer[-1] if self.audio_buffer else None
            recent_emotions = self._get_recent(self.emotion_buffer, now)
        
        return PerceptionSnapshot(
            timestamp=now,
            visual_scene=latest_visual.content if latest_visual else "No visual input",
            audio_content=latest_audio.content if latest_audio else "",
            detected_emotions=recent_emotions[-5:] if recent_emotions else [],
            user_attention=self.user_engaged,
            environmental_state=self.environment.copy(),
            cross_modal_insights=[i["insight"] for i in list(self.recent_insights)[-5:]],
            attention_focus=self.attention_focus,
            overall_mood=self.converged_emotion.emotion if self.converged_emotion else "neutral"
        )

    def get_context_string(self, max_length: int = 500) -> str:
        """Get perception as natural language context for LLM."""
        snapshot = self.get_perception_snapshot()
        
        parts = []
        
        # Visual
        if snapshot.visual_scene and snapshot.visual_scene != "No visual input":
            parts.append(f"[SEEING] {snapshot.visual_scene}")
        
        # Engagement
        if self.user_presence:
            if self.user_engaged > 0.7:
                parts.append("[USER] Present and attentive")
            elif self.user_engaged > 0.4:
                parts.append("[USER] Present")
            else:
                parts.append("[USER] Present but distracted")
        else:
            parts.append("[USER] Not visible")
        
        # Emotional state
        if snapshot.detected_emotions:
            emotions = set(e.emotion for e in snapshot.detected_emotions[-3:])
            parts.append(f"[SENSING] User appears: {', '.join(emotions)}")
        
        # Cross-modal insights
        if snapshot.cross_modal_insights:
            parts.append(f"[NOTICE] {snapshot.cross_modal_insights[-1]}")
        
        context = "\n".join(parts)
        return context[:max_length]

    def get_emotional_context(self) -> Dict:
        """Get emotional context for response generation."""
        if self.converged_emotion:
            return {
                "primary_emotion": self.converged_emotion.emotion,
                "intensity": self.converged_emotion.intensity,
                "confidence": "high" if len(self.emotion_buffer) > 3 else "medium",
                "sources": [e.source_modality.value for e in list(self.emotion_buffer)[-5:]]
            }
        return {
            "primary_emotion": "neutral",
            "intensity": 0.5,
            "confidence": "low",
            "sources": []
        }

    def should_interrupt(self) -> Tuple[bool, str]:
        """
        Determine if ZARA should proactively speak.
        Returns (should_interrupt, reason).
        """
        # Check for important emotional detection
        if self.converged_emotion:
            if self.converged_emotion.emotion in ["sad", "distressed", "crying"]:
                return True, "User appears upset"
            if self.converged_emotion.emotion == "frustrated":
                return True, "User seems frustrated"
        
        # Check attention patterns
        if self.user_presence and self.user_engaged > 0.9:
            # User is looking intently - might want something
            with self.lock:
                if not self.audio_buffer or \
                   time.time() - self.audio_buffer[-1].timestamp > 5:
                    return True, "User looking expectantly"
        
        return False, ""

    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def _rate_descriptor(self, rate: float) -> str:
        if rate < 0.8: return "slow"
        if rate > 1.3: return "fast"
        return "normal"

    def _pitch_descriptor(self, pitch: float) -> str:
        if pitch < 0.3: return "monotone"
        if pitch > 0.7: return "animated"
        return "normal"

    def _volume_descriptor(self, volume: float) -> str:
        if volume < 0.3: return "quiet"
        if volume > 0.7: return "loud"
        return "normal"

    def update_environment(self, **kwargs):
        """Update environmental state."""
        self.environment.update(kwargs)

    def get_status(self) -> Dict:
        """Get fusion system status."""
        return {
            "state": self.perception_state.value,
            "user_present": self.user_presence,
            "user_engaged": self.user_engaged,
            "attention_focus": self.attention_focus,
            "current_emotion": self.converged_emotion.emotion if self.converged_emotion else "neutral",
            "visual_buffer_size": len(self.visual_buffer),
            "audio_buffer_size": len(self.audio_buffer),
            "recent_insights": len(self.recent_insights),
            "environment": self.environment
        }


# Backwards compatibility
FusionEngine = AdvancedMultimodalFusion


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fusion = AdvancedMultimodalFusion()
    
    # Simulate inputs
    fusion.update_vision(
        "User sitting at desk, looking at screen",
        face_detected=True,
        emotion_detected="focused",
        attention_score=0.8
    )
    
    fusion.update_audio(
        "I'm working on this project",
        speaking_rate=1.0,
        volume_level=0.5,
        pitch_variation=0.4
    )
    
    print("Context:", fusion.get_context_string())
    print("\nStatus:", fusion.get_status())
    print("\nEmotional:", fusion.get_emotional_context())
