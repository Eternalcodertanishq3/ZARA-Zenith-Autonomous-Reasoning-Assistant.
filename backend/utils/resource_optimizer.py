"""
ZARA Resource Optimizer - Human-Like Efficiency
================================================
Keeps all senses active while optimizing memory usage.
No unloading - ZARA sees, hears, thinks simultaneously.
"""

import gc
import logging
import threading
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ZARA_RESOURCES")

# Lazy imports
torch = None

def _lazy_load():
    global torch
    if torch is None:
        try:
            import torch as _torch
            torch = _torch
        except ImportError:
            pass


class DeviceType(Enum):
    GPU = "cuda"
    CPU = "cpu"
    AUTO = "auto"


@dataclass
class ResourceStats:
    """Current resource usage statistics."""
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    gpu_memory_free_mb: float
    gpu_utilization_percent: float
    cpu_memory_used_mb: float
    timestamp: float


class ResourceOptimizer:
    """
    Manages GPU/CPU resources for human-like simultaneous processing.
    
    Philosophy:
    - Keep core senses ALWAYS loaded (brain, ears, eyes)
    - Use FP16 for 50% VRAM savings
    - Offload light tasks to CPU
    - Cache responses for instant replies
    - Never unload essential components
    """
    
    # VRAM thresholds
    VRAM_WARNING_THRESHOLD_MB = 5500  # Warn at 5.5GB
    VRAM_CRITICAL_THRESHOLD_MB = 5800  # Critical at 5.8GB
    
    # Component priorities (higher = more important, never unload)
    PRIORITIES = {
        "brain": 100,      # Always on GPU
        "ears": 90,        # Always on GPU (listening)
        "yolo": 80,        # Always on GPU (seeing)
        "tts": 70,         # GPU when speaking
        "internvit": 50,   # CPU (light)
        "gaze": 30,        # CPU
        "depth": 30,       # CPU
        "face_id": 20,     # CPU
    }
    
    # Device assignments
    DEVICE_MAP = {
        "brain": DeviceType.GPU,
        "ears": DeviceType.GPU,
        "yolo": DeviceType.GPU,
        "tts": DeviceType.GPU,
        "internvit": DeviceType.CPU,  # Light enough for CPU
        "gaze": DeviceType.CPU,
        "depth": DeviceType.CPU,
        "face_id": DeviceType.CPU,
        "mediapipe": DeviceType.CPU,
        "wake_word": DeviceType.CPU,
    }
    
    def __init__(self):
        _lazy_load()
        
        self.is_initialized = False
        self.lock = threading.Lock()
        
        # Response cache for instant replies
        self.response_cache: Dict[str, Any] = {}
        self.cache_max_size = 100
        self.cache_ttl = 300  # 5 minutes
        
        # Stats tracking
        self.last_stats: Optional[ResourceStats] = None
        self.stats_interval = 5.0
        
        # FP16 optimization flag
        self.use_fp16 = True
        
        logger.info("Resource Optimizer initialized.")
    
    def get_optimal_device(self, component: str) -> str:
        """Get the optimal device for a component."""
        device_type = self.DEVICE_MAP.get(component, DeviceType.CPU)
        
        if device_type == DeviceType.GPU:
            if torch and torch.cuda.is_available():
                return "cuda"
        
        return "cpu"
    
    def get_optimal_dtype(self, component: str):
        """Get optimal data type (FP16 for GPU, FP32 for CPU)."""
        if not torch:
            return None
        
        device = self.get_optimal_device(component)
        
        if device == "cuda" and self.use_fp16:
            return torch.float16
        else:
            return torch.float32
    
    def get_gpu_stats(self) -> Optional[ResourceStats]:
        """Get current GPU memory statistics."""
        if torch is None or not torch.cuda.is_available():
            return None
        
        try:
            gpu_mem = torch.cuda.memory_allocated() / (1024 * 1024)
            gpu_total = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
            gpu_free = gpu_total - gpu_mem
            
            # Try to get utilization (may not be available)
            gpu_util = 0.0
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = util.gpu
            except:
                pass
            
            import psutil
            cpu_mem = psutil.Process().memory_info().rss / (1024 * 1024)
            
            stats = ResourceStats(
                gpu_memory_used_mb=gpu_mem,
                gpu_memory_total_mb=gpu_total,
                gpu_memory_free_mb=gpu_free,
                gpu_utilization_percent=gpu_util,
                cpu_memory_used_mb=cpu_mem,
                timestamp=time.time()
            )
            
            self.last_stats = stats
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get GPU stats: {e}")
            return None
    
    def optimize_memory(self):
        """Run garbage collection and clear CUDA cache."""
        gc.collect()
        
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.debug("GPU cache cleared.")
    
    def check_vram_health(self) -> bool:
        """Check if VRAM usage is healthy."""
        stats = self.get_gpu_stats()
        if stats is None:
            return True
        
        if stats.gpu_memory_used_mb > self.VRAM_CRITICAL_THRESHOLD_MB:
            logger.warning(f"⚠️ CRITICAL VRAM: {stats.gpu_memory_used_mb:.0f}MB used!")
            self.optimize_memory()
            return False
        
        if stats.gpu_memory_used_mb > self.VRAM_WARNING_THRESHOLD_MB:
            logger.info(f"VRAM usage high: {stats.gpu_memory_used_mb:.0f}MB")
        
        return True
    
    def cache_response(self, query: str, response: Any):
        """Cache a response for fast retrieval."""
        with self.lock:
            # Simple LRU - remove oldest if full
            if len(self.response_cache) >= self.cache_max_size:
                oldest = min(self.response_cache.keys())
                del self.response_cache[oldest]
            
            self.response_cache[query] = {
                "response": response,
                "timestamp": time.time()
            }
    
    def get_cached_response(self, query: str) -> Optional[Any]:
        """Get cached response if available and fresh."""
        with self.lock:
            if query in self.response_cache:
                cached = self.response_cache[query]
                age = time.time() - cached["timestamp"]
                
                if age < self.cache_ttl:
                    logger.debug(f"Cache hit for query (age: {age:.1f}s)")
                    return cached["response"]
                else:
                    del self.response_cache[query]
        
        return None
    
    def get_status(self) -> Dict:
        """Get resource optimizer status."""
        stats = self.get_gpu_stats()
        
        return {
            "gpu_available": torch is not None and torch.cuda.is_available(),
            "gpu_memory_mb": stats.gpu_memory_used_mb if stats else 0,
            "gpu_free_mb": stats.gpu_memory_free_mb if stats else 0,
            "cpu_memory_mb": stats.cpu_memory_used_mb if stats else 0,
            "cache_size": len(self.response_cache),
            "fp16_enabled": self.use_fp16,
            "device_map": {k: v.value for k, v in self.DEVICE_MAP.items()}
        }
    
    def log_resource_report(self):
        """Log a detailed resource report."""
        stats = self.get_gpu_stats()
        if stats:
            logger.info(f"📊 GPU: {stats.gpu_memory_used_mb:.0f}MB / {stats.gpu_memory_total_mb:.0f}MB "
                       f"({stats.gpu_memory_used_mb/stats.gpu_memory_total_mb*100:.1f}%)")
            logger.info(f"📊 CPU RAM: {stats.cpu_memory_used_mb:.0f}MB")


# Global instance
_optimizer: Optional[ResourceOptimizer] = None

def get_optimizer() -> ResourceOptimizer:
    """Get or create the global resource optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = ResourceOptimizer()
    return _optimizer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    optimizer = get_optimizer()
    optimizer.log_resource_report()
    
    print("\nDevice assignments:")
    for component, device in ResourceOptimizer.DEVICE_MAP.items():
        print(f"  {component}: {device.value}")
