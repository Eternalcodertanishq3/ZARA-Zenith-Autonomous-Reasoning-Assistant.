"""
ZARA Latency Buffer - Enhanced Conversation Flow
"""
import logging
import threading
import queue
import time
import random
from typing import Optional, Callable, Generator, List
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger("ZARA_LATENCY")


@dataclass
class LatencyMetrics:
    """Latency statistics."""
    avg_response_ms: float
    min_response_ms: float
    max_response_ms: float
    p95_response_ms: float
    total_requests: int


class LatencyBuffer:
    """
    Masks AI processing latency with natural conversation fillers.
    Enhanced with:
    - Mood-aware filler selection
    - Progressive filler escalation
    - Latency analytics
    - Interruptible fillers
    - Context-aware responses
    """
    
    def __init__(self, speak_callback: Optional[Callable] = None):
        self.speak_callback = speak_callback
        self.is_thinking = False
        self.thinking_start = 0
        self.lock = threading.Lock()
        self.interrupt_event = threading.Event()
        
        # Current context
        self.current_mood = "neutral"
        self.user_waiting = False
        
        # Filler categories
        self.fillers = {
            "quick": [
                "Hmm...",
                "So...",
                "Well...",
                "Umm...",
            ],
            "thinking": [
                "Let me think...",
                "Ek second...",
                "Ruko...",
                "Acha...",
                "Dekho...",
            ],
            "processing": [
                "Give me a moment...",
                "Processing that...",
                "Interesting question...",
                "Sochne do mujhe...",
                "Let me figure this out...",
            ],
            "apologetic": [
                "Sorry, this is taking a bit...",
                "Almost there...",
                "Thanks for your patience...",
                "Bas thoda sa aur...",
            ]
        }
        
        # Mood-specific fillers
        self.mood_fillers = {
            "happy": ["Ooh!", "Hehe...", "Yay, okay..."],
            "focused": ["Analyzing...", "Computing...", "Checking..."],
            "tired": ["*yawns* hmm...", "Ek minute...", "Slowly thinking..."],
            "playful": ["Hmm hmm!", "Soo...", "Guess what..."],
        }
        
        # Typing indicators
        self.typing_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.thinking_dots = [".", "..", "...", "....", "..."]
        
        # Configuration
        self.quick_threshold = 0.5      # seconds
        self.thinking_threshold = 1.5   # seconds
        self.processing_threshold = 3.0 # seconds
        self.apologetic_threshold = 5.0 # seconds
        self.max_fillers = 4
        
        # Latency tracking
        self.latency_history = deque(maxlen=1000)
        self.filler_count = 0
        
        logger.info("Latency Buffer initialized.")
    
    def set_mood(self, mood: str):
        """Set current mood for filler selection."""
        self.current_mood = mood
    
    def start_thinking(self):
        """Signal that ZARA is processing."""
        with self.lock:
            self.is_thinking = True
            self.thinking_start = time.time()
            self.interrupt_event.clear()
            self.filler_count = 0
        
        thread = threading.Thread(target=self._filler_loop, daemon=True)
        thread.start()
    
    def stop_thinking(self):
        """Signal that ZARA finished processing."""
        with self.lock:
            elapsed = time.time() - self.thinking_start
            self.is_thinking = False
            self.interrupt_event.set()
            
            if elapsed > 0:
                self.latency_history.append(elapsed * 1000)
    
    def interrupt(self):
        """Interrupt current filler playback."""
        self.interrupt_event.set()
    
    def _filler_loop(self):
        """Background loop to insert contextual fillers."""
        fillers_used = 0
        last_filler_time = 0
        
        while self.is_thinking and fillers_used < self.max_fillers:
            if self.interrupt_event.is_set():
                break
            
            elapsed = time.time() - self.thinking_start
            
            # Progressive filler selection
            if elapsed > self.apologetic_threshold and fillers_used < 3:
                category = "apologetic"
            elif elapsed > self.processing_threshold and fillers_used < 2:
                category = "processing"
            elif elapsed > self.thinking_threshold and fillers_used < 1:
                category = "thinking"
            elif elapsed > self.quick_threshold and fillers_used == 0:
                category = "quick"
            else:
                time.sleep(0.1)
                continue
            
            # Ensure minimum gap between fillers
            if time.time() - last_filler_time < 1.5:
                time.sleep(0.1)
                continue
            
            filler = self._select_filler(category)
            if filler:
                self._emit_filler(filler)
                fillers_used += 1
                last_filler_time = time.time()
            
            time.sleep(0.5)
    
    def _select_filler(self, category: str) -> str:
        """Select appropriate filler based on category and mood."""
        # Check mood-specific fillers first
        if self.current_mood in self.mood_fillers and random.random() < 0.3:
            return random.choice(self.mood_fillers[self.current_mood])
        
        # Fall back to category
        if category in self.fillers:
            return random.choice(self.fillers[category])
        
        return random.choice(self.fillers["quick"])
    
    def _emit_filler(self, filler: str):
        """Output filler through callback."""
        self.filler_count += 1
        
        if self.speak_callback:
            try:
                self.speak_callback(filler, is_filler=True)
            except Exception as e:
                logger.error(f"Filler emit error: {e}")
        else:
            logger.info(f"[Filler] {filler}")
    
    def get_typing_indicator(self) -> Generator[str, None, None]:
        """Generator for animated typing indicator."""
        idx = 0
        while self.is_thinking:
            yield self.typing_frames[idx % len(self.typing_frames)]
            idx += 1
            time.sleep(0.08)
    
    def get_thinking_dots(self) -> Generator[str, None, None]:
        """Generator for thinking dots animation."""
        idx = 0
        while self.is_thinking:
            yield self.thinking_dots[idx % len(self.thinking_dots)]
            idx += 1
            time.sleep(0.3)
    
    def wrap_response(self, response_generator: Generator) -> Generator:
        """Wrap a response generator to handle latency transparently."""
        self.start_thinking()
        first_token = True
        
        try:
            for token in response_generator:
                if first_token:
                    self.stop_thinking()
                    first_token = False
                yield token
        finally:
            self.stop_thinking()
    
    async def wrap_async_response(self, async_generator):
        """Wrap an async response generator."""
        self.start_thinking()
        first_token = True
        
        try:
            async for token in async_generator:
                if first_token:
                    self.stop_thinking()
                    first_token = False
                yield token
        finally:
            self.stop_thinking()
    
    def measure_latency(self, func: Callable) -> tuple:
        """Measure and report latency of a function."""
        start = time.perf_counter()
        result = func()
        latency_ms = (time.perf_counter() - start) * 1000
        
        self.latency_history.append(latency_ms)
        
        if latency_ms > 2000:
            logger.warning(f"High latency: {latency_ms:.0f}ms")
        
        return result, latency_ms
    
    def get_metrics(self) -> LatencyMetrics:
        """Get latency statistics."""
        if not self.latency_history:
            return LatencyMetrics(0, 0, 0, 0, 0)
        
        history = list(self.latency_history)
        sorted_history = sorted(history)
        
        return LatencyMetrics(
            avg_response_ms=sum(history) / len(history),
            min_response_ms=min(history),
            max_response_ms=max(history),
            p95_response_ms=sorted_history[int(len(sorted_history) * 0.95)] if len(sorted_history) > 20 else max(history),
            total_requests=len(history)
        )
    
    def add_custom_fillers(self, category: str, fillers: List[str]):
        """Add custom fillers for a category."""
        if category in self.fillers:
            self.fillers[category].extend(fillers)
        else:
            self.fillers[category] = fillers


class StreamingResponseBuffer:
    """
    Buffer for streaming responses with chunked output.
    Smooths token-by-token output into natural speech chunks.
    """
    
    def __init__(self, min_chunk_size: int = 10, max_wait_ms: int = 200):
        self.buffer = ""
        self.min_chunk_size = min_chunk_size
        self.max_wait_ms = max_wait_ms
        self.last_emit_time = time.time()
        self.output_queue = queue.Queue()
    
    def add_token(self, token: str) -> Optional[str]:
        """Add a token, return a chunk if ready."""
        self.buffer += token
        
        # Check if we should emit
        time_since_emit = (time.time() - self.last_emit_time) * 1000
        
        # Emit on sentence boundaries
        if any(self.buffer.rstrip().endswith(p) for p in ['.', '!', '?', '।']):
            return self._emit()
        
        # Emit on clause boundaries if buffer is getting long
        if len(self.buffer) > self.min_chunk_size * 2:
            if any(c in self.buffer for c in [',', ';', ':']):
                return self._emit()
        
        # Emit if waiting too long
        if time_since_emit > self.max_wait_ms and len(self.buffer) >= self.min_chunk_size:
            return self._emit()
        
        return None
    
    def _emit(self) -> str:
        """Emit current buffer and reset."""
        chunk = self.buffer.strip()
        self.buffer = ""
        self.last_emit_time = time.time()
        return chunk
    
    def flush(self) -> Optional[str]:
        """Flush remaining buffer."""
        if self.buffer.strip():
            return self._emit()
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    buffer = LatencyBuffer()
    buffer.set_mood("happy")
    
    # Simulate thinking
    buffer.start_thinking()
    time.sleep(2)
    buffer.stop_thinking()
    
    print("Metrics:", buffer.get_metrics())
