"""
ZARA Energy Saver
Reduces resource usage when user is not actively engaged.
"""
import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger("ZARA_POWER")

class PowerState(Enum):
    FULL = "full"          # Maximum responsiveness
    BALANCED = "balanced"  # Normal operation
    SAVING = "saving"      # Reduced resources
    SLEEP = "sleep"        # Minimal activity

class EnergySaver:
    """
    Manages power states and reduces resource usage when appropriate.
    Monitors user attention to adjust system activity.
    """
    
    def __init__(self):
        self.current_state = PowerState.BALANCED
        self.last_interaction = time.time()
        self.idle_timeout = 60  # seconds before going to SAVING
        self.sleep_timeout = 300  # seconds before SLEEP
        self.is_monitoring = False
        self.lock = threading.Lock()
        
        # Callbacks for state changes
        self.state_callbacks: dict = {}
        
        # Configuration per state
        self.state_configs = {
            PowerState.FULL: {
                "fps": 60,
                "vision_interval": 0.033,  # ~30 FPS
                "audio_buffer_size": 1024,
                "model_keep_alive": True
            },
            PowerState.BALANCED: {
                "fps": 30,
                "vision_interval": 0.1,
                "audio_buffer_size": 2048,
                "model_keep_alive": True
            },
            PowerState.SAVING: {
                "fps": 15,
                "vision_interval": 0.5,
                "audio_buffer_size": 4096,
                "model_keep_alive": True
            },
            PowerState.SLEEP: {
                "fps": 5,
                "vision_interval": 2.0,
                "audio_buffer_size": 8192,
                "model_keep_alive": False
            }
        }
        
        logger.info("Energy Saver initialized.")
    
    def register_callback(self, state: PowerState, callback: Callable):
        """Register a callback for when entering a state."""
        self.state_callbacks[state] = callback
    
    def record_interaction(self):
        """Record that user interacted (resets idle timer)."""
        with self.lock:
            self.last_interaction = time.time()
            if self.current_state != PowerState.FULL:
                self._transition_to(PowerState.BALANCED)
    
    def record_attention(self, is_looking: bool):
        """Record whether user is looking at screen."""
        if is_looking:
            self.record_interaction()
    
    def get_config(self, key: str):
        """Get current configuration value."""
        config = self.state_configs.get(self.current_state, {})
        return config.get(key)
    
    def _transition_to(self, new_state: PowerState):
        """Internal state transition."""
        if new_state == self.current_state:
            return
        
        old_state = self.current_state
        self.current_state = new_state
        
        logger.info(f"Power State: {old_state.value} → {new_state.value}")
        
        # Execute callback if registered
        if new_state in self.state_callbacks:
            try:
                self.state_callbacks[new_state]()
            except Exception as e:
                logger.error(f"State callback error: {e}")
    
    def start_monitoring(self):
        """Start background thread for idle monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        logger.info("Power monitoring started.")
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
    
    def _monitor_loop(self):
        """Background loop to check idle state."""
        while self.is_monitoring:
            idle_time = time.time() - self.last_interaction
            
            with self.lock:
                if idle_time > self.sleep_timeout:
                    self._transition_to(PowerState.SLEEP)
                elif idle_time > self.idle_timeout:
                    self._transition_to(PowerState.SAVING)
            
            time.sleep(10)  # Check every 10 seconds
    
    def force_state(self, state: PowerState):
        """Force transition to a specific state."""
        with self.lock:
            self._transition_to(state)
    
    def wake_up(self):
        """Wake from sleep state."""
        self.record_interaction()
        self._transition_to(PowerState.FULL)
    
    def get_status(self) -> dict:
        """Get current power status."""
        idle_time = time.time() - self.last_interaction
        return {
            "state": self.current_state.value,
            "idle_seconds": idle_time,
            "until_saving": max(0, self.idle_timeout - idle_time),
            "until_sleep": max(0, self.sleep_timeout - idle_time),
            "config": self.state_configs.get(self.current_state, {})
        }
