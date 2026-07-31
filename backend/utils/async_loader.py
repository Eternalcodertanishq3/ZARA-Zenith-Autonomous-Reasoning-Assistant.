"""
ZARA Async Model Loader
=======================
Utility for loading heavy models and components in parallel to improve startup time.
"""

import logging
import time
import threading
from typing import Dict, Any, Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future, wait, ALL_COMPLETED
from dataclasses import dataclass, field

logger = logging.getLogger("ZARA_LOADER")

@dataclass
class ComponentStatus:
    name: str
    status: str  # "pending", "loading", "ready", "failed"
    load_time: float = 0.0
    error: Optional[str] = None
    instance: Any = None

class AsyncModelLoader:
    """
    Manages parallel loading of heavy components (LLM, Voice, Vision, etc.).
    """
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: Dict[str, Future] = {}
        self.components: Dict[str, ComponentStatus] = {}
        self.lock = threading.RLock()
        self._start_time = 0.0
        
    def register_loader(self, name: str, factory_fn: Callable[[], Any]):
        """
        Register a component to be loaded.
        
        Args:
            name: Unique name of the component
            factory_fn: Function that returns the initialized component
        """
        with self.lock:
            self.components[name] = ComponentStatus(name=name, status="pending")
            
            # Submit to executor
            logger.info(f"⏳ Scheduled load: {name}")
            future = self.executor.submit(self._load_wrapper, name, factory_fn)
            self.futures[name] = future

    def _load_wrapper(self, name: str, factory_fn: Callable[[], Any]) -> Any:
        """Internal wrapper to track load time and status."""
        start = time.time()
        with self.lock:
            self.components[name].status = "loading"
            
        try:
            instance = factory_fn()
            
            end = time.time()
            duration = end - start
            
            with self.lock:
                status = self.components[name]
                status.status = "ready"
                status.load_time = duration
                status.instance = instance
                
            logger.info(f"✅ Loaded {name} in {duration:.2f}s")
            return instance
            
        except Exception as e:
            end = time.time()
            duration = end - start
            
            with self.lock:
                status = self.components[name]
                status.status = "failed"
                status.error = str(e)
                status.load_time = duration
                
            logger.error(f"❌ Failed to load {name}: {e}")
            raise

    def wait_for_all(self, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Wait for all registered components to finish loading.
        
        Returns:
            Dictionary of {name: instance} for successfully loaded components.
        """
        if not self.futures:
            return {}
            
        logger.info(f"Waiting for {len(self.futures)} components to load...")
        
        # Wait for completion
        done, not_done = wait(self.futures.values(), timeout=timeout, return_when=ALL_COMPLETED)
        
        results = {}
        
        # Collect results (even if we timed out, get what we have)
        with self.lock:
            for name, status in self.components.items():
                if status.status == "ready":
                    results[name] = status.instance
                elif status.status == "failed":
                    logger.warning(f"Skipping failed component: {name}")
                elif status.status == "loading":
                    logger.warning(f"Component timed out: {name}")
                    
        return results

    def get_progress(self) -> Dict[str, Any]:
        """Get current loading progress."""
        with self.lock:
            total = len(self.components)
            if total == 0:
                return {"progress": 1.0, "details": []}
                
            ready = sum(1 for c in self.components.values() if c.status == "ready")
            failed = sum(1 for c in self.components.values() if c.status == "failed")
            
            return {
                "progress": (ready + failed) / total,
                "completed": ready,
                "failed": failed,
                "total": total,
                "details": [
                    {
                        "name": c.name, 
                        "status": c.status, 
                        "time": f"{c.load_time:.2f}s"
                    } 
                    for c in self.components.values()
                ]
            }

    def shutdown(self):
        """Clean up resources."""
        self.executor.shutdown(wait=False)
