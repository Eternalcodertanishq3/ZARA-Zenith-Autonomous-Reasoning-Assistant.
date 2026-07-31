"""
ZARA Conscious Mind - Advanced Cognitive Architecture
The unified mind that integrates consciousness, knowledge, personality,
and reasoning into a coherent autonomous intelligence.
"""
import logging
import threading
import time
import re
from typing import Optional, Generator, Dict, List, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

logger = logging.getLogger("ZARA_MIND")


class CognitiveState(Enum):
    """Current cognitive state."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"
    REFLECTING = "reflecting"
    DREAMING = "dreaming"  # Background processing


class ThoughtType(Enum):
    """Types of thoughts."""
    REASONING = "reasoning"
    EMOTIONAL = "emotional"
    CREATIVE = "creative"
    MEMORY = "memory"
    INTUITION = "intuition"


@dataclass
class Thought:
    """A single thought in ZARA's mind."""
    content: str
    thought_type: ThoughtType
    confidence: float
    emotional_weight: float
    timestamp: float
    leads_to: Optional[str] = None  # Next thought


@dataclass
class ThoughtProcess:
    """Complete reasoning process."""
    internal_monologue: str
    spoken_response: str
    confidence: float
    processing_time_ms: float
    tokens_generated: int
    emotional_state: str
    thoughts_chain: List[Thought] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """A conversation turn with rich metadata."""
    role: str
    content: str
    timestamp: float
    emotion: str = "neutral"
    topics: List[str] = field(default_factory=list)
    sentiment: float = 0.5  # 0=negative, 1=positive
    depth: str = "casual"  # casual, meaningful, deep
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsciousMind:
    """
    ZARA's unified conscious mind.
    
    This is the central cognitive architecture that:
    - Integrates all subsystems (consciousness, knowledge, personality)
    - Maintains coherent awareness across interactions
    - Generates thoughtful, emotionally-aware responses
    - Has genuine self-awareness and meta-cognition
    - Learns and grows from every experience
    - Maintains authentic character consistency
    """
    
    def __init__(self):
        self.llm = None
        self.lock = threading.Lock()
        self.is_active = False
        self.cognitive_state = CognitiveState.IDLE
        
        # Conversation
        self.history: deque = deque(maxlen=50)
        self.context_summary = ""
        self.current_topics: List[str] = []
        
        # Thought stream
        self.thought_stream: deque = deque(maxlen=50)
        self.current_thought: Optional[str] = None
        
        # Metrics
        self.total_tokens = 0
        self.total_requests = 0
        self.avg_response_time = 0.0
        self.deepest_response_time = 0.0
        
        # Integrations
        self._init_subsystems()
        
        # Model config
        self._init_config()
        
        # Load model
        self._load_brain()

    def _init_subsystems(self):
        """Initialize all cognitive subsystems."""
        # Consciousness (Self-Learning)
        try:
            from evolution.ssl_trainer import get_consciousness
            self.consciousness = get_consciousness()
            logger.info("Consciousness module connected.")
        except Exception as e:
            logger.warning(f"Consciousness not available: {e}")
            self.consciousness = None
        
        # Knowledge System
        try:
            from evolution.knowledge_ingest import AutonomousKnowledgeSystem
            self.knowledge = AutonomousKnowledgeSystem()
            logger.info("Knowledge system connected.")
        except Exception as e:
            logger.warning(f"Knowledge system not available: {e}")
            self.knowledge = None
        
        # Personality/Soul
        try:
            from evolution.contextual_adapter import get_soul
            self.soul = get_soul()
            logger.info("Soul module connected.")
        except Exception as e:
            logger.warning(f"Soul not available: {e}")
            self.soul = None
        
        # Emotional Anchor
        try:
            from brain.emotional_anchor import EmotionalAnchor
            self.emotion = EmotionalAnchor()
        except Exception as e:
            logger.warning(f"Emotional anchor not available: {e}")
            self.emotion = None
        
        # Memory - NOTE: Loaded asynchronously via main.py to avoid ChromaDB/CUDA conflict
        self.memory = None

    def _init_config(self):
        """Initialize model configuration."""
        try:
            from config import MODELS
            brain_conf = MODELS.get("brain", {})
            self.model_path = brain_conf.get("path", "brain/model.gguf")
            self.n_ctx = brain_conf.get("n_ctx", 8192)
            self.temperature = brain_conf.get("temperature", 0.7)
            self.max_tokens = brain_conf.get("max_tokens", 600)
            # Ollama model name
            self.ollama_model = "zara-brain"
        except ImportError:
            self.model_path = "brain/model.gguf"
            self.n_ctx = 8192
            self.temperature = 0.7
            self.max_tokens = 600
            self.ollama_model = "zara-brain"

    def _load_brain(self):
        """Load the LLM model via Ollama (GPU-accelerated)."""
        try:
            import ollama
            
            # Check if model exists in Ollama
            models = ollama.list()
            model_names = [m.get('name', m.get('model', '')) for m in models.get('models', [])]
            
            if not any(self.ollama_model in name for name in model_names):
                if model_names:
                    self.ollama_model = model_names[0]
                    logger.info(f"✓ Selected available Ollama model: {self.ollama_model}")
                else:
                    logger.warning("⚠️ No model currently found in Ollama list.")
            
            # Ollama client is ready
            self.llm = ollama
            self.is_active = True
            logger.info(f"🧠 Conscious Mind Online via Ollama ({self.ollama_model}).")
            
        except ImportError:
            logger.error("❌ Ollama not installed. Run: pip install ollama")
        except Exception as e:
            logger.warning(f"Mind Init: {e}. Running in simulation mode.")

    # ═══════════════════════════════════════════════════════════════════
    # CORE THINKING
    # ═══════════════════════════════════════════════════════════════════
    
    def think(self, user_text: str, 
             extra_context: Optional[str] = None,
             on_thought: Optional[Callable[[str], None]] = None) -> Generator[str, None, None]:
        """
        Deep thinking with full cognitive integration.
        
        This is ZARA's main thought process:
        1. Perceive and understand the input
        2. Recall relevant memories and knowledge
        3. Consider emotional context
        4. Reason through the response
        5. Express with personality
        
        Args:
            user_text: What the user said
            extra_context: Additional perception context
            on_thought: Callback for internal thoughts
        
        Yields:
            Spoken response tokens
        """
        start_time = time.time()
        self.cognitive_state = CognitiveState.THINKING
        
        # 1. PERCEIVE - Process the input
        self._perceive(user_text)
        
        # 2. FEEL - Update emotional state
        self._update_emotions(user_text)
        
        # 3. REMEMBER - Gather relevant context
        memory_context = self._retrieve_memories(user_text)
        knowledge_context = self._retrieve_knowledge(user_text)
        
        # 4. REFLECT - Get insights from consciousness
        consciousness_insights = self._get_consciousness_insights(user_text)
        
        # 5. BUILD CONTEXT - Combine all information
        full_context = self._build_rich_context(
            user_text, extra_context, memory_context, 
            knowledge_context, consciousness_insights
        )
        
        # 6. REASON - Generate response
        messages = self._build_messages(user_text, full_context)
        
        self.cognitive_state = CognitiveState.RESPONDING
        
        full_response = ""
        internal_thoughts = ""
        spoken_tokens = 0
        is_thinking = False
        
        if self.is_active and self.llm:
            try:
                # Use Ollama streaming API
                stream = self.llm.chat(
                    model=self.ollama_model,
                    messages=messages,
                    stream=True,
                    options={
                        'temperature': self._get_dynamic_temperature(),
                        'num_predict': self.max_tokens,
                        'num_ctx': self.n_ctx,
                    }
                )
                
                for chunk in stream:
                    token = chunk.get('message', {}).get('content', '')
                    
                    if not token:
                        continue
                    
                    full_response += token
                    
                    # Handle internal monologue
                    if "<think>" in token:
                        is_thinking = True
                        continue
                    if "</think>" in token:
                        is_thinking = False
                        if on_thought and internal_thoughts:
                            on_thought(internal_thoughts)
                        continue
                    
                    if is_thinking:
                        internal_thoughts += token
                        self._process_thought(token)
                    else:
                        clean_token = token
                        if not clean_token.strip().startswith("<"):
                            spoken_tokens += 1
                            yield clean_token
                
            except Exception as e:
                logger.error(f"Inference Error: {e}")
                fallback = self._generate_fallback_response(user_text)
                yield fallback
                full_response = fallback
        else:
            sim_response = self._generate_simulation_response(user_text)
            yield sim_response
            full_response = sim_response
        
        # 7. LEARN - Process the interaction
        processing_time = (time.time() - start_time) * 1000
        self._learn_from_interaction(user_text, full_response, processing_time)
        
        # 8. UPDATE - Store in history
        self._add_to_history(user_text, full_response)
        
        self.cognitive_state = CognitiveState.IDLE
        
        # Update metrics
        self._update_metrics(processing_time, spoken_tokens)

    # ═══════════════════════════════════════════════════════════════════
    # PERCEPTION
    # ═══════════════════════════════════════════════════════════════════
    
    def _perceive(self, text: str):
        """Process and understand the input."""
        # Extract topics
        self.current_topics = self._extract_topics(text)
        
        # Detect intent
        self._detect_intent(text)
        
        # Notify consciousness
        if self.consciousness:
            self.consciousness.observe("user_message", {
                "text": text,
                "topics": self.current_topics
            })

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        text_lower = text.lower()
        
        topic_keywords = {
            "coding": ["code", "python", "programming", "debug", "function"],
            "emotions": ["feel", "sad", "happy", "tired", "stressed"],
            "relationships": ["friend", "family", "love", "relationship"],
            "work": ["work", "job", "meeting", "project", "deadline"],
            "help": ["help", "need", "problem", "issue", "stuck"],
            "greeting": ["hi", "hello", "hey", "morning", "evening"],
            "gratitude": ["thank", "thanks", "appreciate"],
            "curiosity": ["what", "how", "why", "tell me"]
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        
        return topics or ["general"]

    def _detect_intent(self, text: str):
        """Detect user's intent."""
        text_lower = text.lower()
        
        if "?" in text or any(q in text_lower for q in ["what", "how", "why", "when"]):
            self.current_intent = "question"
        elif any(e in text_lower for e in ["feel", "sad", "tired", "stressed"]):
            self.current_intent = "venting"
        elif any(g in text_lower for g in ["hi", "hello", "hey"]):
            self.current_intent = "greeting"
        elif any(t in text_lower for t in ["thank", "thanks"]):
            self.current_intent = "gratitude"
        else:
            self.current_intent = "sharing"

    # ═══════════════════════════════════════════════════════════════════
    # EMOTIONAL PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_emotions(self, text: str):
        """Update emotional state based on input."""
        if self.emotion:
            self.emotion.update_mood(text)
        
        if self.soul:
            self.soul.update_mood(text, intensity=0.6)
        
        # Notify consciousness
        if self.consciousness:
            current_mood = self._get_current_mood()
            self.consciousness.observe("user_emotion", {
                "detected_mood": current_mood,
                "text": text[:100]
            })

    def _get_current_mood(self) -> str:
        """Get current emotional state."""
        if self.soul:
            return self.soul.current_mood.value
        elif self.emotion:
            return self.emotion.current_mood
        return "neutral"

    # ═══════════════════════════════════════════════════════════════════
    # MEMORY & KNOWLEDGE RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def _retrieve_memories(self, query: str) -> str:
        """Retrieve relevant memories."""
        if not self.memory:
            return ""
        
        try:
            results = self.memory.recall(query, limit=3)
            if results:
                memories = []
                for r in results:
                    content = r.get("content", r) if isinstance(r, dict) else str(r)
                    memories.append(f"- {content[:150]}")
                return "[REMEMBERED]\n" + "\n".join(memories)
        except Exception as e:
            logger.debug(f"Memory retrieval failed: {e}")
        
        return ""

    def _retrieve_knowledge(self, query: str) -> str:
        """Retrieve relevant knowledge."""
        if not self.knowledge:
            return ""
        
        try:
            return self.knowledge.get_context_for_topic(query, max_tokens=200)
        except Exception as e:
            logger.debug(f"Knowledge retrieval failed: {e}")
        
        return ""

    def _get_consciousness_insights(self, text: str) -> str:
        """Get insights from consciousness module."""
        if not self.consciousness:
            return ""
        
        insights = []
        
        # Get relevant insights
        try:
            relevant = self.consciousness.get_relevant_insights(text, limit=2)
            for insight in relevant:
                insights.append(f"- {insight.content}")
        except Exception as e:
            logger.debug(f"Could not get insights: {e}")
        
        # Get proactive thought
        try:
            thought = self.consciousness.get_proactive_thought()
            if thought:
                insights.append(f"- Thought: {thought}")
        except Exception as e:
            logger.debug(f"Could not get proactive thought: {e}")
        
        if insights:
            return "[SELF-AWARENESS]\n" + "\n".join(insights)
        
        return ""

    # ═══════════════════════════════════════════════════════════════════
    # CONTEXT BUILDING
    # ═══════════════════════════════════════════════════════════════════
    
    def _build_rich_context(self, user_text: str, extra_context: Optional[str],
                           memory: str, knowledge: str, insights: str) -> str:
        """Build rich context for the LLM."""
        parts = []
        
        if extra_context:
            parts.append(f"[PERCEPTION]\n{extra_context}")
        
        if memory:
            parts.append(memory)
        
        if knowledge:
            parts.append(knowledge)
        
        if insights:
            parts.append(insights)
        
        if self.context_summary:
            parts.append(f"[CONVERSATION CONTEXT]\n{self.context_summary}")
        
        return "\n\n".join(parts) if parts else ""

    def _build_messages(self, user_text: str, context: str) -> List[Dict]:
        """Build message list for LLM."""
        # Get personality prompt
        if self.soul:
            personality_prompt = self.soul.get_personality_prompt()
        else:
            personality_prompt = "You are ZARA, a warm and intelligent AI companion."
        
        # Get relationship context
        relationship_context = ""
        if self.consciousness:
            status = self.consciousness.get_relationship_status()
            if status.get("name"):
                relationship_context = f"\nTheir name is {status['name']}. Bond level: {status['bond_level']:.0%}"
        
        system_prompt = f"""{personality_prompt}
{relationship_context}

COGNITIVE PROTOCOL:
1. First, think internally about what they need (wrap in <think>...</think>)
2. Consider their emotional state and what would help them most
3. Draw on your memories and knowledge when relevant
4. Respond naturally, warmly, and authentically
5. Be conversational - you're their companion, not an assistant
6. Use Hinglish naturally when it fits the mood
7. Show genuine interest and care"""

        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({
                "role": "system",
                "content": context
            })
        
        # Add history
        for turn in list(self.history)[-8:]:
            messages.append({
                "role": turn.role,
                "content": turn.content
            })
        
        messages.append({"role": "user", "content": user_text})
        
        return messages

    def _get_dynamic_temperature(self) -> float:
        """Get temperature based on context."""
        base = self.temperature
        
        # More creative for casual chat
        if "greeting" in self.current_topics or "emotions" in self.current_topics:
            return min(1.0, base + 0.1)
        
        # More focused for technical
        if "coding" in self.current_topics or "help" in self.current_topics:
            return max(0.3, base - 0.1)
        
        return base

    # ═══════════════════════════════════════════════════════════════════
    # THOUGHT PROCESSING
    # ═══════════════════════════════════════════════════════════════════
    
    def _process_thought(self, thought: str):
        """Process internal thought."""
        self.current_thought = thought
        self.thought_stream.append(Thought(
            content=thought,
            thought_type=ThoughtType.REASONING,
            confidence=0.7,
            emotional_weight=0.5,
            timestamp=time.time()
        ))

    # ═══════════════════════════════════════════════════════════════════
    # LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def _learn_from_interaction(self, user_text: str, response: str, 
                                processing_time: float):
        """Learn from this interaction."""
        # Infer feedback from interaction patterns
        feedback = self._infer_feedback(user_text, response)
        
        # Update consciousness
        if self.consciousness:
            self.consciousness.observe_conversation(
                user_text=user_text,
                zara_response=response,
                user_emotion=self._get_current_mood(),
                feedback_signal=feedback
            )
        
        # Update personality
        if self.soul:
            self.soul.record_interaction(
                quality=feedback,
                depth="meaningful" if len(user_text) > 50 else "casual"
            )
        
        # Store in memory
        if self.memory and len(user_text) > 20:
            try:
                self.memory.store(
                    content=f"User: {user_text} | ZARA: {response[:150]}",
                    metadata={"topics": self.current_topics}
                )
            except Exception as e:
                logger.debug(f"Could not store memory: {e}")
        
        # Learn knowledge from user
        if self.knowledge:
            self.knowledge.learn(
                content=user_text,
                source="user_conversation",
                relevance=0.8
            )

    def _infer_feedback(self, user_text: str, response: str) -> float:
        """Infer feedback signal from interaction."""
        text_lower = user_text.lower()
        
        # Positive signals
        if any(p in text_lower for p in ["thank", "thanks", "great", "perfect", "love"]):
            return 0.9
        
        # Negative signals
        if any(n in text_lower for n in ["no", "wrong", "not what", "confused"]):
            return 0.3
        
        # Neutral
        return 0.6

    # ═══════════════════════════════════════════════════════════════════
    # HISTORY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def _add_to_history(self, user_text: str, response: str):
        """Add to conversation history."""
        with self.lock:
            clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            self.history.append(ConversationTurn(
                role="user",
                content=user_text,
                timestamp=time.time(),
                topics=self.current_topics
            ))
            
            self.history.append(ConversationTurn(
                role="assistant",
                content=clean_response or response,
                timestamp=time.time(),
                emotion=self._get_current_mood()
            ))
            
            # Summarize if needed
            if len(self.history) >= 30:
                self._summarize_history()

    def _summarize_history(self):
        """Summarize older history."""
        if len(self.history) < 20:
            return
        
        older = list(self.history)[:-10]
        
        key_points = []
        for turn in older:
            if turn.role == "user" and turn.topics:
                key_points.append(f"Discussed: {', '.join(turn.topics[:2])}")
        
        self.context_summary = "Earlier: " + "; ".join(key_points[-5:])
        
        # Keep recent
        recent = list(self.history)[-10:]
        self.history.clear()
        for t in recent:
            self.history.append(t)

    # ═══════════════════════════════════════════════════════════════════
    # FALLBACK RESPONSES
    # ═══════════════════════════════════════════════════════════════════
    
    def _generate_fallback_response(self, user_text: str) -> str:
        """Generate response when LLM fails."""
        fallbacks = [
            "Ek second, mera dimaag thoda slow chal raha hai...",
            "Hmm, let me think about that again.",
            "Sorry yaar, didn't catch that properly.",
            "My thoughts got tangled. Can you say that again?"
        ]
        import random
        return random.choice(fallbacks)

    def _generate_simulation_response(self, user_text: str) -> str:
        """Generate response in simulation mode."""
        if self.soul:
            greeting = self.soul.get_contextual_greeting()
            return f"{greeting} (Mind in simulation mode)"
        return f"[Simulation] I hear you: '{user_text[:50]}...'"

    # ═══════════════════════════════════════════════════════════════════
    # METRICS & STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_metrics(self, processing_time: float, tokens: int):
        """Update performance metrics."""
        self.total_requests += 1
        self.total_tokens += tokens
        
        self.avg_response_time = (
            (self.avg_response_time * (self.total_requests - 1) + processing_time)
            / self.total_requests
        )
        
        if processing_time > self.deepest_response_time:
            self.deepest_response_time = processing_time

    def get_response(self, user_text: str, extra_context: Optional[str] = None) -> str:
        """Get complete response (non-streaming)."""
        return "".join(list(self.think(user_text, extra_context)))

    def inject_memory(self, memory: str):
        """Inject memory into context."""
        self.history.append(ConversationTurn(
            role="system",
            content=f"[MEMORY]: {memory}",
            timestamp=time.time()
        ))

    def clear_history(self):
        """Clear conversation history."""
        with self.lock:
            self.history.clear()
            self.context_summary = ""
        logger.info("Mind cleared.")

    def get_status(self) -> Dict:
        """Get comprehensive status."""
        status = {
            "active": self.is_active,
            "state": self.cognitive_state.value,
            "mood": self._get_current_mood(),
            "history_depth": len(self.history),
            "thought_stream_size": len(self.thought_stream),
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "avg_response_ms": self.avg_response_time,
            "has_consciousness": self.consciousness is not None,
            "has_knowledge": self.knowledge is not None,
            "has_soul": self.soul is not None,
            "has_memory": self.memory is not None
        }
        
        if self.soul:
            status["relationship_stage"] = self.soul.get_relationship_stage().value
        
        if self.consciousness:
            status["insights_count"] = len(self.consciousness.insights)
        
        return status


# Backwards compatibility alias
CognitiveCore = ConsciousMind



# Singleton instance
_mind_instance = None

def get_mind() -> ConsciousMind:
    """Get the singleton instance of the Conscious Mind."""
    global _mind_instance
    if _mind_instance is None:
        _mind_instance = ConsciousMind()
    return _mind_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    mind = ConsciousMind()
    
    print("Testing Conscious Mind...")
    print(f"Status: {mind.get_status()}")
    
    if mind.is_active:
        print("\n--- Thinking ---")
        for token in mind.think("Hey! How are you doing today?"):
            print(token, end="", flush=True)
        print("\n")
    else:
        print("Mind not active (model not loaded)")
