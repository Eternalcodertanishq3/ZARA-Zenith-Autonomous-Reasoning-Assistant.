"""
ZARA Heartbeat Protocol - Enhanced System Resilience
"""
import logging
import threading
import time
import traceback
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger("ZARA_HEARTBEAT")


class ModuleStatus(Enum):
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    CRASHED = "crashed"
    STOPPED = "stopped"
    RECOVERING = "recovering"


@dataclass
class ModuleHealth:
    """Health status of a monitored module."""
    name: str
    status: ModuleStatus
    last_heartbeat: float
    restart_count: int
    total_uptime: float = 0.0
    start_time: float = field(default_factory=time.time)
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


class HeartbeatProtocol:
    """
    Master supervisor ensuring system resilience.
    Enhanced with:
    - Module dependency tracking
    - Graceful degradation
    - Response time monitoring
    - Crash analytics
    - Recovery strategies
    - Event hooks
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleHealth] = {}
        self.restart_handlers: Dict[str, Callable] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.dependencies: Dict[str, List[str]] = {}
        
        # Configuration
        self.heartbeat_interval = 5.0
        # Timeout for module heartbeats - 60 seconds is reasonable
        # Modules should call heartbeat.heartbeat() periodically
        self.timeout_threshold = 60.0
        self.max_restarts = 3
        self.restart_backoff = 10.0
        
        # State
        self.is_running = False
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Event hooks
        self.on_module_crash: Optional[Callable[[str, str], None]] = None
        self.on_module_recover: Optional[Callable[[str], None]] = None
        self.on_system_degraded: Optional[Callable[[], None]] = None
        
        # Analytics
        self.crash_history: List[Dict] = []
        
        logger.info("Heartbeat Protocol initialized.")
    
    def register_module(self, name: str,
                       health_check: Optional[Callable] = None,
                       restart_handler: Optional[Callable] = None,
                       depends_on: Optional[List[str]] = None):
        """
        Register a module for monitoring.
        
        Args:
            name: Module identifier
            health_check: Function returning True if healthy
            restart_handler: Function to restart the module
            depends_on: List of module names this depends on
        """
        with self.lock:
            self.modules[name] = ModuleHealth(
                name=name,
                status=ModuleStatus.UNKNOWN,
                last_heartbeat=time.time(),
                restart_count=0
            )
            
            if health_check:
                self.health_checks[name] = health_check
            if restart_handler:
                self.restart_handlers[name] = restart_handler
            if depends_on:
                self.dependencies[name] = depends_on
            
            logger.info(f"Registered module: {name}")
    
    def heartbeat(self, module_name: str, response_time_ms: Optional[float] = None):
        """Record a heartbeat from a module."""
        with self.lock:
            if module_name in self.modules:
                module = self.modules[module_name]
                now = time.time()
                
                module.last_heartbeat = now
                
                if module.status in [ModuleStatus.CRASHED, ModuleStatus.RECOVERING]:
                    module.status = ModuleStatus.RUNNING
                    logger.info(f"Module {module_name} recovered!")
                    if self.on_module_recover:
                        self.on_module_recover(module_name)
                else:
                    module.status = ModuleStatus.RUNNING
                
                if response_time_ms:
                    module.response_times.append(response_time_ms)
    
    def report_error(self, module_name: str, error: str, stack: Optional[str] = None):
        """Report an error from a module."""
        with self.lock:
            if module_name in self.modules:
                module = self.modules[module_name]
                module.status = ModuleStatus.DEGRADED
                module.error_message = error
                module.error_stack = stack or traceback.format_exc()
                
                logger.warning(f"Module {module_name} error: {error}")
    
    def mark_starting(self, module_name: str):
        """Mark module as starting up."""
        with self.lock:
            if module_name in self.modules:
                self.modules[module_name].status = ModuleStatus.STARTING
                self.modules[module_name].start_time = time.time()
    
    def mark_stopped(self, module_name: str):
        """Mark module as intentionally stopped."""
        with self.lock:
            if module_name in self.modules:
                module = self.modules[module_name]
                module.status = ModuleStatus.STOPPED
                module.total_uptime += time.time() - module.start_time
    
    def start(self):
        """Start the heartbeat monitoring loop."""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = time.time()
        
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        logger.info("Heartbeat monitoring started.")
    
    def stop(self):
        """Stop monitoring."""
        self.is_running = False
        logger.info("Heartbeat monitoring stopped.")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            current_time = time.time()
            any_degraded = False
            
            with self.lock:
                for name, health in self.modules.items():
                    if health.status == ModuleStatus.STOPPED:
                        continue
                    
                    # Check dependencies first
                    if not self._check_dependencies(name):
                        if health.status != ModuleStatus.DEGRADED:
                            health.status = ModuleStatus.DEGRADED
                            health.error_message = "Dependency unavailable"
                        any_degraded = True
                        continue
                    
                    # Check heartbeat timeout
                    time_since_beat = current_time - health.last_heartbeat
                    
                    if time_since_beat > self.timeout_threshold:
                        if health.status not in [ModuleStatus.CRASHED, ModuleStatus.RECOVERING]:
                            self._handle_crash(name, f"No heartbeat for {time_since_beat:.1f}s")
                    
                    # Run health check
                    elif name in self.health_checks:
                        try:
                            if not self.health_checks[name]():
                                health.status = ModuleStatus.DEGRADED
                                any_degraded = True
                        except Exception as e:
                            health.status = ModuleStatus.DEGRADED
                            health.error_message = str(e)
                            any_degraded = True
            
            if any_degraded and self.on_system_degraded:
                self.on_system_degraded()
            
            time.sleep(self.heartbeat_interval)
    
    def _check_dependencies(self, module_name: str) -> bool:
        """Check if all dependencies are running."""
        deps = self.dependencies.get(module_name, [])
        
        for dep in deps:
            if dep in self.modules:
                if self.modules[dep].status != ModuleStatus.RUNNING:
                    return False
        
        return True
    
    def _handle_crash(self, module_name: str, reason: str):
        """Handle a module crash."""
        module = self.modules[module_name]
        module.status = ModuleStatus.CRASHED
        module.error_message = reason
        
        logger.error(f"Module {module_name} CRASHED: {reason}")
        
        # Record crash
        self.crash_history.append({
            "module": module_name,
            "reason": reason,
            "timestamp": time.time(),
            "restart_count": module.restart_count
        })
        
        # Trigger callback
        if self.on_module_crash:
            self.on_module_crash(module_name, reason)
        
        # Attempt restart with backoff
        self._attempt_restart(module_name)
    
    def _attempt_restart(self, module_name: str):
        """Attempt to restart a crashed module with exponential backoff."""
        module = self.modules.get(module_name)
        if not module:
            return
        
        if module.restart_count >= self.max_restarts:
            logger.critical(f"Module {module_name} exceeded {self.max_restarts} restarts. Manual intervention required.")
            return
        
        if module_name not in self.restart_handlers:
            logger.warning(f"No restart handler for {module_name}")
            return
        
        # Exponential backoff
        backoff = self.restart_backoff * (2 ** module.restart_count)
        
        def delayed_restart():
            time.sleep(backoff)
            if module.status == ModuleStatus.CRASHED:
                logger.info(f"Attempting restart of {module_name} (attempt {module.restart_count + 1})...")
                try:
                    module.status = ModuleStatus.RECOVERING
                    self.restart_handlers[module_name]()
                    module.restart_count += 1
                    module.last_heartbeat = time.time()
                    module.start_time = time.time()
                    logger.info(f"Restart initiated for {module_name}")
                except Exception as e:
                    logger.error(f"Restart failed for {module_name}: {e}")
                    module.status = ModuleStatus.CRASHED
                    module.error_message = str(e)
        
        threading.Thread(target=delayed_restart, daemon=True).start()
    
    def get_status(self) -> Dict:
        """Get comprehensive system health status."""
        with self.lock:
            modules_status = {}
            
            for name, health in self.modules.items():
                avg_response = None
                if health.response_times:
                    avg_response = sum(health.response_times) / len(health.response_times)
                
                modules_status[name] = {
                    "status": health.status.value,
                    "last_heartbeat_ago": time.time() - health.last_heartbeat,
                    "restart_count": health.restart_count,
                    "error": health.error_message,
                    "avg_response_ms": avg_response
                }
            
            # Overall health
            statuses = [m.status for m in self.modules.values()]
            
            if not statuses:
                overall = "UNKNOWN"
            elif all(s == ModuleStatus.RUNNING for s in statuses):
                overall = "HEALTHY"
            elif any(s == ModuleStatus.CRASHED for s in statuses):
                overall = "CRITICAL"
            elif any(s in [ModuleStatus.DEGRADED, ModuleStatus.RECOVERING] for s in statuses):
                overall = "DEGRADED"
            else:
                overall = "STARTING"
            
            return {
                "overall": overall,
                "uptime": time.time() - self.start_time,
                "modules": modules_status,
                "recent_crashes": len([c for c in self.crash_history if time.time() - c["timestamp"] < 3600])
            }
    
    def is_healthy(self) -> bool:
        """Quick health check."""
        return all(
            m.status == ModuleStatus.RUNNING 
            for m in self.modules.values() 
            if m.status != ModuleStatus.STOPPED
        )
    
    def get_crash_report(self) -> List[Dict]:
        """Get recent crash history for debugging."""
        return self.crash_history[-10:]  # Last 10 crashes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    heartbeat = HeartbeatProtocol()
    heartbeat.register_module("brain", health_check=lambda: True)
    heartbeat.register_module("vision", depends_on=["brain"])
    
    heartbeat.start()
    
    # Simulate heartbeats
    for i in range(5):
        heartbeat.heartbeat("brain", response_time_ms=50 + i*10)
        heartbeat.heartbeat("vision", response_time_ms=100 + i*5)
        time.sleep(1)
    
    print("System Status:", heartbeat.get_status())
