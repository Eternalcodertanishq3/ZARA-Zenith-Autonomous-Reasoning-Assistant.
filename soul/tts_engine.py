import logging
import os
import pyttsx3 # 🚀 NEW FAST ENGINE

logger = logging.getLogger("ZARA_SOUL")

class TTSEngine:
    def __init__(self, config=None):
        logger.info("Loading Fast Voice Engine (pyttsx3)...")
        try:
            self.engine = pyttsx3.init()
            
            # Make her sound female and natural speed
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id) # Usually the female voice on Windows
            self.engine.setProperty('rate', 165) # Speaking speed
            
            logger.info("Fast Voice Engine Online.")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.engine = None

    def speak(self, text, mood="neutral", blocking=True):
        """Instant speech generation"""
        if not self.engine or not text:
            print(f"✨ ZARA: {text}")
            return
        
        logger.info(f"Speaking: {text[:30]}...")
        # Clean text of any accidental tags or actions
        clean_text = text.replace("<think>", "").replace("</think>", "")
        # Remove *actions*
        import re
        clean_text = re.sub(r'\*[^*]+\*', '', clean_text).strip()
        
        try:
            self.engine.say(clean_text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 speak failed: {e}")
            print(f"✨ ZARA: {text}")

    def speak_async(self, text: str, mood: str = "neutral"):
        """Fast fallback for async (pyttsx3 is already very fast)"""
        import threading
        threading.Thread(target=self.speak, args=(text, mood, True), daemon=True).start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = TTSEngine()
    tts.speak("Hello Vivaan! This is ZARA's new ultra-fast voice.")
