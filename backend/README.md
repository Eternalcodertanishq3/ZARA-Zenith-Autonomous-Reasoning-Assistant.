# ZARA Backend — Core Intelligence Engine

ZARA is a completely private, 100% local AI desktop companion backend powered by local LLM inference via Ollama, local voice processing, and a native WebSocket nervous system.

---

## 🏗️ Architecture Overview

- **`brain/`**: Local LLM inference wrapper (`CognitiveCore`) via Ollama (`gemma:2b`, `qwen2.5:4b`, etc.).
- **`server/`**: FastAPI + WebSocket bridge (`nervous_system.py`) serving live state and task-detection broadcasts to the Tauri desktop UI.
- **`memory/`**: Semantic graph memory (`graph_memory.py`) with `SentenceTransformer` embeddings & vector DB fallback (`vector_db.py`).
- **`actions/`**: Sandboxed local file operations (`file_tools.py`) with cross-platform path whitelisting.
- **`ears/`**: Isolated local Speech-To-Text worker process using Whisper (`stt_engine.py`).
- **`eyes/`**: Multimodal visual perception worker process (`vision_core.py`).
- **`soul/`**: Fast local Text-to-Speech audio generation (`tts_engine.py` / pyttsx3).
- **`utils/`**: Production resilience utilities, circuit breakers (`resilience.py`), and privacy socket guard (`network_guard.py`).

---

## ⚡ Quickstart

### 1. Requirements
- Python 3.10+
- [Ollama](https://ollama.ai) running locally (`ollama pull gemma:2b`)

### 2. Launch Server
```bash
cd backend
python main.py --server
```

The WebSocket Nervous System will start listening at:
`ws://127.0.0.1:8000/ws/brain`

---

## 🛡️ Privacy Guarantee
ZARA runs 100% locally. Outbound non-localhost network connections are blocked by default via `NetworkBlocker` in `utils/network_guard.py`.
