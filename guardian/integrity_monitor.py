"""
ZARA Guardian Monitor - Enhanced System Health Monitoring
"""
import logging
import time
import threading
import psutil
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger("ZARA_GUARDIAN")


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemVitals:
    """Complete system health snapshot."""
    timestamp: float
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    gpu_temp: float
    gpu_load: float
    gpu_memory_used: float
    gpu_memory_total: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    status: HealthStatus
    warnings: List[str] = field(default_factory=list)


class GuardianMonitor:
    """
    Advanced system health monitor with:
    - Continuous background monitoring
    - Trend analysis
    - Predictive warnings
    - Resource throttling recommendations
    - Alert callbacks
    """
    
    # Thresholds
    CPU_WARNING = 85
    CPU_CRITICAL = 95
    RAM_WARNING = 85
    RAM_CRITICAL = 95
    GPU_TEMP_WARNING = 80
    GPU_TEMP_CRITICAL = 90
    GPU_MEM_WARNING = 90
    DISK_WARNING = 90
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.check_interval = 5.0  # seconds
        
        # History for trend analysis
        self.cpu_history = deque(maxlen=60)
        self.ram_history = deque(maxlen=60)
        self.gpu_temp_history = deque(maxlen=60)
        
        # Callbacks
        self.on_warning: Optional[Callable[[str], None]] = None
        self.on_critical: Optional[Callable[[str], None]] = None
        
        # Last vitals
        self.last_vitals: Optional[SystemVitals] = None
        
        # Network baseline
        self._net_baseline = psutil.net_io_counters()

    def check_vitals(self) -> SystemVitals:
        """Get comprehensive system health snapshot."""
        warnings = []
        status = HealthStatus.HEALTHY
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_percent)
        
        if cpu_percent > self.CPU_CRITICAL:
            status = HealthStatus.CRITICAL
            warnings.append(f"CPU Critical: {cpu_percent:.1f}%")
        elif cpu_percent > self.CPU_WARNING:
            status = HealthStatus.WARNING
            warnings.append(f"CPU High: {cpu_percent:.1f}%")
        
        # RAM
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        self.ram_history.append(ram_percent)
        
        if ram_percent > self.RAM_CRITICAL:
            status = HealthStatus.CRITICAL
            warnings.append(f"RAM Critical: {ram_percent:.1f}%")
        elif ram_percent > self.RAM_WARNING:
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING
            warnings.append(f"RAM High: {ram_percent:.1f}%")
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        if disk_percent > self.DISK_WARNING:
            warnings.append(f"Disk usage high: {disk_percent:.1f}%")
        
        # Network
        net = psutil.net_io_counters()
        net_sent_mb = (net.bytes_sent - self._net_baseline.bytes_sent) / (1024**2)
        net_recv_mb = (net.bytes_recv - self._net_baseline.bytes_recv) / (1024**2)
        
        # GPU
        gpu_temp = 0.0
        gpu_load = 0.0
        gpu_mem_used = 0.0
        gpu_mem_total = 0.0
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_temp = gpu.temperature
                gpu_load = gpu.load * 100
                gpu_mem_used = gpu.memoryUsed
                gpu_mem_total = gpu.memoryTotal
                
                self.gpu_temp_history.append(gpu_temp)
                
                if gpu_temp > self.GPU_TEMP_CRITICAL:
                    status = HealthStatus.CRITICAL
                    warnings.append(f"GPU Overheating: {gpu_temp}°C")
                elif gpu_temp > self.GPU_TEMP_WARNING:
                    if status != HealthStatus.CRITICAL:
                        status = HealthStatus.WARNING
                    warnings.append(f"GPU Warm: {gpu_temp}°C")
                
                if gpu_mem_total > 0:
                    gpu_mem_percent = (gpu_mem_used / gpu_mem_total) * 100
                    if gpu_mem_percent > self.GPU_MEM_WARNING:
                        warnings.append(f"GPU VRAM High: {gpu_mem_percent:.1f}%")
        except ImportError:
            pass  # GPUtil not installed
        
        vitals = SystemVitals(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            gpu_temp=gpu_temp,
            gpu_load=gpu_load,
            gpu_memory_used=gpu_mem_used,
            gpu_memory_total=gpu_mem_total,
            disk_percent=disk_percent,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            status=status,
            warnings=warnings
        )
        
        self.last_vitals = vitals
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        return vitals

    def get_trend_analysis(self) -> Dict:
        """Analyze resource usage trends."""
        analysis = {
            "cpu_trend": "stable",
            "ram_trend": "stable",
            "gpu_trend": "stable",
            "recommendations": []
        }
        
        # CPU trend
        if len(self.cpu_history) >= 10:
            recent = list(self.cpu_history)[-10:]
            older = list(self.cpu_history)[-20:-10] if len(self.cpu_history) >= 20 else recent
            
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            
            if recent_avg > older_avg + 10:
                analysis["cpu_trend"] = "rising"
                analysis["recommendations"].append("CPU usage increasing. Consider closing background apps.")
            elif recent_avg < older_avg - 10:
                analysis["cpu_trend"] = "falling"
        
        # RAM trend
        if len(self.ram_history) >= 10:
            recent = list(self.ram_history)[-5:]
            recent_avg = sum(recent) / len(recent)
            
            if recent_avg > 80:
                analysis["ram_trend"] = "high"
                analysis["recommendations"].append("RAM usage high. Memory-intensive operations may be slow.")
        
        # GPU temperature trend
        if len(self.gpu_temp_history) >= 10:
            recent = list(self.gpu_temp_history)[-5:]
            recent_avg = sum(recent) / len(recent)
            
            if recent_avg > 75:
                analysis["gpu_trend"] = "warming"
                analysis["recommendations"].append("GPU running warm. Ensure adequate cooling.")
        
        return analysis

    def start_monitoring(self, interval: float = 5.0):
        """Start background monitoring thread."""
        if self.is_monitoring:
            return
        
        self.check_interval = interval
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Guardian monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop background monitoring."""
        self.is_monitoring = False
        logger.info("Guardian monitoring stopped.")

    def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.is_monitoring:
            try:
                vitals = self.check_vitals()
                
                # Trigger callbacks
                for warning in vitals.warnings:
                    if vitals.status == HealthStatus.CRITICAL and self.on_critical:
                        self.on_critical(warning)
                    elif vitals.status == HealthStatus.WARNING and self.on_warning:
                        self.on_warning(warning)
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(self.check_interval)

    def get_summary(self) -> str:
        """Get human-readable health summary."""
        vitals = self.last_vitals or self.check_vitals()
        
        lines = [
            f"System Status: {vitals.status.value.upper()}",
            f"CPU: {vitals.cpu_percent:.1f}%",
            f"RAM: {vitals.ram_used_gb:.1f}/{vitals.ram_total_gb:.1f} GB ({vitals.ram_percent:.1f}%)",
        ]
        
        if vitals.gpu_temp > 0:
            lines.append(f"GPU: {vitals.gpu_temp:.0f}°C, {vitals.gpu_load:.1f}% load")
            lines.append(f"VRAM: {vitals.gpu_memory_used:.0f}/{vitals.gpu_memory_total:.0f} MB")
        
        if vitals.warnings:
            lines.append(f"Warnings: {', '.join(vitals.warnings)}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    guardian = GuardianMonitor()
    
    print("System Health Check:")
    print("=" * 40)
    print(guardian.get_summary())
    print("\nTrend Analysis:")
    print(guardian.get_trend_analysis())
