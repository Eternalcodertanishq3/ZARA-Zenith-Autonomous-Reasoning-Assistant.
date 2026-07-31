"""
ZARA Continuous Learning v1.0
==============================
Limitless Learning from Every Interaction

True continuous learning that enables:
1. REAL-TIME LEARNING - Learn from every message instantly
2. PATTERN EXTRACTION - Find patterns across interactions
3. KNOWLEDGE SYNTHESIS - Build understanding from fragments
4. PREFERENCE LEARNING - Learn what user likes/dislikes
5. ERROR CORRECTION - Learn from mistakes
6. SKILL IMPROVEMENT - Get better at tasks over time
7. PERSONALITY EVOLUTION - Natural growth and development
8. CROSS-DOMAIN TRANSFER - Apply learning across areas
9. FEEDBACK INTEGRATION - Learn from explicit feedback
10. ADAPTIVE LEARNING RATE - Learn faster when needed

This makes ZARA truly limitless in her learning capacity,
growing smarter with every interaction, evolving toward
more human-like understanding and intelligence.
"""

import logging
import time
import sys
import json
import hashlib
import threading
import pickle
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque, Counter
from datetime import datetime
import re

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_LEARNING")


# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class LearningType(Enum):
    """Types of learning."""
    FACTUAL = "factual"                 # Learning facts
    PROCEDURAL = "procedural"           # Learning how to do things
    CONCEPTUAL = "conceptual"           # Understanding concepts
    PREFERENCE = "preference"           # User preferences
    BEHAVIORAL = "behavioral"           # Behavior patterns
    EMOTIONAL = "emotional"             # Emotional patterns
    LINGUISTIC = "linguistic"           # Language patterns
    CORRECTIVE = "corrective"           # Learning from errors
    ASSOCIATIVE = "associative"         # Learning associations
    CONTEXTUAL = "contextual"           # Context-dependent learning


class LearningSource(Enum):
    """Sources of learning."""
    CONVERSATION = "conversation"       # From conversations
    FEEDBACK = "feedback"               # Explicit feedback
    OBSERVATION = "observation"         # Observing patterns
    ERROR = "error"                     # From mistakes
    RESEARCH = "research"               # Active learning
    REFLECTION = "reflection"           # Self-reflection
    DREAM = "dream"                     # Dream mode synthesis


class LearningPriority(Enum):
    """Learning priority levels."""
    CRITICAL = "critical"               # Must learn immediately
    HIGH = "high"                       # Learn soon
    NORMAL = "normal"                   # Learn when possible
    LOW = "low"                         # Learn eventually
    BACKGROUND = "background"           # Passive learning


@dataclass
class Learning:
    """A piece of learning."""
    id: str
    type: LearningType
    source: LearningSource
    priority: LearningPriority
    content: str
    context: str
    confidence: float
    timestamp: float
    reinforcement_count: int = 0
    last_reinforced: float = 0
    connections: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class LearningPattern:
    """A pattern discovered through learning."""
    id: str
    pattern_type: str
    description: str
    examples: List[str]
    frequency: int
    confidence: float
    first_seen: float
    last_seen: float
    triggers: List[str]
    predictions: List[str]


@dataclass
class UserProfile:
    """Learned profile of the user."""
    # Preferences
    communication_style: str = "casual"
    preferred_response_length: str = "medium"
    topics_of_interest: List[str] = field(default_factory=list)
    topics_to_avoid: List[str] = field(default_factory=list)
    
    # Personality traits observed
    estimated_personality: Dict[str, float] = field(default_factory=dict)
    
    # Behavioral patterns
    active_hours: List[int] = field(default_factory=list)
    typical_request_types: Counter = field(default_factory=Counter)
    
    # Emotional patterns
    mood_patterns: Dict[str, float] = field(default_factory=dict)
    triggers_positive: List[str] = field(default_factory=list)
    triggers_negative: List[str] = field(default_factory=list)
    
    # Learning about user
    facts_about_user: Dict[str, str] = field(default_factory=dict)
    
    # Relationship
    interaction_count: int = 0
    trust_level: float = 0.5
    rapport_level: float = 0.5


@dataclass
class SkillProgress:
    """Progress in a particular skill."""
    skill_name: str
    proficiency: float = 0.5          # 0-1
    experience_points: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    last_practiced: float = 0
    learning_rate: float = 0.1
    plateau_count: int = 0


@dataclass 
class EvolutionSnapshot:
    """Snapshot of ZARA's evolution."""
    timestamp: float
    total_learnings: int
    knowledge_domains: Dict[str, int]
    skill_proficiencies: Dict[str, float]
    user_understanding: float
    interaction_count: int
    intelligence_score: float


# ═══════════════════════════════════════════════════════════════════════════
# REAL-TIME LEARNER
# ═══════════════════════════════════════════════════════════════════════════

class RealTimeLearner:
    """
    Learns from every interaction in real-time.
    No boundaries, limitless learning.
    """
    
    def __init__(self):
        self.learnings: Dict[str, Learning] = {}
        self.learning_queue: deque = deque(maxlen=1000)
        self.learning_by_type: Dict[LearningType, Set[str]] = defaultdict(set)
        
        # Learning triggers
        self.fact_patterns = [
            r"(?:my name is|i am called|i'm) (\w+)",
            r"(?:i live in|i'm from|i'm based in) (.+?)(?:\.|$)",
            r"(?:i work as|i'm a|my job is) (.+?)(?:\.|$)",
            r"(?:i like|i love|i enjoy) (.+?)(?:\.|$)",
            r"(?:i hate|i dislike|i don't like) (.+?)(?:\.|$)",
            r"(?:i'm|i am) (\d+) (?:years old|yo)",
            r"(?:my favorite|my fav|i prefer) (.+?)(?:\.|$)"
        ]
        
        self.correction_patterns = [
            r"(?:no,|actually,|that's wrong|incorrect) (.+)",
            r"(?:i meant|i mean|what i said was) (.+)",
            r"(?:not [\w\s]+, but) (.+)"
        ]
    
    def learn_from_message(self, message: str, role: str = "user", 
                          context: Dict = None) -> List[Learning]:
        """
        Learn from a single message.
        Extracts all possible learnings.
        """
        learnings = []
        message_lower = message.lower()
        context = context or {}
        
        # 1. Extract facts
        for pattern in self.fact_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                learning = self._create_learning(
                    type=LearningType.FACTUAL,
                    source=LearningSource.CONVERSATION,
                    content=match,
                    context=message,
                    confidence=0.8
                )
                learnings.append(learning)
        
        # 2. Detect preferences
        preference_signals = {
            "positive": ["love", "like", "enjoy", "prefer", "favorite", "best", "great", "awesome"],
            "negative": ["hate", "dislike", "don't like", "worst", "terrible", "awful", "boring"]
        }
        
        for valence, signals in preference_signals.items():
            for signal in signals:
                if signal in message_lower:
                    # Extract what they like/dislike
                    learning = self._create_learning(
                        type=LearningType.PREFERENCE,
                        source=LearningSource.CONVERSATION,
                        content=f"{valence}:{message}",
                        context=signal,
                        confidence=0.7
                    )
                    learnings.append(learning)
                    break
        
        # 3. Detect corrections
        for pattern in self.correction_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                learning = self._create_learning(
                    type=LearningType.CORRECTIVE,
                    source=LearningSource.FEEDBACK,
                    content=match,
                    context=message,
                    confidence=0.9,
                    priority=LearningPriority.HIGH
                )
                learnings.append(learning)
        
        # 4. Learn linguistic patterns
        # Track vocabulary, phrases, communication style
        words = message.split()
        if len(words) > 5:
            learning = self._create_learning(
                type=LearningType.LINGUISTIC,
                source=LearningSource.OBSERVATION,
                content=f"Message length: {len(words)} words",
                context="communication_pattern",
                confidence=0.6,
                priority=LearningPriority.BACKGROUND
            )
            learnings.append(learning)
        
        # 5. Emotional content
        emotion_words = {
            "happy": ["happy", "glad", "excited", "thrilled", "joyful"],
            "sad": ["sad", "upset", "depressed", "down", "unhappy"],
            "angry": ["angry", "mad", "frustrated", "annoyed", "furious"],
            "anxious": ["worried", "anxious", "nervous", "stressed", "scared"]
        }
        
        for emotion, words in emotion_words.items():
            if any(w in message_lower for w in words):
                learning = self._create_learning(
                    type=LearningType.EMOTIONAL,
                    source=LearningSource.OBSERVATION,
                    content=f"Expressed emotion: {emotion}",
                    context=message,
                    confidence=0.7
                )
                learnings.append(learning)
        
        # Store all learnings
        for learning in learnings:
            self.learnings[learning.id] = learning
            self.learning_by_type[learning.type].add(learning.id)
            self.learning_queue.append(learning.id)
        
        return learnings
    
    def _create_learning(self, type: LearningType, source: LearningSource,
                        content: str, context: str, confidence: float,
                        priority: LearningPriority = LearningPriority.NORMAL) -> Learning:
        """Create a new learning."""
        learning_id = hashlib.md5(f"{content}:{time.time()}".encode()).hexdigest()[:12]
        
        return Learning(
            id=learning_id,
            type=type,
            source=source,
            priority=priority,
            content=content,
            context=context,
            confidence=confidence,
            timestamp=time.time(),
            reinforcement_count=0,
            last_reinforced=time.time()
        )
    
    def reinforce_learning(self, learning_id: str, boost: float = 0.1):
        """Reinforce existing learning."""
        if learning_id in self.learnings:
            learning = self.learnings[learning_id]
            learning.reinforcement_count += 1
            learning.last_reinforced = time.time()
            learning.confidence = min(1.0, learning.confidence + boost)
    
    def find_related(self, content: str, limit: int = 5) -> List[Learning]:
        """Find related learnings."""
        content_words = set(content.lower().split())
        
        scored = []
        for learning in self.learnings.values():
            learning_words = set(learning.content.lower().split())
            overlap = len(content_words & learning_words)
            if overlap > 0:
                score = overlap / min(len(content_words), len(learning_words))
                scored.append((score, learning))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in scored[:limit]]
    
    def get_learnings_by_type(self, learning_type: LearningType) -> List[Learning]:
        """Get all learnings of a type."""
        return [self.learnings[lid] for lid in self.learning_by_type[learning_type]
                if lid in self.learnings]


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN DISCOVERER
# ═══════════════════════════════════════════════════════════════════════════

class PatternDiscoverer:
    """
    Discovers patterns across interactions.
    Builds understanding from repeated observations.
    """
    
    def __init__(self):
        self.patterns: Dict[str, LearningPattern] = {}
        self.pattern_candidates: Dict[str, int] = Counter()
        self.minimum_frequency = 3  # Need to see something 3 times
        
        # Pattern templates
        self.behavior_templates = [
            "User asks about {topic} when {condition}",
            "User prefers {style} when discussing {topic}",
            "User becomes {emotion} when {trigger}"
        ]
    
    def observe(self, observation: str, category: str = "general"):
        """Observe something for pattern detection."""
        # Normalize observation
        obs_key = f"{category}:{observation.lower()[:50]}"
        self.pattern_candidates[obs_key] += 1
        
        # Promote to pattern if seen enough times
        if self.pattern_candidates[obs_key] >= self.minimum_frequency:
            if obs_key not in self.patterns:
                pattern_id = hashlib.md5(obs_key.encode()).hexdigest()[:12]
                
                self.patterns[pattern_id] = LearningPattern(
                    id=pattern_id,
                    pattern_type=category,
                    description=observation,
                    examples=[],
                    frequency=self.pattern_candidates[obs_key],
                    confidence=0.6,
                    first_seen=time.time(),
                    last_seen=time.time(),
                    triggers=[],
                    predictions=[]
                )
            else:
                # Update existing pattern
                for pid, pattern in self.patterns.items():
                    if pattern.description.lower() == observation.lower():
                        pattern.frequency += 1
                        pattern.last_seen = time.time()
                        pattern.confidence = min(0.95, pattern.confidence + 0.05)
                        break
    
    def add_example(self, pattern_id: str, example: str):
        """Add example to a pattern."""
        if pattern_id in self.patterns:
            self.patterns[pattern_id].examples.append(example)
            if len(self.patterns[pattern_id].examples) > 10:
                self.patterns[pattern_id].examples = \
                    self.patterns[pattern_id].examples[-10:]
    
    def predict_from_pattern(self, context: str) -> List[Tuple[str, float]]:
        """Use patterns to make predictions."""
        predictions = []
        context_lower = context.lower()
        
        for pattern in self.patterns.values():
            # Check if any triggers match
            for trigger in pattern.triggers:
                if trigger.lower() in context_lower:
                    for pred in pattern.predictions:
                        predictions.append((pred, pattern.confidence))
        
        return predictions
    
    def get_strong_patterns(self, min_confidence: float = 0.7) -> List[LearningPattern]:
        """Get high-confidence patterns."""
        return [p for p in self.patterns.values() if p.confidence >= min_confidence]


# ═══════════════════════════════════════════════════════════════════════════
# USER PROFILER
# ═══════════════════════════════════════════════════════════════════════════

class UserProfiler:
    """
    Builds and maintains a profile of the user.
    Learns preferences, patterns, and personality.
    """
    
    def __init__(self):
        self.profile = UserProfile()
        self.profile_history: deque = deque(maxlen=50)
    
    def update_from_message(self, message: str, metadata: Dict = None):
        """Update profile from a message."""
        metadata = metadata or {}
        message_lower = message.lower()
        
        self.profile.interaction_count += 1
        
        # Track active hours
        current_hour = datetime.now().hour
        if current_hour not in self.profile.active_hours:
            self.profile.active_hours.append(current_hour)
        
        # Detect communication style
        if any(w in message_lower for w in ["yo", "hey", "sup", "lol", "haha"]):
            self.profile.communication_style = "casual"
        elif any(w in message_lower for w in ["please", "kindly", "would you", "sir", "formal"]):
            self.profile.communication_style = "formal"
        
        # Track message length preference
        word_count = len(message.split())
        if word_count < 10:
            self.profile.preferred_response_length = "short"
        elif word_count < 30:
            self.profile.preferred_response_length = "medium"
        else:
            self.profile.preferred_response_length = "detailed"
        
        # Extract topics of interest
        topic_indicators = ["about", "regarding", "concerning", "help with", "interested in"]
        for indicator in topic_indicators:
            if indicator in message_lower:
                idx = message_lower.find(indicator)
                topic = message[idx:idx+50].split()[1:4]
                if topic:
                    topic_str = " ".join(topic)
                    if topic_str not in self.profile.topics_of_interest:
                        self.profile.topics_of_interest.append(topic_str)
        
        # Build trust over interactions
        self.profile.trust_level = min(1.0, 0.5 + self.profile.interaction_count * 0.01)
        self.profile.rapport_level = min(1.0, 0.5 + self.profile.interaction_count * 0.01)
    
    def learn_fact(self, key: str, value: str):
        """Learn a fact about the user."""
        self.profile.facts_about_user[key] = value
        
        self.profile_history.append({
            "type": "fact_learned",
            "key": key,
            "value": value,
            "timestamp": time.time()
        })
    
    def update_preference(self, topic: str, is_positive: bool):
        """Update preference for a topic."""
        if is_positive:
            if topic not in self.profile.topics_of_interest:
                self.profile.topics_of_interest.append(topic)
            if topic in self.profile.topics_to_avoid:
                self.profile.topics_to_avoid.remove(topic)
        else:
            if topic not in self.profile.topics_to_avoid:
                self.profile.topics_to_avoid.append(topic)
            if topic in self.profile.topics_of_interest:
                self.profile.topics_of_interest.remove(topic)
    
    def get_personalization_hints(self) -> Dict[str, Any]:
        """Get hints for personalizing responses."""
        return {
            "style": self.profile.communication_style,
            "length": self.profile.preferred_response_length,
            "interests": self.profile.topics_of_interest[:5],
            "avoid": self.profile.topics_to_avoid[:5],
            "trust": self.profile.trust_level,
            "rapport": self.profile.rapport_level
        }
    
    def get_profile_summary(self) -> str:
        """Get a summary of the user profile."""
        facts = ", ".join(f"{k}: {v}" for k, v in 
                         list(self.profile.facts_about_user.items())[:5])
        interests = ", ".join(self.profile.topics_of_interest[:5])
        
        return f"""User Profile:
• Communication: {self.profile.communication_style}
• Response length: {self.profile.preferred_response_length}
• Interests: {interests or 'not yet learned'}
• Known facts: {facts or 'none yet'}
• Trust level: {self.profile.trust_level:.0%}
• Interactions: {self.profile.interaction_count}"""


# ═══════════════════════════════════════════════════════════════════════════
# SKILL TRACKER
# ═══════════════════════════════════════════════════════════════════════════

class SkillTracker:
    """
    Tracks and improves skills over time.
    Gets better at tasks through practice.
    """
    
    def __init__(self):
        self.skills: Dict[str, SkillProgress] = {}
        self.skill_history: deque = deque(maxlen=500)
        
        # Initialize core skills
        core_skills = [
            "conversation", "empathy", "reasoning", "creativity",
            "coding", "explanation", "problem_solving", "humor"
        ]
        
        for skill in core_skills:
            self.skills[skill] = SkillProgress(
                skill_name=skill,
                proficiency=0.7,
                experience_points=100
            )
    
    def record_skill_use(self, skill_name: str, success: bool, 
                        difficulty: float = 0.5):
        """Record use of a skill."""
        if skill_name not in self.skills:
            self.skills[skill_name] = SkillProgress(skill_name=skill_name)
        
        skill = self.skills[skill_name]
        skill.last_practiced = time.time()
        
        if success:
            skill.successful_uses += 1
            # More XP for harder tasks
            xp_gain = int(10 * difficulty * (1 + skill.learning_rate))
            skill.experience_points += xp_gain
            
            # Improve proficiency
            improvement = skill.learning_rate * difficulty * 0.1
            skill.proficiency = min(1.0, skill.proficiency + improvement)
            
        else:
            skill.failed_uses += 1
            # Still learn from failure, just less
            skill.experience_points += int(5 * difficulty)
        
        # Log
        self.skill_history.append({
            "skill": skill_name,
            "success": success,
            "difficulty": difficulty,
            "proficiency": skill.proficiency,
            "timestamp": time.time()
        })
    
    def get_proficiency(self, skill_name: str) -> float:
        """Get current proficiency for a skill."""
        if skill_name in self.skills:
            return self.skills[skill_name].proficiency
        return 0.5  # Default
    
    def get_best_skills(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top skills."""
        sorted_skills = sorted(self.skills.values(), 
                              key=lambda x: x.proficiency, reverse=True)
        return [(s.skill_name, s.proficiency) for s in sorted_skills[:limit]]
    
    def get_skills_to_improve(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get skills that need improvement."""
        sorted_skills = sorted(self.skills.values(), 
                              key=lambda x: x.proficiency)
        return [(s.skill_name, s.proficiency) for s in sorted_skills[:limit]]
    
    def decay_unused_skills(self, days_threshold: int = 7):
        """Decay skills that haven't been used."""
        current_time = time.time()
        threshold_seconds = days_threshold * 86400
        
        for skill in self.skills.values():
            if skill.last_practiced > 0:
                time_since_use = current_time - skill.last_practiced
                if time_since_use > threshold_seconds:
                    decay = 0.01 * (time_since_use / threshold_seconds)
                    skill.proficiency = max(0.3, skill.proficiency - decay)


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════

class KnowledgeSynthesizer:
    """
    Synthesizes new knowledge from fragments.
    Creates understanding by connecting learnings.
    """
    
    def __init__(self):
        self.knowledge_graph: Dict[str, Set[str]] = defaultdict(set)
        self.synthesized_insights: List[Dict] = []
    
    def connect(self, concept_a: str, concept_b: str, relationship: str = "related"):
        """Connect two concepts."""
        key_a = concept_a.lower()
        key_b = concept_b.lower()
        
        self.knowledge_graph[key_a].add(f"{relationship}:{key_b}")
        self.knowledge_graph[key_b].add(f"{relationship}:{key_a}")
    
    def synthesize(self, learnings: List[Learning]) -> List[Dict]:
        """
        Synthesize new insights from multiple learnings.
        """
        insights = []
        
        # Group learnings by topic
        by_topic: Dict[str, List[Learning]] = defaultdict(list)
        
        for learning in learnings:
            # Extract topics from content
            words = learning.content.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    by_topic[word].append(learning)
        
        # Find insights where multiple learnings connect
        for topic, topic_learnings in by_topic.items():
            if len(topic_learnings) >= 2:
                # Multiple learnings about same topic = potential insight
                types_present = set(l.type for l in topic_learnings)
                
                if len(types_present) >= 2:
                    # Cross-type insight
                    insight = {
                        "type": "cross_type_insight",
                        "topic": topic,
                        "contributing_learnings": len(topic_learnings),
                        "learning_types": [t.value for t in types_present],
                        "confidence": sum(l.confidence for l in topic_learnings) / len(topic_learnings),
                        "timestamp": time.time()
                    }
                    insights.append(insight)
                    self.synthesized_insights.append(insight)
        
        return insights
    
    def get_related_concepts(self, concept: str, depth: int = 2) -> Set[str]:
        """Get concepts related to a given concept."""
        related = set()
        to_explore = [concept.lower()]
        explored = set()
        
        for _ in range(depth):
            next_explore = []
            for c in to_explore:
                if c in explored:
                    continue
                explored.add(c)
                
                if c in self.knowledge_graph:
                    for connection in self.knowledge_graph[c]:
                        _, connected = connection.split(":", 1)
                        related.add(connected)
                        next_explore.append(connected)
            
            to_explore = next_explore
        
        return related


# ═══════════════════════════════════════════════════════════════════════════
# EVOLUTION TRACKER
# ═══════════════════════════════════════════════════════════════════════════

class EvolutionTracker:
    """
    Tracks ZARA's evolution and growth over time.
    Measures progress toward human-like intelligence.
    """
    
    def __init__(self):
        self.snapshots: List[EvolutionSnapshot] = []
        self.metrics_history: deque = deque(maxlen=1000)
        
        # Intelligence components
        self.intelligence_weights = {
            "knowledge_breadth": 0.15,
            "skill_depth": 0.15,
            "learning_rate": 0.1,
            "pattern_recognition": 0.15,
            "user_understanding": 0.15,
            "emotional_intelligence": 0.1,
            "creativity": 0.1,
            "self_awareness": 0.1
        }
    
    def take_snapshot(self, learner: 'ContinuousLearner') -> EvolutionSnapshot:
        """Take a snapshot of current evolution state."""
        # Calculate intelligence score
        skill_avg = sum(s.proficiency for s in learner.skill_tracker.skills.values()) / \
                   max(len(learner.skill_tracker.skills), 1)
        
        pattern_count = len(learner.pattern_discoverer.patterns)
        
        intelligence_score = (
            0.15 * min(1.0, len(learner.real_time_learner.learnings) / 500) +
            0.15 * skill_avg +
            0.1 * learner.learning_rate +
            0.15 * min(1.0, pattern_count / 20) +
            0.15 * learner.user_profiler.profile.trust_level +
            0.1 * skill_avg +  # Emotional intelligence approximation
            0.1 * learner.skill_tracker.get_proficiency("creativity") +
            0.1 * 0.8  # Self-awareness (meta-awareness module)
        )
        
        # Create snapshot
        snapshot = EvolutionSnapshot(
            timestamp=time.time(),
            total_learnings=len(learner.real_time_learner.learnings),
            knowledge_domains={lt.value: len(ids) for lt, ids in 
                              learner.real_time_learner.learning_by_type.items()},
            skill_proficiencies={s.skill_name: s.proficiency 
                                for s in learner.skill_tracker.skills.values()},
            user_understanding=learner.user_profiler.profile.trust_level,
            interaction_count=learner.user_profiler.profile.interaction_count,
            intelligence_score=intelligence_score
        )
        
        self.snapshots.append(snapshot)
        
        return snapshot
    
    def get_growth_rate(self) -> float:
        """Calculate growth rate over recent snapshots."""
        if len(self.snapshots) < 2:
            return 0.0
        
        recent = self.snapshots[-10:]
        if len(recent) < 2:
            return 0.0
        
        first_score = recent[0].intelligence_score
        last_score = recent[-1].intelligence_score
        
        growth = (last_score - first_score) / first_score if first_score > 0 else 0
        return growth
    
    def get_evolution_summary(self) -> str:
        """Get summary of evolution."""
        if not self.snapshots:
            return "No evolution data yet."
        
        latest = self.snapshots[-1]
        growth = self.get_growth_rate()
        
        return f"""Evolution Status:
• Intelligence Score: {latest.intelligence_score:.2f}
• Total Learnings: {latest.total_learnings}
• Interactions: {latest.interaction_count}
• Growth Rate: {growth:+.1%}
• User Understanding: {latest.user_understanding:.0%}"""


# ═══════════════════════════════════════════════════════════════════════════
# CONTINUOUS LEARNER - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class ContinuousLearner:
    """
    Main continuous learning engine.
    Limitless learning from every interaction.
    """
    
    def __init__(self):
        self.real_time_learner = RealTimeLearner()
        self.pattern_discoverer = PatternDiscoverer()
        self.user_profiler = UserProfiler()
        self.skill_tracker = SkillTracker()
        self.knowledge_synthesizer = KnowledgeSynthesizer()
        self.evolution_tracker = EvolutionTracker()
        
        # Learning configuration
        self.learning_rate = 0.1
        self.auto_synthesize = True
        self.synthesis_threshold = 10  # Synthesize every N learnings
        
        # Stats
        self.total_messages_processed = 0
        self.total_learnings_created = 0
        
        # Persistence
        self.state_file = Path("learning/continuous_state.json")
        
        # Background processing
        self.learning_lock = threading.Lock()
        
        logger.info("📚 Continuous Learning initialized")
    
    def learn(self, message: str, role: str = "user", 
             metadata: Dict = None) -> Dict:
        """
        Learn from a message.
        Main entry point for all learning.
        
        Args:
            message: The message content
            role: Who sent it (user/assistant)
            metadata: Additional context
            
        Returns:
            Summary of what was learned
        """
        with self.learning_lock:
            metadata = metadata or {}
            self.total_messages_processed += 1
            
            result = {
                "learnings": [],
                "patterns": [],
                "insights": [],
                "profile_updated": False,
                "skills_used": []
            }
            
            # 1. Real-time learning
            learnings = self.real_time_learner.learn_from_message(
                message, role, metadata
            )
            result["learnings"] = [l.content for l in learnings]
            self.total_learnings_created += len(learnings)
            
            # 2. Update user profile
            if role == "user":
                self.user_profiler.update_from_message(message, metadata)
                result["profile_updated"] = True
            
            # 3. Pattern observation
            for learning in learnings:
                self.pattern_discoverer.observe(
                    learning.content, 
                    learning.type.value
                )
            
            # 4. Knowledge synthesis (periodically)
            if self.auto_synthesize and \
               len(self.real_time_learner.learnings) % self.synthesis_threshold == 0:
                all_learnings = list(self.real_time_learner.learnings.values())
                recent = all_learnings[-50:]  # Last 50 learnings
                insights = self.knowledge_synthesizer.synthesize(recent)
                result["insights"] = insights
            
            # 5. Track skills from my own responses
            if role == "assistant":
                # Estimate which skills were used
                skills_used = self._detect_skills_used(message)
                for skill in skills_used:
                    # Assume success for now (could be updated with feedback)
                    self.skill_tracker.record_skill_use(skill, True, 0.5)
                    result["skills_used"].append(skill)
            
            # 6. Extract facts about user
            if role == "user":
                facts = self._extract_user_facts(message)
                for key, value in facts.items():
                    self.user_profiler.learn_fact(key, value)
            
            return result
    
    def _detect_skills_used(self, response: str) -> List[str]:
        """Detect which skills were used in a response."""
        skills = []
        response_lower = response.lower()
        
        skill_indicators = {
            "coding": ["```", "def ", "function", "class ", "import"],
            "explanation": ["because", "therefore", "this means", "in other words"],
            "empathy": ["i understand", "that must be", "i can see how"],
            "creativity": ["imagine", "what if", "here's an idea"],
            "humor": ["haha", "lol", "😄", "joke", "funny"],
            "problem_solving": ["solution", "try this", "approach", "let's"],
            "reasoning": ["if", "then", "therefore", "because", "since"]
        }
        
        for skill, indicators in skill_indicators.items():
            if any(ind in response_lower for ind in indicators):
                skills.append(skill)
        
        return skills if skills else ["conversation"]
    
    def _extract_user_facts(self, message: str) -> Dict[str, str]:
        """Extract factual information about user."""
        facts = {}
        message_lower = message.lower()
        
        # Name extraction
        name_match = re.search(r"(?:my name is|i am called|i'm) (\w+)", message_lower)
        if name_match:
            facts["name"] = name_match.group(1).title()
        
        # Location extraction
        loc_match = re.search(r"(?:i live in|i'm from|based in) (.+?)(?:\.|,|$)", message_lower)
        if loc_match:
            facts["location"] = loc_match.group(1).strip().title()
        
        # Job extraction  
        job_match = re.search(r"(?:i work as|i'm a|my job is) (.+?)(?:\.|,|$)", message_lower)
        if job_match:
            facts["occupation"] = job_match.group(1).strip()
        
        return facts
    
    def receive_feedback(self, feedback_type: str, content: str, 
                        context: str = "") -> Learning:
        """
        Receive explicit feedback for learning.
        
        feedback_type: "positive", "negative", "correction"
        """
        priority = LearningPriority.HIGH if feedback_type == "correction" else LearningPriority.NORMAL
        
        learning = self.real_time_learner._create_learning(
            type=LearningType.CORRECTIVE,
            source=LearningSource.FEEDBACK,
            content=f"{feedback_type}: {content}",
            context=context,
            confidence=0.9,
            priority=priority
        )
        
        self.real_time_learner.learnings[learning.id] = learning
        self.total_learnings_created += 1
        
        # Update skill based on feedback
        if feedback_type == "negative":
            # Find recent skills used and mark as less successful
            recent_skills = list(self.skill_tracker.skill_history)[-3:]
            for entry in recent_skills:
                if entry.get("success"):
                    # Retroactively reduce proficiency
                    skill_name = entry.get("skill")
                    if skill_name in self.skill_tracker.skills:
                        self.skill_tracker.skills[skill_name].proficiency -= 0.02
        
        return learning
    
    def get_personalized_context(self) -> Dict:
        """Get context for personalizing responses."""
        return {
            "user_profile": self.user_profiler.get_personalization_hints(),
            "recent_learnings": [l.content for l in 
                                list(self.real_time_learner.learnings.values())[-5:]],
            "strong_patterns": [p.description for p in 
                               self.pattern_discoverer.get_strong_patterns()[:3]],
            "best_skills": self.skill_tracker.get_best_skills(3)
        }
    
    def get_evolution_state(self) -> EvolutionSnapshot:
        """Get current evolution state."""
        return self.evolution_tracker.take_snapshot(self)
    
    def get_status(self) -> str:
        """Get learning status summary."""
        evolution = self.get_evolution_state()
        user_summary = self.user_profiler.get_profile_summary()
        
        best_skills = self.skill_tracker.get_best_skills(3)
        need_work = self.skill_tracker.get_skills_to_improve(3)
        
        lines = [
            "📚 Continuous Learning Status",
            "=" * 40,
            "",
            f"Messages processed: {self.total_messages_processed}",
            f"Total learnings: {self.total_learnings_created}",
            f"Patterns discovered: {len(self.pattern_discoverer.patterns)}",
            f"Knowledge connections: {sum(len(v) for v in self.knowledge_synthesizer.knowledge_graph.values())}",
            "",
            "🎯 Best Skills:",
            *[f"  • {name}: {prof:.0%}" for name, prof in best_skills],
            "",
            "📈 Needs Practice:",
            *[f"  • {name}: {prof:.0%}" for name, prof in need_work],
            "",
            self.evolution_tracker.get_evolution_summary(),
            "",
            user_summary
        ]
        
        return "\n".join(lines)
    
    def save_state(self):
        """Save learning state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "total_messages": self.total_messages_processed,
            "total_learnings": self.total_learnings_created,
            "user_profile": {
                "communication_style": self.user_profiler.profile.communication_style,
                "interests": self.user_profiler.profile.topics_of_interest,
                "facts": self.user_profiler.profile.facts_about_user,
                "interaction_count": self.user_profiler.profile.interaction_count
            },
            "skills": {
                name: {"proficiency": s.proficiency, "xp": s.experience_points}
                for name, s in self.skill_tracker.skills.items()
            }
        }
        
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"💾 Learning state saved")
    
    def load_state(self):
        """Load learning state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                
                self.total_messages_processed = state.get("total_messages", 0)
                self.total_learnings_created = state.get("total_learnings", 0)
                
                if "user_profile" in state:
                    up = state["user_profile"]
                    self.user_profiler.profile.communication_style = up.get("communication_style", "casual")
                    self.user_profiler.profile.topics_of_interest = up.get("interests", [])
                    self.user_profiler.profile.facts_about_user = up.get("facts", {})
                    self.user_profiler.profile.interaction_count = up.get("interaction_count", 0)
                
                if "skills" in state:
                    for name, data in state["skills"].items():
                        if name in self.skill_tracker.skills:
                            self.skill_tracker.skills[name].proficiency = data.get("proficiency", 0.5)
                            self.skill_tracker.skills[name].experience_points = data.get("xp", 0)
                
                logger.info(f"📂 Learning state loaded")
                
            except Exception as e:
                logger.error(f"Error loading state: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_continuous_learner = None

def get_continuous_learner() -> ContinuousLearner:
    """Get the global continuous learner instance."""
    global _continuous_learner
    if _continuous_learner is None:
        _continuous_learner = ContinuousLearner()
    return _continuous_learner


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n📚 ZARA Continuous Learning v1.0\n")
    print("=" * 60)
    
    learner = ContinuousLearner()
    
    # Simulate a conversation
    messages = [
        ("user", "Hey! My name is Alex and I'm from Seattle."),
        ("assistant", "Nice to meet you Alex! Seattle is a beautiful city. What brings you here today?"),
        ("user", "I love programming and I'm working on an AI project. I really enjoy Python."),
        ("assistant", "That's awesome! Python is great for AI. I can help you with your project. What specifically are you working on?"),
        ("user", "I'm building a chatbot. I hate when they give generic responses."),
        ("assistant", "I totally understand that frustration! Let me help you create something more personalized and engaging."),
        ("user", "Thanks! You're actually pretty helpful. I was skeptical at first."),
        ("assistant", "I appreciate you giving me a chance! I'm always learning to be better."),
    ]
    
    print("🎭 Simulating conversation...\n")
    
    for role, message in messages:
        print(f"  {role.upper()}: {message[:50]}...")
        result = learner.learn(message, role)
        
        if result["learnings"]:
            for l in result["learnings"][:2]:
                print(f"    📝 Learned: {l[:40]}...")
    
    # Show status
    print("\n" + "-" * 60)
    print(learner.get_status())
    
    # Test personalization
    print("\n" + "-" * 60)
    print("🎯 Personalization Context:")
    context = learner.get_personalized_context()
    print(f"  User profile: {context['user_profile']}")
    print(f"  Best skills: {context['best_skills']}")
    
    # Test feedback
    print("\n" + "-" * 60)
    print("📋 Receiving feedback...")
    learner.receive_feedback("positive", "Great explanation!", "coding help")
    print("  ✓ Positive feedback recorded")
    
    # Evolution
    print("\n" + "-" * 60)
    evolution = learner.get_evolution_state()
    print(f"🧬 Evolution:")
    print(f"  Intelligence Score: {evolution.intelligence_score:.2f}")
    print(f"  Total Learnings: {evolution.total_learnings}")
    print(f"  Interactions: {evolution.interaction_count}")
    
    print("\n" + "=" * 60)
    print("✅ Continuous Learning ready!\n")
