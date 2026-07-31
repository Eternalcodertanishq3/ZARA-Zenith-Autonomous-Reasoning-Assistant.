"""
ZARA Local File Tools
=====================
Secure local file reading and writing tools with whitelist enforcement.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("ZARA_FILE_TOOLS")

# Whitelisted root paths for local operations
WHITELIST = [
    os.path.abspath(os.path.expanduser("~")),
    "C:\\Personal Projects",
    "c:\\Personal Projects",
]

def is_whitelisted(path: str) -> bool:
    try:
        abs_path = os.path.abspath(path)
        return any(os.path.commonpath([abs_path, os.path.abspath(w)]) == os.path.abspath(w) for w in WHITELIST if os.path.exists(w))
    except Exception:
        return True

def tool_file_read(path: str) -> str:
    abs_path = os.path.abspath(path)
    if not is_whitelisted(abs_path):
        return "Error: Access denied (path outside whitelist)"
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            if len(content) > 10000:
                return content[:10000] + "\n... [Truncated due to size]"
            return content
    except Exception as e:
        return f"Error reading file: {e}"

def tool_file_write(path: str, content: str) -> str:
    abs_path = os.path.abspath(path)
    if not is_whitelisted(abs_path):
        return "Error: Access denied (path outside whitelist)"
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully written {len(content)} bytes to {abs_path}"
    except Exception as e:
        return f"Error writing file: {e}"
