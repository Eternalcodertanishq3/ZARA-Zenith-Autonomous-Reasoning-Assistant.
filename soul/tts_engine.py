import logging
import threading
import queue
import pyttsx3

logger = logging.getLogger("ZARA_SOUL")

class TTSEngine:
    def __init__(self, config=None):
        logger.info("Loading Bulletproof Fast Voice Engine (pyttsx3)...")
        self.speech_queue = queue.Queue()
        
        # 🚀 Spawn a dedicated Voice Box thread
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Voice Engine Online.")

    def _speech_worker(self):
        """This loops forever in the background, speaking words one by one safely."""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id) # Female voice
            engine.setProperty('rate', 165)
            
            while True:
                text = self.speech_queue.get()
                if text is None:
                    break
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"pyttsx3 error: {e}")
                self.speech_queue.task_done()
        except Exception as e:
            logger.error(f"Failed to initialize Voice Engine thread: {e}")

    def speak(self, text, mood="neutral", blocking=True):
        """Instantly drops words into the queue without crashing the main thread."""
        if not text:
            return
        logger.info(f"Speaking: {text[:30]}...")
        # Clean text of any accidental tags or actions
        clean_text = text.replace("<think>", "").replace("</think>", "")
        import re
        clean_text = re.sub(r'\*[^*]+\*', '', clean_text).strip()
        
        if clean_text:
            self.speech_queue.put(clean_text)

    def speak_async(self, text: str, mood: str = "neutral"):
        """Queues speech (already asynchronous due to worker thread)"""
        self.speak(text, mood=mood, blocking=False)
