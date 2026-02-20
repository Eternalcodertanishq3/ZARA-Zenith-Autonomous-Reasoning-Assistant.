"""
ZARA Advanced Memory Management
Intelligent memory lifecycle with tiered storage, 
importance weighting, and automatic consolidation.
"""
import logging
import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from pathlib import Path
from enum import Enum
import heapq

logger = logging.getLogger("ZARA_MEMORY_MGR")


class MemoryTier(Enum):
    """Memory storage tiers."""
    WORKING = "working"     # Active, fast access
    SHORT_TERM = "short"    # Recent memories
    LONG_TERM = "long"      # Consolidated, durable
    ARCHIVED = "archived"   # Old but important


class MemoryType(Enum):
    """Types of memories."""
    CONVERSATION = "conversation"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    PROCEDURAL = "procedural"


@dataclass
class ManagedMemory:
    """A memory with management metadata."""
    id: str
    content: str
    memory_type: MemoryType
    tier: MemoryTier
    importance: float          # 0-1, affects retention
    emotional_weight: float    # 0-1, emotional significance
    access_count: int = 0
    last_accessed: float = 0
    created_at: float = field(default_factory=time.time)
    consolidated: bool = False
    related_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class AdvancedMemoryManager:
    """
    ZARA's intelligent memory management system.
    
    Features:
    - Tiered storage (working → short-term → long-term → archived)
    - Importance-based retention
    - Automatic consolidation
    - Memory linking and clustering
    - Intelligent garbage collection
    - Memory strength decay
    
    This gives ZARA human-like memory dynamics.
    """
    
    def __init__(self):
        try:
            from config import MEMORY_DIR
            self.memory_dir = MEMORY_DIR / "managed"
        except ImportError:
            self.memory_dir = Path("memory/managed")
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory storage by tier
        self.memories: Dict[str, ManagedMemory] = {}
        self.tier_indices: Dict[MemoryTier, List[str]] = {
            tier: [] for tier in MemoryTier
        }
        
        # Access patterns
        self.access_log: deque = deque(maxlen=500)
        
        # Configuration
        self.config = {
            "working_memory_limit": 20,      # Active memories
            "short_term_limit": 100,         # Recent memories
            "long_term_limit": 1000,         # Consolidated memories
            "archive_limit": 5000,           # Old important memories
            "min_importance_for_long": 0.4,
            "min_importance_for_archive": 0.6,
            "consolidation_interval": 3600,  # 1 hour
            "decay_rate": 0.01,              # Per hour
            "emotional_boost": 0.2           # Extra importance for emotional
        }
        
        # Background thread
        self.is_running = False
        self.management_thread: Optional[threading.Thread] = None
        
        # Persistence
        self._load_memories()
        
        self.lock = threading.Lock()
        
        logger.info("🧠 Advanced Memory Manager initialized")

    def _load_memories(self):
        """Load persisted memories."""
        memory_file = self.memory_dir / "memories.json"
        
        if memory_file.exists():
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    item['memory_type'] = MemoryType(item['memory_type'])
                    item['tier'] = MemoryTier(item['tier'])
                    mem = ManagedMemory(**item)
                    self.memories[mem.id] = mem
                    self.tier_indices[mem.tier].append(mem.id)
                    
                logger.info(f"Loaded {len(self.memories)} memories")
            except Exception as e:
                logger.warning(f"Could not load memories: {e}")

    def _save_memories(self):
        """Persist memories."""
        memory_file = self.memory_dir / "memories.json"
        
        data = []
        for mem in self.memories.values():
            data.append({
                "id": mem.id,
                "content": mem.content[:2000],
                "memory_type": mem.memory_type.value,
                "tier": mem.tier.value,
                "importance": mem.importance,
                "emotional_weight": mem.emotional_weight,
                "access_count": mem.access_count,
                "last_accessed": mem.last_accessed,
                "created_at": mem.created_at,
                "consolidated": mem.consolidated,
                "related_ids": mem.related_ids[:10],
                "metadata": {k: v for k, v in list(mem.metadata.items())[:5]}
            })
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════════
    # MEMORY LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════
    
    def start(self):
        """Start background memory management."""
        if self.is_running:
            return
        
        self.is_running = True
        self.management_thread = threading.Thread(
            target=self._management_loop, daemon=True
        )
        self.management_thread.start()
        logger.info("Memory management started")

    def stop(self):
        """Stop management and save."""
        self.is_running = False
        self._save_memories()

    def _management_loop(self):
        """Background memory management."""
        last_consolidation = time.time()
        last_decay = time.time()
        
        while self.is_running:
            now = time.time()
            
            # Consolidation
            if now - last_consolidation > self.config["consolidation_interval"]:
                self._consolidate_memories()
                last_consolidation = now
            
            # Decay
            if now - last_decay > 3600:  # Every hour
                self._apply_decay()
                last_decay = now
            
            # GC
            self._garbage_collect()
            
            # Save periodically
            self._save_memories()
            
            time.sleep(300)  # Every 5 minutes

    # ═══════════════════════════════════════════════════════════════════
    # MEMORY OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def store(self, content: str, memory_type: MemoryType,
             importance: float = 0.5, emotional_weight: float = 0.0,
             metadata: Dict = None) -> str:
        """Store a new memory."""
        memory_id = f"mem_{int(time.time() * 1000)}"
        
        # Emotional boost
        if emotional_weight > 0.3:
            importance = min(1.0, importance + self.config["emotional_boost"])
        
        memory = ManagedMemory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            tier=MemoryTier.WORKING,  # Start in working memory
            importance=importance,
            emotional_weight=emotional_weight,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.memories[memory_id] = memory
            self.tier_indices[MemoryTier.WORKING].append(memory_id)
            
            # Manage working memory limit
            self._manage_tier_limit(MemoryTier.WORKING)
        
        logger.debug(f"Stored memory: {memory_id}")
        return memory_id

    def retrieve(self, memory_id: str) -> Optional[ManagedMemory]:
        """Retrieve a memory by ID."""
        with self.lock:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                memory.access_count += 1
                memory.last_accessed = time.time()
                
                # Boost importance on access
                memory.importance = min(1.0, memory.importance + 0.05)
                
                self.access_log.append({
                    "id": memory_id,
                    "timestamp": time.time()
                })
                
                return memory
        return None

    def query_by_type(self, memory_type: MemoryType, 
                     limit: int = 10) -> List[ManagedMemory]:
        """Query memories by type."""
        results = []
        
        with self.lock:
            for mem in self.memories.values():
                if mem.memory_type == memory_type:
                    results.append(mem)
        
        # Sort by importance
        results.sort(key=lambda m: m.importance, reverse=True)
        return results[:limit]

    def query_recent(self, limit: int = 10) -> List[ManagedMemory]:
        """Get most recent memories."""
        with self.lock:
            memories = list(self.memories.values())
        
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:limit]

    def query_important(self, min_importance: float = 0.6,
                       limit: int = 10) -> List[ManagedMemory]:
        """Get important memories."""
        results = []
        
        with self.lock:
            for mem in self.memories.values():
                if mem.importance >= min_importance:
                    results.append(mem)
        
        results.sort(key=lambda m: m.importance, reverse=True)
        return results[:limit]

    def link_memories(self, id1: str, id2: str):
        """Link two related memories."""
        with self.lock:
            if id1 in self.memories and id2 in self.memories:
                if id2 not in self.memories[id1].related_ids:
                    self.memories[id1].related_ids.append(id2)
                if id1 not in self.memories[id2].related_ids:
                    self.memories[id2].related_ids.append(id1)

    def get_related(self, memory_id: str) -> List[ManagedMemory]:
        """Get memories related to a given memory."""
        results = []
        
        with self.lock:
            if memory_id in self.memories:
                for related_id in self.memories[memory_id].related_ids:
                    if related_id in self.memories:
                        results.append(self.memories[related_id])
        
        return results

    # ═══════════════════════════════════════════════════════════════════
    # MEMORY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def _manage_tier_limit(self, tier: MemoryTier):
        """Manage tier size limit by promoting/demoting."""
        limits = {
            MemoryTier.WORKING: self.config["working_memory_limit"],
            MemoryTier.SHORT_TERM: self.config["short_term_limit"],
            MemoryTier.LONG_TERM: self.config["long_term_limit"],
            MemoryTier.ARCHIVED: self.config["archive_limit"]
        }
        
        tier_ids = self.tier_indices[tier]
        limit = limits[tier]
        
        if len(tier_ids) <= limit:
            return
        
        # Find least important memories to demote
        tier_memories = [self.memories[mid] for mid in tier_ids if mid in self.memories]
        tier_memories.sort(key=lambda m: m.importance)
        
        to_demote = len(tier_ids) - limit
        
        for i in range(to_demote):
            mem = tier_memories[i]
            self._demote_memory(mem)

    def _demote_memory(self, memory: ManagedMemory):
        """Demote a memory to a lower tier (or delete)."""
        current_tier = memory.tier
        
        # Remove from current tier
        if memory.id in self.tier_indices[current_tier]:
            self.tier_indices[current_tier].remove(memory.id)
        
        # Determine next tier
        tier_order = [MemoryTier.WORKING, MemoryTier.SHORT_TERM, 
                     MemoryTier.LONG_TERM, MemoryTier.ARCHIVED]
        current_idx = tier_order.index(current_tier)
        
        if current_idx >= len(tier_order) - 1:
            # Already archived - check if should delete
            if memory.importance < 0.3:
                del self.memories[memory.id]
                logger.debug(f"Deleted low-importance memory: {memory.id}")
                return
        else:
            # Demote to next tier
            next_tier = tier_order[current_idx + 1]
            memory.tier = next_tier
            self.tier_indices[next_tier].append(memory.id)

    def _consolidate_memories(self):
        """Consolidate memories from working/short-term to long-term."""
        with self.lock:
            now = time.time()
            
            # Consolidate short-term memories older than 1 hour
            for mem_id in list(self.tier_indices[MemoryTier.SHORT_TERM]):
                if mem_id not in self.memories:
                    continue
                    
                mem = self.memories[mem_id]
                age_hours = (now - mem.created_at) / 3600
                
                if age_hours > 1 and not mem.consolidated:
                    if mem.importance >= self.config["min_importance_for_long"]:
                        self._promote_to_long_term(mem)
                    else:
                        self._demote_memory(mem)

    def _promote_to_long_term(self, memory: ManagedMemory):
        """Promote a memory to long-term storage."""
        # Remove from current tier
        if memory.id in self.tier_indices[memory.tier]:
            self.tier_indices[memory.tier].remove(memory.id)
        
        # Add to long-term
        memory.tier = MemoryTier.LONG_TERM
        memory.consolidated = True
        self.tier_indices[MemoryTier.LONG_TERM].append(memory.id)
        
        logger.debug(f"Consolidated memory to long-term: {memory.id}")

    def _apply_decay(self):
        """Apply importance decay to memories."""
        with self.lock:
            now = time.time()
            
            for mem in self.memories.values():
                # Decay based on time since last access
                hours_since_access = (now - mem.last_accessed) / 3600 if mem.last_accessed else 0
                
                if hours_since_access > 24:
                    decay = self.config["decay_rate"] * (hours_since_access / 24)
                    mem.importance = max(0.1, mem.importance - decay)

    def _garbage_collect(self):
        """Remove very low-importance memories."""
        with self.lock:
            to_delete = []
            
            for mem_id, mem in self.memories.items():
                if mem.importance < 0.1 and mem.tier == MemoryTier.ARCHIVED:
                    to_delete.append(mem_id)
            
            for mem_id in to_delete[:10]:  # Delete max 10 per cycle
                if mem_id in self.tier_indices[MemoryTier.ARCHIVED]:
                    self.tier_indices[MemoryTier.ARCHIVED].remove(mem_id)
                del self.memories[mem_id]
            
            if to_delete:
                logger.debug(f"GC deleted {len(to_delete)} memories")

    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_statistics(self) -> Dict:
        """Get memory statistics."""
        with self.lock:
            return {
                "total_memories": len(self.memories),
                "by_tier": {
                    tier.value: len(ids) 
                    for tier, ids in self.tier_indices.items()
                },
                "avg_importance": sum(m.importance for m in self.memories.values()) / max(1, len(self.memories))
            }

    def get_status(self) -> Dict:
        """Get system status."""
        stats = self.get_statistics()
        return {
            "is_running": self.is_running,
            **stats
        }


# Singleton
_memory_mgr = None

def get_memory_manager() -> AdvancedMemoryManager:
    """Get the global memory manager."""
    global _memory_mgr
    if _memory_mgr is None:
        _memory_mgr = AdvancedMemoryManager()
    return _memory_mgr


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    mgr = AdvancedMemoryManager()
    
    # Store some memories
    id1 = mgr.store(
        "User mentioned they love Python programming",
        MemoryType.SEMANTIC,
        importance=0.7
    )
    
    id2 = mgr.store(
        "Had a deep conversation about feelings",
        MemoryType.EMOTIONAL,
        importance=0.6,
        emotional_weight=0.8
    )
    
    # Link them
    mgr.link_memories(id1, id2)
    
    # Retrieve
    mem = mgr.retrieve(id1)
    if mem:
        print(f"Retrieved: {mem.content}")
        print(f"Related: {len(mem.related_ids)}")
    
    print(f"Stats: {mgr.get_statistics()}")
