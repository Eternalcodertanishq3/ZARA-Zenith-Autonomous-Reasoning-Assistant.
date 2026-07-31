import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence, useSpring } from "framer-motion";
import { getCurrentWindow, LogicalPosition } from "@tauri-apps/api/window";
import LumiOrb from "./components/LumiOrb";
import { ListeningUI, TaskUI, ErrorUI, IncomingCallUI, ActiveCallUI, CallEndedUI, MusicVisualizerUI, DeployingUI, DictatingUI, WarningUI, MessageReceivedUI, MessageSendingUI, MessageSentUI, ThinkingUI } from "./components/StateOverlays";
import { LumiState } from "./config/lumi.config";
import "./App.css";

export default function App() {
  const [appState, setAppState] = useState<LumiState>("boot");

  // 3D Tilt interactive spring values with responsive damping
  const rotateX = useSpring(0, { stiffness: 120, damping: 20 });
  const rotateY = useSpring(0, { stiffness: 120, damping: 20 });
  const tiltScale = useSpring(1, { stiffness: 120, damping: 20 });
  const tiltZ = useSpring(0, { stiffness: 120, damping: 20 });

  // WebGL tracking states
  const normalizedMouseX = useSpring(0, { stiffness: 150, damping: 25 });
  const normalizedMouseY = useSpring(0, { stiffness: 150, damping: 25 });
  const dragOffsetX = useSpring(0, { stiffness: 120, damping: 15 });
  const dragOffsetY = useSpring(0, { stiffness: 120, damping: 15 });
  const audioVolumeRef = useRef<number>(0);

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    
    // Normalized cursor coordinates (-0.5 to 0.5)
    const x = (e.clientX - rect.left) / width - 0.5;
    const y = (e.clientY - rect.top) / height - 0.5;
    
    // Task panel is larger, so tilt it slightly less to keep text readable
    const maxTilt = ["task", "task_bg", "compiling", "fetching_data"].includes(appState) ? 8 : 14;

    rotateX.set(-y * maxTilt);
    rotateY.set(x * maxTilt);
    tiltScale.set(1.03);
    tiltZ.set(15);
    normalizedMouseX.set(x * 2.0);
    normalizedMouseY.set(y * 2.0);
  };

  const handlePointerLeave = () => {
    rotateX.set(0);
    rotateY.set(0);
    tiltScale.set(1);
    tiltZ.set(0);
    normalizedMouseX.set(0);
    normalizedMouseY.set(0);
  };

  // Audio Analyzer
  useEffect(() => {
    let audioCtx: AudioContext;
    let analyzer: AnalyserNode;
    let dataArray: Uint8Array;
    let rafId: number;

    const setupAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new AudioContext();
        analyzer = audioCtx.createAnalyser();
        analyzer.fftSize = 256;
        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyzer);
        dataArray = new Uint8Array(analyzer.frequencyBinCount);

        const tick = () => {
          analyzer.getByteFrequencyData(dataArray as any);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const average = sum / dataArray.length;
          // Normalize volume roughly between 0 and 1
          audioVolumeRef.current = Math.min(average / 100, 1.0);
          rafId = requestAnimationFrame(tick);
        };
        tick();
      } catch (err) {
        console.warn("Microphone access denied or unavailable", err);
      }
    };
    setupAudio();

    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      if (audioCtx) audioCtx.close();
    };
  }, []);

  // Inertia Window Drag
  useEffect(() => {
    let unlisten: () => void;
    let lastX = 0;
    let lastY = 0;
    
    const trackDrag = async () => {
      try {
        const appWindow = getCurrentWindow();
        const pos = await appWindow.outerPosition();
        lastX = pos.x;
        lastY = pos.y;

        unlisten = await appWindow.onMoved(({ payload }) => {
          const dx = payload.x - lastX;
          const dy = payload.y - lastY;
          lastX = payload.x;
          lastY = payload.y;

          // Push the orb in the opposite direction of the drag (lag effect)
          dragOffsetX.set(Math.max(-40, Math.min(40, dragOffsetX.get() - dx)));
          dragOffsetY.set(Math.max(-40, Math.min(40, dragOffsetY.get() - dy)));
        });
      } catch (e) {}
    };
    trackDrag();

    // Snap back loop - constantly seek 0 so the spring pulls it back when dragging stops
    const interval = setInterval(() => {
      dragOffsetX.set(0);
      dragOffsetY.set(0);
    }, 100);

    return () => {
      if (unlisten) unlisten();
      clearInterval(interval);
    };
  }, []);

  // Automatically transition from Boot to Idle, and Call Ended to Idle after 2 seconds
  useEffect(() => {
    if (appState === "boot") {
      const timer = setTimeout(() => setAppState("idle"), 2000);
      return () => clearTimeout(timer);
    } else if (appState === "call_ended") {
      const timer = setTimeout(() => setAppState("idle"), 2000);
      return () => clearTimeout(timer);
    }
  }, [appState]);

  // Position logic (Top Center)
  useEffect(() => {
    const positionWindow = async () => {
      try {
        const appWindow = getCurrentWindow();
        await appWindow.center();
        const pos = await appWindow.outerPosition();
        const factor = await appWindow.scaleFactor();
        await appWindow.setPosition(new LogicalPosition(pos.x / factor, 40));
      } catch (err) {}
    };
    positionWindow();
  }, []);

  // Keyboard Simulation (Cycle through states for testing)
  useEffect(() => {
    const states: LumiState[] = [
      "boot", "idle", "sleep", "waking", "locked", "admin_override", "shutting_down",
      "listening", "listening_loud", "thinking", "speaking", "dictating",
      "incoming_call", "active_call", "call_ended", "message_received", "message_sending", "message_sent",
      "task", "task_bg", "compiling", "fetching_data", "deploying", "success", "error", "warning",
      "music_playing", "music_paused", "muted", "dnd_mode",
      "hover", "clicked", "file_dropped",
      "analyzing_vision", "reading_screen", "writing_code", "generating_media",
      "network_offline", "battery_low", "syncing_cloud", "focus_mode"
    ];
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") {
        setAppState(prev => states[(states.indexOf(prev) + 1) % states.length]);
      } else if (e.key === "ArrowLeft") {
        setAppState(prev => states[(states.indexOf(prev) - 1 + states.length) % states.length]);
      } else if (e.key === "1") setAppState("idle");
      else if (e.key === "2") setAppState("listening");
      else if (e.key === "3") setAppState("task");
      else if (e.key === "4") setAppState("incoming_call");
      else if (e.key === "5") setAppState("music_playing");
      else if (e.key === "6") setAppState("deploying");
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // WebSocket connection to Python Backend
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: number;

    const connect = () => {
      ws = new WebSocket("ws://localhost:8000");

      ws.onopen = () => {
        console.log("Connected to Python backend");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.trigger) {
            setAppState(data.trigger as LumiState);
          }
        } catch (err) {
          console.error("Failed to parse websocket message", err);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket closed, attempting to reconnect...");
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error", err);
        ws?.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null; // Prevent reconnect on explicit unmount
        ws.close();
      }
    };
  }, []);

  // Determine if the current state uses the premium glass background
  const isGlassState = ![
    "boot", "shutting_down", "sleep", "dnd_mode",
    "idle", "waking", "locked", "admin_override", 
    "success", "hover", "clicked", "file_dropped", "music_paused", "muted",
    "analyzing_vision", "reading_screen", "writing_code", "generating_media",
    "network_offline", "battery_low", "syncing_cloud", "focus_mode"
  ].includes(appState);

  // Shadow animated smoothly by Framer Motion in sync with size (border lives on the glass child)
  const glassAnimate = isGlassState
    ? { boxShadow: "0px 12px 40px rgba(0, 0, 0, 0.4)" }
    : { boxShadow: "0px 0px 0px rgba(0, 0, 0, 0)" };

  // Mapping each state to its exact physical dimensions to bypass Chromium's transform scale backdrop-blur bug
  const getLayout = (state: LumiState) => {
    if (["boot", "shutting_down"].includes(state)) {
      return { 
        width: 256, 
        height: 256, 
        borderRadius: 40, 
        paddingLeft: 0, 
        paddingRight: 0, 
        paddingTop: 0, 
        paddingBottom: 0, 
        flexDirection: "row" as const, 
        alignItems: "center", 
        justifyContent: "center" 
      };
    }
    if (["sleep", "dnd_mode", "focus_mode"].includes(state)) {
      return { 
        width: 40, 
        height: 40, 
        borderRadius: 20, 
        paddingLeft: 0, 
        paddingRight: 0, 
        paddingTop: 0, 
        paddingBottom: 0, 
        flexDirection: "row" as const, 
        alignItems: "center", 
        justifyContent: "center" 
      };
    }
    if (["idle", "waking", "locked", "admin_override", "success", "hover", "clicked", "file_dropped", "music_paused", "muted", "analyzing_vision", "reading_screen", "writing_code", "generating_media", "network_offline", "battery_low", "syncing_cloud"].includes(state)) {
      return { 
        width: 80, 
        height: 80, 
        borderRadius: 40, 
        paddingLeft: 0, 
        paddingRight: 0, 
        paddingTop: 0, 
        paddingBottom: 0, 
        flexDirection: "row" as const, 
        alignItems: "center", 
        justifyContent: "center" 
      };
    }
    if (["incoming_call", "active_call", "call_ended", "music_playing"].includes(state)) {
      return { 
        width: 336, 
        height: 72, 
        borderRadius: 36, 
        paddingLeft: 12, 
        paddingRight: 16, 
        paddingTop: 0, 
        paddingBottom: 0, 
        flexDirection: "row" as const, 
        alignItems: "center", 
        justifyContent: "space-between" 
      };
    }
    if (["listening", "listening_loud", "thinking", "speaking", "dictating", "error", "warning", "message_received", "message_sending", "message_sent"].includes(state)) {
      return { 
        width: 320, 
        height: 72, 
        borderRadius: 36, 
        paddingLeft: 16, 
        paddingRight: 16, 
        paddingTop: 0, 
        paddingBottom: 0, 
        flexDirection: "row" as const, 
        alignItems: "center", 
        justifyContent: "space-between" 
      };
    }
    // Task card layout states
    return { 
      width: 320, 
      height: 288, 
      borderRadius: 32, 
      paddingLeft: 20, 
      paddingRight: 20, 
      paddingTop: 20, 
      paddingBottom: 20, 
      flexDirection: "column" as const, 
      alignItems: "flex-start", 
      justifyContent: "flex-start" 
    };
  };

  const layout = getLayout(appState);

  return (
    <div className="w-screen h-screen flex items-start justify-center pt-6 relative select-none" style={{ perspective: 1000 }}>
      {/* Ambient Floating Wrapper */}
      <motion.div
        animate={{ 
          y: [0, -5, 0],
          rotateX: [-1, 1, -1],
          rotateY: [-1.5, 1.5, -1.5],
        }}
        transition={{ 
          repeat: Infinity, 
          duration: 6, 
          ease: "easeInOut" 
        }}
        style={{ transformStyle: "preserve-3d" }}
      >
        {/* Interactive 3D Tilt Wrapper */}
        <motion.div
          style={{
            rotateX,
            rotateY,
            scale: tiltScale,
            z: tiltZ,
            transformStyle: "preserve-3d",
          }}
          onPointerMove={handlePointerMove}
          onPointerLeave={handlePointerLeave}
        >
          {/* Sizing Layout Container */}
          <motion.div
            data-tauri-drag-region
            onPointerDown={(e) => { e.preventDefault(); getCurrentWindow().startDragging(); }}
            animate={{ ...layout, ...glassAnimate }}
            transition={{ type: "spring", stiffness: 220, damping: 25 }}
            className="flex cursor-grab active:cursor-grabbing relative"
            style={{ transformStyle: "preserve-3d" }}
          >
            {/* Glassmorphic Background Child — border lives here to avoid pointed-corner artifacts */}
            {isGlassState && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, borderRadius: layout.borderRadius }}
                transition={{ 
                  opacity: { duration: 0.3 },
                  borderRadius: { type: "spring", stiffness: 220, damping: 25 }
                }}
                className="absolute inset-0 bg-black/35 backdrop-blur-3xl border border-white/[0.15] -z-10 pointer-events-none"
                style={{ transform: "translateZ(-8px)" }}
              />
            )}

            <LumiOrb 
              appState={appState} 
              mouseX={normalizedMouseX}
              mouseY={normalizedMouseY}
              dragOffsetX={dragOffsetX}
              dragOffsetY={dragOffsetY}
              audioVolumeRef={audioVolumeRef}
            />

            <div style={{ transform: "translateZ(10px)", transformStyle: "preserve-3d" }} className="flex flex-grow items-center h-full min-w-0">
              <AnimatePresence mode="wait">
                {["listening", "listening_loud"].includes(appState) && <ListeningUI key="listen" />}
                {appState === "thinking" && <ThinkingUI key="thinking" />}
                {["task", "task_bg", "compiling", "fetching_data"].includes(appState) && <TaskUI key="task" />}
                {appState === "error" && <ErrorUI key="error" />}
                {appState === "warning" && <WarningUI key="warning" />}
                {appState === "dictating" && <DictatingUI key="dictate" />}
                {appState === "message_received" && <MessageReceivedUI key="msg_recv" />}
                {appState === "message_sending" && <MessageSendingUI key="msg_send" />}
                {appState === "message_sent" && <MessageSentUI key="msg_sent" />}
                {appState === "incoming_call" && (
                  <IncomingCallUI 
                    key="incoming_call" 
                    onAccept={() => setAppState("active_call")} 
                    onDecline={() => setAppState("call_ended")} 
                  />
                )}
                {appState === "active_call" && (
                  <ActiveCallUI 
                    key="active_call" 
                    onDecline={() => setAppState("call_ended")} 
                  />
                )}
                {appState === "call_ended" && <CallEndedUI key="call_ended" />}
                {appState === "music_playing" && <MusicVisualizerUI key="music" />}
                {appState === "deploying" && <DeployingUI key="deploying" />}
              </AnimatePresence>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
