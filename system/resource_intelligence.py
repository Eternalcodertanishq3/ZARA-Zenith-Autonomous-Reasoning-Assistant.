"""
ZARA Autonomous Resource Intelligence - Self-Managing System
An intelligent, self-optimizing resource management system that
autonomously balances performance, power, and user experience.
"""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger("ZARA_SYSTEM")


# ═══════════════════════════════════════════════════════════════════════
# COMPUTE DEVICES
# ═══════════════════════════════════════════════════════════════════════

class ComputeDevice(Enum):
    NVIDIA_GPU = "nvidia"
    INTEL_IGPU = "intel"
    CPU = "cpu"
    AUTO = "auto"


class QuantizationLevel(Enum):
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"
    Q4_K_M = "q4_k_m"
    Q5_K_M = "q5_k_m"


class PowerState(Enum):
    TURBO = "turbo"        # Maximum performance
    ACTIVE = "active"      # Normal operation
    EFFICIENT = "efficient"# Balanced power/performance
    QUIET = "quiet"        # Minimal resources
    HIBERNATE = "hibernate"# Almost no activity


class SystemHealth(Enum):
    OPTIMAL = "optimal"
    GOOD = "good"
    STRESSED = "stressed"
    CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ResourceMetrics:
    """Current resource usage metrics."""
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    vram_used_gb: float = 0.0
    vram_total_gb: float = 6.0
    gpu_temp_celsius: float = 45.0
    power_watts: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskProfile:
    """Profile of a compute task."""
    name: str
    vram_requirement: float
    compute_intensity: float  # 0-1
    latency_sensitive: bool
    preferred_device: ComputeDevice
    min_quantization: QuantizationLevel = QuantizationLevel.INT4
    priority: int = 5  # 1=highest, 10=lowest
    can_offload: bool = True


@dataclass
class ModelState:
    """Current state of a loaded model."""
    name: str
    is_loaded: bool = False
    device: Optional[ComputeDevice] = None
    vram_used: float = 0.0
    quantization: QuantizationLevel = QuantizationLevel.INT4
    last_used: float = 0.0
    use_count: int = 0
    avg_inference_ms: float = 0.0


@dataclass
class SystemDecision:
    """An autonomous decision made by the system."""
    timestamp: float
    decision_type: str
    action: str
    reason: str
    impact: str
    confidence: float


# ═══════════════════════════════════════════════════════════════════════
# AUTONOMOUS RESOURCE INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════

class AutonomousResourceIntelligence:
    """
    ZARA's self-managing resource system.
    
    Capabilities:
    - Autonomous workload distribution
    - Predictive resource allocation
    - Self-healing and recovery
    - Performance learning and optimization
    - Intelligent power management
    - Proactive problem prevention
    """
    
    def __init__(self, vram_budget: float = 6.0):
        self.vram_budget = vram_budget
        self.vram_buffer = 0.5  # Reserve for OS
        self.vram_available = vram_budget - self.vram_buffer
        self.vram_allocated = 0.0
        
        self.lock = threading.RLock()
        self.is_running = False
        
        # Current state
        self.power_state = PowerState.ACTIVE
        self.health = SystemHealth.OPTIMAL
        self.last_user_activity = time.time()
        
        # Task and model tracking
        self.task_profiles: Dict[str, TaskProfile] = self._init_task_profiles()
        self.model_states: Dict[str, ModelState] = {}
        self.active_tasks: Dict[str, TaskProfile] = {}
        
        # Performance history
        self.metrics_history: deque = deque(maxlen=100)
        self.decision_history: deque = deque(maxlen=50)
        self.inference_times: Dict[str, deque] = {}
        
        # Learning parameters
        self.performance_baseline: Dict[str, float] = {}
        self.optimal_allocations: Dict[str, Dict] = {}
        
        # Quantization factors
        self.quant_factors = {
            QuantizationLevel.FP16: 1.0,
            QuantizationLevel.INT8: 0.5,
            QuantizationLevel.INT4: 0.3,
            QuantizationLevel.Q4_K_M: 0.28,
            QuantizationLevel.Q5_K_M: 0.35,
        }
        
        # Power state configurations
        self.power_configs = {
            PowerState.TURBO: {
                "fps": 60, "vision_interval": 0.033,
                "inference_priority": "quality", "keep_models_hot": True
            },
            PowerState.ACTIVE: {
                "fps": 30, "vision_interval": 0.1,
                "inference_priority": "balanced", "keep_models_hot": True
            },
            PowerState.EFFICIENT: {
                "fps": 20, "vision_interval": 0.2,
                "inference_priority": "speed", "keep_models_hot": True
            },
            PowerState.QUIET: {
                "fps": 10, "vision_interval": 0.5,
                "inference_priority": "speed", "keep_models_hot": False
            },
            PowerState.HIBERNATE: {
                "fps": 1, "vision_interval": 5.0,
                "inference_priority": "none", "keep_models_hot": False
            }
        }
        
        # Callbacks
        self.on_decision: Optional[Callable[[SystemDecision], None]] = None
        self.on_health_change: Optional[Callable[[SystemHealth], None]] = None
        self.on_power_change: Optional[Callable[[PowerState], None]] = None
        
        # Thresholds
        self.idle_efficient = 60  # seconds
        self.idle_quiet = 180
        self.idle_hibernate = 600
        self.temp_warning = 75
        self.temp_critical = 85
        
        logger.info(f"🔋 Resource Intelligence: {self.vram_available:.1f}GB available")

    def _init_task_profiles(self) -> Dict[str, TaskProfile]:
        """Initialize task profiles."""
        return {
            "brain": TaskProfile(
                "Brain (Qwen)", 2.8, 0.9, True,
                ComputeDevice.NVIDIA_GPU, QuantizationLevel.Q5_K_M, 1
            ),
            "vision": TaskProfile(
                "Vision (InternVL)", 1.6, 0.8, True,
                ComputeDevice.NVIDIA_GPU, QuantizationLevel.INT4, 2
            ),
            "tts": TaskProfile(
                "TTS (XTTS)", 1.5, 0.6, False,
                ComputeDevice.CPU, QuantizationLevel.FP16, 3
            ),
            "rvc": TaskProfile(
                "Voice (RVC)", 0.8, 0.7, False,
                ComputeDevice.NVIDIA_GPU, QuantizationLevel.FP16, 4, True
            ),
            "avatar": TaskProfile(
                "Avatar", 0.2, 0.3, True,
                ComputeDevice.INTEL_IGPU, QuantizationLevel.FP16, 5
            ),
            "stt": TaskProfile(
                "STT (Whisper)", 0.5, 0.5, True,
                ComputeDevice.CPU, QuantizationLevel.INT8, 2
            ),
            "memory": TaskProfile(
                "Memory DB", 0.0, 0.2, False,
                ComputeDevice.CPU, QuantizationLevel.FP16, 6
            ),
        }

    # ═══════════════════════════════════════════════════════════════════
    # AUTONOMOUS DECISION MAKING
    # ═══════════════════════════════════════════════════════════════════
    
    def request_resources(self, task_name: str) -> Tuple[bool, ComputeDevice]:
        """
        Autonomously allocate resources for a task.
        Returns (success, assigned_device).
        """
        profile = self.task_profiles.get(task_name)
        if not profile:
            logger.warning(f"Unknown task: {task_name}")
            return False, ComputeDevice.CPU
        
        with self.lock:
            # Check if already allocated
            if task_name in self.active_tasks:
                return True, self.model_states.get(task_name, ModelState(task_name)).device or profile.preferred_device
            
            # Determine allocation
            device, success = self._intelligent_allocate(task_name, profile)
            
            if success:
                self.active_tasks[task_name] = profile
                self._log_decision(
                    "allocation",
                    f"Allocated {task_name} to {device.value}",
                    f"VRAM: {self.vram_allocated:.1f}/{self.vram_available:.1f}GB",
                    0.9
                )
            
            return success, device

    def _intelligent_allocate(self, task_name: str, profile: TaskProfile) -> Tuple[ComputeDevice, bool]:
        """Make intelligent allocation decision."""
        # For GPU tasks
        if profile.preferred_device == ComputeDevice.NVIDIA_GPU:
            needed = profile.vram_requirement
            
            # Check if we have room
            if self.vram_allocated + needed <= self.vram_available:
                self.vram_allocated += needed
                self._update_model_state(task_name, True, ComputeDevice.NVIDIA_GPU, needed)
                return ComputeDevice.NVIDIA_GPU, True
            
            # Try to make room
            if self._try_free_vram(needed):
                self.vram_allocated += needed
                self._update_model_state(task_name, True, ComputeDevice.NVIDIA_GPU, needed)
                return ComputeDevice.NVIDIA_GPU, True
            
            # Fallback to CPU if allowed
            if profile.can_offload:
                self._update_model_state(task_name, True, ComputeDevice.CPU, 0)
                return ComputeDevice.CPU, True
            
            return ComputeDevice.NVIDIA_GPU, False
        
        # For other devices
        self._update_model_state(task_name, True, profile.preferred_device, 0)
        return profile.preferred_device, True

    def _try_free_vram(self, needed: float) -> bool:
        """Try to free VRAM by offloading low-priority tasks."""
        # Find offloadable tasks sorted by priority (lowest first)
        candidates = []
        for task_name, profile in self.active_tasks.items():
            if profile.can_offload and profile.preferred_device == ComputeDevice.NVIDIA_GPU:
                state = self.model_states.get(task_name)
                if state and state.is_loaded:
                    # Score: lower is better to offload
                    idle_time = time.time() - state.last_used
                    score = profile.priority + (idle_time / 60)  # Favor idle tasks
                    candidates.append((score, task_name, state.vram_used))
        
        candidates.sort(reverse=True)  # Highest score = best to offload
        
        freed = 0.0
        for score, task_name, vram in candidates:
            if freed >= needed:
                break
            
            # Offload this task
            self.release_resources(task_name)
            freed += vram
            
            self._log_decision(
                "offload",
                f"Offloaded {task_name} to make room",
                f"Freed {vram:.2f}GB",
                0.8
            )
        
        return freed >= needed

    def release_resources(self, task_name: str):
        """Release resources for a task."""
        with self.lock:
            if task_name in self.active_tasks:
                profile = self.active_tasks.pop(task_name)
                
                state = self.model_states.get(task_name)
                if state and state.device == ComputeDevice.NVIDIA_GPU:
                    self.vram_allocated -= state.vram_used
                    self.vram_allocated = max(0, self.vram_allocated)
                
                self._update_model_state(task_name, False, None, 0)
                logger.debug(f"Released {task_name}")

    def _update_model_state(self, task_name: str, loaded: bool, 
                           device: Optional[ComputeDevice], vram: float):
        """Update model state tracking."""
        if task_name not in self.model_states:
            self.model_states[task_name] = ModelState(task_name)
        
        state = self.model_states[task_name]
        state.is_loaded = loaded
        state.device = device
        state.vram_used = vram
        state.last_used = time.time()
        if loaded:
            state.use_count += 1

    # ═══════════════════════════════════════════════════════════════════
    # POWER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def record_user_activity(self):
        """Record user interaction."""
        self.last_user_activity = time.time()
        
        # Wake up if in power saving mode
        if self.power_state in [PowerState.QUIET, PowerState.HIBERNATE]:
            self._transition_power(PowerState.ACTIVE)

    def _update_power_state(self):
        """Update power state based on activity."""
        idle_time = time.time() - self.last_user_activity
        
        if idle_time > self.idle_hibernate:
            target = PowerState.HIBERNATE
        elif idle_time > self.idle_quiet:
            target = PowerState.QUIET
        elif idle_time > self.idle_efficient:
            target = PowerState.EFFICIENT
        else:
            target = PowerState.ACTIVE
        
        if target != self.power_state:
            self._transition_power(target)

    def _transition_power(self, new_state: PowerState):
        """Transition to a new power state."""
        old_state = self.power_state
        self.power_state = new_state
        
        self._log_decision(
            "power",
            f"Power: {old_state.value} → {new_state.value}",
            f"Idle: {time.time() - self.last_user_activity:.0f}s",
            0.95
        )
        
        if self.on_power_change:
            self.on_power_change(new_state)
        
        # Handle model keep-alive
        config = self.power_configs[new_state]
        if not config["keep_models_hot"]:
            self._unload_non_essential_models()

    def _unload_non_essential_models(self):
        """Unload models that aren't essential."""
        for task_name, profile in list(self.active_tasks.items()):
            if profile.priority > 3:  # Low priority
                self.release_resources(task_name)

    def get_power_config(self) -> Dict:
        """Get current power configuration."""
        return self.power_configs.get(self.power_state, {})

    # ═══════════════════════════════════════════════════════════════════
    # HEALTH MONITORING
    # ═══════════════════════════════════════════════════════════════════
    
    def update_metrics(self, metrics: ResourceMetrics):
        """Update with new resource metrics."""
        self.metrics_history.append(metrics)
        
        # Assess health
        new_health = self._assess_health(metrics)
        
        if new_health != self.health:
            old_health = self.health
            self.health = new_health
            
            self._log_decision(
                "health",
                f"Health: {old_health.value} → {new_health.value}",
                f"GPU: {metrics.gpu_temp_celsius}°C, VRAM: {metrics.vram_used_gb:.1f}GB",
                0.9
            )
            
            if self.on_health_change:
                self.on_health_change(new_health)
            
            # Take action if needed
            if new_health == SystemHealth.CRITICAL:
                self._emergency_mitigation()

    def _assess_health(self, metrics: ResourceMetrics) -> SystemHealth:
        """Assess system health from metrics."""
        # Temperature check
        if metrics.gpu_temp_celsius >= self.temp_critical:
            return SystemHealth.CRITICAL
        if metrics.gpu_temp_celsius >= self.temp_warning:
            return SystemHealth.STRESSED
        
        # VRAM check
        vram_util = metrics.vram_used_gb / metrics.vram_total_gb
        if vram_util > 0.95:
            return SystemHealth.STRESSED
        
        # CPU check
        if metrics.cpu_percent > 90:
            return SystemHealth.STRESSED
        
        # RAM check
        if metrics.ram_percent > 90:
            return SystemHealth.STRESSED
        
        if vram_util > 0.8 or metrics.cpu_percent > 70:
            return SystemHealth.GOOD
        
        return SystemHealth.OPTIMAL

    def _emergency_mitigation(self):
        """Take emergency action when system is critical."""
        self._log_decision(
            "emergency",
            "Emergency mitigation activated",
            "Unloading non-essential models",
            1.0
        )
        
        # Unload low priority models
        for task_name, profile in list(self.active_tasks.items()):
            if profile.priority > 2:
                self.release_resources(task_name)
        
        # Force efficient mode
        self._transition_power(PowerState.EFFICIENT)

    # ═══════════════════════════════════════════════════════════════════
    # PERFORMANCE LEARNING
    # ═══════════════════════════════════════════════════════════════════
    
    def record_inference(self, task_name: str, duration_ms: float):
        """Record inference performance."""
        if task_name not in self.inference_times:
            self.inference_times[task_name] = deque(maxlen=50)
        
        self.inference_times[task_name].append(duration_ms)
        
        # Update model state
        if task_name in self.model_states:
            times = list(self.inference_times[task_name])
            self.model_states[task_name].avg_inference_ms = statistics.mean(times)
            self.model_states[task_name].last_used = time.time()

    def get_performance_stats(self, task_name: str) -> Dict:
        """Get performance statistics for a task."""
        times = self.inference_times.get(task_name, [])
        
        if not times:
            return {"available": False}
        
        times_list = list(times)
        return {
            "available": True,
            "avg_ms": statistics.mean(times_list),
            "min_ms": min(times_list),
            "max_ms": max(times_list),
            "samples": len(times_list),
            "p95_ms": sorted(times_list)[int(len(times_list) * 0.95)] if len(times_list) > 10 else max(times_list)
        }

    def suggest_optimization(self, task_name: str) -> Optional[str]:
        """Suggest optimization for a task."""
        profile = self.task_profiles.get(task_name)
        state = self.model_states.get(task_name)
        
        if not profile or not state:
            return None
        
        suggestions = []
        
        # Check if running on suboptimal device
        if state.device != profile.preferred_device:
            suggestions.append(f"Move to {profile.preferred_device.value} for better performance")
        
        # Check idle time
        idle = time.time() - state.last_used
        if idle > 300 and profile.can_offload:
            suggestions.append(f"Consider unloading (idle for {idle/60:.1f} min)")
        
        # Performance degradation
        stats = self.get_performance_stats(task_name)
        if stats.get("available"):
            baseline = self.performance_baseline.get(task_name)
            if baseline and stats["avg_ms"] > baseline * 1.5:
                suggestions.append("Performance degraded - consider reloading model")
        
        return suggestions[0] if suggestions else None

    # ═══════════════════════════════════════════════════════════════════
    # DECISION LOGGING
    # ═══════════════════════════════════════════════════════════════════
    
    def _log_decision(self, decision_type: str, action: str, 
                     impact: str, confidence: float):
        """Log an autonomous decision."""
        decision = SystemDecision(
            timestamp=time.time(),
            decision_type=decision_type,
            action=action,
            reason="autonomous_optimization",
            impact=impact,
            confidence=confidence
        )
        
        self.decision_history.append(decision)
        logger.info(f"[DECISION] {action} | {impact}")
        
        if self.on_decision:
            self.on_decision(decision)

    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND MONITORING
    # ═══════════════════════════════════════════════════════════════════
    

    def start(self):
        """Start the resource intelligence system."""
        self.start_monitoring()

    def start_monitoring(self):
        """Start autonomous monitoring."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        logger.info("🔋 Resource monitoring started")

    def stop(self):
        """Stop the resource intelligence system."""
        self.stop_monitoring()

    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_running = False

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.is_running:
            # Update power state
            self._update_power_state()
            
            # Collect metrics if available
            metrics = self._collect_metrics()
            if metrics:
                self.update_metrics(metrics)
            
            # Periodic optimization
            self._periodic_optimization()
            
            time.sleep(10)

    def _collect_metrics(self) -> Optional[ResourceMetrics]:
        """Collect current system metrics."""
        try:
            import psutil
            
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            # Try to get GPU info
            gpu_temp = 45.0
            vram_used = self.vram_allocated
            
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_temp = gpus[0].temperature
                    vram_used = gpus[0].memoryUsed / 1024
            except:
                pass
            
            return ResourceMetrics(
                cpu_percent=cpu,
                ram_percent=ram,
                vram_used_gb=vram_used,
                gpu_temp_celsius=gpu_temp
            )
        except:
            return None

    def _periodic_optimization(self):
        """Run periodic optimization."""
        # Clean up unused models
        now = time.time()
        for task_name, state in list(self.model_states.items()):
            if state.is_loaded:
                idle = now - state.last_used
                profile = self.task_profiles.get(task_name)
                
                # Unload if idle too long and power saving
                if profile and profile.can_offload:
                    if self.power_state == PowerState.QUIET and idle > 120:
                        self.release_resources(task_name)
                    elif self.power_state == PowerState.HIBERNATE and idle > 30:
                        self.release_resources(task_name)

    # ═══════════════════════════════════════════════════════════════════
    # STATUS AND REPORTING
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "vram": {
                "allocated_gb": self.vram_allocated,
                "available_gb": self.vram_available,
                "utilization": self.vram_allocated / self.vram_available,
                "budget_gb": self.vram_budget
            },
            "power": {
                "state": self.power_state.value,
                "config": self.power_configs[self.power_state],
                "idle_seconds": time.time() - self.last_user_activity
            },
            "health": self.health.value,
            "active_tasks": list(self.active_tasks.keys()),
            "loaded_models": {
                name: {
                    "device": state.device.value if state.device else "none",
                    "vram_gb": state.vram_used,
                    "uses": state.use_count,
                    "avg_ms": state.avg_inference_ms
                }
                for name, state in self.model_states.items()
                if state.is_loaded
            },
            "recent_decisions": len(self.decision_history)
        }

    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations."""
        recommendations = []
        
        if self.health == SystemHealth.STRESSED:
            recommendations.append("⚠️ System stressed - consider reducing workload")
        
        if self.vram_allocated / self.vram_available > 0.9:
            recommendations.append("🔴 VRAM nearly full - offload unused models")
        
        # Find idle models
        now = time.time()
        for name, state in self.model_states.items():
            if state.is_loaded and now - state.last_used > 300:
                recommendations.append(f"💤 {name} idle for {(now - state.last_used)/60:.0f}min")
        
        return recommendations


# Singleton
_system_instance = None

def get_system() -> AutonomousResourceIntelligence:
    """Get the global system instance."""
    global _system_instance
    if _system_instance is None:
        _system_instance = AutonomousResourceIntelligence()
    return _system_instance


# Backwards compatibility
HybridLoadBalancer = AutonomousResourceIntelligence
VRAMGovernor = AutonomousResourceIntelligence
EnergySaver = AutonomousResourceIntelligence


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    system = AutonomousResourceIntelligence()
    
    # Test allocations
    success, device = system.request_resources("brain")
    print(f"Brain: {success} on {device.value}")
    
    success, device = system.request_resources("vision")
    print(f"Vision: {success} on {device.value}")
    
    print(f"\nStatus:\n{system.get_status()}")
    print(f"\nRecommendations:\n{system.get_recommendations()}")
