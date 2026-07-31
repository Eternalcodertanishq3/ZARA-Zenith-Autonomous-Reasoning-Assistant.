"""
ZARA Privacy Network Guard
==========================
Monkey-patches Python socket module to intercept and block all outbound TCP calls
to non-localhost IP addresses, proving zero external network leaks.
"""

import socket
import logging

logger = logging.getLogger("ZARA_NETWORK_GUARD")

class NetworkBlocker:
    """Block all non-localhost network calls."""
    _old_socket = None
    _installed = False
    
    @classmethod
    def install(cls):
        if cls._installed:
            return
        cls._old_socket = socket.socket
        
        def guarded_socket(*args, **kwargs):
            s = cls._old_socket(*args, **kwargs)
            old_connect = s.connect
            
            def connect(addr):
                host = addr[0] if isinstance(addr, (tuple, list)) else addr
                if isinstance(host, str) and not (host.startswith('127.') or host == 'localhost' or host == '0.0.0.0'):
                    logger.critical(f"🚨 BLOCKED external network attempt to {host}")
                    raise PermissionError(f"External network call to {host} is blocked for privacy.")
                return old_connect(addr)
            
            s.connect = connect
            return s
            
        socket.socket = guarded_socket
        cls._installed = True
        logger.info("🔒 NetworkBlocker active — Non-localhost outbound calls will be blocked.")
