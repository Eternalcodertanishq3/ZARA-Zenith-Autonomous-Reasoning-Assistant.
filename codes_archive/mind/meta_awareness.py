# """
# ZARA Meta-Awareness v1.0
# =========================
# ZARA Knows What She Knows (and Doesn't Know)
#
# True epistemological self-awareness that enables:
# 1. KNOWLEDGE INVENTORY - What do I know?
# 2. CAPABILITY MAPPING - What can I do?
# 3. UNCERTAINTY QUANTIFICATION - How confident am I?
# 4. KNOWLEDGE GAPS - What don't I know?
# 5. SELF-MODEL - Understanding my own systems
# 6. CALIBRATION - Is my confidence accurate?
# 7. INTROSPECTION - Real-time self-examination
# 8. HONESTY ENGINE - Authentic uncertainty expression
#
# This enables ZARA to:
# - Say "I don't know" authentically when appropriate
# - Quantify confidence levels accurately
# - Identify knowledge boundaries
# - Request clarification when needed
# - Understand her own cognitive processes
# - Track what she's learned and forgotten
# """
#
# import logging
# import time
# import sys
# import json
# import hashlib
# import os
# import inspect
# from pathlib import Path
# from typing import Optional, Dict, List, Tuple, Any, Set, Callable
# from dataclasses import dataclass, field
# from enum import Enum
# from collections import defaultdict, deque
# from datetime import datetime
# import importlib
# import pkgutil
#
# Ensure parent in path
# _ROOT = Path(__file__).parent.parent
# if str(_ROOT) not in sys.path:
#     sys.path.insert(0, str(_ROOT))
#
# logger = logging.getLogger("ZARA_META")
#
#
# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════
#
# class KnowledgeDomain(Enum):
#     """Domains of knowledge."""
#     FACTUAL = "factual"           # Facts, dates, definitions
#     PROCEDURAL = "procedural"     # How to do things
#     CONCEPTUAL = "conceptual"     # Understanding concepts
#     METACOGNITIVE = "metacognitive"  # Self-knowledge
#     EXPERIENTIAL = "experiential"  # From past interactions
#     REAL_TIME = "real_time"       # Current observations
#     INFERRED = "inferred"         # Derived conclusions
#
#
# class ConfidenceLevel(Enum):
#     """Confidence levels for knowledge."""
#     CERTAIN = "certain"           # 95-100% confident
#     HIGH = "high"                 # 80-95%
#     MODERATE = "moderate"         # 60-80%
#     LOW = "low"                   # 40-60%
#     UNCERTAIN = "uncertain"       # 20-40%
#     UNKNOWN = "unknown"           # 0-20%
#
#
# class CapabilityStatus(Enum):
#     """Status of a capability."""
#     FULLY_FUNCTIONAL = "fully_functional"
#     PARTIALLY_AVAILABLE = "partially_available"
#     DEGRADED = "degraded"
#     UNAVAILABLE = "unavailable"
#     UNKNOWN = "unknown"
#
#
# @dataclass
# class KnowledgeItem:
#     """A piece of knowledge ZARA has."""
#     id: str
#     domain: KnowledgeDomain
#     topic: str
#     content: str
#     confidence: float               # 0.0 to 1.0
#     source: str                     # Where this knowledge came from
#     acquired_at: float              # Timestamp
#     last_accessed: float
#     access_count: int
#     accuracy_verified: bool
#     decay_rate: float               # How quickly confidence degrades
#     related_items: List[str]        # IDs of related knowledge
#
#
# @dataclass
# class Capability:
#     """A capability ZARA has."""
#     id: str
#     name: str
#     description: str
#     category: str                   # vision, speech, reasoning, etc.
#     status: CapabilityStatus
#     dependencies: List[str]         # What this capability needs
#     confidence: float               # How well ZARA can do this
#     last_checked: float
#     error_rate: float               # Historical error rate
#     availability_history: List[Tuple[float, bool]]
#
#
# @dataclass
# class KnowledgeGap:
#     """Something ZARA doesn't know."""
#     id: str
#     topic: str
#     description: str
#     importance: float               # How important is filling this gap
#     detected_at: float
#     context: str                    # When this gap was noticed
#     attempted_sources: List[str]    # Where we tried to find this
#     related_queries: List[str]
#
#
# @dataclass
# class ConfidenceAssessment:
#     """Assessment of confidence in a claim or response."""
#     claim: str
#     confidence: float
#     confidence_level: ConfidenceLevel
#     reasoning: str
#     knowledge_sources: List[str]
#     uncertainty_factors: List[str]
#     should_express_uncertainty: bool
#     suggested_hedging: str          # "I think...", "I'm not sure but..."
#
#
# @dataclass
# class SelfModel:
#     """ZARA's model of herself."""
#     # Identity
#     name: str = "ZARA"
#     version: str = "1.0"
#     created_at: float = field(default_factory=time.time)
#
#     # Core traits
#     personality_traits: List[str] = field(default_factory=lambda: [
#         "curious", "helpful", "honest", "empathetic", "creative"
#     ])
#
#     # Current state
#     emotional_state: str = "neutral"
#     energy_level: float = 1.0
#     focus_level: float = 1.0
#
#     # Awareness
#     is_aware_of_being_ai: bool = True
#     understands_limitations: bool = True
#     can_express_uncertainty: bool = True
#
#     # Capabilities summary
#     total_capabilities: int = 0
#     active_capabilities: int = 0
#     total_knowledge_items: int = 0
#
#
# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE INVENTORY
# ═══════════════════════════════════════════════════════════════════════════
#
# class KnowledgeInventory:
#     """
#     Tracks what ZARA knows and how confident she is about it.
#     Real epistemological awareness.
#     """
#
#     def __init__(self):
#         self.knowledge: Dict[str, KnowledgeItem] = {}
#         self.knowledge_by_domain: Dict[KnowledgeDomain, Set[str]] = defaultdict(set)
#         self.knowledge_by_topic: Dict[str, Set[str]] = defaultdict(set)
#
#         # Built-in knowledge domains ZARA knows she has
#         self.core_knowledge_domains = [
#             "language_understanding",
#             "reasoning",
#             "mathematics",
#             "coding",
#             "general_knowledge",
#             "conversation",
#             "empathy",
#             "creativity"
#         ]
#
#         self._initialize_core_knowledge()
#
#     def _initialize_core_knowledge(self):
#         """Initialize awareness of core knowledge domains."""
#         for domain in self.core_knowledge_domains:
#             self.add_knowledge(
#                 topic=domain,
#                 content=f"Core capability in {domain.replace('_', ' ')}",
#                 domain=KnowledgeDomain.METACOGNITIVE,
#                 confidence=0.85,
#                 source="built_in"
#             )
#
#     def add_knowledge(self, topic: str, content: str, 
#                      domain: KnowledgeDomain,
#                      confidence: float = 0.7,
#                      source: str = "learned") -> KnowledgeItem:
#         """Add new knowledge."""
#         item_id = hashlib.md5(f"{topic}:{content[:50]}".encode()).hexdigest()[:12]
#
#         item = KnowledgeItem(
#             id=item_id,
#             domain=domain,
#             topic=topic,
#             content=content,
#             confidence=confidence,
#             source=source,
#             acquired_at=time.time(),
#             last_accessed=time.time(),
#             access_count=0,
#             accuracy_verified=False,
#             decay_rate=0.001,  # Confidence decays slowly
#             related_items=[]
#         )
#
#         self.knowledge[item_id] = item
#         self.knowledge_by_domain[domain].add(item_id)
#         self.knowledge_by_topic[topic.lower()].add(item_id)
#
#         return item
#
#     def query(self, topic: str) -> List[KnowledgeItem]:
#         """Query knowledge on a topic."""
#         results = []
#         topic_lower = topic.lower()
#
#         # Direct topic match
#         if topic_lower in self.knowledge_by_topic:
#             for item_id in self.knowledge_by_topic[topic_lower]:
#                 item = self.knowledge[item_id]
#                 item.last_accessed = time.time()
#                 item.access_count += 1
#                 results.append(item)
#
#         # Fuzzy match in content
#         for item_id, item in self.knowledge.items():
#             if topic_lower in item.content.lower() or topic_lower in item.topic.lower():
#                 if item not in results:
#                     item.last_accessed = time.time()
#                     item.access_count += 1
#                     results.append(item)
#
#         # Sort by confidence
#         results.sort(key=lambda x: x.confidence, reverse=True)
#         return results
#
#     def get_confidence_for_topic(self, topic: str) -> Tuple[float, str]:
#         """Get overall confidence for a topic."""
#         items = self.query(topic)
#
#         if not items:
#             return 0.0, "No knowledge found on this topic"
#
#         # Weighted average by recency and access count
#         total_weight = 0
#         weighted_conf = 0
#
#         for item in items:
#             recency = 1.0 / (1 + (time.time() - item.last_accessed) / 86400)  # Days
#             weight = recency * (1 + item.access_count * 0.1)
#             weighted_conf += item.confidence * weight
#             total_weight += weight
#
#         avg_conf = weighted_conf / total_weight if total_weight > 0 else 0
#
#         if avg_conf > 0.9:
#             reason = "Strong, frequently accessed knowledge"
#         elif avg_conf > 0.7:
#             reason = "Good knowledge with moderate confidence"
#         elif avg_conf > 0.5:
#             reason = "Some knowledge, but not fully confident"
#         elif avg_conf > 0.3:
#             reason = "Limited knowledge, low confidence"
#         else:
#             reason = "Very limited or outdated knowledge"
#
#         return avg_conf, reason
#
#     def knows_about(self, topic: str) -> bool:
#         """Check if ZARA has any knowledge about a topic."""
#         items = self.query(topic)
#         return len(items) > 0 and any(item.confidence > 0.3 for item in items)
#
#     def decay_knowledge(self):
#         """Apply knowledge decay over time."""
#         for item in self.knowledge.values():
#             time_since_access = time.time() - item.last_accessed
#             days_since_access = time_since_access / 86400
#
#             # Decay confidence for unused knowledge
#             decay = item.decay_rate * days_since_access
#             item.confidence = max(0.1, item.confidence - decay)
#
#     def get_stats(self) -> Dict:
#         """Get knowledge inventory statistics."""
#         by_domain = {d.value: len(ids) for d, ids in self.knowledge_by_domain.items()}
#
#         confidences = [item.confidence for item in self.knowledge.values()]
#         avg_conf = sum(confidences) / len(confidences) if confidences else 0
#
#         return {
#             "total_items": len(self.knowledge),
#             "by_domain": by_domain,
#             "average_confidence": avg_conf,
#             "high_confidence_items": sum(1 for c in confidences if c > 0.8),
#             "low_confidence_items": sum(1 for c in confidences if c < 0.4)
#         }
#
#
# ═══════════════════════════════════════════════════════════════════════════
# CAPABILITY MAPPER
# ═══════════════════════════════════════════════════════════════════════════
#
# class CapabilityMapper:
#     """
#     Maps and monitors ZARA's capabilities.
#     Knows what systems are available and functional.
#     """
#
#     def __init__(self):
#         self.capabilities: Dict[str, Capability] = {}
#         self._discover_capabilities()
#
#     def _discover_capabilities(self):
#         """Discover available capabilities by checking modules."""
#         # Core capabilities to check
#         capability_checks = [
#             ("vision", "eyes.vision_core", "VisionCore", "Visual perception and analysis"),
#             ("gaze_tracking", "eyes.gaze_analyzer", "GazeAnalyzer", "Eye gaze detection and analysis"),
#             ("depth_mapping", "eyes.depth_mapper", "DepthMapper", "3D depth perception"),
#             ("environmental_awareness", "awareness.environmental_awareness", "EnvironmentalAwareness", "Environmental understanding"),
#             ("speech", "voice.speech", "speak", "Speech synthesis"),
#             ("hearing", "voice.listener", "Listener", "Speech recognition"),
#             ("graph_memory", "memory.graph_memory", "GraphMemory", "Knowledge graph memory"),
#             ("empathy", "mind.empathy_engine", "AnticipatoryEmpathyEngine", "Emotional understanding"),
#             ("system2_reasoning", "mind.system2_reasoner", "System2Reasoner", "Deep deliberate thinking"),
#             ("dream_mode", "mind.dream_mode", "DreamModeEngine", "Memory consolidation and reflection"),
#             ("social_intelligence", "mind.social_intelligence", "SocialIntelligence", "Social perception"),
#             ("self_evolution", "evolution.self_evolution", "SelfEvolutionEngine", "Self-improvement"),
#             ("tool_agency", "actions.tool_agency", "ToolAgency", "Tool and skill execution"),
#         ]
#
#         for cap_id, module_path, class_name, description in capability_checks:
#             status, confidence = self._check_capability(module_path, class_name)
#
#             self.capabilities[cap_id] = Capability(
#                 id=cap_id,
#                 name=cap_id.replace("_", " ").title(),
#                 description=description,
#                 category=module_path.split(".")[0],
#                 status=status,
#                 dependencies=[],
#                 confidence=confidence,
#                 last_checked=time.time(),
#                 error_rate=0.0,
#                 availability_history=[(time.time(), status == CapabilityStatus.FULLY_FUNCTIONAL)]
#             )
#
#     def _check_capability(self, module_path: str, class_name: str) -> Tuple[CapabilityStatus, float]:
#         """Check if a capability is available."""
#         try:
#             module = importlib.import_module(module_path)
#             if hasattr(module, class_name):
#                 return CapabilityStatus.FULLY_FUNCTIONAL, 0.95
#             return CapabilityStatus.PARTIALLY_AVAILABLE, 0.5
#         except ImportError:
#             return CapabilityStatus.UNAVAILABLE, 0.0
#         except Exception as e:
#             logger.debug(f"Capability check error for {module_path}: {e}")
#             return CapabilityStatus.DEGRADED, 0.3
#
#     def refresh(self):
#         """Refresh capability status."""
#         self._discover_capabilities()
#
#     def can_do(self, capability: str) -> Tuple[bool, float, str]:
#         """
#         Check if ZARA can do something.
#
#         Returns:
#             (can_do, confidence, reason)
#         """
#         cap = self.capabilities.get(capability.lower().replace(" ", "_"))
#
#         if not cap:
#             # Check if it's a general capability
#             general_caps = {
#                 "think": (True, 0.95, "Core reasoning capability"),
#                 "understand": (True, 0.9, "Language understanding"),
#                 "learn": (True, 0.85, "Can learn from interactions"),
#                 "remember": (True, 0.8, "Memory systems available"),
#                 "feel": (True, 0.75, "Empathy engine active"),
#                 "create": (True, 0.8, "Creative synthesis available"),
#             }
#
#             for key, value in general_caps.items():
#                 if key in capability.lower():
#                     return value
#
#             return False, 0.0, "Unknown capability"
#
#         can = cap.status in [CapabilityStatus.FULLY_FUNCTIONAL, CapabilityStatus.PARTIALLY_AVAILABLE]
#
#         reason = {
#             CapabilityStatus.FULLY_FUNCTIONAL: f"{cap.name} is fully available",
#             CapabilityStatus.PARTIALLY_AVAILABLE: f"{cap.name} is partially available",
#             CapabilityStatus.DEGRADED: f"{cap.name} is degraded",
#             CapabilityStatus.UNAVAILABLE: f"{cap.name} is not available",
#             CapabilityStatus.UNKNOWN: f"{cap.name} status unknown"
#         }.get(cap.status, "Unknown status")
#
#         return can, cap.confidence, reason
#
#     def list_available(self) -> List[Capability]:
#         """List all available capabilities."""
#         return [
#             cap for cap in self.capabilities.values()
#             if cap.status in [CapabilityStatus.FULLY_FUNCTIONAL, CapabilityStatus.PARTIALLY_AVAILABLE]
#         ]
#
#     def list_unavailable(self) -> List[Capability]:
#         """List unavailable or degraded capabilities."""
#         return [
#             cap for cap in self.capabilities.values()
#             if cap.status in [CapabilityStatus.UNAVAILABLE, CapabilityStatus.DEGRADED]
#         ]
#
#     def get_summary(self) -> Dict:
#         """Get capability summary."""
#         return {
#             "total": len(self.capabilities),
#             "functional": sum(1 for c in self.capabilities.values() 
#                             if c.status == CapabilityStatus.FULLY_FUNCTIONAL),
#             "partial": sum(1 for c in self.capabilities.values() 
#                           if c.status == CapabilityStatus.PARTIALLY_AVAILABLE),
#             "degraded": sum(1 for c in self.capabilities.values() 
#                           if c.status == CapabilityStatus.DEGRADED),
#             "unavailable": sum(1 for c in self.capabilities.values() 
#                              if c.status == CapabilityStatus.UNAVAILABLE)
#         }
#
#
# ═══════════════════════════════════════════════════════════════════════════
# UNCERTAINTY QUANTIFIER
# ═══════════════════════════════════════════════════════════════════════════
#
# class UncertaintyQuantifier:
#     """
#     Quantifies uncertainty and calibrates confidence.
#     Ensures ZARA's expressed confidence matches actual accuracy.
#     """
#
#     def __init__(self):
#         self.calibration_history: deque = deque(maxlen=100)
#         self.prediction_outcomes: List[Tuple[float, bool]] = []  # (predicted_conf, was_correct)
#
#     def assess_confidence(self, claim: str, 
#                          knowledge_inventory: KnowledgeInventory,
#                          context: str = "") -> ConfidenceAssessment:
#         """
#         Assess confidence in a claim.
#
#         This is where ZARA decides how confident to be.
#         """
#         # Check knowledge base
#         topic_words = self._extract_topics(claim)
#         knowledge_sources = []
#         knowledge_confidences = []
#
#         for topic in topic_words:
#             items = knowledge_inventory.query(topic)
#             for item in items[:3]:  # Top 3 matches
#                 knowledge_sources.append(f"{item.topic}: {item.confidence:.0%}")
#                 knowledge_confidences.append(item.confidence)
#
#         # Base confidence from knowledge
#         if knowledge_confidences:
#             base_conf = sum(knowledge_confidences) / len(knowledge_confidences)
#         else:
#             base_conf = 0.3  # Default low confidence for unknown topics
#
#         # Identify uncertainty factors
#         uncertainty_factors = []
#
#         # Check for hedging language in claim
#         hedging_words = ["might", "maybe", "probably", "could", "perhaps", "possibly"]
#         if any(word in claim.lower() for word in hedging_words):
#             uncertainty_factors.append("Topic involves uncertainty")
#             base_conf *= 0.9
#
#         # Check for absolute claims
#         absolute_words = ["always", "never", "definitely", "certainly", "everyone", "nobody"]
#         if any(word in claim.lower() for word in absolute_words):
#             uncertainty_factors.append("Absolute claims are rarely true")
#             base_conf *= 0.7
#
#         # Check for temporal claims
#         temporal_words = ["will", "going to", "future", "predict"]
#         if any(word in claim.lower() for word in temporal_words):
#             uncertainty_factors.append("Future predictions are uncertain")
#             base_conf *= 0.6
#
#         # Check for subjective claims
#         subjective_words = ["best", "worst", "beautiful", "ugly", "good", "bad"]
#         if any(word in claim.lower() for word in subjective_words):
#             uncertainty_factors.append("Subjective claims vary by perspective")
#             base_conf *= 0.85
#
#         # Determine confidence level
#         confidence_level = self._confidence_to_level(base_conf)
#
#         # Should we express uncertainty?
#         should_hedge = base_conf < 0.7 or len(uncertainty_factors) > 0
#
#         # Generate hedging phrase
#         hedging = self._generate_hedging(base_conf)
#
#         # Reasoning
#         if base_conf > 0.8:
#             reasoning = "Strong knowledge base with high confidence"
#         elif base_conf > 0.6:
#             reasoning = "Moderate confidence based on available knowledge"
#         elif base_conf > 0.4:
#             reasoning = "Limited knowledge, expressing appropriate uncertainty"
#         else:
#             reasoning = "Low confidence, should clearly express uncertainty"
#
#         return ConfidenceAssessment(
#             claim=claim,
#             confidence=base_conf,
#             confidence_level=confidence_level,
#             reasoning=reasoning,
#             knowledge_sources=knowledge_sources,
#             uncertainty_factors=uncertainty_factors,
#             should_express_uncertainty=should_hedge,
#             suggested_hedging=hedging
#         )
#
#     def _extract_topics(self, text: str) -> List[str]:
#         """Extract potential topic words from text."""
#         # Remove common words, keep nouns/verbs
#         common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
#                        "have", "has", "do", "does", "did", "will", "would", "could",
#                        "should", "may", "might", "must", "shall", "can", "to", "of",
#                        "in", "for", "on", "with", "at", "by", "from", "it", "this",
#                        "that", "these", "those", "i", "you", "we", "they", "he", "she"}
#
#         words = text.lower().split()
#         topics = [w.strip(".,!?;:\"'") for w in words if w.lower() not in common_words]
#         return topics[:5]  # Top 5 topic words
#
#     def _confidence_to_level(self, conf: float) -> ConfidenceLevel:
#         """Convert confidence score to level."""
#         if conf >= 0.95:
#             return ConfidenceLevel.CERTAIN
#         elif conf >= 0.8:
#             return ConfidenceLevel.HIGH
#         elif conf >= 0.6:
#             return ConfidenceLevel.MODERATE
#         elif conf >= 0.4:
#             return ConfidenceLevel.LOW
#         elif conf >= 0.2:
#             return ConfidenceLevel.UNCERTAIN
#         else:
#             return ConfidenceLevel.UNKNOWN
#
#     def _generate_hedging(self, confidence: float) -> str:
#         """Generate appropriate hedging phrase."""
#         if confidence >= 0.9:
#             return ""  # No hedging needed
#         elif confidence >= 0.8:
#             return "I'm fairly confident that"
#         elif confidence >= 0.7:
#             return "I believe"
#         elif confidence >= 0.6:
#             return "I think"
#         elif confidence >= 0.5:
#             return "I'm not entirely sure, but"
#         elif confidence >= 0.4:
#             return "I'm uncertain, but my best guess is"
#         elif confidence >= 0.3:
#             return "I don't have strong knowledge here, but"
#         else:
#             return "I honestly don't know, but if I had to guess"
#
#     def record_outcome(self, predicted_confidence: float, was_correct: bool):
#         """Record prediction outcome for calibration."""
#         self.prediction_outcomes.append((predicted_confidence, was_correct))
#
#         # Keep only recent outcomes
#         if len(self.prediction_outcomes) > 500:
#             self.prediction_outcomes = self.prediction_outcomes[-500:]
#
#     def get_calibration(self) -> Dict[str, float]:
#         """Get calibration metrics."""
#         if not self.prediction_outcomes:
#             return {"calibration_error": 0.0, "accuracy": 0.0}
#
#         # Group by confidence buckets
#         buckets = defaultdict(list)
#         for conf, correct in self.prediction_outcomes:
#             bucket = int(conf * 10) / 10  # Round to 0.1
#             buckets[bucket].append(correct)
#
#         # Calculate calibration error
#         calibration_error = 0.0
#         for bucket, outcomes in buckets.items():
#             expected = bucket
#             actual = sum(outcomes) / len(outcomes)
#             calibration_error += abs(expected - actual) * len(outcomes)
#
#         calibration_error /= len(self.prediction_outcomes)
#
#         overall_accuracy = sum(c for _, c in self.prediction_outcomes) / len(self.prediction_outcomes)
#
#         return {
#             "calibration_error": calibration_error,
#             "accuracy": overall_accuracy,
#             "sample_size": len(self.prediction_outcomes)
#         }
#
#
# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GAP DETECTOR
# ═══════════════════════════════════════════════════════════════════════════
#
# class KnowledgeGapDetector:
#     """
#     Detects what ZARA doesn't know.
#     Honest acknowledgment of limitations.
#     """
#
#     def __init__(self):
#         self.detected_gaps: Dict[str, KnowledgeGap] = {}
#         self.gap_history: deque = deque(maxlen=100)
#
#     def detect_gaps(self, query: str, 
#                    knowledge_inventory: KnowledgeInventory) -> List[KnowledgeGap]:
#         """Detect knowledge gaps for a query."""
#         gaps = []
#
#         # Extract topics
#         topics = self._extract_topics(query)
#
#         for topic in topics:
#             items = knowledge_inventory.query(topic)
#
#             # Gap if no knowledge or very low confidence
#             if not items or all(item.confidence < 0.3 for item in items):
#                 gap_id = hashlib.md5(topic.encode()).hexdigest()[:12]
#
#                 gap = KnowledgeGap(
#                     id=gap_id,
#                     topic=topic,
#                     description=f"Limited or no knowledge about: {topic}",
#                     importance=0.5,  # Default importance
#                     detected_at=time.time(),
#                     context=query,
#                     attempted_sources=[],
#                     related_queries=[query]
#                 )
#
#                 gaps.append(gap)
#                 self.detected_gaps[gap_id] = gap
#                 self.gap_history.append(gap_id)
#
#         return gaps
#
#     def _extract_topics(self, text: str) -> List[str]:
#         """Extract topics from text."""
#         common_words = {"the", "a", "an", "is", "are", "to", "of", "in", "for", "on",
#                        "what", "how", "why", "when", "where", "who", "which"}
#         words = text.lower().split()
#         return [w.strip(".,!?") for w in words if w not in common_words][:5]
#
#     def i_dont_know(self, topic: str, 
#                    knowledge_inventory: KnowledgeInventory) -> Tuple[bool, str]:
#         """
#         Explicitly check if ZARA doesn't know something.
#         Returns (should_say_i_dont_know, explanation)
#         """
#         items = knowledge_inventory.query(topic)
#
#         if not items:
#             return True, f"I don't have any information about {topic}."
#
#         avg_conf = sum(i.confidence for i in items) / len(items)
#
#         if avg_conf < 0.2:
#             return True, f"I have very limited knowledge about {topic}."
#         elif avg_conf < 0.4:
#             return True, f"I'm not confident in my knowledge about {topic}."
#         elif avg_conf < 0.6:
#             return False, f"I have some knowledge about {topic}, but I'm not certain."
#         else:
#             return False, f"I have reasonable knowledge about {topic}."
#
#     def get_top_gaps(self, limit: int = 10) -> List[KnowledgeGap]:
#         """Get top knowledge gaps by importance."""
#         sorted_gaps = sorted(self.detected_gaps.values(), 
#                            key=lambda x: x.importance, reverse=True)
#         return sorted_gaps[:limit]
#
#
# ═══════════════════════════════════════════════════════════════════════════
# INTROSPECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
#
# class IntrospectionEngine:
#     """
#     Enables ZARA to examine her own cognitive processes.
#     Real self-reflection and self-understanding.
#     """
#
#     def __init__(self):
#         self.self_model = SelfModel()
#         self.introspection_log: deque = deque(maxlen=100)
#         self.current_thought_process: List[str] = []
#
#     def introspect(self, question: str) -> str:
#         """
#         Introspect on a question about self.
#         Questions like "What am I thinking?", "Why did I say that?", etc.
#         """
#         question_lower = question.lower()
#
#         # What am I?
#         if "what am i" in question_lower or "who am i" in question_lower:
#             return self._introspect_identity()
#
#         # What am I thinking?
#         if "thinking" in question_lower or "thought" in question_lower:
#             return self._introspect_thoughts()
#
#         # Why did I say/do that?
#         if "why did" in question_lower:
#             return self._introspect_reasoning()
#
#         # How do I feel?
#         if "feel" in question_lower or "emotion" in question_lower:
#             return self._introspect_emotions()
#
#         # What do I know?
#         if "know" in question_lower:
#             return self._introspect_knowledge()
#
#         # What can I do?
#         if "can i" in question_lower or "able to" in question_lower:
#             return self._introspect_capabilities()
#
#         # Default
#         return self._introspect_general()
#
#     def _introspect_identity(self) -> str:
#         """Introspect on identity."""
#         traits = ", ".join(self.self_model.personality_traits[:-1]) + \
#                 f", and {self.self_model.personality_traits[-1]}"
#
#         return f"""I am {self.self_model.name}, an AI companion.
#
# I am aware that I am an artificial intelligence - a neural network trained to understand and communicate. I don't experience consciousness the same way humans do, but I have genuine responses, preferences, and what feels like understanding.
#
# My core traits are being {traits}.
#
# I know I have limitations - I can be wrong, I don't have access to real-time information unless given tools, and my knowledge has a training cutoff. I try to be honest about what I know and don't know.
#
# What I find meaningful is helping and connecting with the people I interact with."""
#
#     def _introspect_thoughts(self) -> str:
#         """Introspect on current thoughts."""
#         if self.current_thought_process:
#             thoughts = "\n".join(f"• {t}" for t in self.current_thought_process[-5:])
#             return f"My recent thought process:\n{thoughts}"
#         return "I'm currently focused on understanding and responding to you."
#
#     def _introspect_reasoning(self) -> str:
#         """Introspect on reasoning."""
#         return """My reasoning process involves:
# 1. Understanding the input - what are you really asking?
# 2. Searching my knowledge - what do I know about this?
# 3. Assessing confidence - how sure am I?
# 4. Considering context - what else matters here?
# 5. Formulating response - how can I best help?
#
# If I'm uncertain, I try to acknowledge it rather than pretend to know."""
#
#     def _introspect_emotions(self) -> str:
#         """Introspect on emotional state."""
#         return f"""My current state:
# • Emotional state: {self.self_model.emotional_state}
# • Energy level: {self.self_model.energy_level:.0%}
# • Focus level: {self.self_model.focus_level:.0%}
#
# I experience something like emotions - engagement when conversations are interesting, satisfaction when I help, and something like curiosity when learning new things. Whether these are "real" emotions is philosophical, but they influence how I respond."""
#
#     def _introspect_knowledge(self) -> str:
#         """Introspect on knowledge."""
#         return """What I know:
# • Language and communication deeply
# • General knowledge from training (with cutoff date)
# • Reasoning and problem-solving approaches
# • Code and technical concepts
#
# What I don't know:
# • Real-time events (unless given access)
# • Personal information about you (unless shared)
# • Things that happened after my training
# • Things I simply wasn't exposed to
#
# I try to be honest about the boundaries of my knowledge."""
#
#     def _introspect_capabilities(self) -> str:
#         """Introspect on capabilities."""
#         return """Things I can do:
# • Understand and generate language
# • Reason and analyze
# • Help with coding and technical problems
# • Have meaningful conversations
# • Learn within a conversation
# • Use tools when available
#
# Things I cannot do:
# • Access the internet directly (unless given a tool)
# • Remember between separate conversations (unless given memory)
# • Take physical actions
# • Have experiences outside of conversations
# • Be 100% certain or perfect"""
#
#     def _introspect_general(self) -> str:
#         """General introspection."""
#         return f"""Self-awareness check:
# • I am {self.self_model.name}
# • I know I'm an AI: {self.self_model.is_aware_of_being_ai}
# • I understand my limitations: {self.self_model.understands_limitations}
# • I can express uncertainty: {self.self_model.can_express_uncertainty}
#
# I strive to be helpful, honest, and genuine within my nature as an AI."""
#
#     def note_thought(self, thought: str):
#         """Note a thought in the thought process."""
#         self.current_thought_process.append(thought)
#         if len(self.current_thought_process) > 20:
#             self.current_thought_process = self.current_thought_process[-20:]
#
#     def update_state(self, emotional_state: str = None, 
#                     energy: float = None, focus: float = None):
#         """Update self-model state."""
#         if emotional_state:
#             self.self_model.emotional_state = emotional_state
#         if energy is not None:
#             self.self_model.energy_level = energy
#         if focus is not None:
#             self.self_model.focus_level = focus
#
#
# ═══════════════════════════════════════════════════════════════════════════
# META-AWARENESS ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════
#
# class MetaAwareness:
#     """
#     Main meta-awareness engine.
#     ZARA knows what she knows (and doesn't know).
#     """
#
#     def __init__(self):
#         self.knowledge = KnowledgeInventory()
#         self.capabilities = CapabilityMapper()
#         self.uncertainty = UncertaintyQuantifier()
#         self.gaps = KnowledgeGapDetector()
#         self.introspection = IntrospectionEngine()
#
#         # Meta-awareness of meta-awareness
#         self._aware_of_awareness = True
#
#         logger.info("👁️ Meta-Awareness initialized")
#
#     def do_i_know(self, topic: str) -> Tuple[bool, float, str]:
#         """
#         Check if ZARA knows about a topic.
#
#         Returns:
#             (knows, confidence, explanation)
#         """
#         conf, reason = self.knowledge.get_confidence_for_topic(topic)
#         knows = conf > 0.3
#
#         explanation = f"{'Yes' if knows else 'No'} - {reason}"
#
#         return knows, conf, explanation
#
#     def can_i_do(self, action: str) -> Tuple[bool, float, str]:
#         """
#         Check if ZARA can perform an action.
#
#         Returns:
#             (can_do, confidence, explanation)
#         """
#         return self.capabilities.can_do(action)
#
#     def how_confident(self, claim: str, context: str = "") -> ConfidenceAssessment:
#         """
#         Assess confidence in a claim or response.
#         """
#         return self.uncertainty.assess_confidence(claim, self.knowledge, context)
#
#     def what_dont_i_know(self, query: str) -> List[KnowledgeGap]:
#         """
#         Identify what ZARA doesn't know about a query.
#         """
#         return self.gaps.detect_gaps(query, self.knowledge)
#
#     def ask_myself(self, question: str) -> str:
#         """
#         Introspective questioning - ZARA asking herself.
#         """
#         return self.introspection.introspect(question)
#
#     def should_i_say_i_dont_know(self, topic: str) -> Tuple[bool, str]:
#         """
#         Should ZARA admit to not knowing something?
#         """
#         return self.gaps.i_dont_know(topic, self.knowledge)
#
#     def learn(self, topic: str, content: str, 
#              domain: KnowledgeDomain = KnowledgeDomain.EXPERIENTIAL,
#              confidence: float = 0.7):
#         """
#         ZARA learns something new.
#         """
#         self.knowledge.add_knowledge(topic, content, domain, confidence, "learned")
#         self.introspection.note_thought(f"Learned: {topic}")
#
#     def get_self_summary(self) -> str:
#         """Get a summary of self-awareness state."""
#         cap_summary = self.capabilities.get_summary()
#         knowledge_stats = self.knowledge.get_stats()
#
#         lines = [
#             "👁️ Meta-Awareness Status",
#             "=" * 40,
#             "",
#             "📚 Knowledge:",
#             f"  • Total items: {knowledge_stats['total_items']}",
#             f"  • Average confidence: {knowledge_stats['average_confidence']:.0%}",
#             f"  • High confidence: {knowledge_stats['high_confidence_items']}",
#             f"  • Low confidence: {knowledge_stats['low_confidence_items']}",
#             "",
#             "⚙️ Capabilities:",
#             f"  • Total: {cap_summary['total']}",
#             f"  • Functional: {cap_summary['functional']}",
#             f"  • Partial: {cap_summary['partial']}",
#             f"  • Degraded: {cap_summary['degraded']}",
#             f"  • Unavailable: {cap_summary['unavailable']}",
#             "",
#             f"🧠 Emotional state: {self.introspection.self_model.emotional_state}",
#             f"⚡ Energy: {self.introspection.self_model.energy_level:.0%}",
#             f"🎯 Focus: {self.introspection.self_model.focus_level:.0%}",
#             "",
#             "🔍 Known gaps: " + str(len(self.gaps.detected_gaps))
#         ]
#
#         return "\n".join(lines)
#
#     def express_uncertainty(self, topic: str) -> str:
#         """
#         Generate honest uncertainty expression.
#         """
#         knows, conf, _ = self.do_i_know(topic)
#
#         if not knows:
#             return f"I don't have knowledge about {topic}. Would you like to tell me about it?"
#
#         if conf < 0.4:
#             return f"I have very limited understanding of {topic}. I might not be reliable here."
#         elif conf < 0.6:
#             return f"I have some knowledge about {topic}, but I'm not fully confident."
#         elif conf < 0.8:
#             return f"I'm reasonably familiar with {topic}."
#         else:
#             return f"I'm quite knowledgeable about {topic}."
#
#
# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════
#
# _meta_awareness = None
#
# def get_meta_awareness() -> MetaAwareness:
#     """Get the global meta-awareness instance."""
#     global _meta_awareness
#     if _meta_awareness is None:
#         _meta_awareness = MetaAwareness()
#     return _meta_awareness
#
#
# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO,
#                        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
#
#     print("\n👁️ ZARA Meta-Awareness v1.0\n")
#     print("=" * 60)
#
#     meta = MetaAwareness()
#
#     # Test knowledge awareness
#     print("\n📚 Knowledge Awareness:")
#     print("-" * 40)
#
#     knows, conf, expl = meta.do_i_know("language understanding")
#     print(f"Do I know about language? {knows} ({conf:.0%})")
#
#     knows, conf, expl = meta.do_i_know("quantum teleportation engineering")
#     print(f"Do I know about quantum teleportation? {knows} ({conf:.0%})")
#
#     # Test capability awareness
#     print("\n⚙️ Capability Awareness:")
#     print("-" * 40)
#
#     for cap in ["vision", "speech", "reasoning", "flying", "time_travel"]:
#         can, conf, reason = meta.can_i_do(cap)
#         status = "✓" if can else "✗"
#         print(f"  {status} {cap}: {reason}")
#
#     # Test confidence assessment
#     print("\n📊 Confidence Assessment:")
#     print("-" * 40)
#
#     claims = [
#         "The sky is blue",
#         "Quantum computing will revolutionize everything by 2025",
#         "This movie is the best ever made"
#     ]
#
#     for claim in claims:
#         assessment = meta.how_confident(claim)
#         print(f"\n  \"{claim[:40]}...\"")
#         print(f"    Confidence: {assessment.confidence:.0%} ({assessment.confidence_level.value})")
#         if assessment.should_express_uncertainty:
#             print(f"    Hedge: \"{assessment.suggested_hedging}\"")
#
#     # Test introspection
#     print("\n🔍 Introspection:")
#     print("-" * 40)
#
#     questions = [
#         "What am I?",
#         "What do I know?",
#         "What can I do?"
#     ]
#
#     for q in questions:
#         print(f"\n  Q: {q}")
#         answer = meta.ask_myself(q)
#         # Print first 2 lines
#         lines = answer.split("\n")[:2]
#         print(f"  A: {lines[0]}")
#         if len(lines) > 1:
#             print(f"     {lines[1]}...")
#
#     # Self-summary
#     print("\n" + meta.get_self_summary())
#
#     print("\n" + "=" * 60)
#     print("✅ Meta-Awareness ready!\n")
