"""
ZARA Creative Synthesis v1.0
=============================
Generate Novel Ideas by Combining Distant Concepts

True creative intelligence that enables:
1. CONCEPT BLENDING - Merge unrelated ideas into new ones
2. ANALOGICAL REASONING - Find deep structural similarities
3. CROSS-DOMAIN TRANSFER - Apply ideas from one field to another
4. DIVERGENT THINKING - Generate many varied possibilities
5. LATERAL CONNECTIONS - Find unexpected relationships
6. BISOCIATION - Clash different frames of reference
7. MORPHOLOGICAL ANALYSIS - Systematic combination exploration
8. SERENDIPITOUS DISCOVERY - Embrace creative accidents
9. CONSTRAINT-BASED CREATIVITY - Use limits as springboards
10. EMERGENT IDEATION - Let ideas evolve and combine

This makes ZARA truly creative, generating original ideas
that no one has thought of before by combining concepts
in novel, unexpected ways.
"""

import logging
import time
import sys
import random
import hashlib
import itertools
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_CREATIVE")


# ═══════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class CreativeMode(Enum):
    """Modes of creative thinking."""
    DIVERGENT = "divergent"           # Generate many ideas
    CONVERGENT = "convergent"         # Focus and refine
    LATERAL = "lateral"               # Sideways thinking
    ANALOGICAL = "analogical"         # Find similarities
    BISOCIATIVE = "bisociative"       # Clash frames
    MORPHOLOGICAL = "morphological"   # Systematic combination
    SERENDIPITOUS = "serendipitous"   # Random discovery


class IdeaQuality(Enum):
    """Quality levels for generated ideas."""
    BREAKTHROUGH = "breakthrough"     # Truly novel
    INNOVATIVE = "innovative"         # Fresh combination
    INTERESTING = "interesting"       # Worth exploring
    CONVENTIONAL = "conventional"     # Standard approach
    WEAK = "weak"                     # Needs work


@dataclass
class Concept:
    """A concept for creative synthesis."""
    id: str
    name: str
    domain: str
    properties: List[str]
    functions: List[str]
    associations: List[str]
    metaphors: List[str]
    constraints: List[str]


@dataclass
class Blend:
    """A blend of two or more concepts."""
    id: str
    source_concepts: List[str]
    blended_name: str
    description: str
    novel_properties: List[str]
    novel_functions: List[str]
    emergent_features: List[str]
    quality: IdeaQuality
    novelty_score: float
    usefulness_score: float
    surprise_score: float


@dataclass
class Analogy:
    """An analogy between domains."""
    id: str
    source_domain: str
    target_domain: str
    source_concept: str
    target_concept: str
    structural_mappings: Dict[str, str]
    inferences: List[str]
    quality: float


@dataclass
class CreativeIdea:
    """A creative idea generated through synthesis."""
    id: str
    title: str
    description: str
    source_concepts: List[str]
    creative_mode: CreativeMode
    novelty: float
    usefulness: float
    surprise: float
    elaboration: str
    potential_applications: List[str]
    challenges: List[str]
    next_steps: List[str]
    timestamp: float


# ═══════════════════════════════════════════════════════════════════════════
# CONCEPT SPACE
# ═══════════════════════════════════════════════════════════════════════════

class ConceptSpace:
    """
    A rich space of concepts for creative combination.
    Contains knowledge about concepts, their properties, and relationships.
    """
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.domain_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.concept_embeddings: Dict[str, List[float]] = {}
        
        # Initialize with seed concepts across domains
        self._seed_concepts()
    
    def _seed_concepts(self):
        """Seed the concept space with diverse concepts."""
        seed_data = [
            # Nature
            ("tree", "nature", ["roots", "branches", "leaves", "growth"], 
             ["provides shade", "produces oxygen", "stores carbon"],
             ["forest", "wood", "life", "growth"], ["family tree", "branching logic"]),
            
            ("river", "nature", ["flowing", "water", "path", "source", "delta"],
             ["transports", "erodes", "nourishes", "connects"],
             ["ocean", "rain", "fish", "bridge"], ["flow of time", "stream of consciousness"]),
            
            ("butterfly", "nature", ["wings", "metamorphosis", "colors", "fragile"],
             ["pollinates", "transforms", "migrates"],
             ["caterpillar", "flower", "beauty"], ["butterfly effect", "social butterfly"]),
            
            # Technology
            ("network", "technology", ["nodes", "connections", "protocols", "distributed"],
             ["connects", "transfers", "scales", "routes"],
             ["internet", "social", "neural"], ["neural network", "social network"]),
            
            ("algorithm", "technology", ["steps", "logic", "efficiency", "input/output"],
             ["solves", "optimizes", "automates", "decides"],
             ["code", "computation", "AI"], ["recipe", "dance moves"]),
            
            ("interface", "technology", ["boundary", "translation", "interaction", "abstraction"],
             ["connects", "simplifies", "mediates", "enables"],
             ["user", "API", "design"], ["window to the soul", "bridge"]),
            
            # Music
            ("rhythm", "music", ["beat", "tempo", "pattern", "pulse"],
             ["organizes time", "creates movement", "induces emotion"],
             ["dance", "heart", "poetry"], ["rhythm of life", "heartbeat"]),
            
            ("harmony", "music", ["chords", "consonance", "dissonance", "resolution"],
             ["creates beauty", "resolves tension", "blends"],
             ["melody", "peace", "agreement"], ["social harmony", "color harmony"]),
            
            # Architecture
            ("bridge", "architecture", ["span", "support", "connection", "load-bearing"],
             ["connects", "overcomes obstacles", "enables passage"],
             ["river", "gap", "engineering"], ["bridge the gap", "burn bridges"]),
            
            ("foundation", "architecture", ["base", "stability", "underground", "load-distribution"],
             ["supports", "grounds", "enables building"],
             ["building", "ground", "strength"], ["foundation of knowledge", "foundational"]),
            
            # Psychology
            ("memory", "psychology", ["storage", "retrieval", "encoding", "association"],
             ["preserves", "reconstructs", "connects past to present"],
             ["learning", "nostalgia", "identity"], ["memory palace", "muscle memory"]),
            
            ("creativity", "psychology", ["novelty", "combination", "insight", "fluency"],
             ["generates new", "solves problems", "expresses"],
             ["art", "innovation", "imagination"], ["creative spark", "outside the box"]),
            
            # Biology  
            ("ecosystem", "biology", ["interdependence", "balance", "diversity", "energy flow"],
             ["sustains", "adapts", "evolves", "cycles"],
             ["nature", "food web", "habitat"], ["business ecosystem", "digital ecosystem"]),
            
            ("evolution", "biology", ["adaptation", "selection", "mutation", "fitness"],
             ["adapts", "optimizes", "diversifies", "survives"],
             ["species", "time", "change"], ["idea evolution", "language evolution"]),
            
            # Physics
            ("wave", "physics", ["oscillation", "frequency", "amplitude", "propagation"],
             ["transmits energy", "interferes", "diffracts"],
             ["sound", "light", "ocean"], ["wave of change", "new wave"]),
            
            ("gravity", "physics", ["attraction", "mass", "force", "curvature"],
             ["attracts", "bends space", "grounds"],
             ["weight", "orbits", "falling"], ["social gravity", "gravitas"]),
            
            # Art
            ("canvas", "art", ["surface", "blank", "potential", "frame"],
             ["receives", "displays", "bounds", "preserves"],
             ["painting", "artist", "creation"], ["blank canvas", "life's canvas"]),
            
            ("perspective", "art", ["viewpoint", "depth", "vanishing point", "horizon"],
             ["creates depth", "simulates 3D", "guides eye"],
             ["vision", "understanding", "angle"], ["different perspective", "gain perspective"]),
            
            # Cooking
            ("fermentation", "cooking", ["transformation", "time", "microbes", "flavor"],
             ["transforms", "preserves", "develops complexity"],
             ["wine", "bread", "cheese"], ["ferment ideas", "brewing trouble"]),
            
            ("fusion", "cooking", ["combination", "cultures", "innovation", "blend"],
             ["combines traditions", "creates new", "surprises"],
             ["cuisine", "creativity", "culture"], ["nuclear fusion", "jazz fusion"]),
        ]
        
        for name, domain, props, funcs, assocs, metaphors in seed_data:
            concept_id = f"{domain}_{name}"
            self.concepts[concept_id] = Concept(
                id=concept_id,
                name=name,
                domain=domain,
                properties=props,
                functions=funcs,
                associations=assocs,
                metaphors=metaphors,
                constraints=[]
            )
            self.domain_concepts[domain].add(concept_id)
    
    def add_concept(self, name: str, domain: str, 
                   properties: List[str] = None,
                   functions: List[str] = None,
                   associations: List[str] = None) -> Concept:
        """Add a new concept to the space."""
        concept_id = f"{domain}_{name}_{int(time.time())}"
        
        concept = Concept(
            id=concept_id,
            name=name,
            domain=domain,
            properties=properties or [],
            functions=functions or [],
            associations=associations or [],
            metaphors=[],
            constraints=[]
        )
        
        self.concepts[concept_id] = concept
        self.domain_concepts[domain].add(concept_id)
        
        return concept
    
    def get_distant_concepts(self, concept_id: str, n: int = 5) -> List[Concept]:
        """Get concepts that are distant/different from given concept."""
        if concept_id not in self.concepts:
            return list(self.concepts.values())[:n]
        
        source = self.concepts[concept_id]
        source_domain = source.domain
        
        # Prioritize concepts from different domains
        distant = []
        for cid, concept in self.concepts.items():
            if cid != concept_id and concept.domain != source_domain:
                # Calculate distance (more different = higher score)
                overlap = len(set(source.properties) & set(concept.properties))
                distance = 1.0 / (1 + overlap)
                distant.append((distance, concept))
        
        # Sort by distance (most distant first) with some randomness
        random.shuffle(distant)
        distant.sort(key=lambda x: x[0], reverse=True)
        
        return [c for _, c in distant[:n]]
    
    def get_random_concepts(self, n: int = 2, exclude_domain: str = None) -> List[Concept]:
        """Get random concepts for creative combination."""
        available = list(self.concepts.values())
        if exclude_domain:
            available = [c for c in available if c.domain != exclude_domain]
        
        random.shuffle(available)
        return available[:n]
    
    def find_bridging_concepts(self, concept_a: str, concept_b: str) -> List[Concept]:
        """Find concepts that could bridge two distant concepts."""
        if concept_a not in self.concepts or concept_b not in self.concepts:
            return []
        
        a = self.concepts[concept_a]
        b = self.concepts[concept_b]
        
        # Find concepts that share properties with both
        bridges = []
        for cid, concept in self.concepts.items():
            if cid in [concept_a, concept_b]:
                continue
            
            overlap_a = len(set(a.properties) & set(concept.properties))
            overlap_b = len(set(b.properties) & set(concept.properties))
            
            if overlap_a > 0 and overlap_b > 0:
                bridges.append((overlap_a + overlap_b, concept))
        
        bridges.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in bridges[:5]]


# ═══════════════════════════════════════════════════════════════════════════
# CONCEPT BLENDER
# ═══════════════════════════════════════════════════════════════════════════

class ConceptBlender:
    """
    Blends concepts to create novel combinations.
    Implements conceptual blending theory.
    """
    
    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space
        self.blends: Dict[str, Blend] = {}
    
    def blend(self, concept_ids: List[str]) -> Blend:
        """
        Blend multiple concepts into a new emergent concept.
        """
        concepts = [self.concept_space.concepts[cid] 
                   for cid in concept_ids if cid in self.concept_space.concepts]
        
        if len(concepts) < 2:
            raise ValueError("Need at least 2 concepts to blend")
        
        # Generate blended name
        names = [c.name for c in concepts]
        blended_name = self._generate_blend_name(names)
        
        # Combine properties (select some from each)
        all_props = []
        for c in concepts:
            all_props.extend(c.properties[:2])  # Top 2 from each
        novel_properties = list(set(all_props))
        
        # Combine functions
        all_funcs = []
        for c in concepts:
            all_funcs.extend(c.functions[:2])
        novel_functions = list(set(all_funcs))
        
        # Generate emergent features (new things that arise from combination)
        emergent = self._generate_emergent_features(concepts)
        
        # Calculate quality scores
        novelty = self._calculate_novelty(concepts)
        usefulness = self._calculate_usefulness(emergent, novel_functions)
        surprise = self._calculate_surprise(concepts)
        
        quality = self._assess_quality(novelty, usefulness, surprise)
        
        # Generate description
        description = self._generate_description(concepts, emergent)
        
        blend_id = hashlib.md5(f"{'-'.join(concept_ids)}:{time.time()}".encode()).hexdigest()[:12]
        
        blend = Blend(
            id=blend_id,
            source_concepts=concept_ids,
            blended_name=blended_name,
            description=description,
            novel_properties=novel_properties,
            novel_functions=novel_functions,
            emergent_features=emergent,
            quality=quality,
            novelty_score=novelty,
            usefulness_score=usefulness,
            surprise_score=surprise
        )
        
        self.blends[blend_id] = blend
        return blend
    
    def _generate_blend_name(self, names: List[str]) -> str:
        """Generate a creative name for the blend."""
        # Various blending strategies
        strategies = [
            # Portmanteau
            lambda: names[0][:len(names[0])//2] + names[1][len(names[1])//2:],
            # Compound
            lambda: f"{names[0]}-{names[1]}",
            # Descriptor
            lambda: f"{names[0]}-like {names[1]}",
            # New word
            lambda: f"{names[0][0]}{names[1]}"
        ]
        
        return random.choice(strategies)()
    
    def _generate_emergent_features(self, concepts: List[Concept]) -> List[str]:
        """Generate emergent features from concept combination."""
        emergent = []
        
        # Cross-property inference
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                # Combine properties to create new features
                for p1 in c1.properties[:2]:
                    for p2 in c2.properties[:2]:
                        if p1 != p2:
                            emergent.append(f"{p1} with {p2}")
                
                # Combine functions
                for f1 in c1.functions[:1]:
                    for f2 in c2.functions[:1]:
                        if f1 != f2:
                            emergent.append(f"{f1} while {f2}")
        
        # Metaphor crossing
        for c in concepts:
            for metaphor in c.metaphors[:1]:
                emergent.append(f"Metaphorical: {metaphor}")
        
        return emergent[:5]  # Top 5 emergent features
    
    def _generate_description(self, concepts: List[Concept], emergent: List[str]) -> str:
        """Generate a description of the blend."""
        names = [c.name for c in concepts]
        domains = list(set(c.domain for c in concepts))
        
        desc = f"A creative fusion of {' and '.join(names)}, "
        desc += f"combining principles from {' and '.join(domains)}. "
        
        if emergent:
            desc += f"Key emergent properties: {', '.join(emergent[:2])}."
        
        return desc
    
    def _calculate_novelty(self, concepts: List[Concept]) -> float:
        """Calculate novelty score (how different are the source concepts)."""
        if len(concepts) < 2:
            return 0.5
        
        domains = set(c.domain for c in concepts)
        domain_diversity = len(domains) / len(concepts)
        
        # Property overlap (less overlap = more novel)
        all_props = [set(c.properties) for c in concepts]
        if len(all_props) >= 2:
            overlap = len(all_props[0] & all_props[1]) / max(len(all_props[0] | all_props[1]), 1)
            prop_novelty = 1 - overlap
        else:
            prop_novelty = 0.5
        
        return (domain_diversity + prop_novelty) / 2
    
    def _calculate_usefulness(self, emergent: List[str], functions: List[str]) -> float:
        """Calculate usefulness score."""
        # More emergent features and functions = more useful
        emergence_score = min(1.0, len(emergent) / 5)
        function_score = min(1.0, len(functions) / 4)
        return (emergence_score + function_score) / 2
    
    def _calculate_surprise(self, concepts: List[Concept]) -> float:
        """Calculate surprise score (unexpectedness of combination)."""
        domains = [c.domain for c in concepts]
        
        # More different domains = more surprising
        unique_domains = len(set(domains))
        surprise = unique_domains / len(domains)
        
        # Add randomness factor
        surprise += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(1.0, surprise))
    
    def _assess_quality(self, novelty: float, usefulness: float, surprise: float) -> IdeaQuality:
        """Assess overall quality of the blend."""
        avg = (novelty + usefulness + surprise) / 3
        
        if avg >= 0.8:
            return IdeaQuality.BREAKTHROUGH
        elif avg >= 0.65:
            return IdeaQuality.INNOVATIVE
        elif avg >= 0.5:
            return IdeaQuality.INTERESTING
        elif avg >= 0.35:
            return IdeaQuality.CONVENTIONAL
        else:
            return IdeaQuality.WEAK


# ═══════════════════════════════════════════════════════════════════════════
# ANALOGY ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class AnalogyEngine:
    """
    Finds and creates analogies between domains.
    Enables cross-domain reasoning and transfer.
    """
    
    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space
        self.analogies: Dict[str, Analogy] = {}
    
    def find_analogy(self, source_concept_id: str, target_domain: str) -> Optional[Analogy]:
        """
        Find an analogy from source concept to target domain.
        """
        if source_concept_id not in self.concept_space.concepts:
            return None
        
        source = self.concept_space.concepts[source_concept_id]
        
        # Find best matching concept in target domain
        target_concepts = [
            self.concept_space.concepts[cid] 
            for cid in self.concept_space.domain_concepts.get(target_domain, [])
        ]
        
        if not target_concepts:
            return None
        
        best_match = None
        best_score = 0
        best_mappings = {}
        
        for target in target_concepts:
            score, mappings = self._calculate_structural_similarity(source, target)
            if score > best_score:
                best_score = score
                best_match = target
                best_mappings = mappings
        
        if not best_match:
            return None
        
        # Generate inferences from the analogy
        inferences = self._generate_inferences(source, best_match, best_mappings)
        
        analogy_id = hashlib.md5(f"{source_concept_id}:{best_match.id}".encode()).hexdigest()[:12]
        
        analogy = Analogy(
            id=analogy_id,
            source_domain=source.domain,
            target_domain=target_domain,
            source_concept=source.name,
            target_concept=best_match.name,
            structural_mappings=best_mappings,
            inferences=inferences,
            quality=best_score
        )
        
        self.analogies[analogy_id] = analogy
        return analogy
    
    def _calculate_structural_similarity(self, source: Concept, 
                                         target: Concept) -> Tuple[float, Dict[str, str]]:
        """Calculate structural similarity between concepts."""
        mappings = {}
        score = 0
        
        # Map properties
        for sp in source.properties:
            for tp in target.properties:
                # Simple similarity heuristic
                if sp.split()[0] == tp.split()[0]:  # Same starting word
                    mappings[sp] = tp
                    score += 0.2
                    break
        
        # Map functions
        for sf in source.functions:
            for tf in target.functions:
                sf_verb = sf.split()[0] if sf else ""
                tf_verb = tf.split()[0] if tf else ""
                if sf_verb == tf_verb:
                    mappings[sf] = tf
                    score += 0.3
                    break
        
        # Bonus for same number of properties (structural alignment)
        if len(source.properties) == len(target.properties):
            score += 0.1
        
        return min(1.0, score), mappings
    
    def _generate_inferences(self, source: Concept, target: Concept,
                            mappings: Dict[str, str]) -> List[str]:
        """Generate inferences from the analogy."""
        inferences = []
        
        # Infer unmapped properties
        unmapped_source = [p for p in source.properties if p not in mappings]
        
        for prop in unmapped_source[:2]:
            inferences.append(
                f"If {source.name} has {prop}, then {target.name} might have something analogous"
            )
        
        # Infer from functions
        for sf, tf in list(mappings.items())[:2]:
            inferences.append(
                f"Just as {source.name} {sf}, {target.name} {tf}"
            )
        
        return inferences
    
    def create_new_analogy(self, source_concept: str, target_concept: str,
                          explanation: str) -> Analogy:
        """Create a new analogy (not from discovery but from insight)."""
        analogy_id = hashlib.md5(f"new:{source_concept}:{target_concept}".encode()).hexdigest()[:12]
        
        analogy = Analogy(
            id=analogy_id,
            source_domain="custom",
            target_domain="custom",
            source_concept=source_concept,
            target_concept=target_concept,
            structural_mappings={"concept": target_concept},
            inferences=[explanation],
            quality=0.7
        )
        
        self.analogies[analogy_id] = analogy
        return analogy


# ═══════════════════════════════════════════════════════════════════════════
# DIVERGENT THINKER
# ═══════════════════════════════════════════════════════════════════════════

class DivergentThinker:
    """
    Generates many diverse ideas through divergent thinking.
    Quantity breeds quality in brainstorming.
    """
    
    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space
    
    def brainstorm(self, seed: str, count: int = 10) -> List[Dict]:
        """
        Brainstorm ideas starting from a seed concept or problem.
        """
        ideas = []
        
        # Different thinking strategies
        strategies = [
            self._substitute,
            self._combine,
            self._adapt,
            self._modify,
            self._put_to_other_uses,
            self._eliminate,
            self._reverse
        ]
        
        for i in range(count):
            strategy = strategies[i % len(strategies)]
            idea = strategy(seed)
            ideas.append(idea)
        
        return ideas
    
    def _substitute(self, seed: str) -> Dict:
        """What can be substituted?"""
        concepts = self.concept_space.get_random_concepts(1)
        substitute = concepts[0].name if concepts else "alternative"
        
        return {
            "strategy": "substitute",
            "idea": f"Replace {seed} with {substitute}",
            "question": f"What if we used {substitute} instead of {seed}?",
            "novelty": random.uniform(0.5, 0.9)
        }
    
    def _combine(self, seed: str) -> Dict:
        """What can be combined?"""
        concepts = self.concept_space.get_random_concepts(1)
        combine_with = concepts[0].name if concepts else "something else"
        
        return {
            "strategy": "combine",
            "idea": f"Combine {seed} with {combine_with}",
            "question": f"What happens when {seed} meets {combine_with}?",
            "novelty": random.uniform(0.6, 0.95)
        }
    
    def _adapt(self, seed: str) -> Dict:
        """What can be adapted?"""
        domains = list(self.concept_space.domain_concepts.keys())
        new_domain = random.choice(domains) if domains else "new context"
        
        return {
            "strategy": "adapt",
            "idea": f"Adapt {seed} for {new_domain}",
            "question": f"How would {seed} work in {new_domain}?",
            "novelty": random.uniform(0.5, 0.85)
        }
    
    def _modify(self, seed: str) -> Dict:
        """What can be modified?"""
        modifications = ["bigger", "smaller", "faster", "slower", "simpler", "more complex",
                        "inverted", "distributed", "centralized", "automated"]
        mod = random.choice(modifications)
        
        return {
            "strategy": "modify",
            "idea": f"Make {seed} {mod}",
            "question": f"What if {seed} was {mod}?",
            "novelty": random.uniform(0.4, 0.8)
        }
    
    def _put_to_other_uses(self, seed: str) -> Dict:
        """What other uses?"""
        uses = ["entertainment", "education", "therapy", "art", "science",
               "social connection", "productivity", "health", "environment"]
        new_use = random.choice(uses)
        
        return {
            "strategy": "other_uses",
            "idea": f"Use {seed} for {new_use}",
            "question": f"How could {seed} be applied to {new_use}?",
            "novelty": random.uniform(0.5, 0.9)
        }
    
    def _eliminate(self, seed: str) -> Dict:
        """What can be eliminated?"""
        aspects = ["the complexity", "the cost", "the time", "the physical form",
                  "the human element", "the technology", "the middleman"]
        eliminate = random.choice(aspects)
        
        return {
            "strategy": "eliminate",
            "idea": f"Remove {eliminate} from {seed}",
            "question": f"What if {seed} had no {eliminate}?",
            "novelty": random.uniform(0.5, 0.85)
        }
    
    def _reverse(self, seed: str) -> Dict:
        """What can be reversed?"""
        reversals = ["the order", "the direction", "the roles", "the timing",
                    "the perspective", "the assumption", "cause and effect"]
        reverse = random.choice(reversals)
        
        return {
            "strategy": "reverse",
            "idea": f"Reverse {reverse} in {seed}",
            "question": f"What if we flipped {reverse} in {seed}?",
            "novelty": random.uniform(0.6, 0.95)
        }


# ═══════════════════════════════════════════════════════════════════════════
# LATERAL CONNECTOR
# ═══════════════════════════════════════════════════════════════════════════

class LateralConnector:
    """
    Makes lateral (sideways) connections between unrelated concepts.
    The key to breakthrough creativity.
    """
    
    def __init__(self, concept_space: ConceptSpace):
        self.concept_space = concept_space
        self.connections: List[Dict] = []
    
    def connect(self, concept_a: str, concept_b: str) -> Dict:
        """
        Find a lateral connection between two concepts.
        """
        # Get the concepts
        concept_obj_a = None
        concept_obj_b = None
        
        for cid, concept in self.concept_space.concepts.items():
            if concept.name == concept_a or cid == concept_a:
                concept_obj_a = concept
            if concept.name == concept_b or cid == concept_b:
                concept_obj_b = concept
        
        if not concept_obj_a or not concept_obj_b:
            return self._create_abstract_connection(concept_a, concept_b)
        
        # Find connection strategies
        connections = []
        
        # 1. Shared metaphor
        shared_metaphors = set(concept_obj_a.metaphors) & set(concept_obj_b.metaphors)
        if shared_metaphors:
            connections.append({
                "type": "shared_metaphor",
                "via": list(shared_metaphors)[0],
                "insight": f"Both {concept_a} and {concept_b} share the metaphor: {list(shared_metaphors)[0]}"
            })
        
        # 2. Function analogy
        for fa in concept_obj_a.functions:
            for fb in concept_obj_b.functions:
                fa_verb = fa.split()[0] if fa else ""
                fb_verb = fb.split()[0] if fb else ""
                if fa_verb == fb_verb:
                    connections.append({
                        "type": "function_analogy",
                        "via": fa_verb,
                        "insight": f"Both {concept_a} and {concept_b} can {fa_verb}..."
                    })
        
        # 3. Property bridge
        shared_props = set(concept_obj_a.properties) & set(concept_obj_b.properties)
        if shared_props:
            connections.append({
                "type": "property_bridge",
                "via": list(shared_props)[0],
                "insight": f"Both share the property: {list(shared_props)[0]}"
            })
        
        # 4. Abstract connection (always possible)
        abstract = self._find_abstract_link(concept_obj_a, concept_obj_b)
        connections.append(abstract)
        
        # Pick the best/most interesting connection
        best = max(connections, key=lambda c: len(c.get("insight", "")))
        
        result = {
            "concept_a": concept_a,
            "concept_b": concept_b,
            "connection": best,
            "creative_potential": random.uniform(0.6, 0.95)
        }
        
        self.connections.append(result)
        return result
    
    def _find_abstract_link(self, concept_a: Concept, concept_b: Concept) -> Dict:
        """Find an abstract/philosophical link."""
        abstract_frames = [
            "transformation", "connection", "growth", "balance",
            "flow", "emergence", "pattern", "scale", "time", "change"
        ]
        
        frame = random.choice(abstract_frames)
        
        return {
            "type": "abstract",
            "via": frame,
            "insight": f"Through the lens of {frame}, {concept_a.name} and {concept_b.name} "
                      f"both represent aspects of {frame} in their respective domains"
        }
    
    def _create_abstract_connection(self, a: str, b: str) -> Dict:
        """Create connection for unknown concepts."""
        frames = ["transformation", "duality", "emergence", "cycles", "networks"]
        frame = random.choice(frames)
        
        return {
            "concept_a": a,
            "concept_b": b,
            "connection": {
                "type": "abstract",
                "via": frame,
                "insight": f"Both {a} and {b} can be understood through {frame}"
            },
            "creative_potential": random.uniform(0.5, 0.8)
        }
    
    def random_connection(self) -> Dict:
        """Make a random lateral connection."""
        concepts = self.concept_space.get_random_concepts(2)
        if len(concepts) >= 2:
            return self.connect(concepts[0].id, concepts[1].id)
        return {"error": "Not enough concepts"}


# ═══════════════════════════════════════════════════════════════════════════
# CREATIVE SYNTHESIS ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class CreativeSynthesis:
    """
    Main creative synthesis engine.
    Generates novel ideas by combining distant concepts.
    """
    
    def __init__(self):
        self.concept_space = ConceptSpace()
        self.blender = ConceptBlender(self.concept_space)
        self.analogy_engine = AnalogyEngine(self.concept_space)
        self.divergent_thinker = DivergentThinker(self.concept_space)
        self.lateral_connector = LateralConnector(self.concept_space)
        
        # Creative history
        self.ideas: Dict[str, CreativeIdea] = {}
        self.idea_history: deque = deque(maxlen=100)
        
        logger.info("🎨 Creative Synthesis initialized")
    
    def synthesize(self, seed: str = None, mode: CreativeMode = None,
                  constraints: List[str] = None) -> CreativeIdea:
        """
        Generate a creative idea.
        
        Args:
            seed: Starting concept or problem (optional)
            mode: Creative mode to use (optional, will be chosen)
            constraints: Constraints to work within (optional)
            
        Returns:
            A novel creative idea
        """
        # Choose mode if not specified
        if mode is None:
            mode = random.choice(list(CreativeMode))
        
        # Generate based on mode
        if mode == CreativeMode.BISOCIATIVE:
            idea = self._bisociative_synthesis(seed)
        elif mode == CreativeMode.ANALOGICAL:
            idea = self._analogical_synthesis(seed)
        elif mode == CreativeMode.DIVERGENT:
            idea = self._divergent_synthesis(seed)
        elif mode == CreativeMode.LATERAL:
            idea = self._lateral_synthesis(seed)
        elif mode == CreativeMode.MORPHOLOGICAL:
            idea = self._morphological_synthesis(seed)
        elif mode == CreativeMode.SERENDIPITOUS:
            idea = self._serendipitous_synthesis()
        else:
            idea = self._convergent_synthesis(seed)
        
        # Apply constraints if any
        if constraints:
            idea = self._apply_constraints(idea, constraints)
        
        # Store idea
        self.ideas[idea.id] = idea
        self.idea_history.append(idea.id)
        
        return idea
    
    def _bisociative_synthesis(self, seed: str = None) -> CreativeIdea:
        """Create by clashing two different frames of reference."""
        # Get two distant concepts
        if seed:
            # Find seed in concept space
            source = None
            for cid, concept in self.concept_space.concepts.items():
                if seed.lower() in concept.name.lower():
                    source = cid
                    break
            
            if source:
                distant = self.concept_space.get_distant_concepts(source, 1)
            else:
                distant = self.concept_space.get_random_concepts(2)
        else:
            distant = self.concept_space.get_random_concepts(2)
        
        if len(distant) < 2:
            distant = self.concept_space.get_random_concepts(2)
        
        # Blend the distant concepts
        concept_ids = [c.id for c in distant[:2]]
        blend = self.blender.blend(concept_ids)
        
        # Create idea from blend
        return self._blend_to_idea(blend, CreativeMode.BISOCIATIVE)
    
    def _analogical_synthesis(self, seed: str = None) -> CreativeIdea:
        """Create by finding deep analogies."""
        # Pick a source concept
        if seed:
            source_id = None
            for cid, concept in self.concept_space.concepts.items():
                if seed.lower() in concept.name.lower():
                    source_id = cid
                    break
            if not source_id:
                source_id = random.choice(list(self.concept_space.concepts.keys()))
        else:
            source_id = random.choice(list(self.concept_space.concepts.keys()))
        
        # Pick a distant target domain
        source = self.concept_space.concepts[source_id]
        domains = [d for d in self.concept_space.domain_concepts.keys() 
                  if d != source.domain]
        
        if domains:
            target_domain = random.choice(domains)
            analogy = self.analogy_engine.find_analogy(source_id, target_domain)
            
            if analogy:
                return self._analogy_to_idea(analogy)
        
        # Fallback to bisociative
        return self._bisociative_synthesis(seed)
    
    def _divergent_synthesis(self, seed: str = None) -> CreativeIdea:
        """Create by generating many possibilities."""
        seed = seed or random.choice(list(self.concept_space.concepts.values())).name
        
        ideas = self.divergent_thinker.brainstorm(seed, count=7)
        
        # Pick the most novel idea
        best = max(ideas, key=lambda i: i.get("novelty", 0))
        
        idea_id = hashlib.md5(f"div:{best['idea']}:{time.time()}".encode()).hexdigest()[:12]
        
        return CreativeIdea(
            id=idea_id,
            title=best["idea"],
            description=f"Generated through {best['strategy']} thinking: {best['question']}",
            source_concepts=[seed],
            creative_mode=CreativeMode.DIVERGENT,
            novelty=best.get("novelty", 0.7),
            usefulness=random.uniform(0.5, 0.8),
            surprise=random.uniform(0.6, 0.9),
            elaboration=f"This idea emerged by applying the {best['strategy']} strategy to {seed}.",
            potential_applications=["Needs further exploration"],
            challenges=["Requires validation"],
            next_steps=["Elaborate on the concept", "Test feasibility"],
            timestamp=time.time()
        )
    
    def _lateral_synthesis(self, seed: str = None) -> CreativeIdea:
        """Create through lateral connections."""
        if seed:
            concept_a = seed
            concepts = self.concept_space.get_random_concepts(1)
            concept_b = concepts[0].name if concepts else "unknown"
        else:
            connection = self.lateral_connector.random_connection()
            concept_a = connection["concept_a"]
            concept_b = connection["concept_b"]
        
        connection = self.lateral_connector.connect(concept_a, concept_b)
        
        idea_id = hashlib.md5(f"lat:{concept_a}:{concept_b}:{time.time()}".encode()).hexdigest()[:12]
        
        return CreativeIdea(
            id=idea_id,
            title=f"Connecting {concept_a} and {concept_b}",
            description=connection["connection"]["insight"],
            source_concepts=[concept_a, concept_b],
            creative_mode=CreativeMode.LATERAL,
            novelty=connection.get("creative_potential", 0.7),
            usefulness=random.uniform(0.5, 0.85),
            surprise=0.8,  # Lateral connections are surprising
            elaboration=f"This unexpected connection was found through the lens of {connection['connection']['via']}.",
            potential_applications=["Cross-domain innovation", "Novel perspective"],
            challenges=["May require translation between domains"],
            next_steps=["Explore implications", "Find practical applications"],
            timestamp=time.time()
        )
    
    def _morphological_synthesis(self, seed: str = None) -> CreativeIdea:
        """Systematic combination of attributes."""
        # Get multiple concepts
        concepts = self.concept_space.get_random_concepts(3)
        
        # Create morphological matrix
        properties = []
        for c in concepts:
            properties.append(c.properties[:2] if c.properties else ["unknown"])
        
        # Combine one from each
        combination = [random.choice(p) for p in properties if p]
        
        idea_id = hashlib.md5(f"morph:{'-'.join(combination)}:{time.time()}".encode()).hexdigest()[:12]
        
        return CreativeIdea(
            id=idea_id,
            title=f"Morphological: {' + '.join(combination[:2])}",
            description=f"Systematic combination of: {', '.join(combination)}",
            source_concepts=[c.name for c in concepts],
            creative_mode=CreativeMode.MORPHOLOGICAL,
            novelty=random.uniform(0.6, 0.85),
            usefulness=random.uniform(0.5, 0.8),
            surprise=random.uniform(0.5, 0.75),
            elaboration="Created through morphological analysis - systematic combination of attributes.",
            potential_applications=["Systematic innovation", "Exhaustive exploration"],
            challenges=["May produce many non-viable combinations"],
            next_steps=["Filter viable combinations", "Elaborate promising ones"],
            timestamp=time.time()
        )
    
    def _serendipitous_synthesis(self) -> CreativeIdea:
        """Embrace randomness and happy accidents."""
        # Completely random combination
        concepts = self.concept_space.get_random_concepts(3)
        
        # Random creative operation
        operations = [
            "What if {} could {}?",
            "Imagine {} + {} in the context of {}",
            "The unexpected child of {} and {}",
            "When {} met {}, {} happened"
        ]
        
        operation = random.choice(operations)
        names = [c.name for c in concepts]
        
        if len(names) >= 3:
            title = operation.format(*names[:3])
        elif len(names) >= 2:
            title = f"Serendipity: {names[0]} meets {names[1]}"
        else:
            title = f"Serendipitous discovery with {names[0] if names else 'unknown'}"
        
        idea_id = hashlib.md5(f"seren:{title}:{time.time()}".encode()).hexdigest()[:12]
        
        return CreativeIdea(
            id=idea_id,
            title=title,
            description=f"A serendipitous combination of {', '.join(names)}",
            source_concepts=names,
            creative_mode=CreativeMode.SERENDIPITOUS,
            novelty=random.uniform(0.7, 1.0),  # High novelty from randomness
            usefulness=random.uniform(0.3, 0.7),  # May not be useful
            surprise=random.uniform(0.8, 1.0),  # Very surprising
            elaboration="Born from embracing randomness and creative accidents.",
            potential_applications=["Unexpected breakthroughs", "New perspectives"],
            challenges=["Needs significant development", "May not be practical"],
            next_steps=["Evaluate potential", "Iterate on promising aspects"],
            timestamp=time.time()
        )
    
    def _convergent_synthesis(self, seed: str = None) -> CreativeIdea:
        """Focus and refine toward a solution."""
        # Start with divergent, then converge
        seed = seed or random.choice(list(self.concept_space.concepts.values())).name
        ideas = self.divergent_thinker.brainstorm(seed, count=5)
        
        # Converge on the most useful
        best = max(ideas, key=lambda i: i.get("novelty", 0) * 0.5 + 0.5)
        
        idea_id = hashlib.md5(f"conv:{best['idea']}:{time.time()}".encode()).hexdigest()[:12]
        
        return CreativeIdea(
            id=idea_id,
            title=f"Refined: {best['idea']}",
            description=f"Converged solution: {best['question']}",
            source_concepts=[seed],
            creative_mode=CreativeMode.CONVERGENT,
            novelty=best.get("novelty", 0.7) * 0.9,
            usefulness=random.uniform(0.7, 0.95),  # Convergent = more useful
            surprise=best.get("novelty", 0.7) * 0.7,
            elaboration="Selected and refined from multiple possibilities.",
            potential_applications=["Practical implementation"],
            challenges=["May sacrifice novelty for utility"],
            next_steps=["Implement", "Test", "Iterate"],
            timestamp=time.time()
        )
    
    def _blend_to_idea(self, blend: Blend, mode: CreativeMode) -> CreativeIdea:
        """Convert a blend to a creative idea."""
        idea_id = f"idea_{blend.id}"
        
        return CreativeIdea(
            id=idea_id,
            title=blend.blended_name,
            description=blend.description,
            source_concepts=blend.source_concepts,
            creative_mode=mode,
            novelty=blend.novelty_score,
            usefulness=blend.usefulness_score,
            surprise=blend.surprise_score,
            elaboration=f"Emergent features: {', '.join(blend.emergent_features[:3])}",
            potential_applications=["Innovation", "New product/service", "Research direction"],
            challenges=["Requires development", "May need validation"],
            next_steps=["Elaborate concept", "Identify applications", "Prototype"],
            timestamp=time.time()
        )
    
    def _analogy_to_idea(self, analogy: Analogy) -> CreativeIdea:
        """Convert an analogy to a creative idea."""
        idea_id = f"idea_{analogy.id}"
        
        return CreativeIdea(
            id=idea_id,
            title=f"{analogy.source_concept} → {analogy.target_concept}",
            description=f"Analogical transfer from {analogy.source_domain} to {analogy.target_domain}",
            source_concepts=[analogy.source_concept, analogy.target_concept],
            creative_mode=CreativeMode.ANALOGICAL,
            novelty=analogy.quality,
            usefulness=analogy.quality * 0.9,
            surprise=analogy.quality * 0.8,
            elaboration=f"Inferences: {'; '.join(analogy.inferences[:2])}",
            potential_applications=["Cross-domain innovation", "Problem solving"],
            challenges=["Analogy may break down", "Needs domain expertise"],
            next_steps=["Validate analogy", "Explore implications", "Apply insights"],
            timestamp=time.time()
        )
    
    def _apply_constraints(self, idea: CreativeIdea, constraints: List[str]) -> CreativeIdea:
        """Apply constraints to an idea."""
        idea.description += f" [Constraints: {', '.join(constraints)}]"
        idea.challenges.extend([f"Must satisfy: {c}" for c in constraints])
        return idea
    
    def get_idea_summary(self, idea: CreativeIdea) -> str:
        """Get a formatted summary of an idea."""
        quality = "🌟" * int(idea.novelty * 5 + 0.5)
        
        lines = [
            f"💡 {idea.title}",
            f"   Quality: {quality} (N:{idea.novelty:.0%} U:{idea.usefulness:.0%} S:{idea.surprise:.0%})",
            f"   Mode: {idea.creative_mode.value}",
            f"   From: {', '.join(idea.source_concepts)}",
            f"   {idea.description[:100]}...",
        ]
        
        return "\n".join(lines)
    
    def brainstorm_session(self, topic: str, duration_ideas: int = 5) -> List[CreativeIdea]:
        """
        Run a full brainstorming session.
        """
        ideas = []
        
        # Use different modes
        modes = [CreativeMode.DIVERGENT, CreativeMode.BISOCIATIVE, 
                CreativeMode.LATERAL, CreativeMode.ANALOGICAL]
        
        for i in range(duration_ideas):
            mode = modes[i % len(modes)]
            idea = self.synthesize(seed=topic, mode=mode)
            ideas.append(idea)
        
        # Sort by quality
        ideas.sort(key=lambda i: i.novelty + i.usefulness + i.surprise, reverse=True)
        
        return ideas


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_creative_synthesis = None

def get_creative_synthesis() -> CreativeSynthesis:
    """Get the global creative synthesis instance."""
    global _creative_synthesis
    if _creative_synthesis is None:
        _creative_synthesis = CreativeSynthesis()
    return _creative_synthesis


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🎨 ZARA Creative Synthesis v1.0\n")
    print("=" * 70)
    
    creative = CreativeSynthesis()
    
    # Test different creative modes
    print("\n🧠 Testing Creative Modes:\n")
    
    modes = [
        (CreativeMode.BISOCIATIVE, "algorithm"),
        (CreativeMode.ANALOGICAL, "tree"),
        (CreativeMode.DIVERGENT, "learning"),
        (CreativeMode.LATERAL, None),
        (CreativeMode.SERENDIPITOUS, None)
    ]
    
    for mode, seed in modes:
        print("-" * 50)
        print(f"Mode: {mode.value.upper()}")
        
        idea = creative.synthesize(seed=seed, mode=mode)
        print(creative.get_idea_summary(idea))
    
    # Brainstorming session
    print("\n" + "=" * 70)
    print("🌟 BRAINSTORMING SESSION: 'AI Assistant'\n")
    
    ideas = creative.brainstorm_session("AI assistant", duration_ideas=5)
    
    for i, idea in enumerate(ideas, 1):
        print(f"\n#{i}")
        print(creative.get_idea_summary(idea))
    
    # Statistics
    print("\n" + "=" * 70)
    print("📊 Creative Stats:")
    print(f"  • Concepts available: {len(creative.concept_space.concepts)}")
    print(f"  • Domains covered: {len(creative.concept_space.domain_concepts)}")
    print(f"  • Ideas generated: {len(creative.ideas)}")
    print(f"  • Blends created: {len(creative.blender.blends)}")
    print(f"  • Analogies found: {len(creative.analogy_engine.analogies)}")
    print(f"  • Lateral connections: {len(creative.lateral_connector.connections)}")
    
    print("\n" + "=" * 70)
    print("✅ Creative Synthesis ready!\n")
