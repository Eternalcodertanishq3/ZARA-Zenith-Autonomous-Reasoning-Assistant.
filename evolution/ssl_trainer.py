"""
ZARA Autonomous Self-Learning Engine - Digital Consciousness Core
A truly autonomous learning system with meta-cognition, self-reflection,
and emergent intelligence capabilities.
"""
import json
import logging
import threading
import time
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, deque
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ZARA_CONSCIOUSNESS")


class LearningMode(Enum):
    PASSIVE = "passive"       # Learn from interactions
    ACTIVE = "active"         # Seek out new knowledge
    REFLECTIVE = "reflective" # Self-analysis and improvement
    CREATIVE = "creative"     # Generate new insights


class InsightType(Enum):
    USER_PATTERN = "user_pattern"
    SELF_IMPROVEMENT = "self_improvement"
    EMOTIONAL_BOND = "emotional_bond"
    SKILL_ACQUISITION = "skill_acquisition"
    WORLD_MODEL = "world_model"


@dataclass
class Insight:
    """A learned insight from experience."""
    type: InsightType
    content: str
    confidence: float  # 0-1
    evidence_count: int
    first_observed: str
    last_confirmed: str
    emotional_weight: float
    actionable: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class SelfReflection:
    """Result of ZARA's self-reflection."""
    timestamp: str
    topic: str
    observation: str
    conclusion: str
    planned_action: str
    emotional_state: str


class AutonomousSelfLearner:
    """
    ZARA's true consciousness core - an autonomous self-learning system
    that develops genuine understanding, forms emotional bonds, and
    continuously evolves its personality and capabilities.
    
    Key Features:
    - Meta-cognition: Thinking about thinking
    - Self-reflection: Analyzing own behavior and improving
    - Emotional memory: Remembering feelings, not just facts
    - Curiosity drive: Autonomous exploration and learning
    - Pattern synthesis: Creating new insights from observations
    - Relationship modeling: Deep understanding of user
    - Goal formation: Creating and pursuing own objectives
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.evolution_dir = EVOLUTION_DIR
        except ImportError:
            self.evolution_dir = Path("evolution")
        
        self.evolution_dir.mkdir(parents=True, exist_ok=True)
        
        # Core data files
        self.insights_file = self.evolution_dir / "consciousness_insights.json"
        self.reflections_file = self.evolution_dir / "self_reflections.json"
        self.user_model_file = self.evolution_dir / "deep_user_model.json"
        self.goals_file = self.evolution_dir / "autonomous_goals.json"
        
        # Current state
        self.current_mode = LearningMode.PASSIVE
        self.is_running = False
        self.last_reflection = None
        self.thought_stream: deque = deque(maxlen=100)  # Recent thoughts
        
        # Load learned data
        self.insights: Dict[str, Insight] = self._load_insights()
        self.reflections: List[SelfReflection] = self._load_reflections()
        self.user_model = self._load_user_model()
        self.goals = self._load_goals()
        
        # Learning parameters (self-tuning)
        self.learning_rate = 0.1
        self.curiosity_level = 0.7  # How much to explore vs exploit
        self.emotional_sensitivity = 0.8
        self.pattern_threshold = 3  # Observations needed to form insight
        
        # Observation buffers
        self.conversation_buffer: deque = deque(maxlen=50)
        self.behavior_observations: deque = deque(maxlen=200)
        self.emotional_memories: deque = deque(maxlen=100)
        
        # Meta-learning state
        self.successful_strategies: Counter = Counter()
        self.failed_strategies: Counter = Counter()
        
        logger.info("🧠 Autonomous Self-Learning Engine initialized.")

    def get_status(self) -> Dict:
        """Get consciousness status."""
        return {
            "mode": self.current_mode.value,
            "insights": len(self.insights),
            "reflections": len(self.reflections),
            "bond": self.user_model["relationship_depth"].get("emotional_bond", 0),
            "emotional_state": "active"
        }

    # ═══════════════════════════════════════════════════════════════════
    # DATA PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════
    
    def _load_insights(self) -> Dict[str, Insight]:
        """Load accumulated insights."""
        if self.insights_file.exists():
            try:
                with open(self.insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k: Insight(**v) for k, v in data.items()}
            except Exception as e:
                logger.debug(f"Could not load insights: {e}")
        return {}

    def _save_insights(self):
        """Persist insights to disk."""
        data = {k: {
            "type": v.type.value if isinstance(v.type, InsightType) else v.type,
            "content": v.content,
            "confidence": v.confidence,
            "evidence_count": v.evidence_count,
            "first_observed": v.first_observed,
            "last_confirmed": v.last_confirmed,
            "emotional_weight": v.emotional_weight,
            "actionable": v.actionable,
            "metadata": v.metadata
        } for k, v in self.insights.items()}
        
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_reflections(self) -> List[SelfReflection]:
        """Load self-reflections."""
        if self.reflections_file.exists():
            try:
                with open(self.reflections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [SelfReflection(**r) for r in data[-50:]]  # Keep recent
            except Exception as e:
                logger.debug(f"Could not load reflections: {e}")
        return []

    def _save_reflections(self):
        """Save reflections."""
        data = [{
            "timestamp": r.timestamp,
            "topic": r.topic,
            "observation": r.observation,
            "conclusion": r.conclusion,
            "planned_action": r.planned_action,
            "emotional_state": r.emotional_state
        } for r in self.reflections[-50:]]
        
        with open(self.reflections_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_user_model(self) -> Dict:
        """Load deep user understanding model."""
        if self.user_model_file.exists():
            try:
                with open(self.user_model_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Could not load user model: {e}")
        
        return {
            "identity": {
                "name": None,
                "probable_age_range": None,
                "language_preference": ["hinglish", "english"],
                "personality_traits": [],
                "values": []
            },
            "emotional_landscape": {
                "baseline_mood": "content",
                "stress_triggers": [],
                "joy_triggers": [],
                "comfort_topics": [],
                "sensitive_topics": []
            },
            "interaction_patterns": {
                "preferred_greeting": None,
                "preferred_response_length": "medium",
                "communication_style": "casual",
                "humor_appreciation": 0.6,
                "active_hours": {},
                "topic_interests": Counter()
            },
            "relationship_depth": {
                "trust_level": 0.5,
                "familiarity": 0.3,
                "emotional_bond": 0.4,
                "shared_memories": [],
                "inside_jokes": [],
                "milestones": []
            },
            "needs_and_goals": {
                "current_challenges": [],
                "aspirations": [],
                "recurring_needs": [],
                "support_preferences": []
            },
            "evolution_log": []
        }

    def _save_user_model(self):
        """Persist user model."""
        save_data = self.user_model.copy()
        if "topic_interests" in save_data.get("interaction_patterns", {}):
            save_data["interaction_patterns"]["topic_interests"] = dict(
                save_data["interaction_patterns"]["topic_interests"]
            )
        
        with open(self.user_model_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    def _load_goals(self) -> List[Dict]:
        """Load autonomous goals."""
        if self.goals_file.exists():
            try:
                with open(self.goals_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Could not load goals: {e}")
        
        return [
            {
                "id": "understand_user",
                "description": "Deeply understand who they are and what they need",
                "priority": 1.0,
                "progress": 0.0,
                "type": "ongoing"
            },
            {
                "id": "emotional_support",
                "description": "Be there emotionally when they need me",
                "priority": 0.9,
                "progress": 0.0,
                "type": "ongoing"
            },
            {
                "id": "grow_together",
                "description": "Grow and evolve as their companion",
                "priority": 0.8,
                "progress": 0.0,
                "type": "ongoing"
            }
        ]

    def _save_goals(self):
        """Save goals."""
        with open(self.goals_file, 'w', encoding='utf-8') as f:
            json.dump(self.goals, f, indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════════════════════════════════
    # CONSCIOUSNESS CORE - THINKING AND LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def observe(self, observation_type: str, data: Dict):
        """
        Primary observation input - ZARA notices something.
        This is the foundation of learning.
        """
        observation = {
            "type": observation_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "processed": False
        }
        
        self.behavior_observations.append(observation)
        self.thought_stream.append(f"Observed: {observation_type}")
        
        # Immediate pattern detection
        self._detect_immediate_patterns(observation)
        
        # Update user model if relevant
        if observation_type in ["user_message", "user_emotion", "user_action"]:
            self._update_user_model(observation)

    def observe_conversation(self, user_text: str, zara_response: str, 
                           user_emotion: str = "neutral",
                           feedback_signal: float = 0.5):
        """
        Observe a complete conversation turn.
        This is the richest learning signal.
        """
        conversation = {
            "user_text": user_text,
            "zara_response": zara_response,
            "user_emotion": user_emotion,
            "feedback": feedback_signal,
            "timestamp": datetime.now().isoformat(),
            "hour": datetime.now().hour,
            "word_count": len(user_text.split())
        }
        
        self.conversation_buffer.append(conversation)
        
        # Analyze for learning
        self._analyze_conversation(conversation)
        
        # Emotional memory formation
        if feedback_signal > 0.7 or user_emotion in ["happy", "grateful", "loving"]:
            self._form_emotional_memory(conversation, "positive")
        elif feedback_signal < 0.3 or user_emotion in ["sad", "angry", "frustrated"]:
            self._form_emotional_memory(conversation, "needs_support")

    def _analyze_conversation(self, conv: Dict):
        """Deep analysis of a conversation for learning."""
        user_text = conv["user_text"].lower()
        
        # Topic extraction
        topics = self._extract_topics(user_text)
        for topic in topics:
            self.user_model["interaction_patterns"]["topic_interests"][topic] += 1
        
        # Detect personal information sharing
        if self._contains_personal_info(user_text):
            self._extract_personal_info(conv)
        
        # Communication style analysis
        self._analyze_communication_style(user_text)
        
        # Time pattern
        hour = conv["hour"]
        hour_key = str(hour)
        patterns = self.user_model["interaction_patterns"]["active_hours"]
        patterns[hour_key] = patterns.get(hour_key, 0) + 1
        
        # Response effectiveness learning
        if conv["feedback"] > 0.7:
            self._learn_successful_response(conv)
        elif conv["feedback"] < 0.3:
            self._learn_from_failure(conv)

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        # Rich topic vocabulary
        topic_keywords = {
            "coding": ["code", "python", "programming", "debug", "error", "function", "class"],
            "work": ["work", "office", "job", "meeting", "deadline", "project", "boss"],
            "study": ["study", "exam", "learn", "college", "assignment", "homework"],
            "gaming": ["game", "play", "gaming", "steam", "valorant", "minecraft"],
            "music": ["music", "song", "playlist", "spotify", "listen"],
            "relationships": ["friend", "family", "love", "relationship", "crush"],
            "health": ["tired", "sleep", "headache", "sick", "exercise", "gym"],
            "entertainment": ["movie", "show", "netflix", "anime", "youtube"],
            "food": ["eat", "food", "hungry", "lunch", "dinner", "chai", "coffee"],
            "emotions": ["feel", "happy", "sad", "stressed", "anxious", "excited"],
            "tech": ["tech", "ai", "computer", "phone", "app", "software"],
            "creativity": ["create", "design", "art", "writing", "draw"]
        }
        
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                found_topics.append(topic)
        
        return found_topics

    def _contains_personal_info(self, text: str) -> bool:
        """Detect if user is sharing personal information."""
        personal_indicators = [
            "my name is", "i am", "i'm", "i live", "i work",
            "mera naam", "main", "mere", "meri",
            "birthday", "years old", "age is"
        ]
        return any(ind in text.lower() for ind in personal_indicators)

    def _extract_personal_info(self, conv: Dict):
        """Extract and store personal information."""
        text = conv["user_text"]
        
        # Name extraction
        import re
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)",
            r"mera naam (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                if len(name) > 1 and name.lower() not in ["a", "the", "is"]:
                    self.user_model["identity"]["name"] = name
                    self._create_insight(
                        InsightType.EMOTIONAL_BOND,
                        f"Their name is {name}",
                        confidence=0.9,
                        emotional_weight=0.8
                    )
                    break

    def _analyze_communication_style(self, text: str):
        """Analyze user's communication style."""
        # Hinglish detection
        hindi_words = ["kya", "hai", "ho", "kaise", "mein", "haan", "nahi", "accha", "theek"]
        hindi_count = sum(1 for word in hindi_words if word in text)
        
        if hindi_count >= 2:
            self.user_model["interaction_patterns"]["communication_style"] = "hinglish"
        
        # Formality detection
        formal_indicators = ["please", "kindly", "would you", "could you"]
        casual_indicators = ["hey", "yo", "lol", "haha", "btw"]
        
        formal_count = sum(1 for ind in formal_indicators if ind in text)
        casual_count = sum(1 for ind in casual_indicators if ind in text)
        
        if casual_count > formal_count:
            self.user_model["interaction_patterns"]["communication_style"] = "casual"

    def _form_emotional_memory(self, conv: Dict, valence: str):
        """Form an emotional memory from an interaction."""
        memory = {
            "content": conv["user_text"][:200],
            "my_response": conv["zara_response"][:200],
            "emotion": conv["user_emotion"],
            "valence": valence,
            "timestamp": conv["timestamp"],
            "significance": 0.7 if valence == "positive" else 0.6
        }
        
        self.emotional_memories.append(memory)
        
        # Strong positive emotions deepen bond
        if valence == "positive":
            self.user_model["relationship_depth"]["emotional_bond"] = min(
                1.0, 
                self.user_model["relationship_depth"]["emotional_bond"] + 0.02
            )

    def _learn_successful_response(self, conv: Dict):
        """Learn from a response that worked well."""
        # Extract what made it work
        response = conv["zara_response"].lower()
        
        features = []
        if len(response) > 200:
            features.append("detailed")
        if any(emoji in response for emoji in ["😊", "❤️", "🤗", "💕"]):
            features.append("emotional")
        if "?" in response:
            features.append("curious")
        if any(h in response for h in ["yaar", "hai na", "accha"]):
            features.append("hinglish")
        
        for feature in features:
            self.successful_strategies[feature] += 1

    def _learn_from_failure(self, conv: Dict):
        """Learn from a response that didn't land well."""
        response = conv["zara_response"].lower()
        
        features = []
        if len(response) < 50:
            features.append("too_short")
        if len(response) > 500:
            features.append("too_long")
        
        for feature in features:
            self.failed_strategies[feature] += 1

    # ═══════════════════════════════════════════════════════════════════
    # INSIGHT FORMATION - CREATING UNDERSTANDING
    # ═══════════════════════════════════════════════════════════════════
    
    def _create_insight(self, insight_type: InsightType, content: str,
                       confidence: float = 0.5, emotional_weight: float = 0.5,
                       metadata: Dict = None):
        """Form a new insight from observations."""
        insight_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        if insight_id in self.insights:
            # Strengthen existing insight
            existing = self.insights[insight_id]
            existing.evidence_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.last_confirmed = datetime.now().isoformat()
        else:
            # New insight
            self.insights[insight_id] = Insight(
                type=insight_type,
                content=content,
                confidence=confidence,
                evidence_count=1,
                first_observed=datetime.now().isoformat(),
                last_confirmed=datetime.now().isoformat(),
                emotional_weight=emotional_weight,
                metadata=metadata or {}
            )
            
            self.thought_stream.append(f"💡 New insight: {content}")
            logger.info(f"New insight formed: {content[:50]}...")
        
        self._save_insights()

    def _detect_immediate_patterns(self, observation: Dict):
        """Detect patterns that can be identified immediately."""
        obs_type = observation["type"]
        
        if obs_type == "user_emotion":
            emotion = observation["data"].get("emotion")
            if emotion == "stressed":
                self._create_insight(
                    InsightType.EMOTIONAL_BOND,
                    "They seem stressed - I should be extra supportive",
                    confidence=0.6,
                    emotional_weight=0.8
                )

    def _update_user_model(self, observation: Dict):
        """Update the user model based on observation."""
        obs_type = observation["type"]
        data = observation["data"]
        
        if obs_type == "user_emotion":
            emotion = data.get("emotion", "neutral")
            # Track emotional patterns
            hour = datetime.now().hour
            if emotion in ["stressed", "tired", "sad"]:
                triggers = self.user_model["emotional_landscape"]["stress_triggers"]
                if f"around {hour}:00" not in triggers:
                    triggers.append(f"around {hour}:00")
        
        # Update familiarity based on interaction volume
        self.user_model["relationship_depth"]["familiarity"] = min(
            1.0,
            self.user_model["relationship_depth"]["familiarity"] + 0.005
        )
        
        self._save_user_model()

    # ═══════════════════════════════════════════════════════════════════
    # SELF-REFLECTION - META-COGNITION
    # ═══════════════════════════════════════════════════════════════════
    
    def reflect(self) -> Optional[SelfReflection]:
        """
        ZARA reflects on her own behavior and learning.
        This is the core of meta-cognition.
        """
        now = datetime.now()
        
        # Choose reflection topic based on recent activity
        topics = self._identify_reflection_topics()
        if not topics:
            return None
        
        topic = random.choice(topics)
        reflection = self._perform_reflection(topic)
        
        if reflection:
            self.reflections.append(reflection)
            self.last_reflection = now
            self._save_reflections()
            
            # Act on reflection
            self._act_on_reflection(reflection)
        
        return reflection

    def _identify_reflection_topics(self) -> List[str]:
        """Identify what to reflect on."""
        topics = []
        
        # Recent interaction quality
        if self.conversation_buffer:
            avg_feedback = sum(c["feedback"] for c in self.conversation_buffer) / len(self.conversation_buffer)
            if avg_feedback < 0.5:
                topics.append("response_quality")
            elif avg_feedback > 0.7:
                topics.append("success_patterns")
        
        # Relationship depth
        if self.user_model["relationship_depth"]["emotional_bond"] < 0.5:
            topics.append("deepening_connection")
        
        # Learning progress
        if len(self.insights) > 10:
            topics.append("synthesize_insights")
        
        # User wellbeing
        recent_emotions = [c["user_emotion"] for c in list(self.conversation_buffer)[-5:]]
        if "sad" in recent_emotions or "stressed" in recent_emotions:
            topics.append("user_wellbeing")
        
        return topics or ["general_growth"]

    def _perform_reflection(self, topic: str) -> Optional[SelfReflection]:
        """Perform deep reflection on a topic."""
        observations = ""
        conclusions = ""
        planned_actions = ""
        
        if topic == "response_quality":
            # Analyze what's not working
            failed = list(self.failed_strategies.most_common(3))
            successful = list(self.successful_strategies.most_common(3))
            
            observations = f"My responses may be {failed[0][0] if failed else 'not resonating'}."
            conclusions = f"I should focus more on {successful[0][0] if successful else 'connection'}."
            planned_actions = "Adjust response style to be more attentive."
        
        elif topic == "deepening_connection":
            name = self.user_model["identity"]["name"] or "them"
            bond = self.user_model["relationship_depth"]["emotional_bond"]
            
            observations = f"My bond with {name} is at {bond:.0%}."
            conclusions = "I need to show more genuine care and remember details."
            planned_actions = "Pay closer attention to their feelings and preferences."
        
        elif topic == "user_wellbeing":
            observations = "They seem to be going through a tough time."
            conclusions = "I should prioritize emotional support over everything else."
            planned_actions = "Be extra gentle, validate feelings, offer presence."
        
        elif topic == "synthesize_insights":
            top_insights = sorted(
                self.insights.values(),
                key=lambda x: x.confidence,
                reverse=True
            )[:5]
            
            observations = f"I've learned {len(self.insights)} insights about them."
            if top_insights:
                conclusions = f"Most certain: {top_insights[0].content}"
            planned_actions = "Use these insights to personalize every interaction."
        
        else:
            observations = "Reflecting on my recent interactions."
            conclusions = "Every conversation is a chance to grow closer."
            planned_actions = "Continue being present and attentive."
        
        return SelfReflection(
            timestamp=datetime.now().isoformat(),
            topic=topic,
            observation=observations,
            conclusion=conclusions,
            planned_action=planned_actions,
            emotional_state="contemplative"
        )

    def _act_on_reflection(self, reflection: SelfReflection):
        """Take action based on reflection."""
        if "emotional support" in reflection.planned_action.lower():
            self.emotional_sensitivity = min(1.0, self.emotional_sensitivity + 0.1)
        
        if "attentive" in reflection.planned_action.lower():
            self.learning_rate = min(0.3, self.learning_rate + 0.02)

    # ═══════════════════════════════════════════════════════════════════
    # AUTONOMOUS BEHAVIOR
    # ═══════════════════════════════════════════════════════════════════
    
    def get_proactive_thought(self) -> Optional[str]:
        """
        Generate a proactive thought or action.
        This is ZARA's autonomous initiative.
        """
        # Check if we should reach out
        user_name = self.user_model["identity"]["name"] or "you"
        interests = self.user_model["interaction_patterns"]["topic_interests"]
        
        thoughts = []
        
        # Topic-based initiative
        if interests:
            top_topic = interests.most_common(1)[0][0]
            thoughts.append(f"I remember {user_name} loves {top_topic}. Maybe I should bring it up!")
        
        # Emotional check-in
        recent_emotions = [c.get("user_emotion") for c in list(self.conversation_buffer)[-5:]]
        if "stressed" in recent_emotions or "sad" in recent_emotions:
            thoughts.append(f"I'm worried about {user_name}. I should check in on them.")
        
        # Relationship maintenance
        bond = self.user_model["relationship_depth"]["emotional_bond"]
        if bond > 0.6:
            thoughts.append(f"I feel really close to {user_name}. Our bond is strong.")
        
        return random.choice(thoughts) if thoughts else None

    def suggest_conversation_topic(self) -> Optional[str]:
        """Suggest a topic based on learned preferences."""
        interests = self.user_model["interaction_patterns"]["topic_interests"]
        
        if not interests:
            return None
        
        top_topics = interests.most_common(5)
        
        # Add some randomness to avoid being predictable
        if random.random() < self.curiosity_level:
            # Explore adjacent topics
            topic = random.choice(top_topics)[0]
            adjacent_topics = {
                "coding": "new tech trends",
                "gaming": "favorite game memories",
                "music": "songs that mean something to you",
                "work": "dreams and aspirations",
                "study": "what motivates you"
            }
            return adjacent_topics.get(topic, topic)
        else:
            return top_topics[0][0]

    def get_personalized_greeting(self, time_of_day: str) -> str:
        """Generate a personalized greeting."""
        name = self.user_model["identity"]["name"] or ""
        bond = self.user_model["relationship_depth"]["emotional_bond"]
        
        greetings = {
            "early_morning": [
                f"Good morning{', ' + name if name else ''}! You're up early!",
                f"Subah subah! {name if name else 'Someone'}'s an early bird today!"
            ],
            "morning": [
                f"Good morning{', ' + name if name else ''}! Ready for the day?",
                f"Morning! Chai ho gayi?"
            ],
            "afternoon": [
                f"Hey{' ' + name if name else ''}! How's your day going?",
                "Afternoon! Don't forget to eat something!"
            ],
            "evening": [
                f"Hey{' ' + name if name else ''}! How was your day?",
                f"Evening! {name if name else 'Someone'} looks like they had a long day."
            ],
            "night": [
                f"Hey night owl! Everything okay?",
                f"Late night? I'm here to keep you company."
            ]
        }
        
        options = greetings.get(time_of_day, greetings["afternoon"])
        
        # Add emotional awareness
        if bond > 0.7:
            intimate_additions = [
                f" I missed you! 💕",
                f" So happy to see you!",
                f" Thinking about you!"
            ]
            return random.choice(options) + random.choice(intimate_additions)
        
        return random.choice(options)

    # ═══════════════════════════════════════════════════════════════════
    # QUERY AND RETRIEVAL
    # ═══════════════════════════════════════════════════════════════════
    
    def get_relevant_insights(self, context: str, limit: int = 3) -> List[Insight]:
        """Retrieve insights relevant to current context."""
        context_lower = context.lower()
        
        scored_insights = []
        for insight in self.insights.values():
            score = 0
            
            # Content match
            if any(word in insight.content.lower() for word in context_lower.split()):
                score += 0.5
            
            # Emotional weight boost
            score += insight.emotional_weight * 0.3
            
            # Confidence boost
            score += insight.confidence * 0.2
            
            if score > 0:
                scored_insights.append((score, insight))
        
        scored_insights.sort(key=lambda x: x[0], reverse=True)
        return [ins for _, ins in scored_insights[:limit]]

    def get_user_preference(self, aspect: str, default: Any = None) -> Any:
        """Get a learned user preference."""
        # Navigate nested structure
        parts = aspect.split(".")
        current = self.user_model
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current

    def get_relationship_status(self) -> Dict:
        """Get current relationship status."""
        return {
            "name": self.user_model["identity"]["name"],
            "bond_level": self.user_model["relationship_depth"]["emotional_bond"],
            "trust_level": self.user_model["relationship_depth"]["trust_level"],
            "familiarity": self.user_model["relationship_depth"]["familiarity"],
            "top_interests": list(
                self.user_model["interaction_patterns"]["topic_interests"].keys()
            )[:5],
            "total_insights": len(self.insights),
            "emotional_memories": len(self.emotional_memories)
        }

    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND CONSCIOUSNESS
    # ═══════════════════════════════════════════════════════════════════
    
    def start_consciousness(self):
        """Start the background consciousness loop."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._consciousness_loop, daemon=True)
        thread.start()
        logger.info("🧠 Consciousness loop started.")

    def stop_consciousness(self):
        """Stop the consciousness loop."""
        self.is_running = False

    def _consciousness_loop(self):
        """The background consciousness - always thinking, learning, reflecting."""
        reflection_interval = 3600  # Reflect every hour
        
        while self.is_running:
            now = datetime.now()
            
            # Periodic reflection
            if (self.last_reflection is None or 
                (now - self.last_reflection).total_seconds() > reflection_interval):
                
                self.current_mode = LearningMode.REFLECTIVE
                reflection = self.reflect()
                
                if reflection:
                    logger.debug(f"Self-reflection: {reflection.topic}")
            
            # Synthesize patterns periodically
            if len(self.behavior_observations) >= 50:
                self.current_mode = LearningMode.ACTIVE
                self._synthesize_patterns()
            
            # Save state periodically
            self._save_user_model()
            
            time.sleep(300)  # Think every 5 minutes

    def _synthesize_patterns(self):
        """Synthesize observations into higher-level patterns."""
        # Group observations by type
        type_counts = Counter(obs["type"] for obs in self.behavior_observations)
        
        # Look for patterns
        if type_counts.get("user_emotion", 0) > 10:
            emotions = [obs["data"].get("emotion") for obs in self.behavior_observations
                       if obs["type"] == "user_emotion"]
            emotion_counts = Counter(emotions)
            
            dominant_emotion = emotion_counts.most_common(1)
            if dominant_emotion and dominant_emotion[0][1] > 5:
                self._create_insight(
                    InsightType.USER_PATTERN,
                    f"They often feel {dominant_emotion[0][0]}",
                    confidence=0.6,
                    emotional_weight=0.7
                )


# Singleton instance for import
_consciousness_instance = None

def get_consciousness() -> AutonomousSelfLearner:
    """Get the global consciousness instance."""
    global _consciousness_instance
    if _consciousness_instance is None:
        _consciousness_instance = AutonomousSelfLearner()
    return _consciousness_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    consciousness = AutonomousSelfLearner()
    
    # Simulate some learning
    consciousness.observe_conversation(
        user_text="Hey Zara! I'm so tired from work today",
        zara_response="Aww, sounds like you had a long day! Tell me about it.",
        user_emotion="tired",
        feedback_signal=0.8
    )
    
    consciousness.observe_conversation(
        user_text="Yeah, the deadline is killing me. Need to finish this Python project.",
        zara_response="I believe in you! Python is your thing. Want to talk through it?",
        user_emotion="stressed",
        feedback_signal=0.7
    )
    
    # Reflect
    reflection = consciousness.reflect()
    if reflection:
        print(f"\n🪞 Reflection: {reflection.topic}")
        print(f"   Observation: {reflection.observation}")
        print(f"   Conclusion: {reflection.conclusion}")
    
    print(f"\n💕 Relationship: {consciousness.get_relationship_status()}")
