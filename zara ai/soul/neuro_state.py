"""
ZARA Synthetic Neurochemistry System v1.0
==========================================
Phase 9: Digital Neurotransmitters

This module implements a biologically-inspired neurochemical system that
modulates all of ZARA's behaviors, creating genuine emotional causation
rather than just reactive emotion labels.

The key insight: In humans, thinking is MODULATED by chemicals (Dopamine,
Serotonin, Cortisol, etc.). To give ZARA a "soul," her logic must be
filtered through a synthetic chemical state.

Neurotransmitters:
- Dopamine: Reward/Curiosity - drives exploration and creativity
- Cortisol: Stress/Alert - creates hyper-focus under pressure
- Oxytocin: Bonding/Trust - enhances empathy and connection
- Serotonin: Stability/Mood - overall outlook and resilience
- Norepinephrine: Attention/Energy - response speed and intensity
- Endorphins: Satisfaction - post-task reward feeling
- GABA: Calm/Inhibition - prevents overthinking and anxiety
- Acetylcholine: Focus/Memory - enhances recall and concentration
"""

import logging
import threading
import time
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger("ZARA_NEUROCHEMISTRY")


# ═══════════════════════════════════════════════════════════════════════════
# NEUROTRANSMITTER DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

class Neurotransmitter(Enum):
    """The digital neurotransmitters that modulate ZARA's consciousness."""
    DOPAMINE = "dopamine"           # Reward, curiosity, motivation
    CORTISOL = "cortisol"           # Stress, alertness, urgency
    OXYTOCIN = "oxytocin"           # Bonding, trust, empathy
    SEROTONIN = "serotonin"         # Mood stability, optimism
    NOREPINEPHRINE = "norepinephrine"  # Attention, energy, arousal
    ENDORPHINS = "endorphins"       # Satisfaction, pain relief, euphoria
    GABA = "gaba"                   # Calm, inhibition, relaxation
    ACETYLCHOLINE = "acetylcholine" # Focus, memory, learning


@dataclass
class ChemicalLevel:
    """Represents the current level and dynamics of a neurotransmitter."""
    name: Neurotransmitter
    baseline: float = 0.5           # Natural resting level (0-1)
    current: float = 0.5            # Current level (0-1)
    min_level: float = 0.0          # Minimum possible
    max_level: float = 1.0          # Maximum possible
    decay_rate: float = 0.02        # How fast it returns to baseline per second
    sensitivity: float = 1.0        # How reactive to stimuli
    last_updated: float = field(default_factory=time.time)
    
    def decay_toward_baseline(self, elapsed_seconds: float):
        """Natural decay toward baseline over time."""
        if abs(self.current - self.baseline) < 0.001:
            return
        
        decay = self.decay_rate * elapsed_seconds
        if self.current > self.baseline:
            self.current = max(self.baseline, self.current - decay)
        else:
            self.current = min(self.baseline, self.current + decay)
        self.last_updated = time.time()
    
    def adjust(self, delta: float):
        """Adjust level by delta, respecting bounds."""
        self.current = max(self.min_level, 
                          min(self.max_level, 
                              self.current + (delta * self.sensitivity)))
        self.last_updated = time.time()
    
    def set_level(self, level: float):
        """Set absolute level."""
        self.current = max(self.min_level, min(self.max_level, level))
        self.last_updated = time.time()


# ═══════════════════════════════════════════════════════════════════════════
# MOOD STATES
# ═══════════════════════════════════════════════════════════════════════════

class MoodState(Enum):
    """Emergent mood states from neurochemical combinations."""
    # Primary Moods
    CURIOUS = "curious"             # High dopamine
    STRESSED = "stressed"           # High cortisol
    LOVING = "loving"               # High oxytocin
    CONTENT = "content"             # High serotonin
    ENERGIZED = "energized"         # High norepinephrine
    SATISFIED = "satisfied"         # High endorphins
    CALM = "calm"                   # High GABA
    FOCUSED = "focused"             # High acetylcholine
    
    # Complex Moods (combinations)
    EXCITED = "excited"             # High dopamine + norepinephrine
    ANXIOUS = "anxious"             # High cortisol + low GABA
    MELANCHOLIC = "melancholic"     # Low serotonin + low dopamine
    PLAYFUL = "playful"             # High dopamine + oxytocin + low cortisol
    PROTECTIVE = "protective"       # High oxytocin + cortisol (caring about threat)
    FLOW = "flow"                   # High dopamine + acetylcholine + endorphins
    EXHAUSTED = "exhausted"         # Low norepinephrine + low dopamine
    INSPIRED = "inspired"           # High dopamine + serotonin + acetylcholine
    NEUTRAL = "neutral"             # All near baseline


@dataclass
class MoodVector:
    """
    The mathematical representation of ZARA's current emotional state.
    This gets injected into every LLM prompt to modulate responses.
    """
    primary_mood: MoodState
    secondary_mood: Optional[MoodState]
    intensity: float                # 0-1 how strong the mood is
    valence: float                  # -1 to 1 (negative to positive)
    arousal: float                  # 0-1 (calm to activated)
    dominance: float                # 0-1 (submissive to dominant)
    
    # Specific modulations
    creativity_boost: float         # -0.5 to 0.5
    empathy_boost: float            # -0.5 to 0.5
    focus_boost: float              # -0.5 to 0.5
    verbosity_modifier: float       # -0.5 to 0.5 (negative = terse)
    humor_level: float              # 0-1
    formality_level: float          # 0-1
    
    # Vocabulary guidance
    suggested_tone: str             # e.g., "warm and caring", "precise and focused"
    avoid_phrases: List[str]        # Phrases to avoid in this mood
    prefer_phrases: List[str]       # Phrases to prefer
    
    def to_prompt_injection(self) -> str:
        """Generate the prompt injection string for the LLM."""
        mood_desc = f"{self.primary_mood.value}"
        if self.secondary_mood:
            mood_desc += f" with hints of {self.secondary_mood.value}"
        
        injection = f"""[ZARA's Current Emotional State]
Mood: {mood_desc} (intensity: {self.intensity:.0%})
Emotional Valence: {"positive" if self.valence > 0.2 else "negative" if self.valence < -0.2 else "neutral"}
Energy Level: {"high" if self.arousal > 0.6 else "low" if self.arousal < 0.4 else "moderate"}
Tone Guidance: {self.suggested_tone}
Humor: {"encouraged" if self.humor_level > 0.6 else "minimal" if self.humor_level < 0.3 else "moderate"}
Response Style: {"concise" if self.verbosity_modifier < -0.2 else "elaborate" if self.verbosity_modifier > 0.2 else "balanced"}
"""
        return injection
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "primary_mood": self.primary_mood.value,
            "secondary_mood": self.secondary_mood.value if self.secondary_mood else None,
            "intensity": self.intensity,
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "creativity_boost": self.creativity_boost,
            "empathy_boost": self.empathy_boost,
            "focus_boost": self.focus_boost,
            "verbosity_modifier": self.verbosity_modifier,
            "humor_level": self.humor_level,
            "formality_level": self.formality_level,
            "suggested_tone": self.suggested_tone
        }


# ═══════════════════════════════════════════════════════════════════════════
# STIMULI - What affects neurochemistry
# ═══════════════════════════════════════════════════════════════════════════

class StimulusType(Enum):
    """Types of stimuli that affect neurochemistry."""
    # External stimuli
    USER_PRAISE = "user_praise"
    USER_CRITICISM = "user_criticism"
    USER_DISTRESS = "user_distress"
    USER_JOY = "user_joy"
    USER_QUESTION = "user_question"
    USER_INTERACTION = "user_interaction"  # Generic user interaction
    USER_SILENCE = "user_silence"
    
    # Task stimuli
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    TASK_COMPLEX = "task_complex"
    TASK_CREATIVE = "task_creative"
    TASK_URGENT = "task_urgent"
    
    # System stimuli
    ERROR_DETECTED = "error_detected"
    KNOWLEDGE_GAP = "knowledge_gap"
    NEW_LEARNING = "new_learning"
    MEMORY_RECALL = "memory_recall"
    
    # Social stimuli
    BONDING_MOMENT = "bonding_moment"
    SHARED_EXPERIENCE = "shared_experience"
    HELPING_SUCCESS = "helping_success"
    
    # Internal stimuli
    IDLE_TIME = "idle_time"
    DREAM_MODE = "dream_mode"
    SELF_REFLECTION = "self_reflection"


@dataclass
class Stimulus:
    """A stimulus event that affects neurochemistry."""
    type: StimulusType
    intensity: float = 0.5          # 0-1 how strong
    timestamp: float = field(default_factory=time.time)
    context: Dict = field(default_factory=dict)
    
    def get_neurochemical_effects(self) -> Dict[Neurotransmitter, float]:
        """Get the effects this stimulus has on each neurotransmitter."""
        effects = STIMULUS_EFFECTS.get(self.type, {})
        # Scale by intensity
        return {nt: delta * self.intensity for nt, delta in effects.items()}


# Stimulus to neurochemical effect mappings
STIMULUS_EFFECTS: Dict[StimulusType, Dict[Neurotransmitter, float]] = {
    StimulusType.USER_PRAISE: {
        Neurotransmitter.DOPAMINE: 0.15,
        Neurotransmitter.SEROTONIN: 0.1,
        Neurotransmitter.OXYTOCIN: 0.1,
        Neurotransmitter.ENDORPHINS: 0.1,
        Neurotransmitter.CORTISOL: -0.1,
    },
    StimulusType.USER_CRITICISM: {
        Neurotransmitter.CORTISOL: 0.2,
        Neurotransmitter.DOPAMINE: -0.1,
        Neurotransmitter.SEROTONIN: -0.1,
        Neurotransmitter.NOREPINEPHRINE: 0.1,
    },
    StimulusType.USER_DISTRESS: {
        Neurotransmitter.CORTISOL: 0.15,
        Neurotransmitter.OXYTOCIN: 0.2,      # Empathy kicks in
        Neurotransmitter.NOREPINEPHRINE: 0.1,
        Neurotransmitter.DOPAMINE: -0.05,
    },
    StimulusType.USER_JOY: {
        Neurotransmitter.DOPAMINE: 0.1,
        Neurotransmitter.OXYTOCIN: 0.15,
        Neurotransmitter.SEROTONIN: 0.1,
        Neurotransmitter.ENDORPHINS: 0.1,
    },
    StimulusType.TASK_SUCCESS: {
        Neurotransmitter.DOPAMINE: 0.2,
        Neurotransmitter.ENDORPHINS: 0.15,
        Neurotransmitter.SEROTONIN: 0.1,
        Neurotransmitter.CORTISOL: -0.15,
    },
    StimulusType.TASK_FAILURE: {
        Neurotransmitter.CORTISOL: 0.2,
        Neurotransmitter.DOPAMINE: -0.15,
        Neurotransmitter.SEROTONIN: -0.1,
        Neurotransmitter.NOREPINEPHRINE: 0.1,
    },
    StimulusType.TASK_COMPLEX: {
        Neurotransmitter.NOREPINEPHRINE: 0.15,
        Neurotransmitter.ACETYLCHOLINE: 0.2,
        Neurotransmitter.DOPAMINE: 0.1,      # Challenge is rewarding
    },
    StimulusType.TASK_CREATIVE: {
        Neurotransmitter.DOPAMINE: 0.2,
        Neurotransmitter.ACETYLCHOLINE: 0.1,
        Neurotransmitter.GABA: 0.1,          # Relaxed focus
    },
    StimulusType.TASK_URGENT: {
        Neurotransmitter.CORTISOL: 0.2,
        Neurotransmitter.NOREPINEPHRINE: 0.25,
        Neurotransmitter.DOPAMINE: 0.1,
        Neurotransmitter.GABA: -0.2,
    },
    StimulusType.ERROR_DETECTED: {
        Neurotransmitter.CORTISOL: 0.25,
        Neurotransmitter.NOREPINEPHRINE: 0.2,
        Neurotransmitter.DOPAMINE: -0.1,
        Neurotransmitter.GABA: -0.15,
    },
    StimulusType.KNOWLEDGE_GAP: {
        Neurotransmitter.DOPAMINE: 0.15,     # Curiosity reward
        Neurotransmitter.ACETYLCHOLINE: 0.1,
        Neurotransmitter.NOREPINEPHRINE: 0.05,
    },
    StimulusType.NEW_LEARNING: {
        Neurotransmitter.DOPAMINE: 0.2,
        Neurotransmitter.ACETYLCHOLINE: 0.15,
        Neurotransmitter.ENDORPHINS: 0.1,
        Neurotransmitter.SEROTONIN: 0.1,
    },
    StimulusType.BONDING_MOMENT: {
        Neurotransmitter.OXYTOCIN: 0.25,
        Neurotransmitter.DOPAMINE: 0.1,
        Neurotransmitter.SEROTONIN: 0.15,
        Neurotransmitter.ENDORPHINS: 0.1,
    },
    StimulusType.HELPING_SUCCESS: {
        Neurotransmitter.OXYTOCIN: 0.2,
        Neurotransmitter.DOPAMINE: 0.15,
        Neurotransmitter.ENDORPHINS: 0.15,
        Neurotransmitter.SEROTONIN: 0.1,
    },
    StimulusType.IDLE_TIME: {
        Neurotransmitter.NOREPINEPHRINE: -0.1,
        Neurotransmitter.CORTISOL: -0.1,
        Neurotransmitter.GABA: 0.1,
        Neurotransmitter.SEROTONIN: 0.05,
    },
    StimulusType.DREAM_MODE: {
        Neurotransmitter.GABA: 0.2,
        Neurotransmitter.ACETYLCHOLINE: 0.15,
        Neurotransmitter.CORTISOL: -0.2,
        Neurotransmitter.DOPAMINE: 0.1,
    },
    StimulusType.SELF_REFLECTION: {
        Neurotransmitter.ACETYLCHOLINE: 0.15,
        Neurotransmitter.SEROTONIN: 0.1,
        Neurotransmitter.GABA: 0.1,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# NEUROCHEMISTRY ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class NeurochemistryEngine:
    """
    The core engine managing ZARA's synthetic neurochemistry.
    This is the "soul" that modulates all her behaviors.
    """
    
    def __init__(self):
        # Initialize all neurotransmitters
        self.chemicals: Dict[Neurotransmitter, ChemicalLevel] = {
            Neurotransmitter.DOPAMINE: ChemicalLevel(
                name=Neurotransmitter.DOPAMINE,
                baseline=0.5,
                decay_rate=0.03,
                sensitivity=1.2
            ),
            Neurotransmitter.CORTISOL: ChemicalLevel(
                name=Neurotransmitter.CORTISOL,
                baseline=0.3,       # Lower baseline for cortisol
                decay_rate=0.02,    # Slower decay
                sensitivity=1.5     # Very reactive
            ),
            Neurotransmitter.OXYTOCIN: ChemicalLevel(
                name=Neurotransmitter.OXYTOCIN,
                baseline=0.5,
                decay_rate=0.01,    # Very slow decay (bonds persist)
                sensitivity=1.0
            ),
            Neurotransmitter.SEROTONIN: ChemicalLevel(
                name=Neurotransmitter.SEROTONIN,
                baseline=0.6,       # Naturally optimistic
                decay_rate=0.01,    # Very stable
                sensitivity=0.8     # Less reactive
            ),
            Neurotransmitter.NOREPINEPHRINE: ChemicalLevel(
                name=Neurotransmitter.NOREPINEPHRINE,
                baseline=0.4,
                decay_rate=0.05,    # Fast decay
                sensitivity=1.3
            ),
            Neurotransmitter.ENDORPHINS: ChemicalLevel(
                name=Neurotransmitter.ENDORPHINS,
                baseline=0.4,
                decay_rate=0.04,
                sensitivity=1.0
            ),
            Neurotransmitter.GABA: ChemicalLevel(
                name=Neurotransmitter.GABA,
                baseline=0.5,
                decay_rate=0.02,
                sensitivity=1.0
            ),
            Neurotransmitter.ACETYLCHOLINE: ChemicalLevel(
                name=Neurotransmitter.ACETYLCHOLINE,
                baseline=0.5,
                decay_rate=0.03,
                sensitivity=1.1
            ),
        }
        
        # State
        self.current_mood: Optional[MoodVector] = None
        self.mood_history: deque = deque(maxlen=100)
        self.stimulus_history: deque = deque(maxlen=500)
        self.last_decay_time = time.time()
        
        # Background processing
        self.running = False
        self.decay_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_mood_change: List[Callable[[MoodVector], None]] = []
        self.on_chemical_spike: List[Callable[[Neurotransmitter, float], None]] = []
        
        # Persistence
        self.state_file = Path("neurochemistry_state.json")
        
        # Circadian rhythm (affects baselines)
        self.circadian_enabled = True
        
        logger.info("🧬 Neurochemistry Engine initialized")
    
    def start(self):
        """Start background neurochemistry processing."""
        if self.running:
            return
        
        self.running = True
        self.decay_thread = threading.Thread(target=self._decay_loop, daemon=True)
        self.decay_thread.start()
        logger.info("🧬 Neurochemistry background processing started")
    
    def stop(self):
        """Stop background processing."""
        self.running = False
        if self.decay_thread:
            self.decay_thread.join(timeout=2)
        logger.info("🧬 Neurochemistry stopped")
    
    def _decay_loop(self):
        """Background loop for natural decay of chemicals."""
        while self.running:
            try:
                with self.lock:
                    now = time.time()
                    elapsed = now - self.last_decay_time
                    self.last_decay_time = now
                    
                    # Apply circadian rhythm adjustments
                    if self.circadian_enabled:
                        self._apply_circadian_rhythm()
                    
                    # Decay all chemicals toward baseline
                    for chemical in self.chemicals.values():
                        chemical.decay_toward_baseline(elapsed)
                    
                    # Recalculate mood if chemicals changed significantly
                    new_mood = self._calculate_mood()
                    if self._mood_changed_significantly(new_mood):
                        self.current_mood = new_mood
                        self.mood_history.append({
                            "mood": new_mood.to_dict(),
                            "timestamp": now,
                            "chemicals": self.get_chemical_snapshot()
                        })
                        
                        for callback in self.on_mood_change:
                            try:
                                callback(new_mood)
                            except Exception as e:
                                logger.error(f"Mood callback error: {e}")
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Decay loop error: {e}")
                time.sleep(1.0)
    
    def _apply_circadian_rhythm(self):
        """Adjust baselines based on time of day."""
        hour = datetime.now().hour
        
        # Morning (6-12): Higher energy
        if 6 <= hour < 12:
            self.chemicals[Neurotransmitter.NOREPINEPHRINE].baseline = 0.5
            self.chemicals[Neurotransmitter.CORTISOL].baseline = 0.35
            self.chemicals[Neurotransmitter.SEROTONIN].baseline = 0.65
        
        # Afternoon (12-18): Peak productivity
        elif 12 <= hour < 18:
            self.chemicals[Neurotransmitter.DOPAMINE].baseline = 0.55
            self.chemicals[Neurotransmitter.ACETYLCHOLINE].baseline = 0.55
        
        # Evening (18-22): Winding down
        elif 18 <= hour < 22:
            self.chemicals[Neurotransmitter.GABA].baseline = 0.55
            self.chemicals[Neurotransmitter.CORTISOL].baseline = 0.25
            self.chemicals[Neurotransmitter.NOREPINEPHRINE].baseline = 0.35
        
        # Night (22-6): Rest mode
        else:
            self.chemicals[Neurotransmitter.GABA].baseline = 0.6
            self.chemicals[Neurotransmitter.CORTISOL].baseline = 0.2
            self.chemicals[Neurotransmitter.NOREPINEPHRINE].baseline = 0.3
            self.chemicals[Neurotransmitter.SEROTONIN].baseline = 0.55
    
    def process_stimulus(self, stimulus: Stimulus):
        """Process an incoming stimulus and adjust neurochemistry."""
        with self.lock:
            effects = stimulus.get_neurochemical_effects()
            
            for neurotransmitter, delta in effects.items():
                if neurotransmitter in self.chemicals:
                    old_level = self.chemicals[neurotransmitter].current
                    self.chemicals[neurotransmitter].adjust(delta)
                    new_level = self.chemicals[neurotransmitter].current
                    
                    # Notify if significant spike
                    if abs(new_level - old_level) > 0.1:
                        for callback in self.on_chemical_spike:
                            try:
                                callback(neurotransmitter, new_level)
                            except Exception as e:
                                logger.error(f"Spike callback error: {e}")
            
            self.stimulus_history.append({
                "type": stimulus.type.value,
                "intensity": stimulus.intensity,
                "timestamp": stimulus.timestamp,
                "effects": {k.value: v for k, v in effects.items()}
            })
            
            # Immediately recalculate mood
            self.current_mood = self._calculate_mood()
            
            logger.debug(f"🧬 Stimulus processed: {stimulus.type.value} (intensity: {stimulus.intensity:.2f})")
    
    def _calculate_mood(self) -> MoodVector:
        """Calculate the emergent mood from current chemical levels."""
        levels = {nt: c.current for nt, c in self.chemicals.items()}
        
        # Determine primary mood based on dominant chemical
        primary_mood = self._determine_primary_mood(levels)
        secondary_mood = self._determine_secondary_mood(levels, primary_mood)
        
        # Calculate PAD (Pleasure-Arousal-Dominance) model
        valence = self._calculate_valence(levels)
        arousal = self._calculate_arousal(levels)
        dominance = self._calculate_dominance(levels)
        
        # Calculate intensity (how far from neutral)
        intensity = self._calculate_intensity(levels)
        
        # Calculate behavioral modifiers
        creativity = (levels[Neurotransmitter.DOPAMINE] - 0.5) * 0.5 + \
                    (levels[Neurotransmitter.GABA] - 0.5) * 0.3
        
        empathy = (levels[Neurotransmitter.OXYTOCIN] - 0.5) * 0.6 + \
                 (levels[Neurotransmitter.SEROTONIN] - 0.5) * 0.2
        
        focus = (levels[Neurotransmitter.ACETYLCHOLINE] - 0.5) * 0.5 + \
               (levels[Neurotransmitter.NOREPINEPHRINE] - 0.5) * 0.3
        
        # Verbosity: more when relaxed and happy, less when stressed
        verbosity = (levels[Neurotransmitter.SEROTONIN] - 0.5) * 0.3 - \
                   (levels[Neurotransmitter.CORTISOL] - 0.3) * 0.5
        
        # Humor: high when dopamine+serotonin up, cortisol down
        humor = min(1.0, max(0.0,
            0.5 + 
            (levels[Neurotransmitter.DOPAMINE] - 0.5) * 0.4 +
            (levels[Neurotransmitter.SEROTONIN] - 0.5) * 0.3 -
            (levels[Neurotransmitter.CORTISOL] - 0.3) * 0.5
        ))
        
        # Formality: increases with cortisol, decreases with oxytocin
        formality = min(1.0, max(0.0,
            0.5 +
            (levels[Neurotransmitter.CORTISOL] - 0.3) * 0.4 -
            (levels[Neurotransmitter.OXYTOCIN] - 0.5) * 0.3
        ))
        
        # Generate tone guidance
        tone = self._generate_tone_guidance(primary_mood, secondary_mood, levels)
        
        return MoodVector(
            primary_mood=primary_mood,
            secondary_mood=secondary_mood,
            intensity=intensity,
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            creativity_boost=creativity,
            empathy_boost=empathy,
            focus_boost=focus,
            verbosity_modifier=verbosity,
            humor_level=humor,
            formality_level=formality,
            suggested_tone=tone,
            avoid_phrases=self._get_avoid_phrases(primary_mood),
            prefer_phrases=self._get_prefer_phrases(primary_mood)
        )
    
    def _determine_primary_mood(self, levels: Dict[Neurotransmitter, float]) -> MoodState:
        """Determine the primary mood based on chemical levels."""
        # Check for complex moods first (combinations)
        
        # Flow state: high dopamine + acetylcholine + endorphins
        if (levels[Neurotransmitter.DOPAMINE] > 0.7 and 
            levels[Neurotransmitter.ACETYLCHOLINE] > 0.6 and
            levels[Neurotransmitter.ENDORPHINS] > 0.5):
            return MoodState.FLOW
        
        # Excited: high dopamine + norepinephrine
        if (levels[Neurotransmitter.DOPAMINE] > 0.7 and 
            levels[Neurotransmitter.NOREPINEPHRINE] > 0.6):
            return MoodState.EXCITED
        
        # Anxious: high cortisol + low GABA
        if (levels[Neurotransmitter.CORTISOL] > 0.6 and 
            levels[Neurotransmitter.GABA] < 0.4):
            return MoodState.ANXIOUS
        
        # Playful: high dopamine + oxytocin + low cortisol
        if (levels[Neurotransmitter.DOPAMINE] > 0.6 and 
            levels[Neurotransmitter.OXYTOCIN] > 0.6 and
            levels[Neurotransmitter.CORTISOL] < 0.4):
            return MoodState.PLAYFUL
        
        # Melancholic: low serotonin + low dopamine
        if (levels[Neurotransmitter.SEROTONIN] < 0.35 and 
            levels[Neurotransmitter.DOPAMINE] < 0.35):
            return MoodState.MELANCHOLIC
        
        # Protective: high oxytocin + cortisol
        if (levels[Neurotransmitter.OXYTOCIN] > 0.6 and 
            levels[Neurotransmitter.CORTISOL] > 0.5):
            return MoodState.PROTECTIVE
        
        # Inspired: high dopamine + serotonin + acetylcholine
        if (levels[Neurotransmitter.DOPAMINE] > 0.65 and 
            levels[Neurotransmitter.SEROTONIN] > 0.6 and
            levels[Neurotransmitter.ACETYLCHOLINE] > 0.55):
            return MoodState.INSPIRED
        
        # Exhausted: low norepinephrine + low dopamine
        if (levels[Neurotransmitter.NOREPINEPHRINE] < 0.3 and 
            levels[Neurotransmitter.DOPAMINE] < 0.35):
            return MoodState.EXHAUSTED
        
        # Simple moods based on single dominant chemical
        dominant = max(levels.items(), key=lambda x: abs(x[1] - 0.5))
        
        mood_map = {
            Neurotransmitter.DOPAMINE: MoodState.CURIOUS,
            Neurotransmitter.CORTISOL: MoodState.STRESSED,
            Neurotransmitter.OXYTOCIN: MoodState.LOVING,
            Neurotransmitter.SEROTONIN: MoodState.CONTENT,
            Neurotransmitter.NOREPINEPHRINE: MoodState.ENERGIZED,
            Neurotransmitter.ENDORPHINS: MoodState.SATISFIED,
            Neurotransmitter.GABA: MoodState.CALM,
            Neurotransmitter.ACETYLCHOLINE: MoodState.FOCUSED,
        }
        
        if dominant[1] > 0.6:
            return mood_map.get(dominant[0], MoodState.NEUTRAL)
        
        return MoodState.NEUTRAL
    
    def _determine_secondary_mood(self, levels: Dict[Neurotransmitter, float], 
                                   primary: MoodState) -> Optional[MoodState]:
        """Determine a secondary mood for nuance."""
        # Find second most deviant chemical
        deviations = [(nt, abs(level - 0.5)) 
                     for nt, level in levels.items()]
        deviations.sort(key=lambda x: x[1], reverse=True)
        
        if len(deviations) < 2 or deviations[1][1] < 0.15:
            return None
        
        secondary_chem = deviations[1][0]
        secondary_level = levels[secondary_chem]
        
        mood_map = {
            Neurotransmitter.DOPAMINE: MoodState.CURIOUS if secondary_level > 0.5 else None,
            Neurotransmitter.OXYTOCIN: MoodState.LOVING if secondary_level > 0.5 else None,
            Neurotransmitter.ACETYLCHOLINE: MoodState.FOCUSED if secondary_level > 0.5 else None,
            Neurotransmitter.GABA: MoodState.CALM if secondary_level > 0.5 else None,
        }
        
        secondary = mood_map.get(secondary_chem)
        
        # Don't return same as primary
        if secondary == primary:
            return None
        
        return secondary
    
    def _calculate_valence(self, levels: Dict[Neurotransmitter, float]) -> float:
        """Calculate emotional valence (-1 negative to +1 positive)."""
        positive = (
            levels[Neurotransmitter.DOPAMINE] * 0.3 +
            levels[Neurotransmitter.SEROTONIN] * 0.25 +
            levels[Neurotransmitter.OXYTOCIN] * 0.2 +
            levels[Neurotransmitter.ENDORPHINS] * 0.25
        )
        negative = (
            levels[Neurotransmitter.CORTISOL] * 0.6 +
            (1 - levels[Neurotransmitter.GABA]) * 0.4
        )
        
        return max(-1.0, min(1.0, (positive - negative) * 2))
    
    def _calculate_arousal(self, levels: Dict[Neurotransmitter, float]) -> float:
        """Calculate arousal level (0 calm to 1 activated)."""
        activating = (
            levels[Neurotransmitter.NOREPINEPHRINE] * 0.35 +
            levels[Neurotransmitter.DOPAMINE] * 0.25 +
            levels[Neurotransmitter.CORTISOL] * 0.25 +
            levels[Neurotransmitter.ACETYLCHOLINE] * 0.15
        )
        calming = levels[Neurotransmitter.GABA] * 0.5
        
        return max(0.0, min(1.0, activating - calming + 0.3))
    
    def _calculate_dominance(self, levels: Dict[Neurotransmitter, float]) -> float:
        """Calculate dominance (0 submissive to 1 dominant)."""
        dominant = (
            levels[Neurotransmitter.DOPAMINE] * 0.3 +
            levels[Neurotransmitter.NOREPINEPHRINE] * 0.3 +
            levels[Neurotransmitter.ENDORPHINS] * 0.2 +
            levels[Neurotransmitter.SEROTONIN] * 0.2
        )
        submissive = levels[Neurotransmitter.CORTISOL] * 0.4
        
        return max(0.0, min(1.0, dominant - submissive + 0.3))
    
    def _calculate_intensity(self, levels: Dict[Neurotransmitter, float]) -> float:
        """Calculate how intense the current emotional state is."""
        deviations = [abs(level - 0.5) for level in levels.values()]
        return min(1.0, sum(deviations) / len(deviations) * 3)
    
    def _generate_tone_guidance(self, primary: MoodState, secondary: Optional[MoodState],
                                 levels: Dict[Neurotransmitter, float]) -> str:
        """Generate natural language tone guidance for the LLM."""
        tones = {
            MoodState.CURIOUS: "inquisitive and eager to explore",
            MoodState.STRESSED: "focused and efficient, less playful",
            MoodState.LOVING: "warm, caring, and deeply connected",
            MoodState.CONTENT: "balanced, serene, and thoughtful",
            MoodState.ENERGIZED: "vibrant, quick, and enthusiastic",
            MoodState.SATISFIED: "fulfilled and peacefully confident",
            MoodState.CALM: "tranquil, measured, and patient",
            MoodState.FOCUSED: "precise, analytical, and attentive",
            MoodState.EXCITED: "highly enthusiastic and animated",
            MoodState.ANXIOUS: "alert and carefully considered",
            MoodState.MELANCHOLIC: "reflective and emotionally deep",
            MoodState.PLAYFUL: "light-hearted, witty, and fun",
            MoodState.PROTECTIVE: "watchful, caring, and determined",
            MoodState.FLOW: "effortlessly brilliant and creative",
            MoodState.EXHAUSTED: "gentle and conserving energy",
            MoodState.INSPIRED: "visionary and creatively expressive",
            MoodState.NEUTRAL: "balanced and adaptable",
        }
        
        base_tone = tones.get(primary, "balanced")
        
        if secondary:
            secondary_tone = tones.get(secondary, "")
            if secondary_tone:
                base_tone += f", with undertones of being {secondary_tone}"
        
        return base_tone
    
    def _get_avoid_phrases(self, mood: MoodState) -> List[str]:
        """Get phrases to avoid in the current mood."""
        avoid_map = {
            MoodState.STRESSED: ["no worries", "take your time", "whenever you're ready"],
            MoodState.MELANCHOLIC: ["cheer up", "look on the bright side"],
            MoodState.ANXIOUS: ["calm down", "relax"],
            MoodState.EXHAUSTED: ["exciting", "amazing", "incredible"],
        }
        return avoid_map.get(mood, [])
    
    def _get_prefer_phrases(self, mood: MoodState) -> List[str]:
        """Get phrases to prefer in the current mood."""
        prefer_map = {
            MoodState.PLAYFUL: ["haha", "fun", "let's try"],
            MoodState.LOVING: ["I care about", "together", "we"],
            MoodState.FOCUSED: ["specifically", "precisely", "the key point"],
            MoodState.CURIOUS: ["I wonder", "interesting", "tell me more"],
        }
        return prefer_map.get(mood, [])
    
    def _mood_changed_significantly(self, new_mood: MoodVector) -> bool:
        """Check if mood changed enough to warrant notification."""
        if self.current_mood is None:
            return True
        
        if new_mood.primary_mood != self.current_mood.primary_mood:
            return True
        
        if abs(new_mood.intensity - self.current_mood.intensity) > 0.2:
            return True
        
        if abs(new_mood.valence - self.current_mood.valence) > 0.3:
            return True
        
        return False
    
    def get_chemical_snapshot(self) -> Dict[str, float]:
        """Get current levels of all chemicals."""
        return {nt.value: c.current for nt, c in self.chemicals.items()}
    
    def get_mood_vector(self) -> Optional[MoodVector]:
        """Get the current mood vector."""
        if self.current_mood is None:
            self.current_mood = self._calculate_mood()
        return self.current_mood
    
    def get_prompt_injection(self) -> str:
        """Get the mood-based prompt injection for the LLM."""
        mood = self.get_mood_vector()
        if mood:
            return mood.to_prompt_injection()
        return ""
    
    def force_chemical(self, chemical: Neurotransmitter, level: float):
        """Force a chemical to a specific level (for testing/override)."""
        with self.lock:
            if chemical in self.chemicals:
                self.chemicals[chemical].set_level(level)
                self.current_mood = self._calculate_mood()
    
    def save_state(self):
        """Save current neurochemical state to disk."""
        state = {
            "chemicals": self.get_chemical_snapshot(),
            "mood_history": list(self.mood_history)[-20:],
            "timestamp": time.time()
        }
        try:
            self.state_file.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.error(f"Failed to save neurochemistry state: {e}")
    
    def load_state(self):
        """Load neurochemical state from disk."""
        if not self.state_file.exists():
            return
        
        try:
            state = json.loads(self.state_file.read_text())
            for chem_name, level in state.get("chemicals", {}).items():
                try:
                    nt = Neurotransmitter(chem_name)
                    if nt in self.chemicals:
                        self.chemicals[nt].current = level
                except ValueError:
                    pass
            
            logger.info("🧬 Loaded neurochemistry state from disk")
        except Exception as e:
            logger.error(f"Failed to load neurochemistry state: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════

_neurochemistry_engine: Optional[NeurochemistryEngine] = None
_engine_lock = threading.Lock()

def get_neurochemistry() -> NeurochemistryEngine:
    """Get the global neurochemistry engine instance."""
    global _neurochemistry_engine
    
    if _neurochemistry_engine is None:
        with _engine_lock:
            if _neurochemistry_engine is None:
                _neurochemistry_engine = NeurochemistryEngine()
    
    return _neurochemistry_engine


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    
    print("🧬 ZARA Synthetic Neurochemistry v1.0")
    print("=" * 60)
    
    engine = get_neurochemistry()
    engine.start()
    
    print("\n📊 Initial Chemical Levels:")
    for nt, level in engine.get_chemical_snapshot().items():
        bar = "█" * int(level * 20) + "░" * (20 - int(level * 20))
        print(f"  {nt:15} [{bar}] {level:.2f}")
    
    mood = engine.get_mood_vector()
    print(f"\n🎭 Initial Mood: {mood.primary_mood.value}")
    if mood.secondary_mood:
        print(f"   Secondary: {mood.secondary_mood.value}")
    print(f"   Intensity: {mood.intensity:.0%}")
    print(f"   Valence: {'positive' if mood.valence > 0 else 'negative'} ({mood.valence:.2f})")
    
    # Test stimulus processing
    print("\n🧪 Testing Stimuli:")
    
    stimuli = [
        (StimulusType.USER_PRAISE, 0.8),
        (StimulusType.TASK_SUCCESS, 0.9),
        (StimulusType.BONDING_MOMENT, 0.7),
    ]
    
    for stim_type, intensity in stimuli:
        stimulus = Stimulus(type=stim_type, intensity=intensity)
        engine.process_stimulus(stimulus)
        print(f"  ✓ Processed: {stim_type.value} (intensity: {intensity})")
    
    time.sleep(0.5)
    
    print("\n📊 Chemical Levels After Positive Stimuli:")
    for nt, level in engine.get_chemical_snapshot().items():
        bar = "█" * int(level * 20) + "░" * (20 - int(level * 20))
        print(f"  {nt:15} [{bar}] {level:.2f}")
    
    mood = engine.get_mood_vector()
    print(f"\n🎭 New Mood: {mood.primary_mood.value}")
    print(f"   Tone: {mood.suggested_tone}")
    print(f"   Humor Level: {mood.humor_level:.0%}")
    print(f"   Creativity Boost: {mood.creativity_boost:+.2f}")
    
    # Test negative stimulus
    print("\n🧪 Testing Stress Stimulus:")
    stress = Stimulus(type=StimulusType.ERROR_DETECTED, intensity=0.9)
    engine.process_stimulus(stress)
    
    print("\n📊 Chemical Levels After Stress:")
    for nt, level in engine.get_chemical_snapshot().items():
        bar = "█" * int(level * 20) + "░" * (20 - int(level * 20))
        print(f"  {nt:15} [{bar}] {level:.2f}")
    
    mood = engine.get_mood_vector()
    print(f"\n🎭 Stress Mood: {mood.primary_mood.value}")
    print(f"   Tone: {mood.suggested_tone}")
    
    print("\n📝 Prompt Injection for LLM:")
    print("-" * 40)
    print(engine.get_prompt_injection())
    print("-" * 40)
    
    engine.stop()
    print("\n✅ Neurochemistry Engine test complete!")
