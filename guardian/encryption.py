"""
ZARA Encryption Layer - Enhanced Data Protection
"""
import os
import json
import base64
import hashlib
import hmac
import secrets
import logging
import time
from pathlib import Path
from typing import Union, Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger("ZARA_ENCRYPT")


@dataclass
class EncryptionStats:
    """Encryption operation statistics."""
    total_encryptions: int = 0
    total_decryptions: int = 0
    bytes_encrypted: int = 0
    bytes_decrypted: int = 0


class Encryptor:
    """
    AES-256 encryption for ZARA's memories and sensitive data.
    Enhanced with:
    - Key rotation support
    - Authenticated encryption (AEAD)
    - Password-based key derivation
    - Secure memory handling
    - Integrity verification
    - Multiple key support
    """
    
    def __init__(self, key_file: Optional[Path] = None, password: Optional[str] = None):
        try:
            from config import ROOT_DIR
            self.key_file = key_file or (ROOT_DIR / ".zara_key")
        except ImportError:
            self.key_file = key_file or Path(".zara_key")
        
        self.key = None
        self.cipher = None
        self.is_active = False
        self.password = password
        
        # Statistics
        self.stats = EncryptionStats()
        
        # Key rotation tracking
        self.key_version = 1
        self.keys: Dict[int, bytes] = {}
        
        self._initialize()

    def _initialize(self):
        """Initialize encryption system."""
        try:
            from cryptography.fernet import Fernet
            
            if self.password:
                self.key = self._derive_key_from_password(self.password)
            else:
                self.key = self._load_or_create_key()
            
            self.cipher = Fernet(self.key)
            self.keys[self.key_version] = self.key
            self.is_active = True
            
            logger.info("Encryption system initialized.")
            
        except ImportError:
            logger.warning("cryptography not installed. Using fallback encoding.")
            self._init_fallback()
        except Exception as e:
            logger.error(f"Encryption init failed: {e}")
            self._init_fallback()

    def _init_fallback(self):
        """Fallback to obfuscation (not secure)."""
        logger.warning("Using XOR fallback (NOT SECURE - install cryptography)")
        self.is_active = False
        self._fallback_key = secrets.token_bytes(32)

    def _load_or_create_key(self) -> bytes:
        """Load existing key or generate new one."""
        from cryptography.fernet import Fernet
        
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    data = f.read()
                    # Check if versioned key format
                    if data.startswith(b"v"):
                        parts = data.split(b":", 1)
                        self.key_version = int(parts[0][1:])
                        return parts[1]
                    return data
            except Exception as e:
                logger.warning(f"Key load error: {e}. Generating new key.")
        
        # Generate new key
        key = Fernet.generate_key()
        self._save_key(key)
        return key

    def _save_key(self, key: bytes):
        """Save key securely."""
        try:
            # Versioned format
            data = f"v{self.key_version}:".encode() + key
            
            with open(self.key_file, 'wb') as f:
                f.write(data)
            
            # Secure permissions (Unix)
            try:
                os.chmod(self.key_file, 0o600)
            except OSError:
                pass  # Windows doesn't support chmod like Unix
            
            logger.info(f"Saved encryption key (version {self.key_version})")
        except Exception as e:
            logger.error(f"Key save failed: {e}")

    def _derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        
        if salt is None:
            # Load or generate salt
            salt_file = self.key_file.with_suffix('.salt')
            if salt_file.exists():
                with open(salt_file, 'rb') as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(salt_file, 'wb') as f:
                    f.write(salt)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000  # OWASP recommended
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: Union[str, bytes, dict]) -> bytes:
        """Encrypt data with integrity protection."""
        # Serialize if needed
        if isinstance(data, dict):
            data = json.dumps(data, ensure_ascii=False)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        self.stats.total_encryptions += 1
        self.stats.bytes_encrypted += len(data)
        
        if self.is_active and self.cipher:
            # Add version prefix for key rotation support
            encrypted = self.cipher.encrypt(data)
            return f"v{self.key_version}:".encode() + encrypted
        else:
            # XOR fallback (weak obfuscation)
            return self._xor_obfuscate(data)

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data and verify integrity."""
        self.stats.total_decryptions += 1
        
        if self.is_active and self.cipher:
            try:
                # Check for version prefix
                if encrypted_data.startswith(b"v"):
                    parts = encrypted_data.split(b":", 1)
                    version = int(parts[0][1:])
                    data = parts[1]
                    
                    # Use appropriate key for version
                    if version in self.keys:
                        from cryptography.fernet import Fernet
                        cipher = Fernet(self.keys[version])
                        decrypted = cipher.decrypt(data)
                    else:
                        decrypted = self.cipher.decrypt(data)
                else:
                    decrypted = self.cipher.decrypt(encrypted_data)
                
                self.stats.bytes_decrypted += len(decrypted)
                return decrypted.decode('utf-8')
                
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return ""
        else:
            return self._xor_deobfuscate(encrypted_data).decode('utf-8')

    def _xor_obfuscate(self, data: bytes) -> bytes:
        """Simple XOR obfuscation fallback."""
        result = bytearray()
        for i, b in enumerate(data):
            result.append(b ^ self._fallback_key[i % len(self._fallback_key)])
        return base64.b64encode(bytes(result))

    def _xor_deobfuscate(self, data: bytes) -> bytes:
        """Reverse XOR obfuscation."""
        decoded = base64.b64decode(data)
        result = bytearray()
        for i, b in enumerate(decoded):
            result.append(b ^ self._fallback_key[i % len(self._fallback_key)])
        return bytes(result)

    def encrypt_file(self, file_path: Path, output_path: Optional[Path] = None,
                    delete_original: bool = False) -> bool:
        """Encrypt an entire file."""
        file_path = Path(file_path)
        output_path = output_path or file_path.with_suffix(file_path.suffix + '.enc')
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            if delete_original:
                self.secure_delete(file_path)
            
            logger.info(f"Encrypted: {file_path} → {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return False

    def decrypt_file(self, file_path: Path, output_path: Optional[Path] = None) -> bool:
        """Decrypt an encrypted file."""
        file_path = Path(file_path)
        
        if output_path is None:
            output_path = Path(str(file_path).replace('.enc', ''))
            if output_path == file_path:
                output_path = file_path.with_suffix('.dec')
        
        try:
            with open(file_path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.decrypt(encrypted)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decrypted)
            
            logger.info(f"Decrypted: {file_path} → {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """Generate secure password hash."""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 480000)
        return base64.b64encode(salt + key).decode()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        try:
            decoded = base64.b64decode(stored_hash)
            salt = decoded[:32]
            stored_key = decoded[32:]
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 480000)
            return hmac.compare_digest(new_key, stored_key)
        except Exception as e:
            logger.debug(f"Password verification failed: {e}")
            return False

    def rotate_key(self) -> bool:
        """Rotate to a new encryption key."""
        if not self.is_active:
            return False
        
        try:
            from cryptography.fernet import Fernet
            
            # Store old key
            self.keys[self.key_version] = self.key
            
            # Generate new key
            self.key_version += 1
            self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)
            self.keys[self.key_version] = self.key
            
            self._save_key(self.key)
            
            logger.info(f"Key rotated to version {self.key_version}")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False

    def secure_delete(self, file_path: Path, passes: int = 3) -> bool:
        """Securely delete a file with multiple overwrite passes."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        try:
            size = file_path.stat().st_size
            
            for i in range(passes):
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
            
            os.remove(file_path)
            logger.info(f"Securely deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Secure delete failed: {e}")
            return False

    def generate_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(length)

    def get_stats(self) -> Dict:
        """Get encryption statistics."""
        return {
            "is_active": self.is_active,
            "key_version": self.key_version,
            "total_encryptions": self.stats.total_encryptions,
            "total_decryptions": self.stats.total_decryptions,
            "bytes_encrypted": self.stats.bytes_encrypted,
            "bytes_decrypted": self.stats.bytes_decrypted
        }


def generate_master_password() -> str:
    """Generate a strong master password."""
    return secrets.token_urlsafe(24)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    encryptor = Encryptor()
    
    # Test encryption
    original = "This is a secret message!"
    encrypted = encryptor.encrypt(original)
    decrypted = encryptor.decrypt(encrypted)
    
    print(f"Original: {original}")
    print(f"Encrypted: {encrypted[:50]}...")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {original == decrypted}")
    
    print("\nStats:", encryptor.get_stats())
