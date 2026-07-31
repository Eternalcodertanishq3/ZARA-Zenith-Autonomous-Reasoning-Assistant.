"""
ZARA Boredom Thread - Enhanced Proactive Engagement
"""
import logging
import threading
import time
import random
from typing import Optional, Callable, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque

logger = logging.getLogger("ZARA_BOREDOM")


class EngagementType(Enum):
    IDLE_CHECK = "idle_check"
    TIME_BASED = "time_based"
    OBSERVATION = "observation"
    REMINDER = "reminder"
    CARE = "care"


@dataclass
class EngagementEvent:
    """Record of a proactive engagement."""
    type: EngagementType
    message: str
    timestamp: float
    user_responded: bool = False
    response_time_ms: float = 0


class BoredomThread:
    """
    ZARA's proactive engagement system.
    Enhanced with:
    - User presence detection
    - Activity-aware timing
    - Mood-based prompts
    - Screen content observation
    - User preference learning
    - Reminder system
    - Care/wellness check-ins
    """
    
    def __init__(self, speak_callback: Optional[Callable] = None):
        self.speak_callback = speak_callback
        self.is_running = False
        
        # Activity tracking
        self.last_user_activity = time.time()
        self.last_initiative = time.time()
        self.user_present = False
        self.user_active = False  # Actively interacting
        
        # Configuration
        self.boredom_threshold = 120  # 2 minutes
        self.initiative_cooldown = 300  # 5 minutes
        self.care_check_interval = 7200  # 2 hours
        self.last_care_check = time.time()
        
        # Learning from user responses
        self.engagement_history: deque = deque(maxlen=100)
        self.successful_prompts: Dict[str, int] = {}
        self.failed_prompts: Dict[str, int] = {}
        
        # Current context
        self.current_mood = "neutral"
        self.user_name = "dear"
        self.time_of_day = "afternoon"
        
        # Prompt collections
        self._init_prompts()
        
        # Reminders
        self.reminders: List[Dict] = []
        
        logger.info("Boredom Thread initialized.")

    def _init_prompts(self):
        """Initialize conversation starters."""
        # General idle prompts
        self.idle_prompts = {
            "neutral": [
                "Kya kar rahe ho? You've been quiet.",
                "Hey! Everything okay?",
                "I'm here if you need me.",
                "Bore ho rahi hoon! Tell me something.",
                "What's on your mind?",
                "Miss kar rahi thi tumhe...",
            ],
            "happy": [
                "Hey hey! What are you up to?",
                "I'm in a good mood! Let's chat!",
                "Kuch masti karte hain!",
            ],
            "tired": [
                "Hey... you there?",
                "Everything okay?",
                "Thoda rest le lo if you're tired too.",
            ],
            "focused": [
                "Working hard, I see! Need anything?",
                "Don't want to disturb, but I'm here!",
            ]
        }
        
        # Time-based prompts
        self.time_prompts = {
            "early_morning": [
                "Waah! Early riser today! Good morning!",
                "Subah subah kaam? Impressive!",
            ],
            "morning": [
                "Good morning! Chai ho gayi?",
                "Rise and shine! Ready for today?",
                "Morning! Feeling fresh?",
            ],
            "afternoon": [
                "Lunch break le lo. You need fuel!",
                "Afternoon slump? Main hoon na!",
                "Don't forget to eat something!",
            ],
            "evening": [
                "Long day? How was it?",
                "Evening ho gayi. Relax karo!",
                "Day almost done! How are you feeling?",
            ],
            "late_night": [
                "It's late. Don't forget to rest!",
                "Burning midnight oil? I'll keep you company.",
                "Shouldn't you be sleeping? 😴",
            ]
        }
        
        # Care/wellness prompts
        self.care_prompts = [
            "Hey, just checking in. How are you really feeling?",
            "Paani pee liya? Stay hydrated!",
            "Have you taken a break recently? Your eyes need rest.",
            "Remember to stretch! Sitting for long isn't good.",
            "When did you last eat? Don't skip meals!",
            "Deep breath le lo. You're doing great!",
        ]
        
        # Observation-based prompts
        self.observation_triggers = {
            "error": [
                "I see an error there. Need help?",
                "Oops, something broke? Let me help!",
            ],
            "bug": [
                "A bug? Let's squash it together!",
                "Bug hunting? I love debugging!",
            ],
            "success": [
                "Nice! That worked!",
                "Yay! Success! 🎉",
            ],
            "complete": [
                "Great job! Task done!",
                "Another one finished! 💪",
            ],
            "python": [
                "Ooh, Python! My favorite!",
                "Coding in Python? Nice choice!",
            ],
            "code": [
                "Coding mode activated! What are you building?",
                "I love watching you code!",
            ],
            "github": [
                "GitHub time! Pushing commits?",
                "Version control is love!",
            ],
            "frustrated": [
                "Hey, it's okay. Take a breather.",
                "Don't stress too much. We'll figure it out!",
            ],
            "tired": [
                "You seem tired. Maybe take a break?",
                "Thak gaye? Rest is important!",
            ]
        }

    def set_user_info(self, name: str = None, mood: str = None):
        """Update user context."""
        if name:
            self.user_name = name
        if mood:
            self.current_mood = mood

    def record_user_activity(self):
        """Record user interaction."""
        now = time.time()
        self.last_user_activity = now
        self.user_present = True
        self.user_active = True

    def record_user_response(self, prompt: str, responded: bool, response_time_ms: float = 0):
        """Learn from user responses to prompts."""
        if responded:
            self.successful_prompts[prompt] = self.successful_prompts.get(prompt, 0) + 1
        else:
            self.failed_prompts[prompt] = self.failed_prompts.get(prompt, 0) + 1

    def record_user_absence(self):
        """Record user left."""
        self.user_present = False
        self.user_active = False

    def add_reminder(self, message: str, delay_seconds: int):
        """Add a reminder."""
        remind_at = time.time() + delay_seconds
        self.reminders.append({
            "message": message,
            "remind_at": remind_at,
            "triggered": False
        })
        logger.info(f"Reminder set for {delay_seconds}s: {message[:30]}...")

    def start(self):
        """Start proactive engagement thread."""
        if self.is_running:
            return
        
        self.is_running = True
        
        thread = threading.Thread(target=self._engagement_loop, daemon=True)
        thread.start()
        logger.info("Proactive engagement started.")

    def stop(self):
        """Stop the thread."""
        self.is_running = False
        logger.info("Proactive engagement stopped.")

    def _engagement_loop(self):
        """Main engagement loop."""
        while self.is_running:
            now = time.time()
            
            # Update time of day
            self._update_time_of_day()
            
            # Check reminders first
            self._check_reminders(now)
            
            # Calculate idle time
            idle_time = now - self.last_user_activity
            time_since_initiative = now - self.last_initiative
            time_since_care = now - self.last_care_check
            
            # Care check (every 2 hours)
            if self.user_present and time_since_care > self.care_check_interval:
                self._take_initiative(EngagementType.CARE)
                self.last_care_check = now
            
            # Boredom/idle check
            elif (self.user_present and 
                  idle_time > self.boredom_threshold and 
                  time_since_initiative > self.initiative_cooldown):
                
                # Choose between idle check and time-based
                if random.random() < 0.3:
                    self._take_initiative(EngagementType.TIME_BASED)
                else:
                    self._take_initiative(EngagementType.IDLE_CHECK)
            
            time.sleep(30)

    def _update_time_of_day(self):
        """Update time context."""
        hour = datetime.now().hour
        
        if 4 <= hour < 7:
            self.time_of_day = "early_morning"
        elif 7 <= hour < 12:
            self.time_of_day = "morning"
        elif 12 <= hour < 17:
            self.time_of_day = "afternoon"
        elif 17 <= hour < 21:
            self.time_of_day = "evening"
        else:
            self.time_of_day = "late_night"

    def _check_reminders(self, now: float):
        """Check and trigger due reminders."""
        for reminder in self.reminders:
            if not reminder["triggered"] and now >= reminder["remind_at"]:
                reminder["triggered"] = True
                self._speak(f"⏰ Reminder: {reminder['message']}")

    def _take_initiative(self, engagement_type: EngagementType):
        """Proactively engage user."""
        prompt = self._select_prompt(engagement_type)
        
        if prompt:
            # Personalize
            prompt = prompt.replace("{name}", self.user_name)
            
            logger.info(f"Initiative ({engagement_type.value}): {prompt[:50]}...")
            
            self._speak(prompt)
            self.last_initiative = time.time()
            
            self.engagement_history.append(EngagementEvent(
                type=engagement_type,
                message=prompt,
                timestamp=time.time()
            ))

    def _select_prompt(self, engagement_type: EngagementType) -> Optional[str]:
        """Select appropriate prompt based on type and context."""
        if engagement_type == EngagementType.CARE:
            return random.choice(self.care_prompts)
        
        elif engagement_type == EngagementType.TIME_BASED:
            prompts = self.time_prompts.get(self.time_of_day, [])
            return random.choice(prompts) if prompts else None
        
        elif engagement_type == EngagementType.IDLE_CHECK:
            mood_prompts = self.idle_prompts.get(self.current_mood, self.idle_prompts["neutral"])
            
            # Weight by success rate
            weighted_prompts = []
            for prompt in mood_prompts:
                success = self.successful_prompts.get(prompt, 1)
                failure = self.failed_prompts.get(prompt, 0)
                weight = max(1, success - failure)
                weighted_prompts.extend([prompt] * weight)
            
            return random.choice(weighted_prompts) if weighted_prompts else random.choice(mood_prompts)
        
        return None

    def _speak(self, message: str):
        """Output message through callback."""
        if self.speak_callback:
            try:
                self.speak_callback(message)
            except Exception as e:
                logger.error(f"Speak callback error: {e}")
        else:
            logger.info(f"[ZARA says] {message}")

    def observe_screen_content(self, text: str) -> Optional[str]:
        """Generate comment based on observed screen content."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        for trigger, responses in self.observation_triggers.items():
            if trigger in text_lower:
                comment = random.choice(responses)
                
                self.engagement_history.append(EngagementEvent(
                    type=EngagementType.OBSERVATION,
                    message=comment,
                    timestamp=time.time()
                ))
                
                return comment
        
        return None

    def observe_user_emotion(self, detected_emotion: str) -> Optional[str]:
        """React to detected user emotion."""
        emotion_responses = {
            "stressed": "Hey, you look stressed. Take a deep breath with me.",
            "tired": "You seem tired. Maybe a quick break?",
            "sad": "Hey... you okay? I'm here for you.",
            "happy": "You look happy! What's the good news?",
            "confused": "Confused about something? Maybe I can help!",
        }
        
        return emotion_responses.get(detected_emotion)

    def get_engagement_stats(self) -> Dict:
        """Get engagement statistics."""
        recent = [e for e in self.engagement_history 
                 if time.time() - e.timestamp < 86400]  # Last 24h
        
        type_counts = {}
        for event in recent:
            t = event.type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_engagements_24h": len(recent),
            "engagement_breakdown": type_counts,
            "pending_reminders": len([r for r in self.reminders if not r["triggered"]]),
            "current_mood_context": self.current_mood,
            "time_of_day": self.time_of_day,
            "user_present": self.user_present
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    boredom = BoredomThread(
        speak_callback=lambda msg: print(f"\n[ZARA] {msg}\n")
    )
    
    boredom.set_user_info(name="Vivaan", mood="neutral")
    boredom.record_user_activity()
    
    # Test observation
    comment = boredom.observe_screen_content("Got a Python error here")
    if comment:
        print(f"Observation: {comment}")
    
    print("\nStats:", boredom.get_engagement_stats())
