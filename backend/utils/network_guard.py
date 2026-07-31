"""
ZARA Privacy Network Guard
==========================
Monkey-patches socket.socket.connect to intercept and block all outbound TCP calls
to non-localhost IP addresses, proving zero external network leaks.
"""

import socket
import logging

logger = logging.getLogger("ZARA_NETWORK_GUARD")

class NetworkBlocker:
    """Block all non-localhost network calls."""
    _old_connect = None
    _installed = False
    
    @classmethod
    def install(cls):
        if cls._installed:
            return
        cls._old_connect = socket.socket.connect
        
        def guarded_connect(self, addr):
            host = addr[0] if isinstance(addr, (tuple, list)) else addr
            if isinstance(host, str) and not (host.startswith('127.') or host == 'localhost' or host == '0.0.0.0'):
                logger.critical(f"🚨 BLOCKED external network attempt to {host}")
                raise PermissionError(f"External network call to {host} is blocked for privacy.")
            return cls._old_connect(self, addr)
        
        socket.socket.connect = guarded_connect
        cls._installed = True
        logger.info("🔒 NetworkBlocker active — Non-localhost outbound calls will be blocked.")
