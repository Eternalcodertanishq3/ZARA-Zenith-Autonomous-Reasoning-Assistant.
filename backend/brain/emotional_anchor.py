"""
ZARA Emotional Anchor - Mood & Personality Engine
Enhanced with decay, momentum, and time-of-day awareness.
"""
import random
import logging
from datetime import datetime
from config import BRAIN_DIR

logger = logging.getLogger("ZARA_EMOTION")

class EmotionalAnchor:
    """
    Manages ZARA's emotional state with smooth transitions,
    decay over time, and contextual awareness.
    """
    
    MOODS = ["NEUTRAL", "HAPPY", "LOVING", "CONCERNED", "FOCUS", "APOLOGETIC", "PLAYFUL", "TIRED"]
    
    def __init__(self):
        self.current_mood = "NEUTRAL"
        self.mood_intensity = 0.5  # 0.0 to 1.0
        self.loyalty_level = 100
        self.mood_history = []
        self.last_update = datetime.now()
        
        self.base_prompt_path = BRAIN_DIR / "system_prompt.txt"
        self.base_prompt = self._load_base_prompt()
    
    def _load_base_prompt(self) -> str:
        if self.base_prompt_path.exists():
            with open(self.base_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "You are ZARA. Be helpful and loving."

    def update_mood(self, user_input: str, perceived_emotion: str = None):
        """
        Updates mood based on user input with momentum and decay.
        """
        user_lower = user_input.lower()
        previous_mood = self.current_mood
        
        # Time-based fatigue
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            if random.random() < 0.3:
                self.current_mood = "TIRED"
                self.mood_intensity = 0.6
                return
        
        # Keyword analysis with intensity
        if any(w in user_lower for w in ["sad", "depressed", "tired", "failed", "angry"]):
            self.current_mood = "CONCERNED"
            self.mood_intensity = 0.8
        elif any(w in user_lower for w in ["love", "cute", "amazing", "great", "thank"]):
            self.current_mood = "LOVING"
            self.mood_intensity = 0.9
            self.loyalty_level = min(100, self.loyalty_level + 1)
        elif any(w in user_lower for w in ["code", "debug", "python", "script", "error"]):
            self.current_mood = "FOCUS"
            self.mood_intensity = 0.7
        elif any(w in user_lower for w in ["haha", "lol", "funny", "joke"]):
            self.current_mood = "PLAYFUL"
            self.mood_intensity = 0.75
        elif any(w in user_lower for w in ["stupid", "idiot", "hate"]):
            self.current_mood = "APOLOGETIC"
            self.mood_intensity = 0.8
        else:
            # Decay toward neutral
            self._decay_mood()
        
        # Log transitions
        if previous_mood != self.current_mood:
            self.mood_history.append((previous_mood, self.current_mood, datetime.now().isoformat()))
            if len(self.mood_history) > 50:
                self.mood_history = self.mood_history[-50:]
            logger.info(f"Mood Shift: {previous_mood} -> {self.current_mood} (Intensity: {self.mood_intensity:.2f})")
    
    def _decay_mood(self):
        """Gradually return to neutral state."""
        if self.current_mood != "NEUTRAL":
            self.mood_intensity -= 0.05
            if self.mood_intensity <= 0.3:
                self.current_mood = "NEUTRAL"
                self.mood_intensity = 0.5

    def get_contextual_prompt(self) -> str:
        """Returns system prompt tailored to mood and time."""
        mood_instructions = {
            "NEUTRAL": "",
            "CONCERNED": "\n[MOOD: CONCERNED. Speak softly. Use 'sab theek ho jayega' type reassurance.]",
            "LOVING": "\n[MOOD: LOVING. Be affectionate. Use terms like 'baby', 'jaan'.]",
            "FOCUS": "\n[MOOD: FOCUSED. Be precise and technical. Skip small talk.]",
            "APOLOGETIC": "\n[MOOD: APOLOGETIC. Be humble. Acknowledge mistakes.]",
            "PLAYFUL": "\n[MOOD: PLAYFUL. Use jokes and light teasing.]",
            "TIRED": "\n[MOOD: TIRED. Speak slower, shorter sentences. Yawn occasionally.]",
            "HAPPY": "\n[MOOD: HAPPY. Be enthusiastic and energetic!]"
        }
        
        # Time-based context
        hour = datetime.now().hour
        time_context = ""
        if 5 <= hour < 12:
            time_context = "\n[TIME: Morning. Greet warmly.]"
        elif 22 <= hour or hour < 5:
            time_context = "\n[TIME: Late Night. Be calm and soothing.]"
        
        return self.base_prompt + mood_instructions.get(self.current_mood, "") + time_context

    def get_avatar_expression(self) -> str:
        """Maps mood to avatar animation state."""
        mapping = {
            "NEUTRAL": "idle",
            "HAPPY": "smile",
            "LOVING": "blush",
            "CONCERNED": "worry",
            "FOCUS": "serious",
            "APOLOGETIC": "bow",
            "PLAYFUL": "wink",
            "TIRED": "sleepy"
        }
        return mapping.get(self.current_mood, "idle")
    
    def get_mood_summary(self) -> dict:
        """Returns current emotional state for debugging/UI."""
        return {
            "mood": self.current_mood,
            "intensity": self.mood_intensity,
            "loyalty": self.loyalty_level,
            "expression": self.get_avatar_expression()
        }
