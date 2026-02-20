"""
ZARA Test Fixtures and Configuration
=====================================
Common fixtures for all tests.
"""

import pytest
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during tests
    format="%(name)s | %(levelname)s | %(message)s"
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def degrader():
    """Fresh GracefulDegrader instance for testing."""
    from utils.resilience import GracefulDegrader
    return GracefulDegrader()


@pytest.fixture
def circuit_breaker():
    """Fresh CircuitBreaker instance for testing."""
    from utils.resilience import CircuitBreaker
    return CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.5)


@pytest.fixture
def unified_perception():
    """Fresh UnifiedPerception instance for testing."""
    from brain.unified_perception import UnifiedPerception
    return UnifiedPerception()


@pytest.fixture
def perceptual_tokenizer():
    """Fresh PerceptualTokenizer for testing."""
    from brain.unified_perception import PerceptualTokenizer
    return PerceptualTokenizer()


@pytest.fixture
def joint_attention():
    """Fresh JointAttentionMechanism for testing."""
    from brain.unified_perception import JointAttentionMechanism
    return JointAttentionMechanism()


@pytest.fixture
def scene_builder():
    """Fresh SceneGraphBuilder for testing."""
    from brain.unified_perception import SceneGraphBuilder
    return SceneGraphBuilder()


@pytest.fixture
def moment_buffer():
    """Fresh MomentBuffer for testing."""
    from brain.unified_perception import MomentBuffer
    return MomentBuffer()


# ═══════════════════════════════════════════════════════════════════════════════
# MARKERS
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks as integration tests")
    config.addinivalue_line("markers", "unit: marks as unit tests")
