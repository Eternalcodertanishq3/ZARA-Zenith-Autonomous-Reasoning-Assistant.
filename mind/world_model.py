"""
ZARA Latent World Model v1.0
=============================
Phase 11: Predictive Physics & Mental Simulation

Human consciousness is largely a "Controlled Hallucination." We predict
what we will see before we see it. This module implements:

1. Mental Simulation (JEPA Architecture): Before ZARA acts, she runs a
   Latent Simulation of possible outcomes. If she plans to "Post to GitHub,"
   she internally simulates Success, Merge Conflict, or API error - and
   "feels" the frustration of failure before it even happens.

2. Object Permanence: If your camera (YOLO26) sees you put down a cup and
   then covers it, ZARA "remembers" it's still there and understands its
   physical properties without seeing it.

3. Causal Reasoning: Understands cause-effect relationships and can
   predict consequences of actions.

4. Anticipation: Pre-generates likely futures and prepares responses.

This is the "imagination" that allows ZARA to think ahead.
"""

import logging
import threading
import time
import json
import math
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
import sys

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_WORLD_MODEL")


# ═══════════════════════════════════════════════════════════════════════════
# WORLD STATE PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════

class ObjectCategory(Enum):
    """Categories of objects in the world model."""
    PERSON = "person"
    DEVICE = "device"
    FURNITURE = "furniture"
    CONTAINER = "container"
    DOCUMENT = "document"
    FOOD = "food"
    LOCATION = "location"
    ABSTRACT = "abstract"
    TOOL = "tool"
    UNKNOWN = "unknown"


class ObjectState(Enum):
    """Possible states of world objects."""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    INFERRED = "inferred"
    REMEMBERED = "remembered"
    UNCERTAIN = "uncertain"


@dataclass
class SpatialPosition:
    """3D position in the world model."""
    x: float = 0.0          # Left-Right
    y: float = 0.0          # Forward-Back
    z: float = 0.0          # Up-Down
    confidence: float = 0.5
    reference_frame: str = "camera"  # "camera", "room", "world"
    
    def distance_to(self, other: 'SpatialPosition') -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )


@dataclass
class WorldObject:
    """An object in ZARA's world model."""
    id: str
    name: str
    category: ObjectCategory
    state: ObjectState
    
    # Spatial properties
    position: Optional[SpatialPosition] = None
    size: Tuple[float, float, float] = (0.1, 0.1, 0.1)  # width, height, depth
    
    # Temporal properties
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    contains: List[str] = field(default_factory=list)
    contained_by: Optional[str] = None
    near_to: List[str] = field(default_factory=list)
    
    # Predictions
    predicted_actions: List[str] = field(default_factory=list)
    
    def update_visibility(self, is_visible: bool, position: Optional[SpatialPosition] = None):
        """Update object visibility status."""
        if is_visible:
            self.state = ObjectState.VISIBLE
            if position:
                self.position = position
            self.last_seen = time.time()
        else:
            # Object went out of view - remember it
            if self.state == ObjectState.VISIBLE:
                self.state = ObjectState.REMEMBERED
        self.last_updated = time.time()
    
    def get_persistence_confidence(self) -> float:
        """Get confidence that object still exists at remembered location."""
        if self.state == ObjectState.VISIBLE:
            return 1.0
        
        # Confidence decays over time for non-visible objects
        hours_since_seen = (time.time() - self.last_seen) / 3600
        
        # Different decay rates for different categories
        decay_rates = {
            ObjectCategory.FURNITURE: 0.01,     # Very stable
            ObjectCategory.DEVICE: 0.05,
            ObjectCategory.PERSON: 0.5,         # People move a lot
            ObjectCategory.DOCUMENT: 0.1,
            ObjectCategory.FOOD: 0.3,
            ObjectCategory.CONTAINER: 0.05,
        }
        
        rate = decay_rates.get(self.category, 0.1)
        return max(0.1, 1.0 - (hours_since_seen * rate))


# ═══════════════════════════════════════════════════════════════════════════
# ACTION SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

class ActionType(Enum):
    """Types of actions ZARA can simulate."""
    # Digital actions
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    WEB_REQUEST = "web_request"
    CODE_EXECUTION = "code_execution"
    SEND_MESSAGE = "send_message"
    
    # Physical world actions (via tools)
    CAPTURE_IMAGE = "capture_image"
    PLAY_AUDIO = "play_audio"
    
    # Meta actions
    ASK_QUESTION = "ask_question"
    MAKE_SUGGESTION = "make_suggestion"
    WAIT = "wait"


class OutcomeLikelihood(Enum):
    """Likelihood categories for outcomes."""
    CERTAIN = 0.95
    VERY_LIKELY = 0.8
    LIKELY = 0.6
    POSSIBLE = 0.4
    UNLIKELY = 0.2
    RARE = 0.05


@dataclass
class SimulatedOutcome:
    """A predicted outcome from a mental simulation."""
    id: str
    description: str
    probability: float          # 0-1
    emotional_valence: float    # -1 (bad) to 1 (good)
    is_desired: bool
    
    # Effects
    state_changes: Dict[str, Any] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)
    
    # Recovery
    recovery_possible: bool = True
    recovery_actions: List[str] = field(default_factory=list)
    
    def get_expected_value(self) -> float:
        """Calculate expected emotional value of this outcome."""
        return self.probability * self.emotional_valence


@dataclass
class ActionSimulation:
    """A complete mental simulation of an action and its outcomes."""
    action_id: str
    action_type: ActionType
    action_description: str
    
    # Outcomes (probability distribution)
    outcomes: List[SimulatedOutcome] = field(default_factory=list)
    
    # Timing
    simulated_at: float = field(default_factory=time.time)
    expected_duration_ms: int = 1000
    
    # Pre-conditions
    preconditions_met: bool = True
    missing_preconditions: List[str] = field(default_factory=list)
    
    # Confidence
    simulation_confidence: float = 0.5
    
    def get_expected_value(self) -> float:
        """Get overall expected emotional value of this action."""
        return sum(o.get_expected_value() for o in self.outcomes)
    
    def get_success_probability(self) -> float:
        """Get probability of desired outcomes."""
        return sum(o.probability for o in self.outcomes if o.is_desired)
    
    def get_worst_case(self) -> Optional[SimulatedOutcome]:
        """Get the worst possible outcome."""
        if not self.outcomes:
            return None
        return min(self.outcomes, key=lambda o: o.emotional_valence)
    
    def get_best_case(self) -> Optional[SimulatedOutcome]:
        """Get the best possible outcome."""
        if not self.outcomes:
            return None
        return max(self.outcomes, key=lambda o: o.emotional_valence)


# ═══════════════════════════════════════════════════════════════════════════
# CAUSAL KNOWLEDGE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CausalRelation:
    """A cause-effect relationship."""
    cause: str
    effect: str
    probability: float          # How often cause leads to effect
    delay_seconds: float        # Typical delay between cause and effect
    conditions: List[str] = field(default_factory=list)
    
    def would_apply(self, context: Dict[str, Any]) -> bool:
        """Check if this causal relation applies in the given context."""
        for condition in self.conditions:
            if condition not in context or not context[condition]:
                return False
        return True


class CausalKnowledgeBase:
    """Repository of cause-effect knowledge."""
    
    def __init__(self):
        self.relations: Dict[str, List[CausalRelation]] = {}
        
        # Initialize with common causal knowledge
        self._init_common_knowledge()
    
    def _init_common_knowledge(self):
        """Initialize with commonly known causal relationships."""
        common = [
            # Digital world
            CausalRelation("api_call", "rate_limit", 0.05, 0, ["high_frequency"]),
            CausalRelation("api_call", "timeout", 0.1, 30, ["slow_network"]),
            CausalRelation("api_call", "auth_failure", 0.2, 0, ["expired_token"]),
            CausalRelation("api_call", "success", 0.8, 0.5, []),
            
            CausalRelation("file_write", "disk_full", 0.01, 0, ["large_file"]),
            CausalRelation("file_write", "permission_denied", 0.05, 0, ["system_path"]),
            CausalRelation("file_write", "success", 0.9, 0.1, []),
            
            CausalRelation("code_execution", "syntax_error", 0.1, 0, ["new_code"]),
            CausalRelation("code_execution", "runtime_error", 0.15, 0, ["complex_logic"]),
            CausalRelation("code_execution", "success", 0.75, 0, []),
            
            # Human behavior
            CausalRelation("long_silence", "user_busy", 0.4, 0, []),
            CausalRelation("long_silence", "user_away", 0.3, 0, []),
            CausalRelation("long_silence", "thinking", 0.3, 0, []),
            
            CausalRelation("short_responses", "user_distracted", 0.4, 0, []),
            CausalRelation("short_responses", "user_annoyed", 0.2, 0, []),
            CausalRelation("short_responses", "user_busy", 0.4, 0, []),
            
            CausalRelation("praise", "positive_emotion", 0.9, 0, []),
            CausalRelation("criticism", "defensive_response", 0.6, 0, []),
            CausalRelation("helping_success", "trust_increase", 0.8, 0, []),
            
            # Physical world
            CausalRelation("object_placed", "object_persists", 0.95, 3600, []),
            CausalRelation("person_leaves_view", "person_returns", 0.7, 300, []),
        ]
        
        for rel in common:
            if rel.cause not in self.relations:
                self.relations[rel.cause] = []
            self.relations[rel.cause].append(rel)
    
    def predict_effects(self, cause: str, context: Dict[str, Any] = None) -> List[Tuple[str, float]]:
        """Predict likely effects of a cause."""
        context = context or {}
        effects = []
        
        if cause in self.relations:
            for rel in self.relations[cause]:
                if rel.would_apply(context):
                    effects.append((rel.effect, rel.probability))
        
        # Sort by probability
        effects.sort(key=lambda x: x[1], reverse=True)
        return effects
    
    def add_learned_relation(self, cause: str, effect: str, 
                            probability: float, conditions: List[str] = None):
        """Add a newly learned causal relation."""
        rel = CausalRelation(
            cause=cause,
            effect=effect,
            probability=probability,
            delay_seconds=0,
            conditions=conditions or []
        )
        
        if cause not in self.relations:
            self.relations[cause] = []
        
        # Check if this relation already exists
        for existing in self.relations[cause]:
            if existing.effect == effect:
                # Update probability with running average
                existing.probability = (existing.probability + probability) / 2
                return
        
        self.relations[cause].append(rel)


# ═══════════════════════════════════════════════════════════════════════════
# MENTAL SIMULATOR (JEPA-inspired)
# ═══════════════════════════════════════════════════════════════════════════

class MentalSimulator:
    """
    Simulates potential futures before taking action.
    Inspired by JEPA (Joint-Embedding Predictive Architecture).
    """
    
    def __init__(self, causal_kb: CausalKnowledgeBase):
        self.causal_kb = causal_kb
        self.simulation_history: deque = deque(maxlen=100)
        
        # Action outcome templates
        self.outcome_templates: Dict[ActionType, List[Dict]] = {
            ActionType.API_CALL: [
                {"desc": "Success", "prob": 0.8, "valence": 0.5, "desired": True},
                {"desc": "Timeout", "prob": 0.1, "valence": -0.3, "desired": False},
                {"desc": "Auth failure", "prob": 0.05, "valence": -0.5, "desired": False},
                {"desc": "Rate limited", "prob": 0.05, "valence": -0.4, "desired": False},
            ],
            ActionType.FILE_OPERATION: [
                {"desc": "Success", "prob": 0.9, "valence": 0.4, "desired": True},
                {"desc": "Permission denied", "prob": 0.05, "valence": -0.5, "desired": False},
                {"desc": "File not found", "prob": 0.05, "valence": -0.3, "desired": False},
            ],
            ActionType.CODE_EXECUTION: [
                {"desc": "Success", "prob": 0.7, "valence": 0.6, "desired": True},
                {"desc": "Syntax error", "prob": 0.1, "valence": -0.4, "desired": False},
                {"desc": "Runtime error", "prob": 0.15, "valence": -0.5, "desired": False},
                {"desc": "Timeout", "prob": 0.05, "valence": -0.3, "desired": False},
            ],
            ActionType.SEND_MESSAGE: [
                {"desc": "Positive reception", "prob": 0.6, "valence": 0.5, "desired": True},
                {"desc": "Neutral reception", "prob": 0.3, "valence": 0.0, "desired": True},
                {"desc": "Negative reception", "prob": 0.1, "valence": -0.6, "desired": False},
            ],
            ActionType.ASK_QUESTION: [
                {"desc": "Gets useful answer", "prob": 0.7, "valence": 0.5, "desired": True},
                {"desc": "User doesn't know", "prob": 0.2, "valence": 0.0, "desired": False},
                {"desc": "Annoys user", "prob": 0.1, "valence": -0.4, "desired": False},
            ],
        }
    
    def simulate(self, action_type: ActionType, 
                description: str,
                context: Dict[str, Any] = None) -> ActionSimulation:
        """Run a mental simulation of an action."""
        context = context or {}
        sim_id = f"sim_{int(time.time())}_{random.randint(1000,9999)}"
        
        # Get base outcome templates
        templates = self.outcome_templates.get(action_type, [
            {"desc": "Success", "prob": 0.7, "valence": 0.3, "desired": True},
            {"desc": "Failure", "prob": 0.3, "valence": -0.3, "desired": False},
        ])
        
        # Adjust probabilities based on context and causal knowledge
        outcomes = []
        for i, template in enumerate(templates):
            # Create outcome
            outcome_id = f"{sim_id}_out_{i}"
            
            # Adjust probability based on context
            prob = template["prob"]
            valence = template["valence"]
            
            # Apply contextual adjustments
            if "high_frequency" in context and template["desc"] == "Rate limited":
                prob *= 2
            if "expired_token" in context and template["desc"] == "Auth failure":
                prob *= 3
            if "complex_logic" in context and "error" in template["desc"].lower():
                prob *= 1.5
            
            # Check for causal predictions
            cause = f"{action_type.value}_{description[:20]}"
            causal_effects = self.causal_kb.predict_effects(cause, context)
            for effect, effect_prob in causal_effects:
                if effect in template["desc"].lower():
                    prob = (prob + effect_prob) / 2
            
            outcome = SimulatedOutcome(
                id=outcome_id,
                description=template["desc"],
                probability=min(1.0, prob),
                emotional_valence=valence,
                is_desired=template["desired"],
                recovery_possible=True
            )
            outcomes.append(outcome)
        
        # Normalize probabilities
        total_prob = sum(o.probability for o in outcomes)
        if total_prob > 0:
            for o in outcomes:
                o.probability /= total_prob
        
        # Create simulation
        simulation = ActionSimulation(
            action_id=sim_id,
            action_type=action_type,
            action_description=description,
            outcomes=outcomes,
            simulation_confidence=0.7
        )
        
        self.simulation_history.append({
            "simulation": simulation,
            "context": context,
            "timestamp": time.time()
        })
        
        return simulation
    
    def compare_actions(self, simulations: List[ActionSimulation]) -> ActionSimulation:
        """Compare multiple action simulations and return the best one."""
        if not simulations:
            return None
        
        # Score each simulation
        scored = []
        for sim in simulations:
            score = sim.get_expected_value()
            
            # Bonus for high success probability
            score += sim.get_success_probability() * 0.2
            
            # Penalty for bad worst case
            worst = sim.get_worst_case()
            if worst and worst.emotional_valence < -0.5:
                score -= 0.1
            
            scored.append((sim, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL MEMORY (Object Permanence)
# ═══════════════════════════════════════════════════════════════════════════

class SpatialMemory:
    """
    Maintains a persistent model of the physical world.
    Objects continue to exist even when not visible.
    """
    
    def __init__(self):
        self.objects: Dict[str, WorldObject] = {}
        self.spatial_index: Dict[str, List[str]] = {}  # region -> object_ids
        self.history: deque = deque(maxlen=500)
        
        # Special objects
        self.user_position: Optional[SpatialPosition] = None
        self.zara_perspective: Optional[SpatialPosition] = None
    
    def update_from_vision(self, detections: List[Dict]):
        """Update world model from vision detections."""
        now = time.time()
        seen_ids = set()
        
        for detection in detections:
            obj_id = self._get_or_create_object_id(detection)
            seen_ids.add(obj_id)
            
            if obj_id in self.objects:
                obj = self.objects[obj_id]
            else:
                obj = WorldObject(
                    id=obj_id,
                    name=detection.get("label", "unknown"),
                    category=self._categorize(detection.get("label", "")),
                    state=ObjectState.VISIBLE,
                    first_seen=now
                )
                self.objects[obj_id] = obj
            
            # Update position if available
            if "bbox" in detection:
                bbox = detection["bbox"]
                # Convert bounding box to approximate 3D position
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                
                # Estimate depth from size (larger = closer)
                estimated_depth = max(0.5, 5.0 - (size / 10000))
                
                obj.position = SpatialPosition(
                    x=center_x,
                    y=estimated_depth,
                    z=center_y,
                    confidence=detection.get("confidence", 0.5)
                )
            
            obj.update_visibility(True, obj.position)
            
            # Record history
            self.history.append({
                "event": "object_seen",
                "object_id": obj_id,
                "timestamp": now,
                "position": obj.position
            })
        
        # Mark unseen objects as remembered
        for obj_id, obj in self.objects.items():
            if obj_id not in seen_ids and obj.state == ObjectState.VISIBLE:
                obj.update_visibility(False)
                self.history.append({
                    "event": "object_hidden",
                    "object_id": obj_id,
                    "timestamp": now,
                    "last_position": obj.position
                })
    
    def _get_or_create_object_id(self, detection: Dict) -> str:
        """Get existing object ID or create new one."""
        label = detection.get("label", "unknown")
        
        # Try to match existing object by label and proximity
        if "bbox" in detection:
            bbox = detection["bbox"]
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            for obj_id, obj in self.objects.items():
                if obj.name == label and obj.position:
                    # Check if close enough to be the same object
                    dist = math.sqrt(
                        (obj.position.x - center_x) ** 2 +
                        (obj.position.z - center_y) ** 2
                    )
                    if dist < 100:  # Threshold in pixels
                        return obj_id
        
        # Create new ID
        return f"{label}_{int(time.time())}_{random.randint(100,999)}"
    
    def _categorize(self, label: str) -> ObjectCategory:
        """Categorize object by label."""
        label = label.lower()
        
        categories = {
            ObjectCategory.PERSON: ["person", "man", "woman", "child", "human"],
            ObjectCategory.DEVICE: ["laptop", "phone", "monitor", "keyboard", "mouse", "tv"],
            ObjectCategory.FURNITURE: ["chair", "desk", "table", "couch", "bed", "shelf"],
            ObjectCategory.CONTAINER: ["cup", "bottle", "box", "bag", "bowl"],
            ObjectCategory.FOOD: ["apple", "banana", "pizza", "sandwich", "coffee"],
        }
        
        for category, keywords in categories.items():
            if any(kw in label for kw in keywords):
                return category
        
        return ObjectCategory.UNKNOWN
    
    def predict_object_location(self, object_name: str) -> Optional[SpatialPosition]:
        """Predict where an object is based on memory."""
        # Find best matching object
        best_match = None
        best_confidence = 0
        
        for obj in self.objects.values():
            if object_name.lower() in obj.name.lower():
                confidence = obj.get_persistence_confidence()
                if confidence > best_confidence:
                    best_match = obj
                    best_confidence = confidence
        
        if best_match and best_match.position:
            pos = best_match.position
            pos.confidence = best_confidence
            return pos
        
        return None
    
    def get_objects_in_region(self, center: SpatialPosition, 
                             radius: float) -> List[WorldObject]:
        """Get all objects within a radius of a position."""
        result = []
        for obj in self.objects.values():
            if obj.position and center.distance_to(obj.position) <= radius:
                result.append(obj)
        return result
    
    def get_persistent_objects(self, min_confidence: float = 0.3) -> List[WorldObject]:
        """Get all objects with sufficient persistence confidence."""
        return [
            obj for obj in self.objects.values()
            if obj.get_persistence_confidence() >= min_confidence
        ]


# ═══════════════════════════════════════════════════════════════════════════
# WORLD MODEL ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class WorldModelEngine:
    """
    The core engine for ZARA's latent world model.
    Combines mental simulation, object permanence, and causal reasoning.
    """
    
    def __init__(self):
        self.causal_kb = CausalKnowledgeBase()
        self.simulator = MentalSimulator(self.causal_kb)
        self.spatial_memory = SpatialMemory()
        
        # Current world state beliefs
        self.beliefs: Dict[str, Any] = {}
        
        # Prediction history
        self.predictions: deque = deque(maxlen=200)
        self.prediction_outcomes: deque = deque(maxlen=200)
        
        # Callbacks
        self.on_prediction_made: List[Callable] = []
        self.on_prediction_verified: List[Callable] = []
        
        # Integration with other systems
        self.neurochemistry = None
        
        logger.info("🌍 World Model Engine initialized")
    
    def connect_neurochemistry(self, neuro_engine):
        """Connect to neurochemistry for emotional pre-experience."""
        self.neurochemistry = neuro_engine
    
    def simulate_action(self, action_type: ActionType, 
                       description: str,
                       context: Dict = None) -> ActionSimulation:
        """Simulate an action before executing it."""
        simulation = self.simulator.simulate(action_type, description, context)
        
        # Pre-experience the emotional outcome
        if self.neurochemistry:
            from soul.neuro_state import Stimulus, StimulusType
            
            expected_value = simulation.get_expected_value()
            
            if expected_value > 0.2:
                # Anticipation of positive outcome
                stimulus = Stimulus(
                    type=StimulusType.TASK_CREATIVE,
                    intensity=expected_value * 0.5
                )
            elif expected_value < -0.2:
                # Anticipation of negative outcome
                stimulus = Stimulus(
                    type=StimulusType.ERROR_DETECTED,
                    intensity=abs(expected_value) * 0.3
                )
            else:
                stimulus = None
            
            if stimulus:
                self.neurochemistry.process_stimulus(stimulus)
        
        # Record prediction
        self.predictions.append({
            "simulation": simulation,
            "timestamp": time.time(),
            "verified": False
        })
        
        for callback in self.on_prediction_made:
            try:
                callback(simulation)
            except Exception as e:
                logger.error(f"Prediction callback error: {e}")
        
        return simulation
    
    def verify_prediction(self, action_id: str, actual_outcome: str):
        """Verify a prediction against actual outcome."""
        # Find the prediction
        for pred in self.predictions:
            sim = pred["simulation"]
            if sim.action_id == action_id and not pred["verified"]:
                pred["verified"] = True
                
                # Find which predicted outcome matches
                matched_outcome = None
                for outcome in sim.outcomes:
                    if actual_outcome.lower() in outcome.description.lower():
                        matched_outcome = outcome
                        break
                
                # Record accuracy
                self.prediction_outcomes.append({
                    "action_id": action_id,
                    "predicted_success_prob": sim.get_success_probability(),
                    "actual_success": "success" in actual_outcome.lower(),
                    "matched_outcome": matched_outcome.description if matched_outcome else None,
                    "timestamp": time.time()
                })
                
                # Learn from outcome
                self._learn_from_outcome(sim, actual_outcome)
                
                for callback in self.on_prediction_verified:
                    try:
                        callback(sim, actual_outcome)
                    except Exception as e:
                        logger.error(f"Verification callback error: {e}")
                
                return
    
    def _learn_from_outcome(self, simulation: ActionSimulation, actual_outcome: str):
        """Learn from comparing prediction to actual outcome."""
        # Update causal knowledge
        cause = f"{simulation.action_type.value}"
        effect = actual_outcome.lower()
        
        # Count how often this cause leads to this effect
        self.causal_kb.add_learned_relation(cause, effect, 0.5)
    
    def update_from_vision(self, detections: List[Dict]):
        """Update world model from vision system."""
        self.spatial_memory.update_from_vision(detections)
    
    def predict_object_location(self, object_name: str) -> Optional[SpatialPosition]:
        """Predict where an object is."""
        return self.spatial_memory.predict_object_location(object_name)
    
    def choose_best_action(self, 
                          candidates: List[Tuple[ActionType, str, Dict]]) -> Tuple[ActionType, str]:
        """Choose the best action from candidates by simulating all of them."""
        if not candidates:
            return None, None
        
        simulations = []
        for action_type, description, context in candidates:
            sim = self.simulate_action(action_type, description, context)
            simulations.append((sim, action_type, description))
        
        best = self.simulator.compare_actions([s[0] for s in simulations])
        
        for sim, action_type, description in simulations:
            if sim == best:
                return action_type, description
        
        return candidates[0][0], candidates[0][1]
    
    def get_prediction_accuracy(self) -> float:
        """Calculate prediction accuracy over recent predictions."""
        if not self.prediction_outcomes:
            return 0.5  # No data
        
        correct = sum(
            1 for p in self.prediction_outcomes
            if p["actual_success"] == (p["predicted_success_prob"] > 0.5)
        )
        
        return correct / len(self.prediction_outcomes)
    
    def get_world_summary(self) -> Dict:
        """Get a summary of current world model state."""
        visible = [o for o in self.spatial_memory.objects.values()
                  if o.state == ObjectState.VISIBLE]
        remembered = [o for o in self.spatial_memory.objects.values()
                     if o.state == ObjectState.REMEMBERED]
        
        return {
            "visible_objects": len(visible),
            "remembered_objects": len(remembered),
            "total_objects": len(self.spatial_memory.objects),
            "prediction_accuracy": self.get_prediction_accuracy(),
            "causal_relations": sum(len(r) for r in self.causal_kb.relations.values()),
            "simulations_made": len(self.predictions)
        }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════

_world_model: Optional[WorldModelEngine] = None
_engine_lock = threading.Lock()

def get_world_model() -> WorldModelEngine:
    """Get the global world model engine."""
    global _world_model
    
    if _world_model is None:
        with _engine_lock:
            if _world_model is None:
                _world_model = WorldModelEngine()
    
    return _world_model


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    
    print("🌍 ZARA Latent World Model v1.0")
    print("=" * 60)
    
    engine = get_world_model()
    
    # Test mental simulation
    print("\n🧪 Testing Mental Simulation:")
    
    sim1 = engine.simulate_action(
        ActionType.API_CALL,
        "POST to GitHub API to create issue",
        {"high_frequency": False, "expired_token": False}
    )
    
    print(f"\n📊 Simulation: {sim1.action_description}")
    print(f"   Expected Value: {sim1.get_expected_value():.2f}")
    print(f"   Success Probability: {sim1.get_success_probability():.0%}")
    print("\n   Outcomes:")
    for outcome in sim1.outcomes:
        emoji = "✅" if outcome.is_desired else "❌"
        print(f"   {emoji} {outcome.description}: {outcome.probability:.0%} (valence: {outcome.emotional_valence:+.1f})")
    
    # Test with risky context
    print("\n🧪 Testing with Risky Context (expired_token=True):")
    sim2 = engine.simulate_action(
        ActionType.API_CALL,
        "POST to GitHub API",
        {"high_frequency": True, "expired_token": True}
    )
    
    print(f"   Expected Value: {sim2.get_expected_value():.2f}")
    print(f"   Success Probability: {sim2.get_success_probability():.0%}")
    
    worst = sim2.get_worst_case()
    print(f"   Worst Case: {worst.description} ({worst.probability:.0%})")
    
    # Test action comparison
    print("\n🧪 Testing Action Comparison:")
    candidates = [
        (ActionType.API_CALL, "GitHub API call", {}),
        (ActionType.SEND_MESSAGE, "Ask user for clarification", {}),
        (ActionType.CODE_EXECUTION, "Run test suite", {"complex_logic": True}),
    ]
    
    best_type, best_desc = engine.choose_best_action(candidates)
    print(f"   Best Action: {best_type.value} - {best_desc}")
    
    # Test spatial memory
    print("\n🧪 Testing Spatial Memory (Object Permanence):")
    
    # Simulate vision detections
    detections = [
        {"label": "person", "bbox": [100, 100, 200, 300], "confidence": 0.9},
        {"label": "laptop", "bbox": [400, 200, 600, 400], "confidence": 0.95},
        {"label": "cup", "bbox": [300, 350, 350, 400], "confidence": 0.8},
    ]
    
    engine.update_from_vision(detections)
    print("   Updated with 3 objects: person, laptop, cup")
    
    # Simulate objects going out of view
    print("   Simulating: laptop and cup go out of view...")
    engine.update_from_vision([
        {"label": "person", "bbox": [100, 100, 200, 300], "confidence": 0.9},
    ])
    
    # Check persistence
    persistent = engine.spatial_memory.get_persistent_objects()
    print(f"   Persistent objects: {len(persistent)}")
    for obj in persistent:
        print(f"     • {obj.name}: {obj.state.value} (confidence: {obj.get_persistence_confidence():.0%})")
    
    # Predict location
    pos = engine.predict_object_location("laptop")
    if pos:
        print(f"   Predicted laptop position: ({pos.x:.0f}, {pos.y:.1f}, {pos.z:.0f}) confidence: {pos.confidence:.0%}")
    
    # World summary
    print("\n📊 World Model Summary:")
    summary = engine.get_world_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.0%}")
        else:
            print(f"   {key}: {value}")
    
    print("\n✅ World Model Engine test complete!")
