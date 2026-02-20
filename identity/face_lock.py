"""
ZARA Face Lock - Enhanced Biometric Security
"""
import os
import cv2
import pickle
import logging
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("ZARA_ID")

# Lazy import
face_recognition = None

def _lazy_load_fr():
    global face_recognition
    if face_recognition is None:
        try:
            import face_recognition as fr
            face_recognition = fr
        except ImportError:
            pass


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    success: bool
    name: str
    confidence: float
    faces_found: int
    auth_time: float
    message: str


class FaceID:
    """
    Advanced biometric face lock with:
    - Liveness detection (basic anti-spoofing)
    - Confidence scoring
    - Multi-face handling
    - Session locking
    - Failed attempt tracking
    """
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    
    def __init__(self):
        _lazy_load_fr()
        
        try:
            from config import IDENTITY_DIR
            self.authorized_faces_dir = IDENTITY_DIR / "authorized_faces"
            self.encodings_file = IDENTITY_DIR / "encodings.pkl"
        except ImportError:
            self.authorized_faces_dir = Path("identity/authorized_faces")
            self.encodings_file = Path("identity/encodings.pkl")
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.is_active = False
        
        # Security tracking
        self.failed_attempts = 0
        self.last_failed_time = 0
        self.is_locked = False
        self.authenticated_user = None
        self.auth_timestamp = 0
        
        # Liveness detection
        self.prev_frame = None
        self.motion_threshold = 0.02
        
        self.authorized_faces_dir.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self):
        """Initialize face recognition system."""
        if face_recognition is None:
            logger.warning("face_recognition not installed. FaceID disabled.")
            return
        
        self.is_active = True
        logger.info("FaceLock System Initialized.")
        self._load_encodings()

    def _load_encodings(self):
        """Load cached encodings or generate from images."""
        if not self.is_active:
            return

        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data["encodings"]
                    self.known_face_names = data["names"]
                logger.info(f"Loaded {len(self.known_face_names)} authorized identities.")
                return
            except Exception as e:
                logger.error(f"Failed to load encodings: {e}")

        self._scan_and_encode()

    def _scan_and_encode(self):
        """Scan directory and encode all faces."""
        logger.info("Scanning for authorized faces...")
        encodings = []
        names = []
        
        for file_path in self.authorized_faces_dir.glob("*"):
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                name = file_path.stem
                try:
                    image = face_recognition.load_image_file(str(file_path))
                    face_encs = face_recognition.face_encodings(image)
                    
                    if face_encs:
                        encodings.append(face_encs[0])
                        names.append(name)
                        logger.info(f"Encoded identity: {name}")
                    else:
                        logger.warning(f"No face found in {file_path.name}")
                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {e}")
        
        self.known_face_encodings = encodings
        self.known_face_names = names
        self._save_encodings()

    def _save_encodings(self):
        """Save encodings to cache file."""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({
                    "encodings": self.known_face_encodings,
                    "names": self.known_face_names
                }, f)
        except Exception as e:
            logger.error(f"Failed to save encodings: {e}")

    def _check_liveness(self, frame: np.ndarray) -> bool:
        """
        Basic liveness detection via motion analysis.
        Real systems would use depth cameras or challenge-response.
        """
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return True
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(self.prev_frame, gray)
        motion = np.mean(diff) / 255.0
        
        self.prev_frame = gray
        
        # Expect some motion (not a static photo)
        return motion > self.motion_threshold

    def _check_lockout(self) -> bool:
        """Check if system is locked due to failed attempts."""
        if not self.is_locked:
            return False
        
        if time.time() - self.last_failed_time > self.LOCKOUT_DURATION:
            self.is_locked = False
            self.failed_attempts = 0
            logger.info("Lockout period ended.")
            return False
        
        return True

    def identify(self, frame: np.ndarray) -> Tuple[str, float]:
        """
        Identify a face in the frame.
        Returns: (name, confidence)
        """
        if not self.is_active:
            return ("Unknown", 0.0)
        
        if self._check_lockout():
            return ("LOCKED", 0.0)
        
        # Liveness check
        if not self._check_liveness(frame):
            logger.warning("Liveness check failed (static image detected)")
            return ("SPOOFING_DETECTED", 0.0)
        
        # Resize for speed
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        
        if not encodings:
            return ("No Face", 0.0)
        
        # Find best match
        best_name = "Unknown"
        best_confidence = 0.0
        
        for encoding in encodings:
            if not self.known_face_encodings:
                continue
            
            distances = face_recognition.face_distance(self.known_face_encodings, encoding)
            
            if len(distances) > 0:
                best_idx = np.argmin(distances)
                confidence = 1 - distances[best_idx]
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    if confidence > 0.5:
                        best_name = self.known_face_names[best_idx]
        
        # Track failures
        if best_name == "Unknown":
            self._record_failure()
        else:
            self.failed_attempts = 0
            self.authenticated_user = best_name
            self.auth_timestamp = time.time()
        
        return (best_name, best_confidence)

    def authenticate(self, frame: np.ndarray) -> AuthResult:
        """
        Full authentication with detailed result.
        """
        start_time = time.time()
        
        if not self.is_active:
            return AuthResult(
                success=False, name="", confidence=0.0, faces_found=0,
                auth_time=0, message="FaceID not available"
            )
        
        if self._check_lockout():
            remaining = int(self.LOCKOUT_DURATION - (time.time() - self.last_failed_time))
            return AuthResult(
                success=False, name="LOCKED", confidence=0.0, faces_found=0,
                auth_time=0, message=f"System locked. Try again in {remaining}s"
            )
        
        name, confidence = self.identify(frame)
        auth_time = time.time() - start_time
        
        if name in ["Unknown", "No Face", "SPOOFING_DETECTED", "LOCKED"]:
            return AuthResult(
                success=False, name=name, confidence=confidence,
                faces_found=1 if name != "No Face" else 0,
                auth_time=auth_time,
                message=f"Authentication failed: {name}"
            )
        
        return AuthResult(
            success=True, name=name, confidence=confidence,
            faces_found=1, auth_time=auth_time,
            message=f"Welcome back, {name}!"
        )

    def _record_failure(self):
        """Record a failed authentication attempt."""
        self.failed_attempts += 1
        self.last_failed_time = time.time()
        
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.is_locked = True
            logger.critical(f"Too many failed attempts! System locked for {self.LOCKOUT_DURATION}s")

    def register_user(self, frame: np.ndarray, name: str = "Vivaan") -> bool:
        """Register a new authorized user."""
        if not self.is_active:
            logger.error("FaceID not active.")
            return False
        
        # Ensure face is present
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        
        if not encodings:
            logger.error("No face detected in registration image.")
            return False
        
        file_path = self.authorized_faces_dir / f"{name}.jpg"
        cv2.imwrite(str(file_path), frame)
        logger.info(f"Saved new identity: {file_path}")
        
        self._scan_and_encode()
        return True

    def deauthorize_user(self, name: str) -> bool:
        """Remove an authorized user."""
        file_path = self.authorized_faces_dir / f"{name}.jpg"
        if file_path.exists():
            file_path.unlink()
            self._scan_and_encode()
            logger.info(f"Deauthorized: {name}")
            return True
        return False

    def get_security_status(self) -> dict:
        """Get current security status."""
        return {
            "active": self.is_active,
            "locked": self.is_locked,
            "failed_attempts": self.failed_attempts,
            "authenticated_user": self.authenticated_user,
            "registered_users": len(self.known_face_names),
            "users": self.known_face_names
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    security = FaceID()
    print("FaceID Status:", security.get_security_status())
