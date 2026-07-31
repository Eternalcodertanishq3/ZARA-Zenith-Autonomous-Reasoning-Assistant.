"""
ZARA Production Resilience Utilities v1.0
==========================================
Error handling, circuit breakers, and graceful degradation.

These utilities make ZARA production-ready by:
1. Preventing crashes from cascading
2. Auto-recovering from transient failures
3. Gracefully degrading when services fail
4. Logging all issues for debugging
"""

import logging
import time
import threading
import functools
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Dict, Set, TypeVar, Generic
from enum import Enum
from collections import deque

logger = logging.getLogger("ZARA_RESILIENCE")

T = TypeVar('T')


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE CALL DECORATOR
# ═══════════════════════════════════════════════════════════════════════════════

def safe_call(
    fallback: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    error_message: str = None
):
    """
    Decorator for graceful failure handling.
    
    Usage:
        @safe_call(fallback="Error occurred")
        def risky_operation():
            ...
    
    Args:
        fallback: Value to return on failure
        log_error: Whether to log the exception
        reraise: Whether to re-raise after logging
        error_message: Custom error message
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    msg = error_message or f"Error in {func.__name__}"
                    logger.error(f"{msg}: {type(e).__name__}: {e}")
                
                if reraise:
                    raise
                
                # Return fallback (call if callable)
                if callable(fallback):
                    return fallback()
                return fallback
        
        return wrapper
    return decorator


def safe_call_async(
    fallback: Any = None,
    log_error: bool = True,
    error_message: str = None
):
    """Async version of safe_call decorator."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    msg = error_message or f"Error in {func.__name__}"
                    logger.error(f"{msg}: {type(e).__name__}: {e}")
                
                if callable(fallback):
                    return fallback()
                return fallback
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════════

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject calls
    HALF_OPEN = "half_open" # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Prevents cascade failures by stopping calls to failing services.
    
    Pattern:
    1. CLOSED: Normal operation, track failures
    2. OPEN: Too many failures, reject all calls immediately  
    3. HALF_OPEN: After timeout, try one call to test recovery
    
    Usage:
        breaker = CircuitBreaker("llm_service")
        
        @breaker
        def call_llm():
            ...
    """
    name: str
    failure_threshold: int = 5      # Failures before opening
    recovery_timeout: float = 30.0  # Seconds before testing recovery
    success_threshold: int = 2      # Successes to close from half-open
    
    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _success_count: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    
    @property
    def state(self) -> CircuitState:
        """Get current state, potentially transitioning from OPEN to HALF_OPEN."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"🔄 Circuit '{self.name}' entering HALF_OPEN state")
            
            return self._state
    
    def is_available(self) -> bool:
        """Check if calls are allowed."""
        return self.state != CircuitState.OPEN
    
    def record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"✅ Circuit '{self.name}' CLOSED (recovered)")
            
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, back to OPEN
                self._state = CircuitState.OPEN
                logger.warning(f"❌ Circuit '{self.name}' back to OPEN (recovery failed)")
            
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"🔴 Circuit '{self.name}' OPENED after {self._failure_count} failures")
    
    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.is_available():
                logger.warning(f"Circuit '{self.name}' is OPEN, rejecting call to {func.__name__}")
                raise CircuitOpenError(f"Circuit '{self.name}' is open")
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            logger.info(f"🔄 Circuit '{self.name}' manually reset")


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# RETRY WITH BACKOFF
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RetryWithBackoff:
    """
    Automatic retry with exponential backoff for transient failures.
    
    Usage:
        @RetryWithBackoff(max_retries=3, base_delay=1.0)
        def flaky_operation():
            ...
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except self.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        logger.error(f"All {self.max_retries} retries failed for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if self.jitter:
                        import random
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s (error: {e})"
                    )
                    time.sleep(delay)
            
            raise last_exception  # Should not reach here
        
        return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# GRACEFUL DEGRADATION
# ═══════════════════════════════════════════════════════════════════════════════

class GracefulDegrader:
    """
    Tracks degraded services and provides fallback behavior.
    
    When a service fails, it's marked as degraded and ZARA continues
    with reduced capabilities rather than crashing.
    
    Usage:
        degrader = GracefulDegrader()
        
        try:
            result = vision_system.process()
        except Exception as e:
            degrader.mark_degraded("vision", str(e))
            result = degrader.get_fallback("vision")
        
        if degrader.is_degraded("vision"):
            # Skip vision-dependent features
            pass
    """
    
    def __init__(self):
        self._degraded: Dict[str, str] = {}  # service -> error message
        self._fallbacks: Dict[str, Any] = {}
        self._recovery_callbacks: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._degradation_times: Dict[str, float] = {}
        
        # Register default fallbacks
        self._register_default_fallbacks()
    
    def _register_default_fallbacks(self):
        """Register default fallback values for known services."""
        self._fallbacks = {
            "vision": {"description": "Vision unavailable", "objects": []},
            "audio": {"transcription": "", "emotion": "neutral"},
            "llm": "I'm having trouble thinking right now. Please try again.",
            "memory": {"results": [], "error": "Memory unavailable"},
            "tts": None,  # Silent fallback
        }
    
    def mark_degraded(self, service: str, error: str = "Unknown error"):
        """Mark a service as degraded."""
        with self._lock:
            was_degraded = service in self._degraded
            self._degraded[service] = error
            self._degradation_times[service] = time.time()
            
            if not was_degraded:
                logger.warning(f"⚠️ Service '{service}' is now DEGRADED: {error}")
    
    def mark_recovered(self, service: str):
        """Mark a service as recovered."""
        with self._lock:
            if service in self._degraded:
                del self._degraded[service]
                downtime = time.time() - self._degradation_times.get(service, time.time())
                logger.info(f"✅ Service '{service}' RECOVERED (downtime: {downtime:.1f}s)")
                
                # Call recovery callback if registered
                if service in self._recovery_callbacks:
                    try:
                        self._recovery_callbacks[service]()
                    except Exception as e:
                        logger.error(f"Recovery callback failed for {service}: {e}")
    
    def is_degraded(self, service: str) -> bool:
        """Check if a service is degraded."""
        with self._lock:
            return service in self._degraded
    
    def get_degraded_services(self) -> Dict[str, str]:
        """Get all degraded services and their errors."""
        with self._lock:
            return self._degraded.copy()
    
    def get_fallback(self, service: str) -> Any:
        """Get fallback value for a degraded service."""
        return self._fallbacks.get(service)
    
    def set_fallback(self, service: str, fallback: Any):
        """Set custom fallback for a service."""
        self._fallbacks[service] = fallback
    
    def on_recovery(self, service: str, callback: Callable):
        """Register callback for when service recovers."""
        self._recovery_callbacks[service] = callback
    
    def get_health_status(self) -> Dict:
        """Get overall health status."""
        with self._lock:
            degraded_count = len(self._degraded)
            return {
                "healthy": degraded_count == 0,
                "degraded_count": degraded_count,
                "degraded_services": list(self._degraded.keys()),
                "status": "HEALTHY" if degraded_count == 0 else f"DEGRADED ({degraded_count} services)"
            }
    
    def wrap_service(self, service_name: str, fallback: Any = None):
        """
        Decorator to wrap a service call with degradation handling.
        
        Usage:
            @degrader.wrap_service("vision")
            def get_vision():
                return vision_system.capture()
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.is_degraded(service_name):
                    return fallback or self.get_fallback(service_name)
                
                try:
                    result = func(*args, **kwargs)
                    # If was previously degraded, mark recovered
                    if service_name in self._degraded:
                        self.mark_recovered(service_name)
                    return result
                except Exception as e:
                    self.mark_degraded(service_name, str(e))
                    return fallback or self.get_fallback(service_name)
            
            return wrapper
        return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# TIMEOUT WRAPPER
# ═══════════════════════════════════════════════════════════════════════════════

class TimeoutError(Exception):
    """Raised when operation times out."""
    pass


def with_timeout(seconds: float, fallback: Any = None):
    """
    Decorator to add timeout to a function.
    
    Note: Only works on non-blocking operations due to GIL limitations.
    For true timeout behavior, use multiprocessing or async.
    
    Usage:
        @with_timeout(5.0, fallback="Timeout!")
        def slow_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            completed = [False]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                    completed[0] = True
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)
            
            if not completed[0]:
                if exception[0]:
                    raise exception[0]
                logger.warning(f"Timeout ({seconds}s) in {func.__name__}")
                if fallback is not None:
                    return fallback
                raise TimeoutError(f"{func.__name__} timed out after {seconds}s")
            
            return result[0]
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Token bucket rate limiter.
    
    Usage:
        limiter = RateLimiter(rate=10, period=1.0)  # 10 calls per second
        
        @limiter
        def api_call():
            ...
    """
    
    def __init__(self, rate: int, period: float = 1.0):
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.period))
        self.last_update = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_and_acquire(self, tokens: int = 1):
        """Wait until tokens are available, then acquire."""
        while not self.acquire(tokens):
            time.sleep(0.01)
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.wait_and_acquire()
            return func(*args, **kwargs)
        return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HealthCheck:
    """
    Health check for a service.
    
    Usage:
        check = HealthCheck("database", lambda: db.ping())
        if check.is_healthy():
            ...
    """
    name: str
    check_fn: Callable[[], bool]
    timeout: float = 5.0
    last_check: float = field(default=0.0, repr=False)
    last_status: bool = field(default=True, repr=False)
    check_interval: float = 30.0
    
    def is_healthy(self, force: bool = False) -> bool:
        """Check if service is healthy."""
        now = time.time()
        
        # Use cached result if recent
        if not force and (now - self.last_check) < self.check_interval:
            return self.last_status
        
        self.last_check = now
        
        try:
            result = [False]
            
            def target():
                result[0] = self.check_fn()
            
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=self.timeout)
            
            self.last_status = result[0]
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self.last_status = False
        
        return self.last_status


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════════════════════════

# Global degrader instance
_degrader: Optional[GracefulDegrader] = None

def get_degrader() -> GracefulDegrader:
    """Get global graceful degrader instance."""
    global _degrader
    if _degrader is None:
        _degrader = GracefulDegrader()
    return _degrader


# Pre-configured circuit breakers for common services
llm_circuit = CircuitBreaker("llm", failure_threshold=3, recovery_timeout=60.0)
tts_circuit = CircuitBreaker("tts", failure_threshold=5, recovery_timeout=30.0)
vision_circuit = CircuitBreaker("vision", failure_threshold=5, recovery_timeout=15.0)
memory_circuit = CircuitBreaker("memory", failure_threshold=3, recovery_timeout=45.0)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    
    print("\n🛡️ ZARA Production Resilience Utilities v1.0\n")
    print("=" * 60)
    
    # Test safe_call
    print("\n📌 Testing @safe_call decorator...")
    
    @safe_call(fallback="Safe fallback!")
    def risky_function():
        raise ValueError("Something went wrong")
    
    result = risky_function()
    print(f"  Result: {result}")
    assert result == "Safe fallback!", "safe_call failed"
    print("  ✅ safe_call working")
    
    # Test circuit breaker
    print("\n📌 Testing CircuitBreaker...")
    
    test_circuit = CircuitBreaker("test", failure_threshold=2, recovery_timeout=1.0)
    
    @test_circuit
    def failing_function():
        raise RuntimeError("Always fails")
    
    # Trigger failures to open circuit
    for i in range(3):
        try:
            failing_function()
        except (RuntimeError, CircuitOpenError):
            pass
    
    print(f"  Circuit state: {test_circuit.state.value}")
    assert test_circuit.state == CircuitState.OPEN, "Circuit should be open"
    print("  ✅ CircuitBreaker working")
    
    # Test graceful degrader
    print("\n📌 Testing GracefulDegrader...")
    
    degrader = GracefulDegrader()
    degrader.mark_degraded("test_service", "Test error")
    
    assert degrader.is_degraded("test_service"), "Should be degraded"
    print(f"  Health status: {degrader.get_health_status()}")
    
    degrader.mark_recovered("test_service")
    assert not degrader.is_degraded("test_service"), "Should be recovered"
    print("  ✅ GracefulDegrader working")
    
    # Test retry
    print("\n📌 Testing RetryWithBackoff...")
    
    call_count = [0]
    
    @RetryWithBackoff(max_retries=2, base_delay=0.1)
    def flaky_function():
        call_count[0] += 1
        if call_count[0] < 3:
            raise RuntimeError("Temporary failure")
        return "Success!"
    
    result = flaky_function()
    print(f"  Result after {call_count[0]} attempts: {result}")
    assert result == "Success!", "Retry failed"
    print("  ✅ RetryWithBackoff working")
    
    # Test rate limiter
    print("\n📌 Testing RateLimiter...")
    
    limiter = RateLimiter(rate=5, period=1.0)
    
    @limiter
    def limited_function():
        return "OK"
    
    start = time.time()
    for _ in range(3):
        limited_function()
    elapsed = time.time() - start
    print(f"  3 calls in {elapsed:.3f}s")
    print("  ✅ RateLimiter working")
    
    print("\n" + "=" * 60)
    print("✅ All resilience utilities ready!\n")
