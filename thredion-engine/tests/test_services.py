"""
Thredion Engine — Extractor & Classifier Unit Tests
Tests platform detection, extraction fallbacks, and classifier logic.
Run:  cd thredion-engine && python -m pytest tests/test_services.py -v
"""

import pytest
from services.extractor import detect_platform, ExtractedContent
from services.classifier import classify_content, _classify_with_keywords


# ── Platform Detection ─────────────────────────────────────────

class TestDetectPlatform:
    @pytest.mark.parametrize("url,expected", [
        ("https://www.instagram.com/p/ABC123/", "instagram"),
        ("https://instagr.am/p/XYZ/", "instagram"),
        ("https://twitter.com/user/status/123", "twitter"),
        ("https://x.com/user/status/456", "twitter"),
        ("https://www.youtube.com/watch?v=abc", "youtube"),
        ("https://youtu.be/abc", "youtube"),
        ("https://www.reddit.com/r/python/comments/abc", "reddit"),
        ("https://www.tiktok.com/@user/video/123", "tiktok"),
        ("https://medium.com/article-title", "article"),
        ("https://myblog.com/page", "article"),
    ])
    def test_platforms(self, url, expected):
        assert detect_platform(url) == expected


# ── Keyword Classifier ────────────────────────────────────────

class TestKeywordClassifier:
    def test_fitness_keywords(self):
        result = _classify_with_keywords(
            "Best home workout routine for building muscle and strength training",
            "https://example.com",
        )
        assert result.category == "Fitness"

    def test_coding_keywords(self):
        result = _classify_with_keywords(
            "Python programming tutorial for beginners learning to code algorithms",
            "https://example.com",
        )
        assert result.category == "Coding"

    def test_food_keywords(self):
        result = _classify_with_keywords(
            "Easy pasta recipe with homemade sauce for dinner cooking at home",
            "https://example.com",
        )
        assert result.category == "Food"

    def test_unknown_falls_to_lifestyle(self):
        """When no keywords match strongly, it should still return a valid category."""
        result = _classify_with_keywords(
            "xyzzy plugh abracadabra random gibberish text",
            "https://example.com",
        )
        # Should be a valid category string, not crash
        assert isinstance(result.category, str)
        assert len(result.category) > 0

    def test_summary_generated(self):
        result = _classify_with_keywords(
            "Machine learning models are transforming how we understand data science.",
            "https://example.com",
        )
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

    def test_tags_generated(self):
        result = _classify_with_keywords(
            "#python #machinelearning Deep learning tutorial for beginners",
            "https://example.com",
        )
        assert isinstance(result.tags, list)
        assert len(result.tags) > 0

    def test_topic_graph_generated(self):
        result = _classify_with_keywords(
            "JavaScript frontend development React components tutorial",
            "https://example.com",
        )
        assert isinstance(result.topic_graph, list)
        assert len(result.topic_graph) > 0


# ── classify_content (wrapper — uses keyword fallback without API key) ──

class TestClassifyContent:
    def test_returns_valid_structure(self):
        result = classify_content("A quick guide to investing in stocks for beginners", "https://example.com")
        assert hasattr(result, "category")
        assert hasattr(result, "summary")
        assert hasattr(result, "tags")
        assert hasattr(result, "topic_graph")
        assert result.category in [
            "Fitness", "Coding", "Design", "Food", "Travel", "Business",
            "Science", "Music", "Art", "Fashion", "Education", "Technology",
            "Health", "Finance", "Motivation", "Entertainment", "Sports",
            "Lifestyle", "DIY", "Photography",
        ]

    def test_handles_empty_text(self):
        result = classify_content("", "https://example.com")
        assert isinstance(result.category, str)
