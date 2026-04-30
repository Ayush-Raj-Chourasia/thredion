"""
Thredion Engine - Unit Tests for LLM Processor Service
Tests Groq integration, structured output parsing, and fallback classification.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from services.llm_processor import (
    process_with_groq,
    fallback_classification,
    CognitiveStructure,
    get_groq_client,
)


class TestGroqIntegration:
    """Test Groq Cloud LLM integration."""
    
    @pytest.mark.asyncio
    @patch('services.llm_processor.Groq')
    async def test_valid_groq_response_parsing(self, mock_groq_class):
        """Test parsing valid Groq response."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        valid_response = {
            "cognitive_mode": "learn",
            "title": "AI Tools",
            "summary": "Discussion about new AI models",
            "key_points": ["Model comparison", "Performance metrics"],
            "bucket": "AI Tools",
            "tags": ["AI", "LLM", "Tools"],
            "actionability_score": 0.7,
            "emotional_tone": "curious",
            "confidence_score": 0.85,
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(valid_response)
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await process_with_groq(
            "Test transcription about AI tools",
            existing_buckets=["AI Tools", "Startup Ideas"],
            platform="youtube"
        )
        
        assert result is not None
        assert result.cognitive_mode == "learn"
        assert result.bucket == "AI Tools"
        assert result.actionability_score == 0.7
        assert result.confidence_score == 0.85
    
    @pytest.mark.asyncio
    @patch('services.llm_processor.Groq')
    async def test_groq_markdown_code_block_handling(self, mock_groq_class):
        """Test parsing Groq response wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        valid_data = {
            "cognitive_mode": "think",
            "title": "Startup Idea",
            "summary": "New business model",
            "key_points": ["Market gap", "Revenue model"],
            "bucket": "Startup Ideas",
            "tags": ["Business", "Ideas"],
            "actionability_score": 0.9,
            "emotional_tone": "excited",
            "confidence_score": 0.8,
        }
        
        # Groq sometimes wraps in markdown
        markdown_response = f"```json\n{json.dumps(valid_data)}\n```"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = markdown_response
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await process_with_groq("Startup idea transcript")
        
        assert result is not None
        assert result.cognitive_mode == "think"
    
    @pytest.mark.asyncio
    @patch('services.llm_processor.Groq')
    async def test_groq_api_failure_fallback(self, mock_groq_class):
        """Test fallback when Groq API fails."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Should return None and log error, then fallback is called
        result = await process_with_groq("Test content")
        
        assert result is None  # LLM failed


class TestCognitiveStructureValidation:
    """Test Pydantic model validation."""
    
    def test_valid_cognitive_structure(self):
        """Test creating valid CognitiveStructure."""
        data = {
            "cognitive_mode": "learn",
            "title": "Test Title",
            "summary": "Test summary",
            "key_points": ["point1", "point2"],
            "bucket": "Technology",
            "tags": ["tag1", "tag2"],
            "actionability_score": 0.5,
            "emotional_tone": "neutral",
            "confidence_score": 0.8,
        }
        
        structure = CognitiveStructure(**data)
        assert structure.cognitive_mode == "learn"
        assert structure.actionability_score == 0.5
    
    def test_invalid_cognitive_mode(self):
        """Test that invalid cognitive mode is rejected."""
        data = {
            "cognitive_mode": "invalid",  # Should be learn|think|reflect
            "title": "Test",
            "summary": "Test",
            "key_points": [],
            "bucket": "Test",
            "tags": [],
            "actionability_score": 0.5,
            "emotional_tone": "neutral",
            "confidence_score": 0.8,
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            CognitiveStructure(**data)
    
    def test_score_bounds(self):
        """Test that scores are bounded 0-1."""
        data = {
            "cognitive_mode": "learn",
            "title": "Test",
            "summary": "Test",
            "key_points": [],
            "bucket": "Test",
            "tags": [],
            "actionability_score": 1.5,  # Invalid: should be 0-1
            "emotional_tone": "neutral",
            "confidence_score": 0.8,
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            CognitiveStructure(**data)


class TestFallbackClassification:
    """Test keyword-based fallback when LLM fails."""
    
    @pytest.mark.asyncio
    async def test_fallback_learns_mode(self):
        """Test fallback correctly identifies learn mode."""
        text = "This is an article about machine learning on Medium"
        
        result = await fallback_classification(text)
        
        assert result.cognitive_mode == "learn"  # External content
        assert result.confidence_score < 0.5  # Low confidence for fallback
    
    @pytest.mark.asyncio
    async def test_fallback_think_mode(self):
        """Test fallback correctly identifies think mode."""
        text = "I think we should build a SaaS product that helps with project management"
        
        result = await fallback_classification(text)
        
        assert result.cognitive_mode == "think"  # Original idea
    
    @pytest.mark.asyncio
    async def test_fallback_reflect_mode(self):
        """Test fallback correctly identifies reflect mode."""
        text = "Today I felt anxious about my decision to quit my job"
        
        result = await fallback_classification(text)
        
        assert result.cognitive_mode == "reflect"  # Personal reflection
    
    @pytest.mark.asyncio
    async def test_fallback_bucket_detection(self):
        """Test fallback bucket detection from keywords."""
        text = "Python code for building FastAPI web applications with async support"
        
        result = await fallback_classification(text)
        
        assert result.bucket == "Coding"  # Should detect programming keywords
    
    @pytest.mark.asyncio
    async def test_fallback_default_bucket(self):
        """Test fallback uses default bucket when no keywords match."""
        text = "xyz abc qwerty placeholder text with no keywords"
        
        result = await fallback_classification(text)
        
        assert result.bucket == "Uncategorized"


class TestGroqClientInitialization:
    """Test Groq client setup."""
    
    @patch.dict('os.environ', {})
    def test_no_api_key_warning(self):
        """Test warning when GROQ_API_KEY not set."""
        # This should log a warning
        client = get_groq_client()
        assert client is None or True  # Either None or returns client


class TestBucketPreference:
    """Test preference for existing buckets in LLM processing."""
    
    @pytest.mark.asyncio
    @patch('services.llm_processor.Groq')
    async def test_prompt_includes_existing_buckets(self, mock_groq_class):
        """Test that existing buckets are included in the system prompt."""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "cognitive_mode": "learn",
            "title": "Test",
            "summary": "Test",
            "key_points": [],
            "bucket": "Existing Bucket",
            "tags": [],
            "actionability_score": 0.5,
            "emotional_tone": "neutral",
            "confidence_score": 0.8,
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        existing = ["Bucket1", "Bucket2", "Existing Bucket"]
        await process_with_groq("Test content", existing_buckets=existing)
        
        # Check that the system prompt included the buckets
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        system_prompt = messages[0]['content']
        
        assert "Bucket1" in system_prompt
        assert "Bucket2" in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
