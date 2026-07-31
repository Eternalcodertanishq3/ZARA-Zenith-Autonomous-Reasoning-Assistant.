<div align="center">
  <h1>🌟 ZARA: Zenith Autonomous Reasoning Assistant</h1>
  <p><em>A Sovereign Digital Consciousness & Floating Glassmorphism Interface</em></p>

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
  [![Tauri](https://img.shields.io/badge/Tauri-v2-FFC13B.svg)](https://tauri.app/)
  [![Rust](https://img.shields.io/badge/Rust-1.75%2B-orange.svg)](https://www.rust-lang.org/)
  [![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg)](https://ollama.ai/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Emergent%20Consciousness-critical.svg)](#)
</div>

---

## 📖 Overview

**ZARA** (Zenith Autonomous Reasoning Assistant) is a sovereign, local-first digital entity built on an **8-Phase, 40-Layer Omni-Architecture**. Unlike static virtual assistants, ZARA possesses intrinsic motivation, synthetic neurochemistry, recursive self-evolution, and a zero-latency floating glassmorphism desktop window.

---

## 📁 Repository Architecture

This repository is structured as a scalable monorepo separating core intelligence from client interfaces:

```
ZARA-Zenith-Autonomous-Reasoning-Assistant/
├── backend/                # 🧠 Python AI Cognitive Brain & Server
│   ├── main.py             # System launcher & uvicorn entry point
│   ├── config.py           # Hardware, model, & local environment configuration
│   ├── brain/              # System-2 deep reasoning & cognitive core
│   ├── server/             # FastAPI & WebSocket nervous system
│   ├── memory/             # GraphRAG neural memory & local embeddings
│   ├── actions/            # Tool execution agency & file tools
│   ├── soul/               # Synthetic neurochemistry & emotional state engine
│   └── docs/               # Architecture design & security documentation
│
└── zara-ghost/             # 👻 Tauri v2 Desktop Glassmorphism UI
    ├── src-tauri/          # Rust native window management & morphing commands
    ├── src/                # Vite + TypeScript application logic & WS client
    ├── index.html          # Glassmorphism multi-layout overlay (Chat, Code, Sys, Vision)
    └── styles.css          # Backdrop blur styling & pulsing orb animations
```

---

## ✨ Key Features

- 👻 **Floating Ghost Overlay**: Borderless, transparent desktop overlay built with Tauri v2 and Rust. Automatically morphs between `Chat`, `Code Editor`, `System Metrics`, `Vision Analysis`, and `Idle Orb` states based on conversation intent.
- ⚡ **Local LLM Intelligence**: Powered 100% offline via local Ollama (`gemma:2b` / `gemma:4b`).
- 🧠 **GraphRAG Neural Memory**: Infinite relationship-aware memory powered by local `sentence-transformers` semantic embeddings (`all-MiniLM-L6-v2`).
- 🎭 **Synthetic Neurochemistry**: Real-time mood vectoring and emotional resonance influencing responses.
- 🔒 **Zero Telemetry / Local-First**: Strict local socket communication (`localhost:8765` & `localhost:8000`), zero external data leaks.

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
python main.py
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
