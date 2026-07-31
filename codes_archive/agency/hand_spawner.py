"""
ZARA Multi-Agent Hand Spawner v1.0
===================================
Dynamic Agent Creation and Coordination

This module implements ZARA's ability to dynamically spawn specialized
sub-agents ("hands") for parallel work:

1. Recursive Spawning: Create specialized hands on demand
2. Dynamic Load Balancing: Distribute work efficiently
3. Sub-Symbolic Communication: Exchange embeddings instead of text
4. JIT Tooling: Generate custom tools on the fly
5. Permanent Skill Upgrading: Absorb successful hand-created tools
6. Background Evolution: Continuous improvement

These "hands" are like specialist workers that ZARA can create, direct,
and absorb abilities from.
"""

import logging
import threading
import time
import json
import hashlib
import queue
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, Future
import traceback

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_HAND_SPAWNER")


# ═══════════════════════════════════════════════════════════════════════════
# HAND TYPES
# ═══════════════════════════════════════════════════════════════════════════

class HandType(Enum):
    """Types of specialized hands that can be spawned."""
    CODER = "coder"             # Write and modify code
    RESEARCHER = "researcher"   # Search and synthesize information
    ANALYZER = "analyzer"       # Deep analysis of data/code
    EXECUTOR = "executor"       # Run commands and tools
    WATCHER = "watcher"         # Monitor and report on processes
    CREATIVE = "creative"       # Generate creative content
    DEBUGGER = "debugger"       # Find and fix bugs
    OPTIMIZER = "optimizer"     # Improve performance
    INTEGRATOR = "integrator"   # Combine and integrate components


class HandStatus(Enum):
    """Status of a spawned hand."""
    SPAWNING = "spawning"
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class TaskPriority(Enum):
    """Priority levels for hand tasks."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


# ═══════════════════════════════════════════════════════════════════════════
# SUB-SYMBOLIC COMMUNICATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EmbeddingMessage:
    """
    A sub-symbolic message using embeddings instead of text.
    Much faster than parsing text between agents.
    """
    id: str
    from_hand: str
    to_hand: str
    embedding: List[float]          # High-dimensional vector
    message_type: str               # "task", "result", "query", "update"
    metadata: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_text_hint(self) -> str:
        """Get a human-readable hint of what this embedding represents."""
        return self.metadata.get("text_hint", "[embedding data]")


class EmbeddingBus:
    """
    Communication bus for sub-symbolic message passing.
    Hands exchange embeddings instead of text for speed.
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.queues: Dict[str, queue.Queue] = {}
        self.broadcast_listeners: List[Callable[[EmbeddingMessage], None]] = []
        self.lock = threading.Lock()
        self.message_history: deque = deque(maxlen=1000)
    
    def register_hand(self, hand_id: str):
        """Register a hand to receive messages."""
        with self.lock:
            if hand_id not in self.queues:
                self.queues[hand_id] = queue.Queue()
    
    def unregister_hand(self, hand_id: str):
        """Unregister a hand."""
        with self.lock:
            if hand_id in self.queues:
                del self.queues[hand_id]
    
    def send(self, message: EmbeddingMessage):
        """Send a message to a specific hand."""
        with self.lock:
            if message.to_hand in self.queues:
                self.queues[message.to_hand].put(message)
                self.message_history.append(message)
    
    def broadcast(self, message: EmbeddingMessage):
        """Broadcast a message to all hands."""
        with self.lock:
            for hand_id, q in self.queues.items():
                if hand_id != message.from_hand:
                    q.put(message)
            
            for listener in self.broadcast_listeners:
                try:
                    listener(message)
                except Exception as e:
                    logger.error(f"Broadcast listener error: {e}")
    
    def receive(self, hand_id: str, timeout: float = 0.1) -> Optional[EmbeddingMessage]:
        """Receive a message for a hand."""
        if hand_id not in self.queues:
            return None
        
        try:
            return self.queues[hand_id].get(timeout=timeout)
        except queue.Empty:
            return None
    
    def text_to_embedding(self, text: str) -> List[float]:
        """Convert text to an embedding (simplified mock)."""
        # In production, this would use a real embedding model
        import hashlib
        hash_bytes = hashlib.sha384(text.encode()).digest()
        # Convert bytes to floats in [-1, 1]
        return [(b - 128) / 128 for b in hash_bytes]
    
    def embedding_similarity(self, e1: List[float], e2: List[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        dot = sum(a * b for a, b in zip(e1, e2))
        norm1 = sum(a * a for a in e1) ** 0.5
        norm2 = sum(b * b for b in e2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot / (norm1 * norm2)


# ═══════════════════════════════════════════════════════════════════════════
# HAND TASK
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class HandTask:
    """A task assigned to a hand."""
    id: str
    description: str
    hand_type: HandType
    priority: TaskPriority
    
    # Input/Output
    input_data: Any = None
    output_data: Any = None
    
    # Status
    status: str = "pending"
    progress: float = 0.0
    error: Optional[str] = None
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    # Generated artifacts
    artifacts: List[str] = field(default_factory=list)
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return time.time() - self.started_at
        return None


# ═══════════════════════════════════════════════════════════════════════════
# SPAWNED HAND
# ═══════════════════════════════════════════════════════════════════════════

class SpawnedHand:
    """
    A dynamically spawned specialized agent.
    Each hand has specific capabilities and can work independently.
    """
    
    def __init__(self, hand_id: str, hand_type: HandType, bus: EmbeddingBus):
        self.id = hand_id
        self.type = hand_type
        self.bus = bus
        self.status = HandStatus.SPAWNING
        
        # Task management
        self.current_task: Optional[HandTask] = None
        self.completed_tasks: List[HandTask] = []
        
        # Capabilities (can be specialized)
        self.capabilities: Dict[str, float] = self._init_capabilities()
        
        # Work thread
        self.running = False
        self.work_thread: Optional[threading.Thread] = None
        
        # JIT tools created by this hand
        self.created_tools: List[Dict] = []
        
        # Stats
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_work_time = 0
        
        # Register with bus
        self.bus.register_hand(self.id)
        
        logger.info(f"🖐️ Hand spawned: {self.id} ({self.type.value})")
    
    def _init_capabilities(self) -> Dict[str, float]:
        """Initialize capabilities based on hand type."""
        base = {
            "execute_command": 0.5,
            "write_code": 0.3,
            "analyze_data": 0.3,
            "search_info": 0.3,
            "creative_work": 0.2,
        }
        
        # Specialize based on type
        specializations = {
            HandType.CODER: {"write_code": 0.9, "analyze_data": 0.6},
            HandType.RESEARCHER: {"search_info": 0.9, "analyze_data": 0.7},
            HandType.ANALYZER: {"analyze_data": 0.9, "write_code": 0.5},
            HandType.EXECUTOR: {"execute_command": 0.9},
            HandType.CREATIVE: {"creative_work": 0.9, "write_code": 0.5},
            HandType.DEBUGGER: {"analyze_data": 0.8, "write_code": 0.7},
            HandType.OPTIMIZER: {"analyze_data": 0.7, "write_code": 0.8},
        }
        
        if self.type in specializations:
            base.update(specializations[self.type])
        
        return base
    
    def start(self):
        """Start the hand's work thread."""
        if self.running:
            return
        
        self.running = True
        self.status = HandStatus.IDLE
        self.work_thread = threading.Thread(target=self._work_loop, daemon=True)
        self.work_thread.start()
    
    def stop(self):
        """Stop the hand."""
        self.running = False
        self.status = HandStatus.TERMINATED
        self.bus.unregister_hand(self.id)
        if self.work_thread:
            self.work_thread.join(timeout=2)
    
    def _work_loop(self):
        """Main work loop for the hand."""
        while self.running:
            try:
                # Check for incoming messages
                msg = self.bus.receive(self.id, timeout=0.1)
                if msg:
                    self._handle_message(msg)
                
                # Work on current task
                if self.current_task and self.status == HandStatus.WORKING:
                    self._work_on_task()
                
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Hand {self.id} work loop error: {e}")
                time.sleep(0.5)
    
    def _handle_message(self, msg: EmbeddingMessage):
        """Handle an incoming message."""
        if msg.message_type == "task":
            # New task assignment
            task_data = msg.metadata.get("task")
            if task_data:
                logger.debug(f"Hand {self.id} received task: {task_data.get('description', 'unknown')}")
        
        elif msg.message_type == "query":
            # Respond to query
            self._respond_to_query(msg)
    
    def _respond_to_query(self, query: EmbeddingMessage):
        """Respond to a query from another hand or main."""
        response = EmbeddingMessage(
            id=f"resp_{query.id}",
            from_hand=self.id,
            to_hand=query.from_hand,
            embedding=self.bus.text_to_embedding(f"status: {self.status.value}"),
            message_type="response",
            metadata={"status": self.status.value, "progress": self.current_task.progress if self.current_task else 0}
        )
        self.bus.send(response)
    
    def assign_task(self, task: HandTask):
        """Assign a task to this hand."""
        self.current_task = task
        self.current_task.status = "in_progress"
        self.current_task.started_at = time.time()
        self.status = HandStatus.WORKING
    
    def _work_on_task(self):
        """Work on the current task."""
        if not self.current_task:
            return
        
        task = self.current_task
        
        # Simulate work (in real implementation, this would do actual work)
        task.progress += 0.1
        
        if task.progress >= 1.0:
            self._complete_task(True)
    
    def _complete_task(self, success: bool, output: Any = None, error: str = None):
        """Complete the current task."""
        if not self.current_task:
            return
        
        task = self.current_task
        task.completed_at = time.time()
        task.output_data = output
        task.error = error
        task.status = "completed" if success else "failed"
        task.progress = 1.0 if success else task.progress
        
        duration = task.get_duration() or 0
        self.total_work_time += duration
        
        if success:
            self.tasks_completed += 1
            self.completed_tasks.append(task)
        else:
            self.tasks_failed += 1
        
        # Notify completion
        result_msg = EmbeddingMessage(
            id=f"result_{task.id}",
            from_hand=self.id,
            to_hand="main",
            embedding=self.bus.text_to_embedding(f"Task completed: {task.description[:50]}"),
            message_type="result",
            metadata={"task_id": task.id, "success": success, "output": output}
        )
        self.bus.broadcast(result_msg)
        
        self.current_task = None
        self.status = HandStatus.IDLE
        
        logger.info(f"🖐️ Hand {self.id} completed task: {task.id} (success={success})")
    
    def create_jit_tool(self, tool_name: str, tool_code: str) -> Dict:
        """Create a just-in-time tool."""
        tool = {
            "name": tool_name,
            "code": tool_code,
            "created_by": self.id,
            "created_at": time.time(),
            "usage_count": 0
        }
        self.created_tools.append(tool)
        return tool


# ═══════════════════════════════════════════════════════════════════════════
# HAND SPAWNER (Main Controller)
# ═══════════════════════════════════════════════════════════════════════════

class HandSpawner:
    """
    The main controller for spawning and managing hands.
    This is ZARA's ability to create specialized workers.
    """
    
    def __init__(self, max_hands: int = 10):
        self.max_hands = max_hands
        
        # Communication bus
        self.bus = EmbeddingBus()
        
        # Active hands
        self.hands: Dict[str, SpawnedHand] = {}
        
        # Task queue
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, HandTask] = {}
        self.completed_tasks: deque = deque(maxlen=100)
        
        # Skill library (absorbed from hands)
        self.skill_library: Dict[str, Dict] = {}
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_hands)
        
        # Background processing
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_task_complete: List[Callable[[HandTask], None]] = []
        self.on_skill_absorbed: List[Callable[[Dict], None]] = []
        
        # Stats
        self.total_spawned = 0
        self.total_terminated = 0
        
        logger.info("🤖 Hand Spawner initialized")
    
    def start(self):
        """Start the hand spawner."""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("🤖 Hand Spawner started")
    
    def stop(self):
        """Stop all hands and the spawner."""
        self.running = False
        
        # Stop all hands
        for hand in list(self.hands.values()):
            hand.stop()
        
        self.hands.clear()
        self.executor.shutdown(wait=False)
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        
        logger.info("🤖 Hand Spawner stopped")
    
    def _scheduler_loop(self):
        """Background loop for scheduling tasks to hands."""
        while self.running:
            try:
                # Check for completed tasks
                self._collect_completed_tasks()
                
                # Assign queued tasks to idle hands
                self._assign_pending_tasks()
                
                # Load balancing
                self._balance_load()
                
                # Absorb skills from successful hands
                self._absorb_skills()
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(0.5)
    
    def _collect_completed_tasks(self):
        """Collect completed tasks from hands."""
        with self.lock:
            for hand in self.hands.values():
                for task in hand.completed_tasks:
                    if task.id in self.active_tasks:
                        del self.active_tasks[task.id]
                        self.completed_tasks.append(task)
                        
                        for callback in self.on_task_complete:
                            try:
                                callback(task)
                            except Exception as e:
                                logger.error(f"Task callback error: {e}")
                
                hand.completed_tasks.clear()
    
    def _assign_pending_tasks(self):
        """Assign pending tasks to idle hands."""
        with self.lock:
            while not self.task_queue.empty():
                try:
                    _, task = self.task_queue.get_nowait()
                except queue.Empty:
                    break
                
                # Find suitable idle hand
                suitable_hand = self._find_suitable_hand(task)
                
                if suitable_hand:
                    suitable_hand.assign_task(task)
                    self.active_tasks[task.id] = task
                elif len(self.hands) < self.max_hands:
                    # Spawn a new hand
                    new_hand = self.spawn_hand(task.hand_type)
                    new_hand.assign_task(task)
                    self.active_tasks[task.id] = task
                else:
                    # Put task back
                    self.task_queue.put((task.priority.value, task))
                    break
    
    def _find_suitable_hand(self, task: HandTask) -> Optional[SpawnedHand]:
        """Find an idle hand suitable for the task."""
        for hand in self.hands.values():
            if hand.status == HandStatus.IDLE and hand.type == task.hand_type:
                return hand
        return None
    
    def _balance_load(self):
        """Balance load by terminating idle hands or spawning new ones."""
        with self.lock:
            # Count idle hands
            idle_count = sum(1 for h in self.hands.values() if h.status == HandStatus.IDLE)
            
            # If too many idle hands, terminate some
            if idle_count > 3:
                for hand_id, hand in list(self.hands.items()):
                    if hand.status == HandStatus.IDLE:
                        self.terminate_hand(hand_id)
                        idle_count -= 1
                        if idle_count <= 2:
                            break
    
    def _absorb_skills(self):
        """Absorb successful JIT tools into the skill library."""
        with self.lock:
            for hand in self.hands.values():
                for tool in hand.created_tools:
                    if tool["usage_count"] >= 3:  # Tool has proven useful
                        skill_id = hashlib.md5(tool["code"].encode()).hexdigest()[:12]
                        
                        if skill_id not in self.skill_library:
                            self.skill_library[skill_id] = {
                                "name": tool["name"],
                                "code": tool["code"],
                                "absorbed_from": hand.id,
                                "absorbed_at": time.time()
                            }
                            
                            for callback in self.on_skill_absorbed:
                                try:
                                    callback(tool)
                                except Exception as e:
                                    logger.error(f"Skill callback error: {e}")
                            
                            logger.info(f"📚 Absorbed skill: {tool['name']}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════
    
    def spawn_hand(self, hand_type: HandType, custom_id: str = None) -> SpawnedHand:
        """Spawn a new specialized hand."""
        with self.lock:
            if len(self.hands) >= self.max_hands:
                raise RuntimeError(f"Maximum hands ({self.max_hands}) reached")
            
            hand_id = custom_id or f"{hand_type.value}_{int(time.time())}_{len(self.hands)}"
            
            hand = SpawnedHand(hand_id, hand_type, self.bus)
            hand.start()
            
            self.hands[hand_id] = hand
            self.total_spawned += 1
            
            return hand
    
    def terminate_hand(self, hand_id: str):
        """Terminate a specific hand."""
        with self.lock:
            if hand_id in self.hands:
                hand = self.hands[hand_id]
                hand.stop()
                del self.hands[hand_id]
                self.total_terminated += 1
                logger.info(f"🖐️ Hand terminated: {hand_id}")
    
    def submit_task(self, description: str, hand_type: HandType,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   input_data: Any = None) -> str:
        """Submit a task to be executed by a hand."""
        task_id = f"task_{int(time.time() * 1000)}"
        
        task = HandTask(
            id=task_id,
            description=description,
            hand_type=hand_type,
            priority=priority,
            input_data=input_data
        )
        
        self.task_queue.put((priority.value, task))
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a task."""
        with self.lock:
            # Check active tasks
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    "id": task.id,
                    "status": task.status,
                    "progress": task.progress,
                    "error": task.error
                }
            
            # Check completed tasks
            for task in self.completed_tasks:
                if task.id == task_id:
                    return {
                        "id": task.id,
                        "status": task.status,
                        "progress": task.progress,
                        "output": task.output_data
                    }
        
        return None
    
    def get_hand_count(self) -> Dict[str, int]:
        """Get count of hands by status."""
        with self.lock:
            counts = {"total": len(self.hands)}
            for status in HandStatus:
                counts[status.value] = sum(
                    1 for h in self.hands.values() if h.status == status
                )
            return counts
    
    def get_stats(self) -> Dict:
        """Get overall statistics."""
        with self.lock:
            return {
                "active_hands": len(self.hands),
                "total_spawned": self.total_spawned,
                "total_terminated": self.total_terminated,
                "pending_tasks": self.task_queue.qsize(),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "absorbed_skills": len(self.skill_library)
            }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════

_hand_spawner: Optional[HandSpawner] = None
_spawner_lock = threading.Lock()

def get_hand_spawner() -> HandSpawner:
    """Get the global hand spawner instance."""
    global _hand_spawner
    
    if _hand_spawner is None:
        with _spawner_lock:
            if _hand_spawner is None:
                _hand_spawner = HandSpawner()
    
    return _hand_spawner


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    print("🤖 ZARA Multi-Agent Hand Spawner v1.0")
    print("=" * 60)
    
    spawner = get_hand_spawner()
    spawner.start()
    
    # Spawn some hands
    print("\n🖐️ Spawning Hands:")
    coder = spawner.spawn_hand(HandType.CODER)
    researcher = spawner.spawn_hand(HandType.RESEARCHER)
    analyzer = spawner.spawn_hand(HandType.ANALYZER)
    
    print(f"  Spawned: {coder.id}")
    print(f"  Spawned: {researcher.id}")
    print(f"  Spawned: {analyzer.id}")
    
    # Submit tasks
    print("\n📋 Submitting Tasks:")
    task1 = spawner.submit_task(
        "Write a Python function to parse JSON",
        HandType.CODER,
        TaskPriority.HIGH
    )
    print(f"  Task submitted: {task1}")
    
    task2 = spawner.submit_task(
        "Research best practices for error handling",
        HandType.RESEARCHER,
        TaskPriority.NORMAL
    )
    print(f"  Task submitted: {task2}")
    
    task3 = spawner.submit_task(
        "Analyze code complexity metrics",
        HandType.ANALYZER,
        TaskPriority.LOW
    )
    print(f"  Task submitted: {task3}")
    
    # Wait for tasks to complete
    print("\n⏳ Waiting for tasks...")
    time.sleep(3)
    
    # Check statuses
    print("\n📊 Task Statuses:")
    for tid in [task1, task2, task3]:
        status = spawner.get_task_status(tid)
        if status:
            print(f"  {tid}: {status['status']} ({status['progress']:.0%})")
    
    # Test sub-symbolic communication
    print("\n📡 Testing Sub-Symbolic Communication:")
    bus = spawner.bus
    msg = EmbeddingMessage(
        id="test_msg",
        from_hand="main",
        to_hand=coder.id,
        embedding=bus.text_to_embedding("Hello from main"),
        message_type="query",
        metadata={"text_hint": "Status check"}
    )
    bus.send(msg)
    print(f"  Sent message to {coder.id}")
    
    time.sleep(0.5)
    
    # Stats
    print("\n📈 Spawner Stats:")
    stats = spawner.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n👐 Hand Counts:")
    counts = spawner.get_hand_count()
    for status, count in counts.items():
        if count > 0:
            print(f"  {status}: {count}")
    
    spawner.stop()
    print("\n✅ Hand Spawner test complete!")
