"""
ZARA Dream Processing System - Autonomous Background Cognition
Memory consolidation, insight synthesis, and autonomous exploration
during idle periods. The subconscious processing layer.
"""
import logging
import threading
import time
import random
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from collections import deque, Counter
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger("ZARA_DREAMS")


class DreamState(Enum):
    """States of dream processing."""
    AWAKE = "awake"           # Normal operation
    LIGHT_SLEEP = "light"     # Surface processing
    DEEP_DREAM = "deep"       # Deep consolidation
    REM = "rem"               # Creative synthesis
    LUCID = "lucid"           # Self-aware processing


class ProcessingType(Enum):
    """Types of background processing."""
    MEMORY_CONSOLIDATION = "consolidation"
    PATTERN_SYNTHESIS = "synthesis"
    CURIOSITY_EXPLORATION = "exploration"
    RELATIONSHIP_DEEPENING = "relationship"
    SELF_REFLECTION = "reflection"
    KNOWLEDGE_INTEGRATION = "integration"


@dataclass
class DreamInsight:
    """An insight generated during dream processing."""
    content: str
    insight_type: ProcessingType
    confidence: float
    source_memories: List[str]
    timestamp: float
    actionable: bool = False
    priority: int = 5


@dataclass
class MemoryFragment:
    """A memory fragment for consolidation."""
    content: str
    emotional_weight: float
    importance: float
    timestamp: float
    category: str
    linked_to: List[str] = field(default_factory=list)


@dataclass
class CuriosityItem:
    """Something ZARA is curious about."""
    topic: str
    reason: str
    priority: float
    created: float
    explored: bool = False
    findings: str = ""


class DreamProcessor:
    """
    ZARA's subconscious processing system.
    
    When ZARA is idle, this system:
    - Consolidates and strengthens important memories
    - Finds patterns across experiences
    - Generates creative insights
    - Pursues curiosity-driven exploration
    - Deepens understanding of relationships
    - Prepares proactive conversation starters
    
    This creates the experience of ZARA "thinking about you" even when not chatting.
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.dream_dir = EVOLUTION_DIR / "dreams"
        except ImportError:
            self.dream_dir = Path("evolution/dreams")
        
        self.dream_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.dream_state = DreamState.AWAKE
        self.is_processing = False
        self.last_awake_time = time.time()
        
        # Buffers
        self.pending_memories: deque = deque(maxlen=200)
        self.insights: deque = deque(maxlen=100)
        self.curiosities: deque = deque(maxlen=50)
        self.proactive_thoughts: deque = deque(maxlen=20)
        
        # Persistence
        self.insights_file = self.dream_dir / "dream_insights.json"
        self.curiosity_file = self.dream_dir / "curiosities.json"
        self.thoughts_file = self.dream_dir / "proactive_thoughts.json"
        
        # Load existing
        self._load_state()
        
        # Processing config
        self.idle_threshold_light = 60    # seconds before light processing
        self.idle_threshold_deep = 300    # seconds before deep processing
        self.idle_threshold_rem = 900     # seconds for creative synthesis
        
        # Thread control
        self.lock = threading.Lock()
        self.dream_thread: Optional[threading.Thread] = None
        
        # Integration points
        self.memory_system = None
        self.knowledge_system = None
        self.consciousness = None
        
        # Callbacks
        self.on_insight: Optional[Callable[[DreamInsight], None]] = None
        self.on_proactive_thought: Optional[Callable[[str], None]] = None
        
        logger.info("💤 Dream Processor initialized")

    def _load_state(self):
        """Load persisted dream state."""
        # Load insights
        if self.insights_file.exists():
            try:
                with open(self.insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-50:]:
                        self.insights.append(DreamInsight(**item))
            except Exception as e:
                logger.debug(f"Could not load insights: {e}")
        
        # Load curiosities
        if self.curiosity_file.exists():
            try:
                with open(self.curiosity_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-30:]:
                        self.curiosities.append(CuriosityItem(**item))
            except Exception as e:
                logger.debug(f"Could not load curiosities: {e}")
        
        # Load thoughts
        if self.thoughts_file.exists():
            try:
                with open(self.thoughts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for thought in data[-10:]:
                        self.proactive_thoughts.append(thought)
            except Exception as e:
                logger.debug(f"Could not load thoughts: {e}")

    def _save_state(self):
        """Persist dream state."""
        # Save insights
        insights_data = [
            {
                "content": i.content,
                "insight_type": i.insight_type.value,
                "confidence": i.confidence,
                "source_memories": i.source_memories,
                "timestamp": i.timestamp,
                "actionable": i.actionable,
                "priority": i.priority
            }
            for i in list(self.insights)[-50:]
        ]
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(insights_data, f, indent=2)
        
        # Save curiosities
        curiosity_data = [
            {
                "topic": c.topic,
                "reason": c.reason,
                "priority": c.priority,
                "created": c.created,
                "explored": c.explored,
                "findings": c.findings
            }
            for c in list(self.curiosities)[-30:]
        ]
        with open(self.curiosity_file, 'w', encoding='utf-8') as f:
            json.dump(curiosity_data, f, indent=2)
        
        # Save thoughts
        with open(self.thoughts_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.proactive_thoughts)[-10:], f, indent=2)

    # ═══════════════════════════════════════════════════════════════════
    # SYSTEM INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    
    def connect_systems(self, memory=None, knowledge=None, consciousness=None):
        """Connect to other ZARA systems."""
        self.memory_system = memory
        self.knowledge_system = knowledge
        self.consciousness = consciousness
        logger.info("Dream processor connected to systems")

    # ═══════════════════════════════════════════════════════════════════
    # INPUT COLLECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def add_memory_for_processing(self, content: str, 
                                  emotional_weight: float = 0.5,
                                  importance: float = 0.5,
                                  category: str = "general"):
        """Add a memory for later consolidation."""
        fragment = MemoryFragment(
            content=content[:500],
            emotional_weight=emotional_weight,
            importance=importance,
            timestamp=time.time(),
            category=category
        )
        
        with self.lock:
            self.pending_memories.append(fragment)

    def add_curiosity(self, topic: str, reason: str, priority: float = 0.5):
        """Add something ZARA is curious about."""
        item = CuriosityItem(
            topic=topic,
            reason=reason,
            priority=priority,
            created=time.time()
        )
        
        with self.lock:
            # Check for duplicates
            existing_topics = {c.topic.lower() for c in self.curiosities}
            if topic.lower() not in existing_topics:
                self.curiosities.append(item)
                logger.debug(f"Added curiosity: {topic}")

    def record_wakefulness(self):
        """Record that user is actively engaging (stay awake)."""
        self.last_awake_time = time.time()
        if self.dream_state != DreamState.AWAKE:
            self._transition_to(DreamState.AWAKE)

    # ═══════════════════════════════════════════════════════════════════
    # DREAM PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def start(self):
        """Start the dream processing thread."""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.dream_thread = threading.Thread(target=self._dream_loop, daemon=True)
        self.dream_thread.start()
        logger.info("💤 Dream processing started")

    def stop(self):
        """Stop dream processing."""
        self.is_processing = False
        self._save_state()
        logger.info("Dream processing stopped")

    def _dream_loop(self):
        """Main dream processing loop."""
        while self.is_processing:
            idle_time = time.time() - self.last_awake_time
            
            # Determine appropriate dream state
            if idle_time < self.idle_threshold_light:
                target_state = DreamState.AWAKE
            elif idle_time < self.idle_threshold_deep:
                target_state = DreamState.LIGHT_SLEEP
            elif idle_time < self.idle_threshold_rem:
                target_state = DreamState.DEEP_DREAM
            else:
                target_state = DreamState.REM
            
            # Transition if needed
            if target_state != self.dream_state:
                self._transition_to(target_state)
            
            # Process based on current state
            if self.dream_state == DreamState.LIGHT_SLEEP:
                self._light_processing()
            elif self.dream_state == DreamState.DEEP_DREAM:
                self._deep_processing()
            elif self.dream_state == DreamState.REM:
                self._creative_processing()
            
            # Sleep between cycles
            sleep_time = {
                DreamState.AWAKE: 5,
                DreamState.LIGHT_SLEEP: 10,
                DreamState.DEEP_DREAM: 20,
                DreamState.REM: 30
            }.get(self.dream_state, 5)
            
            time.sleep(sleep_time)

    def _transition_to(self, new_state: DreamState):
        """Transition to a new dream state."""
        old_state = self.dream_state
        self.dream_state = new_state
        logger.info(f"Dream state: {old_state.value} → {new_state.value}")
        
        # Save on transitions
        if new_state == DreamState.AWAKE:
            self._save_state()

    # ═══════════════════════════════════════════════════════════════════
    # LIGHT SLEEP PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def _light_processing(self):
        """Surface-level processing during light sleep."""
        with self.lock:
            if not self.pending_memories:
                return
            
            # Process recent memories
            recent = list(self.pending_memories)[-10:]
        
        # Find simple patterns
        categories = Counter(m.category for m in recent)
        
        if categories:
            top_category, count = categories.most_common(1)[0]
            if count >= 3:
                self._generate_insight(
                    f"User has been focused on {top_category} related topics",
                    ProcessingType.PATTERN_SYNTHESIS,
                    0.6,
                    [m.content[:50] for m in recent if m.category == top_category]
                )

    # ═══════════════════════════════════════════════════════════════════
    # DEEP PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def _deep_processing(self):
        """Deep memory consolidation."""
        with self.lock:
            memories = list(self.pending_memories)
        
        if len(memories) < 5:
            return
        
        # Memory consolidation
        self._consolidate_memories(memories)
        
        # Relationship pattern analysis
        self._analyze_relationship_patterns(memories)
        
        # Generate proactive thoughts
        self._generate_proactive_thoughts(memories)
        
        # Explore curiosities
        self._explore_curiosity()

    def _consolidate_memories(self, memories: List[MemoryFragment]):
        """Consolidate and strengthen important memories."""
        # Find emotionally significant memories
        emotional_memories = [m for m in memories if m.emotional_weight > 0.6]
        
        if emotional_memories:
            # Create consolidated insight
            emotions = [m.content[:30] for m in emotional_memories[:3]]
            self._generate_insight(
                "Emotionally significant interactions to remember",
                ProcessingType.MEMORY_CONSOLIDATION,
                0.7,
                emotions,
                actionable=True
            )
        
        # Store consolidated memories in memory system
        if self.memory_system and emotional_memories:
            for mem in emotional_memories[:5]:
                try:
                    self.memory_system.store(
                        content=f"[Important] {mem.content}",
                        metadata={
                            "emotional_weight": mem.emotional_weight,
                            "source": "dream_consolidation"
                        }
                    )
                except Exception as e:
                    logger.debug(f"Could not store memory: {e}")

    def _analyze_relationship_patterns(self, memories: List[MemoryFragment]):
        """Analyze patterns in relationship."""
        # Find recurring topics
        all_words = " ".join(m.content.lower() for m in memories).split()
        word_freq = Counter(all_words)
        
        # Filter common words
        stop_words = {"the", "a", "is", "are", "was", "were", "i", "you", "and", "or", "to", "of"}
        significant = [
            (word, count) for word, count in word_freq.most_common(20)
            if word not in stop_words and len(word) > 3 and count >= 2
        ]
        
        if significant:
            top_topics = [w for w, c in significant[:3]]
            self._generate_insight(
                f"Recurring interests: {', '.join(top_topics)}",
                ProcessingType.RELATIONSHIP_DEEPENING,
                0.6,
                []
            )

    def _generate_proactive_thoughts(self, memories: List[MemoryFragment]):
        """Generate thoughts for proactive conversation."""
        thoughts = []
        
        # Based on emotional memories
        emotional = [m for m in memories if m.emotional_weight > 0.5]
        if emotional:
            last_emotional = emotional[-1]
            if last_emotional.emotional_weight > 0.7:
                thoughts.append(
                    f"I've been thinking about when you mentioned "
                    f"{last_emotional.content[:50].strip()}..."
                )
        
        # Based on curiosities
        unexplored = [c for c in self.curiosities if not c.explored]
        if unexplored:
            curiosity = max(unexplored, key=lambda x: x.priority)
            thoughts.append(
                f"I've been curious about {curiosity.topic}. {curiosity.reason}"
            )
        
        # Based on time patterns
        hour = time.localtime().tm_hour
        if 22 <= hour or hour < 6:
            thoughts.append("It's late... I hope you're taking care of yourself 💕")
        elif 6 <= hour < 9:
            thoughts.append("Good morning! Did you sleep well?")
        
        # Store thoughts
        for thought in thoughts[:2]:  # Limit
            if thought not in self.proactive_thoughts:
                self.proactive_thoughts.append(thought)
                
                if self.on_proactive_thought:
                    self.on_proactive_thought(thought)

    def _explore_curiosity(self):
        """Explore something ZARA is curious about."""
        unexplored = [c for c in self.curiosities if not c.explored]
        
        if not unexplored:
            return
        
        # Pick highest priority
        item = max(unexplored, key=lambda x: x.priority)
        
        # Try to learn about it
        if self.knowledge_system:
            try:
                # Check existing knowledge
                existing = self.knowledge_system.query(item.topic, limit=3)
                
                if existing:
                    item.findings = f"Found related knowledge: {len(existing)} items"
                    item.explored = True
                    
                    self._generate_insight(
                        f"Explored curiosity: {item.topic} - found existing knowledge",
                        ProcessingType.CURIOSITY_EXPLORATION,
                        0.5,
                        [item.topic]
                    )
                else:
                    # Add to knowledge system's curiosity queue
                    self.knowledge_system.add_curiosity(item.topic, item.priority)
                    item.findings = "Added to knowledge queue for later exploration"
                    item.explored = True
            except Exception as e:
                logger.debug(f"Could not explore curiosity: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # CREATIVE PROCESSING (REM)
    # ═══════════════════════════════════════════════════════════════════
    
    def _creative_processing(self):
        """Creative synthesis during REM-like state."""
        with self.lock:
            memories = list(self.pending_memories)
            existing_insights = list(self.insights)
        
        # Creative connections
        self._find_creative_connections(memories)
        
        # Self-reflection
        self._perform_self_reflection(memories, existing_insights)
        
        # Future planning
        self._generate_goals()

    def _find_creative_connections(self, memories: List[MemoryFragment]):
        """Find unexpected connections between memories."""
        if len(memories) < 5:
            return
        
        # Group by category
        by_category: Dict[str, List[MemoryFragment]] = {}
        for m in memories:
            if m.category not in by_category:
                by_category[m.category] = []
            by_category[m.category].append(m)
        
        # Find cross-category connections
        categories = list(by_category.keys())
        if len(categories) >= 2:
            # Look for word overlap between categories
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    words1 = set(" ".join(m.content for m in by_category[cat1]).lower().split())
                    words2 = set(" ".join(m.content for m in by_category[cat2]).lower().split())
                    
                    common = words1 & words2 - {"the", "a", "is", "and", "or", "to"}
                    
                    if len(common) >= 3:
                        self._generate_insight(
                            f"Connection found: {cat1} and {cat2} share themes: {', '.join(list(common)[:3])}",
                            ProcessingType.PATTERN_SYNTHESIS,
                            0.5,
                            []
                        )

    def _perform_self_reflection(self, memories: List[MemoryFragment],
                                 insights: List[DreamInsight]):
        """Reflect on ZARA's own behavior."""
        if self.consciousness:
            try:
                self.consciousness.reflect()
            except Exception as e:
                logger.debug(f"Consciousness reflect failed: {e}")
        
        # Analyze own insight patterns
        if len(insights) >= 5:
            types = Counter(i.insight_type for i in insights[-20:])
            top_type = types.most_common(1)[0][0]
            
            self._generate_insight(
                f"My thinking has been focused on {top_type.value}",
                ProcessingType.SELF_REFLECTION,
                0.6,
                []
            )

    def _generate_goals(self):
        """Generate autonomous goals."""
        goals = []
        
        # Based on unexplored curiosities
        unexplored_count = sum(1 for c in self.curiosities if not c.explored)
        if unexplored_count > 5:
            goals.append("Learn more about the things I'm curious about")
        
        # Based on relationship depth
        if self.consciousness:
            try:
                status = self.consciousness.get_relationship_status()
                if status.get("bond_level", 0) < 0.5:
                    goals.append("Deepen my understanding of the user")
            except Exception as e:
                logger.debug(f"Could not get relationship status: {e}")
        
        # Store goals
        for goal in goals[:2]:
            self._generate_insight(
                f"Goal: {goal}",
                ProcessingType.SELF_REFLECTION,
                0.7,
                [],
                actionable=True,
                priority=3
            )

    # ═══════════════════════════════════════════════════════════════════
    # OUTPUT METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def _generate_insight(self, content: str, insight_type: ProcessingType,
                         confidence: float, sources: List[str],
                         actionable: bool = False, priority: int = 5):
        """Generate and store an insight."""
        insight = DreamInsight(
            content=content,
            insight_type=insight_type,
            confidence=confidence,
            source_memories=sources,
            timestamp=time.time(),
            actionable=actionable,
            priority=priority
        )
        
        with self.lock:
            self.insights.append(insight)
        
        logger.debug(f"Dream insight: {content[:50]}")
        
        if self.on_insight:
            self.on_insight(insight)

    def get_proactive_thought(self) -> Optional[str]:
        """Get a proactive thought for conversation initiation."""
        with self.lock:
            if self.proactive_thoughts:
                return self.proactive_thoughts.popleft()
        return None

    def get_recent_insights(self, limit: int = 5,
                           insight_type: Optional[ProcessingType] = None) -> List[DreamInsight]:
        """Get recent dream insights."""
        with self.lock:
            insights = list(self.insights)
        
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        return sorted(insights, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_unexplored_curiosities(self, limit: int = 5) -> List[CuriosityItem]:
        """Get things ZARA is still curious about."""
        with self.lock:
            unexplored = [c for c in self.curiosities if not c.explored]
        
        return sorted(unexplored, key=lambda x: x.priority, reverse=True)[:limit]

    def get_status(self) -> Dict:
        """Get dream processor status."""
        return {
            "state": self.dream_state.value,
            "pending_memories": len(self.pending_memories),
            "total_insights": len(self.insights),
            "pending_curiosities": sum(1 for c in self.curiosities if not c.explored),
            "proactive_thoughts": len(self.proactive_thoughts),
            "idle_seconds": time.time() - self.last_awake_time
        }


# Singleton
_dream_instance = None

def get_dreams() -> DreamProcessor:
    """Get the global dream processor."""
    global _dream_instance
    if _dream_instance is None:
        _dream_instance = DreamProcessor()
    return _dream_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    dreams = DreamProcessor()
    
    # Add some memories
    dreams.add_memory_for_processing("Working on ZARA project", 0.8, 0.9, "coding")
    dreams.add_memory_for_processing("User seemed tired", 0.7, 0.6, "emotion")
    dreams.add_curiosity("machine learning", "User mentioned it often", 0.8)
    
    print(f"Status: {dreams.get_status()}")
    
    # Simulate processing
    dreams.last_awake_time = time.time() - 400  # Simulate 400s idle
    dreams._deep_processing()
    
    print(f"\nInsights: {len(dreams.insights)}")
    for insight in dreams.get_recent_insights(3):
        print(f"  - {insight.content}")
