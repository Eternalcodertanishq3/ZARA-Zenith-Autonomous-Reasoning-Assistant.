"""
ZARA Code Generator - Enhanced Code Extraction & Validation
"""
import re
import ast
import logging

logger = logging.getLogger("ZARA_CODEGEN")

class CodeGenerator:
    """
    Extracts and validates code from LLM responses.
    Supports Python, JavaScript, Shell, and generic code blocks.
    """
    
    SUPPORTED_LANGUAGES = ["python", "javascript", "js", "bash", "shell", "powershell", "sql"]
    
    @staticmethod
    def extract_python(text: str) -> str:
        """
        Extracts python code from markdown blocks.
        Returns first valid Python block found.
        """
        # Try explicit python blocks first
        pattern = r"```python\s*(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            code = matches[0].strip()
            if CodeGenerator._validate_python_syntax(code):
                return code
            logger.warning("Extracted Python code has syntax errors")
            return code  # Return anyway, let sandbox handle errors
        
        # Fallback: generic code blocks
        pattern = r"```\s*(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            code = match.strip()
            # Check if it looks like Python
            if CodeGenerator._looks_like_python(code):
                return code
        
        return None
    
    @staticmethod
    def extract_all_code_blocks(text: str) -> list:
        """
        Extract all code blocks with their detected languages.
        Returns list of (language, code) tuples.
        """
        results = []
        
        # Pattern with language specification
        pattern = r"```(\w+)?\s*(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for lang, code in matches:
            detected_lang = lang.lower() if lang else "unknown"
            code = code.strip()
            
            # Auto-detect if no language specified
            if detected_lang == "unknown":
                if CodeGenerator._looks_like_python(code):
                    detected_lang = "python"
                elif code.startswith("function") or "=>" in code:
                    detected_lang = "javascript"
            
            results.append((detected_lang, code))
        
        return results
    
    @staticmethod
    def _validate_python_syntax(code: str) -> bool:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    @staticmethod
    def _looks_like_python(code: str) -> bool:
        """Heuristic check if code looks like Python."""
        python_indicators = [
            "def ", "class ", "import ", "from ", "if __name__",
            "print(", "return ", "self.", "async def", "await "
        ]
        return any(indicator in code for indicator in python_indicators)
    
    @staticmethod
    def clean_code(code: str) -> str:
        """
        Clean extracted code by removing common artifacts.
        """
        # Remove leading/trailing whitespace
        code = code.strip()
        
        # Remove common LLM artifacts
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that are just comments about the code
            if line.strip().startswith("# Here's") or line.strip().startswith("# This"):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def wrap_in_function(code: str, func_name: str = "generated_task") -> str:
        """
        Wrap standalone code in a function for safer execution.
        """
        indented = '\n'.join('    ' + line for line in code.split('\n'))
        return f"def {func_name}():\n{indented}\n\n# Auto-execute\n{func_name}()"


if __name__ == "__main__":
    # Test
    test_text = '''
    Here's how to do it:
    ```python
    def hello():
        print("Hello World!")
    
    hello()
    ```
    '''
    
    gen = CodeGenerator()
    code = gen.extract_python(test_text)
    print("Extracted:", code)
