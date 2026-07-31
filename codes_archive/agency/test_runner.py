"""
ZARA Automated Unit Test Runner
Self-testing capability for generated code.
"""
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("ZARA_TEST")

@dataclass
class TestResult:
    passed: bool
    output: str
    error: str
    duration_ms: float
    test_cases_run: int
    test_cases_passed: int

class TestRunner:
    """
    Automated testing for ZARA's self-generated code.
    Runs unit tests, catches errors, and reports results.
    """
    
    def __init__(self):
        self.test_timeout = 30  # seconds
        logger.info("Test Runner initialized.")
    
    def run_python_tests(self, code: str, test_code: str) -> TestResult:
        """
        Run test code against the generated code.
        """
        import time
        start = time.perf_counter()
        
        # Combine code and tests
        full_code = f"{code}\n\n{test_code}"
        
        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_path = f.name
            
            # Run tests
            result = subprocess.run(
                ["python", "-m", "pytest", temp_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=self.test_timeout
            )
            
            duration = (time.perf_counter() - start) * 1000
            
            # Parse output
            passed = result.returncode == 0
            
            # Count test cases from output
            tests_run = 0
            tests_passed = 0
            for line in result.stdout.split('\n'):
                if 'passed' in line.lower():
                    try:
                        tests_passed = int(line.split()[0])
                    except:
                        pass
                if 'failed' in line.lower() or 'passed' in line.lower():
                    tests_run = tests_passed  # Simplified
            
            return TestResult(
                passed=passed,
                output=result.stdout,
                error=result.stderr,
                duration_ms=duration,
                test_cases_run=tests_run,
                test_cases_passed=tests_passed
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                output="",
                error="Test execution timed out",
                duration_ms=self.test_timeout * 1000,
                test_cases_run=0,
                test_cases_passed=0
            )
        except Exception as e:
            return TestResult(
                passed=False,
                output="",
                error=str(e),
                duration_ms=0,
                test_cases_run=0,
                test_cases_passed=0
            )
        finally:
            # Cleanup
            try:
                Path(temp_path).unlink()
            except:
                pass
    
    def quick_syntax_check(self, code: str) -> Tuple[bool, str]:
        """
        Quick syntax check without execution.
        """
        try:
            compile(code, '<string>', 'exec')
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error at line {e.lineno}: {e.msg}"
    
    def generate_test_cases(self, function_code: str) -> str:
        """
        Auto-generate basic test cases for a function.
        This is a simplified version - in production, use AI.
        """
        import re
        
        # Extract function name
        match = re.search(r'def\s+(\w+)\s*\((.*?)\):', function_code)
        if not match:
            return ""
        
        func_name = match.group(1)
        params = match.group(2)
        
        # Generate basic test skeleton
        test_code = f'''
import pytest

def test_{func_name}_basic():
    """Basic test for {func_name}"""
    # TODO: Add actual test assertions
    result = {func_name}()  # Add appropriate arguments
    assert result is not None

def test_{func_name}_edge_case():
    """Edge case test for {func_name}"""
    # TODO: Add edge case tests
    pass
'''
        return test_code
    
    def run_with_coverage(self, code_file: Path, test_file: Path) -> Dict:
        """
        Run tests with coverage analysis.
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file), 
                 f"--cov={code_file.stem}", "--cov-report=term-missing"],
                capture_output=True,
                text=True,
                timeout=self.test_timeout
            )
            
            # Parse coverage
            coverage = 0
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line:
                    parts = line.split()
                    for p in parts:
                        if '%' in p:
                            coverage = int(p.replace('%', ''))
                            break
            
            return {
                "passed": result.returncode == 0,
                "coverage_percent": coverage,
                "output": result.stdout
            }
            
        except Exception as e:
            return {
                "passed": False,
                "coverage_percent": 0,
                "output": str(e)
            }
