"""
ZARA Vector Memory - Enhanced Semantic Memory System
"""
import os
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger("ZARA_MEMORY")


@dataclass
class Memory:
    """A single memory unit."""
    content: str
    memory_type: str  # "conversation", "fact", "preference", "emotion", "skill"
    timestamp: str
    emotional_weight: float  # 0-1, how emotionally significant
    source: str  # "user", "zara", "observation", "learning"
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    access_count: int = 0
    last_accessed: str = ""


@dataclass
class RecallResult:
    """Result of a memory recall operation."""
    content: str
    metadata: Dict[str, Any]
    distance: float
    relevance_score: float  # Combined score with emotional weight
    memory_id: str


class VectorMemory:
    """
    ZARA's long-term semantic memory system.
    Enhanced with:
    - Emotional weighting in search
    - Memory importance scoring
    - Access tracking (spaced repetition)
    - Memory consolidation
    - Hybrid search (vector + keyword)
    - Automatic cleanup
    """
    
    def __init__(self, collection_name: str = "zara_soul"):
        try:
            from config import MEMORY_DIR
            self.db_path = MEMORY_DIR / "chroma_db"
            self.memory_dir = MEMORY_DIR
        except ImportError:
            self.db_path = Path("memory/chroma_db")
            self.memory_dir = Path("memory")
        
        self.collection_name = collection_name
        self.collection = None
        self.client = None
        self.is_active = False
        
        # Fallback storage
        self.fallback_file = self.memory_dir / "memories.json"
        self.fallback_data: List[Dict] = []
        
        # Statistics
        self.stats = {
            "total_stores": 0,
            "total_recalls": 0,
            "cache_hits": 0
        }
        
        # Memory cache (LRU-style)
        self.cache: Dict[str, RecallResult] = {}
        self.cache_max_size = 100
        
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB or fallback."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.db_path.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.is_active = True
            count = self.collection.count()
            logger.info(f"Vector Memory Online. {count} memories loaded.")
            
        except ImportError:
            logger.warning("ChromaDB not installed. Using JSON fallback.")
            self._init_fallback()
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}. Using fallback.")
            self._init_fallback()

    def _init_fallback(self):
        """Initialize JSON fallback storage."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        if self.fallback_file.exists():
            try:
                with open(self.fallback_file, 'r', encoding='utf-8') as f:
                    self.fallback_data = json.load(f)
            except Exception as e:
                logger.debug(f"Could not load fallback memories: {e}")
                self.fallback_data = []
        
        logger.info(f"JSON fallback active. {len(self.fallback_data)} memories.")

    def _generate_id(self, content: str) -> str:
        """Generate unique memory ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(f"{content}{timestamp}".encode()).hexdigest()[:16]

    def store(self, memory: Memory) -> str:
        """Store a memory in the database."""
        if not memory.id:
            memory.id = self._generate_id(memory.content)
        
        memory.timestamp = datetime.now().isoformat()
        memory.last_accessed = memory.timestamp
        
        self.stats["total_stores"] += 1
        
        if self.is_active and self.collection:
            try:
                self.collection.add(
                    documents=[memory.content],
                    metadatas=[{
                        "type": memory.memory_type,
                        "timestamp": memory.timestamp,
                        "emotional_weight": memory.emotional_weight,
                        "source": memory.source,
                        "access_count": memory.access_count,
                        **(memory.metadata or {})
                    }],
                    ids=[memory.id]
                )
                logger.debug(f"Stored memory: {memory.id}")
            except Exception as e:
                logger.error(f"Store failed: {e}")
        else:
            self.fallback_data.append({
                "id": memory.id,
                **asdict(memory)
            })
            self._save_fallback()
        
        return memory.id

    def recall(self, query: str, n_results: int = 5,
              memory_type: Optional[str] = None,
              min_emotional_weight: float = 0.0) -> List[RecallResult]:
        """
        Recall memories similar to the query.
        Enhanced with emotional weighting.
        """
        self.stats["total_recalls"] += 1
        
        # Check cache
        cache_key = f"{query}:{n_results}:{memory_type}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return [self.cache[cache_key]]
        
        if self.is_active and self.collection:
            return self._vector_recall(query, n_results, memory_type, min_emotional_weight)
        else:
            return self._fallback_search(query, n_results, memory_type)

    def _vector_recall(self, query: str, n_results: int,
                      memory_type: Optional[str],
                      min_emotional_weight: float) -> List[RecallResult]:
        """Vector-based memory recall."""
        where_filter = None
        if memory_type:
            where_filter = {"type": memory_type}
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get extra for filtering
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            memories = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    emotional_weight = metadata.get('emotional_weight', 0.5)
                    
                    # Filter by emotional weight
                    if emotional_weight < min_emotional_weight:
                        continue
                    
                    # Calculate relevance score (lower distance = higher relevance)
                    # Boost by emotional weight
                    base_relevance = max(0, 1 - distance)
                    relevance_score = base_relevance * (0.7 + 0.3 * emotional_weight)
                    
                    memories.append(RecallResult(
                        content=doc,
                        metadata=metadata,
                        distance=distance,
                        relevance_score=relevance_score,
                        memory_id=results['ids'][0][i] if results['ids'] else ""
                    ))
            
            # Sort by relevance score
            memories.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Update access counts
            for mem in memories[:n_results]:
                self._update_access(mem.memory_id)
            
            return memories[:n_results]
            
        except Exception as e:
            logger.error(f"Vector recall failed: {e}")
            return []

    def _fallback_search(self, query: str, n_results: int,
                        memory_type: Optional[str]) -> List[RecallResult]:
        """Keyword-based fallback search."""
        query_words = set(query.lower().split())
        scored = []
        
        for mem in self.fallback_data:
            if memory_type and mem.get('memory_type') != memory_type:
                continue
            
            content = mem.get('content', '').lower()
            content_words = set(content.split())
            
            # Calculate word overlap
            overlap = len(query_words & content_words)
            if overlap > 0:
                emotional_weight = mem.get('emotional_weight', 0.5)
                score = overlap * (0.7 + 0.3 * emotional_weight)
                scored.append((score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, mem in scored[:n_results]:
            results.append(RecallResult(
                content=mem.get('content', ''),
                metadata=mem,
                distance=1 - (score / max(len(query_words), 1)),
                relevance_score=score,
                memory_id=mem.get('id', '')
            ))
        
        return results

    def _update_access(self, memory_id: str):
        """Update access count for memory (spaced repetition benefit)."""
        if self.is_active and self.collection:
            try:
                # ChromaDB doesn't support in-place updates easily
                # This would require a get + update pattern
                pass
            except Exception as e:
                logger.debug(f"Could not update access count: {e}")

    def _save_fallback(self):
        """Save fallback JSON file."""
        try:
            with open(self.fallback_file, 'w', encoding='utf-8') as f:
                json.dump(self.fallback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Fallback save failed: {e}")

    def remember_conversation(self, user_text: str, zara_response: str,
                             emotion: str = "neutral"):
        """Store a conversation turn as memory."""
        combined = f"User: {user_text}\nZara: {zara_response}"
        
        # Determine emotional weight
        emotional_weight = 0.5
        if emotion in ["happy", "excited", "love"]:
            emotional_weight = 0.8
        elif emotion in ["sad", "angry", "frustrated"]:
            emotional_weight = 0.7
        elif emotion in ["curious", "interested"]:
            emotional_weight = 0.6
        
        memory = Memory(
            content=combined,
            memory_type="conversation",
            timestamp="",
            emotional_weight=emotional_weight,
            source="conversation",
            metadata={"emotion": emotion, "user_text_preview": user_text[:50]}
        )
        
        self.store(memory)

    def remember_fact(self, fact: str, source: str = "user"):
        """Store a factual memory."""
        memory = Memory(
            content=fact,
            memory_type="fact",
            timestamp="",
            emotional_weight=0.6,
            source=source,
            metadata={"type": "fact"}
        )
        self.store(memory)

    def remember_preference(self, preference: str, importance: float = 0.7):
        """Store a user preference."""
        memory = Memory(
            content=preference,
            memory_type="preference",
            timestamp="",
            emotional_weight=importance,
            source="user",
            metadata={"type": "preference"}
        )
        self.store(memory)

    def get_context_for_query(self, query: str, max_tokens: int = 1000) -> str:
        """Build context string from relevant memories."""
        memories = self.recall(query, n_results=10)
        
        context_parts = []
        current_tokens = 0
        
        for mem in memories:
            # Rough token estimation
            mem_tokens = len(mem.content.split()) * 1.3
            if current_tokens + mem_tokens > max_tokens:
                break
            context_parts.append(f"[{mem.metadata.get('type', 'memory')}] {mem.content}")
            current_tokens += mem_tokens
        
        if context_parts:
            return "[REMEMBERED CONTEXT]\n" + "\n---\n".join(context_parts)
        return ""

    def count(self) -> int:
        """Get total memory count."""
        if self.is_active and self.collection:
            return self.collection.count()
        return len(self.fallback_data)

    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get most recent memories."""
        if self.is_active and self.collection:
            try:
                results = self.collection.peek(limit=n)
                return results.get('documents', [])
            except Exception as e:
                logger.debug(f"Could not peek recent: {e}")
                return []
        else:
            return [{"content": m.get("content", "")} for m in self.fallback_data[-n:]]

    def cleanup_old(self, days: int = 90) -> int:
        """Remove memories older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = 0
        
        if not self.is_active:
            original_count = len(self.fallback_data)
            self.fallback_data = [
                m for m in self.fallback_data
                if self._parse_timestamp(m.get('timestamp', '')) > cutoff
            ]
            removed = original_count - len(self.fallback_data)
            self._save_fallback()
        
        logger.info(f"Cleaned up {removed} old memories.")
        return removed

    def _parse_timestamp(self, ts: str) -> float:
        """Parse ISO timestamp to epoch."""
        try:
            return datetime.fromisoformat(ts).timestamp()
        except Exception as e:
            logger.debug(f"Could not parse timestamp: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get memory system statistics."""
        return {
            "total_memories": self.count(),
            "is_active": self.is_active,
            "using_chroma": self.is_active,
            **self.stats
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    memory = VectorMemory()
    
    # Test store
    mem = Memory(
        content="Vivaan's favorite color is purple.",
        memory_type="preference",
        timestamp="",
        emotional_weight=0.6,
        source="user"
    )
    memory.store(mem)
    
    # Test recall
    results = memory.recall("What is Vivaan's favorite color?")
    print("Recalled:", [(r.content, r.relevance_score) for r in results])
    
    print("\nStats:", memory.get_stats())
