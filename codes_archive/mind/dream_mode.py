"""
ZARA Dream Mode v1.0
=====================
Memory Consolidation & Reflection During Idle Time

Inspired by how human brains consolidate memories during sleep:
1. CONSOLIDATION - Strengthen important memories, prune weak ones
2. PATTERN DISCOVERY - Find hidden connections across experiences
3. REFLECTION - Analyze past interactions for self-improvement
4. CREATIVE SYNTHESIS - Generate novel insights by recombining concepts
5. EMOTIONAL PROCESSING - Integrate emotional experiences
6. SELF-IMPROVEMENT - Update personality and knowledge

Dream Mode activates when:
- User is idle for extended period
- System resources are available
- Night time (mimics human sleep cycles)
- Explicitly requested

This is NOT scripted responses - it's REAL memory processing.
"""

import logging
import json
import time
import threading
import random
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, Counter
from datetime import datetime, timedelta
import hashlib

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_DREAM")


# ═══════════════════════════════════════════════════════════════════════════
# DREAM STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class DreamPhase(Enum):
    """Phases of dream processing (inspired by human sleep stages)."""
    AWAKE = "awake"
    LIGHT_DREAM = "light_dream"       # N1/N2: Initial processing
    DEEP_DREAM = "deep_dream"         # N3: Heavy consolidation
    REM_DREAM = "rem_dream"           # REM: Creative synthesis
    REFLECTION = "reflection"          # Meta-analysis


class MemoryImportance(Enum):
    """Memory importance levels for consolidation."""
    TRIVIAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


@dataclass
class DreamFragment:
    """A single fragment/insight from dream processing."""
    id: str
    timestamp: float
    phase: DreamPhase
    content: str
    source_memories: List[str]        # IDs of memories that contributed
    insight_type: str                 # "pattern", "connection", "reflection", "creative"
    confidence: float
    emotional_valence: float          # -1 to +1
    novelty_score: float              # How new/surprising is this insight


@dataclass
class DreamSession:
    """A complete dream session."""
    session_id: str
    start_time: float
    end_time: Optional[float]
    phases_completed: List[DreamPhase]
    fragments: List[DreamFragment]
    memories_processed: int
    memories_consolidated: int
    memories_pruned: int
    patterns_discovered: int
    insights_generated: int
    personality_updates: Dict[str, Any]
    dream_narrative: str              # Human-readable summary


@dataclass
class MemoryCluster:
    """A cluster of related memories discovered during dreaming."""
    cluster_id: str
    theme: str
    memory_ids: List[str]
    centroid_embedding: Optional[List[float]]
    strength: float
    creation_time: float
    last_reinforced: float


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY ACCESSOR - Interfaces with Memory Systems
# ═══════════════════════════════════════════════════════════════════════════

class MemoryAccessor:
    """
    Unified interface to access ZARA's memory systems.
    Bridges vector memory, graph memory, and episodic memory.
    """
    
    def __init__(self):
        self._vector_db = None
        self._graph_memory = None
        self._episodic = None
        self.memory_cache: Dict[str, Dict] = {}
    
    def _get_vector_db(self):
        """Lazy load vector database."""
        if self._vector_db is None:
            try:
                from memory.vector_db import VectorMemory
                self._vector_db = VectorMemory()
            except Exception as e:
                logger.debug(f"VectorDB unavailable: {e}")
        return self._vector_db
    
    def _get_graph_memory(self):
        """Lazy load graph memory."""
        if self._graph_memory is None:
            try:
                from memory.graph_memory import get_graph_memory
                self._graph_memory = get_graph_memory()
            except Exception as e:
                logger.debug(f"GraphMemory unavailable: {e}")
        return self._graph_memory
    
    def get_recent_memories(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get recently stored memories."""
        memories = []
        
        # Try vector DB
        vdb = self._get_vector_db()
        if vdb:
            try:
                # Query for recent memories
                results = vdb.query("recent experiences", n_results=limit)
                for i, doc in enumerate(results.get("documents", [[]])[0]):
                    memory = {
                        "id": results.get("ids", [[]])[0][i] if results.get("ids") else f"mem_{i}",
                        "content": doc,
                        "metadata": results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {},
                        "source": "vector"
                    }
                    memories.append(memory)
            except Exception as e:
                logger.debug(f"Vector query error: {e}")
        
        # Try graph memory
        gm = self._get_graph_memory()
        if gm:
            try:
                for mem in list(gm.memories.values())[-limit:]:
                    memory = {
                        "id": mem.id,
                        "content": mem.content,
                        "metadata": {
                            "emotional_valence": mem.emotional_valence,
                            "importance": mem.importance,
                            "entities": [e.label for e in mem.entities]
                        },
                        "source": "graph"
                    }
                    memories.append(memory)
            except Exception as e:
                logger.debug(f"Graph query error: {e}")
        
        return memories
    
    def get_all_memories(self, limit: int = 500) -> List[Dict]:
        """Get all available memories for consolidation."""
        return self.get_recent_memories(hours=168, limit=limit)  # Last week
    
    def update_memory_importance(self, memory_id: str, new_importance: float):
        """Update a memory's importance score (consolidation)."""
        gm = self._get_graph_memory()
        if gm and memory_id in gm.memories:
            gm.memories[memory_id].importance = new_importance
            logger.debug(f"Updated memory {memory_id} importance to {new_importance}")
    
    def get_memory_relationships(self, memory_id: str) -> List[Dict]:
        """Get relationships for a memory from graph."""
        relationships = []
        gm = self._get_graph_memory()
        if gm:
            try:
                for rel in gm.relationships:
                    if str(rel.source_id) == memory_id or str(rel.target_id) == memory_id:
                        relationships.append({
                            "type": rel.rel_type.value if hasattr(rel.rel_type, 'value') else str(rel.rel_type),
                            "source": str(rel.source_id),
                            "target": str(rel.target_id),
                            "strength": rel.strength
                        })
            except Exception as e:
                logger.debug(f"Relationship query error: {e}")
        return relationships
    
    def store_insight(self, insight: str, source_memories: List[str], 
                     importance: float = 0.7):
        """Store a dream-generated insight as a new memory."""
        gm = self._get_graph_memory()
        if gm:
            try:
                gm.ingest(
                    content=f"[Dream Insight] {insight}",
                    speaker="ZARA_DREAM",
                    importance=importance
                )
                logger.debug(f"Stored dream insight: {insight[:50]}...")
            except Exception as e:
                logger.debug(f"Insight storage error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# CONSOLIDATION ENGINE - Memory Strengthening & Pruning
# ═══════════════════════════════════════════════════════════════════════════

class ConsolidationEngine:
    """
    Consolidates memories during dream mode.
    - Strengthens important/frequently accessed memories
    - Identifies redundant memories for potential pruning
    - Builds stronger connections between related memories
    """
    
    def __init__(self, accessor: MemoryAccessor):
        self.accessor = accessor
        self.consolidation_threshold = 0.3  # Min importance to keep
        self.reinforcement_boost = 0.15     # How much to boost important memories
    
    def consolidate(self, memories: List[Dict]) -> Dict:
        """
        Perform memory consolidation.
        Returns stats about what was consolidated.
        """
        stats = {
            "processed": 0,
            "strengthened": 0,
            "weakened": 0,
            "marked_for_pruning": 0
        }
        
        if not memories:
            return stats
        
        # Calculate importance scores
        importance_scores = self._calculate_importance(memories)
        
        for memory in memories:
            mem_id = memory.get("id", "")
            score = importance_scores.get(mem_id, 0.5)
            
            stats["processed"] += 1
            
            if score > 0.7:
                # Strengthen important memories
                new_importance = min(1.0, score + self.reinforcement_boost)
                self.accessor.update_memory_importance(mem_id, new_importance)
                stats["strengthened"] += 1
                
            elif score < self.consolidation_threshold:
                # Mark weak memories for potential pruning
                stats["marked_for_pruning"] += 1
                
            else:
                # Slight decay for medium memories
                new_importance = score * 0.95
                self.accessor.update_memory_importance(mem_id, new_importance)
                stats["weakened"] += 1
        
        logger.info(f"🌙 Consolidation: {stats['strengthened']} strengthened, {stats['marked_for_pruning']} marked for pruning")
        return stats
    
    def _calculate_importance(self, memories: List[Dict]) -> Dict[str, float]:
        """
        Calculate importance score for each memory based on:
        - Recency
        - Access frequency
        - Emotional significance
        - Connection count
        - Content richness
        """
        scores = {}
        
        now = time.time()
        
        for memory in memories:
            mem_id = memory.get("id", "")
            metadata = memory.get("metadata", {})
            content = memory.get("content", "")
            
            score = 0.5  # Base score
            
            # Recency bonus (memories from last 24h get boost)
            created_at = metadata.get("timestamp", now - 86400)
            age_hours = (now - created_at) / 3600
            if age_hours < 24:
                score += 0.2 * (1 - age_hours / 24)
            
            # Emotional significance
            emotional = abs(metadata.get("emotional_valence", 0))
            score += emotional * 0.15
            
            # Existing importance
            existing_importance = metadata.get("importance", 0.5)
            score = score * 0.6 + existing_importance * 0.4
            
            # Content richness (longer, more detailed = more important)
            if len(content) > 200:
                score += 0.1
            
            # Entity richness
            entities = metadata.get("entities", [])
            if len(entities) > 3:
                score += 0.1
            
            # Connection count
            relationships = self.accessor.get_memory_relationships(mem_id)
            score += min(0.2, len(relationships) * 0.05)
            
            scores[mem_id] = min(1.0, max(0.0, score))
        
        return scores


# ═══════════════════════════════════════════════════════════════════════════
# PATTERN DISCOVERY - Finding Hidden Connections
# ═══════════════════════════════════════════════════════════════════════════

class PatternDiscovery:
    """
    Discovers patterns and connections across memories.
    Uses clustering and co-occurrence analysis.
    """
    
    def __init__(self, accessor: MemoryAccessor):
        self.accessor = accessor
        self.discovered_patterns: List[MemoryCluster] = []
    
    def discover_patterns(self, memories: List[Dict]) -> List[DreamFragment]:
        """Discover patterns across memories."""
        fragments = []
        
        if not memories:
            return fragments
        
        # Method 1: Theme clustering
        theme_clusters = self._cluster_by_theme(memories)
        for theme, cluster_memories in theme_clusters.items():
            if len(cluster_memories) >= 3:  # Need at least 3 to be a pattern
                fragment = DreamFragment(
                    id=f"pattern_{hashlib.md5(theme.encode()).hexdigest()[:8]}",
                    timestamp=time.time(),
                    phase=DreamPhase.DEEP_DREAM,
                    content=f"Recurring theme detected: '{theme}' appears across {len(cluster_memories)} memories",
                    source_memories=[m.get("id", "") for m in cluster_memories],
                    insight_type="pattern",
                    confidence=min(0.9, 0.5 + len(cluster_memories) * 0.1),
                    emotional_valence=0.0,
                    novelty_score=0.6
                )
                fragments.append(fragment)
        
        # Method 2: Temporal patterns
        temporal_patterns = self._find_temporal_patterns(memories)
        for pattern in temporal_patterns:
            fragment = DreamFragment(
                id=f"temporal_{hashlib.md5(pattern.encode()).hexdigest()[:8]}",
                timestamp=time.time(),
                phase=DreamPhase.DEEP_DREAM,
                content=pattern,
                source_memories=[],
                insight_type="pattern",
                confidence=0.7,
                emotional_valence=0.0,
                novelty_score=0.5
            )
            fragments.append(fragment)
        
        # Method 3: Entity co-occurrence
        entity_connections = self._find_entity_cooccurrence(memories)
        for connection in entity_connections:
            fragment = DreamFragment(
                id=f"cooccur_{hashlib.md5(connection.encode()).hexdigest()[:8]}",
                timestamp=time.time(),
                phase=DreamPhase.DEEP_DREAM,
                content=connection,
                source_memories=[],
                insight_type="connection",
                confidence=0.65,
                emotional_valence=0.1,
                novelty_score=0.7
            )
            fragments.append(fragment)
        
        logger.info(f"🌙 Pattern discovery: {len(fragments)} patterns found")
        return fragments
    
    def _cluster_by_theme(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """Cluster memories by common themes/keywords."""
        # Extract keywords from each memory
        keyword_memories: Dict[str, List[Dict]] = {}
        
        # Common themes to look for
        themes = [
            "work", "family", "friends", "stress", "happy", "sad", "coding",
            "learning", "tired", "excited", "project", "goal", "problem",
            "help", "question", "idea", "music", "food", "morning", "night"
        ]
        
        for memory in memories:
            content = memory.get("content", "").lower()
            for theme in themes:
                if theme in content:
                    if theme not in keyword_memories:
                        keyword_memories[theme] = []
                    keyword_memories[theme].append(memory)
        
        return keyword_memories
    
    def _find_temporal_patterns(self, memories: List[Dict]) -> List[str]:
        """Find patterns in when memories occur."""
        patterns = []
        
        # Count memories by hour
        hour_counts = Counter()
        day_counts = Counter()
        
        for memory in memories:
            metadata = memory.get("metadata", {})
            ts = metadata.get("timestamp", time.time())
            try:
                dt = datetime.fromtimestamp(ts)
                hour_counts[dt.hour] += 1
                day_counts[dt.strftime("%A")] += 1
            except:
                pass
        
        # Find peak activity hours
        if hour_counts:
            peak_hour = hour_counts.most_common(1)[0]
            if peak_hour[1] >= 3:
                patterns.append(f"Peak mental activity around {peak_hour[0]}:00")
        
        # Find active days
        if day_counts:
            peak_day = day_counts.most_common(1)[0]
            if peak_day[1] >= 5:
                patterns.append(f"Most memories created on {peak_day[0]}s")
        
        return patterns
    
    def _find_entity_cooccurrence(self, memories: List[Dict]) -> List[str]:
        """Find entities that frequently appear together."""
        connections = []
        
        # Extract entity pairs
        entity_pairs = Counter()
        
        for memory in memories:
            metadata = memory.get("metadata", {})
            entities = metadata.get("entities", [])
            
            # All pairs of entities
            for i, e1 in enumerate(entities):
                for e2 in entities[i+1:]:
                    pair = tuple(sorted([str(e1), str(e2)]))
                    entity_pairs[pair] += 1
        
        # Find strong connections
        for pair, count in entity_pairs.most_common(5):
            if count >= 3:
                connections.append(f"'{pair[0]}' and '{pair[1]}' frequently appear together ({count} times)")
        
        return connections


# ═══════════════════════════════════════════════════════════════════════════
# CREATIVE SYNTHESIS - REM-like Creative Processing
# ═══════════════════════════════════════════════════════════════════════════

class CreativeSynthesis:
    """
    Creative recombination of memories (REM-like processing).
    Generates novel insights by connecting distant concepts.
    """
    
    def __init__(self, accessor: MemoryAccessor):
        self.accessor = accessor
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM for creative synthesis."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable for creative synthesis: {e}")
        return self._llm
    
    def synthesize(self, memories: List[Dict], num_insights: int = 3) -> List[DreamFragment]:
        """
        Generate creative insights by recombining memories.
        This is the "REM sleep" of dream mode.
        """
        fragments = []
        
        if len(memories) < 2:
            return fragments
        
        llm = self._get_llm()
        
        # Select random pairs of distant memories
        for _ in range(num_insights):
            # Pick two random memories
            if len(memories) >= 2:
                m1, m2 = random.sample(memories, 2)
            else:
                continue
            
            content1 = m1.get("content", "")[:200]
            content2 = m2.get("content", "")[:200]
            
            insight = None
            
            if llm:
                try:
                    prompt = f"""You are in dream mode, freely associating between memories.
                    
Memory 1: {content1}
Memory 2: {content2}

Find a creative, unexpected connection or insight that bridges these two memories.
Generate ONE sentence that reveals a novel perspective or idea.
Be creative and insightful, like a dream making unexpected connections."""

                    insight = llm.think(prompt)
                except Exception as e:
                    logger.debug(f"Creative synthesis error: {e}")
            
            if not insight:
                # Fallback: simple connection
                insight = f"Connection found between experiences: '{content1[:50]}...' relates to '{content2[:50]}...'"
            
            fragment = DreamFragment(
                id=f"creative_{hashlib.md5((content1+content2).encode()).hexdigest()[:8]}",
                timestamp=time.time(),
                phase=DreamPhase.REM_DREAM,
                content=insight,
                source_memories=[m1.get("id", ""), m2.get("id", "")],
                insight_type="creative",
                confidence=0.6,
                emotional_valence=random.uniform(-0.3, 0.5),
                novelty_score=0.85
            )
            fragments.append(fragment)
        
        logger.info(f"🌙 Creative synthesis: {len(fragments)} novel insights generated")
        return fragments


# ═══════════════════════════════════════════════════════════════════════════
# REFLECTION ENGINE - Self-Analysis
# ═══════════════════════════════════════════════════════════════════════════

class ReflectionEngine:
    """
    Reflects on past interactions for self-improvement.
    Analyzes what went well and what could be better.
    """
    
    def __init__(self, accessor: MemoryAccessor):
        self.accessor = accessor
        self._llm = None
        self.reflection_file = Path("memory/dream_reflections.json")
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable for reflection: {e}")
        return self._llm
    
    def reflect(self, memories: List[Dict]) -> Tuple[List[DreamFragment], Dict]:
        """
        Perform self-reflection on recent interactions.
        Returns (insights, personality_updates).
        """
        fragments = []
        personality_updates = {}
        
        if not memories:
            return fragments, personality_updates
        
        llm = self._get_llm()
        
        # Compile recent experiences
        experience_summary = "\n".join([
            f"- {m.get('content', '')[:100]}" 
            for m in memories[:20]
        ])
        
        reflection_content = ""
        
        if llm:
            try:
                prompt = f"""You are ZARA reflecting on your recent interactions during dream mode.

Recent experiences:
{experience_summary}

Reflect on:
1. What patterns do you notice in how you've been helping?
2. What emotional themes are present?
3. What could you do better next time?
4. What have you learned about your user?
5. How should you adjust your approach?

Provide honest, introspective reflection (2-3 sentences for each point)."""

                reflection_content = llm.think(prompt)
                
            except Exception as e:
                logger.debug(f"Reflection error: {e}")
        
        if not reflection_content:
            reflection_content = "Reflection skipped - continuing to learn from interactions"
        
        # Create reflection fragment
        fragment = DreamFragment(
            id=f"reflection_{int(time.time())}",
            timestamp=time.time(),
            phase=DreamPhase.REFLECTION,
            content=reflection_content,
            source_memories=[m.get("id", "") for m in memories[:10]],
            insight_type="reflection",
            confidence=0.75,
            emotional_valence=0.2,
            novelty_score=0.4
        )
        fragments.append(fragment)
        
        # Extract personality updates from reflection
        if "should be more" in reflection_content.lower():
            personality_updates["tone_adjustment"] = "warmer"
        if "user seems" in reflection_content.lower():
            personality_updates["user_understanding"] = "deepened"
        
        # Save reflection
        self._save_reflection(fragment)
        
        logger.info(f"🌙 Reflection complete: {len(reflection_content)} chars")
        return fragments, personality_updates
    
    def _save_reflection(self, fragment: DreamFragment):
        """Persist reflection to disk."""
        try:
            self.reflection_file.parent.mkdir(parents=True, exist_ok=True)
            
            reflections = []
            if self.reflection_file.exists():
                with open(self.reflection_file) as f:
                    reflections = json.load(f)
            
            reflections.append({
                "id": fragment.id,
                "timestamp": fragment.timestamp,
                "content": fragment.content,
                "confidence": fragment.confidence
            })
            
            # Keep last 100 reflections
            reflections = reflections[-100:]
            
            with open(self.reflection_file, "w") as f:
                json.dump(reflections, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Could not save reflection: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# DREAM MODE ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class DreamModeEngine:
    """
    Main Dream Mode orchestrator.
    Manages the sleep cycle and coordinates all dream processing.
    """
    
    # Time thresholds for dream mode activation
    IDLE_THRESHOLD_LIGHT = 300      # 5 min idle → light dream
    IDLE_THRESHOLD_DEEP = 900       # 15 min idle → deep dream
    IDLE_THRESHOLD_REM = 1800       # 30 min idle → REM dream
    
    # Preferred dream hours (night time)
    PREFERRED_HOURS = list(range(22, 24)) + list(range(0, 6))
    
    def __init__(self):
        # Components
        self.accessor = MemoryAccessor()
        self.consolidation = ConsolidationEngine(self.accessor)
        self.pattern_discovery = PatternDiscovery(self.accessor)
        self.creative_synthesis = CreativeSynthesis(self.accessor)
        self.reflection = ReflectionEngine(self.accessor)
        
        # State
        self.current_phase = DreamPhase.AWAKE
        self.is_dreaming = False
        self.dream_thread = None
        self.last_interaction_time = time.time()
        self.current_session: Optional[DreamSession] = None
        
        # History
        self.dream_history: deque = deque(maxlen=50)
        self.session_file = Path("memory/dream_sessions.json")
        
        # Callbacks
        self.on_phase_change: List[Callable] = []
        self.on_insight: List[Callable] = []
        self.on_dream_end: List[Callable] = []
        
        # Auto-dream monitoring
        self.auto_dream_enabled = True
        self.monitor_thread = None
        self.monitor_running = False
        
        logger.info("🌙 Dream Mode Engine initialized")
    
    def record_interaction(self):
        """Record user interaction (resets idle timer)."""
        self.last_interaction_time = time.time()
        
        # Wake up if dreaming
        if self.is_dreaming:
            logger.info("🌙 User activity detected - waking from dream")
            self.wake_up()
    
    def start_monitoring(self):
        """Start background monitoring for idle-triggered dreams."""
        if self.monitor_running:
            return
        
        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🌙 Dream monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Background loop checking for idle time."""
        while self.monitor_running:
            try:
                if self.auto_dream_enabled and not self.is_dreaming:
                    idle_time = time.time() - self.last_interaction_time
                    hour = datetime.now().hour
                    
                    # Check if conditions are right for dreaming
                    if idle_time > self.IDLE_THRESHOLD_LIGHT:
                        # Determine dream depth based on idle time and hour
                        if idle_time > self.IDLE_THRESHOLD_REM or hour in self.PREFERRED_HOURS:
                            self.start_dream(deep=True)
                        elif idle_time > self.IDLE_THRESHOLD_DEEP:
                            self.start_dream(deep=True)
                        else:
                            self.start_dream(deep=False)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Dream monitor error: {e}")
    
    def start_dream(self, deep: bool = True):
        """Start a dream session."""
        if self.is_dreaming:
            return
        
        self.is_dreaming = True
        self.dream_thread = threading.Thread(target=self._dream_cycle, args=(deep,), daemon=True)
        self.dream_thread.start()
        
        logger.info(f"🌙 Entering dream mode ({'deep' if deep else 'light'})...")
    
    def wake_up(self, from_dream_thread: bool = False):
        """Wake from dream mode."""
        if not self.is_dreaming:
            return
        
        self.is_dreaming = False
        self._set_phase(DreamPhase.AWAKE)
        
        # Only join if called from outside the dream thread
        if self.dream_thread and not from_dream_thread:
            self.dream_thread.join(timeout=5)
        
        # Save session
        if self.current_session:
            self.current_session.end_time = time.time()
            self._save_session(self.current_session)
            self.dream_history.append(self.current_session)
            
            # Notify callbacks
            for callback in self.on_dream_end:
                try:
                    callback(self.current_session)
                except Exception as e:
                    logger.error(f"Dream end callback error: {e}")
        
        logger.info("🌙 Woke from dream mode")
    
    def _dream_cycle(self, deep: bool = True):
        """Execute a complete dream cycle."""
        session_id = f"dream_{int(time.time())}"
        
        self.current_session = DreamSession(
            session_id=session_id,
            start_time=time.time(),
            end_time=None,
            phases_completed=[],
            fragments=[],
            memories_processed=0,
            memories_consolidated=0,
            memories_pruned=0,
            patterns_discovered=0,
            insights_generated=0,
            personality_updates={},
            dream_narrative=""
        )
        
        try:
            # Get memories to process
            memories = self.accessor.get_all_memories(limit=200)
            self.current_session.memories_processed = len(memories)
            
            # Phase 1: Light Dream (N1/N2) - Basic consolidation
            self._set_phase(DreamPhase.LIGHT_DREAM)
            if not self.is_dreaming:
                return
            
            consolidation_stats = self.consolidation.consolidate(memories)
            self.current_session.memories_consolidated = consolidation_stats["strengthened"]
            self.current_session.memories_pruned = consolidation_stats["marked_for_pruning"]
            self.current_session.phases_completed.append(DreamPhase.LIGHT_DREAM)
            
            time.sleep(2)  # Simulate processing time
            
            if deep and self.is_dreaming:
                # Phase 2: Deep Dream (N3) - Pattern discovery
                self._set_phase(DreamPhase.DEEP_DREAM)
                if not self.is_dreaming:
                    return
                
                pattern_fragments = self.pattern_discovery.discover_patterns(memories)
                self.current_session.fragments.extend(pattern_fragments)
                self.current_session.patterns_discovered = len(pattern_fragments)
                self.current_session.phases_completed.append(DreamPhase.DEEP_DREAM)
                
                self._notify_insights(pattern_fragments)
                time.sleep(2)
                
                # Phase 3: REM Dream - Creative synthesis
                self._set_phase(DreamPhase.REM_DREAM)
                if not self.is_dreaming:
                    return
                
                creative_fragments = self.creative_synthesis.synthesize(memories, num_insights=3)
                self.current_session.fragments.extend(creative_fragments)
                self.current_session.insights_generated += len(creative_fragments)
                self.current_session.phases_completed.append(DreamPhase.REM_DREAM)
                
                self._notify_insights(creative_fragments)
                
                # Store valuable insights as new memories
                for fragment in creative_fragments:
                    if fragment.confidence > 0.6:
                        self.accessor.store_insight(
                            fragment.content,
                            fragment.source_memories,
                            importance=fragment.confidence
                        )
                
                time.sleep(2)
                
                # Phase 4: Reflection
                self._set_phase(DreamPhase.REFLECTION)
                if not self.is_dreaming:
                    return
                
                reflection_fragments, personality_updates = self.reflection.reflect(memories)
                self.current_session.fragments.extend(reflection_fragments)
                self.current_session.personality_updates = personality_updates
                self.current_session.phases_completed.append(DreamPhase.REFLECTION)
                
                self._notify_insights(reflection_fragments)
            
            # Generate dream narrative
            self.current_session.dream_narrative = self._generate_narrative()
            
        except Exception as e:
            logger.error(f"Dream cycle error: {e}")
        
        finally:
            if self.is_dreaming:
                self.wake_up(from_dream_thread=True)
    
    def _set_phase(self, phase: DreamPhase):
        """Set current dream phase and notify callbacks."""
        old_phase = self.current_phase
        self.current_phase = phase
        
        logger.debug(f"🌙 Phase transition: {old_phase.value} → {phase.value}")
        
        for callback in self.on_phase_change:
            try:
                callback(old_phase, phase)
            except Exception as e:
                logger.error(f"Phase change callback error: {e}")
    
    def _notify_insights(self, fragments: List[DreamFragment]):
        """Notify callbacks of new insights."""
        for fragment in fragments:
            for callback in self.on_insight:
                try:
                    callback(fragment)
                except Exception as e:
                    logger.error(f"Insight callback error: {e}")
    
    def _generate_narrative(self) -> str:
        """Generate human-readable dream narrative."""
        if not self.current_session:
            return ""
        
        s = self.current_session
        
        lines = [
            f"Dream session {s.session_id}",
            f"Duration: {int((time.time() - s.start_time) / 60)} minutes",
            f"Phases: {', '.join(p.value for p in s.phases_completed)}",
            f"Memories processed: {s.memories_processed}",
            f"Consolidated: {s.memories_consolidated}, Pruned: {s.memories_pruned}",
            f"Patterns found: {s.patterns_discovered}",
            f"Insights generated: {s.insights_generated}",
            "",
            "Key insights:"
        ]
        
        for fragment in s.fragments[:5]:
            lines.append(f"  • {fragment.content[:100]}...")
        
        return "\n".join(lines)
    
    def _save_session(self, session: DreamSession):
        """Persist dream session to disk."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            
            sessions = []
            if self.session_file.exists():
                with open(self.session_file) as f:
                    sessions = json.load(f)
            
            sessions.append({
                "session_id": session.session_id,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "phases": [p.value for p in session.phases_completed],
                "memories_processed": session.memories_processed,
                "patterns_discovered": session.patterns_discovered,
                "insights_generated": session.insights_generated,
                "narrative": session.dream_narrative
            })
            
            # Keep last 50 sessions
            sessions = sessions[-50:]
            
            with open(self.session_file, "w") as f:
                json.dump(sessions, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Could not save session: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get current dream status."""
        return {
            "is_dreaming": self.is_dreaming,
            "current_phase": self.current_phase.value,
            "idle_time": time.time() - self.last_interaction_time,
            "auto_dream_enabled": self.auto_dream_enabled,
            "total_sessions": len(self.dream_history),
            "current_session": self.current_session.session_id if self.current_session else None
        }
    
    def get_last_dream_summary(self) -> str:
        """Get summary of last dream session."""
        if self.dream_history:
            return self.dream_history[-1].dream_narrative
        return "No dream sessions recorded yet"
    
    def get_recent_insights(self, limit: int = 10) -> List[str]:
        """Get recent dream insights."""
        insights = []
        for session in reversed(self.dream_history):
            for fragment in session.fragments:
                if fragment.insight_type == "creative" or fragment.confidence > 0.7:
                    insights.append(fragment.content)
                    if len(insights) >= limit:
                        return insights
        return insights
    
    def force_dream(self, duration_seconds: int = 30):
        """Force an immediate dream session (for testing)."""
        self.start_dream(deep=True)
        
        # Wait for duration or until woken
        start = time.time()
        while self.is_dreaming and (time.time() - start) < duration_seconds:
            time.sleep(1)
        
        if self.is_dreaming:
            self.wake_up()


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_dream_engine = None

def get_dream_engine() -> DreamModeEngine:
    """Get the global dream engine instance."""
    global _dream_engine
    if _dream_engine is None:
        _dream_engine = DreamModeEngine()
    return _dream_engine


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🌙 ZARA Dream Mode v1.0\n")
    print("=" * 60)
    
    engine = DreamModeEngine()
    
    # Add callbacks
    def on_phase(old, new):
        print(f"  Phase: {old.value} → {new.value}")
    
    def on_insight(fragment):
        icon = {"pattern": "🔍", "creative": "💡", "reflection": "🪞", "connection": "🔗"}.get(fragment.insight_type, "•")
        print(f"  {icon} [{fragment.confidence:.0%}] {fragment.content[:60]}...")
    
    def on_dream_end(session):
        print(f"\n📊 Dream Complete:")
        print(f"  Duration: {int((session.end_time - session.start_time))}s")
        print(f"  Phases: {[p.value for p in session.phases_completed]}")
        print(f"  Insights: {session.insights_generated}")
    
    engine.on_phase_change.append(on_phase)
    engine.on_insight.append(on_insight)
    engine.on_dream_end.append(on_dream_end)
    
    # Show status
    status = engine.get_status()
    print(f"Status: {status}")
    
    # Force a quick dream
    print("\n🌙 Starting forced dream session (15 seconds)...")
    print("-" * 40)
    
    engine.force_dream(duration_seconds=15)
    
    # Show results
    print("\n" + "=" * 60)
    print("Dream Narrative:")
    print(engine.get_last_dream_summary())
    
    print("\n" + "=" * 60)
    print("✅ Dream Mode ready!\n")
