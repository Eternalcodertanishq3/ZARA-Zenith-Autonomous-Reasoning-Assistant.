"""
ZARA Unified Multimodal Perception System v1.0
===============================================
True multimodal fusion - not parallel streams, but UNIFIED PERCEPTION.

This creates a coherent perceptual experience by:
1. Converting all inputs to shared PERCEPTUAL TOKENS
2. JOINT ATTENTION across modalities (binding "that voice" to "that face")
3. Building a unified SCENE GRAPH with multimodal entities
4. Maintaining a MOMENT BUFFER of coherent perception snapshots

This is how humans perceive - not "I see + I hear + I read" but
"I experience THIS MOMENT with all my senses as ONE."
"""

import logging
import threading
import time
import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import deque
from enum import Enum
from datetime import datetime

logger = logging.getLogger("ZARA_UNIFIED_PERCEPTION")


# ═══════════════════════════════════════════════════════════════════════════════
# CORE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class Modality(Enum):
    """Sensory modalities."""
    VISION = "vision"
    AUDIO = "audio"
    TEXT = "text"
    TOUCH = "touch"        # Future: haptic feedback
    PROPRIOCEPTION = "proprioception"  # Future: body sense
    

class Salience(Enum):
    """How attention-grabbing something is."""
    CRITICAL = 5    # Danger, urgent
    HIGH = 4        # Important, novel
    NORMAL = 3      # Regular attention
    LOW = 2         # Background
    SUBLIMINAL = 1  # Barely registered


class EntityType(Enum):
    """Types of entities in the scene."""
    PERSON = "person"
    OBJECT = "object"
    SOUND = "sound"
    CONCEPT = "concept"
    LOCATION = "location"
    EVENT = "event"


@dataclass
class PerceptualToken:
    """
    Universal representation for ANY modality.
    
    The key insight: all perception can be represented as tokens
    with content, embedding, and attention weights.
    """
    id: str
    modality: Modality
    content: Any                    # Raw content (text, description, etc.)
    timestamp: float
    salience: Salience = Salience.NORMAL
    embedding: List[float] = field(default_factory=list)  # 128-dim semantic vector
    attention_weight: float = 1.0   # How much attention this gets
    bound_to: List[str] = field(default_factory=list)     # IDs of bound tokens
    metadata: Dict = field(default_factory=dict)
    confidence: float = 1.0
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class SceneEntity:
    """
    An entity in the unified scene with multimodal properties.
    
    Example: A person who we see (face), hear (voice), and know about (text).
    """
    id: str
    entity_type: EntityType
    name: str                       # Human-readable name
    modality_data: Dict[Modality, Any] = field(default_factory=dict)
    confidence: float = 1.0
    last_seen: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, str] = field(default_factory=dict)  # relation -> target_id


@dataclass
class Moment:
    """
    A coherent perception snapshot integrating ALL modalities.
    
    This is what consciousness experiences - not separate streams,
    but a unified "now" containing everything perceived.
    """
    id: str
    timestamp: float
    
    # Unified content
    tokens: List[PerceptualToken] = field(default_factory=list)
    entities: Dict[str, SceneEntity] = field(default_factory=dict)
    attention_focus: Optional[str] = None  # ID of focused entity/token
    
    # Synthesized understanding
    scene_description: str = ""         # Natural language scene summary
    emotional_tone: str = "neutral"     # Overall emotional atmosphere
    salient_features: List[str] = field(default_factory=list)
    
    # Cross-modal bindings
    bindings: Dict[str, Set[str]] = field(default_factory=dict)  # entity_id -> token_ids


# ═══════════════════════════════════════════════════════════════════════════════
# PERCEPTUAL TOKENIZER
# ═══════════════════════════════════════════════════════════════════════════════

class PerceptualTokenizer:
    """
    Converts raw sensory inputs into unified perceptual tokens.
    
    All modalities become tokens in a shared semantic space,
    enabling cross-modal comparison and binding.
    """
    
    def __init__(self):
        self._token_count = 0
        
        # Semantic keywords for embedding generation
        self._emotion_keywords = {
            "happy": [1.0, 0.8, 0.2, 0.0, 0.3],
            "sad": [0.0, 0.2, 0.8, 0.1, 0.7],
            "angry": [0.1, 0.9, 0.3, 0.9, 0.2],
            "calm": [0.5, 0.2, 0.1, 0.0, 0.1],
            "excited": [0.9, 0.9, 0.1, 0.3, 0.5],
            "neutral": [0.5, 0.5, 0.5, 0.2, 0.3],
            "focused": [0.4, 0.3, 0.1, 0.1, 0.8],
            "tired": [0.2, 0.1, 0.6, 0.0, 0.2],
        }
    
    def tokenize_vision(self, 
                       description: str,
                       objects: List[str] = None,
                       faces: List[Dict] = None,
                       emotion: Optional[str] = None,
                       attention_score: float = 0.5) -> List[PerceptualToken]:
        """Convert visual input to perceptual tokens."""
        tokens = []
        now = time.time()
        
        # Main scene token
        scene_token = PerceptualToken(
            id=self._gen_id("vis_scene"),
            modality=Modality.VISION,
            content=description,
            timestamp=now,
            salience=self._calculate_salience(attention_score),
            embedding=self._generate_embedding(description, "vision"),
            metadata={
                "type": "scene",
                "objects": objects or [],
                "emotion": emotion
            }
        )
        tokens.append(scene_token)
        
        # Object tokens
        for obj in (objects or []):
            obj_token = PerceptualToken(
                id=self._gen_id("vis_obj"),
                modality=Modality.VISION,
                content=obj,
                timestamp=now,
                salience=Salience.NORMAL,
                embedding=self._generate_embedding(obj, "object"),
                metadata={"type": "object", "parent_scene": scene_token.id}
            )
            tokens.append(obj_token)
        
        # Face tokens
        for face in (faces or []):
            face_token = PerceptualToken(
                id=self._gen_id("vis_face"),
                modality=Modality.VISION,
                content=f"Face: {face.get('emotion', 'neutral')}",
                timestamp=now,
                salience=Salience.HIGH,  # Faces are always salient
                embedding=self._generate_embedding(
                    face.get('emotion', 'neutral'), "face_emotion"
                ),
                metadata={
                    "type": "face",
                    "emotion": face.get("emotion"),
                    "confidence": face.get("confidence", 0.8),
                    "attention": face.get("attention", 0.5)
                }
            )
            tokens.append(face_token)
        
        return tokens
    
    def tokenize_audio(self,
                      transcription: str,
                      voice_emotion: Optional[str] = None,
                      speaker_id: Optional[str] = None,
                      volume: float = 0.5,
                      pitch: float = 0.5,
                      speaking_rate: float = 1.0) -> List[PerceptualToken]:
        """Convert audio input to perceptual tokens."""
        tokens = []
        now = time.time()
        
        # Calculate salience from audio features
        urgency = (speaking_rate - 0.8) + volume + abs(pitch - 0.5)
        salience = Salience.HIGH if urgency > 1.0 else Salience.NORMAL
        
        # Speech content token
        if transcription:
            speech_token = PerceptualToken(
                id=self._gen_id("aud_speech"),
                modality=Modality.AUDIO,
                content=transcription,
                timestamp=now,
                salience=salience,
                embedding=self._generate_embedding(transcription, "speech"),
                metadata={
                    "type": "speech",
                    "speaker_id": speaker_id,
                    "emotion": voice_emotion,
                    "volume": volume,
                    "pitch": pitch,
                    "rate": speaking_rate
                }
            )
            tokens.append(speech_token)
        
        # Voice emotion token (if detected)
        if voice_emotion:
            emotion_token = PerceptualToken(
                id=self._gen_id("aud_emotion"),
                modality=Modality.AUDIO,
                content=f"Voice emotion: {voice_emotion}",
                timestamp=now,
                salience=Salience.HIGH,
                embedding=self._generate_embedding(voice_emotion, "voice_emotion"),
                metadata={
                    "type": "voice_emotion",
                    "emotion": voice_emotion,
                    "speaker_id": speaker_id
                }
            )
            tokens.append(emotion_token)
        
        return tokens
    
    def tokenize_text(self,
                     text: str,
                     sentiment: float = 0.5,
                     topics: List[str] = None,
                     is_question: bool = False,
                     source: str = "user") -> List[PerceptualToken]:
        """Convert text input to perceptual tokens."""
        tokens = []
        now = time.time()
        
        # Determine salience
        salience = Salience.HIGH if is_question else Salience.NORMAL
        
        # Main text token
        text_token = PerceptualToken(
            id=self._gen_id("txt_content"),
            modality=Modality.TEXT,
            content=text,
            timestamp=now,
            salience=salience,
            embedding=self._generate_embedding(text, "text"),
            metadata={
                "type": "text_content",
                "sentiment": sentiment,
                "is_question": is_question,
                "topics": topics or [],
                "source": source
            }
        )
        tokens.append(text_token)
        
        # Topic tokens
        for topic in (topics or []):
            topic_token = PerceptualToken(
                id=self._gen_id("txt_topic"),
                modality=Modality.TEXT,
                content=topic,
                timestamp=now,
                salience=Salience.NORMAL,
                embedding=self._generate_embedding(topic, "topic"),
                metadata={"type": "topic", "parent_text": text_token.id}
            )
            tokens.append(topic_token)
        
        return tokens
    
    def _gen_id(self, prefix: str) -> str:
        """Generate unique token ID."""
        self._token_count += 1
        timestamp = int(time.time() * 1000)
        return f"{prefix}_{timestamp}_{self._token_count}"
    
    def _calculate_salience(self, score: float) -> Salience:
        """Convert attention score to salience level."""
        if score > 0.9:
            return Salience.CRITICAL
        if score > 0.7:
            return Salience.HIGH
        if score > 0.4:
            return Salience.NORMAL
        if score > 0.2:
            return Salience.LOW
        return Salience.SUBLIMINAL
    
    def _generate_embedding(self, content: str, context: str) -> List[float]:
        """
        Generate semantic embedding for content.
        
        In production, this would use a proper embedding model.
        For now, we use a deterministic hash-based approach.
        """
        # Create a 128-dimensional embedding
        embedding = [0.0] * 128
        
        if not content:
            return embedding
        
        # Base: hash-based embedding
        content_lower = content.lower()
        hash_bytes = hashlib.sha256(content_lower.encode()).digest()
        
        for i in range(min(128, len(hash_bytes))):
            embedding[i] = (hash_bytes[i] / 255.0) - 0.5
        
        # Add emotion-based components
        for emotion, weights in self._emotion_keywords.items():
            if emotion in content_lower:
                for i, w in enumerate(weights):
                    embedding[i] = embedding[i] * 0.5 + w * 0.5
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding


# ═══════════════════════════════════════════════════════════════════════════════
# JOINT ATTENTION MECHANISM
# ═══════════════════════════════════════════════════════════════════════════════

class JointAttentionMechanism:
    """
    Cross-modal attention that BINDS perceptions together.
    
    When you hear a voice and see a face, your brain binds them
    together as "that person speaking." This mechanism does the same.
    
    Key operations:
    1. BINDING: Connect tokens across modalities (voice + face = person)
    2. SPOTLIGHT: What should consciousness focus on right now?
    3. GATING: What should be filtered out (irrelevant/noisy)?
    """
    
    def __init__(self, binding_threshold: float = 0.6):
        self.binding_threshold = binding_threshold
        self.attention_spotlight: Optional[str] = None  # Current focus
        self.attention_history: deque = deque(maxlen=50)
        
        # Binding rules: (modality1, modality2, property_to_match)
        self.binding_rules = [
            (Modality.VISION, Modality.AUDIO, "emotion"),      # Matching emotions
            (Modality.VISION, Modality.AUDIO, "speaker_id"),    # Known speaker
            (Modality.AUDIO, Modality.TEXT, "content"),        # Speech matches text
        ]
    
    def compute_bindings(self, tokens: List[PerceptualToken]) -> Dict[str, Set[str]]:
        """
        Find cross-modal bindings between tokens.
        
        Returns mapping of token_id -> set of bound token_ids.
        """
        bindings: Dict[str, Set[str]] = {}
        
        # Group tokens by modality
        by_modality: Dict[Modality, List[PerceptualToken]] = {}
        for token in tokens:
            if token.modality not in by_modality:
                by_modality[token.modality] = []
            by_modality[token.modality].append(token)
        
        # Try to bind across modalities
        for mod1, mod2, property_key in self.binding_rules:
            if mod1 not in by_modality or mod2 not in by_modality:
                continue
            
            for token1 in by_modality[mod1]:
                for token2 in by_modality[mod2]:
                    if self._should_bind(token1, token2, property_key):
                        # Add bidirectional binding
                        if token1.id not in bindings:
                            bindings[token1.id] = set()
                        if token2.id not in bindings:
                            bindings[token2.id] = set()
                        
                        bindings[token1.id].add(token2.id)
                        bindings[token2.id].add(token1.id)
        
        # Also bind by embedding similarity
        embedding_bindings = self._bind_by_embedding_similarity(tokens)
        for token_id, bound_ids in embedding_bindings.items():
            if token_id not in bindings:
                bindings[token_id] = set()
            bindings[token_id].update(bound_ids)
        
        return bindings
    
    def _should_bind(self, token1: PerceptualToken, token2: PerceptualToken,
                    property_key: str) -> bool:
        """Check if two tokens should be bound based on property match."""
        # Temporal proximity check (within 2 seconds)
        if abs(token1.timestamp - token2.timestamp) > 2.0:
            return False
        
        # Property matching
        val1 = token1.metadata.get(property_key)
        val2 = token2.metadata.get(property_key)
        
        if val1 and val2:
            if isinstance(val1, str) and isinstance(val2, str):
                return val1.lower() == val2.lower()
            return val1 == val2
        
        return False
    
    def _bind_by_embedding_similarity(self, 
                                      tokens: List[PerceptualToken]) -> Dict[str, Set[str]]:
        """Bind tokens with similar embeddings across modalities."""
        bindings: Dict[str, Set[str]] = {}
        
        for i, token1 in enumerate(tokens):
            for token2 in tokens[i+1:]:
                # Only bind across different modalities
                if token1.modality == token2.modality:
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(token1.embedding, token2.embedding)
                
                if similarity >= self.binding_threshold:
                    if token1.id not in bindings:
                        bindings[token1.id] = set()
                    if token2.id not in bindings:
                        bindings[token2.id] = set()
                    
                    bindings[token1.id].add(token2.id)
                    bindings[token2.id].add(token1.id)
        
        return bindings
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(x*x for x in vec1))
        mag2 = math.sqrt(sum(x*x for x in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot / (mag1 * mag2)
    
    def compute_spotlight(self, tokens: List[PerceptualToken],
                         bindings: Dict[str, Set[str]]) -> Optional[str]:
        """
        Determine what to focus attention on.
        
        The spotlight is the most salient token cluster, considering:
        - Individual token salience
        - Binding strength (more bindings = more important)
        - Recency (newer things grab attention)
        """
        if not tokens:
            return None
        
        now = time.time()
        scores: Dict[str, float] = {}
        
        for token in tokens:
            # Base salience
            score = token.salience.value
            
            # Recency bonus (exponential decay)
            age = now - token.timestamp
            recency_bonus = math.exp(-age / 5.0)  # 5-second half-life
            score += recency_bonus * 2
            
            # Binding bonus (more connections = more salient)
            binding_count = len(bindings.get(token.id, []))
            score += binding_count * 0.5
            
            # Confidence factor
            score *= token.confidence
            
            scores[token.id] = score
        
        # Find highest-scoring token
        spotlight = max(scores.keys(), key=lambda k: scores[k])
        
        # Track attention history
        self.attention_history.append({
            "token_id": spotlight,
            "timestamp": now,
            "score": scores[spotlight]
        })
        
        self.attention_spotlight = spotlight
        return spotlight
    
    def apply_attention_weights(self, tokens: List[PerceptualToken],
                                spotlight_id: Optional[str],
                                bindings: Dict[str, Set[str]]) -> List[PerceptualToken]:
        """
        Apply attention weights to tokens based on spotlight.
        
        Tokens in the spotlight and bound to it get higher weights;
        unrelated tokens get suppressed.
        """
        if not spotlight_id:
            return tokens
        
        spotlight_cluster = {spotlight_id}
        spotlight_cluster.update(bindings.get(spotlight_id, set()))
        
        for token in tokens:
            if token.id == spotlight_id:
                token.attention_weight = 1.0
            elif token.id in spotlight_cluster:
                token.attention_weight = 0.8
            else:
                # Calculate distance from spotlight
                distance = self._distance_from_cluster(
                    token.id, spotlight_cluster, bindings
                )
                token.attention_weight = max(0.1, 1.0 - (distance * 0.3))
        
        return tokens
    
    def _distance_from_cluster(self, token_id: str, cluster: Set[str],
                              bindings: Dict[str, Set[str]]) -> int:
        """BFS to find shortest path to cluster."""
        if token_id in cluster:
            return 0
        
        visited = set()
        queue = [(token_id, 0)]
        
        while queue:
            current, distance = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            if current in cluster:
                return distance
            
            for neighbor in bindings.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, distance + 1))
        
        return 10  # Not connected


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class SceneGraphBuilder:
    """
    Builds unified scene representation from multimodal tokens.
    
    The scene graph contains:
    - ENTITIES: Things we perceive (people, objects, sounds)
    - RELATIONSHIPS: How entities relate to each other
    - PROPERTIES: Multimodal properties of each entity
    """
    
    def __init__(self):
        self.entities: Dict[str, SceneEntity] = {}
        self.entity_history: deque = deque(maxlen=100)
    
    def build_from_tokens(self, tokens: List[PerceptualToken],
                          bindings: Dict[str, Set[str]]) -> Dict[str, SceneEntity]:
        """
        Convert tokens into scene entities.
        
        Bound tokens become properties of the same entity.
        """
        now = time.time()
        new_entities: Dict[str, SceneEntity] = {}
        
        # Find token clusters (connected components via bindings)
        clusters = self._find_clusters(tokens, bindings)
        
        for cluster_id, cluster_tokens in enumerate(clusters):
            # Determine entity type from tokens
            entity_type = self._infer_entity_type(cluster_tokens)
            
            # Create entity
            entity_id = f"entity_{int(now * 1000)}_{cluster_id}"
            
            # Gather multimodal data
            modality_data = {}
            properties = {}
            
            for token in cluster_tokens:
                # Store modality-specific data
                if token.modality not in modality_data:
                    modality_data[token.modality] = []
                modality_data[token.modality].append(token.content)
                
                # Extract properties from metadata
                for key, value in token.metadata.items():
                    if key not in ["type", "parent_scene", "parent_text"]:
                        properties[f"{token.modality.value}_{key}"] = value
            
            # Generate name
            name = self._generate_entity_name(entity_type, cluster_tokens)
            
            entity = SceneEntity(
                id=entity_id,
                entity_type=entity_type,
                name=name,
                modality_data=modality_data,
                confidence=sum(t.confidence for t in cluster_tokens) / len(cluster_tokens),
                last_seen=now,
                properties=properties
            )
            
            new_entities[entity_id] = entity
        
        # Merge with existing entities (persistence)
        self._merge_entities(new_entities)
        
        return self.entities
    
    def _find_clusters(self, tokens: List[PerceptualToken],
                      bindings: Dict[str, Set[str]]) -> List[List[PerceptualToken]]:
        """Find connected components of tokens via bindings."""
        token_map = {t.id: t for t in tokens}
        visited = set()
        clusters = []
        
        for token in tokens:
            if token.id in visited:
                continue
            
            # BFS to find cluster
            cluster = []
            queue = [token.id]
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                if current_id in token_map:
                    cluster.append(token_map[current_id])
                
                for neighbor_id in bindings.get(current_id, []):
                    if neighbor_id not in visited:
                        queue.append(neighbor_id)
            
            if cluster:
                clusters.append(cluster)
        
        return clusters
    
    def _infer_entity_type(self, tokens: List[PerceptualToken]) -> EntityType:
        """Infer entity type from token metadata."""
        for token in tokens:
            token_type = token.metadata.get("type", "")
            
            if "face" in token_type:
                return EntityType.PERSON
            if "speech" in token_type:
                return EntityType.PERSON
            if "object" in token_type:
                return EntityType.OBJECT
            if "sound" in token_type:
                return EntityType.SOUND
        
        return EntityType.CONCEPT
    
    def _generate_entity_name(self, entity_type: EntityType,
                             tokens: List[PerceptualToken]) -> str:
        """Generate human-readable name for entity."""
        if entity_type == EntityType.PERSON:
            # Try to find speaker ID or face info
            for token in tokens:
                speaker = token.metadata.get("speaker_id")
                if speaker:
                    return f"Person ({speaker})"
            return "Unknown Person"
        
        elif entity_type == EntityType.OBJECT:
            for token in tokens:
                if token.metadata.get("type") == "object":
                    return str(token.content)
            return "Object"
        
        elif entity_type == EntityType.SOUND:
            return "Sound"
        
        else:
            # Use first content
            return tokens[0].content[:30] if tokens else "Entity"
    
    def _merge_entities(self, new_entities: Dict[str, SceneEntity]):
        """Merge new entities with existing, updating persistent entities."""
        now = time.time()
        
        # Expire old entities
        expired_ids = [
            eid for eid, entity in self.entities.items()
            if now - entity.last_seen > 30.0  # 30 second timeout
        ]
        for eid in expired_ids:
            self.entity_history.append(self.entities.pop(eid))
        
        # Add new entities
        for eid, entity in new_entities.items():
            # Check if similar entity exists (same type and similar properties)
            matched_existing = self._find_matching_entity(entity)
            
            if matched_existing:
                # Update existing entity
                matched_existing.last_seen = now
                matched_existing.modality_data.update(entity.modality_data)
                matched_existing.properties.update(entity.properties)
            else:
                self.entities[eid] = entity
    
    def _find_matching_entity(self, new_entity: SceneEntity) -> Optional[SceneEntity]:
        """Find existing entity that matches the new one."""
        for existing in self.entities.values():
            if existing.entity_type != new_entity.entity_type:
                continue
            
            # Check for property overlap
            common_props = set(existing.properties.keys()) & set(new_entity.properties.keys())
            if common_props:
                matches = sum(
                    1 for k in common_props 
                    if existing.properties[k] == new_entity.properties[k]
                )
                if matches / len(common_props) > 0.5:
                    return existing
        
        return None
    
    def get_scene_description(self) -> str:
        """Generate natural language description of the scene."""
        if not self.entities:
            return "Empty scene"
        
        parts = []
        
        # Describe people
        people = [e for e in self.entities.values() if e.entity_type == EntityType.PERSON]
        if people:
            for person in people[:2]:  # Max 2 people
                emotion = person.properties.get("vision_emotion") or \
                         person.properties.get("audio_emotion", "neutral")
                parts.append(f"{person.name} appears {emotion}")
        
        # Describe objects
        objects = [e for e in self.entities.values() if e.entity_type == EntityType.OBJECT]
        if objects:
            obj_names = [o.name for o in objects[:5]]
            parts.append(f"Objects: {', '.join(obj_names)}")
        
        return ". ".join(parts) if parts else "Quiet scene"


# ═══════════════════════════════════════════════════════════════════════════════
# MOMENT BUFFER
# ═══════════════════════════════════════════════════════════════════════════════

class MomentBuffer:
    """
    Buffer of coherent perception moments.
    
    Unlike separate modality buffers, this stores integrated
    "moments" that contain everything perceived at once.
    """
    
    def __init__(self, max_moments: int = 30, moment_duration_ms: float = 500):
        self.moments: deque = deque(maxlen=max_moments)
        self.moment_duration = moment_duration_ms / 1000.0
        self._moment_count = 0
    
    def create_moment(self,
                     tokens: List[PerceptualToken],
                     entities: Dict[str, SceneEntity],
                     bindings: Dict[str, Set[str]],
                     attention_focus: Optional[str]) -> Moment:
        """Create a new coherent perception moment."""
        now = time.time()
        self._moment_count += 1
        
        # Synthesize emotional tone from tokens
        emotional_tone = self._synthesize_emotion(tokens)
        
        # Extract salient features
        salient = [
            t.content[:50] for t in tokens 
            if t.salience.value >= Salience.HIGH.value
        ][:5]
        
        # Generate scene description from entities
        entity_descriptions = []
        for entity in list(entities.values())[:3]:  # Top 3 entities
            if entity.entity_type == EntityType.PERSON:
                emotion = entity.properties.get("vision_emotion", "neutral")
                entity_descriptions.append(f"{entity.name} ({emotion})")
            else:
                entity_descriptions.append(entity.name)
        
        scene_description = "; ".join(entity_descriptions) if entity_descriptions else "Quiet"
        
        moment = Moment(
            id=f"moment_{int(now * 1000)}_{self._moment_count}",
            timestamp=now,
            tokens=tokens.copy(),
            entities=entities.copy(),
            attention_focus=attention_focus,
            scene_description=scene_description,
            emotional_tone=emotional_tone,
            salient_features=salient,
            bindings=bindings
        )
        
        self.moments.append(moment)
        return moment
    
    def _synthesize_emotion(self, tokens: List[PerceptualToken]) -> str:
        """Synthesize emotional tone from tokens."""
        emotion_votes: Dict[str, float] = {}
        
        for token in tokens:
            emotion = token.metadata.get("emotion")
            if emotion:
                if emotion not in emotion_votes:
                    emotion_votes[emotion] = 0
                emotion_votes[emotion] += token.confidence * token.attention_weight
        
        if emotion_votes:
            return max(emotion_votes.keys(), key=lambda k: emotion_votes[k])
        return "neutral"
    
    def get_current(self) -> Optional[Moment]:
        """Get the most recent moment."""
        return self.moments[-1] if self.moments else None
    
    def get_recent(self, count: int = 5) -> List[Moment]:
        """Get recent moments."""
        return list(self.moments)[-count:]
    
    def get_temporal_context(self, window_seconds: float = 10.0) -> Dict:
        """Get context from recent moments."""
        now = time.time()
        recent = [m for m in self.moments if now - m.timestamp <= window_seconds]
        
        if not recent:
            return {"moments": 0, "emotions": [], "entities": []}
        
        # Aggregate emotions
        emotions = [m.emotional_tone for m in recent]
        
        # Aggregate entities
        all_entities = set()
        for m in recent:
            all_entities.update(e.name for e in m.entities.values())
        
        return {
            "moments": len(recent),
            "emotions": list(set(emotions)),
            "entities": list(all_entities)[:10],
            "dominant_emotion": max(set(emotions), key=emotions.count) if emotions else "neutral"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED PERCEPTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedPerception:
    """
    Main orchestrator for unified multimodal perception.
    
    This is ZARA's perceptual consciousness - the unified experience
    of seeing, hearing, and understanding as ONE coherent NOW.
    """
    
    def __init__(self):
        # Components
        self.tokenizer = PerceptualTokenizer()
        self.attention = JointAttentionMechanism()
        self.scene_builder = SceneGraphBuilder()
        self.moment_buffer = MomentBuffer()
        
        # Current state
        self.current_tokens: List[PerceptualToken] = []
        self.current_bindings: Dict[str, Set[str]] = {}
        self.attention_focus: Optional[str] = None
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Callbacks
        self.on_moment_created: List[callable] = []
        self.on_attention_shift: List[callable] = []
        
        logger.info("🌐 Unified Perception Engine initialized")
    
    def perceive_vision(self,
                       description: str,
                       objects: List[str] = None,
                       faces: List[Dict] = None,
                       emotion: Optional[str] = None,
                       attention_score: float = 0.5):
        """Process visual perception."""
        with self.lock:
            tokens = self.tokenizer.tokenize_vision(
                description, objects, faces, emotion, attention_score
            )
            self._integrate_tokens(tokens)
    
    def perceive_audio(self,
                      transcription: str,
                      voice_emotion: Optional[str] = None,
                      speaker_id: Optional[str] = None,
                      volume: float = 0.5,
                      pitch: float = 0.5,
                      speaking_rate: float = 1.0):
        """Process audio perception."""
        with self.lock:
            tokens = self.tokenizer.tokenize_audio(
                transcription, voice_emotion, speaker_id,
                volume, pitch, speaking_rate
            )
            self._integrate_tokens(tokens)
    
    def perceive_text(self,
                     text: str,
                     sentiment: float = 0.5,
                     topics: List[str] = None,
                     is_question: bool = False,
                     source: str = "user"):
        """Process text perception."""
        with self.lock:
            tokens = self.tokenizer.tokenize_text(
                text, sentiment, topics, is_question, source
            )
            self._integrate_tokens(tokens)
    
    def _integrate_tokens(self, new_tokens: List[PerceptualToken]):
        """Integrate new tokens into unified perception."""
        # Add to current tokens
        self.current_tokens.extend(new_tokens)
        
        # Prune old tokens (keep last 2 seconds)
        now = time.time()
        self.current_tokens = [
            t for t in self.current_tokens
            if now - t.timestamp <= 2.0
        ]
        
        # Compute bindings
        self.current_bindings = self.attention.compute_bindings(self.current_tokens)
        
        # Compute attention spotlight
        new_focus = self.attention.compute_spotlight(
            self.current_tokens, self.current_bindings
        )
        
        # Notify if attention shifted
        if new_focus != self.attention_focus:
            old_focus = self.attention_focus
            self.attention_focus = new_focus
            for callback in self.on_attention_shift:
                try:
                    callback(old_focus, new_focus)
                except Exception as e:
                    logger.error(f"Attention callback error: {e}")
        
        # Apply attention weights
        self.current_tokens = self.attention.apply_attention_weights(
            self.current_tokens, self.attention_focus, self.current_bindings
        )
        
        # Build scene graph
        entities = self.scene_builder.build_from_tokens(
            self.current_tokens, self.current_bindings
        )
        
        # Create moment
        moment = self.moment_buffer.create_moment(
            self.current_tokens, entities, 
            self.current_bindings, self.attention_focus
        )
        
        # Notify moment created
        for callback in self.on_moment_created:
            try:
                callback(moment)
            except Exception as e:
                logger.error(f"Moment callback error: {e}")
    
    def get_unified_context(self) -> Dict:
        """Get unified perception context for LLM."""
        with self.lock:
            current = self.moment_buffer.get_current()
            temporal = self.moment_buffer.get_temporal_context()
            
            if not current:
                return {
                    "scene": "No perception data",
                    "emotion": "neutral",
                    "attention": "none",
                    "entities": []
                }
            
            return {
                "scene": current.scene_description,
                "emotion": current.emotional_tone,
                "attention": current.attention_focus,
                "salient": current.salient_features,
                "entities": [e.name for e in current.entities.values()],
                "temporal_emotion": temporal.get("dominant_emotion", "neutral"),
                "recent_entities": temporal.get("entities", [])
            }
    
    def get_context_string(self) -> str:
        """Get perception as natural language for LLM prompt."""
        ctx = self.get_unified_context()
        
        parts = []
        
        if ctx["scene"] and ctx["scene"] != "No perception data":
            parts.append(f"[PERCEIVING] {ctx['scene']}")
        
        if ctx["emotion"] != "neutral":
            parts.append(f"[SENSING] User emotion: {ctx['emotion']}")
        
        if ctx.get("salient"):
            parts.append(f"[NOTICE] {'; '.join(ctx['salient'][:3])}")
        
        return "\n".join(parts)
    
    def get_current_moment(self) -> Optional[Moment]:
        """Get the current perception moment."""
        return self.moment_buffer.get_current()
    
    def get_status(self) -> Dict:
        """Get perception engine status."""
        with self.lock:
            current = self.moment_buffer.get_current()
            return {
                "active_tokens": len(self.current_tokens),
                "active_bindings": len(self.current_bindings),
                "attention_focus": self.attention_focus,
                "entities": len(self.scene_builder.entities),
                "moments_buffered": len(self.moment_buffer.moments),
                "current_emotion": current.emotional_tone if current else "none",
                "current_scene": current.scene_description if current else "none"
            }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

_unified_perception: Optional[UnifiedPerception] = None

def get_unified_perception() -> UnifiedPerception:
    """Get the global unified perception instance."""
    global _unified_perception
    if _unified_perception is None:
        _unified_perception = UnifiedPerception()
    return _unified_perception


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    
    print("\n🌐 ZARA Unified Multimodal Perception v1.0\n")
    print("=" * 60)
    
    perception = UnifiedPerception()
    
    # Simulate multimodal input
    print("\n📥 Simulating multimodal perception...")
    
    # Visual: User sitting at desk
    perception.perceive_vision(
        description="User sitting at desk, looking at camera",
        objects=["desk", "monitor", "keyboard"],
        faces=[{"emotion": "focused", "attention": 0.8}],
        emotion="focused",
        attention_score=0.8
    )
    print("  ✓ Vision processed")
    
    # Audio: User speaking
    perception.perceive_audio(
        transcription="Hey, I need help with my project",
        voice_emotion="curious",
        speaker_id="user_1",
        volume=0.6,
        pitch=0.5,
        speaking_rate=1.1
    )
    print("  ✓ Audio processed")
    
    # Text: Message content
    perception.perceive_text(
        text="Help with my AI project",
        sentiment=0.5,
        topics=["AI", "project", "help"],
        is_question=True
    )
    print("  ✓ Text processed")
    
    # Show unified perception
    print("\n" + "-" * 60)
    print("🎯 Unified Perception Context:")
    context = perception.get_unified_context()
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    print("\n📝 Context String for LLM:")
    print(perception.get_context_string())
    
    # Status
    print("\n" + "-" * 60)
    print("📊 Status:")
    status = perception.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Unified Perception ready!\n")
