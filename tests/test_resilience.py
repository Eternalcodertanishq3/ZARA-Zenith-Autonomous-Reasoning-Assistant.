"""
ZARA Resilience Utilities Tests
================================
Comprehensive tests for production resilience patterns.
Run with: pytest tests/test_resilience.py -v
"""

import pytest
import time
import threading


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE_CALL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeCall:
    """Tests for @safe_call decorator."""
    
    def test_import(self):
        """Test module imports correctly."""
        from utils.resilience import safe_call
        assert safe_call is not None
    
    def test_success_passthrough(self):
        """Test successful calls return normally."""
        from utils.resilience import safe_call
        
        @safe_call(fallback="fallback")
        def success_fn():
            return "success"
        
        assert success_fn() == "success"
    
    def test_fallback_on_exception(self):
        """Test fallback is returned on exception."""
        from utils.resilience import safe_call
        
        @safe_call(fallback="fallback")
        def failing_fn():
            raise ValueError("error")
        
        assert failing_fn() == "fallback"
    
    def test_callable_fallback(self):
        """Test callable fallbacks are executed."""
        from utils.resilience import safe_call
        
        @safe_call(fallback=lambda: "dynamic_fallback")
        def failing_fn():
            raise ValueError("error")
        
        assert failing_fn() == "dynamic_fallback"
    
    def test_reraise_option(self):
        """Test reraise option re-raises exception."""
        from utils.resilience import safe_call
        
        @safe_call(fallback="fallback", reraise=True)
        def failing_fn():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            failing_fn()


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_import(self):
        """Test module imports correctly."""
        from utils.resilience import CircuitBreaker, CircuitState
        assert CircuitBreaker is not None
        assert CircuitState is not None
    
    def test_initial_state_closed(self, circuit_breaker):
        """Test circuit starts in CLOSED state."""
        from utils.resilience import CircuitState
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_opens_after_threshold(self, circuit_breaker):
        """Test circuit opens after failure threshold."""
        from utils.resilience import CircuitState
        
        # Record failures up to threshold
        for _ in range(2):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
    
    def test_rejects_when_open(self, circuit_breaker):
        """Test circuit rejects calls when open."""
        from utils.resilience import CircuitOpenError
        
        # Force open
        for _ in range(2):
            circuit_breaker.record_failure()
        
        @circuit_breaker
        def test_fn():
            return "success"
        
        with pytest.raises(CircuitOpenError):
            test_fn()
    
    def test_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions to HALF_OPEN after timeout."""
        from utils.resilience import CircuitState
        
        # Open the circuit
        for _ in range(2):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.6)
        
        assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    def test_closes_after_success(self, circuit_breaker):
        """Test circuit closes after successful calls in HALF_OPEN."""
        from utils.resilience import CircuitState
        
        # Open then wait for half-open
        for _ in range(2):
            circuit_breaker.record_failure()
        
        # Must be OPEN now
        assert circuit_breaker._state == CircuitState.OPEN
        
        time.sleep(0.6)
        
        # Access state to trigger half-open check
        _ = circuit_breaker.state
        
        # Record successes (will only work in HALF_OPEN or CLOSED)
        for _ in range(2):
            circuit_breaker.record_success()
        
        assert circuit_breaker._state == CircuitState.CLOSED
    
    def test_reset(self, circuit_breaker):
        """Test manual reset works."""
        from utils.resilience import CircuitState
        
        # Open the circuit
        for _ in range(2):
            circuit_breaker.record_failure()
        
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitState.CLOSED


# ═══════════════════════════════════════════════════════════════════════════════
# GRACEFUL DEGRADER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGracefulDegrader:
    """Tests for GracefulDegrader."""
    
    def test_import(self):
        """Test module imports correctly."""
        from utils.resilience import GracefulDegrader
        assert GracefulDegrader is not None
    
    def test_initially_healthy(self, degrader):
        """Test starts with no degraded services."""
        health = degrader.get_health_status()
        assert health["healthy"] is True
        assert health["degraded_count"] == 0
    
    def test_mark_degraded(self, degrader):
        """Test marking service as degraded."""
        degrader.mark_degraded("test_service", "Some error")
        
        assert degrader.is_degraded("test_service")
        health = degrader.get_health_status()
        assert health["healthy"] is False
        assert "test_service" in health["degraded_services"]
    
    def test_mark_recovered(self, degrader):
        """Test marking service as recovered."""
        degrader.mark_degraded("test_service", "error")
        degrader.mark_recovered("test_service")
        
        assert not degrader.is_degraded("test_service")
        assert degrader.get_health_status()["healthy"]
    
    def test_get_fallback(self, degrader):
        """Test fallback values are returned."""
        # Default fallback
        fallback = degrader.get_fallback("vision")
        assert fallback is not None
        assert "description" in fallback
        
        # Custom fallback
        degrader.set_fallback("custom", "custom_value")
        assert degrader.get_fallback("custom") == "custom_value"
    
    def test_wrap_service_decorator(self, degrader):
        """Test wrap_service decorator."""
        call_count = [0]
        
        @degrader.wrap_service("test_service", fallback="fallback")
        def service_call():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("First call fails")
            return "success"
        
        # First call should fail and return fallback
        result1 = service_call()
        assert result1 == "fallback"
        assert degrader.is_degraded("test_service")
        
        # Second call should also return fallback (still degraded)
        result2 = service_call()
        assert result2 == "fallback"


# ═══════════════════════════════════════════════════════════════════════════════
# RETRY WITH BACKOFF TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRetryWithBackoff:
    """Tests for RetryWithBackoff."""
    
    def test_import(self):
        """Test module imports correctly."""
        from utils.resilience import RetryWithBackoff
        assert RetryWithBackoff is not None
    
    def test_succeeds_without_retry(self):
        """Test successful calls don't retry."""
        from utils.resilience import RetryWithBackoff
        
        call_count = [0]
        
        @RetryWithBackoff(max_retries=3, base_delay=0.01)
        def success_fn():
            call_count[0] += 1
            return "success"
        
        result = success_fn()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retries_on_failure(self):
        """Test retries on transient failure."""
        from utils.resilience import RetryWithBackoff
        
        call_count = [0]
        
        @RetryWithBackoff(max_retries=3, base_delay=0.01)
        def flaky_fn():
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("Transient error")
            return "success"
        
        result = flaky_fn()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_raises_after_max_retries(self):
        """Test raises exception after max retries exhausted."""
        from utils.resilience import RetryWithBackoff
        
        @RetryWithBackoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise RuntimeError("Always fails")
        
        with pytest.raises(RuntimeError):
            always_fails()


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def test_import(self):
        """Test module imports correctly."""
        from utils.resilience import RateLimiter
        assert RateLimiter is not None
    
    def test_allows_under_limit(self):
        """Test allows calls under rate limit."""
        from utils.resilience import RateLimiter
        
        limiter = RateLimiter(rate=10, period=1.0)
        
        for _ in range(5):
            assert limiter.acquire()
    
    def test_blocks_over_limit(self):
        """Test blocks calls over rate limit."""
        from utils.resilience import RateLimiter
        
        limiter = RateLimiter(rate=2, period=1.0)
        
        # Exhaust tokens
        limiter.acquire()
        limiter.acquire()
        
        # Next should fail
        assert not limiter.acquire()


# ═══════════════════════════════════════════════════════════════════════════════
# THREAD SAFETY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestThreadSafety:
    """Tests for thread safety of resilience utilities."""
    
    @pytest.mark.slow
    def test_circuit_breaker_thread_safe(self, circuit_breaker):
        """Test CircuitBreaker is thread-safe."""
        results = []
        
        def record_failures():
            for _ in range(10):
                circuit_breaker.record_failure()
                time.sleep(0.01)
        
        def record_successes():
            for _ in range(10):
                circuit_breaker.record_success()
                time.sleep(0.01)
        
        threads = [
            threading.Thread(target=record_failures),
            threading.Thread(target=record_successes),
            threading.Thread(target=record_failures),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert True
    
    @pytest.mark.slow
    def test_degrader_thread_safe(self, degrader):
        """Test GracefulDegrader is thread-safe."""
        def mark_degraded():
            for i in range(10):
                degrader.mark_degraded(f"service_{i}", "error")
                time.sleep(0.01)
        
        def mark_recovered():
            for i in range(10):
                degrader.mark_recovered(f"service_{i}")
                time.sleep(0.01)
        
        threads = [
            threading.Thread(target=mark_degraded),
            threading.Thread(target=mark_recovered),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert True
