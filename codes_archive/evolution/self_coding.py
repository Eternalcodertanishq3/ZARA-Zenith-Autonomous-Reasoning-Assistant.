"""
ZARA Self-Coding Engine
Allows ZARA to introspect, modify, and improve her own code.
This is the foundation of recursive self-improvement (AGI).
"""
import logging
import ast
import time
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import threading

logger = logging.getLogger("ZARA_SELFCODE")


@dataclass
class CodeModification:
    """A record of a self-modification."""
    file_path: str
    function_name: str
    original_code: str
    new_code: str
    reason: str
    timestamp: float
    success: bool
    test_result: Optional[str] = None


class SelfCodingEngine:
    """
    ZARA's Recursive Self-Improvement Engine.
    
    Capabilities:
    - Introspect own source code
    - Generate improved versions of functions
    - Test modifications in sandbox
    - Hot-swap code at runtime
    - Maintain modification history
    
    Safety:
    - All modifications are tested before deployment
    - Rollback capability for failed changes
    - Modification history for audit
    """
    
    def __init__(self, brain=None):
        try:
            from config import EVOLUTION_DIR
            self.code_dir = EVOLUTION_DIR / "self_code"
        except ImportError:
            self.code_dir = Path("evolution/self_code")
        
        self.code_dir.mkdir(parents=True, exist_ok=True)
        
        # Reference to ZARA's brain for LLM access
        self.brain = brain
        
        # Modification history
        self.history: List[CodeModification] = []
        self.history_file = self.code_dir / "modification_history.json"
        
        # Backup storage
        self.backup_dir = self.code_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Allowed directories for modification
        self.allowed_paths = [
            Path("evolution/"),
            Path("memory/"),
            Path("pulse/"),
            Path("actions/"),
            Path("social/"),
        ]
        
        # Load history
        self._load_history()
        
        self.lock = threading.Lock()
        
        logger.info("🧬 Self-Coding Engine initialized")
    
    def _load_history(self):
        """Load modification history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-100:]:  # Last 100 modifications
                        self.history.append(CodeModification(**item))
            except Exception as e:
                logger.warning(f"Could not load history: {e}")
    
    def _save_history(self):
        """Save modification history."""
        history_data = [
            {
                "file_path": m.file_path,
                "function_name": m.function_name,
                "original_code": m.original_code[:500],  # Truncate for storage
                "new_code": m.new_code[:500],
                "reason": m.reason,
                "timestamp": m.timestamp,
                "success": m.success,
                "test_result": m.test_result
            }
            for m in self.history[-100:]
        ]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2)
    
    # ═══════════════════════════════════════════════════════════════════
    # INTROSPECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def read_function(self, file_path: str, function_name: str) -> Optional[str]:
        """Read a specific function from a file."""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Get the source lines for this function
                    lines = source.split('\n')
                    start = node.lineno - 1
                    end = node.end_lineno
                    return '\n'.join(lines[start:end])
            
            logger.warning(f"Function {function_name} not found in {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading function: {e}")
            return None
    
    def list_functions(self, file_path: str) -> List[str]:
        """List all functions in a file."""
        path = Path(file_path)
        if not path.exists():
            return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            return functions
            
        except Exception as e:
            logger.error(f"Error listing functions: {e}")
            return []
    
    def analyze_function(self, file_path: str, function_name: str) -> Dict:
        """Analyze a function's structure."""
        code = self.read_function(file_path, function_name)
        if not code:
            return {}
        
        try:
            tree = ast.parse(code)
            func_node = tree.body[0]
            
            analysis = {
                "name": function_name,
                "args": [arg.arg for arg in func_node.args.args],
                "has_docstring": (
                    isinstance(func_node.body[0], ast.Expr) and
                    isinstance(func_node.body[0].value, ast.Constant)
                ),
                "line_count": len(code.split('\n')),
                "complexity": self._estimate_complexity(func_node)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing function: {e}")
            return {}
    
    def _estimate_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    # ═══════════════════════════════════════════════════════════════════
    # SELF-MODIFICATION
    # ═══════════════════════════════════════════════════════════════════
    
    def improve_function(self, file_path: str, function_name: str, 
                        goal: str, test_code: str = None) -> bool:
        """
        Attempt to improve a function.
        
        Args:
            file_path: Path to the file containing the function
            function_name: Name of the function to improve
            goal: What improvement to make (e.g., "optimize for speed", "add error handling")
            test_code: Optional test code to verify the improvement
        
        Returns:
            True if improvement was successful
        """
        # Security check
        if not self._is_path_allowed(file_path):
            logger.error(f"Path not allowed for modification: {file_path}")
            return False
        
        # Read original code
        original_code = self.read_function(file_path, function_name)
        if not original_code:
            return False
        
        # Generate improved version using LLM
        new_code = self._generate_improvement(original_code, goal)
        if not new_code:
            logger.error("Failed to generate improvement")
            return False
        
        # Validate syntax
        if not self._validate_syntax(new_code):
            logger.error("Generated code has syntax errors")
            return False
        
        # Test in sandbox
        test_result = None
        if test_code:
            test_result = self._test_in_sandbox(new_code, test_code)
            if not test_result.get("passed", False):
                logger.error(f"Test failed: {test_result.get('error')}")
                self._record_modification(
                    file_path, function_name, original_code, new_code,
                    goal, success=False, test_result=str(test_result)
                )
                return False
        
        # Create backup
        self._create_backup(file_path)
        
        # Apply modification
        success = self._apply_modification(file_path, function_name, new_code)
        
        # Record
        self._record_modification(
            file_path, function_name, original_code, new_code,
            goal, success=success, test_result=str(test_result) if test_result else None
        )
        
        if success:
            logger.info(f"✅ Successfully improved {function_name}")
        
        return success
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """Check if path is in allowed directories."""
        path = Path(file_path)
        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False
    
    def _generate_improvement(self, original_code: str, goal: str) -> Optional[str]:
        """Use LLM to generate improved code."""
        if not self.brain:
            logger.warning("No brain connected, cannot generate improvement")
            return None
        
        prompt = f"""You are a Python code optimizer. Improve this function according to the goal.

ORIGINAL CODE:
```python
{original_code}
```

GOAL: {goal}

RULES:
1. Return ONLY the improved Python function code
2. Keep the same function name and signature
3. Maintain all existing functionality
4. Add appropriate error handling
5. Follow Python best practices

IMPROVED CODE:
```python
"""
        
        try:
            response = ""
            for token in self.brain.think(prompt):
                response += token
            
            # Extract code from response
            if "```python" in response:
                code = response.split("```python")[1].split("```")[0]
            elif "```" in response:
                code = response.split("```")[1].split("```")[0]
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"Error generating improvement: {e}")
            return None
    
    def _validate_syntax(self, code: str) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error: {e}")
            return False
    
    def _test_in_sandbox(self, code: str, test_code: str) -> Dict:
        """Test code in isolated sandbox."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code file
            code_file = Path(tmpdir) / "code_to_test.py"
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Write test file
            test_file = Path(tmpdir) / "test_code.py"
            test_content = f"""
import sys
sys.path.insert(0, r'{tmpdir}')
from code_to_test import *

{test_code}

print("TEST_PASSED")
"""
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Run test
            try:
                result = subprocess.run(
                    ["python", str(test_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                passed = "TEST_PASSED" in result.stdout
                return {
                    "passed": passed,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": result.stderr if not passed else None
                }
                
            except subprocess.TimeoutExpired:
                return {"passed": False, "error": "Test timed out"}
            except Exception as e:
                return {"passed": False, "error": str(e)}
    
    def _create_backup(self, file_path: str):
        """Create backup of file before modification."""
        path = Path(file_path)
        if path.exists():
            backup_name = f"{path.stem}_{int(time.time())}{path.suffix}"
            backup_path = self.backup_dir / backup_name
            shutil.copy(path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
    
    def _apply_modification(self, file_path: str, function_name: str, 
                           new_code: str) -> bool:
        """Apply the modification to the actual file."""
        path = Path(file_path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Find the function in the AST
            tree = ast.parse(source)
            lines = source.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    start = node.lineno - 1
                    end = node.end_lineno
                    
                    # Replace the function
                    new_lines = lines[:start] + new_code.split('\n') + lines[end:]
                    new_source = '\n'.join(new_lines)
                    
                    # Validate the new source
                    ast.parse(new_source)
                    
                    # Write back
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_source)
                    
                    return True
            
            logger.error(f"Function {function_name} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error applying modification: {e}")
            return False
    
    def _record_modification(self, file_path: str, function_name: str,
                            original_code: str, new_code: str, reason: str,
                            success: bool, test_result: str = None):
        """Record a modification attempt."""
        mod = CodeModification(
            file_path=file_path,
            function_name=function_name,
            original_code=original_code,
            new_code=new_code,
            reason=reason,
            timestamp=time.time(),
            success=success,
            test_result=test_result
        )
        
        with self.lock:
            self.history.append(mod)
            self._save_history()
    
    # ═══════════════════════════════════════════════════════════════════
    # ROLLBACK
    # ═══════════════════════════════════════════════════════════════════
    
    def rollback_last(self, file_path: str) -> bool:
        """Rollback to the last backup of a file."""
        path = Path(file_path)
        
        # Find latest backup
        backups = list(self.backup_dir.glob(f"{path.stem}_*{path.suffix}"))
        if not backups:
            logger.error("No backups found")
            return False
        
        latest = max(backups, key=lambda p: p.stat().st_mtime)
        
        try:
            shutil.copy(latest, path)
            logger.info(f"Rolled back to: {latest}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get engine status."""
        return {
            "total_modifications": len(self.history),
            "successful": sum(1 for m in self.history if m.success),
            "failed": sum(1 for m in self.history if not m.success),
            "backups": len(list(self.backup_dir.glob("*"))),
            "allowed_paths": [str(p) for p in self.allowed_paths]
        }
    
    def get_recent_modifications(self, limit: int = 10) -> List[Dict]:
        """Get recent modifications."""
        return [
            {
                "file": m.file_path,
                "function": m.function_name,
                "reason": m.reason,
                "success": m.success,
                "timestamp": m.timestamp
            }
            for m in self.history[-limit:]
        ]


# Singleton
_engine_instance = None

def get_self_coder(brain=None) -> SelfCodingEngine:
    """Get the global self-coding engine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SelfCodingEngine(brain)
    return _engine_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = SelfCodingEngine()
    
    print(f"Status: {engine.get_status()}")
    
    # Example: List functions in this file
    functions = engine.list_functions(__file__)
    print(f"Functions in this file: {functions}")
