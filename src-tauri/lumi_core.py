import asyncio
import json
import io
import wave
import numpy as np
import websockets
import sounddevice as sd
from silero_vad import VADIterator, load_silero_vad
import traceback
import pyaudio
import requests
import pyttsx3
import base64
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# AI Engines
from faster_whisper import WhisperModel
from openai import OpenAI
import ollama
from google import genai

# ==========================================
# ⚙️ HYBRID CONFIGURATION SWITCHBOARD
# ==========================================
class Config:
    # Mode Toggles: True = Cloud Pipeline, False = Local Pipeline
    USE_CLOUD_STT = False 
    USE_CLOUD_LLM = os.getenv("USE_CLOUD_LLM", "False").lower() in ("true", "1")
    USE_CLOUD_TTS = os.getenv("USE_CLOUD_TTS", "False").lower() in ("true", "1")
    
    # API Keys
    CLOUD_STT_API_KEY = "your-stt-api-key-here"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
    
    # Local Model Configurations
    LOCAL_STT_MODEL = "base.en" 
    LOCAL_LLM_MODEL = "gemma4:e2b"
    
    SAMPLE_RATE = 16000

    # VAD Tuning
    VAD_THRESHOLD = 0.85          # Confidence required (0.0 - 1.0)
    VAD_SILENCE_MS = 800          # Silence before speech-end is declared
    RMS_ENERGY_GATE = 300         # Minimum RMS energy to even consider a chunk as speech
    MIN_SPEECH_CHUNKS = 12        # Minimum chunks of speech before we consider it real (~384ms at 512 chunk)

# ==========================================
# 🧠 HYBRID SPEECH-TO-TEXT ENGINE
# ==========================================
class HybridSTT:
    def __init__(self):
        if Config.USE_CLOUD_STT:
            print("[STT] Initializing Cloud Engine (OpenAI/Groq compatible)...")
            self.cloud_client = OpenAI(api_key=Config.CLOUD_STT_API_KEY)
        else:
            print(f"[STT] Initializing Local Engine (Faster-Whisper {Config.LOCAL_STT_MODEL})...")
            self.local_model = WhisperModel(Config.LOCAL_STT_MODEL, device="cpu", compute_type="int8")

    def transcribe(self, audio_bytes: bytes) -> str:
        if Config.USE_CLOUD_STT:
            audio_file = ("audio.wav", audio_bytes, "audio/wav")
            response = self.cloud_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            return response.text.strip()
        else:
            segments, _ = self.local_model.transcribe(io.BytesIO(audio_bytes), beam_size=5)
            text = "".join([segment.text for segment in segments])
            return text.strip()

# ==========================================
# ⚡ HYBRID LLM BRAIN ENGINE
# ==========================================
class HybridLLM:
    def __init__(self):
        self.system_prompt = (
            "You are Lumi, a highly advanced, premium desktop AI assistant. "
            "Your responses must be crisp, direct, and sophisticated. Avoid conversational filler. "
            "Keep responses under 3 sentences unless the user asks for detail."
        )
        
        if Config.USE_CLOUD_LLM:
            print("[LLM] Initializing Cloud Brain (Gemini)...")
            self.cloud_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        else:
            print(f"[LLM] Initializing Local Brain (Ollama: {Config.LOCAL_LLM_MODEL})...")

    def generate_response(self, user_prompt: str) -> str:
        if not user_prompt:
            return "I didn't quite catch that."

        if Config.USE_CLOUD_LLM:
            response = self.cloud_client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    max_output_tokens=150
                )
            )
            return response.text.strip()
        else:
            response = ollama.chat(
                model=Config.LOCAL_LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            return response['message']['content'].strip()

# ==========================================
# 🗣️ HYBRID TEXT-TO-SPEECH ENGINE
# ==========================================
class HybridTTS:
    def __init__(self):
        if Config.USE_CLOUD_TTS:
            print("[TTS] Initializing Cloud Voice (Sarvam AI: Bulbul v3)...")
        else:
            print("[TTS] Initializing Local Voice (Windows Offline Engine)...")
            try:
                self.local_engine = pyttsx3.init()
                self.local_engine.setProperty('rate', 175) # Adjust speed (default is usually 200)
            except Exception as e:
                print(f"[TTS] Failed to initialize pyttsx3: {e}")
                self.local_engine = None

    def speak(self, text: str):
        if Config.USE_CLOUD_TTS:
            try:
                # Sarvam AI API Endpoint
                url = "https://api.sarvam.ai/text-to-speech"
                payload = {
                    "text": text,
                    "target_language_code": "en-IN", # Indian English
                    "speaker": "shreya",             # Premium female voice
                    "model": "bulbul:v3",
                    "pace": 1.05                     # Slightly faster pace
                }
                headers = {
                    "api-subscription-key": Config.SARVAM_API_KEY,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Decode Base64 Audio from Sarvam
                data = response.json()
                audio_base64 = data.get("audios", [])[0]
                audio_bytes = base64.b64decode(audio_base64)
                
                # Play audio using PyAudio
                with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                    p = pyaudio.PyAudio()
                    stream = p.open(
                        format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True
                    )
                    
                    chunk_data = wf.readframes(1024)
                    while chunk_data:
                        stream.write(chunk_data)
                        chunk_data = wf.readframes(1024)
                        
                    stream.stop_stream()
                    stream.close()
                    p.terminate()

            except Exception as e:
                print(f"[TTS Cloud Error]: {e}")
                print("Falling back to local TTS...")
                if self.local_engine:
                    try:
                        self.local_engine.say(text)
                        self.local_engine.runAndWait()
                    except Exception as le:
                        print(f"[TTS Local Error]: {le}")
        else:
            # Execute Local Offline Voice
            if self.local_engine:
                try:
                    self.local_engine.say(text)
                    self.local_engine.runAndWait()
                except Exception as le:
                    print(f"[TTS Local Error]: {le}")

# ==========================================
# 🎤 SILERO VAD AUDIO STREAMER
# ==========================================
class VoiceActivityDetector:
    def __init__(self):
        print("[VAD] Loading Silero VAD Model...")
        self.model = load_silero_vad()
        self.iterator = VADIterator(
            self.model, 
            sampling_rate=Config.SAMPLE_RATE, 
            threshold=Config.VAD_THRESHOLD,
            min_silence_duration_ms=Config.VAD_SILENCE_MS
        )
        
    def reset(self):
        self.iterator.reset_states()

    @staticmethod
    def rms_energy(audio_chunk: np.ndarray) -> float:
        """Calculate RMS energy of an audio chunk. Low values = silence/noise."""
        return float(np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2)))

# ==========================================
# 🌐 ORCHESTRATION & CORE PIPELINE
# ==========================================
connected_clients = set()

# Noise words that Whisper hallucinates on silence/noise
WHISPER_HALLUCINATIONS = {
    "", "(music)", "[music]", "(silence)", "[silence]", 
    "thank you.", "thanks.", "you", "thank you",
    "(applause)", "[applause]", "(laughing)", "[laughing]",
    "(clicking)", "(typing)", "(bell)", "(ding)",
    "♪", "...", ".", "(inaudible)", "[inaudible]"
}

async def send_ui_state(state: str):
    """Broadcasts physical state changes to the Tauri frontend."""
    if connected_clients:
        message = json.dumps({"trigger": state})
        await asyncio.gather(*[client.send(message) for client in connected_clients], return_exceptions=True)

def pcm_to_wav(pcm_data: bytes) -> bytes:
    """Wraps raw PCM audio data into a valid WAV container for STT consumption."""
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(Config.SAMPLE_RATE)
            wav_file.writeframes(pcm_data)
        return wav_buffer.getvalue()

async def audio_processing_loop():
    print("\n[Lumi] Physical nervous system active. Awaiting input...")
    print(f"[Lumi] VAD Threshold={Config.VAD_THRESHOLD}, RMS Gate={Config.RMS_ENERGY_GATE}, Min Chunks={Config.MIN_SPEECH_CHUNKS}")
    
    chunk_size = 512 
    audio_queue = asyncio.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[Audio Status Error]: {status}")
        loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())

    loop = asyncio.get_running_loop()
    stream = sd.InputStream(
        samplerate=Config.SAMPLE_RATE, 
        channels=1, 
        dtype='int16', 
        blocksize=chunk_size, 
        callback=audio_callback
    )

    # Initialize engines AFTER the event loop is running
    stt_engine = HybridSTT()
    llm_engine = HybridLLM()
    tts_engine = HybridTTS()
    vad_detector = VoiceActivityDetector()

    with stream:
        recording = False
        audio_buffer = []
        speech_chunk_count = 0  # Track how many chunks of actual speech we've recorded
        processing = False       # Prevent re-entry while pipeline is running

        while True:
            data = await audio_queue.get()
            flat_data = data.flatten()

            # GATE 1: Raw energy check — skip near-silent chunks entirely
            rms = VoiceActivityDetector.rms_energy(flat_data)

            # If we are currently processing an LLM response, skip all VAD
            if processing:
                continue
            
            # Process chunk through Silero VAD
            speech_dict = vad_detector.iterator(flat_data)
            
            if speech_dict:
                if "start" in speech_dict and not recording:
                    # GATE 2: Only begin recording if this chunk has real energy
                    if rms < Config.RMS_ENERGY_GATE:
                        print(f"[VAD] Ignoring low-energy start trigger (RMS={rms:.0f})")
                        vad_detector.reset()
                        continue
                    
                    print(f"\n[Lumi] VAD: Speech Started (RMS={rms:.0f})")
                    recording = True
                    audio_buffer = []
                    speech_chunk_count = 0
                    # NOTE: Do NOT reset VAD here — it needs its state to detect end-of-speech
                    await send_ui_state("listening")
                
                elif "end" in speech_dict and recording:
                    recording = False
                    
                    # GATE 3: If total speech was too short, it was likely a click or cough
                    if speech_chunk_count < Config.MIN_SPEECH_CHUNKS:
                        print(f"[VAD] Discarding short utterance ({speech_chunk_count} chunks, need {Config.MIN_SPEECH_CHUNKS})")
                        vad_detector.reset()
                        await send_ui_state("idle")
                        audio_buffer = []
                        continue
                    
                    print(f"[Lumi] VAD: Speech Ended ({speech_chunk_count} chunks)")
                    processing = True
                    await send_ui_state("thinking")
                    
                    raw_pcm = b"".join(audio_buffer)
                    wav_bytes = pcm_to_wav(raw_pcm)
                    
                    try:
                        # 1. Transcribe speech to text
                        transcript = await asyncio.to_thread(stt_engine.transcribe, wav_bytes)
                        print(f'[User Command]: "{transcript}"')
                        
                        # GATE 4: Filter Whisper hallucinations
                        if transcript.lower().strip() in WHISPER_HALLUCINATIONS:
                            print(f"[STT] Filtered hallucination: '{transcript}'")
                            await send_ui_state("idle")
                            audio_buffer = []
                            processing = False
                            vad_detector.reset()
                            continue
                        
                        if transcript:
                            # 2. Process through LLM Brain
                            response_text = await asyncio.to_thread(llm_engine.generate_response, transcript)
                            print(f'[Lumi Brain]: "{response_text}"')
                            
                            # 3. Speak response using TTS engine
                            await send_ui_state("speaking")
                            await asyncio.to_thread(tts_engine.speak, response_text)
                        
                    except Exception as e:
                        print(f"[Pipeline Error]: {type(e).__name__}: {e}")
                        traceback.print_exc()
                        # Don't show error UI for transient issues — just go back to idle
                    
                    await send_ui_state("idle")
                    audio_buffer = []
                    processing = False
                    vad_detector.reset()
            
            # Cache audio frames while recording
            if recording:
                # Only count chunks with meaningful energy toward the minimum
                if rms > Config.RMS_ENERGY_GATE * 0.5:
                    speech_chunk_count += 1
                audio_buffer.append(flat_data.tobytes())

async def websocket_handler(websocket):
    print("[Network] Tauri Frontend interface synchronized.")
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("[Network] Tauri Frontend interface disconnected.")

async def main():
    server = await websockets.serve(websocket_handler, "localhost", 8000)
    print("[Network] WebSocket server ready on ws://localhost:8000")
    await audio_processing_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[System] Graceful shutdown executed.")
