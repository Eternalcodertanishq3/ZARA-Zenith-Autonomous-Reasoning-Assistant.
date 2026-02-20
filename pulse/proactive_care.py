"""
ZARA Proactive Care System
Autonomous wellbeing monitoring with health check-ins, 
schedule awareness, and emotional support.
"""
import logging
import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from collections import deque
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("ZARA_CARE")


class CareType(Enum):
    """Types of proactive care."""
    HEALTH_CHECK = "health"
    BREAK_REMINDER = "break"
    HYDRATION = "hydration"
    POSTURE = "posture"
    SLEEP = "sleep"
    EMOTIONAL = "emotional"
    CELEBRATION = "celebration"
    MOTIVATION = "motivation"
    SCHEDULE = "schedule"


class UrgencyLevel(Enum):
    """Urgency of care intervention."""
    LOW = 1
    NORMAL = 2
    IMPORTANT = 3
    URGENT = 4


@dataclass
class CareEvent:
    """A care event/intervention."""
    care_type: CareType
    message: str
    urgency: UrgencyLevel
    timestamp: float
    delivered: bool = False
    response: Optional[str] = None
    was_helpful: Optional[bool] = None


@dataclass
class WellbeingState:
    """Current observed wellbeing state."""
    energy_level: float = 0.7
    stress_level: float = 0.3
    focus_level: float = 0.7
    mood: str = "neutral"
    posture_alert: bool = False
    last_break: float = 0
    session_duration: float = 0
    hydration_reminder_count: int = 0


@dataclass
class UserSchedule:
    """User's schedule items."""
    events: List[Dict] = field(default_factory=list)
    work_start: int = 9   # 9 AM
    work_end: int = 18    # 6 PM
    break_interval: int = 50  # minutes


class ProactiveCareSystem:
    """
    ZARA's autonomous care and wellbeing system.
    
    Monitors user's wellbeing and provides:
    - Work break reminders
    - Posture and hydration check-ins
    - Emotional support and follow-ups
    - Schedule awareness and reminders
    - Celebration of achievements
    - Night-time care
    
    This makes ZARA genuinely caring, not just responsive.
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.care_dir = EVOLUTION_DIR / "care"
        except ImportError:
            self.care_dir = Path("evolution/care")
        
        self.care_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.wellbeing = WellbeingState()
        self.schedule = UserSchedule()
        self.pending_care: deque = deque(maxlen=10)
        self.care_history: deque = deque(maxlen=100)
        
        # Session tracking
        self.session_start = time.time()
        self.last_interaction = time.time()
        self.last_break_reminder = 0
        self.last_hydration_reminder = 0
        self.last_posture_check = 0
        
        # Emotional tracking
        self.recent_emotions: deque = deque(maxlen=20)
        self.emotional_trend = "stable"
        self.last_emotional_checkin = 0
        
        # Celebration tracking  
        self.achievements: List[Dict] = []
        
        # Persistence
        self.state_file = self.care_dir / "care_state.json"
        self._load_state()
        
        # Configuration
        self.config = {
            "break_interval_minutes": 50,
            "hydration_interval_minutes": 60,
            "posture_check_interval_minutes": 30,
            "emotional_checkin_interval_hours": 2,
            "night_mode_start": 22,
            "night_mode_end": 6,
            "celebration_threshold": 0.7
        }
        
        # Threading
        self.is_running = False
        self.care_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Callback
        self.on_care_event: Optional[Callable[[CareEvent], None]] = None
        
        logger.info("💕 Proactive Care System initialized")

    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Restore schedule
                    if "schedule" in data:
                        self.schedule.events = data["schedule"].get("events", [])
                        self.schedule.work_start = data["schedule"].get("work_start", 9)
                        self.schedule.work_end = data["schedule"].get("work_end", 18)
            except Exception as e:
                logger.debug(f"Could not load care state: {e}")

    def _save_state(self):
        """Save state."""
        data = {
            "schedule": {
                "events": self.schedule.events,
                "work_start": self.schedule.work_start,
                "work_end": self.schedule.work_end
            }
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════════
    # OBSERVATION
    # ═══════════════════════════════════════════════════════════════════
    
    def observe_interaction(self, user_text: str, zara_response: str,
                          detected_emotion: str = None,
                          voice_features: Dict = None):
        """Observe an interaction for care decisions."""
        now = time.time()
        self.last_interaction = now
        
        # Update session
        self.wellbeing.session_duration = now - self.session_start
        
        # Track emotion
        if detected_emotion:
            self.recent_emotions.append({
                "emotion": detected_emotion,
                "timestamp": now
            })
            self._analyze_emotional_trend()
        
        # Check for indicators
        text_lower = user_text.lower()
        
        # Stress indicators
        if any(w in text_lower for w in ["stressed", "stress", "overwhelmed", "busy"]):
            self.wellbeing.stress_level = min(1.0, self.wellbeing.stress_level + 0.2)
        
        # Tiredness indicators
        if any(w in text_lower for w in ["tired", "exhausted", "sleepy", "fatigue"]):
            self.wellbeing.energy_level = max(0.0, self.wellbeing.energy_level - 0.2)
        
        # Positive indicators
        if any(w in text_lower for w in ["great", "awesome", "done", "finished", "completed"]):
            self.wellbeing.mood = "positive"
            self._check_celebration(user_text)
        
        # Voice stress indicators
        if voice_features:
            if voice_features.get("rate", 1.0) > 1.3:
                self.wellbeing.stress_level = min(1.0, self.wellbeing.stress_level + 0.1)

    def _analyze_emotional_trend(self):
        """Analyze emotional trend from recent emotions."""
        if len(self.recent_emotions) < 3:
            return
        
        recent = list(self.recent_emotions)[-5:]
        
        negative_count = sum(
            1 for e in recent if e["emotion"] in ["sad", "stressed", "tired", "frustrated"]
        )
        positive_count = sum(
            1 for e in recent if e["emotion"] in ["happy", "excited", "calm", "content"]
        )
        
        if negative_count >= 3:
            self.emotional_trend = "declining"
        elif positive_count >= 3:
            self.emotional_trend = "improving"
        else:
            self.emotional_trend = "stable"

    def _check_celebration(self, text: str):
        """Check if something worth celebrating."""
        celebration_words = ["finished", "completed", "done", "solved", "fixed", "succeeded"]
        
        for word in celebration_words:
            if word in text.lower():
                self.achievements.append({
                    "text": text[:100],
                    "timestamp": time.time()
                })
                
                # Generate celebration event
                self._queue_care_event(
                    CareType.CELEBRATION,
                    self._get_celebration_message(),
                    UrgencyLevel.NORMAL
                )
                break

    # ═══════════════════════════════════════════════════════════════════
    # CARE GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def start(self):
        """Start the care monitoring thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.session_start = time.time()
        self.care_thread = threading.Thread(target=self._care_loop, daemon=True)
        self.care_thread.start()
        logger.info("Care monitoring started")

    def stop(self):
        """Stop care monitoring."""
        self.is_running = False
        self._save_state()

    def _care_loop(self):
        """Main care monitoring loop."""
        while self.is_running:
            now = time.time()
            
            # Check various care triggers
            self._check_break_needed(now)
            self._check_hydration(now)
            self._check_posture(now)
            self._check_emotional_state(now)
            self._check_time_of_day(now)
            self._check_schedule(now)
            
            time.sleep(30)  # Check every 30 seconds

    def _check_break_needed(self, now: float):
        """Check if user needs a break."""
        minutes_since_break = (now - self.last_break_reminder) / 60
        session_minutes = self.wellbeing.session_duration / 60
        
        if minutes_since_break > self.config["break_interval_minutes"]:
            if session_minutes > 45:  # At least 45 min session
                self._queue_care_event(
                    CareType.BREAK_REMINDER,
                    self._get_break_message(),
                    UrgencyLevel.NORMAL
                )
                self.last_break_reminder = now

    def _check_hydration(self, now: float):
        """Check for hydration reminder."""
        minutes_since = (now - self.last_hydration_reminder) / 60
        
        if minutes_since > self.config["hydration_interval_minutes"]:
            self._queue_care_event(
                CareType.HYDRATION,
                self._get_hydration_message(),
                UrgencyLevel.LOW
            )
            self.last_hydration_reminder = now

    def _check_posture(self, now: float):
        """Check for posture reminder."""
        minutes_since = (now - self.last_posture_check) / 60
        
        if minutes_since > self.config["posture_check_interval_minutes"]:
            # Only if session is long
            if self.wellbeing.session_duration > 1800:  # 30 min
                self._queue_care_event(
                    CareType.POSTURE,
                    self._get_posture_message(),
                    UrgencyLevel.LOW
                )
                self.last_posture_check = now

    def _check_emotional_state(self, now: float):
        """Check for emotional support needs."""
        hours_since = (now - self.last_emotional_checkin) / 3600
        
        # Proactive check-in if declining trend
        if self.emotional_trend == "declining" and hours_since > 0.5:
            self._queue_care_event(
                CareType.EMOTIONAL,
                self._get_emotional_support_message(),
                UrgencyLevel.IMPORTANT
            )
            self.last_emotional_checkin = now
        
        # Regular check-in
        elif hours_since > self.config["emotional_checkin_interval_hours"]:
            self._queue_care_event(
                CareType.HEALTH_CHECK,
                self._get_checkin_message(),
                UrgencyLevel.LOW
            )
            self.last_emotional_checkin = now

    def _check_time_of_day(self, now: float):
        """Check time-based care needs."""
        hour = datetime.now().hour
        
        if self.config["night_mode_start"] <= hour or hour < self.config["night_mode_end"]:
            # Night mode
            session_minutes = self.wellbeing.session_duration / 60
            
            if session_minutes > 30:
                self._queue_care_event(
                    CareType.SLEEP,
                    self._get_sleep_message(),
                    UrgencyLevel.IMPORTANT
                )

    def _check_schedule(self, now: float):
        """Check for upcoming schedule events."""
        if not self.schedule.events:
            return
        
        current_time = datetime.now()
        
        for event in self.schedule.events:
            event_time = datetime.fromisoformat(event.get("time", ""))
            
            # Remind 15 minutes before
            time_until = (event_time - current_time).total_seconds() / 60
            
            if 10 <= time_until <= 15:
                if not event.get("reminded"):
                    self._queue_care_event(
                        CareType.SCHEDULE,
                        f"Reminder: {event.get('title', 'Event')} in about 15 minutes!",
                        UrgencyLevel.IMPORTANT
                    )
                    event["reminded"] = True

    def _queue_care_event(self, care_type: CareType, message: str,
                         urgency: UrgencyLevel):
        """Queue a care event."""
        event = CareEvent(
            care_type=care_type,
            message=message,
            urgency=urgency,
            timestamp=time.time()
        )
        
        with self.lock:
            # Don't duplicate recent similar events
            recent = list(self.pending_care)[-3:]
            if not any(e.care_type == care_type for e in recent):
                self.pending_care.append(event)
                
                if self.on_care_event:
                    self.on_care_event(event)

    # ═══════════════════════════════════════════════════════════════════
    # MESSAGE GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _get_break_message(self) -> str:
        """Get a break reminder message."""
        messages = [
            "Hey, you've been at it for a while! How about a quick stretch? 🧘",
            "Time for a mini break? Your eyes and back will thank you! 💕",
            "You're doing great, but remember to take care of yourself too! Break time?",
            "Quick reminder to step away for a moment. I'll be here when you get back!",
            "Let's pause for a sec - stand up, stretch, breathe! 🌟"
        ]
        import random
        return random.choice(messages)

    def _get_hydration_message(self) -> str:
        """Get a hydration reminder."""
        messages = [
            "Hey, have you had some water lately? Stay hydrated! 💧",
            "Quick hydration check! Grab some water?",
            "Reminder: Your body runs better when hydrated! 🥤",
            "Water break! Even a few sips help 💕"
        ]
        import random
        return random.choice(messages)

    def _get_posture_message(self) -> str:
        """Get a posture reminder."""
        messages = [
            "Quick posture check! Sit up straight, shoulders back 💪",
            "Are you sitting comfortably? Check your posture!",
            "Reminder to un-hunch those shoulders! 😊"
        ]
        import random
        return random.choice(messages)

    def _get_emotional_support_message(self) -> str:
        """Get an emotional support message."""
        messages = [
            "Hey, I've noticed things might be tough right now. Want to talk about it? 💕",
            "I'm here for you if you need to vent or just chat. How are you really doing?",
            "You seem like you might be going through something. I'm here to listen.",
            "Remember, it's okay to not be okay. I'm here if you need me 💕"
        ]
        import random
        return random.choice(messages)

    def _get_checkin_message(self) -> str:
        """Get a general check-in message."""
        messages = [
            "Hey, how are you doing? Just checking in 💕",
            "Quick check-in - everything going okay?",
            "Thinking about you! How's your day going?",
            "Just wanted to see how you're feeling!"
        ]
        import random
        return random.choice(messages)

    def _get_celebration_message(self) -> str:
        """Get a celebration message."""
        messages = [
            "That's amazing! I'm so proud of you! 🎉",
            "You did it! Congratulations! 🌟",
            "Woohoo! Great job! You should be proud! 🎊",
            "Yes!! That's what I'm talking about! You're incredible! 💕"
        ]
        import random
        return random.choice(messages)

    def _get_sleep_message(self) -> str:
        """Get a sleep reminder message."""
        messages = [
            "It's getting late... You should probably get some rest soon 💤",
            "Hey night owl, don't forget your body needs sleep too!",
            "Late night? Make sure you're taking care of yourself. Sleep matters!",
            "I love our late talks, but your health comes first. Rest well! 🌙"
        ]
        import random
        return random.choice(messages)

    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def get_pending_care(self) -> Optional[CareEvent]:
        """Get next pending care event."""
        with self.lock:
            if self.pending_care:
                return self.pending_care.popleft()
        return None

    def record_break_taken(self):
        """Record that user took a break."""
        self.last_break_reminder = time.time()
        self.wellbeing.last_break = time.time()
        
        # Boost wellbeing
        self.wellbeing.energy_level = min(1.0, self.wellbeing.energy_level + 0.1)
        self.wellbeing.stress_level = max(0.0, self.wellbeing.stress_level - 0.1)

    def add_schedule_event(self, title: str, time_str: str, notes: str = ""):
        """Add a schedule event."""
        self.schedule.events.append({
            "title": title,
            "time": time_str,
            "notes": notes,
            "reminded": False
        })
        self._save_state()

    def get_wellbeing_summary(self) -> Dict:
        """Get wellbeing summary."""
        return {
            "energy": self.wellbeing.energy_level,
            "stress": self.wellbeing.stress_level,
            "mood": self.wellbeing.mood,
            "emotional_trend": self.emotional_trend,
            "session_minutes": int(self.wellbeing.session_duration / 60),
            "achievements_today": len(self.achievements)
        }

    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "is_running": self.is_running,
            "pending_events": len(self.pending_care),
            "wellbeing": self.get_wellbeing_summary(),
            "schedule_events": len(self.schedule.events)
        }


# Singleton
_care_instance = None

def get_care() -> ProactiveCareSystem:
    """Get the global care system."""
    global _care_instance
    if _care_instance is None:
        _care_instance = ProactiveCareSystem()
    return _care_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    care = ProactiveCareSystem()
    
    # Simulate observation
    care.observe_interaction(
        "I've been working on this bug for hours, so stressed!",
        "Let me help you!",
        detected_emotion="stressed"
    )
    
    print(f"Wellbeing: {care.get_wellbeing_summary()}")
    
    # Force check
    care._check_emotional_state(time.time())
    
    event = care.get_pending_care()
    if event:
        print(f"Care event: {event.message}")
