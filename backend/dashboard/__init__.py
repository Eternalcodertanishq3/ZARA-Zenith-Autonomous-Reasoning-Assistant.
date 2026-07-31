"""
ZARA Dashboard Package
Holographic desktop interface — powered by pywebview + Three.js VRM.
Run:  python dashboard/native_app.py
"""
from .native_app import get_native_dashboard

__all__ = ['get_native_dashboard']
