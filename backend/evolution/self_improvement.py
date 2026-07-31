"""
ZARA Self-Improvement System
Autonomous optimization of prompts, parameters, and behavior
based on interaction feedback and performance metrics.
"""
import logging
import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, Counter
from pathlib import Path
from enum import Enum
import statistics

logger = logging.getLogger("ZARA_IMPROVE")


class ImprovementArea(Enum):
    """Areas for self-improvement."""
    RESPONSE_QUALITY = "response_quality"
    EMOTIONAL_ACCURACY = "emotional_accuracy"
    PERSONALITY_FIT = "personality_fit"
    KNOWLEDGE_COVERAGE = "knowledge_coverage"
    HELPFULNESS = "helpfulness"
    ENGAGEMENT = "engagement"


class FeedbackType(Enum):
    """Types of feedback."""
    EXPLICIT_POSITIVE = "explicit_positive"
    EXPLICIT_NEGATIVE = "explicit_negative"
    IMPLICIT_POSITIVE = "implicit_positive"
    IMPLICIT_NEGATIVE = "implicit_negative"
    CORRECTION = "correction"
    ABANDONMENT = "abandonment"


@dataclass
class FeedbackSignal:
    """A feedback signal from interaction."""
    feedback_type: FeedbackType
    area: ImprovementArea
    context: str
    details: str
    timestamp: float
    strength: float = 0.5  # -1 to 1


@dataclass
class PromptOptimization:
    """A prompt optimization."""
    original: str
    optimized: str
    reason: str
    improvement_score: float
    timestamp: float


@dataclass
class PerformanceMetric:
    """A performance metric."""
    name: str
    value: float
    trend: str  # improving, declining, stable
    samples: int


class SelfImprovementSystem:
    """
    ZARA's autonomous self-improvement system.
    
    Capabilities:
    - Learns from explicit and implicit feedback
    - Optimizes system prompts based on performance
    - Adjusts personality parameters
    - Identifies knowledge gaps
    - Tracks improvement over time
    
    This allows ZARA to genuinely get better at her job.
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.improve_dir = EVOLUTION_DIR / "improvement"
        except ImportError:
            self.improve_dir = Path("evolution/improvement")
        
        self.improve_dir.mkdir(parents=True, exist_ok=True)
        
        # Feedback collection
        self.feedback_buffer: deque = deque(maxlen=500)
        self.daily_feedback: Dict[str, List[FeedbackSignal]] = {}
        
        # Performance tracking
        self.metrics: Dict[str, List[float]] = {
            area.value: [] for area in ImprovementArea
        }
        
        # Optimization history
        self.prompt_history: List[PromptOptimization] = []
        self.parameter_adjustments: List[Dict] = []
        
        # Current optimized state
        self.optimized_prompt_additions = []
        self.personality_adjustments = {}
        
        # Knowledge gaps identified
        self.knowledge_gaps: deque = deque(maxlen=50)
        
        # Interaction patterns
        self.response_patterns: Dict[str, float] = {}  # pattern -> success rate
        
        # Persistence
        self.state_file = self.improve_dir / "improvement_state.json"
        self.feedback_file = self.improve_dir / "feedback_history.json"
        self._load_state()
        
        self.lock = threading.Lock()
        
        logger.info("🔧 Self-Improvement System initialized")

    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.optimized_prompt_additions = data.get("prompt_additions", [])
                    self.personality_adjustments = data.get("personality_adj", {})
                    self.response_patterns = data.get("patterns", {})
            except:
                pass
        
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-200:]:  # Last 200
                        item['feedback_type'] = FeedbackType(item['feedback_type'])
                        item['area'] = ImprovementArea(item['area'])
                        self.feedback_buffer.append(FeedbackSignal(**item))
            except:
                pass

    def _save_state(self):
        """Save state."""
        # Save main state
        state = {
            "prompt_additions": self.optimized_prompt_additions[-10:],
            "personality_adj": self.personality_adjustments,
            "patterns": dict(list(self.response_patterns.items())[-50:])
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        # Save feedback
        feedback_data = [
            {
                "feedback_type": f.feedback_type.value,
                "area": f.area.value,
                "context": f.context[:100],
                "details": f.details[:100],
                "timestamp": f.timestamp,
                "strength": f.strength
            }
            for f in list(self.feedback_buffer)[-100:]
        ]
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════════
    # FEEDBACK COLLECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def record_feedback(self, feedback_type: FeedbackType,
                       area: ImprovementArea,
                       context: str,
                       details: str = "",
                       strength: float = 0.5):
        """Record a feedback signal."""
        signal = FeedbackSignal(
            feedback_type=feedback_type,
            area=area,
            context=context[:200],
            details=details[:200],
            timestamp=time.time(),
            strength=strength
        )
        
        with self.lock:
            self.feedback_buffer.append(signal)
            
            # Update metrics
            score = strength if feedback_type in [
                FeedbackType.EXPLICIT_POSITIVE, FeedbackType.IMPLICIT_POSITIVE
            ] else -strength
            
            self.metrics[area.value].append(score)
            
            # Keep last 100 samples per metric
            if len(self.metrics[area.value]) > 100:
                self.metrics[area.value] = self.metrics[area.value][-100:]
        
        logger.debug(f"Feedback recorded: {feedback_type.value} for {area.value}")

    def infer_feedback_from_interaction(self, user_input: str,
                                        zara_response: str,
                                        next_user_input: str = None,
                                        session_continued: bool = True):
        """Infer feedback from interaction patterns."""
        # Implicit positive: Session continues, user engages
        if session_continued and next_user_input:
            if len(next_user_input) > 20:  # Substantive follow-up
                self.record_feedback(
                    FeedbackType.IMPLICIT_POSITIVE,
                    ImprovementArea.ENGAGEMENT,
                    context=f"Response to: {user_input[:50]}",
                    strength=0.3
                )
        
        # Implicit negative: Very short follow-up
        if next_user_input and len(next_user_input) < 5:
            self.record_feedback(
                FeedbackType.IMPLICIT_NEGATIVE,
                ImprovementArea.ENGAGEMENT,
                context=f"Short reply after: {zara_response[:50]}",
                strength=0.2
            )
        
        # Abandonment
        if not session_continued:
            self.record_feedback(
                FeedbackType.ABANDONMENT,
                ImprovementArea.ENGAGEMENT,
                context=f"Session ended after: {zara_response[:50]}",
                strength=0.4
            )
        
        # Detect explicit feedback
        input_lower = user_input.lower()
        
        # Positive signals
        if any(w in input_lower for w in ["thanks", "thank you", "perfect", "great", "exactly"]):
            self.record_feedback(
                FeedbackType.EXPLICIT_POSITIVE,
                ImprovementArea.HELPFULNESS,
                context=user_input[:100],
                strength=0.6
            )
        
        # Negative signals
        if any(w in input_lower for w in ["no", "wrong", "not what", "that's not"]):
            self.record_feedback(
                FeedbackType.EXPLICIT_NEGATIVE,
                ImprovementArea.RESPONSE_QUALITY,
                context=user_input[:100],
                strength=0.5
            )
        
        # Correction signals
        if any(w in input_lower for w in ["i meant", "actually", "let me clarify"]):
            self.record_feedback(
                FeedbackType.CORRECTION,
                ImprovementArea.RESPONSE_QUALITY,
                context=user_input[:100],
                strength=0.4
            )

    def record_knowledge_gap(self, topic: str, context: str):
        """Record a knowledge gap."""
        with self.lock:
            self.knowledge_gaps.append({
                "topic": topic,
                "context": context[:100],
                "timestamp": time.time()
            })

    # ═══════════════════════════════════════════════════════════════════
    # SELF-OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════
    
    def analyze_and_optimize(self) -> Dict:
        """Analyze feedback and generate optimizations."""
        results = {
            "metrics": self.get_performance_metrics(),
            "prompt_suggestions": [],
            "personality_suggestions": {},
            "areas_needing_work": []
        }
        
        with self.lock:
            feedback = list(self.feedback_buffer)
        
        if len(feedback) < 10:
            return results
        
        # Analyze each area
        for area in ImprovementArea:
            area_feedback = [f for f in feedback if f.area == area]
            
            if not area_feedback:
                continue
            
            # Calculate success rate
            positive = sum(1 for f in area_feedback if f.strength > 0)
            total = len(area_feedback)
            success_rate = positive / total
            
            if success_rate < 0.6:
                results["areas_needing_work"].append({
                    "area": area.value,
                    "success_rate": success_rate,
                    "sample_size": total
                })
                
                # Generate suggestions based on area
                suggestions = self._generate_suggestions(area, area_feedback)
                results["prompt_suggestions"].extend(suggestions)
        
        # Personality adjustments based on engagement feedback
        engagement_feedback = [
            f for f in feedback 
            if f.area == ImprovementArea.ENGAGEMENT
        ]
        
        if engagement_feedback:
            results["personality_suggestions"] = self._suggest_personality_adjustments(
                engagement_feedback
            )
        
        return results

    def _generate_suggestions(self, area: ImprovementArea,
                             feedback: List[FeedbackSignal]) -> List[str]:
        """Generate improvement suggestions for an area."""
        suggestions = []
        
        # Analyze negative feedback contexts
        negative = [f for f in feedback if f.strength < 0]
        
        if area == ImprovementArea.RESPONSE_QUALITY:
            corrections = [f for f in negative if f.feedback_type == FeedbackType.CORRECTION]
            if len(corrections) > 3:
                suggestions.append(
                    "Consider asking for clarification before responding to ambiguous queries"
                )
            
            if len(negative) > 5:
                suggestions.append(
                    "Focus on understanding user intent before providing solutions"
                )
        
        elif area == ImprovementArea.EMOTIONAL_ACCURACY:
            if len(negative) > 3:
                suggestions.append(
                    "Pay more attention to emotional cues in user messages"
                )
        
        elif area == ImprovementArea.HELPFULNESS:
            if len(negative) > 3:
                suggestions.append(
                    "Provide more actionable and specific responses"
                )
        
        elif area == ImprovementArea.ENGAGEMENT:
            short_responses = [
                f for f in negative 
                if f.feedback_type == FeedbackType.ABANDONMENT
            ]
            if len(short_responses) > 3:
                suggestions.append(
                    "Consider being more engaging and personable"
                )
        
        return suggestions

    def _suggest_personality_adjustments(self,
                                        engagement_feedback: List[FeedbackSignal]) -> Dict:
        """Suggest personality parameter adjustments."""
        adjustments = {}
        
        positive = [f for f in engagement_feedback if f.strength > 0]
        negative = [f for f in engagement_feedback if f.strength < 0]
        
        positive_rate = len(positive) / max(1, len(engagement_feedback))
        
        if positive_rate < 0.5:
            # Low engagement - increase warmth/playfulness
            adjustments["warmth"] = 0.05
            adjustments["playfulness"] = 0.05
        elif positive_rate > 0.8:
            # High engagement - reinforce current settings
            adjustments["maintain"] = True
        
        return adjustments

    def get_optimized_prompt_additions(self) -> List[str]:
        """Get current prompt optimizations."""
        return self.optimized_prompt_additions.copy()

    def add_prompt_optimization(self, addition: str, reason: str):
        """Add a prompt optimization."""
        opt = PromptOptimization(
            original="",
            optimized=addition,
            reason=reason,
            improvement_score=0.0,
            timestamp=time.time()
        )
        self.prompt_history.append(opt)
        self.optimized_prompt_additions.append(addition)
        self._save_state()

    def apply_personality_adjustment(self, personality_system):
        """Apply learned adjustments to personality system."""
        if not self.personality_adjustments or not personality_system:
            return
        
        for trait, adjustment in self.personality_adjustments.items():
            if trait == "maintain":
                continue
            
            try:
                if hasattr(personality_system, 'adjust_trait'):
                    personality_system.adjust_trait(trait, adjustment)
            except:
                pass

    # ═══════════════════════════════════════════════════════════════════
    # PERFORMANCE METRICS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_performance_metrics(self) -> List[PerformanceMetric]:
        """Get current performance metrics."""
        metrics = []
        
        for area_name, scores in self.metrics.items():
            if not scores:
                continue
            
            current = statistics.mean(scores[-20:]) if len(scores) >= 20 else statistics.mean(scores)
            
            # Calculate trend
            trend = "stable"
            if len(scores) >= 10:
                early = statistics.mean(scores[:len(scores)//2])
                late = statistics.mean(scores[len(scores)//2:])
                
                if late > early * 1.1:
                    trend = "improving"
                elif late < early * 0.9:
                    trend = "declining"
            
            metrics.append(PerformanceMetric(
                name=area_name,
                value=current,
                trend=trend,
                samples=len(scores)
            ))
        
        return metrics

    def get_improvement_summary(self) -> str:
        """Get a summary of improvement status."""
        metrics = self.get_performance_metrics()
        
        if not metrics:
            return "Not enough data to analyze improvement."
        
        improving = [m for m in metrics if m.trend == "improving"]
        declining = [m for m in metrics if m.trend == "declining"]
        
        summary_parts = []
        
        if improving:
            summary_parts.append(
                f"Improving in: {', '.join(m.name for m in improving)}"
            )
        
        if declining:
            summary_parts.append(
                f"Needs work: {', '.join(m.name for m in declining)}"
            )
        
        avg_score = statistics.mean(m.value for m in metrics)
        summary_parts.append(f"Overall performance: {avg_score:.2f}")
        
        return ". ".join(summary_parts)

    def get_knowledge_gaps(self, limit: int = 10) -> List[Dict]:
        """Get identified knowledge gaps."""
        with self.lock:
            return list(self.knowledge_gaps)[-limit:]

    def get_status(self) -> Dict:
        """Get system status."""
        metrics = self.get_performance_metrics()
        
        return {
            "total_feedback": len(self.feedback_buffer),
            "knowledge_gaps": len(self.knowledge_gaps),
            "prompt_optimizations": len(self.optimized_prompt_additions),
            "metrics": [
                {"name": m.name, "value": m.value, "trend": m.trend}
                for m in metrics
            ],
            "summary": self.get_improvement_summary()
        }

    def periodic_save(self):
        """Periodic save of state."""
        self._save_state()


# Singleton
_improve_instance = None

def get_improvement() -> SelfImprovementSystem:
    """Get the global improvement system."""
    global _improve_instance
    if _improve_instance is None:
        _improve_instance = SelfImprovementSystem()
    return _improve_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    improve = SelfImprovementSystem()
    
    # Simulate feedback
    improve.record_feedback(
        FeedbackType.EXPLICIT_POSITIVE,
        ImprovementArea.HELPFULNESS,
        "Helped with Python code",
        strength=0.8
    )
    
    improve.infer_feedback_from_interaction(
        "How do I fix this bug?",
        "Try checking the variable types...",
        "Thanks, that helped!",
        session_continued=True
    )
    
    print(f"Status: {improve.get_status()}")
    
    # Analyze
    results = improve.analyze_and_optimize()
    print(f"Analysis: {results}")
