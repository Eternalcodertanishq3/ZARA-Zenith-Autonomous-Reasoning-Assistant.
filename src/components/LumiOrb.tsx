import { useEffect, useRef } from "react";
import { motion, MotionValue } from "framer-motion";
import { LumiPhysics, LumiState } from "../config/lumi.config";

const fragmentShaderSource = `
  precision highp float;
  uniform float u_time;
  uniform vec2 u_resolution;
  uniform float u_intensity;
  uniform float u_color_mode;
  uniform vec2 u_mouse;

  void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    float d = length(uv);

    // Give the orb slightly more breathing room so the glow doesn't hit the canvas edge
    float mask = smoothstep(0.95, 0.80, d);
    if (mask <= 0.0) { gl_FragColor = vec4(0.0); return; }

    float t = u_time;
    // Clamp the wave amplitude so the geometry doesn't tear itself apart at high intensities
    float amp = 0.5 + min(u_intensity * 0.15, 0.3); 
    
    // Core offset based on u_mouse
    vec2 coreUv = uv - (u_mouse * 0.3); // slight offset towards mouse
    float dCore = length(coreUv);

    float wave1 = sin(uv.x * 2.5 + t) * amp + 0.5;
    float wave2 = cos(uv.y * 3.0 - t * 0.8) * amp + 0.5;
    float wave3 = sin((uv.x + uv.y) * 2.0 + t * 1.2) * amp + 0.5;

    float coreWave1 = sin(coreUv.x * 2.5 + t) * amp + 0.5;
    float coreWave2 = cos(coreUv.y * 3.0 - t * 0.8) * amp + 0.5;
    float coreWave3 = sin((coreUv.x + coreUv.y) * 2.0 + t * 1.2) * amp + 0.5;

    vec3 baseColor = mix(vec3(0.3, 0.0, 1.0), vec3(0.7, 0.0, 0.9), wave1);
    baseColor = mix(baseColor, vec3(0.0, 1.0, 0.6), wave2 * wave3);

    vec3 successColor = mix(vec3(0.0, 0.9, 0.5), vec3(0.8, 1.0, 0.9), wave2);
    vec3 errorColor = mix(vec3(1.0, 0.0, 0.1), vec3(1.0, 0.4, 0.0), wave3);
    vec3 callColor = mix(vec3(0.0, 1.0, 0.4), vec3(0.6, 0.0, 1.0), wave1 * wave3);

    // Mode 3.0: Music (Gold / Sunset Orange)
    vec3 musicColor = mix(vec3(1.0, 0.4, 0.0), vec3(1.0, 0.8, 0.0), wave2);
    
    // Mode 4.0: Sleep / DND (Deep, dark void blue)
    vec3 sleepColor = mix(vec3(0.0, 0.0, 0.05), vec3(0.0, 0.05, 0.15), wave1);
    
    // Mode 5.0: Warning / Locked (Amber)
    vec3 warningColor = mix(vec3(1.0, 0.6, 0.0), vec3(1.0, 0.8, 0.0), wave3);
    
    // Mode 6.0: Auth / Admin (Red Corona, Pure White Core)
    vec3 authColor = mix(vec3(1.0, 0.0, 0.1), vec3(0.9, 0.9, 1.0), wave2 * wave3);

    // Mode 7.0: Focus (Deep Purple)
    vec3 focusColor = mix(vec3(0.1, 0.0, 0.3), vec3(0.3, 0.0, 0.5), wave1);

    // --- UPDATED BLEND LOGIC ---
    
    float successBlend = max(0.0, 1.0 - abs(u_color_mode - 1.0));
    float errorBlend = max(0.0, 1.0 - abs(u_color_mode - 2.0));
    float musicBlend = max(0.0, 1.0 - abs(u_color_mode - 3.0));
    float sleepBlend = max(0.0, 1.0 - abs(u_color_mode - 4.0));
    float warningBlend = max(0.0, 1.0 - abs(u_color_mode - 5.0));
    float authBlend = max(0.0, 1.0 - abs(u_color_mode - 6.0));
    float callBlend = max(0.0, 1.0 - abs(u_color_mode - 0.5));
    float focusBlend = max(0.0, 1.0 - abs(u_color_mode - 7.0));
    
    float auroraBlend = max(0.0, 1.0 - (successBlend + errorBlend + musicBlend + sleepBlend + warningBlend + authBlend + callBlend + focusBlend));

    vec3 finalColor = (baseColor * auroraBlend) + 
                      (successColor * successBlend) + 
                      (errorColor * errorBlend) + 
                      (musicColor * musicBlend) +
                      (sleepColor * sleepBlend) +
                      (warningColor * warningBlend) +
                      (authColor * authBlend) +
                      (callColor * callBlend) +
                      (focusColor * focusBlend);

    // FIX: The Core Clamp
    // Require higher wave intersection to trigger the core
    float core = smoothstep(0.7, 1.0, coreWave1 * coreWave2 * coreWave3); 
    // Force the core to stay strictly in the offset position
    float radialFalloff = 1.0 - smoothstep(0.0, 0.6, dCore); 
    
    // Controlled brightness addition
    finalColor += vec3(1.0) * core * radialFalloff * (1.0 + u_intensity * 0.8);

    finalColor *= smoothstep(1.0, 0.2, d);
    gl_FragColor = vec4(finalColor * mask * 1.8, mask * 0.95);
  }
`;

const vertexShaderSource = `
  attribute vec2 position;
  void main() { gl_Position = vec4(position, 0.0, 1.0); }
`;

export default function LumiOrb({ 
  appState, 
  mouseX, 
  mouseY, 
  dragOffsetX, 
  dragOffsetY, 
  audioVolumeRef 
}: { 
  appState: LumiState;
  mouseX?: MotionValue<number>;
  mouseY?: MotionValue<number>;
  dragOffsetX?: MotionValue<number>;
  dragOffsetY?: MotionValue<number>;
  audioVolumeRef?: React.MutableRefObject<number>;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const targetIntensity = useRef(LumiPhysics.idle.intensity);
  const targetSpeed = useRef(LumiPhysics.idle.speed);
  const targetColorMode = useRef(LumiPhysics.idle.colorMode);

  useEffect(() => {
    const config = LumiPhysics[appState] || LumiPhysics.idle;
    targetIntensity.current = config.intensity;
    targetSpeed.current = config.speed;
    targetColorMode.current = config.colorMode;
  }, [appState]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const gl = canvas.getContext("webgl", { alpha: true });
    if (!gl) return;

    const compile = (src: string, type: number) => {
      const shader = gl.createShader(type);
      if (!shader) return null; gl.shaderSource(shader, src); gl.compileShader(shader); return shader;
    };

    const program = gl.createProgram();
    const vs = compile(vertexShaderSource, gl.VERTEX_SHADER);
    const fs = compile(fragmentShaderSource, gl.FRAGMENT_SHADER);
    if (!vs || !fs || !program) return;
    gl.attachShader(program, vs); gl.attachShader(program, fs); gl.linkProgram(program); gl.useProgram(program);

    const vertices = new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(posLoc); gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    const timeLoc = gl.getUniformLocation(program, "u_time");
    const resLoc = gl.getUniformLocation(program, "u_resolution");
    const intLoc = gl.getUniformLocation(program, "u_intensity");
    const colorModeLoc = gl.getUniformLocation(program, "u_color_mode");
    const mouseLoc = gl.getUniformLocation(program, "u_mouse");

    let frameId: number; let lastTime = performance.now();
    let curIntensity = 0.0; let curSpeed = 1.0; let curColorMode = 0.0; let timeAcc = 0.0;

    const render = () => {
      const now = performance.now(); const dt = (now - lastTime) * 0.001; lastTime = now;
      
      const finalTargetIntensity = audioVolumeRef?.current && audioVolumeRef.current > 0
        ? targetIntensity.current + (audioVolumeRef.current * 1.5)
        : targetIntensity.current;

      curIntensity += (finalTargetIntensity - curIntensity) * 0.1;
      curSpeed += (targetSpeed.current - curSpeed) * 0.05;
      curColorMode += (targetColorMode.current - curColorMode) * 0.15;
      timeAcc += dt * curSpeed;

      // FIX: High-DPI Display support for razor-sharp rendering
      const dpr = window.devicePixelRatio || 1;
      const displayWidth = Math.floor(canvas.clientWidth * dpr);
      const displayHeight = Math.floor(canvas.clientHeight * dpr);

      if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
        canvas.width = displayWidth;
        canvas.height = displayHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }

      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      gl.uniform1f(timeLoc, timeAcc); gl.uniform2f(resLoc, canvas.width, canvas.height); 
      gl.uniform1f(intLoc, curIntensity); gl.uniform1f(colorModeLoc, curColorMode);
      gl.uniform2f(mouseLoc, mouseX?.get() || 0, -(mouseY?.get() || 0));
      
      gl.drawArrays(gl.TRIANGLES, 0, 6); frameId = requestAnimationFrame(render);
    };
    render(); return () => cancelAnimationFrame(frameId);
  }, []);

  return (
    <motion.div 
      data-tauri-drag-region
      layout 
      // Handle fade-in natively through Framer Motion, not CSS
      initial={{ opacity: 0 }}
      animate={{ 
        opacity: 1,
        scale: appState === "speaking" ? [1, 1.15, 1] : 
               appState === "thinking" ? [1, 0.9, 1] : 
               appState === "incoming_call" ? [1, 1.2, 0.9, 1.1, 1] : 1 
      }}
      transition={{ 
        opacity: { duration: 1.5, ease: "easeOut" },
        scale: { 
          repeat: ["speaking", "thinking", "incoming_call"].includes(appState) ? Infinity : 0, 
          duration: appState === "incoming_call" ? 1.2 : appState === "thinking" ? 2.0 : 0.8, 
          ease: "easeInOut" 
        },
        layout: { type: "spring", stiffness: 220, damping: 25 }
      }}
      className={`relative flex-shrink-0 pointer-events-none ${
        ["boot", "shutting_down", "sleep", "dnd_mode", "idle", "waking", "locked", "admin_override", "success", "hover", "clicked", "file_dropped", "music_paused", "muted", "analyzing_vision", "reading_screen", "writing_code", "generating_media", "network_offline", "battery_low", "syncing_cloud", "focus_mode"].includes(appState) 
          ? "w-full h-full" 
          : "w-12 h-12"
      }`}
      style={{ 
        transform: "translateZ(20px)", 
        transformStyle: "preserve-3d",
        x: dragOffsetX,
        y: dragOffsetY 
      }}
    >
      <canvas ref={canvasRef} className="w-full h-full" />
    </motion.div>
  );
}
