"""
ZARA Native Desktop Application — PyWebView Wrapper
====================================================
Launches a borderless, transparent desktop window that renders
the ZARA holographic VRM frontend via WebGL (iGPU).

Usage:
    1. Start the brain first:  python main.py --server
    2. Then open this window:  python dashboard/native_app.py

The window is frameless and transparent so ZARA's 3D face floats
directly over the desktop wallpaper — JARVIS-style.

Dependencies:
    pip install pywebview
"""

from __future__ import annotations

import sys
import os
import time
import logging
import threading
from pathlib import Path

# Add root to path so we can import from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("ZARA_APP")
logging.basicConfig(
    format="%(asctime)s | %(name)-15s | %(levelname)-7s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)

# ─── PyWebView import ─────────────────────────────────────────────
try:
    import webview
except ImportError:
    logger.critical("pywebview not installed.")
    logger.critical("Run:  pip install pywebview")
    sys.exit(1)


# ─── Config ───────────────────────────────────────────────────────
BRAIN_URL     = "http://127.0.0.1:8000/"
BRAIN_WS_URL  = "ws://127.0.0.1:8000/ws/brain"
APP_TITLE     = "ZARA — Holographic Interface"
WINDOW_W      = 1440
WINDOW_H      = 860
MAX_WAIT_SECS = 30   # How long to wait for the brain server


# ═══════════════════════════════════════════════════════════════════
# PYTHON ↔ JAVASCRIPT API BRIDGE
# Exposes Python system metrics to the JS frontend.
# ═══════════════════════════════════════════════════════════════════
class ZaraAPI:
    """Thin Python ↔ WebView API bridge exposed as `window.pyapi`."""

    def __init__(self, window_ref):
        self._window = window_ref

    # ── System metrics ────────────────────────────────────────────
    def get_metrics(self) -> dict:
        """Return CPU / RAM metrics for the HUD overlay."""
        metrics = {"cpu": 0, "ram": 0, "vram": 0, "gpu_temp": 0}
        try:
            import psutil
            metrics["cpu"] = round(psutil.cpu_percent(interval=None), 1)
            metrics["ram"] = round(psutil.virtual_memory().percent, 1)
        except ImportError:
            pass
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 3:
                    used  = float(parts[0].strip()) / 1024   # MB → GB
                    total = float(parts[1].strip()) / 1024
                    temp  = float(parts[2].strip())
                    metrics["vram"] = round(used, 2)
                    metrics["vram_pct"] = round((used / max(total, 1)) * 100, 1)
                    metrics["gpu_temp"] = temp
        except Exception:
            pass
        return metrics

    # ── Window controls (callable from JS) ────────────────────────
    def minimize(self):
        self._window.minimize()

    def close(self):
        self._window.destroy()

    def toggle_fullscreen(self):
        self._window.toggle_fullscreen()


# ═══════════════════════════════════════════════════════════════════
# WAIT FOR BRAIN (poll until server responds)
# ═══════════════════════════════════════════════════════════════════
def wait_for_brain() -> bool:
    """Poll the brain HTTP endpoint until it comes alive or times out."""
    import urllib.request
    import urllib.error

    logger.info(f"Waiting for ZARA brain at {BRAIN_URL} ...")
    deadline = time.time() + MAX_WAIT_SECS

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(BRAIN_URL, timeout=1) as resp:
                if resp.status < 500:
                    logger.info("✓ Brain server is alive!")
                    return True
        except Exception:
            pass
        time.sleep(0.6)

    logger.warning(f"Brain did not respond within {MAX_WAIT_SECS}s. Opening anyway...")
    return False


# ═══════════════════════════════════════════════════════════════════
# INLINE FALLBACK PAGE
# Shown if the brain server is not available.
# ═══════════════════════════════════════════════════════════════════
FALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>ZARA — Brain Offline</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #04040c;
      color: #e8e8ff;
      font-family: 'Outfit', 'Segoe UI', sans-serif;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      height: 100vh; gap: 20px;
    }
    .hex { font-size: 60px; color: #7c6fff;
           animation: pulse 2s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
    h1 { font-size: 28px; letter-spacing: 6px;
         background: linear-gradient(90deg, #7c6fff, #06d6f0);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p  { color: rgba(200,200,255,0.5); font-size: 14px; }
    code { background: rgba(255,255,255,0.06); padding: 8px 16px;
           border-radius: 8px; font-size: 13px; color: #06d6f0;
           border: 1px solid rgba(6,214,240,0.2); }
    button {
      margin-top: 10px; padding: 12px 28px;
      border: 1px solid rgba(124,111,255,0.5);
      border-radius: 10px; background: rgba(124,111,255,0.12);
      color: #7c6fff; font-size: 14px; font-weight: 600;
      cursor: pointer; letter-spacing: 1px;
    }
    button:hover { background: rgba(124,111,255,0.25); }
  </style>
</head>
<body>
  <div class="hex">⬡</div>
  <h1>ZARA</h1>
  <p>Brain server is not running.</p>
  <code>python main.py --server</code>
  <button onclick="location.reload()">🔄 Retry Connection</button>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════════
# METRIC POLLING — injects live metrics into the JS HUD
# ═══════════════════════════════════════════════════════════════════
def _start_metrics_loop(api: ZaraAPI, window):
    """Push system metrics to the web page every 2 seconds via JS eval."""
    def loop():
        while True:
            time.sleep(2)
            try:
                m = api.get_metrics()
                js = (
                    f"if(window._updateMetrics)"
                    f"window._updateMetrics({m['cpu']},{m['ram']},{m['vram']},{m['gpu_temp']});"
                )
                window.evaluate_js(js)
            except Exception:
                pass  # Window may have been closed
    t = threading.Thread(target=loop, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════
# PYWEBVIEW JS INJECTION
# This JS snippet runs after the page loads and wires pyapi metrics
# into the frontend's HUD update function.
# ═══════════════════════════════════════════════════════════════════
INJECTED_JS = """
// Expose a _updateMetrics function that the Python metrics loop can call
window._updateMetrics = function(cpu, ram, vram, gpuTemp) {
  const setBar = (id, pct) => {
    const el = document.getElementById(id);
    if (el) el.style.width = Math.min(100, pct) + '%';
  };
  const setVal = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.textContent = txt;
  };
  setVal('cpu-val',  cpu  + '%');
  setVal('ram-val',  ram  + '%');
  setVal('vram-val', vram + ' GB');
  setBar('cpu-bar',  cpu);
  setBar('ram-bar',  ram);
  setBar('vram-bar', (vram / 6) * 100);   // Assume 6 GB VRAM max (RTX 4050)
};
console.log('[PyWebView] Metrics bridge ready.');
"""


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def launch():
    """Launch the ZARA holographic desktop window."""

    # Optionally wait for the brain to start
    brain_alive = wait_for_brain()

    if brain_alive:
        # Load the live holographic UI from the FastAPI server
        url = BRAIN_URL
        html = None
    else:
        # Show the offline fallback page
        url  = None
        html = FALLBACK_HTML

    # Create the PyWebView window
    window = webview.create_window(
        title=APP_TITLE,
        url=url,
        html=html,
        width=WINDOW_W,
        height=WINDOW_H,
        resizable=True,
        fullscreen=False,
        frameless=True,          # No OS chrome → floats over desktop
        easy_drag=True,          # Click-drag to move the frameless window
        transparent=True,        # Background transparent → avatar floats
        background_color="#04040c",
        text_select=True,
        min_size=(800, 500),
    )

    # Create and expose the Python API bridge
    api = ZaraAPI(window)

    # Wire up JS injection after page loads
    def on_loaded():
        try:
            window.evaluate_js(INJECTED_JS)
            _start_metrics_loop(api, window)
        except Exception as e:
            logger.warning(f"JS injection failed: {e}")

    window.events.loaded += on_loaded

    logger.info("")
    logger.info("🖥  ZARA Holographic Window launching...")
    logger.info(f"    URL  : {url or 'offline fallback'}")
    logger.info(f"    Size : {WINDOW_W} × {WINDOW_H}")
    logger.info(f"    Mode : frameless + transparent")
    logger.info("")

    webview.start(
        debug=False,
        gui="edgechromium",   # Use Edge/Chromium on Windows for best WebGL support
    )


# ─── Backwards-compat stub for main.py import ────────────────────
class _NativeDashboardStub:
    """Lightweight stub returned by get_native_dashboard() so main.py won't crash."""
    def __init__(self): self.zara = None
    def start(self, zara=None): pass

def get_native_dashboard():
    return _NativeDashboardStub()


# ─── Entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    launch()
