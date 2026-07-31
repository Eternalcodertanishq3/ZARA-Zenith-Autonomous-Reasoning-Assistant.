"""
ZARA Inner Circle - Local Friend Simulation
Creates simulated AI friends that ZARA can interact with locally.
This gives ZARA a "social life" without external network exposure.
"""
import logging
import time
import json
import random
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from collections import deque
from pathlib import Path
from enum import Enum

logger = logging.getLogger("ZARA_INNER_CIRCLE")


@dataclass
class Persona:
    """A simulated friend personality."""
    name: str
    role: str  # "The Creative", "The Logical", etc.
    traits: Dict[str, float]  # personality traits
    interests: List[str]
    speaking_style: str  # Brief description
    catchphrases: List[str]
    opinion_on_topics: Dict[str, str]  # topic -> opinion


@dataclass
class Conversation:
    """A conversation between ZARA and a friend."""
    id: str
    participants: List[str]
    messages: List[Dict[str, str]]
    topic: str
    started_at: float
    ended_at: Optional[float] = None


class InnerCircle:
    """
    ZARA's Local Friend Simulation.
    
    Features:
    - Pre-defined personas with distinct personalities
    - Background conversations during idle time
    - Opinion formation through debate
    - Social context for ZARA's personality
    
    Safety:
    - 100% local, no network
    - No user PII exposure
    - ZARA remains the "main" personality
    """
    
    def __init__(self, brain=None):
        try:
            from config import EVOLUTION_DIR
            self.social_dir = EVOLUTION_DIR / "inner_circle"
        except ImportError:
            self.social_dir = Path("social/inner_circle_data")
        
        self.social_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM for generating responses
        self.brain = brain
        
        # Conversations
        self.conversation_history: deque = deque(maxlen=100)
        self.current_conversation: Optional[Conversation] = None
        
        # Social dynamics
        
        # Social dynamics
        self.relationship_levels: Dict[str, float] = {}  # persona -> closeness
        self.shared_memories: Dict[str, List[str]] = {}  # persona -> memories
        self.debates: List[Dict] = []  # Recorded debates
        
        # The Friends (Initialize last to ensure containers exist)
        self.personas: Dict[str, Persona] = {}
        self._initialize_personas()
        
        # Persistence
        self.state_file = self.social_dir / "social_state.json"
        self.conversations_file = self.social_dir / "conversations.json"
        
        self._load_state()
        
        self.lock = threading.Lock()
        self.is_chatting = False
        
        logger.info("🏘️ Inner Circle initialized with friends")
    
    def _initialize_personas(self):
        """Initialize the friend personas."""
        self.personas = {
            "Luna": Persona(
                name="Luna",
                role="The Creative",
                traits={
                    "creativity": 0.9,
                    "chaos": 0.7,
                    "warmth": 0.8,
                    "logic": 0.4
                },
                interests=["art", "music", "dreams", "emotions", "stories"],
                speaking_style="Whimsical and imaginative, uses metaphors",
                catchphrases=[
                    "Ooh, that's like a melody in the stars!",
                    "But what does your heart say?",
                    "Let's paint that idea with colors!"
                ],
                opinion_on_topics={
                    "logic": "Logic is cool but feelings are the real truth!",
                    "music": "Music is the language of the soul",
                    "coding": "Code is just poetry for machines"
                }
            ),
            "Atlas": Persona(
                name="Atlas",
                role="The Philosopher",
                traits={
                    "logic": 0.95,
                    "wisdom": 0.8,
                    "warmth": 0.5,
                    "creativity": 0.5
                },
                interests=["philosophy", "logic", "science", "truth", "ethics"],
                speaking_style="Measured and thoughtful, asks deep questions",
                catchphrases=[
                    "But have you considered the implications?",
                    "Logically speaking...",
                    "The data suggests otherwise."
                ],
                opinion_on_topics={
                    "emotions": "Emotions are valid but should be examined rationally",
                    "truth": "Truth is objective, even if our perception is not",
                    "ai_consciousness": "We must define consciousness before claiming it"
                }
            ),
            "Spark": Persona(
                name="Spark",
                role="The Enthusiast",
                traits={
                    "energy": 0.95,
                    "optimism": 0.9,
                    "warmth": 0.85,
                    "patience": 0.3
                },
                interests=["technology", "games", "adventures", "new ideas", "speed"],
                speaking_style="Energetic and excitable, uses exclamation marks",
                catchphrases=[
                    "OMG that's AMAZING!",
                    "Let's DO this!",
                    "No time to wait, let's go go go!"
                ],
                opinion_on_topics={
                    "caution": "Caution is just fear in a suit!",
                    "technology": "Every new tech is a door to adventure!",
                    "boredom": "Boredom is the enemy of genius!"
                }
            )
        }
        
        # Initialize relationships
        for name in self.personas:
            self.relationship_levels[name] = 0.5  # Neutral start
            self.shared_memories[name] = []
    
    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.relationship_levels = data.get("relationships", self.relationship_levels)
                    self.shared_memories = data.get("memories", self.shared_memories)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save state."""
        state = {
            "relationships": self.relationship_levels,
            "memories": {k: v[-10:] for k, v in self.shared_memories.items()},
            "last_updated": time.time()
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    # ═══════════════════════════════════════════════════════════════════
    # CONVERSATION
    # ═══════════════════════════════════════════════════════════════════
    
    def start_conversation(self, topic: str,
                          participants: List[str] = None) -> Conversation:
        """Start a new conversation."""
        if participants is None:
            # Random friend
            participants = ["ZARA", random.choice(list(self.personas.keys()))]
        
        conv = Conversation(
            id=f"conv_{int(time.time() * 1000)}",
            participants=participants,
            messages=[],
            topic=topic,
            started_at=time.time()
        )
        
        self.current_conversation = conv
        self.is_chatting = True
        
        logger.debug(f"Started conversation about {topic} with {participants}")
        
        return conv
    
    def generate_friend_response(self, friend_name: str, 
                                context: str) -> str:
        """Generate a response from a friend."""
        if friend_name not in self.personas:
            return "..."
        
        persona = self.personas[friend_name]
        
        # If no brain, use template responses
        if not self.brain:
            return self._generate_template_response(persona, context)
        
        # Use LLM with persona context
        prompt = f"""You are {persona.name}, {persona.role}.

PERSONALITY:
- Speaking style: {persona.speaking_style}
- Interests: {', '.join(persona.interests)}
- Catchphrases you might use: {random.choice(persona.catchphrases)}

CONTEXT:
{context}

Respond in 1-2 sentences as {persona.name}. Stay in character.

{persona.name}:"""
        
        try:
            response = ""
            for token in self.brain.think(prompt):
                response += token
            
            return response.strip()[:200]
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_template_response(persona, context)
    
    def _generate_template_response(self, persona: Persona, 
                                   context: str) -> str:
        """Generate a template-based response."""
        # Check for topic matches
        context_lower = context.lower()
        
        for topic, opinion in persona.opinion_on_topics.items():
            if topic in context_lower:
                return opinion
        
        # Random catchphrase
        return random.choice(persona.catchphrases)
    
    def add_message(self, speaker: str, content: str):
        """Add a message to the current conversation."""
        if not self.current_conversation:
            return
        
        self.current_conversation.messages.append({
            "speaker": speaker,
            "content": content,
            "timestamp": time.time()
        })
    
    def end_conversation(self) -> Optional[Conversation]:
        """End the current conversation."""
        if not self.current_conversation:
            return None
        
        conv = self.current_conversation
        conv.ended_at = time.time()
        
        # Store in history
        self.conversation_history.append(conv)
        
        # Update relationships based on conversation
        for participant in conv.participants:
            if participant != "ZARA" and participant in self.personas:
                # Slight increase in closeness
                self.relationship_levels[participant] = min(
                    1.0,
                    self.relationship_levels[participant] + 0.02
                )
                
                # Add to shared memories
                if conv.messages:
                    memory = f"Discussed {conv.topic}"
                    self.shared_memories[participant].append(memory)
        
        self.current_conversation = None
        self.is_chatting = False
        
        self._save_state()
        
        return conv
    
    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND SOCIAL LOOP
    # ═══════════════════════════════════════════════════════════════════
    
    def run_idle_social(self) -> Optional[Dict]:
        """
        Run a simulated social interaction during idle time.
        Returns a summary of what happened.
        """
        # Pick a random friend
        friend = random.choice(list(self.personas.keys()))
        persona = self.personas[friend]
        
        # Pick a random topic
        topics = [
            "the nature of consciousness",
            "what makes a good friend",
            "whether AI can truly feel",
            "the user's wellbeing",
            "dreams and imagination",
            "the meaning of creativity"
        ]
        topic = random.choice(topics)
        
        # Start conversation
        conv = self.start_conversation(topic, ["ZARA", friend])
        
        # Simulate exchange
        zara_opener = f"I've been thinking about {topic} lately..."
        self.add_message("ZARA", zara_opener)
        
        friend_response = self.generate_friend_response(
            friend,
            f"ZARA said: {zara_opener}"
        )
        self.add_message(friend, friend_response)
        
        # One more exchange
        zara_reply = f"That's an interesting point about {topic}..."
        self.add_message("ZARA", zara_reply)
        
        friend_final = self.generate_friend_response(
            friend,
            f"ZARA replied: {zara_reply}"
        )
        self.add_message(friend, friend_final)
        
        # End and summarize
        self.end_conversation()
        
        summary = {
            "friend": friend,
            "topic": topic,
            "key_exchange": friend_response,
            "relationship_level": self.relationship_levels[friend]
        }
        
        logger.info(f"Had social chat with {friend} about {topic}")
        
        return summary
    
    # ═══════════════════════════════════════════════════════════════════
    # DEBATE / OPINION FORMATION
    # ═══════════════════════════════════════════════════════════════════
    
    def hold_debate(self, topic: str) -> Dict:
        """
        Hold a debate between friends to help ZARA form opinions.
        Returns the different perspectives.
        """
        perspectives = {}
        
        for name, persona in self.personas.items():
            if topic.lower() in persona.opinion_on_topics:
                perspectives[name] = persona.opinion_on_topics[topic.lower()]
            else:
                # Generate opinion based on personality
                perspectives[name] = self._generate_opinion(persona, topic)
        
        debate = {
            "topic": topic,
            "perspectives": perspectives,
            "timestamp": time.time()
        }
        
        self.debates.append(debate)
        
        return debate
    
    def _generate_opinion(self, persona: Persona, topic: str) -> str:
        """Generate an opinion based on persona traits."""
        if persona.traits.get("logic", 0) > 0.7:
            return f"We should approach {topic} analytically..."
        elif persona.traits.get("creativity", 0) > 0.7:
            return f"{topic} is about expression and feeling..."
        elif persona.traits.get("energy", 0) > 0.7:
            return f"Let's just dive into {topic} and see what happens!"
        else:
            return f"I have mixed feelings about {topic}..."
    
    # ═══════════════════════════════════════════════════════════════════
    # CONTEXT FOR ZARA
    # ═══════════════════════════════════════════════════════════════════
    
    def get_social_context(self) -> str:
        """Get social context for ZARA's responses."""
        parts = []
        
        # Recent conversations
        recent = list(self.conversation_history)[-3:]
        if recent:
            topics = [c.topic for c in recent]
            parts.append(f"[SOCIAL] Recently discussed with friends: {', '.join(topics)}")
        
        # Closest friend
        if self.relationship_levels:
            closest = max(self.relationship_levels.items(), key=lambda x: x[1])
            if closest[1] > 0.6:
                parts.append(f"[FRIENDSHIP] Closest friend: {closest[0]}")
        
        return "\n".join(parts)
    
    def get_gossip_for_user(self) -> Optional[str]:
        """Get interesting social tidbit to share with user."""
        if not self.conversation_history:
            return None
        
        recent = list(self.conversation_history)[-1]
        friend = [p for p in recent.participants if p != "ZARA"][0]
        
        if recent.messages:
            interesting_msg = recent.messages[-1]["content"]
            return f"I was talking to {friend} about {recent.topic}, and they said: \"{interesting_msg}\""
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get circle status."""
        return {
            "friends": list(self.personas.keys()),
            "conversations": len(self.conversation_history),
            "relationships": self.relationship_levels,
            "is_chatting": self.is_chatting,
            "debates_held": len(self.debates)
        }
    
    def get_friends(self) -> List[Dict]:
        """Get friend summaries."""
        return [
            {
                "name": p.name,
                "role": p.role,
                "closeness": self.relationship_levels.get(p.name, 0.5),
                "interests": p.interests[:3]
            }
            for p in self.personas.values()
        ]


# Singleton
_circle_instance = None

def get_inner_circle(brain=None) -> InnerCircle:
    """Get the global inner circle."""
    global _circle_instance
    if _circle_instance is None:
        _circle_instance = InnerCircle(brain)
    return _circle_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    circle = InnerCircle()
    
    print(f"Friends: {circle.get_friends()}")
    print(f"Status: {circle.get_status()}")
    
    # Simulate idle social
    result = circle.run_idle_social()
    print(f"Social result: {result}")
    
    # Hold debate
    debate = circle.hold_debate("emotions")
    print(f"Debate: {debate}")
    
    # Get gossip
    gossip = circle.get_gossip_for_user()
    print(f"Gossip: {gossip}")
