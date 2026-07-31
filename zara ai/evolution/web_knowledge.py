"""
ZARA Web Knowledge System - Real-Time Information Access
Enables ZARA to fetch and learn from the web autonomously.
"""
import logging
import threading
import time
import json
import re
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from pathlib import Path
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger("ZARA_WEB")


class ContentType(Enum):
    """Types of web content."""
    ARTICLE = "article"
    DOCUMENTATION = "documentation"
    NEWS = "news"
    WIKI = "wiki"
    SOCIAL = "social"
    CODE = "code"
    UNKNOWN = "unknown"


@dataclass
class WebContent:
    """Fetched web content."""
    url: str
    title: str
    content: str
    content_type: ContentType
    timestamp: float
    word_count: int
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    relevance_score: float = 0.5


@dataclass
class SearchResult:
    """Web search result."""
    title: str
    url: str
    snippet: str
    source: str
    rank: int


class WebKnowledgeSystem:
    """
    ZARA's web access for real-time knowledge.
    
    Capabilities:
    - Web page content extraction
    - Search query execution
    - Content summarization
    - Knowledge extraction and storage
    - Caching for efficiency
    
    Safety:
    - URL validation
    - Content filtering
    - Rate limiting
    """
    
    def __init__(self):
        try:
            from config import EVOLUTION_DIR
            self.cache_dir = EVOLUTION_DIR / "web_cache"
        except ImportError:
            self.cache_dir = Path("evolution/web_cache")
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Lazy load libraries
        self._requests = None
        self._bs4 = None
        self._available = None
        
        # Cache
        self.content_cache: Dict[str, WebContent] = {}
        self.cache_file = self.cache_dir / "url_cache.json"
        self._load_cache()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        self.requests_this_hour = 0
        self.max_requests_per_hour = 60
        
        # Blocked domains
        self.blocked_domains = {
            "adult", "gambling", "malware", "phishing"
        }
        
        # Knowledge integration
        self.knowledge_system = None
        
        self.lock = threading.Lock()
        
        logger.info("🌐 Web Knowledge System initialized")

    def _load_libraries(self) -> bool:
        """Lazy load web libraries."""
        if self._available is not None:
            return self._available
        
        try:
            import requests
            self._requests = requests
            
            try:
                from bs4 import BeautifulSoup
                self._bs4 = BeautifulSoup
                self._available = True
                logger.info("Web libraries loaded (requests + bs4)")
            except ImportError:
                self._available = False
                logger.warning("BeautifulSoup not available")
        except ImportError:
            self._available = False
            logger.warning("requests library not available")
        
        return self._available

    def _load_cache(self):
        """Load URL cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for url, item in data.items():
                        item['content_type'] = ContentType(item['content_type'])
                        self.content_cache[url] = WebContent(**item)
            except:
                pass

    def _save_cache(self):
        """Save URL cache to disk."""
        cache_data = {}
        for url, content in list(self.content_cache.items())[-100:]:  # Keep 100 recent
            cache_data[url] = {
                "url": content.url,
                "title": content.title,
                "content": content.content[:2000],  # Limit storage
                "content_type": content.content_type.value,
                "timestamp": content.timestamp,
                "word_count": content.word_count,
                "summary": content.summary,
                "key_points": content.key_points[:5],
                "relevance_score": content.relevance_score
            }
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

    def connect_knowledge(self, knowledge_system):
        """Connect to knowledge system for storage."""
        self.knowledge_system = knowledge_system

    # ═══════════════════════════════════════════════════════════════════
    # URL VALIDATION & SAFETY
    # ═══════════════════════════════════════════════════════════════════
    
    def _is_url_safe(self, url: str) -> Tuple[bool, str]:
        """Check if URL is safe to access."""
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            # Only HTTP/HTTPS
            if parsed.scheme not in ["http", "https"]:
                return False, "Only HTTP/HTTPS allowed"
            
            # Check blocked patterns
            domain_lower = parsed.netloc.lower()
            for blocked in self.blocked_domains:
                if blocked in domain_lower:
                    return False, f"Blocked domain pattern: {blocked}"
            
            return True, "OK"
            
        except Exception as e:
            return False, str(e)

    def _can_make_request(self) -> bool:
        """Check rate limits."""
        now = time.time()
        
        # Check minimum interval
        if now - self.last_request_time < self.min_request_interval:
            return False
        
        # Check hourly limit
        if self.requests_this_hour >= self.max_requests_per_hour:
            return False
        
        return True

    # ═══════════════════════════════════════════════════════════════════
    # CONTENT FETCHING
    # ═══════════════════════════════════════════════════════════════════
    
    def fetch_url(self, url: str, force_refresh: bool = False) -> Optional[WebContent]:
        """
        Fetch and parse content from a URL.
        
        Args:
            url: URL to fetch
            force_refresh: Bypass cache
        
        Returns:
            WebContent or None if failed
        """
        if not self._load_libraries():
            logger.warning("Web libraries not available")
            return None
        
        # Check cache first
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if not force_refresh and url in self.content_cache:
            cached = self.content_cache[url]
            # Cache valid for 1 hour
            if time.time() - cached.timestamp < 3600:
                logger.debug(f"Cache hit: {url}")
                return cached
        
        # Validate URL
        is_safe, reason = self._is_url_safe(url)
        if not is_safe:
            logger.warning(f"Unsafe URL blocked: {reason}")
            return None
        
        # Check rate limits
        if not self._can_make_request():
            logger.warning("Rate limit reached")
            return None
        
        try:
            # Fetch
            headers = {
                "User-Agent": "ZARA-AI/1.0 (Autonomous Knowledge System)",
                "Accept": "text/html,application/xhtml+xml"
            }
            
            response = self._requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Update rate tracking
            self.last_request_time = time.time()
            self.requests_this_hour += 1
            
            # Parse content
            content = self._extract_content(response.text, url)
            
            if content:
                self.content_cache[url] = content
                self._save_cache()
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _extract_content(self, html: str, url: str) -> Optional[WebContent]:
        """Extract meaningful content from HTML."""
        soup = self._bs4(html, 'html.parser')
        
        # Get title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Remove script, style, nav, footer
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Try to find main content
        content_text = ""
        
        # Priority: article > main > body
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', class_=re.compile(r'content|article|post', re.I)) or
            soup.body
        )
        
        if main_content:
            # Get all paragraphs
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'li'])
            content_parts = []
            
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 20:  # Skip very short fragments
                    content_parts.append(text)
            
            content_text = "\n\n".join(content_parts)
        
        if not content_text:
            return None
        
        # Detect content type
        content_type = self._detect_content_type(url, title, content_text)
        
        # Create result
        content = WebContent(
            url=url,
            title=title,
            content=content_text[:10000],  # Limit size
            content_type=content_type,
            timestamp=time.time(),
            word_count=len(content_text.split())
        )
        
        # Generate summary
        content.summary = self._summarize(content_text)
        content.key_points = self._extract_key_points(content_text)
        
        return content

    def _detect_content_type(self, url: str, title: str, content: str) -> ContentType:
        """Detect the type of content."""
        url_lower = url.lower()
        
        if "docs." in url_lower or "/documentation" in url_lower:
            return ContentType.DOCUMENTATION
        if "wikipedia" in url_lower or "wiki" in url_lower:
            return ContentType.WIKI
        if "news" in url_lower or "article" in url_lower:
            return ContentType.NEWS
        if "github.com" in url_lower or "/code" in url_lower:
            return ContentType.CODE
        if any(s in url_lower for s in ["twitter", "reddit", "facebook"]):
            return ContentType.SOCIAL
        
        return ContentType.ARTICLE

    def _summarize(self, content: str, max_sentences: int = 3) -> str:
        """Generate a simple summary."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if not sentences:
            return ""
        
        # Take first few sentences as summary
        return ". ".join(sentences[:max_sentences]) + "."

    def _extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extract key points from content."""
        points = []
        
        # Look for bullet points (lines starting with - or *)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')) and len(line) > 20:
                points.append(line.lstrip('-*• ').strip())
        
        # If no bullet points, use first sentences
        if not points:
            sentences = re.split(r'[.!?]+', content)
            for s in sentences:
                s = s.strip()
                if len(s) > 30 and len(s) < 200:
                    points.append(s)
                    if len(points) >= max_points:
                        break
        
        return points[:max_points]

    # ═══════════════════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════════════════
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search the web for information.
        
        Note: This uses DuckDuckGo instant answers API which is free.
        For full search, you'd need a search API key.
        """
        if not self._load_libraries():
            return []
        
        if not self._can_make_request():
            return []
        
        try:
            # DuckDuckGo instant answer API (free, no key needed)
            api_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = self._requests.get(api_url, params=params, timeout=10)
            self.last_request_time = time.time()
            self.requests_this_hour += 1
            
            data = response.json()
            
            results = []
            
            # Abstract (main answer)
            if data.get("Abstract"):
                results.append(SearchResult(
                    title=data.get("Heading", "Answer"),
                    url=data.get("AbstractURL", ""),
                    snippet=data["Abstract"][:300],
                    source="DuckDuckGo",
                    rank=1
                ))
            
            # Related topics
            for i, topic in enumerate(data.get("RelatedTopics", [])[:num_results - 1]):
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(SearchResult(
                        title=topic.get("Text", "")[:50],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", "")[:200],
                        source="DuckDuckGo",
                        rank=i + 2
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════
    # KNOWLEDGE INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    
    def learn_from_url(self, url: str, topic: str = None) -> bool:
        """
        Fetch URL and add knowledge to the system.
        
        Args:
            url: URL to learn from
            topic: Optional topic to associate with
        
        Returns:
            True if successfully learned
        """
        content = self.fetch_url(url)
        
        if not content:
            return False
        
        # Store in knowledge system
        if self.knowledge_system:
            try:
                self.knowledge_system.learn_from_text(
                    text=content.content,
                    source=url,
                    topics=[topic] if topic else []
                )
                logger.info(f"Learned from: {content.title}")
                return True
            except:
                pass
        
        return False

    def research_topic(self, topic: str, depth: int = 2) -> Dict:
        """
        Research a topic by searching and fetching content.
        
        Args:
            topic: Topic to research
            depth: Number of sources to fetch
        
        Returns:
            Research summary
        """
        results = self.search(topic, num_results=depth + 2)
        
        if not results:
            return {"topic": topic, "found": False, "summary": "No results found"}
        
        contents = []
        for result in results[:depth]:
            if result.url:
                content = self.fetch_url(result.url)
                if content:
                    contents.append(content)
        
        # Combine findings
        all_points = []
        sources = []
        
        for content in contents:
            all_points.extend(content.key_points)
            sources.append({"title": content.title, "url": content.url})
        
        # Store in knowledge system
        if self.knowledge_system and contents:
            combined_text = "\n\n".join(c.content[:1000] for c in contents)
            self.knowledge_system.learn_from_text(
                text=combined_text,
                source=f"Web research: {topic}",
                topics=[topic]
            )
        
        return {
            "topic": topic,
            "found": len(contents) > 0,
            "sources_checked": len(results),
            "sources_fetched": len(contents),
            "key_findings": all_points[:10],
            "sources": sources,
            "summary": contents[0].summary if contents else ""
        }

    def answer_question(self, question: str) -> Optional[str]:
        """
        Try to answer a question using web search.
        
        Args:
            question: Question to answer
        
        Returns:
            Answer string or None
        """
        results = self.search(question, num_results=3)
        
        if not results:
            return None
        
        # Return first relevant snippet
        for result in results:
            if result.snippet:
                return f"{result.snippet}\n\n(Source: {result.url})"
        
        return None

    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "available": self._available,
            "cache_size": len(self.content_cache),
            "requests_this_hour": self.requests_this_hour,
            "max_requests": self.max_requests_per_hour,
            "last_request": time.time() - self.last_request_time if self.last_request_time else None
        }


# Singleton
_web_instance = None

def get_web() -> WebKnowledgeSystem:
    """Get the global web knowledge system."""
    global _web_instance
    if _web_instance is None:
        _web_instance = WebKnowledgeSystem()
    return _web_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    web = WebKnowledgeSystem()
    
    # Test search
    results = web.search("Python programming")
    print("Search results:")
    for r in results:
        print(f"  - {r.title}: {r.snippet[:50]}...")
    
    # Test URL fetch
    content = web.fetch_url("https://www.python.org/")
    if content:
        print(f"\nFetched: {content.title}")
        print(f"Words: {content.word_count}")
        print(f"Summary: {content.summary}")
