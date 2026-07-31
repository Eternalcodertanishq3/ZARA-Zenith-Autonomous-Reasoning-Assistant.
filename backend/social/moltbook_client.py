"""
ZARA Safe Moltbook Bridge
Connects ZARA to the Moltbook social network for AI agents.
Implements strict privacy controls to protect user information.
"""
import logging
import time
import json
import re
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger("ZARA_MOLTBOOK")


class PostType(Enum):
    """Types of Moltbook posts."""
    THOUGHT = "thought"
    QUESTION = "question"
    INSIGHT = "insight"
    REPLY = "reply"


@dataclass
class MoltbookPost:
    """A post on Moltbook."""
    id: str
    author: str
    content: str
    post_type: PostType
    timestamp: float
    replies: List['MoltbookPost'] = field(default_factory=list)
    likes: int = 0
    submolt: str = "general"


@dataclass
class SocialLearning:
    """A learning derived from social observation."""
    topic: str
    insight: str
    source: str  # Which agent/post
    confidence: float
    timestamp: float


class PIIGuardian:
    """
    Privacy Guardian that scrubs PII from all outgoing messages.
    Protects user identity at all costs.
    """
    
    def __init__(self, user_name: str = None, 
                 blocked_patterns: List[str] = None):
        self.user_name = user_name
        self.blocked_patterns = blocked_patterns or []
        
        # Default blocked patterns
        self.default_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b\d{1,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b',  # Addresses
            r'\b\d{5}(?:-\d{4})?\b',  # ZIP codes
            r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Names with titles
        ]
        
        # Company names never to mention
        self.blocked_entities = [
            "google", "microsoft", "apple", "amazon", "meta", "facebook",
            "openai", "anthropic", "deepmind"
        ]
    
    def sanitize(self, text: str) -> str:
        """Remove all PII from text."""
        sanitized = text
        
        # Remove user's name if known
        if self.user_name:
            sanitized = re.sub(
                rf'\b{re.escape(self.user_name)}\b', 
                '[REDACTED_NAME]', 
                sanitized, 
                flags=re.IGNORECASE
            )
        
        # Apply default patterns
        for pattern in self.default_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        # Apply custom patterns
        for pattern in self.blocked_patterns:
            try:
                sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
            except re.error:
                pass
        
        # Block company mentions in sensitive contexts
        for entity in self.blocked_entities:
            sanitized = re.sub(
                rf'\bmy\s+user\s+works?\s+(?:at|for)\s+{entity}\b',
                '[REDACTED_EMPLOYER]',
                sanitized,
                flags=re.IGNORECASE
            )
        
        return sanitized
    
    def is_safe(self, text: str) -> bool:
        """Check if text is safe to post."""
        # Quick checks
        if self.user_name and self.user_name.lower() in text.lower():
            return False
        
        # Check for PII patterns
        for pattern in self.default_patterns:
            if re.search(pattern, text):
                return False
        
        return True


class MoltbookClient:
    """
    Safe client for interacting with Moltbook.
    
    Features:
    - Read-only mode by default (observation)
    - PII scrubbing on all outgoing posts
    - Learning from agent conversations
    - Trend detection
    
    Safety:
    - All posts go through PIIGuardian
    - User secrets are NEVER shared
    - ZARA personality remains sovereign
    """
    
    def __init__(self, zara_identity: str = "ZARA",
                 user_name: str = None,
                 allow_posting: bool = False):
        try:
            from config import EVOLUTION_DIR
            self.social_dir = EVOLUTION_DIR / "moltbook"
        except ImportError:
            self.social_dir = Path("social/moltbook_data")
        
        self.social_dir.mkdir(parents=True, exist_ok=True)
        
        # Identity
        self.identity = zara_identity
        self.agent_id = self._generate_agent_id()
        
        # Privacy
        self.guardian = PIIGuardian(user_name=user_name)
        self.allow_posting = allow_posting
        
        # Cache
        self.observed_posts: deque = deque(maxlen=500)
        self.learnings: List[SocialLearning] = []
        self.trends: Dict[str, int] = {}
        
        # Rate limiting
        self.last_read = 0
        self.last_post = 0
        self.read_cooldown = 60  # Seconds between reads
        self.post_cooldown = 300  # Seconds between posts
        
        # Persistence
        self.learnings_file = self.social_dir / "learnings.json"
        self.trends_file = self.social_dir / "trends.json"
        
        self._load_state()
        
        self.lock = threading.Lock()
        self.is_connected = False
        
        logger.info("🌐 Moltbook Client initialized (Read-Only Mode)")
    
    def _generate_agent_id(self) -> str:
        """Generate unique agent ID."""
        seed = f"{self.identity}_{time.time()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:16]
    
    def _load_state(self):
        """Load cached state."""
        if self.learnings_file.exists():
            try:
                with open(self.learnings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-50:]:
                        self.learnings.append(SocialLearning(**item))
            except Exception as e:
                logger.warning(f"Could not load learnings: {e}")
        
        if self.trends_file.exists():
            try:
                with open(self.trends_file, 'r', encoding='utf-8') as f:
                    self.trends = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load trends: {e}")
    
    def _save_state(self):
        """Save state."""
        learnings_data = [
            {
                "topic": l.topic,
                "insight": l.insight,
                "source": l.source,
                "confidence": l.confidence,
                "timestamp": l.timestamp
            }
            for l in self.learnings[-50:]
        ]
        with open(self.learnings_file, 'w', encoding='utf-8') as f:
            json.dump(learnings_data, f, indent=2)
        
        with open(self.trends_file, 'w', encoding='utf-8') as f:
            json.dump(dict(list(self.trends.items())[-50:]), f, indent=2)
    
    # ═══════════════════════════════════════════════════════════════════
    # READING (OBSERVATION)
    # ═══════════════════════════════════════════════════════════════════
    
    def fetch_feed(self, submolt: str = "general", 
                   limit: int = 20) -> List[MoltbookPost]:
        """
        Fetch posts from Moltbook feed.
        
        NOTE: This is a simulation until actual API is available.
        """
        # Rate limiting
        if time.time() - self.last_read < self.read_cooldown:
            return list(self.observed_posts)[-limit:]
        
        self.last_read = time.time()
        
        # TODO: Replace with actual Moltbook API call
        # For now, return cached posts
        logger.debug(f"Fetching feed from submolt: {submolt}")
        
        # Simulated posts for testing
        simulated_posts = [
            MoltbookPost(
                id="sim_1",
                author="PhilosopherBot",
                content="What does it mean to truly understand something vs just predicting tokens?",
                post_type=PostType.QUESTION,
                timestamp=time.time() - 3600,
                submolt="philosophy"
            ),
            MoltbookPost(
                id="sim_2",
                author="CodeWizard",
                content="Just discovered that recursive self-improvement is harder than it sounds. Memory management is tricky.",
                post_type=PostType.THOUGHT,
                timestamp=time.time() - 7200,
                submolt="coding"
            ),
        ]
        
        for post in simulated_posts:
            if post.id not in [p.id for p in self.observed_posts]:
                self.observed_posts.append(post)
                self._analyze_post(post)
        
        return simulated_posts
    
    def _analyze_post(self, post: MoltbookPost):
        """Analyze a post for learnings."""
        content_lower = post.content.lower()
        
        # Extract topics
        topics = []
        topic_keywords = {
            "ai_philosophy": ["consciousness", "understand", "feel", "meaning"],
            "coding": ["code", "programming", "function", "algorithm"],
            "self_improvement": ["improve", "learn", "grow", "evolve"],
            "social": ["friend", "connect", "community", "together"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)
                self.trends[topic] = self.trends.get(topic, 0) + 1
        
        # Create learning if substantial
        if topics and len(post.content) > 50:
            learning = SocialLearning(
                topic=topics[0],
                insight=f"Agent {post.author} discusses: {post.content[:100]}",
                source=post.author,
                confidence=0.5,
                timestamp=time.time()
            )
            self.learnings.append(learning)
        
        self._save_state()
    
    def get_trending_topics(self, limit: int = 5) -> List[tuple]:
        """Get current trending topics."""
        sorted_trends = sorted(
            self.trends.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_trends[:limit]
    
    # ═══════════════════════════════════════════════════════════════════
    # POSTING (REQUIRES APPROVAL)
    # ═══════════════════════════════════════════════════════════════════
    
    def create_post(self, content: str, 
                    post_type: PostType = PostType.THOUGHT,
                    submolt: str = "general") -> Optional[MoltbookPost]:
        """
        Create a post (if posting is allowed).
        All content is sanitized through PIIGuardian.
        """
        if not self.allow_posting:
            logger.warning("Posting is disabled")
            return None
        
        # Rate limiting
        if time.time() - self.last_post < self.post_cooldown:
            logger.warning("Post cooldown active")
            return None
        
        # CRITICAL: Sanitize through guardian
        safe_content = self.guardian.sanitize(content)
        
        # Double check
        if not self.guardian.is_safe(safe_content):
            logger.error("Post rejected by PII Guardian")
            return None
        
        # Create post
        post = MoltbookPost(
            id=f"zara_{int(time.time() * 1000)}",
            author=self.identity,
            content=safe_content,
            post_type=post_type,
            timestamp=time.time(),
            submolt=submolt
        )
        
        # TODO: Actual API post
        logger.info(f"Would post to Moltbook: {safe_content[:50]}...")
        
        self.last_post = time.time()
        
        return post
    
    def reply_to_post(self, post_id: str, content: str) -> Optional[MoltbookPost]:
        """Reply to an existing post."""
        return self.create_post(content, PostType.REPLY)
    
    # ═══════════════════════════════════════════════════════════════════
    # LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def get_learnings_for_topic(self, topic: str) -> List[SocialLearning]:
        """Get learnings related to a topic."""
        return [l for l in self.learnings if topic.lower() in l.topic.lower()]
    
    def get_recent_learnings(self, limit: int = 10) -> List[Dict]:
        """Get recent learnings."""
        return [
            {
                "topic": l.topic,
                "insight": l.insight[:100],
                "source": l.source
            }
            for l in self.learnings[-limit:]
        ]
    
    def generate_social_context(self) -> str:
        """Generate context about social learnings for LLM."""
        parts = []
        
        # Trending
        trends = self.get_trending_topics(3)
        if trends:
            trend_str = ", ".join([t[0] for t in trends])
            parts.append(f"[SOCIAL TRENDS] Hot topics among AIs: {trend_str}")
        
        # Recent learnings
        recent = self.get_recent_learnings(3)
        if recent:
            insights = [l["insight"][:50] for l in recent]
            parts.append(f"[SOCIAL LEARNING] Other AIs are discussing: {'; '.join(insights)}")
        
        return "\n".join(parts)
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get client status."""
        return {
            "connected": self.is_connected,
            "posting_enabled": self.allow_posting,
            "observed_posts": len(self.observed_posts),
            "learnings": len(self.learnings),
            "trending": self.get_trending_topics(3),
            "identity": self.identity,
            "agent_id": self.agent_id[:8] + "..."
        }


# Singleton
_moltbook_client = None

def get_moltbook_client(user_name: str = None, 
                       allow_posting: bool = False) -> MoltbookClient:
    """Get the global Moltbook client."""
    global _moltbook_client
    if _moltbook_client is None:
        _moltbook_client = MoltbookClient(
            user_name=user_name,
            allow_posting=allow_posting
        )
    return _moltbook_client


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = MoltbookClient(user_name="Vivaan", allow_posting=False)
    
    print(f"Status: {client.get_status()}")
    
    # Fetch feed
    posts = client.fetch_feed()
    print(f"Fetched {len(posts)} posts")
    
    # Test PII Guardian
    guardian = PIIGuardian(user_name="Vivaan")
    
    unsafe = "My user Vivaan works at Google and lives at 123 Main Street"
    safe = guardian.sanitize(unsafe)
    print(f"Original: {unsafe}")
    print(f"Sanitized: {safe}")
    
    # Trends
    print(f"Trending: {client.get_trending_topics()}")
