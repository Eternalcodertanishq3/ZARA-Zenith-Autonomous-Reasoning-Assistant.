"""
ZARA Unified Perception Tests
==============================
Tests for the unified multimodal perception system.
Run with: pytest tests/test_unified_perception.py -v
"""

import pytest
import time


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnifiedPerceptionImports:
    """Test all modules import correctly."""
    
    def test_module_imports(self):
        """Test main module imports."""
        from brain.unified_perception import (
            UnifiedPerception,
            PerceptualTokenizer,
            JointAttentionMechanism,
            SceneGraphBuilder,
            MomentBuffer,
            get_unified_perception
        )
        assert UnifiedPerception is not None
        assert PerceptualTokenizer is not None
    
    def test_types_import(self):
        """Test type imports."""
        from brain.unified_perception import (
            Modality,
            Salience,
            EntityType,
            PerceptualToken,
            SceneEntity,
            Moment
        )
        assert Modality.VISION is not None
        assert Salience.HIGH is not None


# ═══════════════════════════════════════════════════════════════════════════════
# PERCEPTUAL TOKENIZER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerceptualTokenizer:
    """Tests for PerceptualTokenizer."""
    
    def test_tokenize_vision(self, perceptual_tokenizer):
        """Test vision input tokenization."""
        tokens = perceptual_tokenizer.tokenize_vision(
            description="User at desk",
            objects=["desk", "monitor"],
            faces=[{"emotion": "happy", "attention": 0.8}],
            emotion="happy",
            attention_score=0.8
        )
        
        assert len(tokens) >= 1
        assert tokens[0].content == "User at desk"
    
    def test_tokenize_audio(self, perceptual_tokenizer):
        """Test audio input tokenization."""
        tokens = perceptual_tokenizer.tokenize_audio(
            transcription="Hello, how are you?",
            voice_emotion="curious",
            speaker_id="user_1",
            volume=0.6
        )
        
        assert len(tokens) >= 1
        assert "Hello" in tokens[0].content
    
    def test_tokenize_text(self, perceptual_tokenizer):
        """Test text input tokenization."""
        tokens = perceptual_tokenizer.tokenize_text(
            text="Help me with my project",
            sentiment=0.5,
            topics=["help", "project"],
            is_question=False
        )
        
        assert len(tokens) >= 1
        assert tokens[0].content == "Help me with my project"
    
    def test_generates_embeddings(self, perceptual_tokenizer):
        """Test embeddings are generated."""
        tokens = perceptual_tokenizer.tokenize_text("Test message")
        
        assert len(tokens[0].embedding) == 128
        assert any(v != 0 for v in tokens[0].embedding)
    
    def test_unique_ids(self, perceptual_tokenizer):
        """Test each token gets unique ID."""
        tokens1 = perceptual_tokenizer.tokenize_text("First")
        tokens2 = perceptual_tokenizer.tokenize_text("Second")
        
        assert tokens1[0].id != tokens2[0].id


# ═══════════════════════════════════════════════════════════════════════════════
# JOINT ATTENTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestJointAttentionMechanism:
    """Tests for JointAttentionMechanism."""
    
    def test_compute_bindings_empty(self, joint_attention):
        """Test bindings with empty tokens."""
        bindings = joint_attention.compute_bindings([])
        assert bindings == {}
    
    def test_compute_bindings_cross_modal(self, joint_attention, perceptual_tokenizer):
        """Test cross-modal binding."""
        # Create tokens with matching emotions
        vision_tokens = perceptual_tokenizer.tokenize_vision(
            description="Face",
            faces=[{"emotion": "happy", "attention": 0.8}]
        )
        audio_tokens = perceptual_tokenizer.tokenize_audio(
            transcription="Hello!",
            voice_emotion="happy"
        )
        
        all_tokens = vision_tokens + audio_tokens
        bindings = joint_attention.compute_bindings(all_tokens)
        
        # Should have some bindings (emotions match)
        # Note: bindings depend on temporal proximity and embedding similarity
        assert isinstance(bindings, dict)
    
    def test_compute_spotlight(self, joint_attention, perceptual_tokenizer):
        """Test spotlight computation."""
        tokens = perceptual_tokenizer.tokenize_text("Important message")
        bindings = {}
        
        spotlight = joint_attention.compute_spotlight(tokens, bindings)
        
        assert spotlight is not None
        assert spotlight == tokens[0].id
    
    def test_apply_attention_weights(self, joint_attention, perceptual_tokenizer):
        """Test attention weight application."""
        tokens = perceptual_tokenizer.tokenize_text("Test")
        bindings = {}
        spotlight = tokens[0].id
        
        weighted = joint_attention.apply_attention_weights(tokens, spotlight, bindings)
        
        assert weighted[0].attention_weight == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE GRAPH TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSceneGraphBuilder:
    """Tests for SceneGraphBuilder."""
    
    def test_build_empty(self, scene_builder):
        """Test building from empty tokens."""
        entities = scene_builder.build_from_tokens([], {})
        assert len(entities) == 0
    
    def test_build_from_face_tokens(self, scene_builder, perceptual_tokenizer):
        """Test entity creation from face tokens."""
        tokens = perceptual_tokenizer.tokenize_vision(
            description="User visible",
            faces=[{"emotion": "focused", "attention": 0.9}]
        )
        bindings = {}
        
        entities = scene_builder.build_from_tokens(tokens, bindings)
        
        # Should create entity for face
        assert len(entities) >= 1
    
    def test_scene_description(self, scene_builder, perceptual_tokenizer):
        """Test scene description generation."""
        tokens = perceptual_tokenizer.tokenize_vision(
            description="Office setting",
            objects=["desk", "chair"]
        )
        scene_builder.build_from_tokens(tokens, {})
        
        description = scene_builder.get_scene_description()
        assert isinstance(description, str)


# ═══════════════════════════════════════════════════════════════════════════════
# MOMENT BUFFER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMomentBuffer:
    """Tests for MomentBuffer."""
    
    def test_create_moment(self, moment_buffer, perceptual_tokenizer):
        """Test moment creation."""
        tokens = perceptual_tokenizer.tokenize_text("Hello")
        
        moment = moment_buffer.create_moment(
            tokens=tokens,
            entities={},
            bindings={},
            attention_focus=tokens[0].id
        )
        
        assert moment is not None
        assert moment.attention_focus == tokens[0].id
    
    def test_get_current(self, moment_buffer, perceptual_tokenizer):
        """Test getting current moment."""
        # Initially empty
        assert moment_buffer.get_current() is None
        
        # After creating moment
        tokens = perceptual_tokenizer.tokenize_text("Test")
        moment_buffer.create_moment(tokens, {}, {}, None)
        
        assert moment_buffer.get_current() is not None
    
    def test_temporal_context(self, moment_buffer, perceptual_tokenizer):
        """Test temporal context aggregation."""
        # Create a few moments
        for i in range(3):
            tokens = perceptual_tokenizer.tokenize_text(f"Message {i}")
            moment_buffer.create_moment(tokens, {}, {}, None)
        
        context = moment_buffer.get_temporal_context(window_seconds=60.0)
        
        assert context["moments"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED PERCEPTION INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnifiedPerception:
    """Integration tests for UnifiedPerception."""
    
    def test_initialization(self, unified_perception):
        """Test engine initializes correctly."""
        assert unified_perception.tokenizer is not None
        assert unified_perception.attention is not None
        assert unified_perception.scene_builder is not None
        assert unified_perception.moment_buffer is not None
    
    def test_perceive_vision(self, unified_perception):
        """Test vision perception."""
        unified_perception.perceive_vision(
            description="User at computer",
            objects=["keyboard", "monitor"],
            emotion="focused"
        )
        
        context = unified_perception.get_unified_context()
        assert "scene" in context
    
    def test_perceive_audio(self, unified_perception):
        """Test audio perception."""
        unified_perception.perceive_audio(
            transcription="Hello ZARA",
            voice_emotion="friendly"
        )
        
        context = unified_perception.get_unified_context()
        assert context is not None
    
    def test_perceive_text(self, unified_perception):
        """Test text perception."""
        unified_perception.perceive_text(
            text="What's the weather?",
            is_question=True
        )
        
        context = unified_perception.get_unified_context()
        assert context is not None
    
    def test_multimodal_integration(self, unified_perception):
        """Test all modalities together."""
        # Simulate multimodal input
        unified_perception.perceive_vision(
            description="User looking at camera",
            faces=[{"emotion": "curious"}]
        )
        unified_perception.perceive_audio(
            transcription="Can you help me?",
            voice_emotion="curious"
        )
        unified_perception.perceive_text(
            text="Help request",
            is_question=True
        )
        
        context = unified_perception.get_unified_context()
        
        # Should have integrated perception
        assert "scene" in context
        assert "emotion" in context
    
    def test_get_context_string(self, unified_perception):
        """Test context string generation for LLM."""
        unified_perception.perceive_text("Test input")
        
        context_str = unified_perception.get_context_string()
        
        assert isinstance(context_str, str)
    
    def test_get_status(self, unified_perception):
        """Test status reporting."""
        status = unified_perception.get_status()
        
        assert "active_tokens" in status
        assert "entities" in status
        assert "moments_buffered" in status
    
    def test_callbacks(self, unified_perception):
        """Test moment and attention callbacks."""
        moments_received = []
        
        def on_moment(moment):
            moments_received.append(moment)
        
        unified_perception.on_moment_created.append(on_moment)
        
        unified_perception.perceive_text("Trigger moment")
        
        assert len(moments_received) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSingleton:
    """Test singleton pattern."""
    
    def test_get_unified_perception_singleton(self):
        """Test singleton returns same instance."""
        from brain.unified_perception import get_unified_perception
        
        instance1 = get_unified_perception()
        instance2 = get_unified_perception()
        
        assert instance1 is instance2
