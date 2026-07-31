"""
ZARA Unified Episodic Learner
Merges all experiential streams (Chat, Vision, Social, Actions) into a 
unified episodic memory that drives organic personality evolution.
"""
import logging
import time
import json
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from pathlib import Path
from enum import Enum

logger = logging.getLogger("ZARA_EPISODIC_LEARNER")


class ExperienceType(Enum):
    """Types of experiences ZARA can have."""
    CONVERSATION = "conversation"      # Talked with user
    VISUAL_OBSERVATION = "visual"      # Saw something
    EMOTIONAL_DETECTION = "emotion"    # Detected emotion from voice/text
    ACTION_TAKEN = "action"            # Did something (tool use, etc.)
    SOCIAL_INTERACTION = "social"      # Interacted with other agents
    SELF_REFLECTION = "reflection"     # Thought about herself
    LEARNING = "learning"              # Learned something new


@dataclass
class Experience:
    """A single experience/event."""
    id: str
    experience_type: ExperienceType
    content: str
    context: Dict[str, Any]
    emotional_valence: float  # -1 (negative) to 1 (positive)
    importance: float  # 0 to 1
    timestamp: float
    tags: List[str] = field(default_factory=list)
    linked_experiences: List[str] = field(default_factory=list)


@dataclass
class Insight:
    """An insight derived from experiences."""
    id: str
    content: str
    source_experiences: List[str]
    confidence: float
    timestamp: float
    applied: bool = False


@dataclass
class PersonalityShift:
    """A shift in personality based on experiences."""
    trait: str
    old_value: float
    new_value: float
    reason: str
    timestamp: float


class EpisodicLearner:
    """
    ZARA's Unified Episodic Learning System.
    
    This is the core of organic learning:
    - Collects experiences from all modalities
    - Synthesizes patterns across experiences
    - Derives insights that influence personality
    - Enables true "learning from life"
    
    No scripting - pure experience-driven growth.
    """
    
    def __init__(self, personality_system=None, memory_system=None):
        try:
            from config import MEMORY_DIR
            self.learner_dir = MEMORY_DIR / "episodic_learner"
        except ImportError:
            self.learner_dir = Path("memory/episodic_learner")
        
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        
        # External systems
        self.personality = personality_system
        self.memory = memory_system
        
        # Experience stream
        self.experience_stream: deque = deque(maxlen=1000)
        self.recent_experiences: List[Experience] = []
        
        # Derived insights
        self.insights: List[Insight] = []
        self.personality_shifts: List[PersonalityShift] = []
        
        # Pattern tracking
        self.patterns: Dict[str, float] = {}  # pattern -> frequency
        self.associations: Dict[str, List[str]] = {}  # tag -> related tags
        
        # Emotional baseline
        self.emotional_baseline = 0.5  # Neutral
        self.emotional_momentum = 0.0
        
        # Persistence
        self.experiences_file = self.learner_dir / "experiences.json"
        self.insights_file = self.learner_dir / "insights.json"
        self.patterns_file = self.learner_dir / "patterns.json"
        
        self._load_state()
        
        self.lock = threading.Lock()
        
        logger.info("📚 Episodic Learner initialized")
    
    def _load_state(self):
        """Load persisted state."""
        # Load patterns
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = data.get("patterns", {})
                    self.associations = data.get("associations", {})
                    self.emotional_baseline = data.get("emotional_baseline", 0.5)
            except Exception as e:
                logger.warning(f"Could not load patterns: {e}")
        
        # Load insights
        if self.insights_file.exists():
            try:
                with open(self.insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-50:]:
                        self.insights.append(Insight(**item))
            except Exception as e:
                logger.warning(f"Could not load insights: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        # Save patterns
        patterns_data = {
            "patterns": dict(list(self.patterns.items())[-100:]),
            "associations": self.associations,
            "emotional_baseline": self.emotional_baseline
        }
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2)
        
        # Save insights
        insights_data = [
            {
                "id": i.id,
                "content": i.content,
                "source_experiences": i.source_experiences[-5:],
                "confidence": i.confidence,
                "timestamp": i.timestamp,
                "applied": i.applied
            }
            for i in self.insights[-50:]
        ]
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(insights_data, f, indent=2)
    
    # ═══════════════════════════════════════════════════════════════════
    # EXPERIENCE INGESTION
    # ═══════════════════════════════════════════════════════════════════
    
    def record_experience(self, 
                         experience_type: ExperienceType,
                         content: str,
                         context: Dict[str, Any] = None,
                         emotional_valence: float = 0.0,
                         importance: float = 0.5,
                         tags: List[str] = None) -> Experience:
        """Record a new experience."""
        exp_id = f"exp_{int(time.time() * 1000)}"
        
        experience = Experience(
            id=exp_id,
            experience_type=experience_type,
            content=content[:500],  # Truncate long content
            context=context or {},
            emotional_valence=emotional_valence,
            importance=importance,
            timestamp=time.time(),
            tags=tags or []
        )
        
        with self.lock:
            self.experience_stream.append(experience)
            self.recent_experiences.append(experience)
            
            # Keep recent limited
            if len(self.recent_experiences) > 50:
                self.recent_experiences = self.recent_experiences[-50:]
            
            # Update patterns
            self._update_patterns(experience)
            
            # Update emotional state
            self._update_emotional_state(experience)
        
        logger.debug(f"Recorded experience: {experience_type.value}")
        
        return experience
    
    def record_conversation(self, user_input: str, zara_response: str,
                           detected_emotion: str = None):
        """Record a conversation experience."""
        valence = self._estimate_valence(user_input, detected_emotion)
        
        tags = self._extract_tags(user_input)
        if detected_emotion:
            tags.append(f"emotion:{detected_emotion}")
        
        context = {
            "user_input": user_input[:200],
            "response_length": len(zara_response),
            "detected_emotion": detected_emotion
        }
        
        self.record_experience(
            ExperienceType.CONVERSATION,
            content=f"User said: {user_input[:100]}",
            context=context,
            emotional_valence=valence,
            importance=self._estimate_importance(user_input),
            tags=tags
        )
    
    def record_visual(self, description: str, emotions_detected: List[str] = None):
        """Record a visual observation."""
        valence = 0.2  # Slightly positive (seeing is engaging)
        if emotions_detected:
            if "smile" in emotions_detected or "happy" in emotions_detected:
                valence = 0.6
            elif "sad" in emotions_detected or "upset" in emotions_detected:
                valence = -0.3
        
        self.record_experience(
            ExperienceType.VISUAL_OBSERVATION,
            content=description[:200],
            context={"emotions_in_scene": emotions_detected or []},
            emotional_valence=valence,
            importance=0.3,
            tags=["visual"] + (emotions_detected or [])
        )
    
    def record_action(self, action_name: str, success: bool, 
                     outcome: str = None):
        """Record an action taken."""
        valence = 0.4 if success else -0.2
        
        self.record_experience(
            ExperienceType.ACTION_TAKEN,
            content=f"Action: {action_name} - {'Success' if success else 'Failed'}",
            context={"action": action_name, "success": success, "outcome": outcome},
            emotional_valence=valence,
            importance=0.5 if success else 0.3,
            tags=["action", "success" if success else "failure"]
        )
    
    def record_social(self, agent_name: str, interaction_type: str,
                     content: str, sentiment: float = 0.0):
        """Record a social interaction with another agent."""
        self.record_experience(
            ExperienceType.SOCIAL_INTERACTION,
            content=f"Interacted with {agent_name}: {content[:100]}",
            context={
                "agent": agent_name,
                "interaction_type": interaction_type
            },
            emotional_valence=sentiment,
            importance=0.4,
            tags=["social", agent_name, interaction_type]
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERN RECOGNITION
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_patterns(self, experience: Experience):
        """Update pattern tracking based on experience."""
        # Track tag frequencies
        for tag in experience.tags:
            self.patterns[tag] = self.patterns.get(tag, 0) + 1
        
        # Build associations between tags
        if len(experience.tags) > 1:
            for i, tag1 in enumerate(experience.tags):
                if tag1 not in self.associations:
                    self.associations[tag1] = []
                for tag2 in experience.tags[i+1:]:
                    if tag2 not in self.associations[tag1]:
                        self.associations[tag1].append(tag2)
    
    def _update_emotional_state(self, experience: Experience):
        """Update emotional baseline based on experiences."""
        # Weighted update
        weight = 0.1 * experience.importance
        self.emotional_momentum = (
            0.9 * self.emotional_momentum + 
            0.1 * experience.emotional_valence
        )
        
        # Slowly shift baseline
        self.emotional_baseline = (
            0.99 * self.emotional_baseline + 
            0.01 * (0.5 + self.emotional_momentum)
        )
        
        # Clamp
        self.emotional_baseline = max(0.3, min(0.7, self.emotional_baseline))
    
    def _estimate_valence(self, text: str, emotion: str = None) -> float:
        """Estimate emotional valence of text."""
        text_lower = text.lower()
        
        # Emotion override
        if emotion:
            emotion_valences = {
                "happy": 0.7, "excited": 0.8, "grateful": 0.6,
                "sad": -0.5, "angry": -0.6, "frustrated": -0.4,
                "neutral": 0.0, "confused": -0.1
            }
            return emotion_valences.get(emotion, 0.0)
        
        # Text analysis
        positive = sum(1 for w in ["thanks", "great", "love", "awesome", "happy"] 
                      if w in text_lower)
        negative = sum(1 for w in ["hate", "bad", "terrible", "sad", "angry"] 
                      if w in text_lower)
        
        return (positive - negative) * 0.2
    
    def _estimate_importance(self, text: str) -> float:
        """Estimate importance of an experience."""
        # Personal = important
        if any(w in text.lower() for w in ["i feel", "i need", "help me", "please"]):
            return 0.8
        
        # Questions are medium
        if "?" in text:
            return 0.5
        
        # Short = less important
        if len(text) < 20:
            return 0.3
        
        return 0.5
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()
        
        # Topic detection
        topic_keywords = {
            "coding": ["code", "python", "function", "bug", "program"],
            "work": ["work", "job", "meeting", "deadline", "project"],
            "health": ["tired", "sleep", "exercise", "sick", "stress"],
            "entertainment": ["movie", "game", "music", "book", "show"],
            "personal": ["feel", "think", "believe", "want", "need"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(topic)
        
        return tags
    
    # ═══════════════════════════════════════════════════════════════════
    # INSIGHT SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════
    
    def synthesize_insights(self) -> List[Insight]:
        """Synthesize insights from recent experiences."""
        new_insights = []
        
        if len(self.recent_experiences) < 5:
            return new_insights
        
        # Group experiences by type
        by_type = {}
        for exp in self.recent_experiences:
            if exp.experience_type not in by_type:
                by_type[exp.experience_type] = []
            by_type[exp.experience_type].append(exp)
        
        # Conversation patterns
        conversations = by_type.get(ExperienceType.CONVERSATION, [])
        if len(conversations) >= 3:
            # Check for emotional trend
            avg_valence = sum(e.emotional_valence for e in conversations) / len(conversations)
            if avg_valence > 0.3:
                insight = Insight(
                    id=f"insight_{int(time.time() * 1000)}",
                    content="User seems to be in a positive mood recently",
                    source_experiences=[e.id for e in conversations[-3:]],
                    confidence=0.7,
                    timestamp=time.time()
                )
                new_insights.append(insight)
                self.insights.append(insight)
            elif avg_valence < -0.2:
                insight = Insight(
                    id=f"insight_{int(time.time() * 1000)}",
                    content="User might be going through a difficult time",
                    source_experiences=[e.id for e in conversations[-3:]],
                    confidence=0.6,
                    timestamp=time.time()
                )
                new_insights.append(insight)
                self.insights.append(insight)
        
        # Topic interest
        top_patterns = sorted(
            self.patterns.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        for pattern, count in top_patterns:
            if count >= 5 and not pattern.startswith("emotion:"):
                insight = Insight(
                    id=f"insight_{int(time.time() * 1000)}_{pattern}",
                    content=f"User frequently discusses: {pattern}",
                    source_experiences=[],
                    confidence=min(0.9, count / 10),
                    timestamp=time.time()
                )
                new_insights.append(insight)
                self.insights.append(insight)
        
        self._save_state()
        
        return new_insights
    
    def apply_insights_to_personality(self) -> List[PersonalityShift]:
        """Apply insights to personality system."""
        if not self.personality:
            return []
        
        shifts = []
        
        # Find unapplied insights
        unapplied = [i for i in self.insights if not i.applied and i.confidence > 0.6]
        
        for insight in unapplied[:3]:  # Limit changes per cycle
            # Determine personality adjustment
            if "positive mood" in insight.content:
                shift = self._adjust_personality("playfulness", 0.02, insight.content)
                if shift:
                    shifts.append(shift)
            
            elif "difficult time" in insight.content:
                shift = self._adjust_personality("warmth", 0.03, insight.content)
                if shift:
                    shifts.append(shift)
            
            elif "frequently discusses" in insight.content:
                # Increase curiosity for topics user cares about
                shift = self._adjust_personality("curiosity", 0.01, insight.content)
                if shift:
                    shifts.append(shift)
            
            insight.applied = True
        
        self._save_state()
        
        return shifts
    
    def _adjust_personality(self, trait: str, delta: float, 
                           reason: str) -> Optional[PersonalityShift]:
        """Adjust a personality trait."""
        if not self.personality or not hasattr(self.personality, 'traits'):
            return None
        
        try:
            old_value = getattr(self.personality.traits, trait, 0.5)
            new_value = max(0.3, min(0.9, old_value + delta))
            
            if hasattr(self.personality, 'adjust_trait'):
                self.personality.adjust_trait(trait, delta)
            
            shift = PersonalityShift(
                trait=trait,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                timestamp=time.time()
            )
            
            self.personality_shifts.append(shift)
            
            logger.info(f"Personality shift: {trait} {old_value:.2f} -> {new_value:.2f}")
            
            return shift
            
        except Exception as e:
            logger.error(f"Could not adjust personality: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get learner status."""
        return {
            "total_experiences": len(self.experience_stream),
            "recent_experiences": len(self.recent_experiences),
            "insights": len(self.insights),
            "personality_shifts": len(self.personality_shifts),
            "emotional_baseline": self.emotional_baseline,
            "top_patterns": sorted(
                self.patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    def get_recent_insights(self, limit: int = 5) -> List[str]:
        """Get recent insights as strings."""
        return [i.content for i in self.insights[-limit:]]
    
    def get_personality_evolution(self) -> List[Dict]:
        """Get history of personality changes."""
        return [
            {
                "trait": s.trait,
                "change": f"{s.old_value:.2f} -> {s.new_value:.2f}",
                "reason": s.reason[:50]
            }
            for s in self.personality_shifts[-10:]
        ]


# Singleton
_learner_instance = None

def get_episodic_learner(personality=None, memory=None) -> EpisodicLearner:
    """Get the global episodic learner."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = EpisodicLearner(personality, memory)
    return _learner_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    learner = EpisodicLearner()
    
    # Simulate experiences
    learner.record_conversation(
        "I'm feeling stressed about my project",
        "I understand. Let me help you!",
        detected_emotion="stressed"
    )
    
    learner.record_visual(
        "User at desk, looking at screen",
        emotions_detected=["focused", "slight_frown"]
    )
    
    learner.record_action("web_search", success=True, outcome="Found helpful info")
    
    print(f"Status: {learner.get_status()}")
    
    # Synthesize
    insights = learner.synthesize_insights()
    print(f"New insights: {[i.content for i in insights]}")
