# ZARA — Local AI Desktop Companion

A completely private, offline AI assistant featuring a morphing glassmorphic desktop interface powered by local LLM inference via Ollama and a native Tauri v2 desktop application.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-v2-FFC13B.svg)](https://tauri.app/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-orange.svg)](https://www.rust-lang.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg)](https://ollama.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📁 Repository Architecture

This monorepo separates core intelligence from client interfaces:

```
ZARA-Zenith-Autonomous-Reasoning-Assistant/
├── backend/                # 🧠 Python Local AI Intelligence Engine & WebSocket Server
│   ├── main.py             # Server launcher & uvicorn entry point
│   ├── config.py           # Hardware, model, & local environment configuration
│   ├── brain/              # Local LLM cognitive core (Ollama GPU)
│   ├── server/             # FastAPI & WebSocket nervous system bridge
│   ├── memory/             # Graph memory & local embeddings (all-MiniLM-L6-v2)
│   ├── actions/            # Sandboxed local file tools & whitelisting
│   ├── ears/               # Isolated Whisper Speech-to-Text process
│   ├── eyes/               # Multimodal visual perception process
│   └── soul/               # Fast local Text-to-Speech engine (pyttsx3)
│
├── zara-ghost/             # 👻 Tauri v2 Desktop Glassmorphic Interface
│   ├── src-tauri/          # Native Rust window management & morphing commands
│   ├── src/                # Vite + TypeScript client application & WebSocket client
│   ├── index.html          # Multi-layout overlay UI (Chat, Code, System Stats, Vision)
│   └── styles.css          # Glassmorphism backdrop blur styling & orb animations
│
└── codes_archive/          # 📦 Isolated Legacy & Experimental Code Modules
```

---

## ✨ Key Features

- 👻 **Floating Ghost Overlay**: Frameless, transparent desktop UI built with Tauri v2 and Rust. Morphs dynamically between `Chat`, `Code`, `System Metrics`, and `Vision` states based on query intent.
- ⚡ **Local LLM Intelligence**: Runs 100% offline via local Ollama (`gemma:2b` / `qwen2.5:4b`).
- 🧠 **Semantic Graph Memory**: Semantic memory backed by local `sentence-transformers` embeddings (`all-MiniLM-L6-v2`).
- 🔒 **Local-First & Private**: Direct localhost WebSocket communication (`ws://127.0.0.1:8000/ws/brain`), zero external data telemetry.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 20+**
- **Rust & Cargo** (for Tauri desktop app)
- **Ollama** installed locally (`ollama pull gemma:2b`)

### 2. Start the AI Backend
```bash
cd backend
pip install -r requirements.txt
python main.py --server
```

### 3. Launch the Ghost Window
In a separate terminal:
```bash
cd zara-ghost
npm install
npm run tauri dev
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
