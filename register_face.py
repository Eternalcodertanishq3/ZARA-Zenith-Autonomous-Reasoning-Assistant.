"""
ZARA Face Registration Script
=============================
Captures your face from webcam and registers it for ZARA to recognize you.
"""

import cv2
import time
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("  ZARA Face Registration")
    print("=" * 60)
    print("\nThis will capture your face and register it with ZARA.")
    print("Make sure you're in good lighting and facing the camera.\n")
    
    name = input("Enter your name [Tanishq]: ").strip() or "Tanishq"
    nickname = input("Enter nickname (optional) [Vivaan]: ").strip() or "Vivaan"
    
    print(f"\nRegistering: {name} (nickname: {nickname})")
    print("\nOpening webcam... Press SPACE to capture, ESC to cancel.\n")
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam!")
        return False
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    captured_frame = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to read from webcam!")
            break
        
        # Mirror the frame for natural viewing
        display = cv2.flip(frame, 1)
        
        # Add instructions
        cv2.putText(display, "Press SPACE to capture, ESC to cancel", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, f"Registering: {name}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Draw face guide rectangle
        h, w = display.shape[:2]
        cx, cy = w // 2, h // 2
        size = 150
        cv2.rectangle(display, (cx - size, cy - size), (cx + size, cy + size), 
                     (0, 255, 0), 2)
        cv2.putText(display, "Center your face here", 
                   (cx - 100, cy - size - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.imshow("ZARA Face Registration", display)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("Registration cancelled.")
            break
        elif key == 32:  # SPACE
            captured_frame = frame.copy()  # Use non-mirrored for saving
            print("\n✓ Face captured!")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if captured_frame is None:
        return False
    
    # Save the face
    from pathlib import Path
    
    faces_dir = Path("identity/authorized_faces")
    faces_dir.mkdir(parents=True, exist_ok=True)
    
    face_path = faces_dir / f"{name}.jpg"
    cv2.imwrite(str(face_path), captured_frame)
    print(f"✓ Saved face to: {face_path}")
    
    # Try to encode the face
    try:
        import face_recognition
        
        print("\nEncoding face...")
        image = face_recognition.load_image_file(str(face_path))
        encodings = face_recognition.face_encodings(image)
        
        if encodings:
            print(f"✓ Face encoded successfully!")
            
            # Save encoding
            import pickle
            encodings_file = Path("identity/encodings.pkl")
            
            # Load existing or create new
            data = {"encodings": [], "names": []}
            if encodings_file.exists():
                with open(encodings_file, 'rb') as f:
                    data = pickle.load(f)
            
            # Add new face
            data["encodings"].append(encodings[0])
            data["names"].append(name)
            
            with open(encodings_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"✓ Encoding saved! ZARA will now recognize you as '{name}'.")
        else:
            print("⚠ No face detected in image. Please try again with better lighting.")
            return False
            
    except ImportError:
        print("\n⚠ face_recognition not installed. Run: pip install face_recognition")
        print("  (The image is saved - encoding will happen on next ZARA startup)")
    
    # Save user profile
    profile_path = Path("identity/user_profile.json")
    import json
    
    profile = {
        "name": name,
        "nickname": nickname,
        "relationship": "best_friend",
        "trust_level": 1.0,
        "registered_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print(f"✓ User profile saved to: {profile_path}")
    
    print("\n" + "=" * 60)
    print("  Registration Complete!")
    print("=" * 60)
    print(f"\n  Name: {name}")
    print(f"  Nickname: {nickname}")
    print(f"  Relationship: Best Friend")
    print(f"\n  ZARA will now greet you by name! Run: python main.py")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
