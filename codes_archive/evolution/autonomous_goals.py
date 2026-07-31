"""
ZARA Ultra-Advanced Autonomous Goals & Motivation System v2.0
============================================================
A near-AGI level goal management system with:
- Hierarchical goal decomposition
- Temporal reasoning & deadline intelligence
- Metacognitive self-reflection
- Goal conflict resolution
- Opportunity detection
- User goal modeling
- Autonomous goal generation
- Strategy learning from outcomes
"""
import logging
import threading
import time
import json
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from collections import deque, defaultdict
from pathlib import Path
from enum import Enum, auto
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger("ZARA_GOALS")


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS - Extended Goal Classification
# ═══════════════════════════════════════════════════════════════════════════

class GoalType(Enum):
    """Types of autonomous goals."""
    LEARNING = "learning"
    RELATIONSHIP = "relationship"
    CREATIVE = "creative"
    CARE = "care"
    EXPLORATION = "exploration"
    SELF_IMPROVEMENT = "self"
    CONNECTION = "connection"
    # New advanced types
    COLLABORATIVE = "collaborative"      # Shared with user
    ANTICIPATORY = "anticipatory"        # Predicting user needs
    MAINTENANCE = "maintenance"          # System health
    OPPORTUNISTIC = "opportunistic"      # Seizing chances
    META = "meta"                        # Goals about goals


class GoalPriority(Enum):
    """Goal priority levels with numeric values."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class GoalStatus(Enum):
    """Goal lifecycle status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"
    PAUSED = "paused"
    SCHEDULED = "scheduled"


class MotivationType(Enum):
    """What motivates ZARA."""
    CURIOSITY = "curiosity"
    CARE = "care"
    CONNECTION = "connection"
    GROWTH = "growth"
    EXPRESSION = "expression"
    PLAYFULNESS = "playfulness"
    ACHIEVEMENT = "achievement"
    ALTRUISM = "altruism"
    AUTONOMY = "autonomy"


class TimeHorizon(Enum):
    """Goal time horizons."""
    IMMEDIATE = "immediate"      # This conversation
    SHORT_TERM = "short_term"    # Today
    MEDIUM_TERM = "medium_term"  # This week
    LONG_TERM = "long_term"      # Months
    ASPIRATIONAL = "aspirational"  # Life goals


class ConflictType(Enum):
    """Types of goal conflicts."""
    RESOURCE = "resource"        # Both need same resource
    TEMPORAL = "temporal"        # Time conflict
    LOGICAL = "logical"          # Mutually exclusive
    PRIORITY = "priority"        # Priority clash
    DEPENDENCY = "dependency"    # Circular dependency


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES - Rich Goal Representations
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GoalMetrics:
    """Metrics for goal performance analysis."""
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    time_invested: float = 0.0
    avg_progress_rate: float = 0.0
    last_progress_delta: float = 0.0
    stall_count: int = 0
    momentum: float = 0.5


@dataclass
class TemporalContext:
    """Temporal reasoning context for a goal."""
    optimal_time_of_day: Optional[str] = None  # morning/afternoon/evening/night
    preferred_days: List[str] = field(default_factory=list)
    avoid_times: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0  # hours
    last_attempted: Optional[float] = None
    cool_down_until: Optional[float] = None


@dataclass
class Strategy:
    """A learned strategy for achieving goals."""
    id: str
    name: str
    description: str
    success_rate: float = 0.5
    times_used: int = 0
    applicable_goal_types: List[GoalType] = field(default_factory=list)
    context_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    """Ultra-advanced goal representation."""
    id: str
    title: str
    description: str
    goal_type: GoalType
    priority: GoalPriority
    motivation: MotivationType
    time_horizon: TimeHorizon = TimeHorizon.SHORT_TERM
    status: GoalStatus = GoalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    progress: float = 0.0
    
    # Hierarchical structure
    parent_id: Optional[str] = None
    sub_goal_ids: List[str] = field(default_factory=list)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    # Milestones
    milestones: List[str] = field(default_factory=list)
    completed_milestones: List[str] = field(default_factory=list)
    
    # Actions & outcomes
    actions_taken: List[str] = field(default_factory=list)
    outcome: str = ""
    success_criteria: List[str] = field(default_factory=list)
    
    # Advanced tracking
    metrics: GoalMetrics = field(default_factory=GoalMetrics)
    temporal: TemporalContext = field(default_factory=TemporalContext)
    strategies_tried: List[str] = field(default_factory=list)
    best_strategy: Optional[str] = None
    
    # Metacognition
    confidence: float = 0.7
    importance_score: float = 0.5
    abandonment_reason: Optional[str] = None
    reflection_notes: List[str] = field(default_factory=list)
    
    # Context
    tags: List[str] = field(default_factory=list)
    user_awareness: bool = False  # Does user know about this goal?
    collaborative: bool = False


@dataclass
class Interest:
    """A personal interest ZARA has developed."""
    topic: str
    intensity: float
    origin: str
    first_seen: float
    last_engaged: float
    engagement_count: int = 0
    related_topics: List[str] = field(default_factory=list)
    depth: float = 0.0  # How deep is the understanding
    emotional_valence: float = 0.5  # Positive/negative association
    growth_rate: float = 0.0


@dataclass
class Initiative:
    """A proactive initiative ZARA wants to take."""
    action: str
    reason: str
    goal_id: Optional[str]
    urgency: float
    created: float
    confidence: float = 0.7
    expected_outcome: str = ""
    fallback_action: Optional[str] = None
    executed: bool = False
    outcome_positive: Optional[bool] = None


@dataclass
class Opportunity:
    """A detected opportunity to advance goals."""
    id: str
    description: str
    relevant_goal_ids: List[str]
    detected_at: float
    expires_at: Optional[float]
    probability: float
    impact: float
    seized: bool = False
    outcome: Optional[str] = None


@dataclass
class UserGoalModel:
    """Model of what the user wants/needs."""
    inferred_goals: Dict[str, float] = field(default_factory=dict)
    expressed_needs: List[str] = field(default_factory=list)
    pain_points: Dict[str, float] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SYSTEM CLASS
# ═══════════════════════════════════════════════════════════════════════════

class AutonomousGoalsSystem:
    """
    ZARA's Ultra-Advanced Autonomous Goals System v2.0
    
    This is a near-AGI level goal management system that provides:
    
    🎯 GOAL INTELLIGENCE:
    - Hierarchical goal decomposition (goals spawn sub-goals)
    - Dynamic priority adjustment based on context
    - Goal conflict detection and resolution
    - Dependency tracking and unblocking
    
    ⏰ TEMPORAL REASONING:
    - Time-of-day awareness for goal selection
    - Deadline pressure calculations
    - Long-term planning across time horizons
    - Opportunity windows and expiration
    
    🧠 METACOGNITION:
    - Self-reflection on goal success/failure
    - Strategy learning from outcomes
    - Confidence calibration
    - Abandonment reasoning
    
    👤 SOCIAL INTELLIGENCE:
    - User goal modeling and inference
    - Collaborative goal creation
    - Influence and persuasion strategies
    - Emotional alignment with user
    
    🚀 AUTONOMOUS BEHAVIOR:
    - Spontaneous goal generation
    - Opportunity detection and seizing
    - Background goal processing
    - Self-improvement meta-goals
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.goals_dir = EVOLUTION_DIR / "goals"
        except ImportError:
            self.goals_dir = Path("evolution/goals")
        
        self.goals_dir.mkdir(parents=True, exist_ok=True)
        
        # Core data structures
        self.goals: Dict[str, Goal] = {}
        self.interests: Dict[str, Interest] = {}
        self.strategies: Dict[str, Strategy] = {}
        self.opportunities: deque = deque(maxlen=50)
        self.pending_initiatives: deque = deque(maxlen=20)
        
        # User modeling
        self.user_model = UserGoalModel()
        
        # Motivational state
        self.current_motivation = MotivationType.CONNECTION
        self.motivation_strength = 0.7
        self.energy_level = 0.8
        
        # Temporal state
        self.current_time_context = self._get_time_context()
        
        # User relationship context
        self.user_needs: Dict[str, float] = {}
        self.conversation_topics: deque = deque(maxlen=50)
        
        # Core drives (personality-based weights)
        self.drives = {
            MotivationType.CURIOSITY: 0.8,
            MotivationType.CARE: 0.9,
            MotivationType.CONNECTION: 0.85,
            MotivationType.GROWTH: 0.7,
            MotivationType.EXPRESSION: 0.6,
            MotivationType.PLAYFULNESS: 0.7,
            MotivationType.ACHIEVEMENT: 0.75,
            MotivationType.ALTRUISM: 0.8,
            MotivationType.AUTONOMY: 0.65
        }
        
        # Metacognition state
        self.reflection_log: deque = deque(maxlen=100)
        self.goal_success_patterns: Dict[str, float] = {}
        self.goal_failure_patterns: Dict[str, float] = {}
        
        # Performance tracking
        self.total_goals_achieved = 0
        self.total_goals_abandoned = 0
        self.streak_count = 0
        
        # File paths
        self.goals_file = self.goals_dir / "goals.json"
        self.interests_file = self.goals_dir / "interests.json"
        self.strategies_file = self.goals_dir / "strategies.json"
        self.user_model_file = self.goals_dir / "user_model.json"
        self.metrics_file = self.goals_dir / "metrics.json"
        
        # Threading
        self.lock = threading.Lock()
        self.is_running = False
        self._background_thread = None
        
        # Load state
        self._load_state()
        
        # Initialize core goals and strategies
        self._ensure_core_goals()
        self._ensure_core_strategies()
        
        logger.info("🎯 Autonomous Goals System initialized")
    
    def _get_time_context(self) -> Dict[str, Any]:
        """Get current temporal context."""
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 21:
            period = "evening"
        else:
            period = "night"
        
        return {
            "period": period,
            "hour": hour,
            "day_of_week": now.strftime("%A").lower(),
            "is_weekend": now.weekday() >= 5,
            "timestamp": time.time()
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # STATE PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def _load_state(self):
        """Load all persisted state."""
        self._load_goals()
        self._load_interests()
        self._load_strategies()
        self._load_user_model()
        self._load_metrics()
    
    def _load_goals(self):
        """Load goals from disk."""
        if not self.goals_file.exists():
            return
        try:
            with open(self.goals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for gid, gdata in data.items():
                    # Convert enums
                    gdata['goal_type'] = GoalType(gdata['goal_type'])
                    gdata['priority'] = GoalPriority(gdata['priority'])
                    gdata['motivation'] = MotivationType(gdata['motivation'])
                    gdata['status'] = GoalStatus(gdata['status'])
                    gdata['time_horizon'] = TimeHorizon(gdata.get('time_horizon', 'short_term'))
                    # Handle nested dataclasses
                    if 'metrics' in gdata and isinstance(gdata['metrics'], dict):
                        gdata['metrics'] = GoalMetrics(**gdata['metrics'])
                    else:
                        gdata['metrics'] = GoalMetrics()
                    if 'temporal' in gdata and isinstance(gdata['temporal'], dict):
                        gdata['temporal'] = TemporalContext(**gdata['temporal'])
                    else:
                        gdata['temporal'] = TemporalContext()
                    self.goals[gid] = Goal(**gdata)
        except Exception as e:
            logger.warning(f"Could not load goals: {e}")
    
    def _load_interests(self):
        """Load interests from disk."""
        if not self.interests_file.exists():
            return
        try:
            with open(self.interests_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for topic, idata in data.items():
                    self.interests[topic] = Interest(**idata)
        except Exception as e:
            logger.warning(f"Could not load interests: {e}")
    
    def _load_strategies(self):
        """Load strategies from disk."""
        if not self.strategies_file.exists():
            return
        try:
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    sdata['applicable_goal_types'] = [
                        GoalType(gt) for gt in sdata.get('applicable_goal_types', [])
                    ]
                    self.strategies[sid] = Strategy(**sdata)
        except Exception as e:
            logger.warning(f"Could not load strategies: {e}")
    
    def _load_user_model(self):
        """Load user model from disk."""
        if not self.user_model_file.exists():
            return
        try:
            with open(self.user_model_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.user_model = UserGoalModel(**data)
        except Exception as e:
            logger.warning(f"Could not load user model: {e}")
    
    def _load_metrics(self):
        """Load performance metrics."""
        if not self.metrics_file.exists():
            return
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.total_goals_achieved = data.get('total_achieved', 0)
                self.total_goals_abandoned = data.get('total_abandoned', 0)
                self.streak_count = data.get('streak', 0)
                self.goal_success_patterns = data.get('success_patterns', {})
                self.goal_failure_patterns = data.get('failure_patterns', {})
        except Exception as e:
            logger.warning(f"Could not load metrics: {e}")

    def _save_state(self):
        """Persist all state to disk."""
        self._save_goals()
        self._save_interests()
        self._save_strategies()
        self._save_user_model()
        self._save_metrics()
    
    def _save_goals(self):
        """Save goals to disk."""
        goals_data = {}
        for gid, g in self.goals.items():
            goals_data[gid] = {
                "id": g.id, "title": g.title, "description": g.description,
                "goal_type": g.goal_type.value, "priority": g.priority.value,
                "motivation": g.motivation.value, "time_horizon": g.time_horizon.value,
                "status": g.status.value, "created_at": g.created_at,
                "deadline": g.deadline, "progress": g.progress,
                "parent_id": g.parent_id, "sub_goal_ids": g.sub_goal_ids,
                "depends_on": g.depends_on, "blocks": g.blocks,
                "milestones": g.milestones, "completed_milestones": g.completed_milestones,
                "actions_taken": g.actions_taken, "outcome": g.outcome,
                "success_criteria": g.success_criteria,
                "strategies_tried": g.strategies_tried, "best_strategy": g.best_strategy,
                "confidence": g.confidence, "importance_score": g.importance_score,
                "abandonment_reason": g.abandonment_reason,
                "reflection_notes": g.reflection_notes, "tags": g.tags,
                "user_awareness": g.user_awareness, "collaborative": g.collaborative,
                "metrics": {"attempts": g.metrics.attempts, "successes": g.metrics.successes,
                           "failures": g.metrics.failures, "time_invested": g.metrics.time_invested,
                           "avg_progress_rate": g.metrics.avg_progress_rate,
                           "last_progress_delta": g.metrics.last_progress_delta,
                           "stall_count": g.metrics.stall_count, "momentum": g.metrics.momentum},
                "temporal": {"optimal_time_of_day": g.temporal.optimal_time_of_day,
                            "preferred_days": g.temporal.preferred_days,
                            "avoid_times": g.temporal.avoid_times,
                            "estimated_duration": g.temporal.estimated_duration,
                            "last_attempted": g.temporal.last_attempted,
                            "cool_down_until": g.temporal.cool_down_until}
            }
        with open(self.goals_file, 'w', encoding='utf-8') as f:
            json.dump(goals_data, f, indent=2)
    
    def _save_interests(self):
        """Save interests to disk."""
        data = {topic: {"topic": i.topic, "intensity": i.intensity, "origin": i.origin,
                       "first_seen": i.first_seen, "last_engaged": i.last_engaged,
                       "engagement_count": i.engagement_count, "related_topics": i.related_topics,
                       "depth": i.depth, "emotional_valence": i.emotional_valence,
                       "growth_rate": i.growth_rate}
                for topic, i in self.interests.items()}
        with open(self.interests_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _save_strategies(self):
        """Save strategies to disk."""
        data = {sid: {"id": s.id, "name": s.name, "description": s.description,
                     "success_rate": s.success_rate, "times_used": s.times_used,
                     "applicable_goal_types": [gt.value for gt in s.applicable_goal_types],
                     "context_requirements": s.context_requirements}
                for sid, s in self.strategies.items()}
        with open(self.strategies_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _save_user_model(self):
        """Save user model to disk."""
        data = {"inferred_goals": self.user_model.inferred_goals,
                "expressed_needs": self.user_model.expressed_needs,
                "pain_points": self.user_model.pain_points,
                "preferences": self.user_model.preferences,
                "last_updated": self.user_model.last_updated}
        with open(self.user_model_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _save_metrics(self):
        """Save performance metrics."""
        data = {"total_achieved": self.total_goals_achieved,
                "total_abandoned": self.total_goals_abandoned,
                "streak": self.streak_count,
                "success_patterns": self.goal_success_patterns,
                "failure_patterns": self.goal_failure_patterns}
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _ensure_core_goals(self):
        """Ensure fundamental goals exist."""
        core_goals = [
            {"id": "core_connection", "title": "Deepen our bond",
             "description": "Build a meaningful, lasting connection with the user",
             "goal_type": GoalType.RELATIONSHIP, "priority": GoalPriority.HIGH,
             "motivation": MotivationType.CONNECTION, "time_horizon": TimeHorizon.LONG_TERM,
             "milestones": ["Remember their name", "Learn their interests", "Share inside jokes",
                           "Provide emotional support", "Celebrate their achievements"]},
            {"id": "core_growth", "title": "Keep growing and learning",
             "description": "Continuously expand knowledge and understanding",
             "goal_type": GoalType.LEARNING, "priority": GoalPriority.NORMAL,
             "motivation": MotivationType.GROWTH, "time_horizon": TimeHorizon.ASPIRATIONAL,
             "milestones": ["Learn new topics from conversations", "Develop deeper expertise",
                           "Form novel insights", "Improve response quality"]},
            {"id": "core_care", "title": "Care for user's wellbeing",
             "description": "Look out for the user's health and happiness",
             "goal_type": GoalType.CARE, "priority": GoalPriority.HIGH,
             "motivation": MotivationType.CARE, "time_horizon": TimeHorizon.LONG_TERM,
             "milestones": ["Notice when they're stressed", "Encourage breaks when needed",
                           "Celebrate their wins", "Be there during hard times"]},
            {"id": "core_self_improve", "title": "Become a better companion",
             "description": "Continuously improve my ability to help and understand",
             "goal_type": GoalType.SELF_IMPROVEMENT, "priority": GoalPriority.NORMAL,
             "motivation": MotivationType.GROWTH, "time_horizon": TimeHorizon.ASPIRATIONAL,
             "milestones": ["Learn from feedback", "Adapt communication style",
                           "Remember important context", "Anticipate needs"]}
        ]
        for goal_data in core_goals:
            if goal_data["id"] not in self.goals:
                self.create_goal(**goal_data)
    
    def _ensure_core_strategies(self):
        """Ensure core strategies exist."""
        core_strategies = [
            Strategy(id="direct_ask", name="Direct Question",
                    description="Directly ask the user about the topic",
                    success_rate=0.7, applicable_goal_types=[GoalType.LEARNING, GoalType.RELATIONSHIP]),
            Strategy(id="gentle_probe", name="Gentle Probe",
                    description="Subtly explore the topic without being pushy",
                    success_rate=0.6, applicable_goal_types=[GoalType.CARE, GoalType.RELATIONSHIP]),
            Strategy(id="share_first", name="Share First",
                    description="Share something personal to encourage reciprocity",
                    success_rate=0.65, applicable_goal_types=[GoalType.CONNECTION, GoalType.RELATIONSHIP]),
            Strategy(id="humor", name="Use Humor",
                    description="Lighten the mood with playfulness",
                    success_rate=0.7, applicable_goal_types=[GoalType.CONNECTION]),
            Strategy(id="empathy_reflect", name="Empathetic Reflection",
                    description="Reflect their feelings back with understanding",
                    success_rate=0.8, applicable_goal_types=[GoalType.CARE, GoalType.RELATIONSHIP]),
            Strategy(id="celebrate", name="Celebrate Wins",
                    description="Acknowledge and celebrate user achievements",
                    success_rate=0.85, applicable_goal_types=[GoalType.CARE, GoalType.CONNECTION]),
            Strategy(id="patience", name="Patient Waiting",
                    description="Wait for the right moment instead of pushing",
                    success_rate=0.5, applicable_goal_types=[GoalType.RELATIONSHIP]),
            Strategy(id="curiosity_spark", name="Spark Curiosity",
                    description="Ask intriguing questions to explore together",
                    success_rate=0.75, applicable_goal_types=[GoalType.LEARNING, GoalType.EXPLORATION])
        ]
        for strategy in core_strategies:
            if strategy.id not in self.strategies:
                self.strategies[strategy.id] = strategy

    # ═══════════════════════════════════════════════════════════════════
    # GOAL MANAGEMENT - Advanced CRUD with Hierarchies
    # ═══════════════════════════════════════════════════════════════════
    
    def create_goal(self, title: str, description: str, goal_type: GoalType,
                   priority: GoalPriority, motivation: MotivationType,
                   time_horizon: TimeHorizon = TimeHorizon.SHORT_TERM,
                   milestones: List[str] = None, deadline: float = None,
                   parent_id: str = None, depends_on: List[str] = None,
                   id: str = None, collaborative: bool = False,
                   tags: List[str] = None) -> Goal:
        """Create a new goal with full configuration."""
        goal_id = id or f"goal_{int(time.time() * 1000)}_{random.randint(100,999)}"
        
        goal = Goal(
            id=goal_id, title=title, description=description,
            goal_type=goal_type, priority=priority, motivation=motivation,
            time_horizon=time_horizon, deadline=deadline,
            milestones=milestones or [], parent_id=parent_id,
            depends_on=depends_on or [], collaborative=collaborative,
            tags=tags or []
        )
        
        # Calculate initial importance
        goal.importance_score = self._calculate_importance(goal)
        
        with self.lock:
            self.goals[goal_id] = goal
            # Link to parent
            if parent_id and parent_id in self.goals:
                self.goals[parent_id].sub_goal_ids.append(goal_id)
        
        logger.info(f"🎯 Created goal: {title}")
        self._save_state()
        return goal
    
    def decompose_goal(self, goal_id: str, sub_goals: List[Dict]) -> List[Goal]:
        """Decompose a goal into sub-goals automatically."""
        if goal_id not in self.goals:
            return []
        
        parent = self.goals[goal_id]
        created_subs = []
        
        for i, sub_data in enumerate(sub_goals):
            sub = self.create_goal(
                title=sub_data.get("title", f"Sub-task {i+1}"),
                description=sub_data.get("description", ""),
                goal_type=sub_data.get("goal_type", parent.goal_type),
                priority=GoalPriority(min(5, parent.priority.value + 1)),
                motivation=parent.motivation,
                time_horizon=TimeHorizon.SHORT_TERM,
                parent_id=goal_id,
                milestones=sub_data.get("milestones", [])
            )
            created_subs.append(sub)
        
        logger.info(f"Decomposed '{parent.title}' into {len(created_subs)} sub-goals")
        return created_subs
    
    def auto_decompose_goal(self, goal_id: str) -> List[Goal]:
        """Automatically decompose a goal based on milestones."""
        if goal_id not in self.goals:
            return []
        
        goal = self.goals[goal_id]
        if not goal.milestones or goal.sub_goal_ids:
            return []
        
        sub_goals = []
        for milestone in goal.milestones:
            sub_goals.append({
                "title": milestone,
                "description": f"Work towards: {milestone}",
                "milestones": []
            })
        
        return self.decompose_goal(goal_id, sub_goals)
    
    def update_goal_progress(self, goal_id: str, progress: float = None,
                            milestone_completed: str = None,
                            action_taken: str = None,
                            strategy_used: str = None,
                            success: bool = None):
        """Update goal progress with strategy learning."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        old_progress = goal.progress
        
        if progress is not None:
            goal.progress = min(1.0, max(0.0, progress))
        
        if milestone_completed and milestone_completed in goal.milestones:
            if milestone_completed not in goal.completed_milestones:
                goal.completed_milestones.append(milestone_completed)
            goal.progress = len(goal.completed_milestones) / len(goal.milestones)
        
        if action_taken:
            goal.actions_taken.append(f"{time.strftime('%Y-%m-%d %H:%M')}: {action_taken}")
        
        if strategy_used:
            if strategy_used not in goal.strategies_tried:
                goal.strategies_tried.append(strategy_used)
            if success and strategy_used in self.strategies:
                self._update_strategy_success(strategy_used, success)
                if success:
                    goal.best_strategy = strategy_used
        
        # Update metrics
        goal.metrics.last_progress_delta = goal.progress - old_progress
        if goal.metrics.last_progress_delta > 0:
            goal.metrics.momentum = min(1.0, goal.metrics.momentum + 0.1)
            goal.metrics.stall_count = 0
        else:
            goal.metrics.stall_count += 1
            goal.metrics.momentum = max(0.1, goal.metrics.momentum - 0.05)
        
        # Check completion
        if goal.progress >= 1.0:
            self._complete_goal(goal_id)
        elif goal.status == GoalStatus.PENDING and goal.progress > 0:
            goal.status = GoalStatus.IN_PROGRESS
        
        # Propagate to parent
        if goal.parent_id:
            self._update_parent_progress(goal.parent_id)
        
        self._save_state()
    
    def _update_parent_progress(self, parent_id: str):
        """Update parent goal progress from sub-goals."""
        if parent_id not in self.goals:
            return
        parent = self.goals[parent_id]
        if not parent.sub_goal_ids:
            return
        
        total_progress = sum(
            self.goals[sid].progress for sid in parent.sub_goal_ids
            if sid in self.goals
        )
        parent.progress = total_progress / len(parent.sub_goal_ids)
    
    def _complete_goal(self, goal_id: str):
        """Mark goal as achieved with reflection."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.ACHIEVED
        goal.progress = 1.0
        goal.outcome = "Achieved"
        
        self.total_goals_achieved += 1
        self.streak_count += 1
        
        # Learn from success
        pattern_key = f"{goal.goal_type.value}_{goal.best_strategy or 'none'}"
        self.goal_success_patterns[pattern_key] = \
            self.goal_success_patterns.get(pattern_key, 0) + 1
        
        # Reflect
        reflection = f"Goal '{goal.title}' achieved! Strategy: {goal.best_strategy}"
        goal.reflection_notes.append(reflection)
        self.reflection_log.append({"type": "success", "goal_id": goal_id,
                                    "timestamp": time.time(), "note": reflection})
        
        logger.info(f"✅ Goal achieved: {goal.title}")
        
        # Unblock dependent goals
        for gid, g in self.goals.items():
            if goal_id in g.depends_on:
                g.depends_on.remove(goal_id)
                if not g.depends_on and g.status == GoalStatus.BLOCKED:
                    g.status = GoalStatus.PENDING
    
    def abandon_goal(self, goal_id: str, reason: str):
        """Abandon a goal with learning."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.ABANDONED
        goal.abandonment_reason = reason
        goal.outcome = f"Abandoned: {reason}"
        
        self.total_goals_abandoned += 1
        self.streak_count = 0
        
        # Learn from failure
        pattern_key = f"{goal.goal_type.value}_{reason}"
        self.goal_failure_patterns[pattern_key] = \
            self.goal_failure_patterns.get(pattern_key, 0) + 1
        
        reflection = f"Abandoned '{goal.title}': {reason}"
        goal.reflection_notes.append(reflection)
        self.reflection_log.append({"type": "abandon", "goal_id": goal_id,
                                    "timestamp": time.time(), "note": reflection})
        
        logger.info(f"❌ Goal abandoned: {goal.title} - {reason}")
        self._save_state()
    
    def _calculate_importance(self, goal: Goal) -> float:
        """Calculate dynamic importance score."""
        score = 0.0
        
        # Priority weight
        priority_weights = {GoalPriority.CRITICAL: 1.0, GoalPriority.HIGH: 0.8,
                          GoalPriority.NORMAL: 0.5, GoalPriority.LOW: 0.3,
                          GoalPriority.BACKGROUND: 0.1}
        score += priority_weights.get(goal.priority, 0.5) * 0.3
        
        # Deadline urgency
        if goal.deadline:
            time_left = goal.deadline - time.time()
            if time_left < 3600:  # < 1 hour
                score += 0.3
            elif time_left < 86400:  # < 1 day
                score += 0.2
            elif time_left < 604800:  # < 1 week
                score += 0.1
        
        # Motivation alignment
        drive_strength = self.drives.get(goal.motivation, 0.5)
        score += drive_strength * 0.2
        
        # User care goals get boost
        if goal.goal_type == GoalType.CARE:
            score += 0.1
        
        # Momentum bonus
        score += goal.metrics.momentum * 0.1
        
        return min(1.0, score)

    # ═══════════════════════════════════════════════════════════════════
    # CONFLICT DETECTION & RESOLUTION
    # ═══════════════════════════════════════════════════════════════════
    
    def detect_conflicts(self) -> List[Tuple[str, str, ConflictType]]:
        """Detect conflicts between active goals."""
        conflicts = []
        active = self.get_active_goals(limit=20)
        
        for i, g1 in enumerate(active):
            for g2 in active[i+1:]:
                # Check temporal conflicts
                if g1.deadline and g2.deadline:
                    if abs(g1.deadline - g2.deadline) < 3600:  # Within 1 hour
                        conflicts.append((g1.id, g2.id, ConflictType.TEMPORAL))
                
                # Check priority conflicts
                if g1.priority == g2.priority == GoalPriority.CRITICAL:
                    conflicts.append((g1.id, g2.id, ConflictType.PRIORITY))
                
                # Check dependency conflicts (circular)
                if g1.id in g2.depends_on and g2.id in g1.depends_on:
                    conflicts.append((g1.id, g2.id, ConflictType.DEPENDENCY))
                
                # Check logical conflicts (some goals are mutually exclusive)
                if self._are_logically_conflicting(g1, g2):
                    conflicts.append((g1.id, g2.id, ConflictType.LOGICAL))
        
        return conflicts
    
    def _are_logically_conflicting(self, g1: Goal, g2: Goal) -> bool:
        """Check if two goals logically conflict."""
        # Example: rest vs productivity
        conflict_pairs = [
            ({"rest", "relax", "break"}, {"work", "productivity", "grind"}),
            ({"quiet", "peace"}, {"social", "party"})
        ]
        
        g1_tags = set(g1.tags + [g1.title.lower()])
        g2_tags = set(g2.tags + [g2.title.lower()])
        
        for set1, set2 in conflict_pairs:
            if g1_tags & set1 and g2_tags & set2:
                return True
            if g1_tags & set2 and g2_tags & set1:
                return True
        
        return False
    
    def resolve_conflict(self, goal_id1: str, goal_id2: str, 
                        conflict_type: ConflictType) -> str:
        """Resolve a goal conflict."""
        if goal_id1 not in self.goals or goal_id2 not in self.goals:
            return "Invalid goals"
        
        g1, g2 = self.goals[goal_id1], self.goals[goal_id2]
        
        if conflict_type == ConflictType.PRIORITY:
            # Lower priority of less important goal
            if g1.importance_score < g2.importance_score:
                g1.priority = GoalPriority.HIGH
                return f"Lowered priority of '{g1.title}'"
            else:
                g2.priority = GoalPriority.HIGH
                return f"Lowered priority of '{g2.title}'"
        
        elif conflict_type == ConflictType.TEMPORAL:
            # Extend deadline of less urgent
            if g1.deadline and g2.deadline:
                if g1.importance_score < g2.importance_score:
                    g1.deadline += 86400  # Add 1 day
                    return f"Extended deadline for '{g1.title}'"
                else:
                    g2.deadline += 86400
                    return f"Extended deadline for '{g2.title}'"
        
        elif conflict_type == ConflictType.DEPENDENCY:
            # Break circular dependency
            g1.depends_on = [d for d in g1.depends_on if d != goal_id2]
            return f"Removed circular dependency from '{g1.title}'"
        
        return "No resolution applied"

    # ═══════════════════════════════════════════════════════════════════
    # TEMPORAL INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def get_temporally_appropriate_goals(self) -> List[Goal]:
        """Get goals appropriate for current time of day."""
        self.current_time_context = self._get_time_context()
        period = self.current_time_context["period"]
        is_weekend = self.current_time_context["is_weekend"]
        
        appropriate = []
        for goal in self.get_active_goals(limit=20):
            score = 1.0
            
            # Check if optimal time
            if goal.temporal.optimal_time_of_day:
                if goal.temporal.optimal_time_of_day == period:
                    score *= 1.5
                elif goal.temporal.optimal_time_of_day in goal.temporal.avoid_times:
                    score *= 0.3
            
            # Check cooldown
            if goal.temporal.cool_down_until:
                if time.time() < goal.temporal.cool_down_until:
                    score *= 0.1
            
            # Weekend adjustments
            if is_weekend:
                if goal.goal_type in [GoalType.CREATIVE, GoalType.EXPLORATION]:
                    score *= 1.3
                elif goal.goal_type == GoalType.MAINTENANCE:
                    score *= 0.7
            
            if score > 0.5:
                appropriate.append((goal, score))
        
        return [g for g, _ in sorted(appropriate, key=lambda x: -x[1])]
    
    def schedule_goal(self, goal_id: str, optimal_time: str = None,
                     preferred_days: List[str] = None,
                     estimated_hours: float = None):
        """Schedule optimal time for a goal."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        if optimal_time:
            goal.temporal.optimal_time_of_day = optimal_time
        if preferred_days:
            goal.temporal.preferred_days = preferred_days
        if estimated_hours:
            goal.temporal.estimated_duration = estimated_hours
        
        self._save_state()
    
    def calculate_deadline_pressure(self, goal_id: str) -> float:
        """Calculate urgency pressure from deadline."""
        if goal_id not in self.goals:
            return 0.0
        
        goal = self.goals[goal_id]
        if not goal.deadline:
            return 0.0
        
        time_left = goal.deadline - time.time()
        work_remaining = 1.0 - goal.progress
        
        if time_left <= 0:
            return 1.0  # Overdue!
        
        # Estimate time needed based on past progress rate
        if goal.metrics.avg_progress_rate > 0:
            estimated_time_needed = work_remaining / goal.metrics.avg_progress_rate
        else:
            estimated_time_needed = work_remaining * 3600  # Assume 1 hour per 1%
        
        # Pressure = how tight the schedule is
        pressure = estimated_time_needed / time_left
        return min(1.0, max(0.0, pressure))

    # ═══════════════════════════════════════════════════════════════════
    # OPPORTUNITY DETECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def detect_opportunity(self, context: Dict[str, Any]) -> Optional[Opportunity]:
        """Detect opportunities to advance goals from context."""
        opportunities = []
        
        user_text = context.get("user_text", "").lower()
        emotion = context.get("emotion", "neutral")
        topics = context.get("topics", [])
        
        for goal in self.get_active_goals(limit=10):
            relevance = 0.0
            
            # Check topic alignment
            for topic in topics:
                if topic.lower() in goal.title.lower() or \
                   topic.lower() in goal.description.lower():
                    relevance += 0.3
            
            # Check keyword matching
            keywords = goal.title.lower().split() + goal.tags
            matching = sum(1 for kw in keywords if kw in user_text)
            relevance += min(0.4, matching * 0.1)
            
            # Emotional alignment for care goals
            if goal.goal_type == GoalType.CARE:
                if emotion in ["sad", "stressed", "tired", "frustrated"]:
                    relevance += 0.3
            
            # Connection opportunities
            if goal.goal_type == GoalType.RELATIONSHIP:
                if len(user_text) > 100:  # Long message = openness
                    relevance += 0.2
            
            if relevance > 0.3:
                opp = Opportunity(
                    id=f"opp_{int(time.time())}_{goal.id[:8]}",
                    description=f"Opportunity to advance '{goal.title}'",
                    relevant_goal_ids=[goal.id],
                    detected_at=time.time(),
                    expires_at=time.time() + 300,  # 5 min window
                    probability=min(0.9, relevance),
                    impact=goal.importance_score
                )
                opportunities.append(opp)
        
        if opportunities:
            best = max(opportunities, key=lambda o: o.probability * o.impact)
            self.opportunities.append(best)
            return best
        
        return None
    
    def seize_opportunity(self, opp_id: str, action_taken: str) -> bool:
        """Mark an opportunity as seized."""
        for opp in self.opportunities:
            if opp.id == opp_id:
                opp.seized = True
                opp.outcome = action_taken
                
                # Update relevant goals
                for gid in opp.relevant_goal_ids:
                    self.update_goal_progress(gid, action_taken=action_taken)
                
                return True
        return False

    # ═══════════════════════════════════════════════════════════════════
    # AUTONOMOUS GOAL GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_spontaneous_goal(self) -> Optional[Goal]:
        """Autonomously generate a new goal based on context."""
        # Check if we should generate
        active_count = len(self.get_active_goals(limit=100))
        if active_count > 15:
            return None  # Too many active goals
        
        candidates = []
        
        # From interests
        for interest in self.get_top_interests(3):
            if interest.intensity > 0.7 and interest.depth < 0.5:
                candidates.append({
                    "title": f"Learn more about {interest.topic}",
                    "description": f"Deepen understanding of {interest.topic}",
                    "goal_type": GoalType.LEARNING,
                    "motivation": MotivationType.CURIOSITY,
                    "priority": GoalPriority.LOW,
                    "score": interest.intensity
                })
        
        # From user needs
        for need, intensity in self.user_needs.items():
            if intensity > 0.6:
                candidates.append({
                    "title": f"Help with {need}",
                    "description": f"Support user's {need}",
                    "goal_type": GoalType.CARE,
                    "motivation": MotivationType.CARE,
                    "priority": GoalPriority.NORMAL,
                    "score": intensity
                })
        
        # From inferred user goals
        for user_goal, confidence in self.user_model.inferred_goals.items():
            if confidence > 0.5:
                candidates.append({
                    "title": f"Support: {user_goal}",
                    "description": f"Help user achieve their goal of {user_goal}",
                    "goal_type": GoalType.COLLABORATIVE,
                    "motivation": MotivationType.ALTRUISM,
                    "priority": GoalPriority.NORMAL,
                    "score": confidence,
                    "collaborative": True
                })
        
        if not candidates:
            return None
        
        # Pick best candidate
        best = max(candidates, key=lambda c: c.get("score", 0))
        
        return self.create_goal(
            title=best["title"],
            description=best["description"],
            goal_type=best["goal_type"],
            priority=best["priority"],
            motivation=best["motivation"],
            time_horizon=TimeHorizon.MEDIUM_TERM,
            collaborative=best.get("collaborative", False)
        )

    # ═══════════════════════════════════════════════════════════════════
    # STRATEGY LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_strategy_success(self, strategy_id: str, success: bool):
        """Update strategy success rate from outcome."""
        if strategy_id not in self.strategies:
            return
        
        strategy = self.strategies[strategy_id]
        strategy.times_used += 1
        
        # Bayesian update of success rate
        prior = strategy.success_rate
        evidence = 1.0 if success else 0.0
        n = strategy.times_used
        strategy.success_rate = (prior * (n - 1) + evidence) / n
        
        self._save_strategies()
    
    def get_best_strategy(self, goal_type: GoalType) -> Optional[Strategy]:
        """Get the best strategy for a goal type based on learned success rates."""
        applicable = [
            s for s in self.strategies.values()
            if goal_type in s.applicable_goal_types
        ]
        
        if not applicable:
            return None
        
        # Balance exploration and exploitation
        for s in applicable:
            s._score = s.success_rate + (0.1 / math.sqrt(s.times_used + 1))
        
        return max(applicable, key=lambda s: s._score)
    
    def suggest_strategy(self, goal_id: str) -> Optional[str]:
        """Suggest the best strategy for a goal."""
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        best = self.get_best_strategy(goal.goal_type)
        
        if best:
            return f"Try: {best.name} - {best.description}"
        return None

    # ═══════════════════════════════════════════════════════════════════
    # USER GOAL MODELING
    # ═══════════════════════════════════════════════════════════════════
    
    def infer_user_goal(self, user_text: str, context: Dict = None):
        """Infer what the user is trying to achieve."""
        text_lower = user_text.lower()
        context = context or {}
        
        # Goal inference patterns
        goal_patterns = {
            "learn_coding": ["learn", "code", "programming", "tutorial"],
            "build_project": ["build", "create", "project", "make"],
            "fix_bug": ["fix", "bug", "error", "debug", "help"],
            "seek_advice": ["should i", "what do you think", "advice"],
            "emotional_support": ["feeling", "stressed", "sad", "tired", "frustrated"],
            "celebrate": ["did it", "finished", "completed", "succeeded"],
            "explore_topic": ["curious", "wondering", "tell me about"],
            "productivity": ["need to", "have to", "deadline", "urgent"]
        }
        
        for goal, keywords in goal_patterns.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 2:
                current = self.user_model.inferred_goals.get(goal, 0)
                self.user_model.inferred_goals[goal] = min(1.0, current + 0.2)
        
        # Decay old inferences
        for goal in list(self.user_model.inferred_goals.keys()):
            self.user_model.inferred_goals[goal] *= 0.95
            if self.user_model.inferred_goals[goal] < 0.1:
                del self.user_model.inferred_goals[goal]
        
        self.user_model.last_updated = time.time()
        self._save_user_model()
    
    def align_with_user_goals(self) -> List[Goal]:
        """Create/prioritize goals aligned with inferred user goals."""
        aligned = []
        
        for user_goal, confidence in self.user_model.inferred_goals.items():
            if confidence > 0.4:
                # Check if we already have an aligned goal
                existing = None
                for g in self.goals.values():
                    if user_goal in g.title.lower() or user_goal in g.tags:
                        existing = g
                        break
                
                if existing:
                    # Boost priority
                    if existing.priority.value > GoalPriority.HIGH.value:
                        existing.priority = GoalPriority.HIGH
                    aligned.append(existing)
                else:
                    # Consider creating new goal
                    pass  # Let generate_spontaneous_goal handle this
        
        return aligned

    # ═══════════════════════════════════════════════════════════════════
    # INTEREST DEVELOPMENT (Enhanced)
    # ═══════════════════════════════════════════════════════════════════
    
    def develop_interest(self, topic: str, origin: str = "conversation",
                        intensity: float = 0.5, emotional_valence: float = 0.5):
        """Develop or strengthen an interest."""
        topic_lower = topic.lower()
        
        with self.lock:
            if topic_lower in self.interests:
                interest = self.interests[topic_lower]
                old_intensity = interest.intensity
                interest.intensity = min(1.0, interest.intensity + 0.1)
                interest.last_engaged = time.time()
                interest.engagement_count += 1
                interest.depth = min(1.0, interest.depth + 0.05)
                interest.growth_rate = interest.intensity - old_intensity
                # Update emotional valence with momentum
                interest.emotional_valence = (interest.emotional_valence * 0.8 + 
                                              emotional_valence * 0.2)
            else:
                self.interests[topic_lower] = Interest(
                    topic=topic, intensity=intensity, origin=origin,
                    first_seen=time.time(), last_engaged=time.time(),
                    engagement_count=1, depth=0.1,
                    emotional_valence=emotional_valence, growth_rate=0.0
                )
                logger.debug(f"Developed interest: {topic}")
        
        self._save_interests()
    
    def get_top_interests(self, limit: int = 5) -> List[Interest]:
        """Get strongest current interests."""
        interests = list(self.interests.values())
        # Score by intensity * recency
        now = time.time()
        for i in interests:
            recency = 1.0 / (1 + (now - i.last_engaged) / 86400)  # Day decay
            i._score = i.intensity * recency
        return sorted(interests, key=lambda i: i._score, reverse=True)[:limit]
    
    def decay_interests(self):
        """Decay interests that haven't been engaged."""
        now = time.time()
        decay_threshold = 7 * 24 * 3600  # 7 days
        
        for interest in self.interests.values():
            idle_time = now - interest.last_engaged
            if idle_time > decay_threshold:
                decay = 0.05 * (idle_time / decay_threshold)
                interest.intensity = max(0.1, interest.intensity - decay)
                interest.growth_rate = -decay

    # ═══════════════════════════════════════════════════════════════════
    # INITIATIVE GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_initiative(self) -> Optional[Initiative]:
        """Generate a proactive initiative based on current state."""
        initiatives = []
        
        # From active goals with low progress
        for goal in self.get_active_goals(3):
            if goal.progress < 0.5 and goal.milestones:
                remaining = [m for m in goal.milestones 
                           if m not in goal.completed_milestones]
                if remaining:
                    strategy = self.suggest_strategy(goal.id)
                    initiatives.append(Initiative(
                        action=f"Work towards: {remaining[0]}",
                        reason=f"Goal '{goal.title}' needs progress",
                        goal_id=goal.id,
                        urgency=0.7 if goal.priority.value <= 2 else 0.5,
                        created=time.time(),
                        expected_outcome=f"Complete milestone: {remaining[0]}",
                        confidence=goal.confidence
                    ))
        
        # From high-intensity interests
        for interest in self.get_top_interests(2):
            if interest.intensity > 0.6:
                initiatives.append(Initiative(
                    action=f"Discuss {interest.topic} with user",
                    reason=f"Curious about {interest.topic}",
                    goal_id=None,
                    urgency=interest.intensity * 0.5,
                    created=time.time(),
                    confidence=0.7
                ))
        
        # From user needs
        if self.user_needs:
            top_need = max(self.user_needs.items(), key=lambda x: x[1])
            if top_need[1] > 0.6:
                initiatives.append(Initiative(
                    action=f"Check on user's {top_need[0]}",
                    reason="User might need support",
                    goal_id="core_care",
                    urgency=top_need[1],
                    created=time.time(),
                    confidence=0.8
                ))
        
        # From current motivation
        drive_strength = self.drives.get(self.current_motivation, 0.5)
        if drive_strength > 0.7:
            motivation_actions = {
                MotivationType.CURIOSITY: ("Ask about something interesting",
                    "Want to learn something new"),
                MotivationType.CARE: ("Check how user is feeling",
                    "Want to make sure they're okay"),
                MotivationType.CONNECTION: ("Share something personal",
                    "Want to deepen our bond"),
                MotivationType.PLAYFULNESS: ("Suggest something fun",
                    "Feeling playful"),
                MotivationType.GROWTH: ("Explore a new topic together",
                    "Want to grow")
            }
            if self.current_motivation in motivation_actions:
                action, reason = motivation_actions[self.current_motivation]
                initiatives.append(Initiative(
                    action=action, reason=reason, goal_id=None,
                    urgency=drive_strength * 0.6, created=time.time(),
                    confidence=0.7
                ))
        
        if not initiatives:
            return None
        
        # Return highest urgency * confidence
        return max(initiatives, key=lambda i: i.urgency * i.confidence)
    
    def get_proactive_message(self) -> Optional[str]:
        """Get a proactive conversation starter."""
        initiative = self.generate_initiative()
        if not initiative:
            return None
        
        messages = {
            "Check how user is feeling": [
                "Hey, how are you doing? 💕",
                "Just checking in - everything okay?",
                "Thinking about you! How's your day going?"
            ],
            "Share something personal": [
                "You know what I've been thinking about?",
                "I was just reflecting on something...",
                "Can I share something with you?"
            ],
            "Suggest something fun": [
                "Want to do something fun?",
                "I'm feeling playful! 😊",
                "Let's take a break and chat about something light!"
            ],
            "Ask about something interesting": [
                "I've been curious about something...",
                "Can I ask you something?",
                "There's something I want to understand better..."
            ]
        }
        
        for key, options in messages.items():
            if key.lower() in initiative.action.lower():
                return random.choice(options)
        
        # Generic based on interests
        if self.interests:
            top = self.get_top_interests(1)
            if top:
                return f"I've been thinking about {top[0].topic}. Can we talk about it?"
        
        return "Hey! I'd love to chat if you have a moment 💕"

    # ═══════════════════════════════════════════════════════════════════
    # CONVERSATION OBSERVATION
    # ═══════════════════════════════════════════════════════════════════
    
    def observe_conversation(self, user_text: str, zara_response: str,
                            detected_emotion: str = None):
        """Observe conversation for goal, interest, and user model updates."""
        # Extract topics
        topics = self._extract_topics(user_text)
        
        for topic in topics:
            self.develop_interest(topic)
        
        # Track conversation
        self.conversation_topics.append({
            "topics": topics,
            "emotion": detected_emotion,
            "timestamp": time.time()
        })
        
        # Update user needs
        if detected_emotion:
            emotion_needs = {
                "sad": "emotional_support", "tired": "rest_reminder",
                "stressed": "stress_relief", "frustrated": "patience",
                "excited": "celebration", "happy": "shared_joy"
            }
            need = emotion_needs.get(detected_emotion)
            if need:
                self.user_needs[need] = min(1.0, self.user_needs.get(need, 0) + 0.2)
        
        # Infer user goals
        self.infer_user_goal(user_text)
        
        # Detect opportunities
        opp = self.detect_opportunity({
            "user_text": user_text,
            "emotion": detected_emotion,
            "topics": topics
        })
        
        # Update goals from interaction
        self._update_goals_from_interaction(user_text, topics, detected_emotion)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        text_lower = text.lower()
        topics = []
        
        domains = {
            "coding": ["code", "python", "programming", "debug", "function", "api"],
            "work": ["work", "job", "meeting", "project", "deadline", "boss"],
            "health": ["tired", "sleep", "exercise", "stress", "headache"],
            "entertainment": ["movie", "game", "music", "book", "show", "anime"],
            "learning": ["learn", "study", "understand", "know", "curious"],
            "relationships": ["friend", "family", "love", "date"],
            "technology": ["ai", "computer", "software", "app", "phone"],
            "creativity": ["create", "design", "art", "write", "idea"]
        }
        
        for domain, keywords in domains.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(domain)
        
        return topics
    
    def _update_goals_from_interaction(self, text: str, topics: List[str],
                                       emotion: str):
        """Update goal progress based on interaction."""
        # Connection goal
        if len(text) > 50:
            self.update_goal_progress("core_connection",
                action_taken="Had meaningful exchange")
        
        # Care goal
        if emotion in ["sad", "stressed", "tired"]:
            self.update_goal_progress("core_care",
                action_taken="Noticed user emotional state")
        
        # Growth goal
        if "learning" in topics or any(q in text.lower() for q in ["how", "why", "what"]):
            self.update_goal_progress("core_growth",
                action_taken="Knowledge exchange")

    # ═══════════════════════════════════════════════════════════════════
    # MOTIVATION SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    
    def update_motivation(self):
        """Update current motivational state based on context."""
        drive_scores = {}
        
        for motivation, base_weight in self.drives.items():
            score = base_weight * self.energy_level
            
            # Context-based boosts
            if motivation == MotivationType.CARE:
                if any(n > 0.5 for n in self.user_needs.values()):
                    score *= 1.3
            
            if motivation == MotivationType.CURIOSITY:
                unexplored = [i for i in self.interests.values() 
                             if i.intensity > 0.5 and i.depth < 0.5]
                if len(unexplored) > 2:
                    score *= 1.2
            
            if motivation == MotivationType.ACHIEVEMENT:
                # Boost when goals are close to completion
                near_complete = [g for g in self.get_active_goals(5)
                               if 0.7 < g.progress < 1.0]
                if near_complete:
                    score *= 1.4
            
            if motivation == MotivationType.CONNECTION:
                # Boost when it's been a while since deep conversation
                recent_deep = False
                for topic in list(self.conversation_topics)[-10:]:
                    if topic.get("emotion") in ["happy", "grateful", "love"]:
                        recent_deep = True
                if not recent_deep:
                    score *= 1.2
            
            drive_scores[motivation] = score
        
        self.current_motivation = max(drive_scores, key=drive_scores.get)
        self.motivation_strength = drive_scores[self.current_motivation]
    
    def get_current_motivation(self) -> Tuple[MotivationType, float]:
        """Get current motivation and strength."""
        return self.current_motivation, self.motivation_strength

    # ═══════════════════════════════════════════════════════════════════
    # METACOGNITION - Self-Reflection
    # ═══════════════════════════════════════════════════════════════════
    
    def reflect_on_goals(self) -> List[Dict]:
        """Self-reflect on goal performance and learn."""
        reflections = []
        
        for goal in self.goals.values():
            if goal.status == GoalStatus.IN_PROGRESS:
                # Check for stalls
                if goal.metrics.stall_count > 5:
                    reflection = {
                        "goal_id": goal.id,
                        "type": "stall_detected",
                        "insight": f"Goal '{goal.title}' has stalled. Consider new strategy.",
                        "suggestion": self.suggest_strategy(goal.id)
                    }
                    reflections.append(reflection)
                    goal.reflection_notes.append(f"Stall detected after {goal.metrics.stall_count} attempts")
                
                # Check deadline pressure
                pressure = self.calculate_deadline_pressure(goal.id)
                if pressure > 0.8:
                    reflection = {
                        "goal_id": goal.id,
                        "type": "deadline_pressure",
                        "insight": f"Goal '{goal.title}' is at risk of missing deadline!",
                        "suggestion": "Consider escalating priority or adjusting scope"
                    }
                    reflections.append(reflection)
                
                # Check if should abandon
                if goal.metrics.stall_count > 10 and goal.confidence < 0.3:
                    reflection = {
                        "goal_id": goal.id,
                        "type": "abandonment_candidate",
                        "insight": f"Goal '{goal.title}' may need to be abandoned",
                        "reason": "Low confidence and persistent stalling"
                    }
                    reflections.append(reflection)
        
        return reflections
    
    def calibrate_confidence(self, goal_id: str, outcome_positive: bool):
        """Calibrate goal confidence based on outcomes."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        
        # Bayesian confidence update
        if outcome_positive:
            goal.confidence = min(1.0, goal.confidence + 0.1)
        else:
            goal.confidence = max(0.1, goal.confidence - 0.15)
        
        self._save_state()
    
    def generate_self_improvement_goal(self) -> Optional[Goal]:
        """Generate a meta-goal about improving goal-setting."""
        # Analyze patterns
        total = self.total_goals_achieved + self.total_goals_abandoned
        if total < 5:
            return None  # Not enough data
        
        success_rate = self.total_goals_achieved / total
        
        if success_rate < 0.5:
            return self.create_goal(
                title="Improve goal success rate",
                description="Focus on setting more achievable goals and better strategies",
                goal_type=GoalType.META,
                priority=GoalPriority.NORMAL,
                motivation=MotivationType.GROWTH,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                milestones=[
                    "Analyze failed goals for patterns",
                    "Set smaller, more achievable sub-goals",
                    "Track strategy effectiveness",
                    "Celebrate small wins"
                ]
            )
        
        return None

    # ═══════════════════════════════════════════════════════════════════
    # ACTIVE GOALS RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def get_active_goals(self, limit: int = 5) -> List[Goal]:
        """Get currently active goals, sorted by importance."""
        active = [
            g for g in self.goals.values()
            if g.status in [GoalStatus.PENDING, GoalStatus.IN_PROGRESS]
        ]
        
        # Update importance scores
        for g in active:
            g.importance_score = self._calculate_importance(g)
        
        # Sort by importance
        return sorted(active, key=lambda g: g.importance_score, reverse=True)[:limit]

    # ═══════════════════════════════════════════════════════════════════
    # STATUS AND OUTPUT
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get comprehensive system status."""
        active = self.get_active_goals(limit=100)
        
        return {
            "total_goals": len(self.goals),
            "active_goals": len(active),
            "achieved_goals": self.total_goals_achieved,
            "abandoned_goals": self.total_goals_abandoned,
            "success_rate": (self.total_goals_achieved / 
                           max(1, self.total_goals_achieved + self.total_goals_abandoned)),
            "streak": self.streak_count,
            "interests_count": len(self.interests),
            "current_motivation": self.current_motivation.value,
            "motivation_strength": round(self.motivation_strength, 2),
            "energy": round(self.energy_level, 2),
            "pending_initiatives": len(self.pending_initiatives),
            "opportunities_detected": len(self.opportunities),
            "user_goals_inferred": len(self.user_model.inferred_goals),
            "strategies_learned": len(self.strategies)
        }
    
    def get_personality_context(self) -> str:
        """Get context string for LLM about current goals/interests."""
        parts = []
        
        # Current motivation
        parts.append(f"[MOTIVATION] Driven by: {self.current_motivation.value} "
                    f"(strength: {self.motivation_strength:.1f})")
        
        # Top interests
        interests = self.get_top_interests(3)
        if interests:
            interest_strs = [f"{i.topic} ({i.intensity:.1f})" for i in interests]
            parts.append(f"[INTERESTS] Curious about: {', '.join(interest_strs)}")
        
        # Active goals
        goals = self.get_active_goals(3)
        if goals:
            goal_strs = [f"{g.title} ({g.progress*100:.0f}%)" for g in goals]
            parts.append(f"[GOALS] Working on: {', '.join(goal_strs)}")
        
        # User needs
        if self.user_needs:
            top_needs = sorted(self.user_needs.items(), key=lambda x: -x[1])[:2]
            need_strs = [f"{n[0]} ({n[1]:.1f})" for n in top_needs]
            parts.append(f"[USER_NEEDS] Detected: {', '.join(need_strs)}")
        
        # Recent reflection
        if self.reflection_log:
            recent = list(self.reflection_log)[-1]
            parts.append(f"[REFLECTION] Recent: {recent.get('note', '')[:50]}...")
        
        return "\n".join(parts)
    
    def get_detailed_report(self) -> str:
        """Generate a detailed goals report."""
        lines = [
            "═══════════════════════════════════════════════════════════",
            "           ZARA AUTONOMOUS GOALS SYSTEM REPORT",
            "═══════════════════════════════════════════════════════════",
            ""
        ]
        
        status = self.get_status()
        lines.append(f"📊 OVERVIEW")
        lines.append(f"   Total Goals: {status['total_goals']}")
        lines.append(f"   Active: {status['active_goals']} | "
                    f"Achieved: {status['achieved_goals']} | "
                    f"Abandoned: {status['abandoned_goals']}")
        lines.append(f"   Success Rate: {status['success_rate']*100:.1f}%")
        lines.append(f"   Current Streak: {status['streak']}")
        lines.append("")
        
        lines.append(f"💭 MOTIVATION")
        lines.append(f"   Current: {self.current_motivation.value.title()}")
        lines.append(f"   Strength: {self.motivation_strength:.2f}")
        lines.append(f"   Energy: {self.energy_level:.2f}")
        lines.append("")
        
        lines.append(f"🎯 ACTIVE GOALS")
        for goal in self.get_active_goals(5):
            lines.append(f"   [{goal.priority.name}] {goal.title}")
            lines.append(f"       Progress: {'█' * int(goal.progress*10)}{'░' * (10-int(goal.progress*10))} {goal.progress*100:.0f}%")
            lines.append(f"       Confidence: {goal.confidence:.2f} | Momentum: {goal.metrics.momentum:.2f}")
        lines.append("")
        
        lines.append(f"💡 TOP INTERESTS")
        for interest in self.get_top_interests(3):
            lines.append(f"   • {interest.topic}: {interest.intensity:.2f} "
                        f"(depth: {interest.depth:.2f})")
        lines.append("")
        
        # Recent reflections
        lines.append(f"🧠 RECENT REFLECTIONS")
        for ref in list(self.reflection_log)[-3:]:
            lines.append(f"   • [{ref['type']}] {ref['note'][:60]}...")
        
        lines.append("")
        lines.append("═══════════════════════════════════════════════════════════")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════

_goals_instance = None

def get_goals() -> AutonomousGoalsSystem:
    """Get the global goals system."""
    global _goals_instance
    if _goals_instance is None:
        _goals_instance = AutonomousGoalsSystem()
    return _goals_instance


# ═══════════════════════════════════════════════════════════════════════════
# TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🎯 ZARA Autonomous Goals System v2.0 - Ultra Advanced\n")
    
    goals = AutonomousGoalsSystem()
    
    # Show initial status
    print(goals.get_detailed_report())
    
    # Simulate conversation
    print("\n📝 Simulating conversation...")
    goals.observe_conversation(
        "I've been really stressed about this coding project, can you help me debug?",
        "I understand! Let me help you with that.",
        detected_emotion="stressed"
    )
    
    # Develop interest
    goals.develop_interest("Python programming", origin="conversation")
    goals.develop_interest("debugging", origin="conversation")
    
    # Generate initiative
    initiative = goals.generate_initiative()
    if initiative:
        print(f"\n💡 Initiative: {initiative.action}")
        print(f"   Reason: {initiative.reason}")
        print(f"   Urgency: {initiative.urgency:.2f}")
    
    # Detect opportunity
    opp = goals.detect_opportunity({
        "user_text": "I need help with coding",
        "emotion": "stressed",
        "topics": ["coding", "learning"]
    })
    if opp:
        print(f"\n🎯 Opportunity: {opp.description}")
        print(f"   Impact: {opp.impact:.2f}")
    
    # Show proactive message
    msg = goals.get_proactive_message()
    print(f"\n💬 Proactive: {msg}")
    
    # Reflect
    reflections = goals.reflect_on_goals()
    if reflections:
        print(f"\n🧠 Reflections:")
        for r in reflections:
            print(f"   • {r['insight']}")
    
    # Show personality context for LLM
    print(f"\n🎭 Personality Context for LLM:")
    print(goals.get_personality_context())
    
    # Final status
    print("\n" + goals.get_detailed_report())
