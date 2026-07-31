"""
tests/test_websocket.py
=======================
WebSocket round-trip test for the ZARA Nervous System.

Prerequisites:
    1. python main.py --server   (must be running in another terminal)

Usage:
    python tests/test_websocket.py
"""

import asyncio
import json
import sys


async def run_test():
    try:
        import websockets
    except ImportError:
        print("websockets not installed. Run: pip install websockets")
        sys.exit(1)

    ws_url = "ws://127.0.0.1:8000/ws/brain"

    print(f"\n{'='*50}")
    print("ZARA WebSocket Nervous System Test")
    print(f"{'='*50}\n")

    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            print(f"✓ Connected to {ws_url}")

            # ── Test 1: Ready handshake ──────────────────────────
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
            assert msg.get("type") == "ready", f"Expected 'ready', got: {msg}"
            print(f"✓ Received ready handshake: version={msg.get('version')}, emotion={msg.get('emotion')}")

            # ── Test 2: Ping / Pong ──────────────────────────────
            await ws.send(json.dumps({"type": "ping"}))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            pong = json.loads(raw)
            assert pong.get("type") == "pong", f"Expected 'pong', got: {pong}"
            print("✓ Ping/Pong working")

            # ── Test 3: Text input → Response ────────────────────
            print("⏳ Sending 'hello' to ZARA brain (may take a moment)...")
            await ws.send(json.dumps({"type": "text", "content": "hello"}))

            # Collect until we get a non-empty response
            reply = None
            for _ in range(10):   # Up to 10 messages (speaking=True then speaking=False)
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                msg = json.loads(raw)
                if msg.get("type") == "response" and msg.get("text"):
                    reply = msg
                    break

            assert reply is not None, "No response received from brain"
            assert "text"    in reply, "Response missing 'text' field"
            assert "emotion" in reply, "Response missing 'emotion' field"
            assert "speaking" in reply, "Response missing 'speaking' field"
            print(f"✓ Brain responded: emotion={reply['emotion']}, speaking={reply['speaking']}")
            print(f"  ZARA says: \"{reply['text'][:120]}{'...' if len(reply['text'])>120 else ''}\"")
            has_audio = bool(reply.get("audio_b64"))
            print(f"  Audio: {'✓ included' if has_audio else '✗ not included (TTS may be unavailable)'}")

    except ConnectionRefusedError:
        print("✗ Connection refused. Is 'python main.py --server' running?")
        sys.exit(1)
    except asyncio.TimeoutError:
        print("✗ Timeout waiting for ZARA response.")
        sys.exit(1)
    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print("✅ All WebSocket tests PASSED")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(run_test())
