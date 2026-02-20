"""
ZARA Evolution Integration v1.0
================================
Hooks Self-Evolution into ZARA's Core Systems

This module connects the Self-Evolution Engine to:
1. Error handling - auto-detect capability gaps from failures
2. Request processing - detect when user asks for unsupported features
3. Background monitoring - periodic evolution cycles
4. Dream mode - evolve during idle time

Usage:
    from evolution.integration import ZARAEvolutionBridge
    
    bridge = ZARAEvolutionBridge()
    bridge.start()  # Start automatic evolution monitoring
    
    # When handling user requests
    bridge.on_user_request("Can you play music from Spotify?")
    
    # When errors occur
    bridge.on_error(exception, context="processing user request")
"""

import logging
import threading
import time
import sys
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass

# Ensure imports work
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from evolution.self_evolution import (
    get_evolution_engine, 
    SelfEvolutionEngine,
    Evolution,
    CapabilityGap,
    EvolutionStatus,
    SafetyLevel
)

logger = logging.getLogger("ZARA_EVOLUTION_BRIDGE")


@dataclass
class EvolutionEvent:
    """Event from the evolution system."""
    event_type: str  # "gap_detected", "evolution_started", "approval_needed", "complete", "failed"
    evolution_id: Optional[str]
    description: str
    requires_action: bool
    timestamp: float


class ZARAEvolutionBridge:
    """
    Bridge between ZARA's core systems and the Self-Evolution Engine.
    Enables automatic capability detection and evolution.
    """
    
    def __init__(self):
        self.engine = get_evolution_engine()
        
        # Event subscribers
        self.on_event: List[Callable[[EvolutionEvent], None]] = []
        
        # Configuration
        self.auto_evolve_on_error = True
        self.auto_evolve_on_request = True
        self.evolve_during_dreams = True
        self.auto_integrate_safe = True  # Auto-integrate SAFE level changes
        
        # State
        self.is_monitoring = False
        self.monitor_thread = None
        self.error_cooldown: Dict[str, float] = {}  # Prevent spam
        self.cooldown_duration = 300  # 5 minutes
        
        # Stats
        self.errors_detected = 0
        self.requests_analyzed = 0
        self.evolutions_triggered = 0
        
        # Register engine callbacks
        self.engine.on_evolution_complete.append(self._on_evolution_complete)
        self.engine.on_approval_needed.append(self._on_approval_needed)
        
        logger.info("🔗 Evolution Bridge initialized")
    
    def start(self):
        """Start evolution monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🔗 Evolution monitoring started")
    
    def stop(self):
        """Stop evolution monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def on_error(self, error: Exception, context: str = "") -> Optional[CapabilityGap]:
        """
        Called when an error occurs anywhere in ZARA.
        Analyzes if this represents a capability gap.
        """
        self.errors_detected += 1
        
        if not self.auto_evolve_on_error:
            return None
        
        # Check cooldown
        error_key = f"{type(error).__name__}:{str(error)[:50]}"
        if error_key in self.error_cooldown:
            if time.time() - self.error_cooldown[error_key] < self.cooldown_duration:
                return None  # Still in cooldown
        
        # Detect gap
        gap = self.engine.detect_gap(error=error)
        
        if gap:
            self.error_cooldown[error_key] = time.time()
            self._emit_event(EvolutionEvent(
                event_type="gap_detected",
                evolution_id=None,
                description=f"Capability gap from error: {gap.description[:100]}",
                requires_action=False,
                timestamp=time.time()
            ))
            
            # Trigger evolution for high-priority gaps
            if gap.priority >= 0.7:
                self._trigger_evolution(gap)
        
        return gap
    
    def on_user_request(self, request: str) -> Optional[CapabilityGap]:
        """
        Called when user makes a request.
        Checks if request requires capabilities we don't have.
        """
        self.requests_analyzed += 1
        
        if not self.auto_evolve_on_request:
            return None
        
        # Keywords that suggest we might not have the capability
        capability_triggers = [
            "can you", "could you", "is it possible", "do you support",
            "integrate with", "connect to", "add", "enable", "learn"
        ]
        
        request_lower = request.lower()
        
        # Only analyze if it looks like a capability request
        if not any(trigger in request_lower for trigger in capability_triggers):
            return None
        
        gap = self.engine.detect_gap(user_request=request)
        
        if gap:
            self._emit_event(EvolutionEvent(
                event_type="gap_detected",
                evolution_id=None,
                description=f"User requested: {gap.description[:100]}",
                requires_action=False,
                timestamp=time.time()
            ))
            
            # User requests are high priority - evolve immediately
            self._trigger_evolution(gap)
        
        return gap
    
    def on_dream_cycle(self):
        """
        Called during dream mode (idle time).
        Good time to process pending evolutions.
        """
        if not self.evolve_during_dreams:
            return
        
        # Get priority gaps that haven't been addressed yet
        priority_gaps = self.engine.detector.get_priority_gaps(limit=3)
        
        for gap in priority_gaps:
            if gap.id not in self.engine.active_evolutions:
                logger.info(f"🌙 Dream evolving: {gap.description[:50]}...")
                self._trigger_evolution(gap)
                time.sleep(5)  # Space out evolutions
    
    def evolve_now(self, description: str, target_file: str = "") -> Optional[Evolution]:
        """
        Explicitly trigger evolution for a specific capability.
        Used when you know exactly what you need.
        """
        gap = CapabilityGap(
            id=f"explicit_{int(time.time())}",
            description=description,
            detected_at=time.time(),
            context="Explicitly requested evolution",
            priority=0.95,  # Very high priority
            suggested_solution=description,
            related_files=[target_file] if target_file else [],
            tags=["explicit", "user_triggered"]
        )
        
        self.engine.detector._record_gap(gap)
        return self._trigger_evolution(gap, target_file)
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get evolutions waiting for human approval."""
        return self.engine.get_pending_approvals()
    
    def approve(self, evolution_id: str) -> tuple:
        """Approve a pending evolution."""
        success, message = self.engine.approve_evolution(evolution_id)
        
        if success:
            self._emit_event(EvolutionEvent(
                event_type="complete",
                evolution_id=evolution_id,
                description=f"Evolution approved and integrated: {evolution_id}",
                requires_action=False,
                timestamp=time.time()
            ))
        
        return success, message
    
    def reject(self, evolution_id: str) -> tuple:
        """Reject a pending evolution."""
        return self.engine.reject_evolution(evolution_id)
    
    def rollback(self, evolution_id: str) -> tuple:
        """Rollback an integrated evolution."""
        return self.engine.rollback_evolution(evolution_id)
    
    def get_status(self) -> Dict:
        """Get comprehensive evolution status."""
        engine_status = self.engine.get_status()
        
        return {
            **engine_status,
            "bridge_active": self.is_monitoring,
            "errors_detected": self.errors_detected,
            "requests_analyzed": self.requests_analyzed,
            "evolutions_triggered": self.evolutions_triggered,
            "auto_evolve_on_error": self.auto_evolve_on_error,
            "auto_evolve_on_request": self.auto_evolve_on_request
        }
    
    def _trigger_evolution(self, gap: CapabilityGap, 
                          target_file: str = "") -> Optional[Evolution]:
        """Trigger evolution for a gap."""
        self.evolutions_triggered += 1
        
        # Determine if we should auto-integrate
        auto_integrate = self.auto_integrate_safe
        
        target = target_file or self.engine._suggest_target_file(gap)
        
        self._emit_event(EvolutionEvent(
            event_type="evolution_started",
            evolution_id=None,
            description=f"Starting evolution: {gap.description[:100]}",
            requires_action=False,
            timestamp=time.time()
        ))
        
        evolution = self.engine.evolve(gap, target_file=target, auto_integrate=auto_integrate)
        
        return evolution
    
    def _on_evolution_complete(self, evolution: Evolution):
        """Callback when evolution completes."""
        self._emit_event(EvolutionEvent(
            event_type="complete",
            evolution_id=evolution.id,
            description=f"Evolution complete: {evolution.description[:100]}",
            requires_action=False,
            timestamp=time.time()
        ))
        
        logger.info(f"🎉 Evolution complete: {evolution.description[:50]}...")
    
    def _on_approval_needed(self, evolution: Evolution):
        """Callback when approval is needed."""
        self._emit_event(EvolutionEvent(
            event_type="approval_needed",
            evolution_id=evolution.id,
            description=f"Approval needed for: {evolution.description[:100]}",
            requires_action=True,
            timestamp=time.time()
        ))
        
        logger.info(f"⏳ Approval needed: {evolution.description[:50]}...")
    
    def _emit_event(self, event: EvolutionEvent):
        """Emit event to subscribers."""
        for callback in self.on_event:
            try:
                callback(event)
            except Exception as e:
                logger.debug(f"Event callback error: {e}")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Check for stale active evolutions
                for gap_id, evolution in list(self.engine.active_evolutions.items()):
                    if evolution.status == EvolutionStatus.FAILED:
                        # Clean up failed evolutions
                        del self.engine.active_evolutions[gap_id]
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL BRIDGE INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_bridge = None

def get_evolution_bridge() -> ZARAEvolutionBridge:
    """Get the global evolution bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = ZARAEvolutionBridge()
    return _bridge


def start_evolution():
    """Convenience function to start evolution monitoring."""
    bridge = get_evolution_bridge()
    bridge.start()
    return bridge


# ═══════════════════════════════════════════════════════════════════════════
# AUTO-HOOK INTO ZARA SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════

def install_error_hooks():
    """Install global error hooks to detect capability gaps."""
    import sys
    
    original_excepthook = sys.excepthook
    bridge = get_evolution_bridge()
    
    def evolution_excepthook(exc_type, exc_value, exc_tb):
        # Detect capability gap from unhandled exception
        bridge.on_error(exc_value, context="unhandled_exception")
        # Call original handler
        original_excepthook(exc_type, exc_value, exc_tb)
    
    sys.excepthook = evolution_excepthook
    logger.info("🔗 Error hooks installed")


def hook_into_dream_mode():
    """Hook evolution into dream mode for idle-time evolution."""
    try:
        from mind.dream_mode import get_dream_engine
        
        dream = get_dream_engine()
        bridge = get_evolution_bridge()
        
        # Add evolution to dream cycle
        def on_dream_phase(old_phase, new_phase):
            if new_phase.value == "rem_dream":
                # Good time for creative evolution
                bridge.on_dream_cycle()
        
        dream.on_phase_change.append(on_dream_phase)
        logger.info("🔗 Hooked into Dream Mode")
        
    except Exception as e:
        logger.debug(f"Could not hook into dream mode: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🔗 ZARA Evolution Bridge v1.0\n")
    print("=" * 60)
    
    # Create bridge
    bridge = get_evolution_bridge()
    
    # Track events
    events = []
    def on_event(event):
        events.append(event)
        icon = {
            "gap_detected": "🔍",
            "evolution_started": "⚡",
            "approval_needed": "⏳",
            "complete": "✅",
            "failed": "❌"
        }.get(event.event_type, "•")
        print(f"  {icon} {event.event_type}: {event.description[:60]}...")
    
    bridge.on_event.append(on_event)
    
    # Start monitoring
    bridge.start()
    print("✓ Evolution monitoring started")
    
    # Simulate error detection
    print("\n" + "-" * 40)
    print("Simulating error detection...")
    
    try:
        import nonexistent_spotify_module
    except ImportError as e:
        gap = bridge.on_error(e, context="trying to play music")
        if gap:
            print(f"✓ Gap detected: {gap.description[:60]}...")
    
    # Simulate user request
    print("\n" + "-" * 40)
    print("Simulating user request...")
    
    gap = bridge.on_user_request("Can you control my smart home lights?")
    if gap:
        print(f"✓ Gap detected: {gap.description[:60]}...")
    
    # Explicit evolution
    print("\n" + "-" * 40)
    print("Triggering explicit evolution...")
    
    evolution = bridge.evolve_now(
        description="Add weather API integration to provide weather forecasts",
        target_file="actions/skills/weather_skill.py"
    )
    if evolution:
        print(f"✓ Evolution triggered: {evolution.id}")
        print(f"  Status: {evolution.status.value}")
    
    # Wait for evolutions
    print("\n" + "-" * 40)
    print("Waiting for evolution cycles (10 seconds)...")
    time.sleep(10)
    
    # Show status
    print("\n" + "-" * 40)
    status = bridge.get_status()
    print("📊 Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Show pending approvals
    pending = bridge.get_pending_approvals()
    if pending:
        print(f"\n⏳ Pending Approvals: {len(pending)}")
        for p in pending:
            print(f"  - [{p['safety_level']}] {p['description'][:50]}...")
    
    # Stop monitoring
    bridge.stop()
    
    print("\n" + "=" * 60)
    print(f"Events captured: {len(events)}")
    print("✅ Evolution Bridge ready!\n")
