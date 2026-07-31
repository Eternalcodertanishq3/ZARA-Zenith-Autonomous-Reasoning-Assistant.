"""
ZARA Priority Interrupt System
Handles emergency commands and immediate response requirements.
"""
import logging
import threading
import queue
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger("ZARA_INTERRUPT")

class InterruptPriority(Enum):
    CRITICAL = 0    # Immediate action (emergency stop)
    HIGH = 1        # User command override
    NORMAL = 2      # Standard processing
    LOW = 3         # Background tasks
    IDLE = 4        # Can be interrupted anytime

@dataclass
class InterruptSignal:
    priority: InterruptPriority
    action: str
    callback: Optional[Callable] = None
    payload: any = None

class PriorityInterrupt:
    """
    Manages interrupt signals for immediate response to critical commands.
    Ensures ZARA can always be stopped or redirected instantly.
    """
    
    def __init__(self):
        self.interrupt_queue = queue.PriorityQueue()
        self.current_priority = InterruptPriority.IDLE
        self.interrupt_flag = threading.Event()
        self.handlers: dict = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        # Register default handlers
        self._register_defaults()
        
        logger.info("Priority Interrupt System initialized.")
    
    def _register_defaults(self):
        """Register default interrupt handlers."""
        self.handlers["STOP"] = self._handle_stop
        self.handlers["PAUSE"] = self._handle_pause
        self.handlers["RESUME"] = self._handle_resume
        self.handlers["SHUTDOWN"] = self._handle_shutdown
    
    def register_handler(self, action: str, callback: Callable):
        """Register a custom interrupt handler."""
        self.handlers[action] = callback
    
    def signal(self, priority: InterruptPriority, action: str, payload=None):
        """
        Send an interrupt signal.
        """
        signal = InterruptSignal(priority, action, self.handlers.get(action), payload)
        
        # Priority queue uses first element for ordering
        self.interrupt_queue.put((priority.value, signal))
        
        if priority.value <= InterruptPriority.HIGH.value:
            self.interrupt_flag.set()
            logger.info(f"INTERRUPT: {action} (Priority: {priority.name})")
    
    def check_interrupt(self) -> Optional[InterruptSignal]:
        """
        Check if there's a pending interrupt.
        Called periodically by processing loops.
        """
        if self.interrupt_flag.is_set():
            try:
                _, signal = self.interrupt_queue.get_nowait()
                
                if self.interrupt_queue.empty():
                    self.interrupt_flag.clear()
                
                return signal
            except queue.Empty:
                self.interrupt_flag.clear()
        
        return None
    
    def should_interrupt(self, current_priority: InterruptPriority) -> bool:
        """
        Check if current task should be interrupted.
        """
        if self.interrupt_flag.is_set():
            try:
                priority_val, _ = self.interrupt_queue.queue[0]  # Peek
                return priority_val < current_priority.value
            except (IndexError, queue.Empty):
                pass
        return False
    
    def process_interrupts(self):
        """Process all pending interrupts."""
        while not self.interrupt_queue.empty():
            try:
                _, signal = self.interrupt_queue.get_nowait()
                
                if signal.callback:
                    try:
                        signal.callback(signal.payload)
                    except Exception as e:
                        logger.error(f"Interrupt handler error: {e}")
                else:
                    logger.warning(f"No handler for action: {signal.action}")
                    
            except queue.Empty:
                break
        
        self.interrupt_flag.clear()
    
    def _handle_stop(self, payload=None):
        """Handle emergency stop."""
        logger.critical("EMERGENCY STOP triggered!")
        # Set global stop flags
        self.is_running = False
    
    def _handle_pause(self, payload=None):
        """Handle pause command."""
        logger.info("System PAUSED by user.")
    
    def _handle_resume(self, payload=None):
        """Handle resume command."""
        logger.info("System RESUMED.")
    
    def _handle_shutdown(self, payload=None):
        """Handle graceful shutdown."""
        logger.info("Graceful SHUTDOWN initiated.")
        self.is_running = False
    
    def start_listener(self):
        """Start background interrupt listener."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        logger.info("Interrupt listener started.")
    
    def _listen_loop(self):
        """Background loop for processing interrupts."""
        while self.is_running:
            if self.interrupt_flag.wait(timeout=0.1):
                self.process_interrupts()
    
    # Convenience methods for common interrupts
    def emergency_stop(self):
        """Trigger emergency stop."""
        self.signal(InterruptPriority.CRITICAL, "STOP")
    
    def pause(self):
        """Pause processing."""
        self.signal(InterruptPriority.HIGH, "PAUSE")
    
    def resume(self):
        """Resume processing."""
        self.signal(InterruptPriority.NORMAL, "RESUME")
    
    def shutdown(self):
        """Initiate graceful shutdown."""
        self.signal(InterruptPriority.HIGH, "SHUTDOWN")
