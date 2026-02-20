"""
ZARA Context Compressor - Enhanced Memory Management
"""
import logging
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("ZARA_COMPRESS")


@dataclass
class CompressionStats:
    """Statistics about compression operation."""
    original_count: int
    compressed_count: int
    compression_ratio: float
    time_ms: float


@dataclass
class CompressedMemory:
    """A compressed memory entry."""
    content: str
    timestamp: str
    emotional_weight: float
    type: str = "compressed"
    source: str = "compression"
    original_count: int = 1
    original_types: List[str] = field(default_factory=list)
    hash: str = ""


class ContextCompressor:
    """
    Memory compression system that summarizes and compresses
    long-term memories while preserving emotional essence.
    
    Enhanced with:
    - LLM-based summarization (when available)
    - Multi-level compression
    - Semantic deduplication
    - Importance decay over time
    - Emotional preservation
    """
    
    def __init__(self):
        self.compression_ratio = 0.3
        self.importance_threshold = 0.4
        self.llm = None
        
        # Importance weights
        self.importance_modifiers = {
            "emotional": 0.3,
            "question": 0.2,
            "code": 0.3,
            "long_form": 0.2,
            "command": 0.2,
            "personal": 0.25
        }

    def set_llm(self, llm):
        """Set LLM for intelligent summarization."""
        self.llm = llm
        logger.info("LLM-based summarization enabled.")

    def compress_conversation(self, messages: List[Dict]) -> Tuple[List[Dict], CompressionStats]:
        """
        Compress conversation messages intelligently.
        """
        start_time = time.time()
        original_count = len(messages)
        
        if len(messages) <= 10:
            return messages, CompressionStats(
                original_count=original_count,
                compressed_count=len(messages),
                compression_ratio=1.0,
                time_ms=(time.time() - start_time) * 1000
            )
        
        compressed = []
        buffer = []
        
        for i, msg in enumerate(messages):
            importance = self._calculate_importance(msg, i, len(messages))
            
            if importance > self.importance_threshold:
                # Flush buffer
                if buffer:
                    summary = self._summarize_buffer(buffer)
                    compressed.append({
                        "role": "system",
                        "content": f"[Summary of {len(buffer)} messages: {summary}]",
                        "compressed": True
                    })
                    buffer = []
                compressed.append(msg)
            else:
                buffer.append(msg)
        
        # Final buffer
        if buffer:
            summary = self._summarize_buffer(buffer)
            compressed.append({
                "role": "system",
                "content": f"[Summary: {summary}]",
                "compressed": True
            })
        
        stats = CompressionStats(
            original_count=original_count,
            compressed_count=len(compressed),
            compression_ratio=len(compressed) / original_count if original_count > 0 else 1.0,
            time_ms=(time.time() - start_time) * 1000
        )
        
        logger.info(f"Compressed {original_count} → {len(compressed)} messages ({stats.compression_ratio:.1%})")
        return compressed, stats

    def _calculate_importance(self, message: Dict, position: int, total: int) -> float:
        """
        Calculate importance score with position-based decay.
        Recent messages are weighted higher.
        """
        content = message.get("content", "")
        score = 0.0
        
        # Base score from content analysis
        if len(content) > 100:
            score += self.importance_modifiers["long_form"]
        
        content_lower = content.lower()
        
        # Emotional content
        emotional_words = [
            "love", "hate", "sad", "happy", "angry", "excited",
            "scared", "proud", "sorry", "thank", "miss", "wish",
            "pyaar", "gussa", "khush", "dukhi"  # Hindi
        ]
        if any(word in content_lower for word in emotional_words):
            score += self.importance_modifiers["emotional"]
        
        # Questions
        if "?" in content:
            score += self.importance_modifiers["question"]
        
        # Commands/requests
        request_words = ["can you", "please", "help", "need", "want", "could you"]
        if any(word in content_lower for word in request_words):
            score += self.importance_modifiers["command"]
        
        # Code blocks
        if "```" in content or "def " in content or "import " in content:
            score += self.importance_modifiers["code"]
        
        # Personal information
        personal_words = ["my name", "i am", "i'm", "birthday", "age", "work", "job"]
        if any(word in content_lower for word in personal_words):
            score += self.importance_modifiers["personal"]
        
        # Position-based boost (recent messages more important)
        recency_boost = (position / total) * 0.3 if total > 0 else 0
        score += recency_boost
        
        return min(score, 1.0)

    def _summarize_buffer(self, messages: List[Dict]) -> str:
        """Create a summary of buffered messages."""
        # Try LLM-based summarization
        if self.llm:
            return self._llm_summarize(messages)
        
        # Fall back to extractive summarization
        return self._extractive_summarize(messages)

    def _llm_summarize(self, messages: List[Dict]) -> str:
        """Use LLM for intelligent summarization."""
        try:
            combined = "\n".join([
                f"{m.get('role', 'unknown')}: {m.get('content', '')[:100]}"
                for m in messages[:10]
            ])
            
            prompt = f"Summarize this conversation briefly in one sentence:\n{combined}"
            
            # This would call the actual LLM
            # summary = self.llm.generate(prompt, max_tokens=50)
            # return summary
            
            # Fallback for now
            return self._extractive_summarize(messages)
        except Exception as e:
            logger.debug(f"LLM summarization failed: {e}")
            return self._extractive_summarize(messages)

    def _extractive_summarize(self, messages: List[Dict]) -> str:
        """Simple extractive summarization."""
        topics = set()
        verbs = set()
        
        for msg in messages:
            content = msg.get("content", "").lower()
            words = content.split()
            
            for word in words:
                word = word.strip(".,!?;:")
                if len(word) > 5 and word.isalpha():
                    topics.add(word)
        
        if topics:
            return f"Discussed: {', '.join(list(topics)[:5])}"
        return "General conversation"

    def compress_memory_batch(self, memories: List[Dict], 
                             age_days: int = 30) -> Tuple[List[Dict], CompressionStats]:
        """
        Compress memories older than specified days.
        Groups by date and creates daily summaries.
        """
        start_time = time.time()
        original_count = len(memories)
        
        grouped = defaultdict(list)
        fresh = []
        threshold_date = datetime.now() - timedelta(days=age_days)
        
        for mem in memories:
            try:
                ts_str = mem.get("timestamp", "")
                if isinstance(ts_str, (int, float)):
                    ts = datetime.fromtimestamp(ts_str)
                else:
                    ts = datetime.fromisoformat(str(ts_str))
                
                if ts < threshold_date:
                    date_key = ts.strftime("%Y-%m-%d")
                    grouped[date_key].append(mem)
                else:
                    fresh.append(mem)
            except Exception as e:
                logger.debug(f"Could not parse memory timestamp: {e}")
                fresh.append(mem)
        
        # Compress grouped memories
        compressed_old = []
        for date, mems in sorted(grouped.items()):
            if len(mems) > 1:
                summary = self._create_daily_summary(date, mems)
                compressed_old.append(summary)
            else:
                compressed_old.append(mems[0])
        
        # Deduplicate fresh memories
        fresh = self._deduplicate(fresh)
        
        result = compressed_old + fresh
        
        stats = CompressionStats(
            original_count=original_count,
            compressed_count=len(result),
            compression_ratio=len(result) / original_count if original_count > 0 else 1.0,
            time_ms=(time.time() - start_time) * 1000
        )
        
        logger.info(f"Compressed {original_count} memories → {len(result)}")
        return result, stats

    def _create_daily_summary(self, date: str, memories: List[Dict]) -> Dict:
        """Create a single memory summarizing a day."""
        types = set(m.get("type", "unknown") for m in memories)
        avg_weight = sum(m.get("emotional_weight", 0.5) for m in memories) / len(memories)
        
        # Get key topics
        all_content = " ".join(m.get("content", "")[:100] for m in memories)
        topics = self._extract_key_topics(all_content)
        
        return {
            "content": f"[{date}] {len(memories)} memories: {topics}",
            "type": "compressed",
            "timestamp": date,
            "emotional_weight": avg_weight,
            "source": "compression",
            "original_count": len(memories),
            "original_types": list(types)
        }

    def _extract_key_topics(self, text: str, max_topics: int = 5) -> str:
        """Extract key topics from text."""
        words = text.lower().split()
        word_freq = defaultdict(int)
        
        stopwords = {
            "the", "a", "an", "is", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must",
            "and", "or", "but", "if", "then", "so", "that", "this",
            "what", "how", "when", "where", "who", "which", "why",
            "for", "with", "about", "from", "into", "of", "to", "in", "on"
        }
        
        for word in words:
            word = word.strip(".,!?;:\"'()[]")
            if len(word) > 3 and word.isalpha() and word not in stopwords:
                word_freq[word] += 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_topics]
        
        if top_words:
            return ", ".join(w[0] for w in top_words)
        return "various topics"

    def _deduplicate(self, memories: List[Dict]) -> List[Dict]:
        """Remove semantically similar memories."""
        seen_hashes = set()
        unique = []
        
        for mem in memories:
            content = mem.get("content", "")
            # Create a fuzzy hash based on key words
            words = sorted(set(content.lower().split()[:20]))
            content_hash = hashlib.md5(" ".join(words).encode()).hexdigest()[:8]
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(mem)
        
        if len(unique) < len(memories):
            logger.info(f"Deduplicated {len(memories)} → {len(unique)} memories")
        
        return unique

    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count for messages."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        # Rough estimate: 4 chars per token
        return total_chars // 4


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    compressor = ContextCompressor()
    
    # Test conversation compression
    messages = [
        {"role": "user", "content": f"Message {i}"} for i in range(25)
    ]
    messages[10]["content"] = "I love how helpful you are! This is amazing!"
    messages[15]["content"] = "Can you help me with Python code?"
    
    compressed, stats = compressor.compress_conversation(messages)
    print(f"Compression: {stats.original_count} → {stats.compressed_count}")
    print(f"Ratio: {stats.compression_ratio:.1%}")
