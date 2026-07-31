"""
ZARA GraphRAG Neural Memory v1.0
=================================
Infinite Neural Memory using Knowledge Graph + RAG architecture.

This replaces simple vector storage with:
- Knowledge Graph (entities + relationships)
- Entity Extraction (auto-detect people, places, concepts)
- Temporal Reasoning (when did X happen?)
- Multi-Hop Retrieval (traverse graph for related memories)
- Semantic Understanding (embeddings for similarity)

Architecture:
    User Message → Entity Extraction → Graph Update → Vector Store
                          ↓
    Query → Graph Traversal + Vector Search → Ranked Results
"""

import logging
import time
import json
import re
import hashlib
import threading
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

# Ensure parent directory is in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_GRAPH_MEMORY")


# ═══════════════════════════════════════════════════════════════════════════
# ENTITY & RELATIONSHIP TYPES
# ═══════════════════════════════════════════════════════════════════════════

class EntityType(Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "person"           # People (Vivaan, mom, friend)
    PLACE = "place"             # Locations (home, office, cafe)
    EVENT = "event"             # Events (meeting, birthday, project)
    CONCEPT = "concept"         # Abstract ideas (happiness, coding, learning)
    OBJECT = "object"           # Physical things (laptop, book, coffee)
    TIME = "time"               # Time references (yesterday, morning)
    EMOTION = "emotion"         # Emotional states (happy, stressed)
    TOPIC = "topic"             # Discussion topics (Python, debugging)
    MEMORY = "memory"           # Memory node (links to actual memory content)


class RelationType(Enum):
    """Types of relationships between entities."""
    # Person relationships
    KNOWS = "knows"
    LOVES = "loves"
    DISLIKES = "dislikes"
    WORKS_WITH = "works_with"
    FAMILY_OF = "family_of"
    
    # Action relationships
    MENTIONED = "mentioned"
    DISCUSSED = "discussed"
    ASKED_ABOUT = "asked_about"
    LEARNED = "learned"
    CREATED = "created"
    USES = "uses"
    
    # Causal relationships
    CAUSED = "caused"
    LED_TO = "led_to"
    RESULTED_IN = "resulted_in"
    
    # Temporal relationships
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    SAME_TIME = "same_time"
    
    # Emotional relationships
    FELT = "felt"
    TRIGGERED = "triggered"
    ASSOCIATED_WITH = "associated_with"
    
    # Structural relationships
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Entity:
    """A node in the knowledge graph."""
    id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_mentioned: float = field(default_factory=time.time)
    mention_count: int = 1
    importance: float = 0.5
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "properties": self.properties,
            "created_at": self.created_at,
            "last_mentioned": self.last_mentioned,
            "mention_count": self.mention_count,
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Entity":
        return cls(
            id=data["id"],
            name=data["name"],
            entity_type=EntityType(data["entity_type"]),
            properties=data.get("properties", {}),
            created_at=data.get("created_at", time.time()),
            last_mentioned=data.get("last_mentioned", time.time()),
            mention_count=data.get("mention_count", 1),
            importance=data.get("importance", 0.5)
        )


@dataclass
class Relationship:
    """An edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    last_activated: float = field(default_factory=time.time)
    activation_count: int = 1
    context: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        return f"{self.source_id}--{self.relation_type.value}-->{self.target_id}"
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "created_at": self.created_at,
            "last_activated": self.last_activated,
            "activation_count": self.activation_count,
            "context": self.context,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Relationship":
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data["relation_type"]),
            weight=data.get("weight", 1.0),
            created_at=data.get("created_at", time.time()),
            last_activated=data.get("last_activated", time.time()),
            activation_count=data.get("activation_count", 1),
            context=data.get("context", ""),
            properties=data.get("properties", {})
        )


@dataclass
class MemoryNode:
    """A memory stored in the graph."""
    id: str
    content: str
    memory_type: str
    timestamp: float
    emotional_valence: float = 0.0
    importance: float = 0.5
    entity_ids: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "emotional_valence": self.emotional_valence,
            "importance": self.importance,
            "entity_ids": self.entity_ids,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryNode":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=data["memory_type"],
            timestamp=data["timestamp"],
            emotional_valence=data.get("emotional_valence", 0.0),
            importance=data.get("importance", 0.5),
            entity_ids=data.get("entity_ids", []),
            metadata=data.get("metadata", {}),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", time.time())
        )


@dataclass
class QueryResult:
    """Result of a graph memory query."""
    memory: MemoryNode
    relevance_score: float
    path_length: int  # Hops from query entities
    related_entities: List[Entity]
    reasoning: str  # Why this was retrieved


# ═══════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════

class EntityExtractor:
    """
    Extracts entities and relationships from text.
    Uses pattern matching + optional LLM for complex cases.
    """
    
    def __init__(self):
        # Common entity patterns
        self.person_patterns = [
            r'\b(I|me|my|myself)\b',
            r'\b(you|your|yourself)\b', 
            r'\b(mom|dad|mother|father|brother|sister|friend|boss)\b',
            r'\b([A-Z][a-z]+)\b',  # Capitalized names
        ]
        
        self.emotion_keywords = {
            "happy": ["happy", "glad", "joyful", "excited", "great", "awesome", "wonderful"],
            "sad": ["sad", "unhappy", "depressed", "down", "blue", "miserable"],
            "stressed": ["stressed", "anxious", "worried", "overwhelmed", "pressure"],
            "angry": ["angry", "frustrated", "annoyed", "mad", "upset", "irritated"],
            "tired": ["tired", "exhausted", "sleepy", "drained", "fatigue"],
            "curious": ["curious", "interested", "wondering", "intrigued"],
            "grateful": ["grateful", "thankful", "appreciative", "blessed"]
        }
        
        self.topic_keywords = {
            "coding": ["code", "coding", "programming", "python", "javascript", "debug", "bug", "software"],
            "work": ["work", "job", "office", "meeting", "project", "deadline", "colleague"],
            "health": ["health", "exercise", "sleep", "diet", "doctor", "medicine", "sick"],
            "learning": ["learn", "study", "course", "tutorial", "understand", "knowledge"],
            "relationships": ["relationship", "love", "friend", "family", "partner"],
            "hobbies": ["game", "music", "movie", "book", "art", "sports", "hobby"]
        }
        
        self.time_patterns = [
            (r'\b(today|now|right now)\b', 0),
            (r'\b(yesterday)\b', -1),
            (r'\b(tomorrow)\b', 1),
            (r'\b(last week)\b', -7),
            (r'\b(this morning|morning)\b', 0),
            (r'\b(tonight|evening)\b', 0),
        ]
        
        self._llm = None
    
    def extract(self, text: str, context: Dict = None) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from text.
        
        Returns:
            (entities, relationships)
        """
        entities = []
        relationships = []
        context = context or {}
        
        text_lower = text.lower()
        
        # Extract persons
        persons = self._extract_persons(text)
        entities.extend(persons)
        
        # Extract emotions
        emotions = self._extract_emotions(text_lower)
        entities.extend(emotions)
        
        # Extract topics
        topics = self._extract_topics(text_lower)
        entities.extend(topics)
        
        # Extract time references
        times = self._extract_times(text_lower)
        entities.extend(times)
        
        # Build relationships
        relationships = self._infer_relationships(entities, text_lower, context)
        
        return entities, relationships
    
    def _extract_persons(self, text: str) -> List[Entity]:
        """Extract person entities."""
        entities = []
        
        # Check for "I/me/my" - indicates user
        if re.search(r'\b(I|me|my)\b', text, re.IGNORECASE):
            entities.append(Entity(
                id="user",
                name="User",
                entity_type=EntityType.PERSON,
                properties={"is_owner": True}
            ))
        
        # Check for "you/your" - indicates ZARA
        if re.search(r'\b(you|your)\b', text, re.IGNORECASE):
            entities.append(Entity(
                id="zara",
                name="ZARA",
                entity_type=EntityType.PERSON,
                properties={"is_self": True}
            ))
        
        # Extract family/role references
        family_roles = ["mom", "dad", "mother", "father", "brother", "sister", 
                       "friend", "boss", "colleague", "partner"]
        for role in family_roles:
            if role in text.lower():
                entities.append(Entity(
                    id=f"person_{role}",
                    name=role.capitalize(),
                    entity_type=EntityType.PERSON,
                    properties={"role": role}
                ))
        
        # Extract capitalized names (simple heuristic)
        names = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
        skip_words = {"The", "This", "That", "What", "When", "Where", "How", "Why",
                     "Can", "Could", "Would", "Should", "Will", "Have", "Has", "Had",
                     "Do", "Does", "Did", "But", "And", "For", "Not", "You", "Your"}
        for name in names:
            if name not in skip_words:
                entities.append(Entity(
                    id=f"person_{name.lower()}",
                    name=name,
                    entity_type=EntityType.PERSON
                ))
        
        return entities
    
    def _extract_emotions(self, text: str) -> List[Entity]:
        """Extract emotion entities."""
        entities = []
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(kw in text for kw in keywords):
                entities.append(Entity(
                    id=f"emotion_{emotion}",
                    name=emotion.capitalize(),
                    entity_type=EntityType.EMOTION,
                    properties={"intensity": 0.7}
                ))
        
        return entities
    
    def _extract_topics(self, text: str) -> List[Entity]:
        """Extract topic entities."""
        entities = []
        
        for topic, keywords in self.topic_keywords.items():
            if any(kw in text for kw in keywords):
                entities.append(Entity(
                    id=f"topic_{topic}",
                    name=topic.capitalize(),
                    entity_type=EntityType.TOPIC
                ))
        
        return entities
    
    def _extract_times(self, text: str) -> List[Entity]:
        """Extract time reference entities."""
        entities = []
        
        for pattern, day_offset in self.time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                ref_time = datetime.now() + timedelta(days=day_offset)
                entities.append(Entity(
                    id=f"time_{int(ref_time.timestamp())}",
                    name=ref_time.strftime("%Y-%m-%d"),
                    entity_type=EntityType.TIME,
                    properties={"day_offset": day_offset}
                ))
                break  # Only take first time reference
        
        return entities
    
    def _infer_relationships(self, entities: List[Entity], text: str, 
                            context: Dict) -> List[Relationship]:
        """Infer relationships between extracted entities."""
        relationships = []
        
        # Get entity IDs by type
        persons = [e for e in entities if e.entity_type == EntityType.PERSON]
        emotions = [e for e in entities if e.entity_type == EntityType.EMOTION]
        topics = [e for e in entities if e.entity_type == EntityType.TOPIC]
        times = [e for e in entities if e.entity_type == EntityType.TIME]
        
        # Person -> Emotion (FELT)
        user_entity = next((e for e in persons if e.id == "user"), None)
        if user_entity:
            for emotion in emotions:
                relationships.append(Relationship(
                    source_id=user_entity.id,
                    target_id=emotion.id,
                    relation_type=RelationType.FELT,
                    context=text[:100]
                ))
        
        # Person -> Topic (DISCUSSED/MENTIONED)
        for person in persons:
            for topic in topics:
                rel_type = RelationType.DISCUSSED if "?" in text else RelationType.MENTIONED
                relationships.append(Relationship(
                    source_id=person.id,
                    target_id=topic.id,
                    relation_type=rel_type,
                    context=text[:100]
                ))
        
        # Love/Like/Dislike patterns
        if "love" in text or "like" in text:
            for topic in topics:
                if user_entity:
                    relationships.append(Relationship(
                        source_id=user_entity.id,
                        target_id=topic.id,
                        relation_type=RelationType.LOVES,
                        context=text[:100]
                    ))
        
        if "hate" in text or "dislike" in text:
            for topic in topics:
                if user_entity:
                    relationships.append(Relationship(
                        source_id=user_entity.id,
                        target_id=topic.id,
                        relation_type=RelationType.DISLIKES,
                        context=text[:100]
                    ))
        
        # Time associations
        for time_entity in times:
            for emotion in emotions:
                relationships.append(Relationship(
                    source_id=emotion.id,
                    target_id=time_entity.id,
                    relation_type=RelationType.DURING
                ))
            for topic in topics:
                relationships.append(Relationship(
                    source_id=topic.id,
                    target_id=time_entity.id,
                    relation_type=RelationType.DURING
                ))
        
        return relationships


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH MEMORY ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class GraphMemory:
    """
    ZARA's GraphRAG Neural Memory System.
    
    Combines knowledge graphs with vector retrieval for
    intelligent, relationship-aware memory.
    """
    
    def __init__(self, storage_dir: Path = None):
        # Storage paths
        if storage_dir is None:
            try:
                from config import MEMORY_DIR
                storage_dir = Path(MEMORY_DIR) / "graph"
            except:
                storage_dir = Path("memory/graph")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Graph storage files
        self.entities_file = self.storage_dir / "entities.json"
        self.relationships_file = self.storage_dir / "relationships.json"
        self.memories_file = self.storage_dir / "memories.json"
        
        # In-memory graph
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.memories: Dict[str, MemoryNode] = {}
        
        # Indexes for fast lookup
        self.entity_by_type: Dict[EntityType, Set[str]] = defaultdict(set)
        self.entity_by_name: Dict[str, str] = {}  # name -> id
        self.relationships_from: Dict[str, List[str]] = defaultdict(list)  # entity_id -> [rel_ids]
        self.relationships_to: Dict[str, List[str]] = defaultdict(list)
        self.memories_by_entity: Dict[str, List[str]] = defaultdict(list)  # entity_id -> [memory_ids]
        
        # Entity extractor
        self.extractor = EntityExtractor()
        
        # Optional vector store
        self._vector_store = None
        self._embedder = None
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load persisted state
        self._load_state()
        
        # Ensure core entities
        self._ensure_core_entities()
        
        logger.info(f"🧠 GraphRAG Memory initialized: {len(self.entities)} entities, "
                   f"{len(self.relationships)} relationships, {len(self.memories)} memories")
    
    def _ensure_core_entities(self):
        """Ensure core entities exist."""
        core = [
            Entity(id="user", name="User", entity_type=EntityType.PERSON,
                  properties={"is_owner": True}, importance=1.0),
            Entity(id="zara", name="ZARA", entity_type=EntityType.PERSON,
                  properties={"is_self": True}, importance=1.0),
        ]
        
        for entity in core:
            if entity.id not in self.entities:
                self._add_entity(entity)
    
    # ═══════════════════════════════════════════════════════════════════
    # STATE PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def _load_state(self):
        """Load graph from disk."""
        # Load entities
        if self.entities_file.exists():
            try:
                with open(self.entities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for eid, edata in data.items():
                        entity = Entity.from_dict(edata)
                        self.entities[eid] = entity
                        self.entity_by_type[entity.entity_type].add(eid)
                        self.entity_by_name[entity.name.lower()] = eid
            except Exception as e:
                logger.warning(f"Could not load entities: {e}")
        
        # Load relationships
        if self.relationships_file.exists():
            try:
                with open(self.relationships_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rid, rdata in data.items():
                        rel = Relationship.from_dict(rdata)
                        self.relationships[rid] = rel
                        self.relationships_from[rel.source_id].append(rid)
                        self.relationships_to[rel.target_id].append(rid)
            except Exception as e:
                logger.warning(f"Could not load relationships: {e}")
        
        # Load memories
        if self.memories_file.exists():
            try:
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mid, mdata in data.items():
                        mem = MemoryNode.from_dict(mdata)
                        self.memories[mid] = mem
                        for eid in mem.entity_ids:
                            self.memories_by_entity[eid].append(mid)
            except Exception as e:
                logger.warning(f"Could not load memories: {e}")
    
    def _save_state(self):
        """Persist graph to disk."""
        try:
            # Save entities
            with open(self.entities_file, 'w', encoding='utf-8') as f:
                json.dump({eid: e.to_dict() for eid, e in self.entities.items()}, 
                         f, indent=2)
            
            # Save relationships
            with open(self.relationships_file, 'w', encoding='utf-8') as f:
                json.dump({rid: r.to_dict() for rid, r in self.relationships.items()}, 
                         f, indent=2)
            
            # Save memories
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump({mid: m.to_dict() for mid, m in self.memories.items()}, 
                         f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save graph state: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # ENTITY & RELATIONSHIP MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def _add_entity(self, entity: Entity) -> str:
        """Add or update an entity."""
        with self.lock:
            if entity.id in self.entities:
                # Update existing
                existing = self.entities[entity.id]
                existing.mention_count += 1
                existing.last_mentioned = time.time()
                existing.importance = min(1.0, existing.importance + 0.05)
            else:
                # Add new
                self.entities[entity.id] = entity
                self.entity_by_type[entity.entity_type].add(entity.id)
                self.entity_by_name[entity.name.lower()] = entity.id
        
        return entity.id
    
    def _add_relationship(self, rel: Relationship) -> str:
        """Add or strengthen a relationship."""
        with self.lock:
            if rel.id in self.relationships:
                # Strengthen existing
                existing = self.relationships[rel.id]
                existing.activation_count += 1
                existing.last_activated = time.time()
                existing.weight = min(2.0, existing.weight + 0.1)
            else:
                # Add new
                self.relationships[rel.id] = rel
                self.relationships_from[rel.source_id].append(rel.id)
                self.relationships_to[rel.target_id].append(rel.id)
        
        return rel.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def find_entity(self, name: str) -> Optional[Entity]:
        """Find entity by name."""
        eid = self.entity_by_name.get(name.lower())
        return self.entities.get(eid) if eid else None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a type."""
        return [self.entities[eid] for eid in self.entity_by_type[entity_type]
                if eid in self.entities]
    
    def get_relationships(self, entity_id: str, 
                         direction: str = "both") -> List[Relationship]:
        """Get relationships for an entity."""
        rels = []
        
        if direction in ("out", "both"):
            for rid in self.relationships_from.get(entity_id, []):
                if rid in self.relationships:
                    rels.append(self.relationships[rid])
        
        if direction in ("in", "both"):
            for rid in self.relationships_to.get(entity_id, []):
                if rid in self.relationships:
                    rels.append(self.relationships[rid])
        
        return rels
    
    def has_relationship(self, source_id: str, target_id: str, 
                        relation_type: RelationType = None) -> bool:
        """Check if relationship exists."""
        for rid in self.relationships_from.get(source_id, []):
            rel = self.relationships.get(rid)
            if rel and rel.target_id == target_id:
                if relation_type is None or rel.relation_type == relation_type:
                    return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════
    # MEMORY INGESTION
    # ═══════════════════════════════════════════════════════════════════
    
    def ingest(self, content: str, memory_type: str = "conversation",
              emotional_valence: float = 0.0, importance: float = 0.5,
              metadata: Dict = None) -> str:
        """
        Ingest a new memory into the graph.
        
        1. Extract entities and relationships
        2. Update graph
        3. Create memory node linked to entities
        4. Persist
        
        Returns:
            Memory ID
        """
        metadata = metadata or {}
        
        # Extract entities and relationships
        entities, relationships = self.extractor.extract(content, metadata)
        
        # Add entities to graph
        entity_ids = []
        for entity in entities:
            eid = self._add_entity(entity)
            entity_ids.append(eid)
        
        # Add relationships
        for rel in relationships:
            self._add_relationship(rel)
        
        # Create memory node
        memory_id = f"mem_{hashlib.md5(content.encode()).hexdigest()[:12]}_{int(time.time())}"
        
        memory = MemoryNode(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            emotional_valence=emotional_valence,
            importance=importance,
            entity_ids=entity_ids,
            metadata=metadata
        )
        
        with self.lock:
            self.memories[memory_id] = memory
            for eid in entity_ids:
                self.memories_by_entity[eid].append(memory_id)
        
        # Persist
        self._save_state()
        
        logger.debug(f"Ingested memory: {len(entities)} entities, {len(relationships)} relationships")
        
        return memory_id
    
    def remember_conversation(self, user_text: str, zara_response: str,
                             emotion: str = None):
        """Convenience method for conversation memories."""
        # Ingest user message
        self.ingest(
            content=f"User: {user_text}",
            memory_type="user_message",
            emotional_valence=self._estimate_valence(emotion),
            importance=self._estimate_importance(user_text),
            metadata={"speaker": "user", "emotion": emotion}
        )
        
        # Ingest ZARA response
        self.ingest(
            content=f"ZARA: {zara_response}",
            memory_type="zara_response",
            importance=0.3,
            metadata={"speaker": "zara"}
        )
    
    def _estimate_valence(self, emotion: str) -> float:
        """Estimate emotional valence from emotion string."""
        if not emotion:
            return 0.0
        
        valence_map = {
            "happy": 0.8, "excited": 0.9, "grateful": 0.7,
            "neutral": 0.0,
            "sad": -0.6, "stressed": -0.5, "angry": -0.7, "tired": -0.3
        }
        return valence_map.get(emotion.lower(), 0.0)
    
    def _estimate_importance(self, text: str) -> float:
        """Estimate importance of text."""
        importance = 0.5
        
        # Questions are important
        if "?" in text:
            importance += 0.2
        
        # Personal statements
        if any(w in text.lower() for w in ["i love", "i hate", "i need", "help me"]):
            importance += 0.2
        
        # Emotional content
        if any(w in text.lower() for w in ["stressed", "worried", "excited", "sad"]):
            importance += 0.1
        
        return min(1.0, importance)
    
    # ═══════════════════════════════════════════════════════════════════
    # GRAPH TRAVERSAL & MULTI-HOP RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def traverse(self, start_entity_id: str, max_hops: int = 2,
                relation_types: List[RelationType] = None) -> List[Tuple[Entity, int]]:
        """
        Traverse graph from starting entity.
        
        Returns:
            List of (entity, hop_distance) tuples
        """
        visited = {start_entity_id: 0}
        queue = [(start_entity_id, 0)]
        results = []
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth < max_hops:
                # Get outgoing relationships
                for rid in self.relationships_from.get(current_id, []):
                    rel = self.relationships.get(rid)
                    if not rel:
                        continue
                    
                    # Filter by relation type if specified
                    if relation_types and rel.relation_type not in relation_types:
                        continue
                    
                    target_id = rel.target_id
                    if target_id not in visited:
                        visited[target_id] = depth + 1
                        queue.append((target_id, depth + 1))
                
                # Get incoming relationships
                for rid in self.relationships_to.get(current_id, []):
                    rel = self.relationships.get(rid)
                    if not rel:
                        continue
                    
                    if relation_types and rel.relation_type not in relation_types:
                        continue
                    
                    source_id = rel.source_id
                    if source_id not in visited:
                        visited[source_id] = depth + 1
                        queue.append((source_id, depth + 1))
        
        # Build results
        for eid, distance in visited.items():
            entity = self.entities.get(eid)
            if entity:
                results.append((entity, distance))
        
        return sorted(results, key=lambda x: x[1])
    
    def find_path(self, source_id: str, target_id: str, 
                 max_hops: int = 4) -> Optional[List[str]]:
        """Find shortest path between two entities."""
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_hops:
                continue
            
            # Check all connected entities
            neighbors = set()
            for rid in self.relationships_from.get(current_id, []):
                rel = self.relationships.get(rid)
                if rel:
                    neighbors.add(rel.target_id)
            
            for rid in self.relationships_to.get(current_id, []):
                rel = self.relationships.get(rid)
                if rel:
                    neighbors.add(rel.source_id)
            
            for neighbor in neighbors:
                if neighbor == target_id:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # GRAPHRAG QUERY
    # ═══════════════════════════════════════════════════════════════════
    
    def query(self, query_text: str, max_results: int = 5,
             max_hops: int = 2) -> List[QueryResult]:
        """
        GraphRAG query - combines graph traversal with semantic search.
        
        1. Extract entities from query
        2. Find matching entities in graph
        3. Traverse graph to find related entities
        4. Retrieve memories connected to all discovered entities
        5. Rank by relevance
        """
        results = []
        
        # 1. Extract entities from query
        query_entities, _ = self.extractor.extract(query_text)
        
        # 2. Find matching entities in graph
        matched_entities = []
        for qe in query_entities:
            # Try exact match
            if qe.id in self.entities:
                matched_entities.append(qe.id)
            # Try name match
            elif qe.name.lower() in self.entity_by_name:
                matched_entities.append(self.entity_by_name[qe.name.lower()])
        
        # Add user entity for personal queries
        if any(word in query_text.lower() for word in ["i", "my", "me"]):
            matched_entities.append("user")
        
        # 3. Traverse graph from matched entities
        all_related = {}
        for eid in matched_entities:
            traversed = self.traverse(eid, max_hops=max_hops)
            for entity, distance in traversed:
                if entity.id not in all_related or all_related[entity.id] > distance:
                    all_related[entity.id] = distance
        
        # 4. Retrieve memories connected to discovered entities
        candidate_memories = {}
        for eid, distance in all_related.items():
            for mid in self.memories_by_entity.get(eid, []):
                if mid not in candidate_memories:
                    candidate_memories[mid] = {"distance": distance, "entities": [eid]}
                else:
                    candidate_memories[mid]["entities"].append(eid)
                    candidate_memories[mid]["distance"] = min(
                        candidate_memories[mid]["distance"], distance
                    )
        
        # 5. Score and rank
        for mid, data in candidate_memories.items():
            memory = self.memories.get(mid)
            if not memory:
                continue
            
            # Calculate relevance score
            entity_count = len(data["entities"])
            hop_distance = data["distance"]
            recency = 1.0 / (1.0 + (time.time() - memory.timestamp) / 86400)  # Days
            
            relevance = (
                0.4 * (1.0 / (1.0 + hop_distance)) +  # Closer = better
                0.3 * min(1.0, entity_count / 3) +    # More entities = better
                0.2 * recency +                       # Recent = better
                0.1 * memory.importance               # Important = better
            )
            
            # Get related entities
            related = [self.entities[eid] for eid in data["entities"] 
                      if eid in self.entities]
            
            results.append(QueryResult(
                memory=memory,
                relevance_score=relevance,
                path_length=hop_distance,
                related_entities=related,
                reasoning=f"Found via {entity_count} entities, {hop_distance} hops away"
            ))
        
        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return results[:max_results]
    
    def get_context_for_query(self, query: str, max_tokens: int = 1000) -> str:
        """Build context string from query results for LLM."""
        results = self.query(query, max_results=5)
        
        if not results:
            return ""
        
        parts = ["[MEMORY CONTEXT]"]
        char_count = 0
        
        for result in results:
            memory_str = f"- {result.memory.content}"
            
            if char_count + len(memory_str) > max_tokens * 4:
                break
            
            parts.append(memory_str)
            char_count += len(memory_str)
        
        return "\n".join(parts)
    
    # ═══════════════════════════════════════════════════════════════════
    # TEMPORAL QUERIES
    # ═══════════════════════════════════════════════════════════════════
    
    def query_by_time(self, start_time: float = None, end_time: float = None,
                     limit: int = 10) -> List[MemoryNode]:
        """Query memories by time range."""
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = time.time()
        
        results = [
            mem for mem in self.memories.values()
            if start_time <= mem.timestamp <= end_time
        ]
        
        return sorted(results, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def query_today(self, limit: int = 20) -> List[MemoryNode]:
        """Get today's memories."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
        return self.query_by_time(start_time=today_start, limit=limit)
    
    def query_last_n_days(self, days: int, limit: int = 50) -> List[MemoryNode]:
        """Get memories from last N days."""
        start_time = time.time() - (days * 86400)
        return self.query_by_time(start_time=start_time, limit=limit)
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS & STATS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get graph memory status."""
        entity_counts = {et.value: len(ids) for et, ids in self.entity_by_type.items()}
        
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "total_memories": len(self.memories),
            "entities_by_type": entity_counts,
            "storage_dir": str(self.storage_dir)
        }
    
    def get_entity_summary(self) -> str:
        """Get human-readable entity summary."""
        lines = ["🧠 Knowledge Graph Summary", "=" * 40]
        
        for entity_type in EntityType:
            entities = self.get_entities_by_type(entity_type)
            if entities:
                names = [e.name for e in sorted(entities, key=lambda e: -e.mention_count)[:5]]
                lines.append(f"{entity_type.value.title()}: {', '.join(names)}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_graph_memory = None

def get_graph_memory() -> GraphMemory:
    """Get the global graph memory instance."""
    global _graph_memory
    if _graph_memory is None:
        _graph_memory = GraphMemory()
    return _graph_memory


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🧠 ZARA GraphRAG Neural Memory v1.0\n")
    print("=" * 60)
    
    graph = GraphMemory()
    
    # Test ingestion
    print("\n📝 Ingesting test memories...")
    
    graph.remember_conversation(
        "I'm really stressed about my Python project deadline",
        "I understand! Deadlines can be tough. Let me help you break it down.",
        emotion="stressed"
    )
    
    graph.remember_conversation(
        "I love coding but debugging is so frustrating",
        "Debugging is like being a detective! Want some tips?",
        emotion="frustrated"
    )
    
    graph.remember_conversation(
        "Yesterday I finished the main feature, feeling happy now!",
        "That's amazing! You should celebrate this win!",
        emotion="happy"
    )
    
    # Show status
    print("\n📊 Graph Status:")
    status = graph.get_status()
    print(f"  Entities: {status['total_entities']}")
    print(f"  Relationships: {status['total_relationships']}")
    print(f"  Memories: {status['total_memories']}")
    print(f"  By type: {status['entities_by_type']}")
    
    # Test query
    print("\n🔍 Testing GraphRAG Query...")
    
    query = "What do I feel about coding?"
    results = graph.query(query, max_results=3)
    
    print(f"\nQuery: '{query}'")
    print("-" * 40)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r.relevance_score:.2f}] {r.memory.content[:60]}...")
        print(f"   Path: {r.path_length} hops | Entities: {[e.name for e in r.related_entities]}")
    
    # Test entity summary
    print("\n" + graph.get_entity_summary())
    
    # Test context generation
    print("\n📄 Context for LLM:")
    context = graph.get_context_for_query("How is user feeling?")
    print(context[:500])
    
    print("\n" + "=" * 60)
    print("✅ GraphRAG Memory ready!")
