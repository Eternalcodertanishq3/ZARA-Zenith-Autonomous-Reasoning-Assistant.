/**
 * ZARA UI — zara_ui.js
 * =====================
 * Three.js VRM holographic avatar + WebSocket brain client.
 *
 * Responsibilities:
 *  1. Particle ambient background (canvas 2D)
 *  2. Three.js scene with transparent background
 *  3. Load Zara_avatar.vrm via GLTFLoader + VRMLoaderPlugin
 *  4. Animate VRM: blink, breathe, mouth, expression morphs
 *  5. WebSocket client → receive brain JSON → trigger animations
 *  6. Mic input via Web Speech API → send text to brain
 *  7. HUD updates: mood, speaking wave, transcript, time
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

// ═══════════════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════════════
const WS_URL      = 'ws://127.0.0.1:8000/ws/brain';
const VRM_URL     = '/assets/avatar/Zara_avatar.vrm';
const RECONNECT_INTERVAL_MS = 3000;

// Emotion → VRM expression name mapping
const EMOTION_TO_VRM = {
  happy:     'happy',
  sad:       'sad',
  angry:     'angry',
  surprised: 'surprised',
  fun:       'fun',
  excited:   'happy',
  neutral:   'neutral',
  thinking:  'relaxed',
  relaxed:   'relaxed',
};

// Emotion → ring / accent color
const EMOTION_COLORS = {
  happy:     '#1affa0',
  sad:       '#4fa3ff',
  angry:     '#ff4444',
  surprised: '#f5a623',
  excited:   '#ff4fa3',
  neutral:   '#7c6fff',
  thinking:  '#06d6f0',
  relaxed:   '#7c6fff',
};


// ═══════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════
let vrm          = null;          // Loaded VRM model
let clock        = new THREE.Clock();
let isSpeaking   = false;
let currentEmotion = 'neutral';
let mouthValue   = 0;             // 0..1 current morph weight for "aa"
let mouthTarget  = 0;
let blinkTimer   = 0;
let isBlinking   = false;
let blinkCooldown = randomBlink();
let breathPhase  = 0;
let muted        = false;

// Audio playback queue
const audioQueue = [];
let audioPlaying = false;


// ═══════════════════════════════════════════════════════════════════
// 1. PARTICLE BACKGROUND
// ═══════════════════════════════════════════════════════════════════
const pCanvas = document.getElementById('particle-canvas');
const pCtx    = pCanvas.getContext('2d');

const PARTICLE_COUNT = 120;
const particles = [];

function initParticles() {
  pCanvas.width  = window.innerWidth;
  pCanvas.height = window.innerHeight;
  particles.length = 0;
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x:  Math.random() * pCanvas.width,
      y:  Math.random() * pCanvas.height,
      r:  Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      a:  Math.random() * 0.6 + 0.1,
    });
  }
}

function animateParticles() {
  pCtx.clearRect(0, 0, pCanvas.width, pCanvas.height);
  for (const p of particles) {
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = pCanvas.width;
    if (p.x > pCanvas.width)  p.x = 0;
    if (p.y < 0) p.y = pCanvas.height;
    if (p.y > pCanvas.height) p.y = 0;
    pCtx.beginPath();
    pCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    pCtx.fillStyle = `rgba(124, 111, 255, ${p.a})`;
    pCtx.fill();
  }
  requestAnimationFrame(animateParticles);
}

initParticles();
animateParticles();


// ═══════════════════════════════════════════════════════════════════
// 2. THREE.JS SCENE
// ═══════════════════════════════════════════════════════════════════
const canvas   = document.getElementById('zara-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000000, 0);     // Fully transparent background
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 1.35, 3.5);

// Lights
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const keyLight = new THREE.DirectionalLight(0xe8f4ff, 1.4);
keyLight.position.set(1, 3, 2);
keyLight.castShadow = true;
scene.add(keyLight);

const rimLight = new THREE.DirectionalLight(0x7c6fff, 0.8);
rimLight.position.set(-2, 1, -2);
scene.add(rimLight);

const fillLight = new THREE.PointLight(0x06d6f0, 0.5, 8);
fillLight.position.set(0, 0.5, 2);
scene.add(fillLight);

// Orbit controls — limited so avatar stays nicely framed
const controls = new OrbitControls(camera, renderer.domElement);
controls.enablePan  = false;
controls.enableZoom = false;
controls.minPolarAngle = Math.PI * 0.28;
controls.maxPolarAngle = Math.PI * 0.62;
controls.minAzimuthAngle = -Math.PI * 0.25;
controls.maxAzimuthAngle =  Math.PI * 0.25;
controls.enableDamping = true;
controls.dampingFactor = 0.08;


// ═══════════════════════════════════════════════════════════════════
// 3. VRM LOADER
// ═══════════════════════════════════════════════════════════════════
function loadVRM() {
  const loader = new GLTFLoader();
  loader.register(parser => new VRMLoaderPlugin(parser, { autoUpdateHumanBones: true }));

  setLoadingStatus('Loading VRM avatar...');

  loader.load(
    VRM_URL,
    (gltf) => {
      vrm = gltf.userData.vrm;
      if (!vrm) {
        setLoadingStatus('⚠ VRM data not found in model.');
        console.error('No VRM userData found in loaded GLTF.');
        setTimeout(hideLoadingScreen, 2000);
        return;
      }

      VRMUtils.removeUnnecessaryJoints(gltf.scene);
      VRMUtils.removeUnnecessaryVertices(gltf.scene);

      // Face camera
      vrm.scene.rotation.y = Math.PI;
      scene.add(vrm.scene);

      // Auto-center & scale the avatar
      const box    = new THREE.Box3().setFromObject(vrm.scene);
      const size   = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const scale  = 1.4 / size.y;
      vrm.scene.scale.setScalar(scale);
      vrm.scene.position.sub(center.multiplyScalar(scale));
      vrm.scene.position.y -= 0.15;

      // ── Fix T-pose: rotate arms down to a natural idle pose ──────────────
      _applyIdlePose();

      console.log('✓ VRM avatar loaded', vrm);
      setLoadingStatus('Avatar online ✓');
      hideLoadingScreen();
    },
    (progress) => {
      const pct = Math.round((progress.loaded / (progress.total || 1)) * 100);
      setLoadingStatus(`Loading VRM... ${pct}%`);
      setLoadingBar(pct);
    },
    (error) => {
      console.error('VRM load failed:', error);
      setLoadingStatus('⚠ Avatar unavailable — running without VRM');
      setTimeout(hideLoadingScreen, 2000);
    }
  );
}


// ═══════════════════════════════════════════════════════════════════
// 4. VRM ANIMATION HELPERS
// ═══════════════════════════════════════════════════════════════════

/**
 * Apply a relaxed idle pose to fix VRM T-pose.
 * Called once after the VRM loads.
 */
function _applyIdlePose() {
  if (!vrm?.humanoid) return;
  const setBone = (name, rx, ry, rz) => {
    const bone = vrm.humanoid.getNormalizedBoneNode(name);
    if (bone) { bone.rotation.x = rx; bone.rotation.y = ry; bone.rotation.z = rz; }
  };
  // Bring arms down from T-pose
  setBone('leftUpperArm',   0,  0,  1.25);  // left shoulder rotates down
  setBone('leftLowerArm',   0, -0.15, 0.2); // slight elbow bend
  setBone('rightUpperArm',  0,  0, -1.25);  // right shoulder mirrors
  setBone('rightLowerArm',  0,  0.15,-0.2);
  // Light forward tilt for natural posture
  setBone('chest', -0.04, 0, 0);
  setBone('spine', -0.02, 0, 0);
}

/** Get a safe VRM expression value (0–1). */
function getExpr(name) {
  if (!vrm?.expressionManager) return 0;
  try { return vrm.expressionManager.getValue(name) ?? 0; } catch { return 0; }
}

/** Set a VRM expression value (0–1). Fails silently if not found. */
function setExpr(name, value) {
  if (!vrm?.expressionManager) return;
  try { vrm.expressionManager.setValue(name, Math.max(0, Math.min(1, value))); } catch {}
}

function randomBlink() { return 2.5 + Math.random() * 3; }

/** Update blink every frame. */
function updateBlink(delta) {
  blinkTimer += delta;
  if (!isBlinking && blinkTimer > blinkCooldown) {
    isBlinking = true; blinkTimer = 0;
  }
  if (isBlinking) {
    const t = blinkTimer / 0.12;
    const v = t < 0.5 ? t * 2 : 2 - t * 2;
    setExpr('blink', Math.max(0, Math.min(1, v)));
    if (blinkTimer > 0.12) { isBlinking = false; blinkTimer = 0; blinkCooldown = randomBlink(); setExpr('blink', 0); }
  }
}

/** Smooth mouth animation driven by isSpeaking flag. */
function updateMouth(delta) {
  if (isSpeaking) {
    mouthTarget = 0.15 + 0.45 * Math.abs(Math.sin(Date.now() * 0.008));
  } else {
    mouthTarget = 0;
  }
  mouthValue += (mouthTarget - mouthValue) * Math.min(1, delta * 12);
  setExpr('aa', mouthValue);
}

/** Subtle head nod to breathing rhythm. */
function updateBreath(delta) {
  breathPhase += delta;
  if (!vrm?.humanoid) return;
  const neck = vrm.humanoid.getNormalizedBoneNode('neck');
  if (neck) {
    neck.rotation.x = Math.sin(breathPhase * 0.6) * 0.012;
  }
  const spine = vrm.humanoid.getNormalizedBoneNode('spine');
  if (spine) {
    spine.rotation.z = Math.sin(breathPhase * 0.4) * 0.008;
  }
}

/** Apply emotion expression. */
function applyEmotion(emotion) {
  if (!vrm?.expressionManager) return;
  const vrmName  = EMOTION_TO_VRM[emotion] ?? 'neutral';
  const allExprs = ['happy', 'sad', 'angry', 'surprised', 'fun', 'relaxed', 'neutral'];

  // Fade out all, fade in target
  for (const e of allExprs) {
    const current = getExpr(e);
    const target  = (e === vrmName) ? 1 : 0;
    setExpr(e, current + (target - current) * 0.15);
  }

  // Update accent color
  const color = EMOTION_COLORS[emotion] ?? EMOTION_COLORS.neutral;
  document.querySelector('.ring-progress')?.style.setProperty('stroke', color);
  document.querySelector('.ring-progress')?.style.setProperty('filter', `drop-shadow(0 0 6px ${color})`);
  fillLight.color.setStyle(color);
}


// ═══════════════════════════════════════════════════════════════════
// 5. RENDER LOOP
// ═══════════════════════════════════════════════════════════════════
function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();

  if (vrm) {
    updateBlink(delta);
    updateMouth(delta);
    updateBreath(delta);
    applyEmotion(currentEmotion);
    vrm.update(delta);
  }

  controls.update();
  renderer.render(scene, camera);
}

animate();


// ═══════════════════════════════════════════════════════════════════
// 6. WEBSOCKET BRAIN CLIENT
// ═══════════════════════════════════════════════════════════════════
let ws          = null;
let wsConnected = false;
let reconnectTimer = null;

function connectWS() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    wsConnected = true;
    setWSStatus(true);
    addMsg('SYSTEM', 'Connected to ZARA brain ✓', 'system');
    clearTimeout(reconnectTimer);
  };

  ws.onclose = () => {
    wsConnected = false;
    setWSStatus(false);
    addMsg('SYSTEM', 'Connection lost. Reconnecting...', 'system');
    reconnectTimer = setTimeout(connectWS, RECONNECT_INTERVAL_MS);
  };

  ws.onerror = (e) => {
    console.error('[WS] Error:', e);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleBrainMessage(data);
    } catch (err) {
      console.error('[WS] JSON parse error:', err, event.data);
    }
  };
}

function handleBrainMessage(data) {
  switch (data.type) {
    case 'ready':
      setConnectionStatus('online', 'ONLINE');
      addMsg('SYSTEM', `ZARA v${data.version ?? '4.0'} ready`, 'system');
      break;

    case 'response':
      if (data.text) {
        addMsg('ZARA', data.text, 'zara');
        // Speak via browser SpeechSynthesis (instant — no network wait)
        speakText(data.text);
      }
      // Emotion
      if (data.emotion) {
        currentEmotion = data.emotion.toLowerCase().trim();
        updateMoodDisplay(currentEmotion);
      }
      // Speaking state
      isSpeaking = !!data.speaking;
      setSpeakingState(isSpeaking);
      break;

    case 'status':
      if (data.mood) {
        currentEmotion = data.mood.toLowerCase();
        updateMoodDisplay(currentEmotion);
      }
      break;

    case 'pong':
      // Heartbeat acknowledged
      break;

    case 'error':
      console.warn('[ZARA] Server error:', data.message);
      addMsg('SYSTEM', `Error: ${data.message}`, 'system');
      break;
  }
}

function sendText(text) {
  if (!text.trim()) return;
  if (!wsConnected || ws.readyState !== WebSocket.OPEN) {
    addMsg('SYSTEM', '⚠ Not connected. Retry...', 'system');
    connectWS();
    return;
  }
  addMsg('YOU', text, 'user');
  ws.send(JSON.stringify({ type: 'text', content: text }));
}


// ═══════════════════════════════════════════════════════════════════
// 7. BROWSER SPEECH SYNTHESIS (instant voice — no latency)
// Window.speechSynthesis is built into every modern browser/webview.
// ═══════════════════════════════════════════════════════════════════
let synth = window.speechSynthesis;
let synthVoice = null;

// Pick the best available female voice
function initSynthVoice() {
  if (synthVoice) return;
  const voices = synth.getVoices();
  // Prefer Microsoft Zira (Windows) or Google UK Female
  synthVoice =
    voices.find(v => v.name.includes('Zira')) ||
    voices.find(v => v.name.includes('Google UK English Female')) ||
    voices.find(v => v.lang === 'en-US' && v.name.toLowerCase().includes('female')) ||
    voices.find(v => v.lang.startsWith('en')) ||
    voices[0] || null;
}

// Pre-load voices (Chrome needs this)
if (synth.onvoiceschanged !== undefined) {
  synth.onvoiceschanged = initSynthVoice;
}
initSynthVoice();

function speakText(text) {
  if (muted || !text || !synth) return;
  // Clean think-tags and action markers
  const clean = text
    .replace(/<think>[\s\S]*?<\/think>/g, '')
    .replace(/\*[^*]+\*/g, '')
    .trim();
  if (!clean) return;

  // Cancel any current speech before starting new one
  synth.cancel();
  initSynthVoice();

  const utt = new SpeechSynthesisUtterance(clean);
  utt.voice  = synthVoice;
  utt.rate   = 1.05;
  utt.pitch  = 1.1;
  utt.volume = 1.0;
  utt.lang   = 'en-US';
  synth.speak(utt);
}


// ═══════════════════════════════════════════════════════════════════
// 8. MIC INPUT — Web Speech API
// ═══════════════════════════════════════════════════════════════════
let recognition = null;
let micActive   = false;

function initMic() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn('[MIC] Web Speech API not supported in this browser.');
    document.getElementById('mic-btn').title = 'Mic not supported in this browser';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous       = false;
  recognition.interimResults   = false;
  recognition.lang             = 'en-US';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    sendText(transcript);
  };

  recognition.onerror = (e) => {
    console.error('[MIC] Error:', e.error);
    setMicState(false);
  };
  recognition.onend  = () => setMicState(false);
  recognition.onstart = () => setMicState(true);
}

function toggleMic() {
  if (!recognition) { initMic(); }
  if (!recognition) return;

  if (micActive) {
    recognition.stop();
  } else {
    try { recognition.start(); } catch {}
  }
}

function setMicState(active) {
  micActive = active;
  const btn = document.getElementById('mic-btn');
  if (active) { btn.classList.add('active'); btn.textContent = '🔴'; }
  else         { btn.classList.remove('active'); btn.textContent = '🎤'; }
}


// ═══════════════════════════════════════════════════════════════════
// 9. HUD UPDATE HELPERS
// ═══════════════════════════════════════════════════════════════════

function addMsg(name, text, type = 'user') {
  const container = document.getElementById('transcript');
  const div       = document.createElement('div');
  div.className   = `msg ${type === 'zara' ? 'zara' : type === 'system' ? 'system' : ''}`;
  div.innerHTML   = `<span class="msg-name">${escapeHtml(name)}</span>
                     <span class="msg-text">${escapeHtml(text)}</span>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function setConnectionStatus(cls, text) {
  const pill = document.getElementById('status-pill');
  const txt  = document.getElementById('status-text');
  pill.className = `status-pill ${cls}`;
  txt.textContent = text;
}

function setWSStatus(connected) {
  const ind = document.getElementById('ws-indicator');
  ind.className = connected ? 'ws-indicator connected' : 'ws-indicator';
  if (connected) {
    setConnectionStatus('online', 'ONLINE');
  } else {
    setConnectionStatus('', 'OFFLINE');
  }
}

function updateMoodDisplay(emotion) {
  const el = document.getElementById('mood-display');
  if (el) el.textContent = emotion.toUpperCase();
  const state = document.getElementById('avatar-state');
  if (state) state.textContent = capitalize(emotion);
}

function setSpeakingState(speaking) {
  const wave  = document.getElementById('speaking-wave');
  const state = document.getElementById('avatar-state');
  if (wave) { speaking ? wave.classList.add('active') : wave.classList.remove('active'); }
  if (state && speaking) state.textContent = 'Speaking...';
  else if (state) state.textContent = capitalize(currentEmotion);
}

function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }

// Clock
function updateClock() {
  const now = new Date();
  const h   = String(now.getHours()).padStart(2, '0');
  const m   = String(now.getMinutes()).padStart(2, '0');
  const el  = document.getElementById('hud-time');
  if (el) el.textContent = `${h}:${m}`;
}
setInterval(updateClock, 1000);
updateClock();

// Ping to keep WS alive
setInterval(() => {
  if (wsConnected && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 20000);


// ═══════════════════════════════════════════════════════════════════
// 10. LOADING SCREEN
// ═══════════════════════════════════════════════════════════════════
function injectLoadingScreen() {
  const div = document.createElement('div');
  div.id = 'loading-screen';
  div.innerHTML = `
    <div class="loading-logo">⬡</div>
    <div class="loading-title">ZARA</div>
    <div class="loading-status" id="loading-status">Initializing neural systems...</div>
    <div class="loading-bar-wrap"><div class="loading-bar" id="loading-bar"></div></div>
  `;
  document.body.appendChild(div);
}

function setLoadingStatus(msg) {
  const el = document.getElementById('loading-status');
  if (el) el.textContent = msg;
}

function setLoadingBar(pct) {
  const el = document.getElementById('loading-bar');
  if (el) el.style.width = `${pct}%`;
}

function hideLoadingScreen() {
  setLoadingBar(100);
  setTimeout(() => {
    const el = document.getElementById('loading-screen');
    if (el) { el.classList.add('fade-out'); setTimeout(() => el.remove(), 900); }
  }, 400);
}


// ═══════════════════════════════════════════════════════════════════
// 11. RESIZE HANDLER
// ═══════════════════════════════════════════════════════════════════
function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  pCanvas.width  = window.innerWidth;
  pCanvas.height = window.innerHeight;
}
window.addEventListener('resize', onResize);


// ═══════════════════════════════════════════════════════════════════
// 12. UI EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════════
document.getElementById('send-btn').addEventListener('click', () => {
  const input = document.getElementById('chat-input');
  sendText(input.value);
  input.value = '';
});

document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    sendText(input.value);
    input.value = '';
  }
});

document.getElementById('mic-btn').addEventListener('click', toggleMic);

document.getElementById('btn-mute').addEventListener('click', () => {
  muted = !muted;
  const btn = document.getElementById('btn-mute');
  btn.textContent = muted ? '🔇' : '🔊';
  btn.classList.toggle('active', muted);
});

document.getElementById('btn-fullscreen').addEventListener('click', () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen();
  else document.exitFullscreen();
});

document.getElementById('btn-end').addEventListener('click', () => {
  if (confirm('End ZARA session?')) {
    ws?.close();
    window.close();
  }
});


// ═══════════════════════════════════════════════════════════════════
// BOOT SEQUENCE
// ═══════════════════════════════════════════════════════════════════
injectLoadingScreen();
setLoadingStatus('Connecting to ZARA brain...');
setLoadingBar(10);
connectWS();
setLoadingBar(30);
setLoadingStatus('Building 3D scene...');
setTimeout(() => {
  setLoadingBar(55);
  setLoadingStatus('Loading VRM avatar from server...');
  loadVRM();
}, 200);
