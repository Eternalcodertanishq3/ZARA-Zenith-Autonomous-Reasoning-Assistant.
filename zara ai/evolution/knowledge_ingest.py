"""
ZARA Autonomous Knowledge System - World Understanding Engine
An intelligent, curious system that actively seeks knowledge,
understands context, and builds a coherent world model.
"""
import json
import logging
import threading
import time
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import queue

logger = logging.getLogger("ZARA_KNOWLEDGE")


class KnowledgeType(Enum):
    FACTUAL = "factual"           # Concrete facts
    CONCEPTUAL = "conceptual"     # Understanding concepts
    PROCEDURAL = "procedural"     # How to do things
    CONTEXTUAL = "contextual"     # Context-dependent knowledge
    RELATIONAL = "relational"     # Relationships between things
    EMOTIONAL = "emotional"       # Emotional understanding
    SKILL = "skill"               # Learned abilities


class SourceReliability(Enum):
    VERIFIED = 1.0
    TRUSTED = 0.8
    UNKNOWN = 0.5
    UNCERTAIN = 0.3


@dataclass
class KnowledgeFragment:
    """A single piece of knowledge."""
    content: str
    knowledge_type: KnowledgeType
    source: str
    confidence: float  # 0-1
    relevance: float   # 0-1, how relevant to user
    timestamp: str
    topics: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # IDs of related knowledge
    access_count: int = 0
    last_accessed: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class Concept:
    """A higher-level concept built from knowledge."""
    name: str
    description: str
    related_concepts: List[str]
    knowledge_ids: List[str]
    understanding_level: float  # 0-1
    created_at: str
    updated_at: str


class AutonomousKnowledgeSystem:
    """
    ZARA's autonomous world understanding system.
    
    Features:
    - Curiosity-driven learning: Actively seeks relevant knowledge
    - Semantic understanding: Builds concepts from fragments
    - Knowledge graphs: Connects information meaningfully
    - Contextual retrieval: Gets relevant knowledge for any situation
    - Self-organizing: Knowledge reorganizes for better access
    - Continuous learning: Never stops absorbing and integrating
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.knowledge_dir = EVOLUTION_DIR / "knowledge_base"
        except ImportError:
            self.knowledge_dir = Path("evolution/knowledge_base")
        
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.fragments_file = self.knowledge_dir / "knowledge_fragments.json"
        self.concepts_file = self.knowledge_dir / "concepts.json"
        self.index_file = self.knowledge_dir / "knowledge_index.json"
        self.curiosity_queue_file = self.knowledge_dir / "curiosity_queue.json"
        
        # In-memory structures
        self.fragments: Dict[str, KnowledgeFragment] = {}
        self.concepts: Dict[str, Concept] = {}
        self.topic_index: Dict[str, Set[str]] = defaultdict(set)  # topic -> fragment_ids
        self.word_index: Dict[str, Set[str]] = defaultdict(set)   # word -> fragment_ids
        
        # Processing
        self.processing_queue = queue.Queue()
        self.curiosity_queue: List[str] = []  # Topics ZARA wants to learn about
        self.is_running = False
        
        # Learning parameters
        self.curiosity_level = 0.7  # How actively to seek new knowledge
        self.integration_threshold = 3  # Fragments needed to form concept
        self.relevance_decay = 0.01  # How quickly old knowledge fades
        
        # Statistics
        self.stats = {
            "fragments_processed": 0,
            "concepts_formed": 0,
            "queries_served": 0,
            "last_learning": None
        }
        
        # Load existing knowledge
        self._load_all()
        
        logger.info(f"🧠 Knowledge System initialized: {len(self.fragments)} fragments, {len(self.concepts)} concepts")

    # ═══════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def _load_all(self):
        """Load all knowledge from disk."""
        self._load_fragments()
        self._load_concepts()
        self._load_curiosity()
        self._rebuild_indices()

    def _load_fragments(self):
        """Load knowledge fragments."""
        if self.fragments_file.exists():
            try:
                with open(self.fragments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for fid, fdata in data.items():
                        fdata['knowledge_type'] = KnowledgeType(fdata['knowledge_type'])
                        self.fragments[fid] = KnowledgeFragment(**fdata)
            except Exception as e:
                logger.error(f"Failed to load fragments: {e}")

    def _load_concepts(self):
        """Load concepts."""
        if self.concepts_file.exists():
            try:
                with open(self.concepts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cid, cdata in data.items():
                        self.concepts[cid] = Concept(**cdata)
            except Exception as e:
                logger.error(f"Failed to load concepts: {e}")

    def _load_curiosity(self):
        """Load curiosity queue."""
        if self.curiosity_queue_file.exists():
            try:
                with open(self.curiosity_queue_file, 'r', encoding='utf-8') as f:
                    self.curiosity_queue = json.load(f)
            except Exception as e:
                logger.debug(f"Could not load curiosity queue: {e}")
                self.curiosity_queue = []

    def _save_fragments(self):
        """Persist fragments."""
        data = {}
        for fid, fragment in self.fragments.items():
            data[fid] = {
                "content": fragment.content,
                "knowledge_type": fragment.knowledge_type.value,
                "source": fragment.source,
                "confidence": fragment.confidence,
                "relevance": fragment.relevance,
                "timestamp": fragment.timestamp,
                "topics": fragment.topics,
                "connections": fragment.connections,
                "access_count": fragment.access_count,
                "last_accessed": fragment.last_accessed,
                "metadata": fragment.metadata
            }
        
        with open(self.fragments_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_concepts(self):
        """Persist concepts."""
        data = {cid: {
            "name": c.name,
            "description": c.description,
            "related_concepts": c.related_concepts,
            "knowledge_ids": c.knowledge_ids,
            "understanding_level": c.understanding_level,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } for cid, c in self.concepts.items()}
        
        with open(self.concepts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_curiosity(self):
        """Save curiosity queue."""
        with open(self.curiosity_queue_file, 'w', encoding='utf-8') as f:
            json.dump(self.curiosity_queue[:50], f)

    def _rebuild_indices(self):
        """Rebuild search indices."""
        self.topic_index.clear()
        self.word_index.clear()
        
        for fid, fragment in self.fragments.items():
            # Topic index
            for topic in fragment.topics:
                self.topic_index[topic.lower()].add(fid)
            
            # Word index (for semantic search)
            words = set(fragment.content.lower().split())
            for word in words:
                if len(word) > 3:
                    self.word_index[word].add(fid)

    # ═══════════════════════════════════════════════════════════════════
    # KNOWLEDGE INGESTION
    # ═══════════════════════════════════════════════════════════════════
    
    def learn(self, content: str, source: str = "observation",
             knowledge_type: KnowledgeType = KnowledgeType.FACTUAL,
             confidence: float = 0.7,
             relevance: float = 0.5,
             topics: List[str] = None,
             metadata: Dict = None) -> str:
        """
        Learn a new piece of knowledge.
        Returns the fragment ID.
        """
        # Generate ID
        fragment_id = hashlib.sha256(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Extract topics if not provided
        if topics is None:
            topics = self._extract_topics(content)
        
        # Create fragment
        fragment = KnowledgeFragment(
            content=content,
            knowledge_type=knowledge_type,
            source=source,
            confidence=confidence,
            relevance=relevance,
            timestamp=datetime.now().isoformat(),
            topics=topics,
            metadata=metadata or {}
        )
        
        # Check for similar existing knowledge
        similar = self._find_similar(content)
        if similar:
            # Merge with existing
            existing = self.fragments[similar[0]]
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.access_count += 1
            existing.last_accessed = datetime.now().isoformat()
            fragment_id = similar[0]
        else:
            self.fragments[fragment_id] = fragment
            self._index_fragment(fragment_id, fragment)
        
        self.stats["fragments_processed"] += 1
        self.stats["last_learning"] = datetime.now().isoformat()
        
        # Try to form concepts
        self._try_concept_formation(topics)
        
        self._save_fragments()
        
        return fragment_id

    def learn_from_text(self, text: str, source: str = "document") -> List[str]:
        """Learn from a longer text by chunking and processing."""
        fragment_ids = []
        
        # Split into paragraphs/chunks
        chunks = self._chunk_text(text)
        
        for chunk in chunks:
            if len(chunk.strip()) > 50:
                fid = self.learn(
                    content=chunk.strip(),
                    source=source,
                    knowledge_type=KnowledgeType.FACTUAL,
                    confidence=0.6
                )
                fragment_ids.append(fid)
        
        return fragment_ids

    def learn_from_file(self, path: Path) -> List[str]:
        """Learn from a file."""
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []
        
        try:
            if path.suffix in ['.txt', '.md']:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.learn_from_text(content, source=str(path))
            
            elif path.suffix == '.py':
                return self._learn_from_code(path)
            
            elif path.suffix == '.json':
                return self._learn_from_json(path)
            
            elif path.suffix == '.pdf':
                return self._learn_from_pdf(path)
            
            else:
                logger.warning(f"Unsupported file type: {path.suffix}")
                return []
                
        except Exception as e:
            logger.error(f"Error learning from {path}: {e}")
            return []

    def _learn_from_code(self, path: Path) -> List[str]:
        """Extract knowledge from code files."""
        fragment_ids = []
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract docstrings
        docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
        for doc in docstrings:
            if len(doc.strip()) > 30:
                fid = self.learn(
                    content=doc.strip(),
                    source=str(path),
                    knowledge_type=KnowledgeType.PROCEDURAL,
                    confidence=0.8,
                    topics=["programming", "documentation"]
                )
                fragment_ids.append(fid)
        
        # Extract function signatures and purposes
        functions = re.findall(r'def (\w+)\([^)]*\):\s*(?:"""([^"]*?)""")?', content)
        for func_name, doc in functions:
            if doc:
                fid = self.learn(
                    content=f"Function {func_name}: {doc.strip()}",
                    source=str(path),
                    knowledge_type=KnowledgeType.SKILL,
                    confidence=0.9,
                    topics=["programming", "python"]
                )
                fragment_ids.append(fid)
        
        return fragment_ids

    def _learn_from_json(self, path: Path) -> List[str]:
        """Learn from JSON files."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        content = json.dumps(data, indent=2)[:2000]
        
        return [self.learn(
            content=content,
            source=str(path),
            knowledge_type=KnowledgeType.FACTUAL,
            confidence=0.9,
            topics=["data", "structured"]
        )]

    def _learn_from_pdf(self, path: Path) -> List[str]:
        """Learn from PDF files."""
        try:
            import PyPDF2
            
            fragment_ids = []
            
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                for page in reader.pages[:20]:  # Limit pages
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:
                        ids = self.learn_from_text(text, source=str(path))
                        fragment_ids.extend(ids)
            
            return fragment_ids
            
        except ImportError:
            logger.warning("PyPDF2 not installed. PDF learning disabled.")
            return []

    def _chunk_text(self, text: str, max_chunk: int = 500) -> List[str]:
        """Chunk text into meaningful pieces."""
        # Split by paragraphs
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chunk:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content."""
        content_lower = content.lower()
        
        topic_keywords = {
            "programming": ["code", "function", "class", "variable", "python", "javascript"],
            "technology": ["ai", "machine learning", "computer", "software", "data"],
            "science": ["research", "study", "experiment", "theory", "hypothesis"],
            "emotions": ["feel", "happy", "sad", "love", "hate", "fear"],
            "relationships": ["friend", "family", "partner", "relationship"],
            "work": ["job", "career", "office", "boss", "project"],
            "health": ["health", "exercise", "sleep", "diet", "medical"],
            "entertainment": ["movie", "music", "game", "book", "show"],
            "learning": ["learn", "study", "understand", "know", "teach"]
        }
        
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                found_topics.append(topic)
        
        return found_topics or ["general"]

    def _find_similar(self, content: str, threshold: float = 0.7) -> List[str]:
        """Find similar existing knowledge."""
        content_words = set(content.lower().split())
        
        similar = []
        for fid, fragment in self.fragments.items():
            frag_words = set(fragment.content.lower().split())
            
            # Jaccard similarity
            if content_words and frag_words:
                intersection = len(content_words & frag_words)
                union = len(content_words | frag_words)
                similarity = intersection / union
                
                if similarity > threshold:
                    similar.append(fid)
        
        return similar

    def _index_fragment(self, fragment_id: str, fragment: KnowledgeFragment):
        """Index a fragment for search."""
        for topic in fragment.topics:
            self.topic_index[topic.lower()].add(fragment_id)
        
        words = set(fragment.content.lower().split())
        for word in words:
            if len(word) > 3:
                self.word_index[word].add(fragment_id)

    # ═══════════════════════════════════════════════════════════════════
    # CONCEPT FORMATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _try_concept_formation(self, topics: List[str]):
        """Try to form concepts from accumulated knowledge."""
        for topic in topics:
            topic_fragments = self.topic_index.get(topic.lower(), set())
            
            if len(topic_fragments) >= self.integration_threshold:
                if not self._concept_exists(topic):
                    self._form_concept(topic, list(topic_fragments))

    def _concept_exists(self, name: str) -> bool:
        """Check if concept exists."""
        return name.lower() in [c.name.lower() for c in self.concepts.values()]

    def _form_concept(self, name: str, fragment_ids: List[str]):
        """Form a new concept from fragments."""
        fragments = [self.fragments[fid] for fid in fragment_ids if fid in self.fragments]
        
        if not fragments:
            return
        
        # Synthesize description
        contents = [f.content[:100] for f in fragments[:5]]
        description = f"Understanding of {name} based on: " + "; ".join(contents)
        
        # Find related concepts
        related = set()
        for f in fragments:
            related.update(f.topics)
        related.discard(name)
        
        concept_id = hashlib.md5(name.encode()).hexdigest()[:12]
        
        concept = Concept(
            name=name,
            description=description[:500],
            related_concepts=list(related)[:10],
            knowledge_ids=fragment_ids[:20],
            understanding_level=min(1.0, len(fragment_ids) * 0.1),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.concepts[concept_id] = concept
        self.stats["concepts_formed"] += 1
        
        logger.info(f"💡 New concept formed: {name}")
        self._save_concepts()

    # ═══════════════════════════════════════════════════════════════════
    # KNOWLEDGE RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def query(self, question: str, max_results: int = 5) -> List[KnowledgeFragment]:
        """Query knowledge base with a question."""
        self.stats["queries_served"] += 1
        
        question_lower = question.lower()
        question_words = set(question_lower.split())
        
        # Score all fragments
        scored = []
        
        for fid, fragment in self.fragments.items():
            score = 0.0
            
            # Word overlap
            frag_words = set(fragment.content.lower().split())
            overlap = len(question_words & frag_words)
            score += overlap * 0.3
            
            # Topic match
            for topic in fragment.topics:
                if topic.lower() in question_lower:
                    score += 0.4
            
            # Recency boost
            try:
                age_days = (datetime.now() - datetime.fromisoformat(fragment.timestamp)).days
                recency_boost = max(0, 1 - age_days / 365)
                score += recency_boost * 0.1
            except Exception as e:
                logger.debug(f"Could not parse timestamp: {e}")
            
            # Confidence and relevance
            score += fragment.confidence * 0.1
            score += fragment.relevance * 0.1
            
            if score > 0:
                scored.append((score, fid, fragment))
        
        # Sort and return
        scored.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for _, fid, fragment in scored[:max_results]:
            fragment.access_count += 1
            fragment.last_accessed = datetime.now().isoformat()
            results.append(fragment)
        
        self._save_fragments()
        return results

    def get_context_for_topic(self, topic: str, max_tokens: int = 500) -> str:
        """Get relevant context for a topic."""
        fragments = self.query(topic, max_results=10)
        
        context_parts = []
        current_tokens = 0
        
        for fragment in fragments:
            frag_tokens = len(fragment.content.split())
            if current_tokens + frag_tokens > max_tokens:
                break
            context_parts.append(fragment.content)
            current_tokens += frag_tokens
        
        if context_parts:
            return "[ZARA'S KNOWLEDGE]\n" + "\n---\n".join(context_parts)
        return ""

    def get_concept_understanding(self, concept_name: str) -> Optional[Concept]:
        """Get ZARA's understanding of a concept."""
        for concept in self.concepts.values():
            if concept.name.lower() == concept_name.lower():
                return concept
        return None

    # ═══════════════════════════════════════════════════════════════════
    # CURIOSITY AND AUTONOMOUS LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def add_curiosity(self, topic: str, priority: float = 0.5):
        """Add something ZARA wants to learn about."""
        if topic not in self.curiosity_queue:
            self.curiosity_queue.append(topic)
            self.curiosity_queue = self.curiosity_queue[:50]  # Limit
            self._save_curiosity()
            logger.info(f"🔍 Added to curiosity queue: {topic}")

    def get_curious_about(self) -> Optional[str]:
        """Get what ZARA is most curious about right now."""
        if self.curiosity_queue:
            return self.curiosity_queue[0]
        return None

    def satisfy_curiosity(self, topic: str, learned_content: str):
        """Mark curiosity as satisfied with learned content."""
        if topic in self.curiosity_queue:
            self.curiosity_queue.remove(topic)
            self._save_curiosity()
        
        self.learn(
            content=learned_content,
            source="curiosity_fulfillment",
            knowledge_type=KnowledgeType.CONCEPTUAL,
            confidence=0.7,
            relevance=0.8,
            topics=[topic]
        )

    def generate_curiosity(self, context: str):
        """Generate new curiosity based on context."""
        # Extract potential learning opportunities
        unknown_concepts = self._find_unknown_concepts(context)
        
        for concept in unknown_concepts[:3]:
            self.add_curiosity(concept)

    def _find_unknown_concepts(self, context: str) -> List[str]:
        """Find concepts ZARA doesn't know about."""
        words = context.lower().split()
        
        # Filter to likely concepts (capitalized, longer words)
        potential = [w for w in words if len(w) > 5]
        
        # Check what we don't know
        unknown = []
        for word in potential:
            if word not in self.word_index or len(self.word_index[word]) < 2:
                unknown.append(word)
        
        return unknown

    # ═══════════════════════════════════════════════════════════════════
    # KNOWLEDGE MAINTENANCE
    # ═══════════════════════════════════════════════════════════════════
    
    def consolidate(self):
        """Consolidate and organize knowledge."""
        # Decay old, unused knowledge
        cutoff = datetime.now() - timedelta(days=90)
        
        to_remove = []
        for fid, fragment in self.fragments.items():
            try:
                frag_time = datetime.fromisoformat(fragment.last_accessed or fragment.timestamp)
                if frag_time < cutoff and fragment.access_count < 2:
                    fragment.relevance *= (1 - self.relevance_decay)
                    if fragment.relevance < 0.1:
                        to_remove.append(fid)
            except Exception as e:
                logger.debug(f"Could not parse fragment time: {e}")
        
        # Remove very stale fragments
        for fid in to_remove:
            del self.fragments[fid]
        
        if to_remove:
            logger.info(f"Consolidated {len(to_remove)} stale fragments.")
            self._rebuild_indices()
            self._save_fragments()

    def connect_knowledge(self, fragment_id1: str, fragment_id2: str):
        """Create a connection between two pieces of knowledge."""
        if fragment_id1 in self.fragments and fragment_id2 in self.fragments:
            f1 = self.fragments[fragment_id1]
            f2 = self.fragments[fragment_id2]
            
            if fragment_id2 not in f1.connections:
                f1.connections.append(fragment_id2)
            if fragment_id1 not in f2.connections:
                f2.connections.append(fragment_id1)
            
            self._save_fragments()

    def get_stats(self) -> Dict:
        """Get knowledge system statistics."""
        return {
            "total_fragments": len(self.fragments),
            "total_concepts": len(self.concepts),
            "topics_known": len(self.topic_index),
            "curiosity_queue_size": len(self.curiosity_queue),
            **self.stats
        }

    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def start_background_learning(self):
        """Start background knowledge processing."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._learning_loop, daemon=True)
        thread.start()
        logger.info("📚 Background knowledge processing started.")

    def stop_background_learning(self):
        """Stop background processing."""
        self.is_running = False

    def _learning_loop(self):
        """Background learning loop."""
        while self.is_running:
            # Process queued items
            try:
                item = self.processing_queue.get_nowait()
                self._process_queue_item(item)
            except queue.Empty:
                pass
            
            # Periodic consolidation
            self.consolidate()
            
            time.sleep(60)

    def _process_queue_item(self, item: Tuple):
        """Process a queued learning item."""
        item_type, data = item
        
        if item_type == "file":
            self.learn_from_file(Path(data))
        elif item_type == "text":
            self.learn_from_text(data)
        elif item_type == "url":
            # Future: web learning
            pass

    def queue_learning(self, item_type: str, data: str):
        """Queue something for learning."""
        self.processing_queue.put((item_type, data))



# Singleton instance
_knowledge_instance = None

def get_knowledge() -> AutonomousKnowledgeSystem:
    """Get the singleton instance of the Knowledge System."""
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = AutonomousKnowledgeSystem()
    return _knowledge_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    knowledge = AutonomousKnowledgeSystem()
    
    # Learn some things
    knowledge.learn(
        "Python is a high-level programming language known for its readability.",
        source="user_teaching",
        knowledge_type=KnowledgeType.FACTUAL,
        topics=["programming", "python"]
    )
    
    knowledge.learn(
        "Machine learning is a subset of AI that enables systems to learn from data.",
        source="conversation",
        knowledge_type=KnowledgeType.CONCEPTUAL,
        topics=["technology", "ai", "machine learning"]
    )
    
    knowledge.learn(
        "To debug Python code, use print statements or a debugger like pdb.",
        source="user_teaching",
        knowledge_type=KnowledgeType.PROCEDURAL,
        topics=["programming", "python", "debugging"]
    )
    
    # Query
    results = knowledge.query("How do I debug Python?")
    print("\n📚 Query Results:")
    for r in results:
        print(f"  - {r.content[:80]}... (conf: {r.confidence:.1f})")
    
    # Add curiosity
    knowledge.add_curiosity("neural networks")
    
    print(f"\n📊 Stats: {knowledge.get_stats()}")
