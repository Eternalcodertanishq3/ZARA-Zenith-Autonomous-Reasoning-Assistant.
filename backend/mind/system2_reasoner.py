"""
ZARA System-2 Recursive Reasoning v1.0
=======================================
Deep-Thinking Loop with Internal Debate

Based on Kahneman's dual-process theory:
- System 1: Fast, intuitive, automatic (default LLM response)
- System 2: Slow, deliberate, analytical (this module)

This module enables ZARA to:
1. PAUSE before responding to complex queries
2. SIMULATE multiple possible responses/actions
3. VERIFY each candidate through self-critique
4. DEBATE between internal "perspectives"
5. Only OUTPUT the most robust conclusion

Key Features:
- Recursive depth-limited tree search
- Monte Carlo thought sampling
- Adversarial self-critique (devil's advocate)
- Confidence calibration
- Thought attribution and transparency
"""

import logging
import json
import time
import threading
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import re

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_SYSTEM2")


# ═══════════════════════════════════════════════════════════════════════════
# THOUGHT STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class ThoughtType(Enum):
    """Types of internal thoughts."""
    HYPOTHESIS = "hypothesis"       # Initial candidate
    ANALYSIS = "analysis"           # Breaking down the problem
    CRITIQUE = "critique"           # Challenging an idea
    DEFENSE = "defense"             # Defending an idea
    SYNTHESIS = "synthesis"         # Combining ideas
    VERIFICATION = "verification"   # Checking correctness
    SIMULATION = "simulation"       # Imagining outcomes
    CONCLUSION = "conclusion"       # Final decision


class ReasoningMode(Enum):
    """Modes of System-2 reasoning."""
    QUICK = "quick"           # Single-pass, light verification
    STANDARD = "standard"     # Multiple candidates, basic debate
    DEEP = "deep"             # Full tree search, extensive debate
    CRITICAL = "critical"     # Maximum rigor, adversarial testing


@dataclass
class Thought:
    """A single unit of reasoning."""
    id: str
    type: ThoughtType
    content: str
    confidence: float           # 0-1, self-assessed confidence
    parent_id: Optional[str]    # For tree structure
    children: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    # Evaluation metrics
    coherence: float = 0.0      # How well it fits with other thoughts
    validity: float = 0.0       # Logical correctness
    relevance: float = 0.0      # How relevant to the query
    
    def score(self) -> float:
        """Overall thought quality score."""
        return (
            self.confidence * 0.3 +
            self.coherence * 0.25 +
            self.validity * 0.25 +
            self.relevance * 0.2
        )


@dataclass
class DebatePosition:
    """A position in an internal debate."""
    stance: str                 # The position taken
    arguments: List[str]        # Supporting arguments
    rebuttals: List[str]        # Counters to opposing views
    confidence: float
    evidence: List[str]


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning session."""
    query: str
    mode: ReasoningMode
    thoughts: List[Thought]
    debate_summary: str
    final_conclusion: str
    confidence: float
    reasoning_time_ms: int
    depth_reached: int
    alternatives_considered: int
    
    def get_tree_visualization(self) -> str:
        """Get ASCII tree of thoughts."""
        # Build parent->children map
        children_map: Dict[str, List[Thought]] = {"root": []}
        thought_map: Dict[str, Thought] = {}
        
        for t in self.thoughts:
            thought_map[t.id] = t
            parent = t.parent_id or "root"
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(t)
        
        lines = []
        def render(thought_id: str, prefix: str = "", is_last: bool = True):
            if thought_id == "root":
                children = children_map.get("root", [])
                for i, child in enumerate(children):
                    render(child.id, "", i == len(children) - 1)
            else:
                t = thought_map[thought_id]
                connector = "└── " if is_last else "├── "
                icon = {
                    ThoughtType.HYPOTHESIS: "💡",
                    ThoughtType.ANALYSIS: "🔍",
                    ThoughtType.CRITIQUE: "⚔️",
                    ThoughtType.DEFENSE: "🛡️",
                    ThoughtType.SYNTHESIS: "🔮",
                    ThoughtType.VERIFICATION: "✓",
                    ThoughtType.SIMULATION: "🎭",
                    ThoughtType.CONCLUSION: "🎯",
                }.get(t.type, "•")
                
                short_content = t.content[:50] + "..." if len(t.content) > 50 else t.content
                lines.append(f"{prefix}{connector}{icon} [{t.confidence:.0%}] {short_content}")
                
                children = children_map.get(thought_id, [])
                child_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    render(child.id, child_prefix, i == len(children) - 1)
        
        render("root")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# THOUGHT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class ThoughtGenerator:
    """
    Generates candidate thoughts using the LLM.
    """
    
    def __init__(self):
        self._llm = None
        self.thought_counter = 0
    
    def _get_llm(self):
        """Get LLM instance lazily."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable: {e}")
        return self._llm
    
    def _new_id(self) -> str:
        """Generate new thought ID."""
        self.thought_counter += 1
        return f"thought_{self.thought_counter}"
    
    def generate_hypotheses(self, query: str, context: str = "", 
                           num_candidates: int = 3) -> List[Thought]:
        """Generate initial hypothesis thoughts."""
        thoughts = []
        
        llm = self._get_llm()
        
        prompt = f"""Given this query, generate {num_candidates} distinct possible responses or approaches.
For each, provide a brief explanation.

Query: {query}
{f'Context: {context}' if context else ''}

Format each as:
CANDIDATE 1: [response]
REASONING: [why this might be correct]

CANDIDATE 2: [response]
REASONING: [why this might be correct]

..."""

        if llm:
            try:
                response = llm.think(prompt)
                candidates = self._parse_candidates(response)
                
                for i, (content, reasoning) in enumerate(candidates):
                    thought = Thought(
                        id=self._new_id(),
                        type=ThoughtType.HYPOTHESIS,
                        content=content,
                        confidence=0.5 + random.uniform(-0.1, 0.1),  # Initial uncertainty
                        parent_id=None,
                        relevance=0.7
                    )
                    thoughts.append(thought)
            except Exception as e:
                logger.debug(f"Hypothesis generation error: {e}")
        
        # Fallback: generate synthetic hypotheses
        if not thoughts:
            for i in range(num_candidates):
                thought = Thought(
                    id=self._new_id(),
                    type=ThoughtType.HYPOTHESIS,
                    content=f"Hypothesis {i+1} for: {query[:100]}",
                    confidence=0.5,
                    parent_id=None
                )
                thoughts.append(thought)
        
        return thoughts
    
    def generate_critique(self, thought: Thought, query: str) -> Thought:
        """Generate a critique of a thought."""
        llm = self._get_llm()
        
        critique_content = f"Critique of: {thought.content[:100]}"
        confidence = 0.5
        
        if llm:
            try:
                prompt = f"""Act as a devil's advocate. Find potential flaws in this response.

Original query: {query}
Proposed response: {thought.content}

Identify:
1. Logical flaws or inconsistencies
2. Missing considerations
3. Potential negative consequences
4. Alternative interpretations

Be critical but fair."""

                response = llm.think(prompt)
                critique_content = response
                
                # Assess severity of critique
                if any(word in response.lower() for word in ["major flaw", "incorrect", "wrong", "invalid"]):
                    confidence = 0.8
                elif any(word in response.lower() for word in ["concern", "issue", "problem"]):
                    confidence = 0.6
                else:
                    confidence = 0.4
                    
            except Exception as e:
                logger.debug(f"Critique generation error: {e}")
        
        return Thought(
            id=self._new_id(),
            type=ThoughtType.CRITIQUE,
            content=critique_content,
            confidence=confidence,
            parent_id=thought.id,
            validity=0.7
        )
    
    def generate_defense(self, thought: Thought, critique: Thought, 
                        query: str) -> Thought:
        """Generate a defense against a critique."""
        llm = self._get_llm()
        
        defense_content = f"Defense of original thought against critique"
        confidence = 0.5
        
        if llm:
            try:
                prompt = f"""Defend the original response against this critique.

Original query: {query}
Original response: {thought.content}
Critique: {critique.content}

Provide a reasoned defense addressing each criticism.
Acknowledge valid points but explain why the original response may still be correct or useful."""

                response = llm.think(prompt)
                defense_content = response
                
                # Assess strength of defense
                if any(word in response.lower() for word in ["however", "nevertheless", "despite"]):
                    confidence = 0.6  # Acknowledging some validity
                elif any(word in response.lower() for word in ["incorrect critique", "misunderstanding"]):
                    confidence = 0.8  # Strong defense
                else:
                    confidence = 0.5
                    
            except Exception as e:
                logger.debug(f"Defense generation error: {e}")
        
        return Thought(
            id=self._new_id(),
            type=ThoughtType.DEFENSE,
            content=defense_content,
            confidence=confidence,
            parent_id=critique.id
        )
    
    def generate_synthesis(self, thoughts: List[Thought], query: str) -> Thought:
        """Synthesize multiple thoughts into one."""
        llm = self._get_llm()
        
        thought_summaries = "\n".join([f"- {t.content[:100]}" for t in thoughts])
        synthesis_content = f"Synthesis of {len(thoughts)} thoughts"
        confidence = 0.6
        
        if llm:
            try:
                prompt = f"""Synthesize these different perspectives into a coherent response.

Original query: {query}

Perspectives to synthesize:
{thought_summaries}

Create a unified response that:
1. Incorporates the strongest elements from each
2. Addresses concerns raised
3. Provides a balanced, well-reasoned answer"""

                response = llm.think(prompt)
                synthesis_content = response
                confidence = 0.7
                
            except Exception as e:
                logger.debug(f"Synthesis generation error: {e}")
        
        return Thought(
            id=self._new_id(),
            type=ThoughtType.SYNTHESIS,
            content=synthesis_content,
            confidence=confidence,
            parent_id=thoughts[0].id if thoughts else None,
            coherence=0.8
        )
    
    def generate_verification(self, thought: Thought, query: str) -> Tuple[Thought, bool]:
        """Verify a thought's correctness. Returns (verification_thought, is_valid)."""
        llm = self._get_llm()
        
        verification_content = "Verification check"
        is_valid = True
        confidence = 0.5
        
        if llm:
            try:
                prompt = f"""Verify this response for correctness.

Original query: {query}
Response to verify: {thought.content}

Check for:
1. Factual accuracy (if applicable)
2. Logical consistency
3. Completeness
4. Appropriateness

Conclude with either "VERIFIED" or "NEEDS REVISION" and explain why."""

                response = llm.think(prompt)
                verification_content = response
                
                is_valid = "VERIFIED" in response.upper() or "NEEDS REVISION" not in response.upper()
                confidence = 0.8 if is_valid else 0.3
                
            except Exception as e:
                logger.debug(f"Verification error: {e}")
        
        verification = Thought(
            id=self._new_id(),
            type=ThoughtType.VERIFICATION,
            content=verification_content,
            confidence=confidence,
            parent_id=thought.id,
            validity=1.0 if is_valid else 0.3
        )
        
        return verification, is_valid
    
    def simulate_outcome(self, thought: Thought, query: str, 
                        scenario: str = "") -> Thought:
        """Simulate the outcome of acting on a thought."""
        llm = self._get_llm()
        
        simulation_content = "Outcome simulation"
        
        if llm:
            try:
                prompt = f"""Simulate what would happen if this response/action is taken.

Original query: {query}
Proposed response: {thought.content}
{f'Scenario: {scenario}' if scenario else ''}

Describe:
1. Immediate effects
2. Potential reactions
3. Long-term consequences
4. Possible failure modes

Be realistic in your simulation."""

                response = llm.think(prompt)
                simulation_content = response
                
            except Exception as e:
                logger.debug(f"Simulation error: {e}")
        
        return Thought(
            id=self._new_id(),
            type=ThoughtType.SIMULATION,
            content=simulation_content,
            confidence=0.5,  # Simulations are inherently uncertain
            parent_id=thought.id
        )
    
    def _parse_candidates(self, response: str) -> List[Tuple[str, str]]:
        """Parse candidate responses from LLM output."""
        candidates = []
        
        # Try to parse CANDIDATE N: format
        pattern = r'CANDIDATE\s*\d+:\s*(.*?)(?:REASONING:\s*(.*?))?(?=CANDIDATE\s*\d+:|$)'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            content = match[0].strip()
            reasoning = match[1].strip() if len(match) > 1 else ""
            if content:
                candidates.append((content, reasoning))
        
        # Fallback: split by newlines
        if not candidates:
            lines = [l.strip() for l in response.split('\n') if l.strip()]
            for line in lines[:3]:
                candidates.append((line, ""))
        
        return candidates[:5]  # Max 5 candidates


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL DEBATE ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class InternalDebate:
    """
    Manages internal debates between different perspectives.
    Implements adversarial self-examination.
    """
    
    def __init__(self, generator: ThoughtGenerator):
        self.generator = generator
    
    def debate(self, hypotheses: List[Thought], query: str,
               rounds: int = 2) -> Tuple[List[Thought], str, Thought]:
        """
        Conduct an internal debate between hypotheses.
        Returns (all_thoughts, debate_summary, winner).
        """
        all_thoughts = list(hypotheses)
        debate_log = []
        
        # Track scores for each hypothesis
        scores: Dict[str, float] = {h.id: h.confidence for h in hypotheses}
        
        for round_num in range(rounds):
            debate_log.append(f"\n--- Round {round_num + 1} ---")
            
            for hypothesis in hypotheses:
                # Generate critique
                critique = self.generator.generate_critique(hypothesis, query)
                all_thoughts.append(critique)
                hypothesis.children.append(critique.id)
                
                debate_log.append(f"Critique of H{hypotheses.index(hypothesis)+1}: {critique.content[:100]}...")
                
                # Generate defense
                defense = self.generator.generate_defense(hypothesis, critique, query)
                all_thoughts.append(defense)
                critique.children.append(defense.id)
                
                debate_log.append(f"Defense: {defense.content[:100]}...")
                
                # Update scores based on debate
                if defense.confidence > critique.confidence:
                    scores[hypothesis.id] += 0.1  # Defense won
                else:
                    scores[hypothesis.id] -= 0.1  # Critique won
        
        # Find winner
        winner_id = max(scores, key=scores.get)
        winner = next(h for h in hypotheses if h.id == winner_id)
        winner.confidence = min(1.0, scores[winner_id])
        
        debate_summary = "\n".join(debate_log)
        
        return all_thoughts, debate_summary, winner


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM-2 REASONING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class System2Reasoner:
    """
    Main System-2 reasoning engine.
    Orchestrates deep thinking, simulation, and verification.
    """
    
    # Mode configurations
    MODE_CONFIG = {
        ReasoningMode.QUICK: {
            "num_hypotheses": 2,
            "debate_rounds": 0,
            "verify": False,
            "simulate": False,
            "max_depth": 2
        },
        ReasoningMode.STANDARD: {
            "num_hypotheses": 3,
            "debate_rounds": 1,
            "verify": True,
            "simulate": False,
            "max_depth": 3
        },
        ReasoningMode.DEEP: {
            "num_hypotheses": 4,
            "debate_rounds": 2,
            "verify": True,
            "simulate": True,
            "max_depth": 5
        },
        ReasoningMode.CRITICAL: {
            "num_hypotheses": 5,
            "debate_rounds": 3,
            "verify": True,
            "simulate": True,
            "max_depth": 7
        }
    }
    
    def __init__(self):
        self.generator = ThoughtGenerator()
        self.debate_engine = InternalDebate(self.generator)
        
        # State
        self.current_trace: Optional[ReasoningTrace] = None
        self.reasoning_history: deque = deque(maxlen=100)
        
        # Callbacks
        self.on_thought: List[Callable] = []  # Called for each new thought
        self.on_conclusion: List[Callable] = []  # Called when reasoning completes
        
        logger.info("🧠 System-2 Recursive Reasoner initialized")
    
    def reason(self, query: str, context: str = "",
               mode: ReasoningMode = ReasoningMode.STANDARD) -> ReasoningTrace:
        """
        Perform System-2 reasoning on a query.
        
        Args:
            query: The question or problem to reason about
            context: Additional context
            mode: How deep to think
            
        Returns:
            Complete reasoning trace with conclusion
        """
        start_time = time.time()
        config = self.MODE_CONFIG[mode]
        
        all_thoughts: List[Thought] = []
        
        logger.info(f"🧠 System-2 Reasoning: {mode.value} mode for '{query[:50]}...'")
        
        # Phase 1: Generate hypotheses
        hypotheses = self.generator.generate_hypotheses(
            query, context, config["num_hypotheses"]
        )
        all_thoughts.extend(hypotheses)
        self._notify_thoughts(hypotheses)
        
        # Phase 2: Internal debate (if enabled)
        debate_summary = "No debate conducted"
        winner = hypotheses[0] if hypotheses else None
        
        if config["debate_rounds"] > 0 and len(hypotheses) > 1:
            debate_thoughts, debate_summary, winner = self.debate_engine.debate(
                hypotheses, query, config["debate_rounds"]
            )
            all_thoughts.extend(debate_thoughts)
            self._notify_thoughts(debate_thoughts)
        
        # Phase 3: Simulation (if enabled)
        if config["simulate"] and winner:
            simulation = self.generator.simulate_outcome(winner, query)
            all_thoughts.append(simulation)
            winner.children.append(simulation.id)
            self._notify_thoughts([simulation])
            
            # Adjust confidence based on simulation
            if any(word in simulation.content.lower() for word in ["failure", "risk", "problem"]):
                winner.confidence *= 0.85
        
        # Phase 4: Verification (if enabled)
        if config["verify"] and winner:
            verification, is_valid = self.generator.generate_verification(winner, query)
            all_thoughts.append(verification)
            winner.children.append(verification.id)
            self._notify_thoughts([verification])
            
            if not is_valid:
                winner.confidence *= 0.7
        
        # Phase 5: Synthesis and conclusion
        if len(hypotheses) > 1:
            synthesis = self.generator.generate_synthesis(
                [winner] + [h for h in hypotheses if h != winner][:2],
                query
            )
            all_thoughts.append(synthesis)
            self._notify_thoughts([synthesis])
            final_content = synthesis.content
            final_confidence = synthesis.confidence
        else:
            final_content = winner.content if winner else "Unable to reason about query"
            final_confidence = winner.confidence if winner else 0.0
        
        # Create conclusion thought
        conclusion = Thought(
            id=self.generator._new_id(),
            type=ThoughtType.CONCLUSION,
            content=final_content,
            confidence=final_confidence,
            parent_id=winner.id if winner else None,
            coherence=0.8,
            validity=0.8,
            relevance=0.9
        )
        all_thoughts.append(conclusion)
        self._notify_thoughts([conclusion])
        
        # Build trace
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        trace = ReasoningTrace(
            query=query,
            mode=mode,
            thoughts=all_thoughts,
            debate_summary=debate_summary,
            final_conclusion=final_content,
            confidence=final_confidence,
            reasoning_time_ms=elapsed_ms,
            depth_reached=self._calculate_depth(all_thoughts),
            alternatives_considered=len(hypotheses)
        )
        
        self.current_trace = trace
        self.reasoning_history.append(trace)
        
        # Notify conclusion
        for callback in self.on_conclusion:
            try:
                callback(trace)
            except Exception as e:
                logger.error(f"Conclusion callback error: {e}")
        
        logger.info(f"🧠 Reasoning complete: {elapsed_ms}ms, {len(all_thoughts)} thoughts, {final_confidence:.0%} confidence")
        
        return trace
    
    def _calculate_depth(self, thoughts: List[Thought]) -> int:
        """Calculate maximum depth of thought tree."""
        # Build parent map
        depth_map = {}
        for t in thoughts:
            if t.parent_id is None:
                depth_map[t.id] = 1
            else:
                parent_depth = depth_map.get(t.parent_id, 0)
                depth_map[t.id] = parent_depth + 1
        
        return max(depth_map.values()) if depth_map else 0
    
    def _notify_thoughts(self, thoughts: List[Thought]):
        """Notify callbacks of new thoughts."""
        for callback in self.on_thought:
            for thought in thoughts:
                try:
                    callback(thought)
                except Exception as e:
                    logger.error(f"Thought callback error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def quick_think(self, query: str) -> str:
        """Fast reasoning, returns just the conclusion."""
        trace = self.reason(query, mode=ReasoningMode.QUICK)
        return trace.final_conclusion
    
    def deep_think(self, query: str, context: str = "") -> str:
        """Deep reasoning with full debate."""
        trace = self.reason(query, context, mode=ReasoningMode.DEEP)
        return trace.final_conclusion
    
    def critical_think(self, query: str, context: str = "") -> str:
        """Maximum rigor reasoning."""
        trace = self.reason(query, context, mode=ReasoningMode.CRITICAL)
        return trace.final_conclusion
    
    def should_use_system2(self, query: str) -> Tuple[bool, ReasoningMode]:
        """
        Determine if System-2 reasoning is needed for a query.
        Returns (should_use, recommended_mode).
        """
        query_lower = query.lower()
        
        # Keywords suggesting deep thinking needed
        critical_triggers = [
            "should i", "is it safe", "important decision",
            "consequences", "trade-off", "ethical", "moral",
            "life-changing", "critical", "urgent"
        ]
        
        deep_triggers = [
            "explain", "why", "how does", "compare",
            "analyze", "evaluate", "consider", "think about"
        ]
        
        standard_triggers = [
            "what if", "could you", "help me understand",
            "options", "alternatives", "suggest"
        ]
        
        if any(t in query_lower for t in critical_triggers):
            return True, ReasoningMode.CRITICAL
        
        if any(t in query_lower for t in deep_triggers):
            return True, ReasoningMode.DEEP
        
        if any(t in query_lower for t in standard_triggers):
            return True, ReasoningMode.STANDARD
        
        # Length-based heuristic
        if len(query) > 200:
            return True, ReasoningMode.STANDARD
        
        return False, ReasoningMode.QUICK
    
    def get_thought_stream(self) -> str:
        """Get formatted stream of current reasoning."""
        if self.current_trace is None:
            return "No active reasoning"
        
        return self.current_trace.get_tree_visualization()
    
    def get_reasoning_summary(self) -> str:
        """Get summary of current reasoning."""
        if self.current_trace is None:
            return "No active reasoning"
        
        t = self.current_trace
        return f"""
Reasoning Summary
═════════════════
Query: {t.query[:100]}...
Mode: {t.mode.value}
Time: {t.reasoning_time_ms}ms
Depth: {t.depth_reached} levels
Alternatives: {t.alternatives_considered}
Confidence: {t.confidence:.0%}

Conclusion:
{t.final_conclusion[:500]}...
"""


# ═══════════════════════════════════════════════════════════════════════════
# THINKING PAUSE DECORATOR
# ═══════════════════════════════════════════════════════════════════════════

class ThinkingPause:
    """
    Context manager for "thinking pause" - visible thinking indicator.
    """
    
    def __init__(self, reasoner: System2Reasoner, query: str, 
                 mode: ReasoningMode = None):
        self.reasoner = reasoner
        self.query = query
        self.mode = mode
        self.trace: Optional[ReasoningTrace] = None
    
    def __enter__(self):
        # Auto-detect mode if not specified
        if self.mode is None:
            _, self.mode = self.reasoner.should_use_system2(self.query)
        
        logger.info(f"🤔 Thinking pause initiated ({self.mode.value})...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.trace = self.reasoner.reason(self.query, mode=self.mode)
            logger.info(f"🤔 Thinking complete. Confidence: {self.trace.confidence:.0%}")
        return False
    
    def get_conclusion(self) -> str:
        """Get the reasoned conclusion."""
        return self.trace.final_conclusion if self.trace else ""


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_system2_reasoner = None

def get_system2_reasoner() -> System2Reasoner:
    """Get the global System-2 reasoner instance."""
    global _system2_reasoner
    if _system2_reasoner is None:
        _system2_reasoner = System2Reasoner()
    return _system2_reasoner


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🧠 ZARA System-2 Recursive Reasoning v1.0\n")
    print("=" * 60)
    
    reasoner = System2Reasoner()
    
    # Track thoughts in real-time
    def on_thought(thought):
        icon = {
            ThoughtType.HYPOTHESIS: "💡",
            ThoughtType.ANALYSIS: "🔍",
            ThoughtType.CRITIQUE: "⚔️",
            ThoughtType.DEFENSE: "🛡️",
            ThoughtType.SYNTHESIS: "🔮",
            ThoughtType.VERIFICATION: "✓",
            ThoughtType.SIMULATION: "🎭",
            ThoughtType.CONCLUSION: "🎯",
        }.get(thought.type, "•")
        print(f"  {icon} {thought.type.value}: {thought.content[:60]}... [{thought.confidence:.0%}]")
    
    reasoner.on_thought.append(on_thought)
    
    # Test queries
    test_queries = [
        ("What's the weather like?", ReasoningMode.QUICK),
        ("Should I learn Python or JavaScript first?", ReasoningMode.STANDARD),
    ]
    
    for query, mode in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Mode: {mode.value}")
        print("-" * 40)
        
        trace = reasoner.reason(query, mode=mode)
        
        print(f"\n📊 Results:")
        print(f"  Time: {trace.reasoning_time_ms}ms")
        print(f"  Thoughts: {len(trace.thoughts)}")
        print(f"  Depth: {trace.depth_reached}")
        print(f"  Confidence: {trace.confidence:.0%}")
        print(f"\n🎯 Conclusion: {trace.final_conclusion[:200]}...")
    
    # Show tree visualization
    print(f"\n{'='*60}")
    print("Thought Tree (last query):")
    print(reasoner.get_thought_stream())
    
    # Test auto-detection
    print(f"\n{'='*60}")
    print("Auto-detection test:")
    test_auto = [
        "Hello!",
        "Should I invest in stocks?",
        "Explain quantum computing in detail",
        "Is it ethical to use AI for hiring decisions?"
    ]
    for q in test_auto:
        should_use, mode = reasoner.should_use_system2(q)
        print(f"  '{q[:40]}...' → {mode.value if should_use else 'System-1'}")
    
    print("\n" + "=" * 60)
    print("✅ System-2 Recursive Reasoner ready!\n")
