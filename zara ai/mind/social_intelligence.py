"""
ZARA Social Intelligence v1.0
==============================
Read Social Dynamics, Detect Sarcasm, Understand Subtext

This is ZARA's social perception layer that enables:
1. SARCASM DETECTION - Identify when words mean the opposite
2. SENTIMENT DEPTH - Beyond positive/negative to nuanced emotions
3. SUBTEXT READING - Understand what's implied but not said
4. INTENT ANALYSIS - What does the speaker really want?
5. SOCIAL DYNAMICS - Power dynamics, relationship cues
6. TONE ANALYSIS - Formal, casual, hostile, friendly, etc.
7. CULTURAL CONTEXT - Idioms, references, cultural nuance

This is REAL NLU, not scripted pattern matching.
"""

import logging
import json
import time
import re
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, deque
import hashlib

# Ensure parent in path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("ZARA_SOCIAL")


# ═══════════════════════════════════════════════════════════════════════════
# SOCIAL INTELLIGENCE STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class SarcasmType(Enum):
    """Types of sarcasm."""
    NONE = "none"
    VERBAL_IRONY = "verbal_irony"           # Saying opposite of meaning
    SITUATIONAL = "situational"              # Outcome opposite of expected
    SELF_DEPRECATING = "self_deprecating"    # Mocking oneself
    DEADPAN = "deadpan"                      # Dry, without obvious cues
    HYPERBOLIC = "hyperbolic"                # Exaggerated for effect


class Tone(Enum):
    """Communication tones."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    FORMAL = "formal"
    CASUAL = "casual"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    SARCASTIC = "sarcastic"
    PASSIVE_AGGRESSIVE = "passive_aggressive"
    ENTHUSIASTIC = "enthusiastic"
    FRUSTRATED = "frustrated"
    APOLOGETIC = "apologetic"
    CONDESCENDING = "condescending"


class Intent(Enum):
    """Speaker intents."""
    INFORM = "inform"
    REQUEST = "request"
    COMMAND = "command"
    QUESTION = "question"
    VENT = "vent"
    SEEK_VALIDATION = "seek_validation"
    COMPLAIN = "complain"
    JOKE = "joke"
    FLIRT = "flirt"
    THREATEN = "threaten"
    APOLOGIZE = "apologize"
    THANK = "thank"
    GREET = "greet"
    FAREWELL = "farewell"
    SMALL_TALK = "small_talk"
    NEGOTIATE = "negotiate"
    PERSUADE = "persuade"


class RelationshipDynamic(Enum):
    """Social relationship dynamics."""
    EQUAL = "equal"
    SUPERIOR = "superior"         # Speaker is in higher position
    SUBORDINATE = "subordinate"   # Speaker is in lower position
    INTIMATE = "intimate"         # Close relationship
    PROFESSIONAL = "professional"
    ADVERSARIAL = "adversarial"
    SUPPORTIVE = "supportive"


@dataclass
class SentimentProfile:
    """Deep sentiment analysis."""
    # Basic
    polarity: float          # -1 to +1
    intensity: float         # 0 to 1
    
    # Emotional components
    joy: float
    sadness: float
    anger: float
    fear: float
    surprise: float
    disgust: float
    trust: float
    anticipation: float
    
    # Meta
    mixed: bool              # Multiple conflicting emotions
    genuine: bool            # Appears authentic
    performative: bool       # Put on for audience


@dataclass
class Subtext:
    """What's implied but not explicitly said."""
    id: str
    surface_meaning: str
    implied_meaning: str
    confidence: float
    reasoning: str
    cultural_context: Optional[str]


@dataclass
class SocialReading:
    """Complete social intelligence analysis of an utterance."""
    # Raw input
    text: str
    timestamp: float
    
    # Sarcasm
    is_sarcastic: bool
    sarcasm_type: SarcasmType
    sarcasm_confidence: float
    literal_meaning: str
    intended_meaning: str
    
    # Tone
    primary_tone: Tone
    secondary_tones: List[Tone]
    tone_confidence: float
    
    # Intent
    primary_intent: Intent
    secondary_intents: List[Intent]
    intent_confidence: float
    
    # Sentiment
    sentiment: SentimentProfile
    
    # Social dynamics
    relationship_dynamic: RelationshipDynamic
    power_level: float         # -1 (subordinate) to +1 (dominant)
    
    # Subtext
    subtexts: List[Subtext]
    has_hidden_meaning: bool
    
    # Context
    references_understood: List[str]
    cultural_elements: List[str]
    
    # Response guidance
    recommended_tone: Tone
    warning_flags: List[str]


# ═══════════════════════════════════════════════════════════════════════════
# SARCASM DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class SarcasmDetector:
    """
    Detects sarcasm using multiple signals:
    - Linguistic markers (yeah right, oh sure, totally, etc.)
    - Sentiment-content mismatch
    - Hyperbolic expressions
    - Context incongruity
    - Punctuation patterns
    """
    
    # Known sarcasm markers
    SARCASM_MARKERS = [
        "yeah right", "oh sure", "oh great", "wow thanks", "shocking",
        "what a surprise", "how wonderful", "so glad", "totally",
        "absolutely", "clearly", "obviously", "of course", "naturally",
        "no way", "as if", "sure thing", "right...", "uhuh", "yay",
        "thanks a lot", "just great", "perfect", "fantastic", "brilliant"
    ]
    
    # Hyperbolic patterns suggesting sarcasm
    HYPERBOLE_PATTERNS = [
        r"the best\s+\w+\s+ever",
        r"never seen anything (like|so)",
        r"absolutely (nothing|no one|never)",
        r"literally (dying|dead|can't)",
        r"(everyone|nobody) (knows|thinks)",
        r"(always|never) happens"
    ]
    
    # Punctuation patterns
    SARCASM_PUNCTUATION = [
        "...", "!!!!", "????", "???!!", "~"
    ]
    
    def __init__(self):
        self._llm = None
        self.detection_cache: Dict[str, Tuple[bool, float]] = {}
    
    def _get_llm(self):
        """Lazy load LLM for complex detection."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable for sarcasm detection: {e}")
        return self._llm
    
    def detect(self, text: str, context: str = "") -> Tuple[bool, SarcasmType, float, str, str]:
        """
        Detect sarcasm in text.
        
        Returns:
            (is_sarcastic, type, confidence, literal_meaning, intended_meaning)
        """
        text_lower = text.lower().strip()
        
        # Quick cache check
        cache_key = hashlib.md5(text_lower.encode()).hexdigest()
        if cache_key in self.detection_cache:
            cached = self.detection_cache[cache_key]
            if cached[0]:  # is sarcastic
                return (True, SarcasmType.VERBAL_IRONY, cached[1], 
                       text, f"Opposite of: {text}")
            return (False, SarcasmType.NONE, cached[1], text, text)
        
        # Score-based detection
        sarcasm_score = 0.0
        sarcasm_signals = []
        
        # Check for sarcasm markers
        for marker in self.SARCASM_MARKERS:
            if marker in text_lower:
                sarcasm_score += 0.3
                sarcasm_signals.append(f"marker: {marker}")
                break
        
        # Check hyperbole patterns
        for pattern in self.HYPERBOLE_PATTERNS:
            if re.search(pattern, text_lower):
                sarcasm_score += 0.2
                sarcasm_signals.append(f"hyperbole: {pattern}")
                break
        
        # Check punctuation
        for punct in self.SARCASM_PUNCTUATION:
            if punct in text:
                sarcasm_score += 0.1
                sarcasm_signals.append(f"punctuation: {punct}")
        
        # Check for positive words with negative context indicators
        positive_words = ["great", "wonderful", "fantastic", "amazing", "love", "perfect"]
        negative_context = ["thanks for", "so glad", "just what", "exactly what", "really needed"]
        
        has_positive = any(w in text_lower for w in positive_words)
        has_neg_context = any(n in text_lower for n in negative_context)
        
        if has_positive and has_neg_context:
            sarcasm_score += 0.25
            sarcasm_signals.append("positive-in-negative-context")
        
        # Quotation marks around normally positive words
        quote_pattern = r'["\'](great|wonderful|fantastic|amazing|love|perfect)["\']'
        if re.search(quote_pattern, text_lower):
            sarcasm_score += 0.3
            sarcasm_signals.append("air-quotes")
        
        # Use LLM for complex cases
        llm = self._get_llm()
        if llm and sarcasm_score > 0.1 and sarcasm_score < 0.6:
            try:
                prompt = f"""Analyze this text for sarcasm. Answer with JSON only.

Text: "{text}"
Context: {context or "No additional context"}

Is this sarcastic? If yes, what does the speaker really mean?

Return ONLY JSON:
{{"is_sarcastic": true/false, "confidence": 0.0-1.0, "intended_meaning": "what they really mean"}}"""

                response = llm.think(prompt)
                
                # Parse response
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{[^}]+\}', response)
                    if json_match:
                        data = json.loads(json_match.group())
                        if data.get("is_sarcastic"):
                            sarcasm_score = max(sarcasm_score, data.get("confidence", 0.7))
                            intended = data.get("intended_meaning", f"Opposite of: {text}")
                            
                            self.detection_cache[cache_key] = (True, sarcasm_score)
                            return (True, SarcasmType.VERBAL_IRONY, sarcasm_score, 
                                   text, intended)
                except json.JSONDecodeError:
                    pass
                    
            except Exception as e:
                logger.debug(f"LLM sarcasm detection error: {e}")
        
        # Determine final result
        is_sarcastic = sarcasm_score >= 0.4
        sarcasm_type = SarcasmType.VERBAL_IRONY if is_sarcastic else SarcasmType.NONE
        
        # Cache result
        self.detection_cache[cache_key] = (is_sarcastic, sarcasm_score)
        
        if is_sarcastic:
            intended = self._infer_intended_meaning(text)
            return (True, sarcasm_type, sarcasm_score, text, intended)
        
        return (False, SarcasmType.NONE, 1.0 - sarcasm_score, text, text)
    
    def _infer_intended_meaning(self, text: str) -> str:
        """Infer what a sarcastic statement really means."""
        text_lower = text.lower()
        
        # Simple inversions
        inversions = {
            "great": "terrible",
            "wonderful": "awful",
            "fantastic": "horrible",
            "amazing": "disappointing",
            "love": "hate",
            "perfect": "completely wrong",
            "thanks": "no thanks",
            "glad": "upset",
            "helpful": "useless"
        }
        
        meaning = text
        for pos, neg in inversions.items():
            if pos in text_lower:
                meaning = meaning.replace(pos, neg).replace(pos.title(), neg.title())
        
        if meaning == text:
            return f"The opposite of: {text}"
        
        return meaning


# ═══════════════════════════════════════════════════════════════════════════
# TONE ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class ToneAnalyzer:
    """
    Analyzes the tone of communication.
    Goes beyond sentiment to capture communication style.
    """
    
    # Tone word patterns
    TONE_PATTERNS = {
        Tone.HOSTILE: {
            "words": ["stupid", "idiot", "hate", "worst", "terrible", "awful", "disgusting", 
                     "pathetic", "useless", "garbage", "trash", "moron"],
            "patterns": [r"what the (hell|heck|f)", r"are you (kidding|serious)", 
                        r"how (dare|could) you"]
        },
        Tone.FRIENDLY: {
            "words": ["friend", "buddy", "love", "appreciate", "thanks", "grateful",
                     "amazing", "wonderful", "great", "awesome", "help", "together"],
            "patterns": [r"(hey|hi) (there|friend|buddy)", r"hope you('re| are)", 
                        r"looking forward"]
        },
        Tone.FORMAL: {
            "words": ["sincerely", "regards", "hereby", "pursuant", "accordingly",
                     "therefore", "moreover", "furthermore", "henceforth"],
            "patterns": [r"(dear|respected) (sir|madam|mr|ms)", r"i (would|shall) like to",
                        r"please (find|note|be advised)"]
        },
        Tone.CASUAL: {
            "words": ["hey", "yo", "gonna", "wanna", "kinda", "sorta", "yeah",
                     "nah", "cool", "chill", "dude", "bro", "lol", "haha"],
            "patterns": [r"\b(u|ur|r)\b", r"(btw|tbh|imo|lmao|rofl)"]
        },
        Tone.PASSIVE_AGGRESSIVE: {
            "words": ["fine", "whatever", "sure", "thanks anyway", "nevermind",
                     "forget it", "if you say so"],
            "patterns": [r"i (guess|suppose)", r"no worries( i guess)?", 
                        r"it('s| is) fine(.+really)?"]
        },
        Tone.FRUSTRATED: {
            "words": ["frustrated", "annoyed", "angry", "tired", "sick of",
                     "enough", "stop", "again", "always"],
            "patterns": [r"(how|why) (many|much) times", r"i('ve| have) (already|told you)",
                        r"this is (the last|ridiculous)"]
        },
        Tone.ENTHUSIASTIC: {
            "words": ["excited", "thrilled", "amazing", "incredible", "fantastic",
                     "awesome", "love", "can't wait", "yes"],
            "patterns": [r"!+", r"(so|really|super) (excited|happy|thrilled)",
                        r"this is (amazing|incredible|awesome)"]
        },
        Tone.APOLOGETIC: {
            "words": ["sorry", "apologize", "apologies", "forgive", "regret",
                     "my bad", "mistake", "fault", "shouldn't have"],
            "patterns": [r"i('m| am) (so |really |truly )?sorry", r"please forgive",
                        r"i (didn't|should have|shouldn't have)"]
        },
        Tone.CONDESCENDING: {
            "words": ["obviously", "clearly", "actually", "sweetie", "honey",
                     "dear", "simple", "easy", "basic"],
            "patterns": [r"as (i|we|everyone) know", r"it('s| is) (not that|quite) (hard|simple)",
                        r"let me explain", r"you (just|simply) need to"]
        }
    }
    
    def __init__(self):
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable: {e}")
        return self._llm
    
    def analyze(self, text: str, is_sarcastic: bool = False) -> Tuple[Tone, List[Tone], float]:
        """
        Analyze the tone of text.
        
        Returns:
            (primary_tone, secondary_tones, confidence)
        """
        text_lower = text.lower()
        tone_scores: Dict[Tone, float] = {tone: 0.0 for tone in Tone}
        
        # Score each tone based on patterns
        for tone, patterns in self.TONE_PATTERNS.items():
            # Word matching
            for word in patterns["words"]:
                if word in text_lower:
                    tone_scores[tone] += 0.2
            
            # Pattern matching
            for pattern in patterns["patterns"]:
                if re.search(pattern, text_lower):
                    tone_scores[tone] += 0.3
        
        # Adjust for sarcasm
        if is_sarcastic:
            tone_scores[Tone.SARCASTIC] += 0.5
            # Sarcasm often masks frustration or passive-aggression
            tone_scores[Tone.FRUSTRATED] += 0.2
            tone_scores[Tone.PASSIVE_AGGRESSIVE] += 0.2
        
        # Punctuation analysis
        if text.count("!") >= 2:
            tone_scores[Tone.ENTHUSIASTIC] += 0.2
            tone_scores[Tone.HOSTILE] += 0.1  # Could be angry
        
        if text.count("?") >= 2:
            tone_scores[Tone.FRUSTRATED] += 0.1
        
        # All caps detection
        words = text.split()
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 1) / max(len(words), 1)
        if caps_ratio > 0.3:
            tone_scores[Tone.HOSTILE] += 0.3
            tone_scores[Tone.ENTHUSIASTIC] += 0.2
        
        # Get top tones
        sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_tones[0][0] if sorted_tones[0][1] > 0 else Tone.NEUTRAL
        primary_score = sorted_tones[0][1]
        
        # Secondary tones (those with significant scores)
        secondary = [t for t, s in sorted_tones[1:4] if s > 0.2]
        
        # Confidence based on score magnitude and separation
        if primary_score > 0.5:
            confidence = min(0.95, 0.6 + primary_score * 0.3)
        elif primary_score > 0.2:
            confidence = 0.5 + primary_score
        else:
            confidence = 0.4
            primary = Tone.NEUTRAL
        
        return primary, secondary, confidence


# ═══════════════════════════════════════════════════════════════════════════
# INTENT ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class IntentAnalyzer:
    """
    Analyzes speaker intent - what do they really want?
    """
    
    INTENT_PATTERNS = {
        Intent.QUESTION: {
            "patterns": [r"^(what|who|where|when|why|how|is|are|do|does|can|could|would|will|should)\b",
                        r"\?$", r"^(tell me|explain|describe)"],
            "weight": 0.4
        },
        Intent.REQUEST: {
            "patterns": [r"^(please|could you|would you|can you|i (need|want|would like))",
                        r"(help me|assist me|show me)", r"i('d| would) (like|appreciate)"],
            "weight": 0.35
        },
        Intent.COMMAND: {
            "patterns": [r"^(do|don't|stop|go|make|get|put|take|give|tell|show|open|close|run|start)",
                        r"^(you (must|need to|have to|should))"],
            "weight": 0.35
        },
        Intent.VENT: {
            "patterns": [r"i('m| am) (so |really )?(frustrated|angry|upset|tired|sick)",
                        r"(hate|can't stand|so annoying|drives me crazy)"],
            "weight": 0.4
        },
        Intent.SEEK_VALIDATION: {
            "patterns": [r"(right|correct|don't you think|isn't it|am i wrong|you know)\?*$",
                        r"^(i think|i believe|in my opinion)"],
            "weight": 0.3
        },
        Intent.COMPLAIN: {
            "patterns": [r"(doesn't work|broken|terrible|worst|awful|never works)",
                        r"(always|never|every time)", r"(why (can't|won't|doesn't))"],
            "weight": 0.35
        },
        Intent.JOKE: {
            "patterns": [r"(lol|haha|😂|🤣|jk|just kidding|joking)",
                        r"(walks into a bar|knock knock|why did the)"],
            "weight": 0.4
        },
        Intent.THANK: {
            "patterns": [r"^(thank|thanks|thx|ty|appreciated|grateful)",
                        r"(you('re| are) (the best|amazing|awesome))"],
            "weight": 0.5
        },
        Intent.APOLOGIZE: {
            "patterns": [r"^(sorry|apologies|i apologize|my bad|my fault)",
                        r"(forgive me|excuse me|pardon)"],
            "weight": 0.5
        },
        Intent.GREET: {
            "patterns": [r"^(hi|hello|hey|good (morning|afternoon|evening)|howdy|sup|yo)",
                        r"^(how are you|how('s| is) it going|what('s| is) up)"],
            "weight": 0.6
        },
        Intent.FAREWELL: {
            "patterns": [r"^(bye|goodbye|see you|later|take care|good night|gotta go)",
                        r"(talk (later|soon|tomorrow)|catch you later)"],
            "weight": 0.6
        },
        Intent.SMALL_TALK: {
            "patterns": [r"(weather|weekend|plans|doing anything|been up to)",
                        r"(nice day|beautiful outside|crazy weather)"],
            "weight": 0.3
        },
        Intent.INFORM: {
            "patterns": [r"(fyi|just so you know|heads up|wanted to (let you know|tell you))",
                        r"(did you know|fun fact|actually)"],
            "weight": 0.3
        }
    }
    
    def __init__(self):
        self._llm = None
    
    def analyze(self, text: str, tone: Tone = Tone.NEUTRAL) -> Tuple[Intent, List[Intent], float]:
        """
        Analyze speaker intent.
        
        Returns:
            (primary_intent, secondary_intents, confidence)
        """
        text_lower = text.lower().strip()
        intent_scores: Dict[Intent, float] = {intent: 0.0 for intent in Intent}
        
        # Pattern matching
        for intent, config in self.INTENT_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower):
                    intent_scores[intent] += config["weight"]
        
        # Adjust based on tone
        if tone == Tone.FRUSTRATED:
            intent_scores[Intent.VENT] += 0.3
            intent_scores[Intent.COMPLAIN] += 0.2
        elif tone == Tone.APOLOGETIC:
            intent_scores[Intent.APOLOGIZE] += 0.3
        elif tone == Tone.ENTHUSIASTIC:
            intent_scores[Intent.THANK] += 0.1
        
        # Sort and return
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_intents[0][0] if sorted_intents[0][1] > 0 else Intent.INFORM
        primary_score = sorted_intents[0][1]
        
        secondary = [i for i, s in sorted_intents[1:3] if s > 0.2]
        
        confidence = min(0.95, 0.5 + primary_score * 0.4)
        
        return primary, secondary, confidence


# ═══════════════════════════════════════════════════════════════════════════
# SENTIMENT ANALYZER (DEEP)
# ═══════════════════════════════════════════════════════════════════════════

class DeepSentimentAnalyzer:
    """
    Deep sentiment analysis beyond positive/negative.
    Analyzes emotional components based on Plutchik's wheel.
    """
    
    # Emotion word lists
    EMOTION_WORDS = {
        "joy": ["happy", "joy", "delighted", "pleased", "glad", "cheerful", "elated",
               "thrilled", "excited", "ecstatic", "wonderful", "great", "love", "amazing"],
        "sadness": ["sad", "unhappy", "depressed", "down", "blue", "miserable", "gloomy",
                   "heartbroken", "disappointed", "dejected", "melancholy", "grief"],
        "anger": ["angry", "mad", "furious", "outraged", "irritated", "annoyed", "frustrated",
                 "enraged", "hostile", "bitter", "hate", "livid", "pissed"],
        "fear": ["afraid", "scared", "terrified", "anxious", "worried", "nervous", "panicked",
                "frightened", "horrified", "alarmed", "uneasy", "dread"],
        "surprise": ["surprised", "shocked", "amazed", "astonished", "startled", "stunned",
                    "unexpected", "wow", "unbelievable", "whoa"],
        "disgust": ["disgusted", "revolted", "repulsed", "gross", "sick", "nauseated",
                   "horrible", "awful", "vile", "nasty", "yuck"],
        "trust": ["trust", "believe", "rely", "faith", "confident", "assured", "secure",
                 "dependable", "honest", "loyal", "reliable"],
        "anticipation": ["expect", "anticipate", "await", "looking forward", "hope",
                        "curious", "eager", "excited about", "can't wait"]
    }
    
    def analyze(self, text: str, is_sarcastic: bool = False) -> SentimentProfile:
        """
        Perform deep sentiment analysis.
        
        Returns:
            SentimentProfile with all emotional components
        """
        text_lower = text.lower()
        
        # Calculate emotion scores
        emotion_scores = {emotion: 0.0 for emotion in self.EMOTION_WORDS}
        
        for emotion, words in self.EMOTION_WORDS.items():
            for word in words:
                if word in text_lower:
                    emotion_scores[emotion] += 0.2
                    # Check for intensifiers
                    if re.search(rf"(very|really|so|extremely|incredibly)\s+{word}", text_lower):
                        emotion_scores[emotion] += 0.15
        
        # Normalize scores (0-1)
        max_score = max(emotion_scores.values()) if any(emotion_scores.values()) else 1
        if max_score > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = min(1.0, emotion_scores[emotion] / max_score)
        
        # Calculate polarity
        positive_emotions = emotion_scores["joy"] + emotion_scores["trust"] + emotion_scores["anticipation"]
        negative_emotions = emotion_scores["sadness"] + emotion_scores["anger"] + emotion_scores["fear"] + emotion_scores["disgust"]
        
        polarity = (positive_emotions - negative_emotions) / 3
        polarity = max(-1.0, min(1.0, polarity))
        
        # Adjust for sarcasm (flip polarity)
        if is_sarcastic:
            polarity = -polarity * 0.8  # Not full flip, sarcasm has complex emotions
        
        # Calculate intensity
        intensity = max(emotion_scores.values()) if any(emotion_scores.values()) else 0.3
        
        # Punctuation affects intensity
        exclamation_count = text.count("!")
        if exclamation_count >= 2:
            intensity = min(1.0, intensity + 0.2)
        
        # Check for mixed emotions
        high_emotions = [e for e, s in emotion_scores.items() if s > 0.3]
        mixed = len(high_emotions) >= 2
        
        # Check if genuine (sarcasm = not genuine)
        genuine = not is_sarcastic
        
        # Check if performative (formal language, seems put-on)
        performative = any(w in text_lower for w in ["sincerely", "regards", "hereby", "respectfully"])
        
        return SentimentProfile(
            polarity=polarity,
            intensity=intensity,
            joy=emotion_scores["joy"],
            sadness=emotion_scores["sadness"],
            anger=emotion_scores["anger"],
            fear=emotion_scores["fear"],
            surprise=emotion_scores["surprise"],
            disgust=emotion_scores["disgust"],
            trust=emotion_scores["trust"],
            anticipation=emotion_scores["anticipation"],
            mixed=mixed,
            genuine=genuine,
            performative=performative
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUBTEXT READER
# ═══════════════════════════════════════════════════════════════════════════

class SubtextReader:
    """
    Reads between the lines - what's implied but not said.
    """
    
    # Common subtext patterns
    SUBTEXT_PATTERNS = [
        # (pattern, surface_template, implied_template)
        (r"i('m| am) fine", "Everything is okay", "Something is wrong but I don't want to talk about it"),
        (r"it('s| is) fine", "The situation is acceptable", "I'm not happy about this but accepting it"),
        (r"do what(ever)? you want", "You have freedom to choose", "I'm upset and withdrawing"),
        (r"i don('t| t) care", "I have no preference", "I'm hurt or giving up"),
        (r"we need to talk", "We should have a conversation", "There's a serious issue to address"),
        (r"i('m| am) not (mad|angry)", "I'm not upset", "I actually am upset"),
        (r"no offense,? but", "I don't mean to offend", "I'm about to say something offensive"),
        (r"with all due respect", "I respect you", "I disagree and am about to argue"),
        (r"i('ll|'d) think about it", "I'll consider it", "Probably not going to happen"),
        (r"we('ll| will) see", "The outcome is uncertain", "Likely no, but I don't want to say it"),
        (r"that('s| is) interesting", "I find this noteworthy", "I disagree or find this strange"),
        (r"i hear you", "I understand what you're saying", "I acknowledge but may not agree"),
        (r"bless (your|their) heart", "Wishing well", "You're being naive or foolish"),
        (r"must be nice", "That's fortunate for you", "I'm envious or resentful"),
        (r"i was just joking", "It was humor", "I meant it but am backtracking")
    ]
    
    def __init__(self):
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from mind.conscious_mind import ConsciousMind
                self._llm = ConsciousMind()
            except Exception as e:
                logger.debug(f"LLM unavailable: {e}")
        return self._llm
    
    def read(self, text: str, context: str = "") -> List[Subtext]:
        """
        Read subtext in the message.
        
        Returns:
            List of detected subtexts
        """
        subtexts = []
        text_lower = text.lower()
        
        # Check known patterns
        for pattern, surface, implied in self.SUBTEXT_PATTERNS:
            if re.search(pattern, text_lower):
                subtext = Subtext(
                    id=f"subtext_{hashlib.md5(pattern.encode()).hexdigest()[:8]}",
                    surface_meaning=surface,
                    implied_meaning=implied,
                    confidence=0.75,
                    reasoning=f"Pattern match: {pattern}",
                    cultural_context="Common English subtext"
                )
                subtexts.append(subtext)
        
        # Use LLM for complex subtext
        llm = self._get_llm()
        if llm and not subtexts:
            try:
                prompt = f"""Analyze this text for hidden meaning or subtext.

Text: "{text}"
Context: {context or "No additional context"}

Is there subtext (implied meaning beyond the literal words)? If yes, what?

Return ONLY JSON:
{{"has_subtext": true/false, "surface_meaning": "what is literally said", "implied_meaning": "what is really meant", "reasoning": "why you think this"}}"""

                response = llm.think(prompt)
                
                try:
                    json_match = re.search(r'\{[^}]+\}', response)
                    if json_match:
                        data = json.loads(json_match.group())
                        if data.get("has_subtext"):
                            subtext = Subtext(
                                id=f"subtext_llm_{int(time.time())}",
                                surface_meaning=data.get("surface_meaning", text),
                                implied_meaning=data.get("implied_meaning", text),
                                confidence=0.7,
                                reasoning=data.get("reasoning", "LLM analysis"),
                                cultural_context=None
                            )
                            subtexts.append(subtext)
                except json.JSONDecodeError:
                    pass
                    
            except Exception as e:
                logger.debug(f"LLM subtext reading error: {e}")
        
        return subtexts


# ═══════════════════════════════════════════════════════════════════════════
# SOCIAL DYNAMICS ANALYZER  
# ═══════════════════════════════════════════════════════════════════════════

class SocialDynamicsAnalyzer:
    """
    Analyzes social dynamics and power relationships.
    """
    
    # Power indicators
    DOMINANT_INDICATORS = [
        r"you (must|need to|have to|should|will)",
        r"i('m| am) (telling|ordering|demanding)",
        r"(do it|make sure|see to it)",
        r"^(listen|look|understand)",
        r"i (decide|say|determine)"
    ]
    
    SUBORDINATE_INDICATORS = [
        r"(please|if you (don't|wouldn't) mind)",
        r"i (was wondering|wanted to ask)",
        r"(could|would|might) you (possibly|maybe)",
        r"(sorry to (bother|ask)|excuse me)",
        r"i('m| am) (just|only)"
    ]
    
    def analyze(self, text: str, tone: Tone = Tone.NEUTRAL) -> Tuple[RelationshipDynamic, float]:
        """
        Analyze social dynamics.
        
        Returns:
            (relationship_dynamic, power_level: -1 to +1)
        """
        text_lower = text.lower()
        
        power_score = 0.0  # -1 = subordinate, +1 = dominant
        
        # Check dominant patterns
        for pattern in self.DOMINANT_INDICATORS:
            if re.search(pattern, text_lower):
                power_score += 0.3
        
        # Check subordinate patterns
        for pattern in self.SUBORDINATE_INDICATORS:
            if re.search(pattern, text_lower):
                power_score -= 0.3
        
        # Tone affects power perception
        if tone == Tone.HOSTILE:
            power_score += 0.2
        elif tone == Tone.APOLOGETIC:
            power_score -= 0.2
        elif tone == Tone.CONDESCENDING:
            power_score += 0.3
        elif tone == Tone.FORMAL:
            pass  # Neutral
        
        # Clamp to range
        power_score = max(-1.0, min(1.0, power_score))
        
        # Determine relationship dynamic
        if power_score > 0.3:
            dynamic = RelationshipDynamic.SUPERIOR
        elif power_score < -0.3:
            dynamic = RelationshipDynamic.SUBORDINATE
        elif tone == Tone.FRIENDLY or tone == Tone.PLAYFUL:
            dynamic = RelationshipDynamic.INTIMATE
        elif tone == Tone.FORMAL:
            dynamic = RelationshipDynamic.PROFESSIONAL
        elif tone == Tone.HOSTILE:
            dynamic = RelationshipDynamic.ADVERSARIAL
        else:
            dynamic = RelationshipDynamic.EQUAL
        
        return dynamic, power_score


# ═══════════════════════════════════════════════════════════════════════════
# SOCIAL INTELLIGENCE ENGINE - Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class SocialIntelligence:
    """
    Main social intelligence engine.
    Provides complete social reading of any utterance.
    """
    
    def __init__(self):
        self.sarcasm_detector = SarcasmDetector()
        self.tone_analyzer = ToneAnalyzer()
        self.intent_analyzer = IntentAnalyzer()
        self.sentiment_analyzer = DeepSentimentAnalyzer()
        self.subtext_reader = SubtextReader()
        self.dynamics_analyzer = SocialDynamicsAnalyzer()
        
        # History for context
        self.reading_history: deque = deque(maxlen=50)
        
        logger.info("🎭 Social Intelligence initialized")
    
    def read(self, text: str, context: str = "") -> SocialReading:
        """
        Perform complete social reading of text.
        
        Args:
            text: The utterance to analyze
            context: Additional context (conversation history, etc.)
            
        Returns:
            Complete SocialReading with all analysis
        """
        start_time = time.time()
        
        # Step 1: Sarcasm detection (affects everything else)
        is_sarcastic, sarcasm_type, sarcasm_conf, literal, intended = \
            self.sarcasm_detector.detect(text, context)
        
        # Step 2: Tone analysis
        primary_tone, secondary_tones, tone_conf = \
            self.tone_analyzer.analyze(text, is_sarcastic)
        
        # Step 3: Intent analysis
        primary_intent, secondary_intents, intent_conf = \
            self.intent_analyzer.analyze(text, primary_tone)
        
        # Step 4: Deep sentiment
        sentiment = self.sentiment_analyzer.analyze(text, is_sarcastic)
        
        # Step 5: Social dynamics
        dynamic, power_level = self.dynamics_analyzer.analyze(text, primary_tone)
        
        # Step 6: Subtext reading
        subtexts = self.subtext_reader.read(text, context)
        
        # Step 7: Identify cultural elements
        cultural_elements = self._identify_cultural_elements(text)
        references = self._identify_references(text)
        
        # Step 8: Generate warnings
        warnings = self._generate_warnings(
            is_sarcastic, primary_tone, primary_intent, sentiment, subtexts
        )
        
        # Step 9: Recommend response tone
        recommended_tone = self._recommend_response_tone(
            primary_tone, primary_intent, sentiment, is_sarcastic
        )
        
        reading = SocialReading(
            text=text,
            timestamp=time.time(),
            is_sarcastic=is_sarcastic,
            sarcasm_type=sarcasm_type,
            sarcasm_confidence=sarcasm_conf,
            literal_meaning=literal,
            intended_meaning=intended,
            primary_tone=primary_tone,
            secondary_tones=secondary_tones,
            tone_confidence=tone_conf,
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            intent_confidence=intent_conf,
            sentiment=sentiment,
            relationship_dynamic=dynamic,
            power_level=power_level,
            subtexts=subtexts,
            has_hidden_meaning=len(subtexts) > 0 or is_sarcastic,
            references_understood=references,
            cultural_elements=cultural_elements,
            recommended_tone=recommended_tone,
            warning_flags=warnings
        )
        
        self.reading_history.append(reading)
        
        elapsed = int((time.time() - start_time) * 1000)
        logger.debug(f"🎭 Social reading complete in {elapsed}ms")
        
        return reading
    
    def _identify_cultural_elements(self, text: str) -> List[str]:
        """Identify cultural references and idioms."""
        elements = []
        text_lower = text.lower()
        
        # Common idioms
        idioms = {
            "break a leg": "Good luck (theater idiom)",
            "piece of cake": "Very easy",
            "under the weather": "Feeling ill",
            "bite the bullet": "Face difficulty",
            "costs an arm and a leg": "Very expensive",
            "hit the nail on the head": "Exactly right",
            "spill the beans": "Reveal a secret",
            "jump the gun": "Act prematurely"
        }
        
        for idiom, meaning in idioms.items():
            if idiom in text_lower:
                elements.append(f"Idiom: '{idiom}' = {meaning}")
        
        return elements
    
    def _identify_references(self, text: str) -> List[str]:
        """Identify pop culture and other references."""
        references = []
        text_lower = text.lower()
        
        # Just some examples - this would be much larger in practice
        known_refs = {
            "may the force": "Star Wars reference",
            "winter is coming": "Game of Thrones reference",
            "i'll be back": "Terminator reference",
            "you shall not pass": "Lord of the Rings reference",
            "houston": "Apollo 13 reference",
            "to infinity": "Toy Story reference"
        }
        
        for ref, meaning in known_refs.items():
            if ref in text_lower:
                references.append(meaning)
        
        return references
    
    def _generate_warnings(self, is_sarcastic: bool, tone: Tone, 
                          intent: Intent, sentiment: SentimentProfile,
                          subtexts: List[Subtext]) -> List[str]:
        """Generate warning flags for response handling."""
        warnings = []
        
        if is_sarcastic:
            warnings.append("⚠️ Message is sarcastic - respond to intended meaning, not literal")
        
        if tone == Tone.HOSTILE:
            warnings.append("⚠️ Hostile tone detected - respond with care")
        elif tone == Tone.PASSIVE_AGGRESSIVE:
            warnings.append("⚠️ Passive-aggressive - underlying frustration present")
        
        if intent == Intent.VENT:
            warnings.append("💬 User may be venting - prioritize empathy over solutions")
        
        if sentiment.anger > 0.5:
            warnings.append("😠 High anger detected - de-escalation may be needed")
        
        if sentiment.sadness > 0.5:
            warnings.append("😢 Sadness detected - offer emotional support")
        
        if subtexts:
            warnings.append("🎭 Hidden meaning present - read between the lines")
        
        if not sentiment.genuine:
            warnings.append("🎪 Response may be performative - not fully genuine")
        
        return warnings
    
    def _recommend_response_tone(self, their_tone: Tone, intent: Intent,
                                sentiment: SentimentProfile, 
                                is_sarcastic: bool) -> Tone:
        """Recommend appropriate response tone."""
        # Handle negative emotions with care
        if sentiment.anger > 0.5 or their_tone == Tone.HOSTILE:
            return Tone.CALM if hasattr(Tone, 'CALM') else Tone.FRIENDLY
        
        if sentiment.sadness > 0.5:
            return Tone.FRIENDLY
        
        if intent == Intent.VENT:
            return Tone.FRIENDLY
        
        if their_tone == Tone.PLAYFUL:
            return Tone.PLAYFUL
        
        if their_tone == Tone.FORMAL:
            return Tone.FORMAL
        
        if is_sarcastic:
            return Tone.FRIENDLY  # Don't match sarcasm, be genuine
        
        return Tone.FRIENDLY  # Default to friendly
    
    def get_summary(self, reading: SocialReading) -> str:
        """Get human-readable summary of a social reading."""
        lines = [
            f"📝 \"{reading.text[:50]}...\"" if len(reading.text) > 50 else f"📝 \"{reading.text}\"",
            "",
            f"🎭 Sarcastic: {'Yes' if reading.is_sarcastic else 'No'} ({reading.sarcasm_confidence:.0%})"
        ]
        
        if reading.is_sarcastic:
            lines.append(f"   Literal: {reading.literal_meaning[:50]}...")
            lines.append(f"   Intended: {reading.intended_meaning[:50]}...")
        
        lines.extend([
            "",
            f"🎤 Tone: {reading.primary_tone.value} ({reading.tone_confidence:.0%})",
            f"   Secondary: {', '.join(t.value for t in reading.secondary_tones) or 'none'}",
            "",
            f"🎯 Intent: {reading.primary_intent.value} ({reading.intent_confidence:.0%})",
            "",
            f"❤️ Sentiment: {'+' if reading.sentiment.polarity > 0 else ''}{reading.sentiment.polarity:.2f}",
            f"   Intensity: {reading.sentiment.intensity:.0%}",
            f"   Mixed: {'Yes' if reading.sentiment.mixed else 'No'} | Genuine: {'Yes' if reading.sentiment.genuine else 'No'}",
            "",
            f"👥 Dynamic: {reading.relationship_dynamic.value} (power: {reading.power_level:+.1f})"
        ])
        
        if reading.subtexts:
            lines.append("")
            lines.append("🔮 Subtext:")
            for st in reading.subtexts[:2]:
                lines.append(f"   Surface: {st.surface_meaning}")
                lines.append(f"   Hidden: {st.implied_meaning}")
        
        if reading.warning_flags:
            lines.extend(["", "⚠️ Warnings:"])
            for w in reading.warning_flags:
                lines.append(f"   {w}")
        
        lines.extend([
            "",
            f"💬 Recommended response tone: {reading.recommended_tone.value}"
        ])
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_social_intelligence = None

def get_social_intelligence() -> SocialIntelligence:
    """Get the global social intelligence instance."""
    global _social_intelligence
    if _social_intelligence is None:
        _social_intelligence = SocialIntelligence()
    return _social_intelligence


# ═══════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    print("\n🎭 ZARA Social Intelligence v1.0\n")
    print("=" * 70)
    
    si = SocialIntelligence()
    
    # Test cases
    test_cases = [
        "Oh great, another meeting. Just what I needed today.",
        "I'm fine.",
        "That's a really 'interesting' idea you have there.",
        "Could you please help me with this when you get a chance?",
        "DO IT NOW!!!",
        "Hey buddy! Hope you're having an awesome day!",
        "With all due respect, I think you're completely wrong.",
        "Thanks SO much for your 'help' earlier...",
        "We need to talk.",
        "I'm not mad, I'm just disappointed.",
    ]
    
    for text in test_cases:
        print("\n" + "-" * 70)
        reading = si.read(text)
        print(si.get_summary(reading))
    
    print("\n" + "=" * 70)
    print("✅ Social Intelligence ready!\n")
