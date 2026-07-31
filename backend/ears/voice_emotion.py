"""
ZARA Voice Emotion Analyzer
Detects emotional state from voice characteristics like pitch,
tone, speaking rate, volume patterns, and prosody.
"""
import logging
import threading
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from enum import Enum

logger = logging.getLogger("ZARA_VOICE_EMO")


class VoiceEmotion(Enum):
    """Emotions detectable from voice."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    TIRED = "tired"
    STRESSED = "stressed"
    CALM = "calm"
    LOVING = "loving"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    BORED = "bored"


class SpeakingStyle(Enum):
    """Speaking style patterns."""
    MONOTONE = "monotone"
    ANIMATED = "animated"
    WHISPER = "whisper"
    SHOUTING = "shouting"
    RUSHED = "rushed"
    SLOW = "slow"
    HESITANT = "hesitant"
    CONFIDENT = "confident"


@dataclass
class VoiceFeatures:
    """Extracted voice features from audio."""
    # Pitch features
    pitch_mean: float = 0.0        # Average pitch (Hz)
    pitch_std: float = 0.0         # Pitch variation
    pitch_range: float = 0.0       # max - min pitch
    pitch_contour: str = "flat"    # rising, falling, flat, varied
    
    # Energy/Volume features
    energy_mean: float = 0.0       # Average volume
    energy_std: float = 0.0        # Volume variation
    energy_max: float = 0.0        # Peak volume
    
    # Timing features
    speaking_rate: float = 1.0     # Words per minute (relative)
    pause_frequency: float = 0.0   # Pauses per sentence
    pause_duration: float = 0.0    # Average pause length
    
    # Spectral features
    spectral_centroid: float = 0.0 # Voice brightness
    spectral_rolloff: float = 0.0  # High frequency content
    
    # Quality features
    jitter: float = 0.0            # Pitch irregularity (stress indicator)
    shimmer: float = 0.0           # Amplitude irregularity
    hnr: float = 0.0               # Harmonics-to-noise ratio (clarity)
    
    # Derived
    duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class VoiceEmotionResult:
    """Result of voice emotion analysis."""
    primary_emotion: VoiceEmotion
    confidence: float
    secondary_emotion: Optional[VoiceEmotion] = None
    speaking_style: SpeakingStyle = SpeakingStyle.ANIMATED
    intensity: float = 0.5  # How strong the emotion
    valence: float = 0.5    # Positive (1) vs Negative (0)
    arousal: float = 0.5    # High energy (1) vs Low energy (0)
    indicators: List[str] = field(default_factory=list)


class VoiceEmotionAnalyzer:
    """
    Analyzes voice to detect emotional state.
    
    Works by extracting acoustic features and mapping them
    to emotional states using prosodic analysis.
    
    Features analyzed:
    - Pitch (fundamental frequency) patterns
    - Speaking rate and pauses
    - Volume/energy patterns  
    - Voice quality (jitter, shimmer, breathiness)
    - Spectral characteristics
    """
    
    def __init__(self):
        self.feature_history: deque = deque(maxlen=50)
        self.emotion_history: deque = deque(maxlen=30)
        
        # Baseline (calibrates to user over time)
        self.baseline_pitch = 150.0  # Default, will adapt
        self.baseline_energy = 0.5
        self.baseline_rate = 1.0
        self.calibration_samples = 0
        
        # Lazy load audio libraries
        self._librosa = None
        self._numpy = None
        self._available = None
        
        self.lock = threading.Lock()
        
        logger.info("🎤 Voice Emotion Analyzer initialized")

    def _load_libraries(self) -> bool:
        """Lazy load audio processing libraries."""
        if self._available is not None:
            return self._available
        
        try:
            import numpy as np
            self._numpy = np
            
            try:
                import librosa
                self._librosa = librosa
                self._available = True
                logger.info("Audio analysis libraries loaded")
            except ImportError:
                self._available = False
                logger.warning("librosa not available - using feature-based analysis")
        except ImportError:
            self._available = False
            logger.warning("numpy not available - using basic analysis")
        
        return self._available

    def analyze_audio(self, audio_data, sample_rate: int = 16000) -> VoiceEmotionResult:
        """
        Analyze audio data to detect emotion.
        
        Args:
            audio_data: Audio samples (numpy array or list)
            sample_rate: Sample rate in Hz
        
        Returns:
            VoiceEmotionResult with detected emotion
        """
        if not self._load_libraries():
            return self._basic_analysis({})
        
        try:
            np = self._numpy
            librosa = self._librosa
            
            # Ensure numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)
            
            # Extract features
            features = self._extract_features(audio_data, sample_rate)
            
            # Analyze emotion
            result = self._analyze_features(features)
            
            # Update history
            with self.lock:
                self.feature_history.append(features)
                self.emotion_history.append(result)
            
            # Update baseline
            self._update_baseline(features)
            
            return result
            
        except Exception as e:
            logger.error(f"Audio analysis error: {e}")
            return self._basic_analysis({})

    def _extract_features(self, audio: 'np.ndarray', sr: int) -> VoiceFeatures:
        """Extract acoustic features from audio."""
        np = self._numpy
        librosa = self._librosa
        
        features = VoiceFeatures()
        features.duration_seconds = len(audio) / sr
        
        try:
            # Pitch extraction
            f0, voiced_flag, _ = librosa.pyin(
                audio, fmin=50, fmax=500, sr=sr
            )
            
            if f0 is not None:
                f0_valid = f0[~np.isnan(f0)]
                if len(f0_valid) > 0:
                    features.pitch_mean = float(np.mean(f0_valid))
                    features.pitch_std = float(np.std(f0_valid))
                    features.pitch_range = float(np.max(f0_valid) - np.min(f0_valid))
                    
                    # Pitch contour
                    if len(f0_valid) > 10:
                        first_half = np.mean(f0_valid[:len(f0_valid)//2])
                        second_half = np.mean(f0_valid[len(f0_valid)//2:])
                        
                        if second_half > first_half * 1.1:
                            features.pitch_contour = "rising"
                        elif second_half < first_half * 0.9:
                            features.pitch_contour = "falling"
                        elif features.pitch_std > 30:
                            features.pitch_contour = "varied"
                        else:
                            features.pitch_contour = "flat"
        except:
            pass
        
        try:
            # Energy (RMS)
            rms = librosa.feature.rms(y=audio)[0]
            features.energy_mean = float(np.mean(rms))
            features.energy_std = float(np.std(rms))
            features.energy_max = float(np.max(rms))
        except:
            pass
        
        try:
            # Speaking rate estimation (from energy envelope)
            onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
            features.speaking_rate = float(tempo[0]) / 100  # Normalize around 1.0
        except:
            pass
        
        try:
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            features.spectral_centroid = float(np.mean(spectral_centroids))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            features.spectral_rolloff = float(np.mean(spectral_rolloff))
        except:
            pass
        
        try:
            # Pause detection (silence ratio)
            non_silent = librosa.effects.split(audio, top_db=30)
            if len(non_silent) > 0:
                total_speech = sum(end - start for start, end in non_silent)
                speech_ratio = total_speech / len(audio)
                features.pause_frequency = len(non_silent) / features.duration_seconds
                features.pause_duration = (1 - speech_ratio) / max(1, len(non_silent))
        except:
            pass
        
        return features

    def _analyze_features(self, features: VoiceFeatures) -> VoiceEmotionResult:
        """Map acoustic features to emotions."""
        indicators = []
        
        # Calculate relative values (compared to baseline)
        pitch_rel = features.pitch_mean / max(1, self.baseline_pitch)
        energy_rel = features.energy_mean / max(0.001, self.baseline_energy)
        rate_rel = features.speaking_rate / max(0.1, self.baseline_rate)
        
        # Arousal (energy level)
        arousal = 0.5
        if energy_rel > 1.2 or rate_rel > 1.2:
            arousal = min(1.0, 0.5 + (energy_rel - 1) * 0.3 + (rate_rel - 1) * 0.2)
            indicators.append("high energy")
        elif energy_rel < 0.8 or rate_rel < 0.8:
            arousal = max(0.0, 0.5 - (1 - energy_rel) * 0.3 - (1 - rate_rel) * 0.2)
            indicators.append("low energy")
        
        # Valence (positive/negative)
        valence = 0.5
        if features.pitch_contour == "rising" and pitch_rel > 1.0:
            valence = min(1.0, valence + 0.2)
            indicators.append("rising pitch")
        elif features.pitch_contour == "falling" and pitch_rel < 1.0:
            valence = max(0.0, valence - 0.2)
            indicators.append("falling pitch")
        
        if features.pitch_std > 40:
            valence = min(1.0, valence + 0.1)  # Animated = more positive
            indicators.append("animated voice")
        
        # Speaking style
        style = SpeakingStyle.ANIMATED
        if features.pitch_std < 15:
            style = SpeakingStyle.MONOTONE
            indicators.append("monotone")
        if rate_rel > 1.4:
            style = SpeakingStyle.RUSHED
            indicators.append("rushed speech")
        elif rate_rel < 0.6:
            style = SpeakingStyle.SLOW
            indicators.append("slow speech")
        if energy_rel > 1.5:
            style = SpeakingStyle.SHOUTING
        elif energy_rel < 0.4:
            style = SpeakingStyle.WHISPER
            indicators.append("quiet voice")
        if features.pause_frequency > 0.5:
            style = SpeakingStyle.HESITANT
            indicators.append("hesitant")
        
        # Map to primary emotion
        emotion, secondary, confidence = self._map_to_emotion(
            arousal, valence, style, features, indicators
        )
        
        return VoiceEmotionResult(
            primary_emotion=emotion,
            confidence=confidence,
            secondary_emotion=secondary,
            speaking_style=style,
            intensity=arousal,
            valence=valence,
            arousal=arousal,
            indicators=indicators
        )

    def _map_to_emotion(self, arousal: float, valence: float,
                       style: SpeakingStyle, features: VoiceFeatures,
                       indicators: List[str]) -> Tuple[VoiceEmotion, Optional[VoiceEmotion], float]:
        """Map dimensional values to categorical emotions."""
        
        # High arousal, high valence = excited, happy
        if arousal > 0.7 and valence > 0.6:
            if style == SpeakingStyle.RUSHED:
                return VoiceEmotion.EXCITED, VoiceEmotion.HAPPY, 0.8
            return VoiceEmotion.HAPPY, VoiceEmotion.EXCITED, 0.75
        
        # High arousal, low valence = angry, stressed, frustrated
        if arousal > 0.7 and valence < 0.4:
            if style == SpeakingStyle.SHOUTING:
                return VoiceEmotion.ANGRY, VoiceEmotion.FRUSTRATED, 0.85
            return VoiceEmotion.STRESSED, VoiceEmotion.FRUSTRATED, 0.7
        
        # Low arousal, low valence = sad, tired
        if arousal < 0.4 and valence < 0.4:
            if style == SpeakingStyle.SLOW:
                return VoiceEmotion.SAD, VoiceEmotion.TIRED, 0.75
            if style == SpeakingStyle.MONOTONE:
                return VoiceEmotion.TIRED, VoiceEmotion.BORED, 0.7
            return VoiceEmotion.SAD, None, 0.65
        
        # Low arousal, high valence = calm, loving
        if arousal < 0.4 and valence > 0.6:
            if features.pitch_mean < self.baseline_pitch * 0.9:
                return VoiceEmotion.LOVING, VoiceEmotion.CALM, 0.7
            return VoiceEmotion.CALM, None, 0.65
        
        # Medium arousal, low valence = frustrated, confused
        if 0.4 <= arousal <= 0.6 and valence < 0.4:
            if style == SpeakingStyle.HESITANT:
                return VoiceEmotion.CONFUSED, VoiceEmotion.FRUSTRATED, 0.65
            return VoiceEmotion.FRUSTRATED, None, 0.6
        
        # Surprised = sudden high pitch
        if features.pitch_range > 100 and features.pitch_contour == "rising":
            return VoiceEmotion.SURPRISED, None, 0.7
        
        # Bored = monotone, slow
        if style == SpeakingStyle.MONOTONE and arousal < 0.5:
            return VoiceEmotion.BORED, VoiceEmotion.TIRED, 0.6
        
        return VoiceEmotion.NEUTRAL, None, 0.5

    def _update_baseline(self, features: VoiceFeatures):
        """Update baseline values for this user."""
        self.calibration_samples += 1
        
        # Running average (weighted towards recent)
        alpha = 0.1 if self.calibration_samples > 10 else 0.3
        
        if features.pitch_mean > 0:
            self.baseline_pitch = (
                self.baseline_pitch * (1 - alpha) + 
                features.pitch_mean * alpha
            )
        
        if features.energy_mean > 0:
            self.baseline_energy = (
                self.baseline_energy * (1 - alpha) + 
                features.energy_mean * alpha
            )
        
        if features.speaking_rate > 0:
            self.baseline_rate = (
                self.baseline_rate * (1 - alpha) + 
                features.speaking_rate * alpha
            )

    def analyze_from_features(self, speaking_rate: float = 1.0,
                            volume: float = 0.5,
                            pitch_variation: float = 0.5,
                            pitch_level: float = 0.5) -> VoiceEmotionResult:
        """
        Analyze emotion from pre-extracted features.
        Use when raw audio isn't available but features are.
        
        All values are relative (0-1 or centered on 1.0 for rate).
        """
        # Create synthetic features
        features = VoiceFeatures()
        features.pitch_mean = pitch_level * 300  # Approximate
        features.pitch_std = pitch_variation * 80
        features.energy_mean = volume
        features.speaking_rate = speaking_rate
        
        if pitch_variation > 0.6:
            features.pitch_contour = "varied"
        elif pitch_level > 0.6:
            features.pitch_contour = "rising"
        elif pitch_level < 0.4:
            features.pitch_contour = "falling"
        
        return self._analyze_features(features)

    def _basic_analysis(self, metadata: Dict) -> VoiceEmotionResult:
        """Fallback analysis without audio libraries."""
        return VoiceEmotionResult(
            primary_emotion=VoiceEmotion.NEUTRAL,
            confidence=0.3,
            speaking_style=SpeakingStyle.ANIMATED,
            intensity=0.5,
            valence=0.5,
            arousal=0.5,
            indicators=["basic_analysis_fallback"]
        )

    def get_emotional_trend(self, window: int = 10) -> Dict:
        """Get emotional trend over recent history."""
        with self.lock:
            recent = list(self.emotion_history)[-window:]
        
        if not recent:
            return {"trend": "unknown", "dominant": "neutral"}
        
        # Count emotions
        from collections import Counter
        emotions = Counter(r.primary_emotion for r in recent)
        dominant = emotions.most_common(1)[0][0]
        
        # Calculate trends
        if len(recent) >= 3:
            early = sum(r.arousal for r in recent[:len(recent)//2]) / (len(recent)//2)
            late = sum(r.arousal for r in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
            
            if late > early * 1.2:
                trend = "increasing_energy"
            elif late < early * 0.8:
                trend = "decreasing_energy"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "dominant": dominant.value,
            "samples": len(recent),
            "avg_arousal": sum(r.arousal for r in recent) / len(recent),
            "avg_valence": sum(r.valence for r in recent) / len(recent)
        }

    def get_status(self) -> Dict:
        """Get analyzer status."""
        return {
            "history_size": len(self.emotion_history),
            "calibration_samples": self.calibration_samples,
            "baseline_pitch": self.baseline_pitch,
            "baseline_energy": self.baseline_energy,
            "libraries_available": self._available
        }


# Singleton
_voice_analyzer = None

def get_voice_analyzer() -> VoiceEmotionAnalyzer:
    """Get the global voice emotion analyzer."""
    global _voice_analyzer
    if _voice_analyzer is None:
        _voice_analyzer = VoiceEmotionAnalyzer()
    return _voice_analyzer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = VoiceEmotionAnalyzer()
    
    # Test with features
    result = analyzer.analyze_from_features(
        speaking_rate=1.4,  # Fast
        volume=0.7,         # Loud
        pitch_variation=0.8 # Animated
    )
    
    print(f"Emotion: {result.primary_emotion.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Style: {result.speaking_style.value}")
    print(f"Indicators: {result.indicators}")
