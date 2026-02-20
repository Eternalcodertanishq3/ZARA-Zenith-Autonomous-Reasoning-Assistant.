"""
ZARA Synchronized Emotional Expression System
Unifies emotional expression across voice, face/avatar, and text
for coherent, authentic emotional communication.
"""
import logging
import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from collections import deque
from pathlib import Path
from enum import Enum

logger = logging.getLogger("ZARA_EMOTION_SYNC")


class EmotionChannel(Enum):
    """Emotional expression channels."""
    VOICE = "voice"         # TTS emotion/prosody
    FACE = "face"           # Avatar facial expression
    TEXT = "text"           # Response text style
    BODY = "body"           # Avatar body language


class CoreEmotion(Enum):
    """Core emotions for expression."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    NEUTRAL = "neutral"


class EmotionIntensity(Enum):
    """Intensity levels."""
    SUBTLE = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    INTENSE = 0.9


@dataclass
class EmotionalState:
    """Current emotional state."""
    primary: CoreEmotion
    secondary: Optional[CoreEmotion] = None
    intensity: float = 0.5          # 0-1
    valence: float = 0.5            # 0=negative, 1=positive
    arousal: float = 0.5            # 0=calm, 1=excited
    authenticity: float = 1.0       # How genuine (vs performed)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ChannelExpression:
    """Expression settings for a channel."""
    channel: EmotionChannel
    emotion: CoreEmotion
    intensity: float
    parameters: Dict = field(default_factory=dict)


@dataclass
class SynchronizedExpression:
    """A synchronized multi-channel expression."""
    voice: ChannelExpression
    face: ChannelExpression
    text: ChannelExpression
    body: Optional[ChannelExpression] = None
    duration: float = 0.0
    transition_time: float = 0.3


class EmotionalExpressionSync:
    """
    Synchronizes emotional expression across all output channels.
    
    Features:
    - Unified emotional state management
    - Channel-specific expression mapping
    - Smooth transitions between states
    - Authenticity tracking
    - Expression history for consistency
    
    This ensures ZARA's emotions feel coherent and genuine.
    """
    
    def __init__(self):
        # Current state
        self.current_state = EmotionalState(
            primary=CoreEmotion.NEUTRAL,
            intensity=0.5
        )
        
        # Expression history
        self.expression_history: deque = deque(maxlen=50)
        self.state_history: deque = deque(maxlen=100)
        
        # Channel handlers (will be connected)
        self.voice_handler: Optional[Callable] = None
        self.face_handler: Optional[Callable] = None
        self.text_handler: Optional[Callable] = None
        
        # Emotion mappings for each channel
        self.voice_mappings = self._init_voice_mappings()
        self.face_mappings = self._init_face_mappings()
        self.text_mappings = self._init_text_mappings()
        
        # Transition state
        self.is_transitioning = False
        self.target_state: Optional[EmotionalState] = None
        
        # Threading
        self.lock = threading.Lock()
        
        logger.info("🎭 Emotional Expression Sync initialized")

    def _init_voice_mappings(self) -> Dict[CoreEmotion, Dict]:
        """Initialize voice expression mappings."""
        return {
            CoreEmotion.JOY: {
                "pitch_mod": 1.1,      # Slightly higher pitch
                "rate_mod": 1.05,      # Slightly faster
                "energy_mod": 1.1,     # More energy
                "style": "cheerful"
            },
            CoreEmotion.SADNESS: {
                "pitch_mod": 0.9,
                "rate_mod": 0.9,
                "energy_mod": 0.8,
                "style": "soft"
            },
            CoreEmotion.ANGER: {
                "pitch_mod": 1.0,
                "rate_mod": 1.1,
                "energy_mod": 1.3,
                "style": "emphatic"
            },
            CoreEmotion.FEAR: {
                "pitch_mod": 1.15,
                "rate_mod": 1.2,
                "energy_mod": 0.9,
                "style": "tense"
            },
            CoreEmotion.SURPRISE: {
                "pitch_mod": 1.2,
                "rate_mod": 1.0,
                "energy_mod": 1.2,
                "style": "excited"
            },
            CoreEmotion.LOVE: {
                "pitch_mod": 0.95,
                "rate_mod": 0.95,
                "energy_mod": 0.9,
                "style": "warm"
            },
            CoreEmotion.TRUST: {
                "pitch_mod": 1.0,
                "rate_mod": 0.95,
                "energy_mod": 1.0,
                "style": "confident"
            },
            CoreEmotion.ANTICIPATION: {
                "pitch_mod": 1.05,
                "rate_mod": 1.05,
                "energy_mod": 1.1,
                "style": "eager"
            },
            CoreEmotion.NEUTRAL: {
                "pitch_mod": 1.0,
                "rate_mod": 1.0,
                "energy_mod": 1.0,
                "style": "default"
            }
        }

    def _init_face_mappings(self) -> Dict[CoreEmotion, Dict]:
        """Initialize facial expression mappings."""
        return {
            CoreEmotion.JOY: {
                "expression": "smile",
                "eye_expression": "happy",
                "brow_position": "neutral",
                "mouth_shape": "smile_open"
            },
            CoreEmotion.SADNESS: {
                "expression": "sad",
                "eye_expression": "droopy",
                "brow_position": "furrowed_up",
                "mouth_shape": "frown"
            },
            CoreEmotion.ANGER: {
                "expression": "angry",
                "eye_expression": "narrow",
                "brow_position": "furrowed_down",
                "mouth_shape": "tense"
            },
            CoreEmotion.FEAR: {
                "expression": "fearful",
                "eye_expression": "wide",
                "brow_position": "raised",
                "mouth_shape": "open_slight"
            },
            CoreEmotion.SURPRISE: {
                "expression": "surprised",
                "eye_expression": "wide",
                "brow_position": "raised_high",
                "mouth_shape": "open_round"
            },
            CoreEmotion.LOVE: {
                "expression": "loving",
                "eye_expression": "soft",
                "brow_position": "relaxed",
                "mouth_shape": "gentle_smile"
            },
            CoreEmotion.TRUST: {
                "expression": "confident",
                "eye_expression": "steady",
                "brow_position": "slightly_raised",
                "mouth_shape": "slight_smile"
            },
            CoreEmotion.NEUTRAL: {
                "expression": "neutral",
                "eye_expression": "normal",
                "brow_position": "neutral",
                "mouth_shape": "relaxed"
            }
        }

    def _init_text_mappings(self) -> Dict[CoreEmotion, Dict]:
        """Initialize text style mappings."""
        return {
            CoreEmotion.JOY: {
                "emoji_style": "happy",
                "punctuation_style": "enthusiastic",
                "word_choice": "positive",
                "sentence_length": "varied",
                "emojis": ["😊", "💕", "✨", "🌟", "😄"]
            },
            CoreEmotion.SADNESS: {
                "emoji_style": "sad",
                "punctuation_style": "muted",
                "word_choice": "gentle",
                "sentence_length": "shorter",
                "emojis": ["😔", "💙", "🫂"]
            },
            CoreEmotion.LOVE: {
                "emoji_style": "affectionate",
                "punctuation_style": "warm",
                "word_choice": "caring",
                "sentence_length": "flowing",
                "emojis": ["💕", "🥰", "💗", "❤️"]
            },
            CoreEmotion.SURPRISE: {
                "emoji_style": "excited",
                "punctuation_style": "exclamatory",
                "word_choice": "expressive",
                "sentence_length": "varied",
                "emojis": ["😮", "✨", "🎉", "!"]
            },
            CoreEmotion.NEUTRAL: {
                "emoji_style": "minimal",
                "punctuation_style": "standard",
                "word_choice": "neutral",
                "sentence_length": "normal",
                "emojis": []
            }
        }

    # ═══════════════════════════════════════════════════════════════════
    # STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def set_emotional_state(self, emotion: CoreEmotion,
                           intensity: float = 0.5,
                           secondary: CoreEmotion = None,
                           valence: float = None,
                           arousal: float = None,
                           transition_time: float = 0.3):
        """Set the current emotional state."""
        # Calculate valence/arousal if not provided
        if valence is None:
            valence = self._emotion_to_valence(emotion)
        if arousal is None:
            arousal = self._emotion_to_arousal(emotion)
        
        new_state = EmotionalState(
            primary=emotion,
            secondary=secondary,
            intensity=intensity,
            valence=valence,
            arousal=arousal
        )
        
        with self.lock:
            self.state_history.append(self.current_state)
            self.current_state = new_state
            self.target_state = new_state
        
        # Generate synchronized expression
        expression = self._generate_expression(new_state)
        
        # Apply to channels
        self._apply_expression(expression, transition_time)
        
        return expression

    def _emotion_to_valence(self, emotion: CoreEmotion) -> float:
        """Map emotion to valence (positive/negative)."""
        mapping = {
            CoreEmotion.JOY: 0.9,
            CoreEmotion.LOVE: 0.95,
            CoreEmotion.TRUST: 0.7,
            CoreEmotion.ANTICIPATION: 0.65,
            CoreEmotion.SURPRISE: 0.6,
            CoreEmotion.NEUTRAL: 0.5,
            CoreEmotion.FEAR: 0.3,
            CoreEmotion.SADNESS: 0.2,
            CoreEmotion.DISGUST: 0.2,
            CoreEmotion.ANGER: 0.15
        }
        return mapping.get(emotion, 0.5)

    def _emotion_to_arousal(self, emotion: CoreEmotion) -> float:
        """Map emotion to arousal (excitement level)."""
        mapping = {
            CoreEmotion.ANGER: 0.9,
            CoreEmotion.FEAR: 0.85,
            CoreEmotion.SURPRISE: 0.8,
            CoreEmotion.JOY: 0.7,
            CoreEmotion.ANTICIPATION: 0.65,
            CoreEmotion.DISGUST: 0.5,
            CoreEmotion.NEUTRAL: 0.4,
            CoreEmotion.LOVE: 0.4,
            CoreEmotion.TRUST: 0.35,
            CoreEmotion.SADNESS: 0.2
        }
        return mapping.get(emotion, 0.5)

    def update_from_context(self, detected_user_emotion: str = None,
                           conversation_sentiment: float = None,
                           topic_category: str = None):
        """Update emotional state based on context."""
        # Parse user emotion
        if detected_user_emotion:
            response_emotion = self._empathetic_response(detected_user_emotion)
            self.set_emotional_state(response_emotion, intensity=0.6)
        
        # Adjust based on sentiment
        if conversation_sentiment is not None:
            if conversation_sentiment > 0.7:
                self.set_emotional_state(CoreEmotion.JOY, intensity=0.5)
            elif conversation_sentiment < 0.3:
                self.set_emotional_state(CoreEmotion.SADNESS, intensity=0.4)

    def _empathetic_response(self, user_emotion: str) -> CoreEmotion:
        """Generate empathetic emotional response."""
        # Mirror or complement user emotion
        empathy_map = {
            "happy": CoreEmotion.JOY,
            "sad": CoreEmotion.LOVE,  # Respond with warmth to sadness
            "angry": CoreEmotion.TRUST,  # Stay calm and trustworthy
            "stressed": CoreEmotion.LOVE,
            "excited": CoreEmotion.JOY,
            "tired": CoreEmotion.LOVE,
            "confused": CoreEmotion.TRUST,
            "neutral": CoreEmotion.NEUTRAL
        }
        return empathy_map.get(user_emotion.lower(), CoreEmotion.NEUTRAL)

    # ═══════════════════════════════════════════════════════════════════
    # EXPRESSION GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _generate_expression(self, state: EmotionalState) -> SynchronizedExpression:
        """Generate synchronized expression for all channels."""
        emotion = state.primary
        intensity = state.intensity
        
        # Voice expression
        voice_params = self.voice_mappings.get(emotion, self.voice_mappings[CoreEmotion.NEUTRAL])
        voice_params = self._scale_by_intensity(voice_params, intensity)
        
        voice_expr = ChannelExpression(
            channel=EmotionChannel.VOICE,
            emotion=emotion,
            intensity=intensity,
            parameters=voice_params
        )
        
        # Face expression
        face_params = self.face_mappings.get(emotion, self.face_mappings[CoreEmotion.NEUTRAL])
        face_params["intensity"] = intensity
        
        face_expr = ChannelExpression(
            channel=EmotionChannel.FACE,
            emotion=emotion,
            intensity=intensity,
            parameters=face_params
        )
        
        # Text expression
        text_params = self.text_mappings.get(emotion, self.text_mappings[CoreEmotion.NEUTRAL])
        text_params["intensity"] = intensity
        
        text_expr = ChannelExpression(
            channel=EmotionChannel.TEXT,
            emotion=emotion,
            intensity=intensity,
            parameters=text_params
        )
        
        # Body (if avatar supports it)
        body_expr = ChannelExpression(
            channel=EmotionChannel.BODY,
            emotion=emotion,
            intensity=intensity,
            parameters={"posture": self._get_body_posture(emotion)}
        )
        
        return SynchronizedExpression(
            voice=voice_expr,
            face=face_expr,
            text=text_expr,
            body=body_expr
        )

    def _scale_by_intensity(self, params: Dict, intensity: float) -> Dict:
        """Scale parameters by intensity."""
        scaled = params.copy()
        
        for key, value in scaled.items():
            if isinstance(value, (int, float)) and key.endswith("_mod"):
                # Scale modification away from 1.0 based on intensity
                diff = value - 1.0
                scaled[key] = 1.0 + (diff * intensity)
        
        return scaled

    def _get_body_posture(self, emotion: CoreEmotion) -> str:
        """Get body posture for emotion."""
        postures = {
            CoreEmotion.JOY: "upright_open",
            CoreEmotion.SADNESS: "slightly_slumped",
            CoreEmotion.LOVE: "leaning_forward",
            CoreEmotion.TRUST: "upright_confident",
            CoreEmotion.FEAR: "tense_back",
            CoreEmotion.SURPRISE: "alert_upright",
            CoreEmotion.NEUTRAL: "relaxed"
        }
        return postures.get(emotion, "relaxed")

    def _apply_expression(self, expression: SynchronizedExpression,
                         transition_time: float):
        """Apply expression to all channels."""
        # Record expression
        with self.lock:
            self.expression_history.append({
                "expression": expression,
                "timestamp": time.time()
            })
        
        # Apply to voice
        if self.voice_handler:
            try:
                self.voice_handler(expression.voice)
            except Exception as e:
                logger.warning(f"Voice expression error: {e}")
        
        # Apply to face/avatar
        if self.face_handler:
            try:
                self.face_handler(expression.face, transition_time)
            except Exception as e:
                logger.warning(f"Face expression error: {e}")
        
        # Text styling is returned for use in response generation
        # (doesn't need a handler, just stored in current state)

    # ═══════════════════════════════════════════════════════════════════
    # TEXT ENHANCEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def enhance_text(self, text: str) -> str:
        """Enhance text with emotional styling."""
        emotion = self.current_state.primary
        intensity = self.current_state.intensity
        
        text_params = self.text_mappings.get(emotion, {})
        emojis = text_params.get("emojis", [])
        
        # Add emoji if appropriate
        if emojis and intensity > 0.4:
            import random
            # Add at end occasionally
            if random.random() < intensity and not text.endswith(tuple(emojis)):
                text = f"{text} {random.choice(emojis)}"
        
        return text

    def get_text_style_hints(self) -> Dict:
        """Get text styling hints for response generation."""
        emotion = self.current_state.primary
        return self.text_mappings.get(emotion, self.text_mappings[CoreEmotion.NEUTRAL])

    # ═══════════════════════════════════════════════════════════════════
    # CHANNEL CONNECTIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def connect_voice(self, handler: Callable):
        """Connect voice expression handler."""
        self.voice_handler = handler
        logger.info("Voice channel connected")

    def connect_face(self, handler: Callable):
        """Connect face/avatar expression handler."""
        self.face_handler = handler
        logger.info("Face channel connected")

    def connect_text(self, handler: Callable):
        """Connect text enhancement handler."""
        self.text_handler = handler
        logger.info("Text channel connected")

    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_current_state(self) -> EmotionalState:
        """Get current emotional state."""
        return self.current_state

    def get_expression_for_mood(self, mood: str) -> SynchronizedExpression:
        """Get expression for a mood string."""
        mood_map = {
            "happy": CoreEmotion.JOY,
            "sad": CoreEmotion.SADNESS,
            "angry": CoreEmotion.ANGER,
            "excited": CoreEmotion.ANTICIPATION,
            "loving": CoreEmotion.LOVE,
            "calm": CoreEmotion.TRUST,
            "worried": CoreEmotion.FEAR,
            "surprised": CoreEmotion.SURPRISE,
            "neutral": CoreEmotion.NEUTRAL
        }
        
        emotion = mood_map.get(mood.lower(), CoreEmotion.NEUTRAL)
        state = EmotionalState(primary=emotion, intensity=0.6)
        return self._generate_expression(state)

    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "current_emotion": self.current_state.primary.value,
            "intensity": self.current_state.intensity,
            "valence": self.current_state.valence,
            "arousal": self.current_state.arousal,
            "voice_connected": self.voice_handler is not None,
            "face_connected": self.face_handler is not None,
            "expression_count": len(self.expression_history)
        }


# Singleton
_emotion_sync = None

def get_emotion_sync() -> EmotionalExpressionSync:
    """Get the global emotion sync system."""
    global _emotion_sync
    if _emotion_sync is None:
        _emotion_sync = EmotionalExpressionSync()
    return _emotion_sync


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sync = EmotionalExpressionSync()
    
    # Set emotion
    expr = sync.set_emotional_state(CoreEmotion.JOY, intensity=0.7)
    print(f"Voice expression: {expr.voice.parameters}")
    print(f"Face expression: {expr.face.parameters}")
    
    # Enhance text
    text = "That's wonderful news!"
    enhanced = sync.enhance_text(text)
    print(f"Enhanced: {enhanced}")
    
    print(f"Status: {sync.get_status()}")
