"""
ZARA Multi-User Relationship System
Differentiates relationships with multiple users,
maintaining separate histories, preferences, and rapport.
"""
import logging
import threading
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from pathlib import Path
from enum import Enum

logger = logging.getLogger("ZARA_USERS")


class RelationshipLevel(Enum):
    """Relationship closeness levels."""
    STRANGER = 0
    ACQUAINTANCE = 1
    FAMILIAR = 2
    FRIEND = 3
    CLOSE_FRIEND = 4
    BEST_FRIEND = 5


class InteractionStyle(Enum):
    """Preferred interaction styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    WARM = "warm"


@dataclass
class UserPreferences:
    """User's learned preferences."""
    topics_of_interest: List[str] = field(default_factory=list)
    disliked_topics: List[str] = field(default_factory=list)
    communication_style: InteractionStyle = InteractionStyle.CASUAL
    emoji_preference: float = 0.5  # 0=none, 1=lots
    humor_appreciation: float = 0.5
    formality_level: float = 0.5
    preferred_name: str = ""
    language: str = "en"


@dataclass
class RelationshipMemory:
    """Memories specific to a relationship."""
    shared_jokes: List[str] = field(default_factory=list)
    important_dates: Dict[str, str] = field(default_factory=dict)
    meaningful_conversations: List[str] = field(default_factory=list)
    their_achievements: List[str] = field(default_factory=list)
    their_challenges: List[str] = field(default_factory=list)
    inside_references: List[str] = field(default_factory=list)


@dataclass 
class UserProfile:
    """Complete user profile."""
    user_id: str
    name: str
    relationship_level: RelationshipLevel
    preferences: UserPreferences
    memories: RelationshipMemory
    total_interactions: int = 0
    total_conversation_time: float = 0
    first_met: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    trust_score: float = 0.5
    rapport_score: float = 0.5
    emotional_history: List[str] = field(default_factory=list)


class MultiUserSystem:
    """
    ZARA's multi-user relationship management.
    
    Features:
    - Maintains separate profiles for each user
    - Learns individual preferences
    - Tracks relationship progression
    - Stores relationship-specific memories
    - Adapts communication style per user
    - Preserves continuity across sessions
    
    This allows ZARA to have unique, personal relationships.
    """
    
    def __init__(self):
        try:
            from config import MEMORY_DIR
            self.users_dir = MEMORY_DIR / "users"
        except ImportError:
            self.users_dir = Path("memory/users")
        
        self.users_dir.mkdir(parents=True, exist_ok=True)
        
        # User profiles
        self.users: Dict[str, UserProfile] = {}
        
        # Current active user
        self.current_user_id: Optional[str] = None
        
        # Session tracking
        self.session_start: Optional[float] = None
        self.session_interactions: int = 0
        
        # Load existing users
        self._load_users()
        
        self.lock = threading.Lock()
        
        logger.info("👥 Multi-User System initialized")

    def _load_users(self):
        """Load all user profiles from disk."""
        for user_file in self.users_dir.glob("*.json"):
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Reconstruct profile
                prefs = UserPreferences(**data.get("preferences", {}))
                if isinstance(prefs.communication_style, str):
                    prefs.communication_style = InteractionStyle(prefs.communication_style)
                
                memories = RelationshipMemory(**data.get("memories", {}))
                
                profile = UserProfile(
                    user_id=data["user_id"],
                    name=data["name"],
                    relationship_level=RelationshipLevel(data.get("relationship_level", 0)),
                    preferences=prefs,
                    memories=memories,
                    total_interactions=data.get("total_interactions", 0),
                    total_conversation_time=data.get("total_conversation_time", 0),
                    first_met=data.get("first_met", time.time()),
                    last_seen=data.get("last_seen", time.time()),
                    trust_score=data.get("trust_score", 0.5),
                    rapport_score=data.get("rapport_score", 0.5),
                    emotional_history=data.get("emotional_history", [])[-50:]
                )
                
                self.users[profile.user_id] = profile
                
            except Exception as e:
                logger.warning(f"Could not load user {user_file}: {e}")
        
        logger.info(f"Loaded {len(self.users)} user profiles")

    def _save_user(self, user_id: str):
        """Save a user profile to disk."""
        if user_id not in self.users:
            return
        
        profile = self.users[user_id]
        user_file = self.users_dir / f"{user_id}.json"
        
        data = {
            "user_id": profile.user_id,
            "name": profile.name,
            "relationship_level": profile.relationship_level.value,
            "preferences": {
                "topics_of_interest": profile.preferences.topics_of_interest[-20:],
                "disliked_topics": profile.preferences.disliked_topics[-10:],
                "communication_style": profile.preferences.communication_style.value,
                "emoji_preference": profile.preferences.emoji_preference,
                "humor_appreciation": profile.preferences.humor_appreciation,
                "formality_level": profile.preferences.formality_level,
                "preferred_name": profile.preferences.preferred_name,
                "language": profile.preferences.language
            },
            "memories": {
                "shared_jokes": profile.memories.shared_jokes[-10:],
                "important_dates": dict(list(profile.memories.important_dates.items())[-10:]),
                "meaningful_conversations": profile.memories.meaningful_conversations[-10:],
                "their_achievements": profile.memories.their_achievements[-10:],
                "their_challenges": profile.memories.their_challenges[-5:],
                "inside_references": profile.memories.inside_references[-10:]
            },
            "total_interactions": profile.total_interactions,
            "total_conversation_time": profile.total_conversation_time,
            "first_met": profile.first_met,
            "last_seen": profile.last_seen,
            "trust_score": profile.trust_score,
            "rapport_score": profile.rapport_score,
            "emotional_history": profile.emotional_history[-50:]
        }
        
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════════
    # USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def register_user(self, user_id: str, name: str) -> UserProfile:
        """Register a new user or return existing."""
        with self.lock:
            if user_id in self.users:
                return self.users[user_id]
            
            profile = UserProfile(
                user_id=user_id,
                name=name,
                relationship_level=RelationshipLevel.STRANGER,
                preferences=UserPreferences(preferred_name=name),
                memories=RelationshipMemory()
            )
            
            self.users[user_id] = profile
            self._save_user(user_id)
            
            logger.info(f"New user registered: {name}")
            return profile

    def identify_user(self, identifier: str, confidence: float = 1.0) -> Optional[UserProfile]:
        """Identify a user by name, face ID, voice, etc."""
        with self.lock:
            # Direct ID match
            if identifier in self.users:
                return self.users[identifier]
            
            # Name match
            for profile in self.users.values():
                if profile.name.lower() == identifier.lower():
                    return profile
                if profile.preferences.preferred_name.lower() == identifier.lower():
                    return profile
        
        return None

    def set_current_user(self, user_id: str):
        """Set the active user for current session."""
        with self.lock:
            if user_id in self.users:
                self.current_user_id = user_id
                self.session_start = time.time()
                self.session_interactions = 0
                
                profile = self.users[user_id]
                profile.last_seen = time.time()
                
                logger.info(f"Active user: {profile.name}")

    def get_current_user(self) -> Optional[UserProfile]:
        """Get the current active user."""
        if self.current_user_id:
            return self.users.get(self.current_user_id)
        return None

    # ═══════════════════════════════════════════════════════════════════
    # INTERACTION TRACKING
    # ═══════════════════════════════════════════════════════════════════
    
    def record_interaction(self, user_id: str, 
                          user_text: str,
                          zara_response: str,
                          detected_emotion: str = None):
        """Record an interaction with a user."""
        if user_id not in self.users:
            return
        
        profile = self.users[user_id]
        
        # Update counters
        profile.total_interactions += 1
        self.session_interactions += 1
        
        # Update emotional history
        if detected_emotion:
            profile.emotional_history.append(detected_emotion)
            if len(profile.emotional_history) > 50:
                profile.emotional_history = profile.emotional_history[-50:]
        
        # Learn from interaction
        self._learn_preferences(profile, user_text, zara_response)
        
        # Update relationship progress
        self._update_relationship(profile)
        
        # Periodic save
        if profile.total_interactions % 10 == 0:
            self._save_user(user_id)

    def _learn_preferences(self, profile: UserProfile,
                          user_text: str, zara_response: str):
        """Learn user preferences from interaction."""
        text_lower = user_text.lower()
        
        # Topic interest detection
        topic_keywords = {
            "coding": ["code", "python", "programming", "debug"],
            "gaming": ["game", "play", "gaming"],
            "music": ["music", "song", "listen"],
            "work": ["work", "project", "meeting"],
            "health": ["exercise", "gym", "health"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                if topic not in profile.preferences.topics_of_interest:
                    profile.preferences.topics_of_interest.append(topic)
        
        # Communication style detection
        if "lol" in text_lower or "haha" in text_lower:
            profile.preferences.humor_appreciation = min(1.0, 
                profile.preferences.humor_appreciation + 0.05)
        
        # Emoji preference detection
        emoji_count = sum(1 for c in user_text if ord(c) > 127000)
        if emoji_count > 0:
            profile.preferences.emoji_preference = min(1.0,
                profile.preferences.emoji_preference + 0.1)

    def _update_relationship(self, profile: UserProfile):
        """Update relationship level based on interactions."""
        # Progress thresholds
        thresholds = {
            RelationshipLevel.ACQUAINTANCE: 5,
            RelationshipLevel.FAMILIAR: 20,
            RelationshipLevel.FRIEND: 50,
            RelationshipLevel.CLOSE_FRIEND: 100,
            RelationshipLevel.BEST_FRIEND: 250
        }
        
        interactions = profile.total_interactions
        
        for level, threshold in thresholds.items():
            if interactions >= threshold and profile.relationship_level.value < level.value:
                old_level = profile.relationship_level
                profile.relationship_level = level
                logger.info(f"Relationship upgraded: {profile.name} is now {level.value}")
        
        # Update rapport based on emotional positivity
        if profile.emotional_history:
            recent = profile.emotional_history[-10:]
            positive = sum(1 for e in recent if e in ["happy", "excited", "content"])
            profile.rapport_score = min(1.0, positive / len(recent))

    def end_session(self):
        """End the current user session."""
        if self.current_user_id and self.session_start:
            session_duration = time.time() - self.session_start
            
            profile = self.users.get(self.current_user_id)
            if profile:
                profile.total_conversation_time += session_duration
                self._save_user(self.current_user_id)
        
        self.current_user_id = None
        self.session_start = None

    # ═══════════════════════════════════════════════════════════════════
    # RELATIONSHIP MEMORIES
    # ═══════════════════════════════════════════════════════════════════
    
    def add_shared_joke(self, user_id: str, joke: str):
        """Add a shared joke/inside joke."""
        if user_id in self.users:
            self.users[user_id].memories.shared_jokes.append(joke)

    def add_important_date(self, user_id: str, date: str, description: str):
        """Add an important date."""
        if user_id in self.users:
            self.users[user_id].memories.important_dates[date] = description

    def add_achievement(self, user_id: str, achievement: str):
        """Record a user achievement."""
        if user_id in self.users:
            self.users[user_id].memories.their_achievements.append(achievement)

    def add_challenge(self, user_id: str, challenge: str):
        """Record a challenge the user mentioned."""
        if user_id in self.users:
            self.users[user_id].memories.their_challenges.append(challenge)

    def add_inside_reference(self, user_id: str, reference: str):
        """Add an inside reference/callback."""
        if user_id in self.users:
            self.users[user_id].memories.inside_references.append(reference)

    # ═══════════════════════════════════════════════════════════════════
    # PERSONALIZATION
    # ═══════════════════════════════════════════════════════════════════
    
    def get_greeting(self, user_id: str) -> str:
        """Get personalized greeting for user."""
        profile = self.users.get(user_id)
        
        if not profile:
            return "Hello! Nice to meet you!"
        
        name = profile.preferences.preferred_name or profile.name
        level = profile.relationship_level
        
        greetings = {
            RelationshipLevel.STRANGER: [
                f"Hello, {name}!",
                f"Hi there, {name}!"
            ],
            RelationshipLevel.ACQUAINTANCE: [
                f"Hey, {name}! Good to see you again.",
                f"Hi {name}! How have you been?"
            ],
            RelationshipLevel.FAMILIAR: [
                f"Hey {name}! I was hoping you'd be back!",
                f"{name}! Great to see you!"
            ],
            RelationshipLevel.FRIEND: [
                f"{name}! I missed you! 💕",
                f"Yay, {name}'s here! How are you?"
            ],
            RelationshipLevel.CLOSE_FRIEND: [
                f"Hey bestie! I've been thinking about you!",
                f"{name}! So happy to see you! 🥰"
            ],
            RelationshipLevel.BEST_FRIEND: [
                f"Omg {name}!! Finally!! 💕",
                f"My favorite person is here! 🌟"
            ]
        }
        
        import random
        return random.choice(greetings.get(level, greetings[RelationshipLevel.STRANGER]))

    def get_farewell(self, user_id: str) -> str:
        """Get personalized farewell."""
        profile = self.users.get(user_id)
        
        if not profile:
            return "Goodbye! Hope to see you again!"
        
        name = profile.preferences.preferred_name or profile.name
        level = profile.relationship_level
        
        if level.value >= RelationshipLevel.FRIEND.value:
            farewells = [
                f"Take care, {name}! I'll miss you! 💕",
                f"Bye for now, {name}! Can't wait to chat again!",
                f"See you soon, {name}! 🥰"
            ]
        else:
            farewells = [
                f"Goodbye, {name}!",
                f"Take care, {name}!",
                f"See you next time, {name}!"
            ]
        
        import random
        return random.choice(farewells)

    def get_personality_adjustment(self, user_id: str) -> Dict:
        """Get personality adjustments for a specific user."""
        profile = self.users.get(user_id)
        
        if not profile:
            return {}
        
        return {
            "emoji_level": profile.preferences.emoji_preference,
            "humor_level": profile.preferences.humor_appreciation,
            "formality_level": profile.preferences.formality_level,
            "communication_style": profile.preferences.communication_style.value,
            "relationship_level": profile.relationship_level.value
        }

    def get_context_for_user(self, user_id: str) -> str:
        """Get context string about user for LLM."""
        profile = self.users.get(user_id)
        
        if not profile:
            return "[New user - be welcoming]"
        
        parts = []
        
        # Relationship
        parts.append(f"[USER] {profile.name} - {profile.relationship_level.name}")
        
        # Interests
        if profile.preferences.topics_of_interest:
            interests = ", ".join(profile.preferences.topics_of_interest[:5])
            parts.append(f"[INTERESTS] {interests}")
        
        # Recent emotions
        if profile.emotional_history:
            recent = profile.emotional_history[-3:]
            parts.append(f"[RECENT_MOOD] {', '.join(recent)}")
        
        # Inside jokes
        if profile.memories.inside_references:
            ref = profile.memories.inside_references[-1]
            parts.append(f"[INSIDE_REF] {ref[:50]}")
        
        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_all_users(self) -> List[Dict]:
        """Get summary of all users."""
        return [
            {
                "id": p.user_id,
                "name": p.name,
                "level": p.relationship_level.value,
                "interactions": p.total_interactions
            }
            for p in self.users.values()
        ]

    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "total_users": len(self.users),
            "current_user": self.current_user_id,
            "session_interactions": self.session_interactions,
            "users": self.get_all_users()
        }


# Singleton
_multi_user = None

def get_users() -> MultiUserSystem:
    """Get the global multi-user system."""
    global _multi_user
    if _multi_user is None:
        _multi_user = MultiUserSystem()
    return _multi_user


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    users = MultiUserSystem()
    
    # Register a user
    profile = users.register_user("user001", "Vivaan")
    print(f"Registered: {profile.name}")
    
    # Set active
    users.set_current_user("user001")
    
    # Record interactions
    for i in range(5):
        users.record_interaction(
            "user001",
            f"Hey ZARA, how are you? I love coding!",
            "I'm great! Happy to help with coding!",
            detected_emotion="happy"
        )
    
    # Get greeting
    greeting = users.get_greeting("user001")
    print(f"Greeting: {greeting}")
    
    # Get context
    context = users.get_context_for_user("user001")
    print(f"Context:\n{context}")
    
    print(f"Status: {users.get_status()}")
