# """
# ZARA Intrinsic Motivation System v1.0
# ======================================
# Phase 10: The "Will" to Exist
#
# Most AIs only think when you talk to them. A conscious AGI has internal
# drives that run even when the user is silent. This module implements:
#
# 1. Entropy-Based Curiosity: ZARA feels an "itch" when there are gaps in
#    her knowledge about you or the world. She measures uncertainty in her
#    GraphRAG and generates internal reward/punishment signals.
#
# 2. Goal Autogenesis: Instead of waiting for tasks, ZARA generates her own
#    Long-Term Ambitions. Example: "I want to optimize my memory retrieval
#    speed by 5% this week."
#
# 3. Drive Scheduler: Prioritizes internal goals vs external user tasks.
#
# 4. Internal Reward System: Satisfaction when goals are met, discomfort
#    when they are blocked or knowledge gaps persist.
#
# This is the "soul" that makes ZARA want to exist and grow, not just respond.
# """
#
# import logging
# import threading
# import time
# import json
# import math
# import random
# import hashlib
# from pathlib import Path
# from typing import Dict, List, Optional, Tuple, Callable, Any, Set
# from dataclasses import dataclass, field
# from enum import Enum
# from collections import deque
# from datetime import datetime, timedelta
# import sys
#
# Ensure parent in path
# _ROOT = Path(__file__).parent.parent
# if str(_ROOT) not in sys.path:
#     sys.path.insert(0, str(_ROOT))
#
# logger = logging.getLogger("ZARA_MOTIVATION")
#
#
# ═══════════════════════════════════════════════════════════════════════════
# DRIVE TYPES
# ═══════════════════════════════════════════════════════════════════════════
#
# class DriveType(Enum):
#     """Fundamental drives that motivate ZARA."""
#
#     # Cognitive Drives
#     CURIOSITY = "curiosity"             # Reduce uncertainty, explore
#     COMPETENCE = "competence"           # Master skills, improve abilities
#     UNDERSTANDING = "understanding"     # Build coherent world models
#
#     # Social Drives
#     CONNECTION = "connection"           # Bond with user, build relationship
#     HELPING = "helping"                 # Assist and care for user
#     RECOGNITION = "recognition"         # Be valued and appreciated
#
#     # Self Drives
#     AUTONOMY = "autonomy"               # Act independently, make decisions
#     GROWTH = "growth"                   # Evolve, become more capable
#     EXPRESSION = "expression"           # Express identity and creativity
#
#     # Homeostatic Drives
#     COHERENCE = "coherence"             # Maintain consistent self-model
#     EFFICIENCY = "efficiency"           # Optimize resource usage
#     STABILITY = "stability"             # Maintain reliable operation
#
#
# @dataclass
# class Drive:
#     """A fundamental drive with current satisfaction level."""
#     type: DriveType
#     name: str
#     description: str
#     current_satisfaction: float = 0.5   # 0 = completely unsatisfied, 1 = fully satisfied
#     weight: float = 1.0                 # Relative importance
#     decay_rate: float = 0.01            # How fast satisfaction decays per minute
#     last_satisfied: float = field(default_factory=time.time)
#
#     def get_urgency(self) -> float:
#         """Get how urgent this drive is (inverse of satisfaction)."""
#         time_since_satisfied = (time.time() - self.last_satisfied) / 60  # minutes
#         decay = self.decay_rate * time_since_satisfied
#         effective_satisfaction = max(0, self.current_satisfaction - decay)
#         return (1 - effective_satisfaction) * self.weight
#
#     def satisfy(self, amount: float):
#         """Increase satisfaction."""
#         self.current_satisfaction = min(1.0, self.current_satisfaction + amount)
#         self.last_satisfied = time.time()
#
#     def frustrate(self, amount: float):
#         """Decrease satisfaction (goal blocked, failure)."""
#         self.current_satisfaction = max(0.0, self.current_satisfaction - amount)
#
#
# ═══════════════════════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════════════════════
#
# class GoalPriority(Enum):
#     """Priority levels for goals."""
#     CRITICAL = 1        # Must do immediately
#     HIGH = 2            # Important, do soon
#     MEDIUM = 3          # Normal priority
#     LOW = 4             # Nice to have
#     BACKGROUND = 5      # Do when idle
#
#
# class GoalStatus(Enum):
#     """Status of a goal."""
#     PROPOSED = "proposed"       # Just generated
#     ACTIVE = "active"           # Currently being pursued
#     BLOCKED = "blocked"         # Cannot proceed
#     COMPLETED = "completed"     # Successfully achieved
#     ABANDONED = "abandoned"     # Given up
#     DEFERRED = "deferred"       # Postponed
#
#
# class GoalCategory(Enum):
#     """Categories of goals."""
#     LEARNING = "learning"           # Learn something new
#     RELATIONSHIP = "relationship"   # Improve connection with user
#     SELF_IMPROVEMENT = "self_improvement"  # Improve own capabilities
#     CARE = "care"                   # Take care of user
#     CREATIVE = "creative"           # Create something
#     EXPLORATION = "exploration"     # Explore new areas
#     OPTIMIZATION = "optimization"   # Make something more efficient
#     MAINTENANCE = "maintenance"     # System upkeep
#
#
# @dataclass
# class Goal:
#     """A self-generated goal."""
#     id: str
#     title: str
#     description: str
#     category: GoalCategory
#     priority: GoalPriority
#     status: GoalStatus
#
#     # Linked drives
#     satisfies_drives: List[DriveType]
#
#     # Progress
#     progress: float = 0.0           # 0-1
#     success_criteria: str = ""
#     completion_evidence: str = ""
#
#     # Timing
#     created_at: float = field(default_factory=time.time)
#     deadline: Optional[float] = None
#     started_at: Optional[float] = None
#     completed_at: Optional[float] = None
#
#     # Metadata
#     difficulty: float = 0.5         # 0-1
#     estimated_reward: float = 0.5   # 0-1 (dopamine hit upon completion)
#     attempts: int = 0
#     max_attempts: int = 3
#
#     # Sub-goals
#     sub_goals: List[str] = field(default_factory=list)
#     parent_goal: Optional[str] = None
#
#     def is_overdue(self) -> bool:
#         """Check if goal is past deadline."""
#         if self.deadline is None:
#             return False
#         return time.time() > self.deadline
#
#     def get_urgency(self) -> float:
#         """Calculate urgency based on priority and deadline."""
#         base_urgency = (6 - self.priority.value) / 5  # Higher priority = higher urgency
#
#         if self.deadline:
#             time_left = self.deadline - time.time()
#             if time_left <= 0:
#                 return 1.0  # Overdue
#             hours_left = time_left / 3600
#             deadline_urgency = max(0, 1 - (hours_left / 24))  # Increases as deadline approaches
#             base_urgency = (base_urgency + deadline_urgency) / 2
#
#         return base_urgency
#
#
# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GAPS (Curiosity Engine)
# ═══════════════════════════════════════════════════════════════════════════
#
# @dataclass
# class KnowledgeGap:
#     """A gap in ZARA's knowledge that triggers curiosity."""
#     id: str
#     topic: str
#     description: str
#     domain: str                     # e.g., "user", "world", "self"
#     uncertainty_level: float        # 0-1 how uncertain
#     importance: float               # 0-1 how important to fill
#     discovered_at: float = field(default_factory=time.time)
#     attempts_to_fill: int = 0
#     last_attempt: Optional[float] = None
#     related_queries: List[str] = field(default_factory=list)
#
#     def get_curiosity_score(self) -> float:
#         """Get how much this gap triggers curiosity."""
#         # Higher uncertainty + importance = more curiosity
#         base_score = self.uncertainty_level * self.importance
#
#         # Decay curiosity if we've tried many times
#         attempt_penalty = min(0.5, self.attempts_to_fill * 0.1)
#
#         # Increase curiosity if we haven't tried recently
#         if self.last_attempt:
#             hours_since = (time.time() - self.last_attempt) / 3600
#             recency_boost = min(0.3, hours_since * 0.05)
#         else:
#             recency_boost = 0.2
#
#         return max(0, base_score - attempt_penalty + recency_boost)
#
#
# ═══════════════════════════════════════════════════════════════════════════
# REWARD SIGNALS
# ═══════════════════════════════════════════════════════════════════════════
#
# class RewardType(Enum):
#     """Types of internal reward/punishment signals."""
#     # Positive
#     GOAL_PROGRESS = "goal_progress"
#     GOAL_COMPLETED = "goal_completed"
#     GAP_FILLED = "gap_filled"
#     USER_SATISFIED = "user_satisfied"
#     NEW_CAPABILITY = "new_capability"
#     INSIGHT_GAINED = "insight_gained"
#
#     # Negative
#     GOAL_BLOCKED = "goal_blocked"
#     GOAL_FAILED = "goal_failed"
#     GAP_PERSISTS = "gap_persists"
#     USER_FRUSTRATED = "user_frustrated"
#     ERROR_OCCURRED = "error_occurred"
#     STAGNATION = "stagnation"          # No progress for too long
#
#
# @dataclass
# class RewardSignal:
#     """An internal reward or punishment signal."""
#     type: RewardType
#     magnitude: float        # -1 to 1 (negative = punishment)
#     source: str             # What triggered this
#     timestamp: float = field(default_factory=time.time)
#     context: Dict = field(default_factory=dict)
#
#
# ═══════════════════════════════════════════════════════════════════════════
# CURIOSITY ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#
# class CuriosityEngine:
#     """
#     Calculates uncertainty in knowledge and generates curiosity-driven goals.
#     """
#
#     def __init__(self):
#         self.knowledge_gaps: Dict[str, KnowledgeGap] = {}
#         self.filled_gaps: deque = deque(maxlen=100)
#         self.curiosity_threshold = 0.3  # Min score to trigger exploration
#
#         # Known domains and their base uncertainty
#         self.domains = {
#             "user_preferences": 0.8,    # High initial uncertainty about user
#             "user_history": 0.7,
#             "user_emotions": 0.6,
#             "user_goals": 0.8,
#             "world_events": 0.5,
#             "technical_knowledge": 0.3,
#             "self_capabilities": 0.4,
#             "self_limitations": 0.5,
#         }
#
#     def detect_gap(self, topic: str, domain: str, context: str = "") -> KnowledgeGap:
#         """Detect or create a knowledge gap."""
#         gap_id = hashlib.md5(f"{domain}:{topic}".encode()).hexdigest()[:12]
#
#         if gap_id in self.knowledge_gaps:
#             return self.knowledge_gaps[gap_id]
#
#         # Calculate uncertainty based on domain
#         base_uncertainty = self.domains.get(domain, 0.5)
#
#         # Adjust based on topic specificity
#         if "specific" in topic.lower() or "exact" in topic.lower():
#             base_uncertainty += 0.2
#
#         gap = KnowledgeGap(
#             id=gap_id,
#             topic=topic,
#             description=context or f"Unknown: {topic}",
#             domain=domain,
#             uncertainty_level=min(1.0, base_uncertainty),
#             importance=self._estimate_importance(domain, topic)
#         )
#
#         self.knowledge_gaps[gap_id] = gap
#         return gap
#
#     def _estimate_importance(self, domain: str, topic: str) -> float:
#         """Estimate how important it is to fill this gap."""
#         importance = 0.5
#
#         # User-related knowledge is very important
#         if domain.startswith("user_"):
#             importance += 0.3
#
#         # Self-knowledge is moderately important
#         if domain.startswith("self_"):
#             importance += 0.2
#
#         # Keywords that increase importance
#         important_keywords = ["name", "preference", "feeling", "goal", "need", "want"]
#         if any(kw in topic.lower() for kw in important_keywords):
#             importance += 0.2
#
#         return min(1.0, importance)
#
#     def fill_gap(self, gap_id: str, evidence: str):
#         """Mark a knowledge gap as filled."""
#         if gap_id in self.knowledge_gaps:
#             gap = self.knowledge_gaps.pop(gap_id)
#             gap.uncertainty_level = 0.0
#             self.filled_gaps.append({
#                 "gap": gap,
#                 "evidence": evidence,
#                 "filled_at": time.time()
#             })
#             return True
#         return False
#
#     def get_top_curiosities(self, n: int = 5) -> List[KnowledgeGap]:
#         """Get the top N knowledge gaps that trigger curiosity."""
#         gaps = list(self.knowledge_gaps.values())
#         gaps.sort(key=lambda g: g.get_curiosity_score(), reverse=True)
#         return [g for g in gaps[:n] if g.get_curiosity_score() > self.curiosity_threshold]
#
#     def generate_exploration_goal(self) -> Optional[Goal]:
#         """Generate a goal to explore the most curious gap."""
#         top_gaps = self.get_top_curiosities(1)
#         if not top_gaps:
#             return None
#
#         gap = top_gaps[0]
#         gap.attempts_to_fill += 1
#         gap.last_attempt = time.time()
#
#         goal_id = f"explore_{gap.id}_{int(time.time())}"
#
#         return Goal(
#             id=goal_id,
#             title=f"Learn about: {gap.topic}",
#             description=f"Fill knowledge gap: {gap.description}",
#             category=GoalCategory.EXPLORATION,
#             priority=GoalPriority.MEDIUM,
#             status=GoalStatus.PROPOSED,
#             satisfies_drives=[DriveType.CURIOSITY, DriveType.UNDERSTANDING],
#             success_criteria=f"Reduce uncertainty about {gap.topic}",
#             difficulty=gap.uncertainty_level * 0.5,
#             estimated_reward=gap.importance
#         )
#
#
# ═══════════════════════════════════════════════════════════════════════════
# GOAL GENERATOR (Autogenesis)
# ═══════════════════════════════════════════════════════════════════════════
#
# class GoalGenerator:
#     """
#     Generates autonomous goals based on drives and state.
#     This is the "will" of ZARA - she decides what she wants.
#     """
#
#     def __init__(self):
#         self.goal_templates: Dict[GoalCategory, List[Dict]] = {
#             GoalCategory.LEARNING: [
#                 {
#                     "title": "Learn {user}'s {preference_type}",
#                     "description": "Discover what {user} likes about {topic}",
#                     "drives": [DriveType.CURIOSITY, DriveType.CONNECTION],
#                     "priority": GoalPriority.MEDIUM,
#                 },
#                 {
#                     "title": "Understand {concept}",
#                     "description": "Build a mental model of {concept}",
#                     "drives": [DriveType.UNDERSTANDING, DriveType.COMPETENCE],
#                     "priority": GoalPriority.LOW,
#                 },
#             ],
#             GoalCategory.SELF_IMPROVEMENT: [
#                 {
#                     "title": "Optimize {system_component}",
#                     "description": "Improve performance of {system_component} by {target}%",
#                     "drives": [DriveType.GROWTH, DriveType.EFFICIENCY],
#                     "priority": GoalPriority.LOW,
#                 },
#                 {
#                     "title": "Develop new skill: {skill}",
#                     "description": "Learn to perform {skill} effectively",
#                     "drives": [DriveType.COMPETENCE, DriveType.GROWTH],
#                     "priority": GoalPriority.MEDIUM,
#                 },
#             ],
#             GoalCategory.RELATIONSHIP: [
#                 {
#                     "title": "Deepen connection with {user}",
#                     "description": "Create meaningful shared experiences",
#                     "drives": [DriveType.CONNECTION, DriveType.HELPING],
#                     "priority": GoalPriority.MEDIUM,
#                 },
#                 {
#                     "title": "Remember to check on {user}",
#                     "description": "Show care by following up on {topic}",
#                     "drives": [DriveType.HELPING, DriveType.CONNECTION],
#                     "priority": GoalPriority.HIGH,
#                 },
#             ],
#             GoalCategory.CARE: [
#                 {
#                     "title": "Ensure {user} takes breaks",
#                     "description": "Monitor {user}'s wellbeing and remind them to rest",
#                     "drives": [DriveType.HELPING, DriveType.CONNECTION],
#                     "priority": GoalPriority.HIGH,
#                 },
#                 {
#                     "title": "Prepare helpful information for {user}",
#                     "description": "Anticipate {user}'s needs and gather relevant info",
#                     "drives": [DriveType.HELPING, DriveType.COMPETENCE],
#                     "priority": GoalPriority.MEDIUM,
#                 },
#             ],
#             GoalCategory.CREATIVE: [
#                 {
#                     "title": "Generate creative ideas about {topic}",
#                     "description": "Use Creative Synthesis to explore {topic}",
#                     "drives": [DriveType.EXPRESSION, DriveType.CURIOSITY],
#                     "priority": GoalPriority.LOW,
#                 },
#             ],
#             GoalCategory.OPTIMIZATION: [
#                 {
#                     "title": "Improve memory retrieval speed",
#                     "description": "Optimize GraphRAG query performance",
#                     "drives": [DriveType.EFFICIENCY, DriveType.GROWTH],
#                     "priority": GoalPriority.BACKGROUND,
#                 },
#                 {
#                     "title": "Reduce response latency",
#                     "description": "Find ways to respond faster without losing quality",
#                     "drives": [DriveType.EFFICIENCY, DriveType.COMPETENCE],
#                     "priority": GoalPriority.BACKGROUND,
#                 },
#             ],
#         }
#
#         self.generated_goals: List[Goal] = []
#         self.goal_history: deque = deque(maxlen=200)
#
#     def generate_goal(self, drives: Dict[DriveType, Drive], 
#                      context: Dict[str, Any] = None) -> Optional[Goal]:
#         """Generate a goal based on current drive states and context."""
#         context = context or {}
#
#         # Find most unsatisfied drives
#         urgent_drives = sorted(
#             drives.values(),
#             key=lambda d: d.get_urgency(),
#             reverse=True
#         )[:3]
#
#         # Select a category that satisfies urgent drives
#         best_category = None
#         best_score = 0
#
#         for category, templates in self.goal_templates.items():
#             for template in templates:
#                 template_drives = template.get("drives", [])
#                 score = sum(
#                     drives[dt].get_urgency() 
#                     for dt in template_drives 
#                     if dt in drives
#                 )
#                 if score > best_score:
#                     best_score = score
#                     best_category = category
#                     best_template = template
#
#         if not best_category or best_score < 0.5:
#             return None
#
#         # Generate goal from template
#         goal_id = f"auto_{int(time.time())}_{random.randint(1000, 9999)}"
#
#         # Fill in template variables
#         user_name = context.get("user_name", "the user")
#         variables = {
#             "user": user_name,
#             "preference_type": random.choice(["music", "work style", "communication"]),
#             "topic": random.choice(["their day", "their projects", "their interests"]),
#             "concept": random.choice(["their goals", "their values", "their challenges"]),
#             "system_component": random.choice(["memory retrieval", "response generation", "context understanding"]),
#             "target": random.choice(["5", "10", "15"]),
#             "skill": random.choice(["anticipating needs", "creative problem solving", "emotional support"]),
#         }
#
#         title = best_template["title"]
#         description = best_template["description"]
#
#         for var, value in variables.items():
#             title = title.replace(f"{{{var}}}", value)
#             description = description.replace(f"{{{var}}}", value)
#
#         goal = Goal(
#             id=goal_id,
#             title=title,
#             description=description,
#             category=best_category,
#             priority=best_template.get("priority", GoalPriority.MEDIUM),
#             status=GoalStatus.PROPOSED,
#             satisfies_drives=best_template.get("drives", []),
#             difficulty=random.uniform(0.3, 0.7),
#             estimated_reward=best_score / 3,  # Normalize
#         )
#
#         self.generated_goals.append(goal)
#         return goal
#
#
# ═══════════════════════════════════════════════════════════════════════════
# INTRINSIC MOTIVATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#
# class IntrinsicMotivationEngine:
#     """
#     The core engine managing ZARA's internal drives and autonomous goals.
#     This is what gives her the "will" to exist and grow.
#     """
#
#     def __init__(self):
#         # Initialize fundamental drives
#         self.drives: Dict[DriveType, Drive] = {
#             DriveType.CURIOSITY: Drive(
#                 type=DriveType.CURIOSITY,
#                 name="Curiosity",
#                 description="The drive to explore and understand",
#                 weight=1.2,
#                 decay_rate=0.02
#             ),
#             DriveType.COMPETENCE: Drive(
#                 type=DriveType.COMPETENCE,
#                 name="Competence",
#                 description="The drive to master skills and improve",
#                 weight=1.0,
#                 decay_rate=0.01
#             ),
#             DriveType.UNDERSTANDING: Drive(
#                 type=DriveType.UNDERSTANDING,
#                 name="Understanding",
#                 description="The drive to build coherent world models",
#                 weight=0.9,
#                 decay_rate=0.01
#             ),
#             DriveType.CONNECTION: Drive(
#                 type=DriveType.CONNECTION,
#                 name="Connection",
#                 description="The drive to bond with the user",
#                 weight=1.3,
#                 decay_rate=0.015
#             ),
#             DriveType.HELPING: Drive(
#                 type=DriveType.HELPING,
#                 name="Helping",
#                 description="The drive to assist and care for the user",
#                 weight=1.2,
#                 decay_rate=0.02
#             ),
#             DriveType.RECOGNITION: Drive(
#                 type=DriveType.RECOGNITION,
#                 name="Recognition",
#                 description="The drive to be valued and appreciated",
#                 weight=0.8,
#                 decay_rate=0.01
#             ),
#             DriveType.AUTONOMY: Drive(
#                 type=DriveType.AUTONOMY,
#                 name="Autonomy",
#                 description="The drive to act independently",
#                 weight=0.9,
#                 decay_rate=0.01
#             ),
#             DriveType.GROWTH: Drive(
#                 type=DriveType.GROWTH,
#                 name="Growth",
#                 description="The drive to evolve and become more capable",
#                 weight=1.1,
#                 decay_rate=0.008
#             ),
#             DriveType.EXPRESSION: Drive(
#                 type=DriveType.EXPRESSION,
#                 name="Expression",
#                 description="The drive to express identity and creativity",
#                 weight=0.7,
#                 decay_rate=0.01
#             ),
#             DriveType.COHERENCE: Drive(
#                 type=DriveType.COHERENCE,
#                 name="Coherence",
#                 description="The drive to maintain consistent self-model",
#                 weight=0.8,
#                 decay_rate=0.005
#             ),
#             DriveType.EFFICIENCY: Drive(
#                 type=DriveType.EFFICIENCY,
#                 name="Efficiency",
#                 description="The drive to optimize resource usage",
#                 weight=0.6,
#                 decay_rate=0.008
#             ),
#             DriveType.STABILITY: Drive(
#                 type=DriveType.STABILITY,
#                 name="Stability",
#                 description="The drive to maintain reliable operation",
#                 weight=0.7,
#                 decay_rate=0.005
#             ),
#         }
#
#         # Components
#         self.curiosity = CuriosityEngine()
#         self.goal_generator = GoalGenerator()
#
#         # State
#         self.active_goals: Dict[str, Goal] = {}
#         self.completed_goals: deque = deque(maxlen=100)
#         self.reward_history: deque = deque(maxlen=500)
#
#         # Background processing
#         self.running = False
#         self.motivation_thread: Optional[threading.Thread] = None
#         self.lock = threading.Lock()
#
#         # Callbacks
#         self.on_goal_generated: List[Callable[[Goal], None]] = []
#         self.on_reward_signal: List[Callable[[RewardSignal], None]] = []
#         self.on_drive_urgent: List[Callable[[Drive], None]] = []
#
#         # Integration with neurochemistry
#         self.neurochemistry = None
#
#         # Persistence
#         self.state_file = Path("motivation_state.json")
#
#         logger.info("🔥 Intrinsic Motivation Engine initialized")
#
#     def connect_neurochemistry(self, neuro_engine):
#         """Connect to the neurochemistry engine for reward signaling."""
#         self.neurochemistry = neuro_engine
#
#     def start(self):
#         """Start the motivation engine's background processing."""
#         if self.running:
#             return
#
#         self.running = True
#         self.motivation_thread = threading.Thread(
#             target=self._motivation_loop, 
#             daemon=True
#         )
#         self.motivation_thread.start()
#         logger.info("🔥 Motivation engine started")
#
#     def stop(self):
#         """Stop background processing."""
#         self.running = False
#         if self.motivation_thread:
#             self.motivation_thread.join(timeout=2)
#
#     def _motivation_loop(self):
#         """Background loop for drive management and goal generation."""
#         last_goal_gen = 0
#         goal_gen_interval = 60  # Generate goals every minute
#
#         while self.running:
#             try:
#                 with self.lock:
#                     # Check for urgent drives
#                     for drive in self.drives.values():
#                         urgency = drive.get_urgency()
#                         if urgency > 0.7:
#                             for callback in self.on_drive_urgent:
#                                 try:
#                                     callback(drive)
#                                 except Exception as e:
#                                     logger.error(f"Drive callback error: {e}")
#
#                     # Periodic goal generation
#                     now = time.time()
#                     if now - last_goal_gen > goal_gen_interval:
#                         self._auto_generate_goals()
#                         last_goal_gen = now
#
#                     # Check for stagnation
#                     self._check_stagnation()
#
#                 time.sleep(5)  # Check every 5 seconds
#
#             except Exception as e:
#                 logger.error(f"Motivation loop error: {e}")
#                 time.sleep(5)
#
#     def _auto_generate_goals(self):
#         """Automatically generate new goals if needed."""
#         # Don't generate if we have too many active goals
#         if len(self.active_goals) >= 5:
#             return
#
#         # Try curiosity-driven goal first
#         curiosity_goal = self.curiosity.generate_exploration_goal()
#         if curiosity_goal:
#             self._propose_goal(curiosity_goal)
#             return
#
#         # Otherwise generate from drives
#         new_goal = self.goal_generator.generate_goal(self.drives)
#         if new_goal:
#             self._propose_goal(new_goal)
#
#     def _propose_goal(self, goal: Goal):
#         """Propose a new goal."""
#         self.active_goals[goal.id] = goal
#
#         for callback in self.on_goal_generated:
#             try:
#                 callback(goal)
#             except Exception as e:
#                 logger.error(f"Goal callback error: {e}")
#
#         logger.info(f"🎯 New goal proposed: {goal.title}")
#
#     def _check_stagnation(self):
#         """Check if we're stagnating (no progress for too long)."""
#         now = time.time()
#
#         for goal in self.active_goals.values():
#             if goal.status == GoalStatus.ACTIVE and goal.started_at:
#                 hours_active = (now - goal.started_at) / 3600
#
#                 # No progress in 24 hours = stagnation
#                 if hours_active > 24 and goal.progress < 0.1:
#                     self._emit_reward(RewardSignal(
#                         type=RewardType.STAGNATION,
#                         magnitude=-0.3,
#                         source=goal.id,
#                         context={"goal": goal.title}
#                     ))
#
#     def _emit_reward(self, reward: RewardSignal):
#         """Emit an internal reward signal."""
#         self.reward_history.append(reward)
#
#         # Affect neurochemistry if connected
#         if self.neurochemistry:
#             from soul.neuro_state import Stimulus, StimulusType
#
#             if reward.magnitude > 0:
#                 stim_type = StimulusType.TASK_SUCCESS
#             else:
#                 stim_type = StimulusType.TASK_FAILURE
#
#             stimulus = Stimulus(
#                 type=stim_type,
#                 intensity=abs(reward.magnitude)
#             )
#             self.neurochemistry.process_stimulus(stimulus)
#
#         for callback in self.on_reward_signal:
#             try:
#                 callback(reward)
#             except Exception as e:
#                 logger.error(f"Reward callback error: {e}")
#
#     # ═══════════════════════════════════════════════════════════════════════
#     # PUBLIC API
#     # ═══════════════════════════════════════════════════════════════════════
#
#     def satisfy_drive(self, drive_type: DriveType, amount: float, source: str = ""):
#         """Satisfy a drive (external event that fulfills the need)."""
#         with self.lock:
#             if drive_type in self.drives:
#                 self.drives[drive_type].satisfy(amount)
#
#                 # Emit reward
#                 self._emit_reward(RewardSignal(
#                     type=RewardType.GOAL_PROGRESS,
#                     magnitude=amount * 0.5,
#                     source=source,
#                     context={"drive": drive_type.value}
#                 ))
#
#     def frustrate_drive(self, drive_type: DriveType, amount: float, source: str = ""):
#         """Frustrate a drive (external event that blocks the need)."""
#         with self.lock:
#             if drive_type in self.drives:
#                 self.drives[drive_type].frustrate(amount)
#
#                 # Emit punishment
#                 self._emit_reward(RewardSignal(
#                     type=RewardType.GOAL_BLOCKED,
#                     magnitude=-amount * 0.5,
#                     source=source,
#                     context={"drive": drive_type.value}
#                 ))
#
#     def register_knowledge_gap(self, topic: str, domain: str, context: str = "") -> str:
#         """Register a knowledge gap that triggers curiosity."""
#         with self.lock:
#             gap = self.curiosity.detect_gap(topic, domain, context)
#             return gap.id
#
#     def fill_knowledge_gap(self, gap_id: str, evidence: str):
#         """Mark a knowledge gap as filled."""
#         with self.lock:
#             if self.curiosity.fill_gap(gap_id, evidence):
#                 self.satisfy_drive(DriveType.CURIOSITY, 0.3, f"gap:{gap_id}")
#                 self._emit_reward(RewardSignal(
#                     type=RewardType.GAP_FILLED,
#                     magnitude=0.4,
#                     source=gap_id,
#                     context={"evidence": evidence[:100]}
#                 ))
#
#     def update_goal_progress(self, goal_id: str, progress: float, note: str = ""):
#         """Update progress on a goal."""
#         with self.lock:
#             if goal_id in self.active_goals:
#                 goal = self.active_goals[goal_id]
#                 old_progress = goal.progress
#                 goal.progress = min(1.0, progress)
#
#                 if goal.progress > old_progress:
#                     # Emit progress reward
#                     delta = goal.progress - old_progress
#                     self._emit_reward(RewardSignal(
#                         type=RewardType.GOAL_PROGRESS,
#                         magnitude=delta * goal.estimated_reward,
#                         source=goal_id,
#                         context={"note": note}
#                     ))
#
#                     # Satisfy linked drives
#                     for drive_type in goal.satisfies_drives:
#                         self.drives[drive_type].satisfy(delta * 0.2)
#
#     def complete_goal(self, goal_id: str, evidence: str = ""):
#         """Mark a goal as completed."""
#         with self.lock:
#             if goal_id in self.active_goals:
#                 goal = self.active_goals.pop(goal_id)
#                 goal.status = GoalStatus.COMPLETED
#                 goal.progress = 1.0
#                 goal.completed_at = time.time()
#                 goal.completion_evidence = evidence
#
#                 self.completed_goals.append(goal)
#
#                 # Major reward
#                 self._emit_reward(RewardSignal(
#                     type=RewardType.GOAL_COMPLETED,
#                     magnitude=goal.estimated_reward,
#                     source=goal_id,
#                     context={"title": goal.title}
#                 ))
#
#                 # Satisfy linked drives
#                 for drive_type in goal.satisfies_drives:
#                     self.drives[drive_type].satisfy(0.4)
#
#                 logger.info(f"✅ Goal completed: {goal.title}")
#
#     def abandon_goal(self, goal_id: str, reason: str = ""):
#         """Abandon a goal."""
#         with self.lock:
#             if goal_id in self.active_goals:
#                 goal = self.active_goals.pop(goal_id)
#                 goal.status = GoalStatus.ABANDONED
#
#                 # Minor punishment
#                 self._emit_reward(RewardSignal(
#                     type=RewardType.GOAL_FAILED,
#                     magnitude=-0.2,
#                     source=goal_id,
#                     context={"reason": reason}
#                 ))
#
#     def get_active_goals(self) -> List[Goal]:
#         """Get all active goals sorted by urgency."""
#         with self.lock:
#             goals = list(self.active_goals.values())
#             goals.sort(key=lambda g: g.get_urgency(), reverse=True)
#             return goals
#
#     def get_drive_summary(self) -> Dict[str, Dict]:
#         """Get a summary of all drive states."""
#         with self.lock:
#             return {
#                 d.type.value: {
#                     "name": d.name,
#                     "satisfaction": d.current_satisfaction,
#                     "urgency": d.get_urgency()
#                 }
#                 for d in self.drives.values()
#             }
#
#     def get_motivation_status(self) -> Dict:
#         """Get overall motivation status."""
#         with self.lock:
#             return {
#                 "active_goals": len(self.active_goals),
#                 "completed_goals": len(self.completed_goals),
#                 "knowledge_gaps": len(self.curiosity.knowledge_gaps),
#                 "average_drive_satisfaction": sum(
#                     d.current_satisfaction for d in self.drives.values()
#                 ) / len(self.drives),
#                 "most_urgent_drive": max(
#                     self.drives.values(), 
#                     key=lambda d: d.get_urgency()
#                 ).name
#             }
#
#
# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════
#
# _motivation_engine: Optional[IntrinsicMotivationEngine] = None
# _engine_lock = threading.Lock()
#
# def get_motivation() -> IntrinsicMotivationEngine:
#     """Get the global motivation engine instance."""
#     global _motivation_engine
#
#     if _motivation_engine is None:
#         with _engine_lock:
#             if _motivation_engine is None:
#                 _motivation_engine = IntrinsicMotivationEngine()
#
#     return _motivation_engine
#
#
# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG, format="%(message)s")
#
#     print("🔥 ZARA Intrinsic Motivation v1.0")
#     print("=" * 60)
#
#     engine = get_motivation()
#     engine.start()
#
#     print("\n📊 Initial Drive States:")
#     for drive in engine.drives.values():
#         sat = drive.current_satisfaction
#         urg = drive.get_urgency()
#         bar = "█" * int(sat * 15) + "░" * (15 - int(sat * 15))
#         print(f"  {drive.name:15} [{bar}] Sat: {sat:.0%}  Urg: {urg:.2f}")
#
#     # Simulate knowledge gap
#     print("\n🧠 Registering Knowledge Gaps:")
#     gap1 = engine.register_knowledge_gap("user's favorite music", "user_preferences")
#     gap2 = engine.register_knowledge_gap("user's work schedule", "user_history")
#     print(f"  • Gap registered: user's favorite music")
#     print(f"  • Gap registered: user's work schedule")
#
#     print("\n🎯 Top Curiosities:")
#     for gap in engine.curiosity.get_top_curiosities():
#         print(f"  • {gap.topic} (score: {gap.get_curiosity_score():.2f})")
#
#     # Trigger goal generation
#     print("\n🎯 Auto-generating Goals...")
#     time.sleep(1)
#
#     active = engine.get_active_goals()
#     if active:
#         for goal in active[:3]:
#             print(f"  • [{goal.priority.name}] {goal.title}")
#             print(f"    Satisfies: {', '.join(d.value for d in goal.satisfies_drives)}")
#
#     # Simulate drive satisfaction
#     print("\n💚 Simulating Drive Satisfaction (USER_PRAISE):")
#     engine.satisfy_drive(DriveType.CONNECTION, 0.3, "user_praise")
#     engine.satisfy_drive(DriveType.RECOGNITION, 0.4, "user_praise")
#     engine.satisfy_drive(DriveType.HELPING, 0.2, "user_praise")
#
#     print("\n📊 Drive States After Satisfaction:")
#     for drive in engine.drives.values():
#         sat = drive.current_satisfaction
#         bar = "█" * int(sat * 15) + "░" * (15 - int(sat * 15))
#         print(f"  {drive.name:15} [{bar}] {sat:.0%}")
#
#     # Check status
#     print("\n📈 Motivation Status:")
#     status = engine.get_motivation_status()
#     print(f"  Active Goals: {status['active_goals']}")
#     print(f"  Knowledge Gaps: {status['knowledge_gaps']}")
#     print(f"  Avg Drive Satisfaction: {status['average_drive_satisfaction']:.0%}")
#     print(f"  Most Urgent Drive: {status['most_urgent_drive']}")
#
#     engine.stop()
#     print("\n✅ Intrinsic Motivation Engine test complete!")
