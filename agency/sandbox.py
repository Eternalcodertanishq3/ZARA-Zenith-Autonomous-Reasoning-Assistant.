"""
ZARA Sandbox - Secure Code Execution Environment
"""
import subprocess
import os
import sys
import threading
import logging
import time
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ZARA_AGENCY")


class ExecutionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"


@dataclass
class ExecutionResult:
    """Result of sandbox execution."""
    status: ExecutionStatus
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    blocked_reason: Optional[str] = None


class Sandbox:
    """
    Secure code execution sandbox with:
    - Comprehensive security filtering
    - Resource limits
    - Execution history
    - Multiple language support
    - Isolated working directory
    """
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        # File system destruction
        "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir",
        "pathlib.Path.unlink", ".unlink(", "rmtree",
        # System commands
        "os.system(", "subprocess.call(", "subprocess.run(",
        "subprocess.Popen(", "os.popen(",
        # Network (optional - can be enabled)
        # "socket.", "requests.", "urllib.",
        # Code execution
        "exec(", "eval(", "compile(",
        # Environment modification
        "os.environ", "sys.path",
        # Dangerous imports
        "__import__('os')", "__import__('subprocess')",
        # Windows specific
        "format c:", "del /f", "rd /s",
    ]
    
    # Allowed imports (whitelist approach for safer execution)
    ALLOWED_IMPORTS = [
        "math", "random", "datetime", "json", "re",
        "collections", "itertools", "functools",
        "statistics", "decimal", "fractions",
    ]
    
    def __init__(self, timeout: int = 30, max_output_size: int = 10000):
        try:
            from config import ROOT_DIR
            self.ghost_dir = ROOT_DIR / "ghost"
        except ImportError:
            self.ghost_dir = Path("ghost")
        
        self.ghost_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        self.max_output_size = max_output_size
        
        # Execution history
        self.history: List[Dict] = []
        self.max_history = 100
        
        logger.info(f"Sandbox initialized at {self.ghost_dir}")

    def execute(self, code: str, filename: str = "auto_script.py") -> ExecutionResult:
        """
        Execute Python code safely.
        
        Args:
            code: Python code to execute
            filename: Script filename
        
        Returns:
            ExecutionResult with output and status
        """
        start_time = time.time()
        
        # Security check
        security_result = self._security_check(code)
        if security_result:
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time_ms=0,
                blocked_reason=security_result
            )
        
        # Write script
        script_path = self.ghost_dir / filename
        
        try:
            # Add safety wrapper
            wrapped_code = self._wrap_code(code)
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(wrapped_code)
            
            logger.info(f"Executing: {filename}")
            
            # Execute with isolation
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.ghost_dir),
                env=self._get_safe_env()
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Truncate output if too large
            stdout = result.stdout[:self.max_output_size]
            stderr = result.stderr[:self.max_output_size]
            
            if len(result.stdout) > self.max_output_size:
                stdout += "\n... (output truncated)"
            
            exec_result = ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.ERROR,
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
                execution_time_ms=execution_time
            )
            
            self._record_execution(filename, code, exec_result)
            return exec_result
            
        except subprocess.TimeoutExpired:
            execution_time = (time.time() - start_time) * 1000
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Execution timed out ({self.timeout}s limit)",
                exit_code=-1,
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=execution_time
            )
        finally:
            # Cleanup script
            try:
                if script_path.exists():
                    script_path.unlink()
            except:
                pass

    def _security_check(self, code: str) -> Optional[str]:
        """Check code for dangerous patterns."""
        code_lower = code.lower()
        
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                logger.warning(f"Blocked dangerous pattern: {pattern}")
                return f"Security Alert: '{pattern}' is not allowed"
        
        return None

    def _wrap_code(self, code: str) -> str:
        """Wrap code with safety measures."""
        wrapper = '''# Sandbox Execution Wrapper
import sys
import warnings
warnings.filterwarnings("ignore")

# Limit recursion
sys.setrecursionlimit(500)

# Execution
try:
    {}
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
        # Indent user code
        indented_code = '\n    '.join(code.split('\n'))
        return wrapper.format(indented_code)

    def _get_safe_env(self) -> Dict[str, str]:
        """Create a restricted environment for execution."""
        safe_env = os.environ.copy()
        # Remove potentially sensitive environment variables
        sensitive_vars = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'CREDENTIAL']
        for key in list(safe_env.keys()):
            if any(s in key.upper() for s in sensitive_vars):
                del safe_env[key]
        return safe_env

    def _record_execution(self, filename: str, code: str, result: ExecutionResult):
        """Record execution in history."""
        record = {
            "filename": filename,
            "code_preview": code[:200] + "..." if len(code) > 200 else code,
            "status": result.status.value,
            "exit_code": result.exit_code,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": time.time()
        }
        
        self.history.append(record)
        
        # Prune history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def execute_shell(self, command: str) -> ExecutionResult:
        """Execute a shell command (more restricted)."""
        # Very strict check for shell commands
        dangerous = ["rm", "del", "format", "mkfs", "dd", ">", "|", "&", ";"]
        
        for d in dangerous:
            if d in command.lower():
                return ExecutionResult(
                    status=ExecutionStatus.BLOCKED,
                    stdout="",
                    stderr="",
                    exit_code=-1,
                    execution_time_ms=0,
                    blocked_reason=f"Shell command contains blocked pattern: {d}"
                )
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.ghost_dir)
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.ERROR,
                stdout=result.stdout[:self.max_output_size],
                stderr=result.stderr[:self.max_output_size],
                exit_code=result.returncode,
                execution_time_ms=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Command timed out ({self.timeout}s)",
                exit_code=-1,
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def cleanup(self):
        """Clean up the ghost directory."""
        try:
            for file in self.ghost_dir.iterdir():
                if file.is_file():
                    file.unlink()
            logger.info("Ghost directory cleaned.")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history."""
        return self.history[-limit:]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sandbox = Sandbox()
    
    # Test safe code
    result = sandbox.execute("print('Hello from sandbox!')\nprint(2 + 2)")
    print(f"Status: {result.status.value}")
    print(f"Output: {result.stdout}")
    print(f"Time: {result.execution_time_ms:.1f}ms")
    
    # Test blocked code
    result = sandbox.execute("import shutil; shutil.rmtree('/')")
    print(f"\nBlocked: {result.blocked_reason}")
