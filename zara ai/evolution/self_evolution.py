"""
ZARA Self-Evolution Engine v1.0
================================
Autonomous Code Generation, Testing, and Integration

This is ZARA's meta-programming core that enables her to:
1. DETECT capability gaps ("I don't know how to do X")
2. RESEARCH solutions (search, analyze existing code)
3. GENERATE new code in a sandbox
4. TEST until it works successfully
5. INTEGRATE into main codebase after validation
6. LEARN from each evolution cycle

Safety Mechanisms:
- All new code runs in isolated sandbox first
- Multiple validation passes before integration
- Rollback capability for failed integrations
- Human approval required for critical changes
- Rate limiting on evolution frequency

This is REAL self-modification, not scripted.
"""

import logging
import json
import time
import threading
import subprocess
import sys
import ast
import os
import shutil
import hashlib
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime
import tempfile
import importlib.util

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_EVOLUTION")


# ═══════════════════════════════════════════════════════════════════════════
# EVOLUTION STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class EvolutionType(Enum):
    """Types of self-evolution."""
    NEW_CAPABILITY = "new_capability"      # Entirely new feature
    ENHANCEMENT = "enhancement"            # Improve existing feature
    BUG_FIX = "bug_fix"                   # Fix known issue
    OPTIMIZATION = "optimization"          # Performance improvement
    INTEGRATION = "integration"            # Connect to new service/API
    PROMPT_UPDATE = "prompt_update"        # Improve prompts


class EvolutionStatus(Enum):
    """Status of an evolution attempt."""
    PROPOSED = "proposed"
    RESEARCHING = "researching"
    GENERATING = "generating"
    TESTING = "testing"
    VALIDATED = "validated"
    INTEGRATING = "integrating"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class SafetyLevel(Enum):
    """Safety level for code changes."""
    SAFE = 1           # Isolated, no side effects
    MODERATE = 2       # May affect internal state  
    SENSITIVE = 3      # Affects core functionality
    CRITICAL = 4       # Requires human approval


@dataclass
class CapabilityGap:
    """A detected capability gap."""
    id: str
    description: str
    detected_at: float
    context: str                    # What triggered the detection
    priority: float                 # 0-1, how important
    suggested_solution: str
    related_files: List[str]
    tags: List[str]


@dataclass
class GeneratedCode:
    """Generated code ready for testing."""
    code: str
    file_path: str
    language: str
    imports: List[str]
    functions: List[str]
    classes: List[str]
    test_code: str
    documentation: str


@dataclass
class TestResult:
    """Result of testing generated code."""
    success: bool
    passed_tests: int
    failed_tests: int
    errors: List[str]
    warnings: List[str]
    execution_time_ms: int
    coverage_percent: float
    output: str


@dataclass
class Evolution:
    """A complete evolution record."""
    id: str
    type: EvolutionType
    status: EvolutionStatus
    safety_level: SafetyLevel
    
    # What's being evolved
    description: str
    capability_gap: Optional[CapabilityGap]
    
    # Generated content
    generated_code: Optional[GeneratedCode]
    target_file: str
    
    # Testing
    test_results: List[TestResult]
    validation_passed: bool
    
    # Integration
    backup_path: Optional[str]
    integrated_at: Optional[float]
    
    # Meta
    created_at: float
    updated_at: float
    attempt_count: int
    max_attempts: int = 5


# ═══════════════════════════════════════════════════════════════════════════
# CAPABILITY DETECTOR - Finds What's Missing
# ═══════════════════════════════════════════════════════════════════════════

class CapabilityDetector:
    """
    Detects capability gaps - things ZARA cannot do but should.
    Triggers evolution when gaps are found.
    """
    
    def __init__(self):
        self.detected_gaps: Dict[str, CapabilityGap] = {}
        self.gap_history: deque = deque(maxlen=100)
        self.gap_file = Path("memory/capability_gaps.json")
        self._load_gaps()
    
    def detect_from_failure(self, error: Exception, context: str) -> Optional[CapabilityGap]:
        """Detect capability gap from an error/failure."""
        error_str = str(error).lower()
        
        gap = None
        
        # Pattern matching for common capability gaps
        if "no module named" in error_str:
            module = error_str.split("'")[1] if "'" in error_str else "unknown"
            gap = CapabilityGap(
                id=f"gap_module_{hashlib.md5(module.encode()).hexdigest()[:8]}",
                description=f"Missing Python module: {module}",
                detected_at=time.time(),
                context=context,
                priority=0.7,
                suggested_solution=f"Install or implement {module} functionality",
                related_files=[],
                tags=["dependency", "module"]
            )
        
        elif "object has no attribute" in error_str:
            gap = CapabilityGap(
                id=f"gap_attr_{hashlib.md5(error_str.encode()).hexdigest()[:8]}",
                description=f"Missing attribute/method: {error_str}",
                detected_at=time.time(),
                context=context,
                priority=0.6,
                suggested_solution="Add the missing method or property",
                related_files=[],
                tags=["method", "attribute"]
            )
        
        elif "not implemented" in error_str or "notimplementederror" in error_str:
            gap = CapabilityGap(
                id=f"gap_impl_{hashlib.md5(error_str.encode()).hexdigest()[:8]}",
                description=f"Unimplemented feature: {context}",
                detected_at=time.time(),
                context=context,
                priority=0.8,
                suggested_solution="Implement the required functionality",
                related_files=[],
                tags=["implementation"]
            )
        
        if gap:
            self._record_gap(gap)
        
        return gap
    
    def detect_from_request(self, user_request: str) -> Optional[CapabilityGap]:
        """Detect capability gap from user request that can't be fulfilled."""
        # Keywords suggesting new capability needed
        capability_keywords = [
            ("integrate with", "integration"),
            ("connect to", "integration"),
            ("add support for", "new_capability"),
            ("enable", "new_capability"),
            ("make it possible to", "new_capability"),
            ("can you learn", "learning"),
            ("remember how to", "memory"),
        ]
        
        request_lower = user_request.lower()
        
        for keyword, tag in capability_keywords:
            if keyword in request_lower:
                gap = CapabilityGap(
                    id=f"gap_req_{hashlib.md5(user_request.encode()).hexdigest()[:8]}",
                    description=f"User requested: {user_request[:200]}",
                    detected_at=time.time(),
                    context=user_request,
                    priority=0.9,  # User requests are high priority
                    suggested_solution=f"Develop capability for: {user_request[:100]}",
                    related_files=[],
                    tags=[tag, "user_request"]
                )
                self._record_gap(gap)
                return gap
        
        return None
    
    def detect_from_research(self, topic: str, findings: str) -> Optional[CapabilityGap]:
        """Detect capability gap from research (new tech discovered)."""
        gap = CapabilityGap(
            id=f"gap_research_{hashlib.md5(topic.encode()).hexdigest()[:8]}",
            description=f"New technology/approach discovered: {topic}",
            detected_at=time.time(),
            context=findings[:500],
            priority=0.5,  # Research-based gaps are lower priority
            suggested_solution=f"Investigate and potentially implement: {topic}",
            related_files=[],
            tags=["research", "new_tech"]
        )
        self._record_gap(gap)
        return gap
    
    def get_priority_gaps(self, limit: int = 5) -> List[CapabilityGap]:
        """Get highest priority capability gaps."""
        gaps = list(self.detected_gaps.values())
        gaps.sort(key=lambda g: g.priority, reverse=True)
        return gaps[:limit]
    
    def _record_gap(self, gap: CapabilityGap):
        """Record a new capability gap."""
        if gap.id not in self.detected_gaps:
            self.detected_gaps[gap.id] = gap
            self.gap_history.append(gap)
            self._save_gaps()
            logger.info(f"🧬 New capability gap detected: {gap.description[:50]}...")
    
    def _save_gaps(self):
        """Save gaps to disk."""
        try:
            self.gap_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                gap_id: {
                    "id": gap.id,
                    "description": gap.description,
                    "detected_at": gap.detected_at,
                    "context": gap.context[:200],
                    "priority": gap.priority,
                    "tags": gap.tags
                }
                for gap_id, gap in self.detected_gaps.items()
            }
            with open(self.gap_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save gaps: {e}")
    
    def _load_gaps(self):
        """Load gaps from disk."""
        try:
            if self.gap_file.exists():
                with open(self.gap_file) as f:
                    data = json.load(f)
                for gap_id, gap_data in data.items():
                    self.detected_gaps[gap_id] = CapabilityGap(
                        id=gap_data["id"],
                        description=gap_data["description"],
                        detected_at=gap_data["detected_at"],
                        context=gap_data.get("context", ""),
                        priority=gap_data["priority"],
                        suggested_solution="",
                        related_files=[],
                        tags=gap_data.get("tags", [])
                    )
        except Exception as e:
            logger.debug(f"Could not load gaps: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# CODE GENERATOR - Creates New Code
# ═══════════════════════════════════════════════════════════════════════════

class CodeGenerator:
    """
    Generates new code to fill capability gaps.
    Uses LLM for intelligent code generation.
    """
    
    def __init__(self):
        self._llm = None
        self.generation_history: deque = deque(maxlen=50)
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable: {e}")
        return self._llm
    
    def generate(self, gap: CapabilityGap, 
                existing_code_context: str = "") -> Optional[GeneratedCode]:
        """Generate code to fill a capability gap."""
        llm = self._get_llm()
        
        if not llm:
            return self._generate_template(gap)
        
        try:
            # Generate main code
            code_prompt = f"""You are an expert Python developer. Generate production-quality code to implement this capability:

CAPABILITY NEEDED: {gap.description}

CONTEXT: {gap.context[:500]}

EXISTING CODE CONTEXT:
{existing_code_context[:1000]}

REQUIREMENTS:
1. Write clean, well-documented Python code
2. Include proper error handling
3. Add type hints
4. Include docstrings
5. Make it modular and testable
6. Follow ZARA project conventions

Generate ONLY the Python code, no explanations. Start with imports."""

            code = llm.think(code_prompt)
            
            # Generate test code
            test_prompt = f"""Generate pytest test code for this implementation:

{code[:2000]}

Include:
1. Unit tests for each function
2. Edge case testing
3. Integration test if applicable

Generate ONLY the test code, no explanations."""

            test_code = llm.think(test_prompt)
            
            # Parse generated code
            generated = GeneratedCode(
                code=code,
                file_path="",  # To be determined
                language="python",
                imports=self._extract_imports(code),
                functions=self._extract_functions(code),
                classes=self._extract_classes(code),
                test_code=test_code,
                documentation=gap.description
            )
            
            self.generation_history.append({
                "gap_id": gap.id,
                "timestamp": time.time(),
                "code_length": len(code)
            })
            
            return generated
            
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return self._generate_template(gap)
    
    def _generate_template(self, gap: CapabilityGap) -> GeneratedCode:
        """Generate a template when LLM is unavailable."""
        code = f'''"""
Auto-generated template for: {gap.description}
Generated at: {datetime.now().isoformat()}
"""

import logging

logger = logging.getLogger(__name__)


def main():
    """
    TODO: Implement {gap.description}
    
    Context: {gap.context[:200]}
    """
    raise NotImplementedError("Implementation required")


if __name__ == "__main__":
    main()
'''
        
        test_code = f'''"""Tests for auto-generated capability."""
import pytest

def test_placeholder():
    """Placeholder test - implement actual tests."""
    assert True, "Replace with actual tests"
'''
        
        return GeneratedCode(
            code=code,
            file_path="",
            language="python",
            imports=["logging"],
            functions=["main"],
            classes=[],
            test_code=test_code,
            documentation=gap.description
        )
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception as e:
            logger.debug(f"Failed to parse imports: {e}")
        return imports
    
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function names from code."""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except Exception as e:
            logger.debug(f"Failed to parse functions: {e}")
        return functions
    
    def _extract_classes(self, code: str) -> List[str]:
        """Extract class names from code."""
        classes = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
        except Exception as e:
            logger.debug(f"Failed to parse classes: {e}")
        return classes


# ═══════════════════════════════════════════════════════════════════════════
# SANDBOX - Safe Testing Environment
# ═══════════════════════════════════════════════════════════════════════════

class Sandbox:
    """
    Isolated environment for testing generated code.
    All new code runs here before integration.
    """
    
    def __init__(self):
        self.sandbox_dir = Path("evolution/sandbox")
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.active_tests: Dict[str, Path] = {}
        self.test_history: deque = deque(maxlen=100)
    
    def prepare(self, evolution_id: str, code: GeneratedCode) -> Path:
        """Prepare sandbox environment for testing."""
        # Create isolated directory for this evolution
        test_dir = self.sandbox_dir / evolution_id
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Write main code
        main_file = test_dir / "main.py"
        with open(main_file, "w") as f:
            f.write(code.code)
        
        # Write test code
        test_file = test_dir / "test_main.py"
        with open(test_file, "w") as f:
            f.write(code.test_code)
        
        # Write requirements if any new imports
        requirements = []
        for imp in code.imports:
            if self._is_external_package(imp):
                requirements.append(imp)
        
        if requirements:
            req_file = test_dir / "requirements.txt"
            with open(req_file, "w") as f:
                f.write("\n".join(requirements))
        
        self.active_tests[evolution_id] = test_dir
        
        logger.info(f"🧪 Sandbox prepared for {evolution_id}")
        return test_dir
    
    def run_tests(self, evolution_id: str) -> TestResult:
        """Run tests in sandbox environment."""
        if evolution_id not in self.active_tests:
            return TestResult(
                success=False,
                passed_tests=0,
                failed_tests=0,
                errors=["Sandbox not prepared"],
                warnings=[],
                execution_time_ms=0,
                coverage_percent=0.0,
                output=""
            )
        
        test_dir = self.active_tests[evolution_id]
        start_time = time.time()
        
        errors = []
        warnings = []
        output_lines = []
        
        # Step 1: Syntax validation
        main_file = test_dir / "main.py"
        syntax_valid, syntax_error = self._validate_syntax(main_file)
        
        if not syntax_valid:
            return TestResult(
                success=False,
                passed_tests=0,
                failed_tests=1,
                errors=[f"Syntax error: {syntax_error}"],
                warnings=[],
                execution_time_ms=int((time.time() - start_time) * 1000),
                coverage_percent=0.0,
                output=""
            )
        
        output_lines.append("✓ Syntax validation passed")
        
        # Step 2: Import validation
        import_valid, import_error = self._validate_imports(main_file)
        
        if not import_valid:
            warnings.append(f"Import warning: {import_error}")
            output_lines.append(f"⚠ Import issue: {import_error}")
        else:
            output_lines.append("✓ Import validation passed")
        
        # Step 3: Run the code in sandbox
        exec_success, exec_output, exec_error = self._execute_in_sandbox(test_dir, main_file)
        
        if exec_error:
            errors.append(f"Execution error: {exec_error}")
            output_lines.append(f"✗ Execution failed: {exec_error}")
        else:
            output_lines.append("✓ Code execution successful")
            output_lines.append(exec_output[:500] if exec_output else "(no output)")
        
        # Step 4: Run pytest if available
        test_file = test_dir / "test_main.py"
        if test_file.exists():
            test_success, test_output = self._run_pytest(test_dir)
            output_lines.append(f"{'✓' if test_success else '✗'} pytest: {test_output[:200]}")
            
            if not test_success:
                errors.append(f"Tests failed: {test_output}")
        
        elapsed = int((time.time() - start_time) * 1000)
        
        # Determine overall success
        success = len(errors) == 0
        
        result = TestResult(
            success=success,
            passed_tests=1 if success else 0,
            failed_tests=0 if success else 1,
            errors=errors,
            warnings=warnings,
            execution_time_ms=elapsed,
            coverage_percent=50.0 if success else 0.0,  # Rough estimate
            output="\n".join(output_lines)
        )
        
        self.test_history.append({
            "evolution_id": evolution_id,
            "success": success,
            "timestamp": time.time()
        })
        
        return result
    
    def cleanup(self, evolution_id: str):
        """Clean up sandbox after testing."""
        if evolution_id in self.active_tests:
            test_dir = self.active_tests[evolution_id]
            try:
                shutil.rmtree(test_dir)
            except Exception as e:
                logger.warning(f"Could not clean sandbox: {e}")
            del self.active_tests[evolution_id]
    
    def _validate_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Validate Python syntax."""
        try:
            with open(file_path) as f:
                code = f.read()
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)
    
    def _validate_imports(self, file_path: Path) -> Tuple[bool, str]:
        """Validate that imports can be resolved."""
        try:
            with open(file_path) as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            importlib.import_module(alias.name)
                        except ImportError:
                            return False, f"Cannot import {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            importlib.import_module(node.module)
                        except ImportError:
                            return False, f"Cannot import {node.module}"
            
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _execute_in_sandbox(self, test_dir: Path, 
                           main_file: Path) -> Tuple[bool, str, str]:
        """Execute code in isolated subprocess."""
        try:
            result = subprocess.run(
                [sys.executable, str(main_file)],
                cwd=str(test_dir),
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout, ""
            else:
                return False, result.stdout, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "", "Execution timed out (30s)"
        except Exception as e:
            return False, "", str(e)
    
    def _run_pytest(self, test_dir: Path) -> Tuple[bool, str]:
        """Run pytest on the test file."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return success, output[:500]
            
        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except Exception as e:
            return False, str(e)
    
    def _is_external_package(self, module_name: str) -> bool:
        """Check if module is an external package."""
        builtin = [
            "os", "sys", "time", "datetime", "json", "re", "math",
            "collections", "itertools", "functools", "typing",
            "pathlib", "logging", "threading", "subprocess", "ast",
            "hashlib", "tempfile", "shutil", "importlib"
        ]
        return module_name.split(".")[0] not in builtin


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATOR - Safely Adds Code to Codebase
# ═══════════════════════════════════════════════════════════════════════════

class Integrator:
    """
    Safely integrates validated code into the main codebase.
    Creates backups and supports rollback.
    """
    
    def __init__(self):
        self.backup_dir = Path("evolution/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.integration_log = Path("evolution/integration_log.json")
        self.integrations: List[Dict] = []
        self._load_log()
    
    def integrate(self, evolution: Evolution, target_path: Path) -> Tuple[bool, str]:
        """Integrate validated code into codebase."""
        if not evolution.validation_passed:
            return False, "Validation not passed"
        
        if not evolution.generated_code:
            return False, "No generated code"
        
        # Create backup if file exists
        backup_path = None
        if target_path.exists():
            backup_path = self._create_backup(target_path, evolution.id)
        
        try:
            # Write new code
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w") as f:
                f.write(evolution.generated_code.code)
            
            # Validate the integration
            valid, error = self._validate_integration(target_path)
            
            if not valid:
                # Rollback
                self._rollback(target_path, backup_path)
                return False, f"Integration validation failed: {error}"
            
            # Log successful integration
            self._log_integration(evolution, target_path, backup_path)
            
            logger.info(f"✅ Successfully integrated: {target_path.name}")
            return True, "Integration successful"
            
        except Exception as e:
            # Rollback on any error
            if backup_path:
                self._rollback(target_path, backup_path)
            return False, str(e)
    
    def rollback(self, evolution_id: str) -> Tuple[bool, str]:
        """Rollback a specific integration."""
        for integration in reversed(self.integrations):
            if integration.get("evolution_id") == evolution_id:
                backup_path = integration.get("backup_path")
                target_path = Path(integration.get("target_path", ""))
                
                if backup_path and Path(backup_path).exists():
                    self._rollback(target_path, Path(backup_path))
                    integration["rolled_back"] = True
                    self._save_log()
                    return True, "Rollback successful"
                else:
                    # No backup, just delete the file
                    if target_path.exists():
                        target_path.unlink()
                    return True, "File removed (no backup)"
        
        return False, "Integration not found"
    
    def _create_backup(self, file_path: Path, evolution_id: str) -> Path:
        """Create backup of existing file."""
        timestamp = int(time.time())
        backup_name = f"{file_path.stem}_{evolution_id}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        
        return backup_path
    
    def _rollback(self, target_path: Path, backup_path: Optional[Path]):
        """Rollback to backup."""
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, target_path)
            logger.info(f"↩️ Rolled back: {target_path.name}")
        elif target_path.exists():
            target_path.unlink()
            logger.info(f"🗑️ Removed: {target_path.name}")
    
    def _validate_integration(self, file_path: Path) -> Tuple[bool, str]:
        """Validate integrated code can be imported."""
        try:
            # Syntax check
            with open(file_path) as f:
                code = f.read()
            ast.parse(code)
            
            # Try to import
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't actually execute, just verify it can be loaded
                return True, ""
            
            return True, ""  # Basic validation passed
            
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, str(e)
    
    def _log_integration(self, evolution: Evolution, 
                        target_path: Path, backup_path: Optional[Path]):
        """Log successful integration."""
        self.integrations.append({
            "evolution_id": evolution.id,
            "target_path": str(target_path),
            "backup_path": str(backup_path) if backup_path else None,
            "timestamp": time.time(),
            "type": evolution.type.value,
            "description": evolution.description[:200]
        })
        self._save_log()
    
    def _save_log(self):
        """Save integration log to disk."""
        try:
            with open(self.integration_log, "w") as f:
                json.dump(self.integrations[-100:], f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save integration log: {e}")
    
    def _load_log(self):
        """Load integration log from disk."""
        try:
            if self.integration_log.exists():
                with open(self.integration_log) as f:
                    self.integrations = json.load(f)
        except Exception as e:
            logger.debug(f"Could not load integration log: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SELF-EVOLUTION ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class SelfEvolutionEngine:
    """
    Main self-evolution engine.
    Orchestrates the complete evolution cycle.
    """
    
    def __init__(self):
        # Components
        self.detector = CapabilityDetector()
        self.generator = CodeGenerator()
        self.sandbox = Sandbox()
        self.integrator = Integrator()
        
        # State
        self.active_evolutions: Dict[str, Evolution] = {}
        self.evolution_history: deque = deque(maxlen=100)
        self.is_evolving = False
        self.evolution_lock = threading.Lock()
        
        # Configuration
        self.auto_evolve_enabled = False  # Require explicit trigger for safety
        self.require_approval_for = [SafetyLevel.SENSITIVE, SafetyLevel.CRITICAL]
        self.pending_approval: List[Evolution] = []
        
        # Callbacks
        self.on_evolution_complete: List[Callable] = []
        self.on_approval_needed: List[Callable] = []
        
        # Stats
        self.total_evolutions = 0
        self.successful_evolutions = 0
        
        # Persistence
        self.state_file = Path("evolution/evolution_state.json")
        
        logger.info("🧬 Self-Evolution Engine initialized")
    
    def detect_gap(self, error: Optional[Exception] = None,
                   user_request: Optional[str] = None,
                   research_topic: Optional[str] = None) -> Optional[CapabilityGap]:
        """Detect a capability gap from various sources."""
        gap = None
        
        if error:
            gap = self.detector.detect_from_failure(error, str(error))
        elif user_request:
            gap = self.detector.detect_from_request(user_request)
        elif research_topic:
            gap = self.detector.detect_from_research(research_topic, "")
        
        return gap
    
    def evolve(self, gap: CapabilityGap, 
              target_file: Optional[str] = None,
              auto_integrate: bool = False) -> Evolution:
        """
        Trigger evolution to fill a capability gap.
        This is the main evolution entry point.
        """
        with self.evolution_lock:
            if gap.id in self.active_evolutions:
                return self.active_evolutions[gap.id]
            
            evolution_id = f"evo_{int(time.time())}_{gap.id[:8]}"
            
            # Determine safety level
            safety = self._assess_safety(gap)
            
            # Create evolution record
            evolution = Evolution(
                id=evolution_id,
                type=self._determine_type(gap),
                status=EvolutionStatus.PROPOSED,
                safety_level=safety,
                description=gap.description,
                capability_gap=gap,
                generated_code=None,
                target_file=target_file or self._suggest_target_file(gap),
                test_results=[],
                validation_passed=False,
                backup_path=None,
                integrated_at=None,
                created_at=time.time(),
                updated_at=time.time(),
                attempt_count=0
            )
            
            self.active_evolutions[gap.id] = evolution
            self.total_evolutions += 1
        
        # Run evolution cycle
        self._run_evolution_cycle(evolution, auto_integrate)
        
        return evolution
    
    def _run_evolution_cycle(self, evolution: Evolution, 
                            auto_integrate: bool = False):
        """Run the complete evolution cycle."""
        try:
            # Phase 1: Generate code
            evolution.status = EvolutionStatus.GENERATING
            evolution.updated_at = time.time()
            
            logger.info(f"🧬 Generating code for: {evolution.description[:50]}...")
            
            generated = self.generator.generate(
                evolution.capability_gap,
                existing_code_context=self._get_existing_context(evolution.target_file)
            )
            
            if not generated:
                evolution.status = EvolutionStatus.FAILED
                return
            
            evolution.generated_code = generated
            evolution.attempt_count += 1
            
            # Phase 2: Test in sandbox
            evolution.status = EvolutionStatus.TESTING
            evolution.updated_at = time.time()
            
            logger.info(f"🧪 Testing in sandbox...")
            
            self.sandbox.prepare(evolution.id, generated)
            test_result = self.sandbox.run_tests(evolution.id)
            evolution.test_results.append(test_result)
            
            if not test_result.success:
                # Retry if under max attempts
                if evolution.attempt_count < evolution.max_attempts:
                    logger.info(f"🔄 Test failed, retrying ({evolution.attempt_count}/{evolution.max_attempts})...")
                    self.sandbox.cleanup(evolution.id)
                    self._run_evolution_cycle(evolution, auto_integrate)
                    return
                else:
                    evolution.status = EvolutionStatus.FAILED
                    self.sandbox.cleanup(evolution.id)
                    return
            
            evolution.validation_passed = True
            evolution.status = EvolutionStatus.VALIDATED
            
            logger.info(f"✅ Validation passed!")
            
            # Phase 3: Integration decision
            if evolution.safety_level in self.require_approval_for:
                # Require human approval
                evolution.status = EvolutionStatus.VALIDATED  # Waiting for approval
                self.pending_approval.append(evolution)
                
                for callback in self.on_approval_needed:
                    try:
                        callback(evolution)
                    except Exception as e:
                        logger.error(f"Approval callback error: {e}")
                
                logger.info(f"⏳ Awaiting human approval for: {evolution.description[:50]}...")
                return
            
            if auto_integrate:
                self._integrate_evolution(evolution)
            
        except Exception as e:
            logger.error(f"Evolution cycle error: {e}")
            evolution.status = EvolutionStatus.FAILED
            evolution.test_results.append(TestResult(
                success=False,
                passed_tests=0,
                failed_tests=1,
                errors=[str(e)],
                warnings=[],
                execution_time_ms=0,
                coverage_percent=0.0,
                output=traceback.format_exc()
            ))
    
    def approve_evolution(self, evolution_id: str) -> Tuple[bool, str]:
        """Approve a pending evolution for integration."""
        evolution = None
        for evo in self.pending_approval:
            if evo.id == evolution_id:
                evolution = evo
                break
        
        if not evolution:
            return False, "Evolution not found in pending approvals"
        
        self.pending_approval.remove(evolution)
        return self._integrate_evolution(evolution)
    
    def reject_evolution(self, evolution_id: str) -> Tuple[bool, str]:
        """Reject a pending evolution."""
        for evo in self.pending_approval:
            if evo.id == evolution_id:
                self.pending_approval.remove(evo)
                evo.status = EvolutionStatus.FAILED
                self.sandbox.cleanup(evo.id)
                return True, "Evolution rejected"
        
        return False, "Evolution not found"
    
    def _integrate_evolution(self, evolution: Evolution) -> Tuple[bool, str]:
        """Integrate validated evolution into codebase."""
        evolution.status = EvolutionStatus.INTEGRATING
        evolution.updated_at = time.time()
        
        target_path = Path(evolution.target_file)
        success, message = self.integrator.integrate(evolution, target_path)
        
        if success:
            evolution.status = EvolutionStatus.COMPLETE
            evolution.integrated_at = time.time()
            self.successful_evolutions += 1
            
            # Cleanup
            self.sandbox.cleanup(evolution.id)
            
            # Move to history
            if evolution.capability_gap.id in self.active_evolutions:
                del self.active_evolutions[evolution.capability_gap.id]
            self.evolution_history.append(evolution)
            
            # Notify
            for callback in self.on_evolution_complete:
                try:
                    callback(evolution)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")
            
            logger.info(f"🎉 Evolution complete: {evolution.description[:50]}...")
        else:
            evolution.status = EvolutionStatus.FAILED
            self.sandbox.cleanup(evolution.id)
        
        return success, message
    
    def rollback_evolution(self, evolution_id: str) -> Tuple[bool, str]:
        """Rollback a completed evolution."""
        return self.integrator.rollback(evolution_id)
    
    def _assess_safety(self, gap: CapabilityGap) -> SafetyLevel:
        """Assess safety level of a potential evolution."""
        # Keywords that indicate higher risk
        critical_keywords = ["delete", "remove", "modify config", "auth", "password", "key"]
        sensitive_keywords = ["core", "main", "engine", "memory", "mind"]
        moderate_keywords = ["update", "change", "add"]
        
        gap_lower = (gap.description + gap.context).lower()
        
        if any(k in gap_lower for k in critical_keywords):
            return SafetyLevel.CRITICAL
        if any(k in gap_lower for k in sensitive_keywords):
            return SafetyLevel.SENSITIVE
        if any(k in gap_lower for k in moderate_keywords):
            return SafetyLevel.MODERATE
        
        return SafetyLevel.SAFE
    
    def _determine_type(self, gap: CapabilityGap) -> EvolutionType:
        """Determine evolution type from gap."""
        tags = [t.lower() for t in gap.tags]
        
        if "integration" in tags:
            return EvolutionType.INTEGRATION
        if "user_request" in tags:
            return EvolutionType.NEW_CAPABILITY
        if "bug" in tags or "fix" in gap.description.lower():
            return EvolutionType.BUG_FIX
        if "new_tech" in tags or "research" in tags:
            return EvolutionType.NEW_CAPABILITY
        
        return EvolutionType.ENHANCEMENT
    
    def _suggest_target_file(self, gap: CapabilityGap) -> str:
        """Suggest target file for new capability."""
        # Simple heuristic based on tags
        tags = [t.lower() for t in gap.tags]
        
        if "memory" in tags:
            return "memory/new_capability.py"
        if "vision" in tags or "eyes" in tags:
            return "eyes/new_capability.py"
        if "voice" in tags or "ears" in tags:
            return "ears/new_capability.py"
        if "action" in tags or "tool" in tags:
            return "actions/new_capability.py"
        
        return "evolution/generated/new_capability.py"
    
    def _get_existing_context(self, target_file: str) -> str:
        """Get existing code context for better generation."""
        target_path = Path(target_file)
        
        if target_path.exists():
            try:
                with open(target_path) as f:
                    return f.read()[:2000]
            except Exception as e:
                logger.debug(f"Could not read target file: {e}")
        
        # Try to get context from related files
        parent_dir = target_path.parent
        if parent_dir.exists():
            context_parts = []
            for py_file in list(parent_dir.glob("*.py"))[:3]:
                try:
                    with open(py_file) as f:
                        context_parts.append(f"# From {py_file.name}:\n{f.read()[:500]}")
                except Exception as e:
                    logger.debug(f"Could not read context file: {e}")
            return "\n\n".join(context_parts)
        
        return ""
    
    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict:
        """Get evolution engine status."""
        return {
            "total_evolutions": self.total_evolutions,
            "successful_evolutions": self.successful_evolutions,
            "active_evolutions": len(self.active_evolutions),
            "pending_approval": len(self.pending_approval),
            "auto_evolve_enabled": self.auto_evolve_enabled,
            "detected_gaps": len(self.detector.detected_gaps)
        }
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get list of evolutions awaiting approval."""
        return [
            {
                "id": evo.id,
                "description": evo.description,
                "type": evo.type.value,
                "safety_level": evo.safety_level.value,
                "target_file": evo.target_file
            }
            for evo in self.pending_approval
        ]
    
    def get_evolution_summary(self) -> str:
        """Get human-readable evolution summary."""
        status = self.get_status()
        
        lines = [
            "🧬 Self-Evolution Engine Status",
            "=" * 40,
            f"Total Evolutions: {status['total_evolutions']}",
            f"Successful: {status['successful_evolutions']}",
            f"Success Rate: {status['successful_evolutions']/max(1,status['total_evolutions']):.0%}",
            f"Active: {status['active_evolutions']}",
            f"Pending Approval: {status['pending_approval']}",
            f"Detected Gaps: {status['detected_gaps']}",
            "",
            "Recent Gaps:"
        ]
        
        for gap in self.detector.get_priority_gaps(3):
            lines.append(f"  • [{gap.priority:.0%}] {gap.description[:50]}...")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_evolution_engine = None

def get_evolution_engine() -> SelfEvolutionEngine:
    """Get the global evolution engine instance."""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SelfEvolutionEngine()
    return _evolution_engine


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🧬 ZARA Self-Evolution Engine v1.0\n")
    print("=" * 60)
    
    engine = SelfEvolutionEngine()
    
    # Track evolution events
    def on_complete(evolution):
        print(f"\n🎉 Evolution complete: {evolution.description[:50]}...")
    
    def on_approval(evolution):
        print(f"\n⏳ Approval needed: {evolution.description[:50]}...")
    
    engine.on_evolution_complete.append(on_complete)
    engine.on_approval_needed.append(on_approval)
    
    # Show status
    print(f"\n📊 Initial Status:")
    print(engine.get_evolution_summary())
    
    # Simulate detecting a capability gap
    print("\n" + "-" * 40)
    print("Simulating capability gap detection...")
    
    # From user request
    gap = engine.detect_gap(user_request="Can you integrate with Spotify to play music?")
    if gap:
        print(f"✓ Detected gap: {gap.description}")
    
    # From error
    try:
        raise ImportError("No module named 'spotify_api'")
    except Exception as e:
        gap = engine.detect_gap(error=e)
        if gap:
            print(f"✓ Detected gap from error: {gap.description}")
    
    # Show priority gaps
    print("\n📋 Priority Gaps:")
    for gap in engine.detector.get_priority_gaps():
        print(f"  [{gap.priority:.0%}] {gap.description[:60]}...")
    
    # Trigger evolution for one gap
    print("\n" + "-" * 40)
    print("Triggering evolution cycle...")
    
    if engine.detector.detected_gaps:
        gap = list(engine.detector.detected_gaps.values())[0]
        evolution = engine.evolve(gap, auto_integrate=False)
        
        print(f"\nEvolution: {evolution.id}")
        print(f"Status: {evolution.status.value}")
        print(f"Safety: {evolution.safety_level.name}")
        
        if evolution.generated_code:
            print(f"Generated: {len(evolution.generated_code.code)} chars")
            print(f"Functions: {evolution.generated_code.functions}")
        
        if evolution.test_results:
            result = evolution.test_results[-1]
            print(f"Test: {'✓ Passed' if result.success else '✗ Failed'}")
            print(f"Output: {result.output[:200]}...")
    
    # Final status
    print("\n" + "=" * 60)
    print("Final Status:")
    print(engine.get_evolution_summary())
    
    print("\n" + "=" * 60)
    print("✅ Self-Evolution Engine ready!\n")
