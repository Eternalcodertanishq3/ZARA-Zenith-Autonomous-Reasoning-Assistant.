"""
ZARA Autonomous Tool Agency v1.0
=================================
Empowers ZARA to use PC and web services autonomously.

This is the "action brain" that:
1. Understands what tools/skills are available
2. Decides WHEN to use them (goal-driven or opportunity-based)
3. Plans HOW to use them (tool chains, parameters)
4. Executes them SAFELY (sandboxing, user approval for dangerous ops)
5. Learns from outcomes (success/failure feedback)

Architecture:
    LLM Intent → Tool Selector → Safety Check → Executor → Result Parser
"""

import logging
import time
import json
import subprocess
import os
import re
import threading
import hashlib
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_TOOL_AGENCY")


# ═══════════════════════════════════════════════════════════════════════════
# SAFETY & PERMISSION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class SafetyLevel(Enum):
    """How dangerous an action is."""
    SAFE = "safe"               # Read-only, no side effects
    MODERATE = "moderate"       # Minor side effects (create file, etc.)
    DANGEROUS = "dangerous"     # Significant effects (delete, network, money)
    CRITICAL = "critical"       # System-level (install, admin, purchases)


class ApprovalStatus(Enum):
    """User approval status for actions."""
    AUTO_APPROVED = "auto"      # Always allowed
    PENDING = "pending"         # Waiting for user
    APPROVED = "approved"       # User said yes
    DENIED = "denied"           # User said no
    EXPIRED = "expired"         # Approval timed out


@dataclass
class Permission:
    """A permission for an action type."""
    action_type: str
    safety_level: SafetyLevel
    auto_approve: bool = False
    require_confirmation: bool = True
    max_auto_per_hour: int = 10
    cooldown_seconds: int = 0


@dataclass
class ApprovalRequest:
    """A request for user approval."""
    id: str
    action_type: str
    description: str
    parameters: Dict[str, Any]
    safety_level: SafetyLevel
    created_at: float = field(default_factory=time.time)
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: float = 0.0
    
    def __post_init__(self):
        if self.expires_at == 0.0:
            self.expires_at = self.created_at + 300  # 5 min default


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Tool:
    """A tool ZARA can use."""
    id: str
    name: str
    description: str
    category: str
    safety_level: SafetyLevel
    parameters: Dict[str, Dict]  # param_name -> {type, required, description}
    executor: Optional[Callable] = None
    examples: List[str] = field(default_factory=list)
    requires_approval: bool = True
    cooldown_seconds: int = 0
    last_used: float = 0.0
    use_count: int = 0
    success_count: int = 0
    failure_count: int = 0


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    stdout: str = ""
    stderr: str = ""


@dataclass
class ToolPlan:
    """A plan to execute one or more tools."""
    id: str
    goal: str
    steps: List[Dict]  # [{tool_id, parameters, depends_on}]
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, executing, completed, failed
    current_step: int = 0
    results: Dict[str, ToolResult] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# CORE TOOLS REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class CoreTools:
    """Built-in tools ZARA always has access to."""
    
    @staticmethod
    def get_all_tools() -> List[Tool]:
        """Get all core tools."""
        return [
            # FILE SYSTEM
            Tool(
                id="read_file",
                name="Read File",
                description="Read contents of a file on the computer",
                category="filesystem",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "path": {"type": "string", "required": True, "description": "File path"}
                },
                requires_approval=False,
                examples=["Read my notes.txt", "What's in config.json?"]
            ),
            Tool(
                id="write_file",
                name="Write File",
                description="Create or overwrite a file",
                category="filesystem",
                safety_level=SafetyLevel.MODERATE,
                parameters={
                    "path": {"type": "string", "required": True, "description": "File path"},
                    "content": {"type": "string", "required": True, "description": "File content"}
                },
                requires_approval=True,
                examples=["Create a note for me", "Save this to a file"]
            ),
            Tool(
                id="list_directory",
                name="List Directory",
                description="List files and folders in a directory",
                category="filesystem",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "path": {"type": "string", "required": True, "description": "Directory path"}
                },
                requires_approval=False,
                examples=["What files are on my desktop?", "List my documents"]
            ),
            Tool(
                id="delete_file",
                name="Delete File",
                description="Delete a file (DANGEROUS)",
                category="filesystem",
                safety_level=SafetyLevel.DANGEROUS,
                parameters={
                    "path": {"type": "string", "required": True, "description": "File to delete"}
                },
                requires_approval=True,
                examples=["Delete temp.txt", "Remove old files"]
            ),
            
            # SYSTEM
            Tool(
                id="run_command",
                name="Run Command",
                description="Execute a shell command",
                category="system",
                safety_level=SafetyLevel.DANGEROUS,
                parameters={
                    "command": {"type": "string", "required": True, "description": "Command to run"},
                    "cwd": {"type": "string", "required": False, "description": "Working directory"}
                },
                requires_approval=True,
                cooldown_seconds=5,
                examples=["Run pip install", "Check system info"]
            ),
            Tool(
                id="open_application",
                name="Open Application",
                description="Launch an application",
                category="system",
                safety_level=SafetyLevel.MODERATE,
                parameters={
                    "app_name": {"type": "string", "required": True, "description": "Application name"}
                },
                requires_approval=False,
                examples=["Open Notepad", "Launch Chrome"]
            ),
            Tool(
                id="get_system_info",
                name="Get System Info",
                description="Get computer system information",
                category="system",
                safety_level=SafetyLevel.SAFE,
                parameters={},
                requires_approval=False,
                examples=["What's my CPU usage?", "How much RAM do I have?"]
            ),
            
            # WEB
            Tool(
                id="web_search",
                name="Web Search",
                description="Search the web for information",
                category="web",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "query": {"type": "string", "required": True, "description": "Search query"}
                },
                requires_approval=False,
                cooldown_seconds=10,
                examples=["Search for Python tutorials", "Look up weather"]
            ),
            Tool(
                id="fetch_url",
                name="Fetch URL",
                description="Retrieve content from a URL",
                category="web",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "url": {"type": "string", "required": True, "description": "URL to fetch"}
                },
                requires_approval=False,
                examples=["Get the page at example.com"]
            ),
            
            # COMMUNICATION
            Tool(
                id="speak",
                name="Speak",
                description="Say something out loud via TTS",
                category="communication",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "text": {"type": "string", "required": True, "description": "Text to speak"}
                },
                requires_approval=False,
                examples=["Say hello", "Read this aloud"]
            ),
            Tool(
                id="send_notification",
                name="Send Notification",
                description="Show a desktop notification",
                category="communication",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "title": {"type": "string", "required": True, "description": "Notification title"},
                    "message": {"type": "string", "required": True, "description": "Notification body"}
                },
                requires_approval=False,
                examples=["Remind me about meeting", "Notify me when done"]
            ),
            
            # SCHEDULING
            Tool(
                id="set_reminder",
                name="Set Reminder",
                description="Create a reminder for later",
                category="scheduling",
                safety_level=SafetyLevel.SAFE,
                parameters={
                    "message": {"type": "string", "required": True, "description": "Reminder message"},
                    "delay_minutes": {"type": "integer", "required": True, "description": "Minutes until reminder"}
                },
                requires_approval=False,
                examples=["Remind me in 30 minutes", "Set alarm for 5pm"]
            ),
            Tool(
                id="check_time",
                name="Check Time",
                description="Get current time and date",
                category="scheduling",
                safety_level=SafetyLevel.SAFE,
                parameters={},
                requires_approval=False,
                examples=["What time is it?", "What's today's date?"]
            ),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# TOOL EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════

class ToolExecutor:
    """Executes tools safely."""
    
    def __init__(self):
        self._tts = None
        self._web = None
        self.execution_log: deque = deque(maxlen=100)
        
        # Dangerous command patterns to block
        self.blocked_patterns = [
            r'rm\s+-rf\s+[/~]',          # Destructive rm
            r'del\s+/[sQ]',              # Windows destructive del
            r'format\s+[a-zA-Z]:',       # Format drive
            r'mkfs\.',                   # Format filesystem
            r'dd\s+if=.*of=',            # dd can destroy disks
            r':\(\)\{:\|:&\};:',         # Fork bomb
            r'shutdown',                 # Shutdown system
            r'reboot',                   # Reboot system
        ]
    
    def execute(self, tool: Tool, parameters: Dict) -> ToolResult:
        """Execute a tool with given parameters."""
        start_time = time.time()
        
        try:
            # Route to appropriate executor
            if tool.category == "filesystem":
                result = self._execute_filesystem(tool.id, parameters)
            elif tool.category == "system":
                result = self._execute_system(tool.id, parameters)
            elif tool.category == "web":
                result = self._execute_web(tool.id, parameters)
            elif tool.category == "communication":
                result = self._execute_communication(tool.id, parameters)
            elif tool.category == "scheduling":
                result = self._execute_scheduling(tool.id, parameters)
            else:
                result = ToolResult(success=False, output=None, error=f"Unknown category: {tool.category}")
            
            result.execution_time = time.time() - start_time
            
            # Log execution
            self.execution_log.append({
                "tool_id": tool.id,
                "parameters": parameters,
                "success": result.success,
                "timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_filesystem(self, tool_id: str, params: Dict) -> ToolResult:
        """Execute filesystem tools."""
        if tool_id == "read_file":
            path = Path(params["path"]).expanduser()
            if not path.exists():
                return ToolResult(success=False, output=None, error=f"File not found: {path}")
            if not path.is_file():
                return ToolResult(success=False, output=None, error=f"Not a file: {path}")
            try:
                content = path.read_text(encoding="utf-8")
                return ToolResult(success=True, output=content)
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "write_file":
            path = Path(params["path"]).expanduser()
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(params["content"], encoding="utf-8")
                return ToolResult(success=True, output=f"Written {len(params['content'])} chars to {path}")
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "list_directory":
            path = Path(params["path"]).expanduser()
            if not path.exists():
                return ToolResult(success=False, output=None, error=f"Directory not found: {path}")
            try:
                items = []
                for item in path.iterdir():
                    item_type = "📁" if item.is_dir() else "📄"
                    size = item.stat().st_size if item.is_file() else 0
                    items.append(f"{item_type} {item.name} ({size} bytes)")
                return ToolResult(success=True, output="\n".join(items))
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "delete_file":
            path = Path(params["path"]).expanduser()
            if not path.exists():
                return ToolResult(success=False, output=None, error=f"File not found: {path}")
            try:
                path.unlink()
                return ToolResult(success=True, output=f"Deleted: {path}")
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        return ToolResult(success=False, output=None, error=f"Unknown filesystem tool: {tool_id}")
    
    def _execute_system(self, tool_id: str, params: Dict) -> ToolResult:
        """Execute system tools."""
        if tool_id == "run_command":
            command = params["command"]
            
            # Safety check - block dangerous patterns
            for pattern in self.blocked_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return ToolResult(
                        success=False, output=None,
                        error=f"BLOCKED: Command matches dangerous pattern"
                    )
            
            cwd = params.get("cwd") or os.getcwd()
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout or result.stderr,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error=None if result.returncode == 0 else f"Exit code: {result.returncode}"
                )
            except subprocess.TimeoutExpired:
                return ToolResult(success=False, output=None, error="Command timed out (60s)")
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "open_application":
            app_name = params["app_name"]
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(app_name)
                else:
                    subprocess.Popen(["open", app_name])
                return ToolResult(success=True, output=f"Opened: {app_name}")
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "get_system_info":
            try:
                import platform
                info = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                }
                
                # Try to get memory info
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    info["memory_total_gb"] = round(mem.total / (1024**3), 2)
                    info["memory_used_percent"] = mem.percent
                    info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
                except ImportError:
                    logger.debug("psutil not installed, skipping memory info")
                
                return ToolResult(success=True, output=info)
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        return ToolResult(success=False, output=None, error=f"Unknown system tool: {tool_id}")
    
    def _execute_web(self, tool_id: str, params: Dict) -> ToolResult:
        """Execute web tools."""
        if tool_id == "web_search":
            query = params["query"]
            try:
                from evolution.web_knowledge import WebKnowledge
                web = WebKnowledge()
                results = web.search(query, max_results=5)
                return ToolResult(success=True, output=results)
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        elif tool_id == "fetch_url":
            url = params["url"]
            try:
                # Security: Validate URL to prevent SSRF
                from urllib.parse import urlparse
                parsed = urlparse(url)
                
                # Only allow HTTP/HTTPS
                if parsed.scheme not in ('http', 'https'):
                    return ToolResult(
                        success=False, output=None,
                        error=f"Security: Only HTTP/HTTPS URLs allowed, got: {parsed.scheme}"
                    )
                
                # Block internal addresses
                blocked_hosts = {'localhost', '127.0.0.1', '0.0.0.0', '::1', '10.', '192.168.', '172.16.'}
                hostname = (parsed.hostname or '').lower()
                if hostname in blocked_hosts or any(hostname.startswith(b) for b in blocked_hosts if b.endswith('.')):
                    return ToolResult(
                        success=False, output=None,
                        error="Security: Internal/localhost URLs are blocked"
                    )
                
                import urllib.request
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode('utf-8')[:5000]
                return ToolResult(success=True, output=content)
            except Exception as e:
                return ToolResult(success=False, output=None, error=str(e))
        
        return ToolResult(success=False, output=None, error=f"Unknown web tool: {tool_id}")
    
    def _execute_communication(self, tool_id: str, params: Dict) -> ToolResult:
        """Execute communication tools."""
        if tool_id == "speak":
            text = params["text"]
            try:
                from soul.voice_synthesis import VoiceSynthesis
                tts = VoiceSynthesis()
                tts.speak(text)
                return ToolResult(success=True, output=f"Spoke: {text[:50]}...")
            except Exception as e:
                # Fallback to print
                print(f"🗣️ ZARA: {text}")
                return ToolResult(success=True, output=f"Spoke (fallback): {text[:50]}...")
        
        elif tool_id == "send_notification":
            title = params["title"]
            message = params["message"]
            try:
                if os.name == 'nt':  # Windows
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                else:
                    subprocess.run(["notify-send", title, message])
                return ToolResult(success=True, output=f"Notification sent: {title}")
            except Exception as e:
                print(f"📢 {title}: {message}")
                return ToolResult(success=True, output=f"Notification (fallback): {title}")
        
        return ToolResult(success=False, output=None, error=f"Unknown communication tool: {tool_id}")
    
    def _execute_scheduling(self, tool_id: str, params: Dict) -> ToolResult:
        """Execute scheduling tools."""
        if tool_id == "set_reminder":
            message = params["message"]
            delay = params.get("delay_minutes", 30)
            
            # Store reminder for later
            reminder = {
                "message": message,
                "trigger_at": time.time() + (delay * 60),
                "created_at": time.time()
            }
            
            return ToolResult(success=True, output=reminder)
        
        elif tool_id == "check_time":
            from datetime import datetime
            now = datetime.now()
            return ToolResult(success=True, output={
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day": now.strftime("%A"),
                "timestamp": now.timestamp()
            })
        
        return ToolResult(success=False, output=None, error=f"Unknown scheduling tool: {tool_id}")


# ═══════════════════════════════════════════════════════════════════════════
# TOOL AGENCY - THE BRAIN
# ═══════════════════════════════════════════════════════════════════════════

class ToolAgency:
    """
    ZARA's Autonomous Tool Agency.
    
    This is the intelligent system that decides:
    - WHICH tool to use
    - WHEN to use it
    - HOW to use it (parameters)
    - WHETHER it's safe (approval needed)
    """
    
    def __init__(self):
        # Tool registry
        self.tools: Dict[str, Tool] = {}
        self._register_core_tools()
        
        # Executor
        self.executor = ToolExecutor()
        
        # Approval system
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: deque = deque(maxlen=100)
        
        # Permission settings
        self.permissions: Dict[str, Permission] = {}
        self._init_default_permissions()
        
        # Skill integration
        self._skill_manager = None
        
        # LLM reasoner for intelligent planning
        self._llm = None
        
        # State
        self.plans: Dict[str, ToolPlan] = {}
        self.execution_history: deque = deque(maxlen=500)
        
        # Persistence
        self.state_file = Path("memory/tool_agency_state.json")
        self._load_state()
        
        logger.info(f"🛠️ Tool Agency initialized with {len(self.tools)} tools")
    
    def _register_core_tools(self):
        """Register built-in tools."""
        for tool in CoreTools.get_all_tools():
            self.tools[tool.id] = tool
    
    def _init_default_permissions(self):
        """Initialize default permission settings."""
        # Safe tools - auto approve
        for tool in self.tools.values():
            self.permissions[tool.id] = Permission(
                action_type=tool.id,
                safety_level=tool.safety_level,
                auto_approve=(tool.safety_level == SafetyLevel.SAFE),
                require_confirmation=(tool.safety_level in [SafetyLevel.DANGEROUS, SafetyLevel.CRITICAL])
            )
    
    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Load tool stats
                    for tool_id, stats in data.get("tool_stats", {}).items():
                        if tool_id in self.tools:
                            self.tools[tool_id].use_count = stats.get("use_count", 0)
                            self.tools[tool_id].success_count = stats.get("success_count", 0)
                            self.tools[tool_id].failure_count = stats.get("failure_count", 0)
            except Exception as e:
                logger.warning(f"Could not load tool agency state: {e}")
    
    def _save_state(self):
        """Save state to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "tool_stats": {
                    tid: {
                        "use_count": t.use_count,
                        "success_count": t.success_count,
                        "failure_count": t.failure_count
                    }
                    for tid, t in self.tools.items()
                }
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save tool agency state: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # TOOL SELECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def find_tool(self, intent: str) -> Optional[Tool]:
        """Find the best tool for a given intent."""
        intent_lower = intent.lower()
        
        # Direct ID match
        if intent_lower in self.tools:
            return self.tools[intent_lower]
        
        # Keyword matching
        keyword_map = {
            "read_file": ["read", "open", "view", "show", "content", "file"],
            "write_file": ["create", "write", "save", "make file"],
            "list_directory": ["list", "ls", "dir", "files in", "folder"],
            "delete_file": ["delete", "remove", "rm"],
            "run_command": ["run", "execute", "command", "terminal", "cmd", "shell"],
            "open_application": ["open", "launch", "start", "run app"],
            "get_system_info": ["system", "cpu", "ram", "memory", "info"],
            "web_search": ["search", "google", "look up", "find online"],
            "fetch_url": ["fetch", "get page", "download url"],
            "speak": ["say", "speak", "tell", "voice", "read aloud"],
            "send_notification": ["notify", "alert", "notification"],
            "set_reminder": ["remind", "reminder", "alarm", "schedule"],
            "check_time": ["time", "date", "what day", "clock"]
        }
        
        best_match = None
        best_score = 0
        
        for tool_id, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in intent_lower)
            if score > best_score:
                best_score = score
                best_match = tool_id
        
        return self.tools.get(best_match) if best_match else None
    
    def suggest_tools(self, context: str, limit: int = 3) -> List[Tool]:
        """Suggest relevant tools based on context."""
        suggestions = []
        context_lower = context.lower()
        
        for tool in self.tools.values():
            score = 0
            
            # Check description match
            if any(word in context_lower for word in tool.description.lower().split()):
                score += 1
            
            # Check example match
            for example in tool.examples:
                if any(word in context_lower for word in example.lower().split()):
                    score += 2
                    break
            
            # Check category relevance
            category_keywords = {
                "filesystem": ["file", "folder", "directory", "read", "write"],
                "system": ["run", "execute", "app", "application"],
                "web": ["search", "web", "internet", "url"],
                "communication": ["say", "speak", "notify"],
                "scheduling": ["remind", "time", "schedule"]
            }
            
            if tool.category in category_keywords:
                if any(kw in context_lower for kw in category_keywords[tool.category]):
                    score += 1
            
            if score > 0:
                suggestions.append((tool, score))
        
        suggestions.sort(key=lambda x: -x[1])
        return [t for t, _ in suggestions[:limit]]
    
    # ═══════════════════════════════════════════════════════════════════
    # EXECUTION
    # ═══════════════════════════════════════════════════════════════════
    
    def can_execute(self, tool_id: str) -> Tuple[bool, str]:
        """Check if a tool can be executed right now."""
        if tool_id not in self.tools:
            return False, f"Unknown tool: {tool_id}"
        
        tool = self.tools[tool_id]
        
        # Check cooldown
        if tool.cooldown_seconds > 0:
            elapsed = time.time() - tool.last_used
            if elapsed < tool.cooldown_seconds:
                remaining = tool.cooldown_seconds - elapsed
                return False, f"Cooldown: {remaining:.0f}s remaining"
        
        # Check permission
        perm = self.permissions.get(tool_id)
        if perm and perm.require_confirmation:
            return False, "Requires user confirmation"
        
        return True, "Ready"
    
    def execute(self, tool_id: str, parameters: Dict = None,
               skip_approval: bool = False) -> ToolResult:
        """
        Execute a tool.
        
        Args:
            tool_id: Which tool to run
            parameters: Tool parameters
            skip_approval: Skip safety check (use cautiously!)
        
        Returns:
            ToolResult with output or error
        """
        parameters = parameters or {}
        
        if tool_id not in self.tools:
            return ToolResult(success=False, output=None, error=f"Unknown tool: {tool_id}")
        
        tool = self.tools[tool_id]
        
        # Validate required parameters
        for param_name, param_def in tool.parameters.items():
            if param_def.get("required") and param_name not in parameters:
                return ToolResult(
                    success=False, output=None,
                    error=f"Missing required parameter: {param_name}"
                )
        
        # Check if approval needed
        if not skip_approval and tool.requires_approval:
            if tool.safety_level in [SafetyLevel.DANGEROUS, SafetyLevel.CRITICAL]:
                # Create approval request
                req_id = self._request_approval(tool, parameters)
                return ToolResult(
                    success=False, output=None,
                    error=f"Approval required. Request ID: {req_id}"
                )
        
        # Execute
        result = self.executor.execute(tool, parameters)
        
        # Update stats
        tool.use_count += 1
        tool.last_used = time.time()
        if result.success:
            tool.success_count += 1
        else:
            tool.failure_count += 1
        
        # Log
        self.execution_history.append({
            "tool_id": tool_id,
            "parameters": parameters,
            "success": result.success,
            "timestamp": time.time()
        })
        
        # Persist
        self._save_state()
        
        return result
    
    def _request_approval(self, tool: Tool, parameters: Dict) -> str:
        """Create an approval request."""
        req_id = f"approval_{int(time.time())}_{tool.id}"
        
        request = ApprovalRequest(
            id=req_id,
            action_type=tool.id,
            description=f"Execute {tool.name}: {tool.description}",
            parameters=parameters,
            safety_level=tool.safety_level
        )
        
        self.pending_approvals[req_id] = request
        
        logger.info(f"⚠️ Approval requested: {tool.name} - {req_id}")
        
        return req_id
    
    def approve(self, request_id: str) -> ToolResult:
        """Approve and execute a pending request."""
        if request_id not in self.pending_approvals:
            return ToolResult(success=False, output=None, error="Request not found or expired")
        
        request = self.pending_approvals[request_id]
        
        if time.time() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            del self.pending_approvals[request_id]
            return ToolResult(success=False, output=None, error="Request expired")
        
        request.status = ApprovalStatus.APPROVED
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        
        # Execute with approval
        return self.execute(request.action_type, request.parameters, skip_approval=True)
    
    def deny(self, request_id: str):
        """Deny a pending request."""
        if request_id in self.pending_approvals:
            request = self.pending_approvals[request_id]
            request.status = ApprovalStatus.DENIED
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
    
    # ═══════════════════════════════════════════════════════════════════
    # AUTONOMOUS PLANNING
    # ═══════════════════════════════════════════════════════════════════
    
    def plan(self, goal: str) -> ToolPlan:
        """
        Create an autonomous plan to achieve a goal.
        Uses LLM reasoning when available.
        """
        plan_id = f"plan_{int(time.time())}"
        
        # Try LLM planning first
        steps = self._llm_plan(goal)
        
        if not steps:
            # Fallback to simple keyword planning
            steps = self._simple_plan(goal)
        
        plan = ToolPlan(
            id=plan_id,
            goal=goal,
            steps=steps
        )
        
        self.plans[plan_id] = plan
        return plan
    
    def _llm_plan(self, goal: str) -> List[Dict]:
        """Use LLM to create a tool execution plan."""
        try:
            from brain.cognitive_core import ConsciousMind
            brain = ConsciousMind()
            
            if not brain.is_active:
                return []
            
            # Create tool list for prompt
            tool_list = "\n".join([
                f"- {t.id}: {t.description} (params: {list(t.parameters.keys())})"
                for t in self.tools.values()
            ])
            
            prompt = f"""You are ZARA's tool planner. Given a goal, create a step-by-step plan using available tools.

AVAILABLE TOOLS:
{tool_list}

GOAL: {goal}

Respond with a JSON array of steps, each with "tool_id" and "parameters".
Example: [{{tool_id: "web_search", parameters: {{query: "test"}}}}]"""
            
            response = ""
            for token in brain.think(prompt):
                response += token
                if len(response) > 500:
                    break
            
            # Parse response
            import json
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
            
        except Exception as e:
            logger.debug(f"LLM planning failed: {e}")
        
        return []
    
    def _simple_plan(self, goal: str) -> List[Dict]:
        """Simple keyword-based planning fallback."""
        steps = []
        goal_lower = goal.lower()
        
        # Search then read
        if "find" in goal_lower or "search" in goal_lower:
            steps.append({"tool_id": "web_search", "parameters": {"query": goal}})
        
        # File operations
        if "read" in goal_lower and "file" in goal_lower:
            # Extract file path if mentioned
            steps.append({"tool_id": "read_file", "parameters": {"path": ""}})
        
        # Time check
        if "time" in goal_lower or "date" in goal_lower:
            steps.append({"tool_id": "check_time", "parameters": {}})
        
        # Default to speak result
        if steps:
            steps.append({"tool_id": "speak", "parameters": {"text": f"Done with: {goal}"}})
        
        return steps
    
    def execute_plan(self, plan_id: str) -> Dict[str, ToolResult]:
        """Execute all steps in a plan."""
        if plan_id not in self.plans:
            return {"error": ToolResult(success=False, output=None, error="Plan not found")}
        
        plan = self.plans[plan_id]
        plan.status = "executing"
        results = {}
        
        for i, step in enumerate(plan.steps):
            plan.current_step = i
            
            tool_id = step.get("tool_id")
            parameters = step.get("parameters", {})
            
            result = self.execute(tool_id, parameters)
            results[f"step_{i}_{tool_id}"] = result
            plan.results[f"step_{i}"] = result
            
            if not result.success:
                plan.status = "failed"
                break
        
        if plan.status != "failed":
            plan.status = "completed"
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS & INTROSPECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get agency status."""
        return {
            "total_tools": len(self.tools),
            "tools_by_category": self._count_by_category(),
            "pending_approvals": len(self.pending_approvals),
            "total_executions": sum(t.use_count for t in self.tools.values()),
            "success_rate": self._calculate_success_rate(),
            "active_plans": len([p for p in self.plans.values() if p.status == "executing"])
        }
    
    def _count_by_category(self) -> Dict[str, int]:
        """Count tools by category."""
        counts = {}
        for tool in self.tools.values():
            counts[tool.category] = counts.get(tool.category, 0) + 1
        return counts
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        total = sum(t.use_count for t in self.tools.values())
        success = sum(t.success_count for t in self.tools.values())
        return success / total if total > 0 else 1.0
    
    def get_tool_descriptions(self) -> str:
        """Get human-readable tool descriptions for LLM."""
        lines = ["## Available Tools\n"]
        
        for category in set(t.category for t in self.tools.values()):
            lines.append(f"### {category.title()}")
            for tool in self.tools.values():
                if tool.category == category:
                    params = ", ".join(tool.parameters.keys()) if tool.parameters else "none"
                    safety = "⚠️" if tool.safety_level != SafetyLevel.SAFE else "✓"
                    lines.append(f"- **{tool.name}** ({tool.id}): {tool.description} [{params}] {safety}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SKILL BRIDGE - OPENCLAW INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class SkillBridge:
    """
    Bridge between OpenClaw skills and the Tool Agency.
    
    Converts SKILL.md files into executable Tool objects that can:
    1. Parse CLI commands from skill instructions
    2. Execute them via subprocess
    3. Handle safety levels based on skill type
    """
    
    # Safety classification based on skill category
    SAFETY_MAP = {
        # Safe - read only, no purchases
        "weather": SafetyLevel.SAFE,
        "github": SafetyLevel.SAFE,
        "model-usage": SafetyLevel.SAFE,
        "peekaboo": SafetyLevel.SAFE,
        "camsnap": SafetyLevel.SAFE,
        "check_time": SafetyLevel.SAFE,
        "songsee": SafetyLevel.SAFE,
        "gifgrep": SafetyLevel.SAFE,
        "video-frames": SafetyLevel.SAFE,
        "summarize": SafetyLevel.SAFE,
        "session-logs": SafetyLevel.SAFE,
        
        # Moderate - creates/modifies local data
        "spotify-player": SafetyLevel.MODERATE,
        "obsidian": SafetyLevel.MODERATE,
        "notion": SafetyLevel.MODERATE,
        "apple-notes": SafetyLevel.MODERATE,
        "apple-reminders": SafetyLevel.MODERATE,
        "bear-notes": SafetyLevel.MODERATE,
        "trello": SafetyLevel.MODERATE,
        "canvas": SafetyLevel.MODERATE,
        "things-mac": SafetyLevel.MODERATE,
        "tmux": SafetyLevel.MODERATE,
        "nano-pdf": SafetyLevel.MODERATE,
        "nano-banana-pro": SafetyLevel.MODERATE,
        "sherpa-onnx-tts": SafetyLevel.MODERATE,
        "openai-whisper": SafetyLevel.MODERATE,
        "openai-whisper-api": SafetyLevel.MODERATE,
        "openhue": SafetyLevel.MODERATE,
        "sonoscli": SafetyLevel.MODERATE,
        "local-places": SafetyLevel.MODERATE,
        "goplaces": SafetyLevel.MODERATE,
        "blogwatcher": SafetyLevel.MODERATE,
        
        # Dangerous - network, messaging, external services
        "discord": SafetyLevel.DANGEROUS,
        "slack": SafetyLevel.DANGEROUS,
        "imsg": SafetyLevel.DANGEROUS,
        "bluebubbles": SafetyLevel.DANGEROUS,
        "wacli": SafetyLevel.DANGEROUS,
        "himalaya": SafetyLevel.DANGEROUS,
        "bird": SafetyLevel.DANGEROUS,
        "gemini": SafetyLevel.DANGEROUS,
        "openai-image-gen": SafetyLevel.DANGEROUS,
        "oracle": SafetyLevel.DANGEROUS,
        "sag": SafetyLevel.DANGEROUS,
        "coding-agent": SafetyLevel.DANGEROUS,
        "skill-creator": SafetyLevel.DANGEROUS,
        "voice-call": SafetyLevel.DANGEROUS,
        "clawhub": SafetyLevel.DANGEROUS,
        "mcporter": SafetyLevel.DANGEROUS,
        "blucli": SafetyLevel.DANGEROUS,
        "eightctl": SafetyLevel.DANGEROUS,
        "gog": SafetyLevel.DANGEROUS,
        
        # Critical - financial transactions, password management
        "1password": SafetyLevel.CRITICAL,
        "food-order": SafetyLevel.CRITICAL,
        "ordercli": SafetyLevel.CRITICAL,
    }
    
    def __init__(self):
        self._skill_manager = None
        self.skills_loaded = False
        self.skill_tools: Dict[str, Tool] = {}
    
    def _get_skill_manager(self):
        """Get or create SkillManager."""
        if self._skill_manager is None:
            try:
                from actions.skill_loader import SkillManager
                self._skill_manager = SkillManager()
                self._skill_manager.scan_skills()
            except Exception as e:
                logger.warning(f"Could not load SkillManager: {e}")
        return self._skill_manager
    
    def load_all_skills(self) -> Dict[str, Tool]:
        """Load all OpenClaw skills as Tools."""
        if self.skills_loaded:
            return self.skill_tools
        
        manager = self._get_skill_manager()
        if not manager:
            return {}
        
        for skill in manager.skills.values():
            tool = self._skill_to_tool(skill)
            if tool:
                self.skill_tools[tool.id] = tool
        
        self.skills_loaded = True
        logger.info(f"🦞 Loaded {len(self.skill_tools)} OpenClaw skills as tools")
        return self.skill_tools
    
    def _skill_to_tool(self, skill) -> Optional[Tool]:
        """Convert an OpenClaw Skill to a Tool."""
        try:
            # Extract key info from skill
            name = skill.metadata.name
            description = skill.metadata.description
            emoji = skill.metadata.emoji
            
            # Determine safety level
            safety = self.SAFETY_MAP.get(name, SafetyLevel.MODERATE)
            
            # Parse CLI commands from skill content
            commands = self._extract_commands(skill.content)
            
            # Create executor for this skill
            def make_executor(skill_obj, cmds):
                def executor(params: Dict) -> ToolResult:
                    return self._execute_skill(skill_obj, cmds, params)
                return executor
            
            tool = Tool(
                id=f"skill_{name}",
                name=f"{emoji} {name.replace('-', ' ').title()}",
                description=description or f"OpenClaw skill: {name}",
                category="skills",
                safety_level=safety,
                parameters={
                    "action": {"type": "string", "required": False, "description": "Specific action to perform"},
                    "args": {"type": "string", "required": False, "description": "Additional arguments"}
                },
                executor=make_executor(skill, commands),
                requires_approval=(safety != SafetyLevel.SAFE),
                examples=commands[:2] if commands else []
            )
            
            return tool
            
        except Exception as e:
            logger.debug(f"Could not convert skill {skill}: {e}")
            return None
    
    def _extract_commands(self, content: str) -> List[str]:
        """Extract CLI commands from skill content."""
        commands = []
        
        # Match lines starting with common CLI patterns
        patterns = [
            r'`([a-zA-Z][\w-]+\s+[^`]+)`',  # `command args`
            r'^\s*[-*]\s*`([^`]+)`',         # - `command`
            r'^\s*\$\s*(.+)$',               # $ command
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            commands.extend(matches[:10])  # Limit per pattern
        
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for cmd in commands:
            if cmd not in seen:
                seen.add(cmd)
                unique.append(cmd)
        
        return unique[:20]  # Max 20 commands per skill
    
    def _execute_skill(self, skill, commands: List[str], params: Dict) -> ToolResult:
        """Execute a skill command."""
        action = params.get("action", "")
        args = params.get("args", "")
        
        # If specific action requested, try to find matching command
        if action:
            for cmd in commands:
                if action.lower() in cmd.lower():
                    return self._run_skill_command(cmd, args)
        
        # Default: run first command or show help
        if commands:
            # If command has --help, use that
            first_cmd = commands[0]
            if "--help" not in first_cmd and "-h" not in first_cmd:
                help_cmd = first_cmd.split()[0] + " --help"
                return ToolResult(
                    success=True,
                    output=f"Skill commands:\n" + "\n".join(f"- {c}" for c in commands[:5])
                )
        
        return ToolResult(
            success=True,
            output=f"Skill: {skill.metadata.name}\n{skill.metadata.description}"
        )
    
    def _run_skill_command(self, command: str, extra_args: str = "") -> ToolResult:
        """Run a skill CLI command."""
        full_command = f"{command} {extra_args}".strip()
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout or result.stderr,
                stdout=result.stdout,
                stderr=result.stderr,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output=None, error="Skill command timed out (30s)")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON & SKILL INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

_tool_agency = None
_skill_bridge = None

def get_skill_bridge() -> SkillBridge:
    """Get the global skill bridge instance."""
    global _skill_bridge
    if _skill_bridge is None:
        _skill_bridge = SkillBridge()
    return _skill_bridge

def get_tool_agency(load_skills: bool = True) -> ToolAgency:
    """Get the global tool agency instance."""
    global _tool_agency
    if _tool_agency is None:
        _tool_agency = ToolAgency()
        
        # Automatically load OpenClaw skills
        if load_skills:
            try:
                bridge = get_skill_bridge()
                skill_tools = bridge.load_all_skills()
                for tool_id, tool in skill_tools.items():
                    _tool_agency.tools[tool_id] = tool
                    _tool_agency.permissions[tool_id] = Permission(
                        action_type=tool_id,
                        safety_level=tool.safety_level,
                        auto_approve=(tool.safety_level == SafetyLevel.SAFE),
                        require_confirmation=(tool.safety_level in [SafetyLevel.DANGEROUS, SafetyLevel.CRITICAL])
                    )
                logger.info(f"🛠️ Total tools after skill integration: {len(_tool_agency.tools)}")
            except Exception as e:
                logger.warning(f"Could not load skills: {e}")
    
    return _tool_agency


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🛠️ ZARA Autonomous Tool Agency v1.0\n")
    print("=" * 60)
    
    agency = ToolAgency()
    
    # Show status
    status = agency.get_status()
    print(f"\n📊 Status:")
    print(f"  Total tools: {status['total_tools']}")
    print(f"  By category: {status['tools_by_category']}")
    
    # Test tool finding
    print("\n🔍 Tool Finding:")
    for intent in ["what time is it", "search for python", "read my notes"]:
        tool = agency.find_tool(intent)
        print(f"  '{intent}' → {tool.name if tool else 'None'}")
    
    # Test safe execution
    print("\n⚙️ Safe Execution Tests:")
    
    # Time check (safe)
    result = agency.execute("check_time")
    print(f"  check_time: {result.output if result.success else result.error}")
    
    # System info (safe)
    result = agency.execute("get_system_info")
    if result.success:
        info = result.output
        print(f"  System: {info['system']} {info['release']}")
    
    # List directory (safe)
    result = agency.execute("list_directory", {"path": "."})
    if result.success:
        files = result.output.split("\n")[:3]
        print(f"  Directory: {len(result.output.split(chr(10)))} items")
    
    # Test dangerous (should require approval)
    print("\n⚠️ Dangerous Tool Test:")
    result = agency.execute("run_command", {"command": "echo hello"})
    print(f"  run_command: {result.error or result.output}")
    
    # Test planning
    print("\n📋 Autonomous Planning:")
    plan = agency.plan("Find the current time and tell me")
    print(f"  Goal: {plan.goal}")
    print(f"  Steps: {len(plan.steps)}")
    for i, step in enumerate(plan.steps):
        print(f"    {i+1}. {step.get('tool_id')}")
    
    # Show tool descriptions
    print("\n" + "=" * 60)
    print("✅ Tool Agency ready!\n")
