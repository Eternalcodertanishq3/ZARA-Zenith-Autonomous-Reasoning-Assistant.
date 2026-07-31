"""
ZARA Local File Tools
=====================
Secure local file reading and writing tools with whitelist enforcement.
"""

import os
import platform
import logging

logger = logging.getLogger("ZARA_FILE_TOOLS")

CUSTOM_PATHS = [p.strip() for p in os.environ.get("ZARA_WHITELIST", "").split(";") if p.strip()]

WHITELIST = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Projects"),
    os.path.expanduser("~/projects"),
    os.path.expanduser("~/Desktop"),
    os.path.abspath(os.path.expanduser("~")),
] + [os.path.abspath(p) for p in CUSTOM_PATHS]

def is_whitelisted(path: str) -> bool:
    try:
        abs_path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
        for w in WHITELIST:
            norm_w = os.path.normpath(os.path.abspath(w))
            if abs_path == norm_w or abs_path.startswith(norm_w + os.sep):
                return True
        return False
    except Exception:
        return False

def tool_file_read(path: str) -> str:
    abs_path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
    if not is_whitelisted(abs_path):
        return f"Error: Access denied. Path '{path}' is outside allowed directories."
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            if len(content) > 10000:
                return content[:10000] + "\n... [Truncated due to size]"
            return content
    except Exception as e:
        return f"Error reading file: {e}"

def tool_file_write(path: str, content: str) -> str:
    abs_path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
    if not is_whitelisted(abs_path):
        return f"Error: Access denied. Path '{path}' is outside allowed directories."
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully written {len(content)} bytes to {abs_path}"
    except Exception as e:
        return f"Error writing file: {e}"
