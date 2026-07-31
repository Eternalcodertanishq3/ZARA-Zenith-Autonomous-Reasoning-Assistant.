"""
ZARA VRAM Governor
Strict VRAM budget enforcement to prevent OOM crashes.
"""
import logging
import threading
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ZARA_VRAM")

class QuantizationLevel(Enum):
    FP16 = "fp16"      # Full precision
    INT8 = "int8"      # 8-bit quantization
    INT4 = "int4"      # 4-bit quantization
    Q4_K_M = "q4_k_m"  # GGUF 4-bit
    Q5_K_M = "q5_k_m"  # GGUF 5-bit

@dataclass
class ModelConfig:
    name: str
    base_vram: float  # GB at FP16
    current_quantization: QuantizationLevel
    is_loaded: bool = False
    actual_vram: float = 0.0

class VRAMGovernor:
    """
    Strict VRAM budget controller for 6GB GPU.
    Manages model quantization and loading priorities.
    """
    
    def __init__(self, total_vram: float = 6.0, buffer: float = 0.5):
        self.total_vram = total_vram
        self.buffer = buffer  # Reserve for OS/Display
        self.available = total_vram - buffer
        self.allocated = 0.0
        self.lock = threading.Lock()
        
        # Model registry
        self.models: Dict[str, ModelConfig] = {
            "brain": ModelConfig("Qwen3-4B", 8.0, QuantizationLevel.Q5_K_M),
            "vision": ModelConfig("InternVL2-4B", 8.0, QuantizationLevel.INT4),
            "rvc": ModelConfig("RVC", 1.5, QuantizationLevel.FP16),
        }
        
        # Quantization multipliers (how much VRAM is reduced)
        self.quant_factors = {
            QuantizationLevel.FP16: 1.0,
            QuantizationLevel.INT8: 0.5,
            QuantizationLevel.INT4: 0.3,
            QuantizationLevel.Q4_K_M: 0.28,
            QuantizationLevel.Q5_K_M: 0.35,
        }
        
        logger.info(f"VRAM Governor: {self.available:.1f}GB available (buffer: {self.buffer}GB)")
    
    def estimate_vram(self, model_name: str, quant: QuantizationLevel) -> float:
        """Estimate VRAM usage for a model at given quantization."""
        model = self.models.get(model_name)
        if not model:
            return 0.0
        
        factor = self.quant_factors.get(quant, 1.0)
        return model.base_vram * factor
    
    def can_load(self, model_name: str) -> bool:
        """Check if we have room to load a model."""
        model = self.models.get(model_name)
        if not model:
            return False
        
        estimated = self.estimate_vram(model_name, model.current_quantization)
        return (self.allocated + estimated) <= self.available
    
    def allocate(self, model_name: str) -> bool:
        """
        Allocate VRAM for a model.
        Returns True if successful.
        """
        with self.lock:
            model = self.models.get(model_name)
            if not model:
                return False
            
            estimated = self.estimate_vram(model_name, model.current_quantization)
            
            if (self.allocated + estimated) > self.available:
                logger.warning(f"Cannot load {model_name}: would exceed budget")
                return False
            
            self.allocated += estimated
            model.is_loaded = True
            model.actual_vram = estimated
            
            logger.info(f"Allocated {model_name}: {estimated:.2f}GB (Total: {self.allocated:.2f}/{self.available:.2f}GB)")
            return True
    
    def deallocate(self, model_name: str):
        """Free VRAM when model is unloaded."""
        with self.lock:
            model = self.models.get(model_name)
            if model and model.is_loaded:
                self.allocated -= model.actual_vram
                self.allocated = max(0, self.allocated)
                model.is_loaded = False
                model.actual_vram = 0.0
                
                logger.info(f"Deallocated {model_name}. Free: {self.available - self.allocated:.2f}GB")
    
    def suggest_quantization(self, model_name: str) -> QuantizationLevel:
        """
        Suggest optimal quantization for available budget.
        """
        model = self.models.get(model_name)
        if not model:
            return QuantizationLevel.INT4
        
        free = self.available - self.allocated
        
        # Try from highest quality to lowest
        for quant in [QuantizationLevel.FP16, QuantizationLevel.INT8, 
                      QuantizationLevel.Q5_K_M, QuantizationLevel.INT4, 
                      QuantizationLevel.Q4_K_M]:
            estimated = self.estimate_vram(model_name, quant)
            if estimated <= free:
                return quant
        
        return QuantizationLevel.Q4_K_M  # Lowest
    
    def get_report(self) -> Dict:
        """Get detailed VRAM report."""
        report = {
            "total_vram": self.total_vram,
            "buffer": self.buffer,
            "available": self.available,
            "allocated": self.allocated,
            "free": self.available - self.allocated,
            "utilization": self.allocated / self.available if self.available > 0 else 0,
            "models": {}
        }
        
        for name, model in self.models.items():
            report["models"][name] = {
                "loaded": model.is_loaded,
                "vram": model.actual_vram,
                "quantization": model.current_quantization.value
            }
        
        return report
    
    def optimize_budget(self) -> List[str]:
        """
        Returns suggestions for freeing VRAM if needed.
        """
        suggestions = []
        
        if self.allocated > self.available * 0.9:
            suggestions.append("VRAM usage high. Consider unloading unused models.")
        
        for name, model in self.models.items():
            if model.is_loaded:
                lower_quant = self._get_lower_quant(model.current_quantization)
                if lower_quant:
                    savings = model.actual_vram - self.estimate_vram(name, lower_quant)
                    suggestions.append(f"Quantize {name} to {lower_quant.value} to save {savings:.2f}GB")
        
        return suggestions
    
    def _get_lower_quant(self, current: QuantizationLevel) -> Optional[QuantizationLevel]:
        """Get next lower quantization level."""
        order = [QuantizationLevel.FP16, QuantizationLevel.INT8, 
                 QuantizationLevel.Q5_K_M, QuantizationLevel.INT4, 
                 QuantizationLevel.Q4_K_M]
        try:
            idx = order.index(current)
            if idx < len(order) - 1:
                return order[idx + 1]
        except ValueError:
            pass
        return None
