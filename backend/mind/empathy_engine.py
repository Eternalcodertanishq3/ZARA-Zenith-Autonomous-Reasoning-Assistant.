"""
ZARA Anticipatory Empathy Engine v1.0
======================================
Predictive Mood Forecast System

This is ZARA's emotional intelligence core that:
1. Tracks emotional patterns over time (hours, days, weeks)
2. Learns YOUR personal baselines and patterns
3. Detects early warning signs BEFORE you're aware
4. Proactively prepares support before you need it

Key Innovations:
- Micro-expression velocity tracking (rate of change)
- Physiological pattern recognition (blink rate, posture shifts)
- Temporal mood modeling (time-of-day, day-of-week patterns)
- Stress accumulation detection (compounding fatigue)
- Anticipatory intervention triggers
"""

import logging
import json
import time
import threading
import numpy as np
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
import statistics

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_EMPATHY")


# ═══════════════════════════════════════════════════════════════════════════
# EMOTIONAL STATES & PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════

class MoodState(Enum):
    """Granular mood states for prediction."""
    EXCELLENT = "excellent"      # Peak positive
    HAPPY = "happy"              # Positive
    CONTENT = "content"          # Neutral-positive
    NEUTRAL = "neutral"          # Baseline
    SLIGHTLY_DOWN = "slightly_down"  # Early warning
    STRESSED = "stressed"        # Needs attention
    EXHAUSTED = "exhausted"      # Critical fatigue
    ANXIOUS = "anxious"          # Worry-based stress
    FRUSTRATED = "frustrated"    # Task-based stress
    OVERWHELMED = "overwhelmed"  # Capacity exceeded


class MoodTrend(Enum):
    """Direction of emotional change."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class AlertLevel(Enum):
    """Intervention urgency levels."""
    NONE = 0
    SUBTLE = 1      # Gentle observation
    PROACTIVE = 2   # Anticipatory support
    ACTIVE = 3      # Direct intervention
    URGENT = 4      # Immediate attention


@dataclass
class MoodSnapshot:
    """Single point-in-time emotional reading."""
    timestamp: float
    mood: MoodState
    valence: float          # -1 (negative) to +1 (positive)
    arousal: float          # 0 (calm) to 1 (activated)
    fatigue: float          # 0-1
    stress: float           # 0-1
    attention: float        # 0-1
    confidence: float       # How confident we are in this reading
    
    # Physiological indicators
    blink_rate: float = 0.0
    micro_expressions: List[str] = field(default_factory=list)
    head_movement: float = 0.0
    
    # Context
    activity: str = "unknown"
    time_of_day: str = "unknown"


@dataclass
class MoodPrediction:
    """Predicted future emotional state."""
    predicted_mood: MoodState
    probability: float              # 0-1 confidence
    time_horizon_minutes: int       # How far ahead
    predicted_valence: float
    predicted_fatigue: float
    predicted_stress: float
    trend: MoodTrend
    warning_signs: List[str]
    recommended_interventions: List[str]


@dataclass
class EmotionalForecast:
    """Complete mood forecast report."""
    timestamp: float
    current_mood: MoodState
    current_valence: float
    current_trend: MoodTrend
    
    # Predictions
    prediction_15min: MoodPrediction
    prediction_30min: MoodPrediction
    prediction_1hour: MoodPrediction
    
    # Alert
    alert_level: AlertLevel
    primary_concern: str
    anticipatory_actions: List[str]
    
    # Personalization
    deviation_from_baseline: float  # How far from your typical state
    pattern_match: str              # "Similar to Tuesday evenings"


# ═══════════════════════════════════════════════════════════════════════════
# MOOD SENSORS - Data Collection
# ═══════════════════════════════════════════════════════════════════════════

class MoodSensor:
    """
    Collects raw emotional data from various sources.
    Integrates with existing ZARA systems.
    """
    
    def __init__(self):
        self._awareness = None
        self._gaze = None
        self.last_reading: Optional[MoodSnapshot] = None
    
    def _get_awareness(self):
        """Get environmental awareness system."""
        if self._awareness is None:
            try:
                from eyes.environmental_awareness import get_environmental_awareness
                self._awareness = get_environmental_awareness()
            except Exception as e:
                logger.debug(f"Environmental awareness unavailable: {e}")
        return self._awareness
    
    def read(self) -> Optional[MoodSnapshot]:
        """Take a mood reading from all available sensors."""
        try:
            awareness = self._get_awareness()
            
            if awareness is None:
                return self._synthetic_reading()
            
            ctx = awareness.get_context()
            user = ctx.user
            
            # Map emotion string to mood state
            mood = self._emotion_to_mood(user.emotion)
            
            # Calculate valence and arousal
            valence = self._calculate_valence(user.emotion, user.fatigue_level)
            arousal = self._calculate_arousal(user.attention_score, user.blink_rate)
            
            snapshot = MoodSnapshot(
                timestamp=time.time(),
                mood=mood,
                valence=valence,
                arousal=arousal,
                fatigue=user.fatigue_level,
                stress=self._estimate_stress(user),
                attention=user.attention_score,
                confidence=0.8 if user.face_visible else 0.3,
                blink_rate=user.blink_rate,
                micro_expressions=user.micro_expressions,
                head_movement=abs(user.head_pose[0]) + abs(user.head_pose[1]),
                activity=ctx.activity.value,
                time_of_day=ctx.time_context.value
            )
            
            self.last_reading = snapshot
            return snapshot
            
        except Exception as e:
            logger.debug(f"Sensor read error: {e}")
            return self._synthetic_reading()
    
    def _emotion_to_mood(self, emotion: str) -> MoodState:
        """Map emotion string to MoodState."""
        mapping = {
            "happy": MoodState.HAPPY,
            "excited": MoodState.EXCELLENT,
            "neutral": MoodState.NEUTRAL,
            "focused": MoodState.CONTENT,
            "sad": MoodState.SLIGHTLY_DOWN,
            "stressed": MoodState.STRESSED,
            "tired": MoodState.EXHAUSTED,
            "angry": MoodState.FRUSTRATED,
            "confused": MoodState.ANXIOUS,
            "surprised": MoodState.NEUTRAL,
        }
        return mapping.get(emotion.lower(), MoodState.NEUTRAL)
    
    def _calculate_valence(self, emotion: str, fatigue: float) -> float:
        """Calculate emotional valence (-1 to +1)."""
        base_valence = {
            "happy": 0.8, "excited": 0.9, "neutral": 0.0,
            "focused": 0.3, "sad": -0.6, "stressed": -0.5,
            "tired": -0.3, "angry": -0.7, "confused": -0.2
        }
        valence = base_valence.get(emotion.lower(), 0.0)
        # Fatigue pulls valence down
        valence -= fatigue * 0.3
        return max(-1.0, min(1.0, valence))
    
    def _calculate_arousal(self, attention: float, blink_rate: float) -> float:
        """Calculate arousal level (0-1)."""
        # High attention = higher arousal
        # High blink rate might indicate stress (higher arousal) OR fatigue (lower arousal)
        arousal = attention * 0.6
        if blink_rate > 25:  # High blink rate
            arousal += 0.2  # Probably stress
        elif blink_rate < 10:  # Low blink rate
            arousal += 0.1  # Focused
        return max(0.0, min(1.0, arousal))
    
    def _estimate_stress(self, user) -> float:
        """Estimate stress level from various indicators."""
        stress = 0.0
        
        # Micro-expressions indicating stress
        stress_expressions = ["tense", "furrowed", "clenched", "tight"]
        for expr in user.micro_expressions:
            if any(s in expr.lower() for s in stress_expressions):
                stress += 0.2
        
        # High fatigue correlates with stress
        stress += user.fatigue_level * 0.3
        
        # Low attention might indicate overwhelm
        stress += (1 - user.attention_score) * 0.2
        
        # Emotion-based stress
        if user.emotion in ["stressed", "angry", "anxious"]:
            stress += 0.4
        
        return min(1.0, stress)
    
    def _synthetic_reading(self) -> MoodSnapshot:
        """Generate synthetic reading when sensors unavailable."""
        hour = datetime.now().hour
        
        # Time-based baseline assumptions
        if 0 <= hour < 6:
            mood = MoodState.EXHAUSTED
            fatigue = 0.7
        elif 6 <= hour < 10:
            mood = MoodState.NEUTRAL
            fatigue = 0.3
        elif 10 <= hour < 14:
            mood = MoodState.CONTENT
            fatigue = 0.2
        elif 14 <= hour < 18:
            mood = MoodState.SLIGHTLY_DOWN
            fatigue = 0.4
        else:
            mood = MoodState.NEUTRAL
            fatigue = 0.5
        
        return MoodSnapshot(
            timestamp=time.time(),
            mood=mood,
            valence=0.0,
            arousal=0.5,
            fatigue=fatigue,
            stress=0.3,
            attention=0.6,
            confidence=0.2,  # Low confidence for synthetic
            time_of_day=self._get_time_of_day(hour)
        )
    
    def _get_time_of_day(self, hour: int) -> str:
        """Get time of day string."""
        if 0 <= hour < 5:
            return "late_night"
        elif 5 <= hour < 8:
            return "early_morning"
        elif 8 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN LEARNER - Personal Baselines
# ═══════════════════════════════════════════════════════════════════════════

class PatternLearner:
    """
    Learns personal emotional patterns and baselines.
    Tracks daily, weekly, and situational patterns.
    """
    
    def __init__(self, data_file: Path = None):
        self.data_file = data_file or Path("memory/emotional_patterns.json")
        
        # Historical data
        self.mood_history: deque = deque(maxlen=10000)  # ~3 days at 1/minute
        
        # Learned baselines
        self.hourly_baselines: Dict[int, Dict] = {}   # Average mood by hour
        self.daily_baselines: Dict[str, Dict] = {}    # Average mood by day of week
        self.activity_baselines: Dict[str, Dict] = {}  # Average mood by activity
        
        # Velocity tracking (rate of change)
        self.valence_velocity: deque = deque(maxlen=30)
        self.fatigue_velocity: deque = deque(maxlen=30)
        self.stress_velocity: deque = deque(maxlen=30)
        
        # Load existing patterns
        self._load_patterns()
    
    def record(self, snapshot: MoodSnapshot):
        """Record a new mood snapshot and update patterns."""
        self.mood_history.append(snapshot)
        
        # Update velocities (rate of change)
        if len(self.mood_history) >= 2:
            prev = self.mood_history[-2]
            dt = snapshot.timestamp - prev.timestamp
            if dt > 0:
                self.valence_velocity.append((snapshot.valence - prev.valence) / dt)
                self.fatigue_velocity.append((snapshot.fatigue - prev.fatigue) / dt)
                self.stress_velocity.append((snapshot.stress - prev.stress) / dt)
        
        # Update baselines periodically
        if len(self.mood_history) % 60 == 0:  # Every hour
            self._update_baselines()
    
    def _update_baselines(self):
        """Update learned baselines from history."""
        if len(self.mood_history) < 100:
            return
        
        # Group by hour
        hourly_data: Dict[int, List] = {h: [] for h in range(24)}
        for snap in self.mood_history:
            hour = datetime.fromtimestamp(snap.timestamp).hour
            hourly_data[hour].append(snap)
        
        # Calculate hourly baselines
        for hour, snaps in hourly_data.items():
            if snaps:
                self.hourly_baselines[hour] = {
                    "valence": statistics.mean(s.valence for s in snaps),
                    "fatigue": statistics.mean(s.fatigue for s in snaps),
                    "stress": statistics.mean(s.stress for s in snaps),
                    "attention": statistics.mean(s.attention for s in snaps),
                    "count": len(snaps)
                }
        
        # Group by day of week
        daily_data: Dict[str, List] = {}
        for snap in self.mood_history:
            day = datetime.fromtimestamp(snap.timestamp).strftime("%A")
            if day not in daily_data:
                daily_data[day] = []
            daily_data[day].append(snap)
        
        for day, snaps in daily_data.items():
            if snaps:
                self.daily_baselines[day] = {
                    "valence": statistics.mean(s.valence for s in snaps),
                    "fatigue": statistics.mean(s.fatigue for s in snaps),
                    "stress": statistics.mean(s.stress for s in snaps),
                    "count": len(snaps)
                }
        
        # Group by activity
        activity_data: Dict[str, List] = {}
        for snap in self.mood_history:
            activity = snap.activity
            if activity not in activity_data:
                activity_data[activity] = []
            activity_data[activity].append(snap)
        
        for activity, snaps in activity_data.items():
            if snaps:
                self.activity_baselines[activity] = {
                    "valence": statistics.mean(s.valence for s in snaps),
                    "fatigue": statistics.mean(s.fatigue for s in snaps),
                    "stress": statistics.mean(s.stress for s in snaps),
                    "count": len(snaps)
                }
        
        # Save periodically
        self._save_patterns()
    
    def get_baseline(self) -> Dict:
        """Get current expected baseline based on time and day."""
        now = datetime.now()
        hour = now.hour
        day = now.strftime("%A")
        
        baseline = {
            "valence": 0.0,
            "fatigue": 0.3,
            "stress": 0.3,
            "attention": 0.6
        }
        
        # Blend hourly and daily baselines
        if hour in self.hourly_baselines:
            hourly = self.hourly_baselines[hour]
            for key in baseline:
                if key in hourly:
                    baseline[key] = hourly[key]
        
        if day in self.daily_baselines:
            daily = self.daily_baselines[day]
            for key in baseline:
                if key in daily:
                    # Blend 70% hourly, 30% daily
                    baseline[key] = baseline[key] * 0.7 + daily[key] * 0.3
        
        return baseline
    
    def get_deviation(self, snapshot: MoodSnapshot) -> float:
        """Calculate how far current state deviates from baseline."""
        baseline = self.get_baseline()
        
        deviation = 0.0
        deviation += abs(snapshot.valence - baseline["valence"])
        deviation += abs(snapshot.fatigue - baseline["fatigue"])
        deviation += abs(snapshot.stress - baseline["stress"])
        deviation += abs(snapshot.attention - baseline["attention"])
        
        return deviation / 4  # Normalize to 0-1ish range
    
    def get_velocities(self) -> Dict[str, float]:
        """Get current rate of change for emotional metrics."""
        return {
            "valence": statistics.mean(self.valence_velocity) if self.valence_velocity else 0.0,
            "fatigue": statistics.mean(self.fatigue_velocity) if self.fatigue_velocity else 0.0,
            "stress": statistics.mean(self.stress_velocity) if self.stress_velocity else 0.0,
        }
    
    def find_similar_pattern(self, snapshot: MoodSnapshot) -> str:
        """Find historical pattern similar to current state."""
        now = datetime.now()
        hour = now.hour
        day = now.strftime("%A")
        
        # Check if this matches typical patterns
        if day in self.daily_baselines:
            daily = self.daily_baselines[day]
            if abs(snapshot.valence - daily.get("valence", 0)) < 0.2:
                return f"Typical for {day}s"
        
        if hour in self.hourly_baselines:
            hourly = self.hourly_baselines[hour]
            if abs(snapshot.fatigue - hourly.get("fatigue", 0)) < 0.2:
                return f"Normal for {hour}:00"
        
        return "Unusual pattern"
    
    def _save_patterns(self):
        """Save learned patterns to disk."""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "hourly_baselines": self.hourly_baselines,
                "daily_baselines": self.daily_baselines,
                "activity_baselines": self.activity_baselines,
                "updated": time.time()
            }
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save patterns: {e}")
    
    def _load_patterns(self):
        """Load learned patterns from disk."""
        try:
            if self.data_file.exists():
                with open(self.data_file) as f:
                    data = json.load(f)
                self.hourly_baselines = {int(k): v for k, v in data.get("hourly_baselines", {}).items()}
                self.daily_baselines = data.get("daily_baselines", {})
                self.activity_baselines = data.get("activity_baselines", {})
                logger.info(f"📊 Loaded emotional patterns: {len(self.hourly_baselines)} hourly, {len(self.daily_baselines)} daily")
        except Exception as e:
            logger.debug(f"Could not load patterns: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# MOOD PREDICTOR - Anticipatory Forecasting
# ═══════════════════════════════════════════════════════════════════════════

class MoodPredictor:
    """
    Predicts future mood states using pattern analysis and velocity tracking.
    The core of anticipatory empathy.
    """
    
    def __init__(self, pattern_learner: PatternLearner):
        self.patterns = pattern_learner
        
        # Warning sign weights
        self.warning_weights = {
            "rising_fatigue": 0.3,
            "rising_stress": 0.35,
            "declining_valence": 0.25,
            "declining_attention": 0.2,
            "high_deviation": 0.15,
            "late_hour": 0.1,
            "long_session": 0.15,
        }
    
    def predict(self, snapshot: MoodSnapshot, history: deque, 
                horizon_minutes: int = 30) -> MoodPrediction:
        """Predict mood state N minutes into the future."""
        
        # Get current velocities
        velocities = self.patterns.get_velocities()
        
        # Calculate trajectory
        predicted_valence = snapshot.valence + (velocities["valence"] * horizon_minutes * 60)
        predicted_fatigue = snapshot.fatigue + (velocities["fatigue"] * horizon_minutes * 60)
        predicted_stress = snapshot.stress + (velocities["stress"] * horizon_minutes * 60)
        
        # Clamp values
        predicted_valence = max(-1.0, min(1.0, predicted_valence))
        predicted_fatigue = max(0.0, min(1.0, predicted_fatigue))
        predicted_stress = max(0.0, min(1.0, predicted_stress))
        
        # Determine predicted mood state
        predicted_mood = self._valence_to_mood(
            predicted_valence, predicted_fatigue, predicted_stress
        )
        
        # Calculate trend
        trend = self._calculate_trend(velocities)
        
        # Identify warning signs
        warning_signs = self._identify_warnings(
            snapshot, velocities, predicted_fatigue, predicted_stress
        )
        
        # Generate recommended interventions
        interventions = self._generate_interventions(
            warning_signs, predicted_mood, horizon_minutes
        )
        
        # Calculate prediction confidence
        confidence = self._calculate_confidence(history, horizon_minutes)
        
        return MoodPrediction(
            predicted_mood=predicted_mood,
            probability=confidence,
            time_horizon_minutes=horizon_minutes,
            predicted_valence=predicted_valence,
            predicted_fatigue=predicted_fatigue,
            predicted_stress=predicted_stress,
            trend=trend,
            warning_signs=warning_signs,
            recommended_interventions=interventions
        )
    
    def _valence_to_mood(self, valence: float, fatigue: float, 
                         stress: float) -> MoodState:
        """Convert predicted metrics to mood state."""
        # High fatigue cases
        if fatigue > 0.7:
            return MoodState.EXHAUSTED
        if fatigue > 0.5 and stress > 0.5:
            return MoodState.OVERWHELMED
        
        # High stress cases
        if stress > 0.7:
            return MoodState.STRESSED
        if stress > 0.5 and valence < -0.3:
            return MoodState.ANXIOUS
        
        # Valence-based states
        if valence > 0.6:
            return MoodState.EXCELLENT
        if valence > 0.3:
            return MoodState.HAPPY
        if valence > 0.0:
            return MoodState.CONTENT
        if valence > -0.3:
            return MoodState.SLIGHTLY_DOWN
        if valence > -0.6:
            return MoodState.STRESSED
        return MoodState.FRUSTRATED
    
    def _calculate_trend(self, velocities: Dict) -> MoodTrend:
        """Determine overall emotional trend."""
        valence_v = velocities.get("valence", 0)
        fatigue_v = velocities.get("fatigue", 0)
        stress_v = velocities.get("stress", 0)
        
        # Check for volatility (rapid changes)
        if abs(valence_v) > 0.01:  # High rate of change
            return MoodTrend.VOLATILE
        
        # Net positive vs negative
        net = valence_v - fatigue_v - stress_v
        
        if net > 0.002:
            return MoodTrend.IMPROVING
        elif net < -0.002:
            return MoodTrend.DECLINING
        return MoodTrend.STABLE
    
    def _identify_warnings(self, snapshot: MoodSnapshot, 
                          velocities: Dict,
                          pred_fatigue: float, 
                          pred_stress: float) -> List[str]:
        """Identify early warning signs."""
        warnings = []
        
        # Rising fatigue
        if velocities.get("fatigue", 0) > 0.001:
            warnings.append("Fatigue gradually increasing")
        
        # Rising stress
        if velocities.get("stress", 0) > 0.001:
            warnings.append("Stress levels climbing")
        
        # Declining attention
        if snapshot.attention < 0.4:
            warnings.append("Attention waning")
        
        # High blink rate (stress indicator)
        if snapshot.blink_rate > 25:
            warnings.append("Elevated blink rate (possible stress)")
        
        # Late night work
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            warnings.append("Working very late")
        
        # Deviation from baseline
        deviation = self.patterns.get_deviation(snapshot)
        if deviation > 0.3:
            warnings.append("Significant deviation from your baseline")
        
        # Micro-expression warnings
        stress_exprs = ["tense", "furrowed", "tight", "clenched"]
        for expr in snapshot.micro_expressions:
            if any(s in expr.lower() for s in stress_exprs):
                warnings.append(f"Detected micro-expression: {expr}")
        
        return warnings
    
    def _generate_interventions(self, warnings: List[str], 
                                predicted_mood: MoodState,
                                horizon: int) -> List[str]:
        """Generate recommended anticipatory interventions."""
        interventions = []
        
        if predicted_mood in [MoodState.EXHAUSTED, MoodState.STRESSED, 
                              MoodState.OVERWHELMED]:
            if horizon <= 15:
                interventions.append("Consider taking a 5-minute break now")
            else:
                interventions.append(f"Schedule a break in the next {horizon} minutes")
        
        if "Fatigue gradually increasing" in warnings:
            interventions.append("Suggest stretching or standing up soon")
        
        if "Stress levels climbing" in warnings:
            interventions.append("Prepare calming music or breathing exercise")
        
        if "Working very late" in warnings:
            interventions.append("Gently remind about sleep importance")
        
        if "Attention waning" in warnings:
            interventions.append("Offer to help prioritize remaining tasks")
        
        if predicted_mood == MoodState.SLIGHTLY_DOWN:
            interventions.append("Share something encouraging or funny")
        
        return interventions
    
    def _calculate_confidence(self, history: deque, horizon: int) -> float:
        """Calculate prediction confidence based on data quality."""
        base_confidence = 0.5
        
        # More history = higher confidence
        if len(history) > 100:
            base_confidence += 0.2
        elif len(history) > 50:
            base_confidence += 0.1
        
        # Shorter horizon = higher confidence
        if horizon <= 15:
            base_confidence += 0.15
        elif horizon <= 30:
            base_confidence += 0.1
        
        # Recent readings confidence
        if history and history[-1].confidence > 0.7:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)


# ═══════════════════════════════════════════════════════════════════════════
# EMPATHY ENGINE - Main System
# ═══════════════════════════════════════════════════════════════════════════

class AnticipatoryEmpathyEngine:
    """
    Main orchestrator for anticipatory empathy.
    Combines sensing, learning, and prediction into proactive support.
    """
    
    def __init__(self):
        # Core components
        self.sensor = MoodSensor()
        self.pattern_learner = PatternLearner()
        self.predictor = MoodPredictor(self.pattern_learner)
        
        # State
        self.is_running = False
        self.update_thread = None
        self.update_interval = 30  # seconds
        
        # Current state
        self.current_snapshot: Optional[MoodSnapshot] = None
        self.current_forecast: Optional[EmotionalForecast] = None
        
        # Callbacks
        self.on_warning: List[Callable] = []
        self.on_intervention: List[Callable] = []
        
        # Intervention tracking
        self.last_intervention_time: Dict[str, float] = {}
        self.intervention_cooldown = 300  # 5 minutes
        
        logger.info("💜 Anticipatory Empathy Engine initialized")
    
    def start(self):
        """Start continuous mood monitoring and prediction."""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("💜 Empathy Engine started - watching over you")
    
    def stop(self):
        """Stop the empathy engine."""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=2)
        
        # Save patterns
        self.pattern_learner._save_patterns()
        logger.info("💜 Empathy Engine stopped")
    
    def _update_loop(self):
        """Continuous update loop."""
        while self.is_running:
            try:
                self._update()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Empathy update error: {e}")
    
    def _update(self):
        """Perform one update cycle."""
        # Take reading
        snapshot = self.sensor.read()
        if snapshot is None:
            return
        
        self.current_snapshot = snapshot
        
        # Record for learning
        self.pattern_learner.record(snapshot)
        
        # Generate forecast
        forecast = self._generate_forecast(snapshot)
        self.current_forecast = forecast
        
        # Check for interventions
        self._check_interventions(forecast)
    
    def _generate_forecast(self, snapshot: MoodSnapshot) -> EmotionalForecast:
        """Generate complete emotional forecast."""
        history = self.pattern_learner.mood_history
        
        # Get predictions at different horizons
        pred_15 = self.predictor.predict(snapshot, history, 15)
        pred_30 = self.predictor.predict(snapshot, history, 30)
        pred_60 = self.predictor.predict(snapshot, history, 60)
        
        # Determine overall trend
        velocities = self.pattern_learner.get_velocities()
        trend = self.predictor._calculate_trend(velocities)
        
        # Calculate deviation
        deviation = self.pattern_learner.get_deviation(snapshot)
        
        # Determine alert level
        alert = self._determine_alert_level(snapshot, pred_15, trend)
        
        # Primary concern
        concern = self._identify_primary_concern(snapshot, pred_15)
        
        # Anticipatory actions
        actions = self._compile_anticipatory_actions(pred_15, pred_30)
        
        # Pattern match
        pattern = self.pattern_learner.find_similar_pattern(snapshot)
        
        return EmotionalForecast(
            timestamp=time.time(),
            current_mood=snapshot.mood,
            current_valence=snapshot.valence,
            current_trend=trend,
            prediction_15min=pred_15,
            prediction_30min=pred_30,
            prediction_1hour=pred_60,
            alert_level=alert,
            primary_concern=concern,
            anticipatory_actions=actions,
            deviation_from_baseline=deviation,
            pattern_match=pattern
        )
    
    def _determine_alert_level(self, snapshot: MoodSnapshot,
                               prediction: MoodPrediction,
                               trend: MoodTrend) -> AlertLevel:
        """Determine intervention urgency."""
        # Urgent: Already in bad state
        if snapshot.mood in [MoodState.OVERWHELMED, MoodState.EXHAUSTED]:
            if snapshot.fatigue > 0.8 or snapshot.stress > 0.8:
                return AlertLevel.URGENT
        
        # Active: Predicted to decline soon
        if prediction.predicted_mood in [MoodState.STRESSED, MoodState.EXHAUSTED]:
            if trend == MoodTrend.DECLINING:
                return AlertLevel.ACTIVE
        
        # Proactive: Warning signs present
        if len(prediction.warning_signs) >= 2:
            return AlertLevel.PROACTIVE
        
        # Subtle: Minor deviations
        if len(prediction.warning_signs) >= 1:
            return AlertLevel.SUBTLE
        
        return AlertLevel.NONE
    
    def _identify_primary_concern(self, snapshot: MoodSnapshot,
                                  prediction: MoodPrediction) -> str:
        """Identify the main concern to address."""
        if prediction.predicted_fatigue > 0.7:
            return "Building fatigue - rest needed soon"
        if prediction.predicted_stress > 0.7:
            return "Rising stress levels"
        if prediction.trend == MoodTrend.DECLINING:
            return "Mood trending downward"
        if snapshot.attention < 0.4:
            return "Focus is drifting"
        
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            return "It's very late"
        
        return "Monitoring - all looks okay"
    
    def _compile_anticipatory_actions(self, pred_15: MoodPrediction,
                                      pred_30: MoodPrediction) -> List[str]:
        """Compile list of recommended anticipatory actions."""
        actions = []
        
        # Combine interventions from both predictions
        seen = set()
        for intervention in pred_15.recommended_interventions + pred_30.recommended_interventions:
            if intervention not in seen:
                actions.append(intervention)
                seen.add(intervention)
        
        return actions[:5]  # Limit to top 5
    
    def _check_interventions(self, forecast: EmotionalForecast):
        """Check if we should trigger any interventions."""
        now = time.time()
        
        if forecast.alert_level.value >= AlertLevel.PROACTIVE.value:
            for action in forecast.anticipatory_actions:
                action_key = action[:20]  # Truncate for key
                last_time = self.last_intervention_time.get(action_key, 0)
                
                if now - last_time > self.intervention_cooldown:
                    # Trigger intervention
                    self.last_intervention_time[action_key] = now
                    
                    for callback in self.on_intervention:
                        try:
                            callback(forecast, action)
                        except Exception as e:
                            logger.error(f"Intervention callback error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def get_forecast(self) -> Optional[EmotionalForecast]:
        """Get current emotional forecast."""
        return self.current_forecast
    
    def get_mood(self) -> Optional[MoodState]:
        """Get current mood state."""
        return self.current_snapshot.mood if self.current_snapshot else None
    
    def get_predictions(self) -> Dict[str, MoodPrediction]:
        """Get all current predictions."""
        if self.current_forecast is None:
            return {}
        
        return {
            "15min": self.current_forecast.prediction_15min,
            "30min": self.current_forecast.prediction_30min,
            "1hour": self.current_forecast.prediction_1hour
        }
    
    def add_warning_callback(self, callback: Callable):
        """Add callback for warning triggers."""
        self.on_warning.append(callback)
    
    def add_intervention_callback(self, callback: Callable):
        """Add callback for intervention triggers."""
        self.on_intervention.append(callback)
    
    def get_summary(self) -> str:
        """Get human-readable empathy summary."""
        if self.current_forecast is None:
            return "Empathy Engine warming up..."
        
        f = self.current_forecast
        lines = []
        
        lines.append(f"Current: {f.current_mood.value} (trend: {f.current_trend.value})")
        lines.append(f"Alert Level: {f.alert_level.name}")
        lines.append(f"Primary Concern: {f.primary_concern}")
        lines.append(f"")
        lines.append("Predictions:")
        lines.append(f"  15min: {f.prediction_15min.predicted_mood.value} ({f.prediction_15min.probability:.0%} confidence)")
        lines.append(f"  30min: {f.prediction_30min.predicted_mood.value}")
        lines.append(f"  1hour: {f.prediction_1hour.predicted_mood.value}")
        
        if f.anticipatory_actions:
            lines.append("")
            lines.append("💜 Suggested Actions:")
            for action in f.anticipatory_actions[:3]:
                lines.append(f"  • {action}")
        
        return "\n".join(lines)
    
    def instant_forecast(self) -> Optional[EmotionalForecast]:
        """Take instant reading and generate forecast (one-shot)."""
        snapshot = self.sensor.read()
        if snapshot:
            self.current_snapshot = snapshot
            self.pattern_learner.record(snapshot)
            forecast = self._generate_forecast(snapshot)
            self.current_forecast = forecast
            return forecast
        return None


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_empathy_engine = None

def get_empathy_engine() -> AnticipatoryEmpathyEngine:
    """Get the global empathy engine instance."""
    global _empathy_engine
    if _empathy_engine is None:
        _empathy_engine = AnticipatoryEmpathyEngine()
    return _empathy_engine


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n💜 ZARA Anticipatory Empathy Engine v1.0\n")
    print("=" * 60)
    
    engine = AnticipatoryEmpathyEngine()
    
    # Add intervention callback
    def on_intervention(forecast, action):
        print(f"\n💜 ANTICIPATORY INTERVENTION: {action}")
    
    engine.add_intervention_callback(on_intervention)
    
    # Take instant reading
    print("\n📊 Taking instant emotional reading...")
    forecast = engine.instant_forecast()
    
    if forecast:
        print(f"\n{engine.get_summary()}")
        
        print(f"\n🔮 Prediction Details (15 min):")
        p = forecast.prediction_15min
        print(f"  Predicted Mood: {p.predicted_mood.value}")
        print(f"  Predicted Fatigue: {p.predicted_fatigue:.1%}")
        print(f"  Predicted Stress: {p.predicted_stress:.1%}")
        print(f"  Trend: {p.trend.value}")
        
        if p.warning_signs:
            print(f"\n⚠️ Warning Signs:")
            for w in p.warning_signs:
                print(f"  • {w}")
    
    # Simulate continuous monitoring
    print(f"\n🔄 Starting continuous monitoring (10 seconds)...")
    engine.start()
    
    time.sleep(10)
    
    print(f"\n📊 After 10 seconds:")
    print(engine.get_summary())
    
    engine.stop()
    
    print("\n" + "=" * 60)
    print("✅ Empathy Engine ready to watch over you!\n")
