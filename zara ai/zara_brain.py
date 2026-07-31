import sys
import os
import threading
from llama_cpp import Llama

class ZaraBrain:
    def __init__(self, model_path, prompt_path):
        print(f"\n[ZARA] Awakening High-Logic Core (Qwen 3)...")
        
        # Initializing on CPU for the Test Phase
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=0,       
            n_ctx=4096,           
            chat_format="chatml", 
            verbose=False
        )
        
        self.lock = threading.Lock()
        self.history = [{"role": "system", "content": self._load_prompt(prompt_path)}]

    def _load_prompt(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "You are ZARA, Vivaan's Life Partner and Technical Assistant. Speak Hinglish."

    def think(self, user_text):
        with self.lock:
            self.history.append({"role": "user", "content": user_text})
            
        stream = self.llm.create_chat_completion(
            messages=self.history,
            stream=True,
            temperature=0.8,
            max_tokens=2048 
        )
        
        full_reply = ""
        print("✨ ZARA: ", end="", flush=True)
        for chunk in stream:
            if 'content' in chunk['choices'][0]['delta']:
                word = chunk['choices'][0]['delta']['content']
                print(word, end="", flush=True)
                full_reply += word
        print()

        with self.lock:
            self.history.append({"role": "assistant", "content": full_reply})
        return full_reply