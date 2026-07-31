"""
ZARA Hybrid Load Balancer
Intelligently distributes workloads between NVIDIA GPU and Intel iGPU.
"""
import logging
import threading
from dataclasses import dataclass
from typing import Dict, Callable, Optional
from enum import Enum
import time

logger = logging.getLogger("ZARA_BALANCER")

class ComputeDevice(Enum):
    NVIDIA_GPU = "nvidia"
    INTEL_IGPU = "intel"
    CPU = "cpu"
    AUTO = "auto"

@dataclass
class TaskProfile:
    name: str
    vram_requirement: float  # GB
    compute_intensity: float  # 0-1
    latency_sensitive: bool
    preferred_device: ComputeDevice

class HybridLoadBalancer:
    """
    Intelligent workload distribution between:
    - NVIDIA RTX 4050 (6GB VRAM) - Heavy AI inference
    - Intel iGPU - Graphics/Display rendering
    - CPU - Background tasks
    """
    
    def __init__(self):
        self.nvidia_budget = 6.0  # GB
        self.nvidia_used = 0.0
        self.active_tasks: Dict[str, TaskProfile] = {}
        self.lock = threading.Lock()
        
        # Task configurations
        self.task_profiles = {
            "brain": TaskProfile("Brain (Qwen)", 2.8, 0.9, True, ComputeDevice.NVIDIA_GPU),
            "vision": TaskProfile("Vision (InternVL)", 1.6, 0.8, True, ComputeDevice.NVIDIA_GPU),
            "rvc": TaskProfile("Voice (RVC)", 0.8, 0.7, False, ComputeDevice.NVIDIA_GPU),
            "tts": TaskProfile("TTS (XTTS)", 1.5, 0.6, False, ComputeDevice.CPU),
            "avatar": TaskProfile("Avatar Render", 0.2, 0.3, True, ComputeDevice.INTEL_IGPU),
            "stt": TaskProfile("Speech-to-Text", 0.0, 0.5, True, ComputeDevice.CPU),
            "memory": TaskProfile("Memory DB", 0.0, 0.2, False, ComputeDevice.CPU),
        }
        
        logger.info("Hybrid Load Balancer initialized.")
    
    def request_allocation(self, task_name: str) -> Optional[ComputeDevice]:
        """
        Request VRAM/resource allocation for a task.
        Returns the assigned device or None if resources unavailable.
        """
        profile = self.task_profiles.get(task_name)
        if not profile:
            logger.warning(f"Unknown task: {task_name}")
            return ComputeDevice.CPU
        
        with self.lock:
            # Check if NVIDIA can handle it
            if profile.preferred_device == ComputeDevice.NVIDIA_GPU:
                if self.nvidia_used + profile.vram_requirement <= self.nvidia_budget:
                    self.nvidia_used += profile.vram_requirement
                    self.active_tasks[task_name] = profile
                    logger.info(f"Allocated {task_name} to NVIDIA ({self.nvidia_used:.1f}/{self.nvidia_budget}GB)")
                    return ComputeDevice.NVIDIA_GPU
                else:
                    # Fallback
                    logger.warning(f"NVIDIA full. Falling back for {task_name}")
                    if profile.vram_requirement < 2.0:
                        return ComputeDevice.CPU
                    return None
            
            return profile.preferred_device
    
    def release(self, task_name: str):
        """Release resources when a task completes."""
        with self.lock:
            if task_name in self.active_tasks:
                profile = self.active_tasks.pop(task_name)
                if profile.preferred_device == ComputeDevice.NVIDIA_GPU:
                    self.nvidia_used -= profile.vram_requirement
                    self.nvidia_used = max(0, self.nvidia_used)
                logger.info(f"Released {task_name}. VRAM: {self.nvidia_used:.1f}/{self.nvidia_budget}GB")
    
    def get_status(self) -> Dict:
        """Get current resource status."""
        return {
            "nvidia_used_gb": self.nvidia_used,
            "nvidia_free_gb": self.nvidia_budget - self.nvidia_used,
            "nvidia_utilization": self.nvidia_used / self.nvidia_budget,
            "active_tasks": list(self.active_tasks.keys())
        }
    
    def can_run(self, task_name: str) -> bool:
        """Check if a task can run without allocation."""
        profile = self.task_profiles.get(task_name)
        if not profile:
            return False
        
        if profile.preferred_device == ComputeDevice.NVIDIA_GPU:
            return self.nvidia_used + profile.vram_requirement <= self.nvidia_budget
        return True
    
    def optimize_allocation(self):
        """
        Optimize current allocations - can unload low-priority tasks if needed.
        Called when a high-priority task needs resources.
        """
        # Find low-priority tasks that can be offloaded
        offload_candidates = []
        for task_name, profile in self.active_tasks.items():
            if not profile.latency_sensitive and profile.compute_intensity < 0.5:
                offload_candidates.append((task_name, profile))
        
        return offload_candidates
