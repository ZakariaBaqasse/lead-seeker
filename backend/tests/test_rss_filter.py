"""
Unit tests for RSS feed filter logic: _has_ai_signal, _has_funding_signal, _is_relevant.
Tests cover keyword matching, word-boundary detection, category tag matching, and tier behavior.
"""

import pytest

from app.pipeline.sources.rss_feeds import (
    _has_ai_signal,
    _has_funding_signal,
    _is_relevant,
)


# ============================================================================
# _has_ai_signal tests
# ============================================================================


class TestHasAiSignal:
    """Test AI signal detection with both substring and word-boundary keywords."""

    def test_matches_broad_ai_keywords(self):
        """Should match expanded AI keywords."""
        assert _has_ai_signal("This is an AI startup", [])
        assert _has_ai_signal("We use artificial intelligence", [])
        assert _has_ai_signal("Machine learning models", [])
        assert _has_ai_signal("LLM-powered platform", [])
        assert _has_ai_signal("Deep learning research", [])
        assert _has_ai_signal("Foundation model development", [])
        assert _has_ai_signal("Large language model API", [])
        assert _has_ai_signal("GenAI solutions", [])
        assert _has_ai_signal("Generative AI tools", [])
        assert _has_ai_signal("Generative artificial intelligence", [])

    def test_word_boundary_ai_match(self):
        """Should match 'AI' word-boundary, not 'ai' substring in other words."""
        assert _has_ai_signal("This AI company", [])
        assert _has_ai_signal("AI startup raises $10M", [])
        assert _has_ai_signal("Using AI for content", [])

    def test_word_boundary_ai_no_false_positives(self):
        """Should NOT match 'ai' as substring within other words."""
        assert not _has_ai_signal("I said hello", [])
        assert not _has_ai_signal("User email sent", [])
        assert not _has_ai_signal("Failover system", [])
        assert not _has_ai_signal(
            "Wait and aided", []
        )  # "aided" contains "ai" but not as word

    def test_matches_ai_in_categories(self):
        """Should detect AI signals in category tags."""
        assert _has_ai_signal("A tech article", ["Artificial Intelligence"])
        assert _has_ai_signal("News piece", ["Machine Learning"])
        assert _has_ai_signal("General news", ["AI", "Startups"])

    def test_case_insensitive_ai_matching(self):
        """AI matching should be case-insensitive."""
        assert _has_ai_signal("This AI company", [])
        assert _has_ai_signal("This ai company", [])
        assert _has_ai_signal("ARTIFICIAL INTELLIGENCE", [])

    def test_no_ai_signal_empty_text_and_categories(self):
        """Should return False for empty text and categories."""
        assert not _has_ai_signal("", [])
        assert not _has_ai_signal("Random article", [])
        assert not _has_ai_signal("Tech news", [])

    def test_ai_signal_with_multiple_keywords(self):
        """Should return True when multiple AI keywords present."""
        assert _has_ai_signal("Machine learning with deep learning", [])
        assert _has_ai_signal("LLM and generative AI", [])

    def test_ai_signal_substring_in_category(self):
        """Should match AI keywords within category strings."""
        assert _has_ai_signal("", ["Deep Learning Research"])
        assert _has_ai_signal("", ["GenAI Applications"])
        assert _has_ai_signal("", ["Artificial Intelligence News"])


# ============================================================================
# _has_funding_signal tests
# ============================================================================


class TestHasFundingSignal:
    """Test funding signal detection."""

    def test_matches_funding_keywords(self):
        """Should match expanded funding keywords."""
        assert _has_funding_signal("Company raises funding", [])
        assert _has_funding_signal("Startup raises money", [])
        assert _has_funding_signal("Series A round", [])
        assert _has_funding_signal("Seed funding announced", [])
        assert _has_funding_signal("Secures investment", [])
        assert _has_funding_signal("Venture backed", [])
        assert _has_funding_signal("Pre-seed capital", [])
        assert _has_funding_signal("Series B funding", [])
        assert _has_funding_signal("$10 million investment", [])

    def test_matches_funding_in_categories(self):
        """Should detect funding signals in category tags."""
        assert _has_funding_signal("Article text", ["Funding"])
        assert _has_funding_signal("News", ["Venture Capital"])
        assert _has_funding_signal("", ["Investment News"])

    def test_case_insensitive_funding_matching(self):
        """Funding matching should be case-insensitive."""
        assert _has_funding_signal("RAISES Money", [])
        assert _has_funding_signal("seed FUNDING", [])
        assert _has_funding_signal("Series A ROUND", [])

    def test_no_funding_signal_empty_text_and_categories(self):
        """Should return False for text without funding keywords."""
        assert not _has_funding_signal("Product announcement", [])
        assert not _has_funding_signal("Team expands", [])
        assert not _has_funding_signal("", [])


# ============================================================================
# _is_relevant tests
# ============================================================================


class TestIsRelevant:
    """Test tier-based relevance filtering."""

    # --- Funding tier tests ---

    def test_funding_tier_requires_only_funding_signal(self):
        """Funding-tier feeds should pass with funding signal only (no AI required)."""
        # Funding keywords present, no AI keywords - should pass for funding tier
        assert _is_relevant("Company raises $5M Series A", [], "funding")
        assert _is_relevant("Startup secures investment", ["Funding"], "funding")

    def test_funding_tier_passes_with_ai_and_funding(self):
        """Funding-tier feeds should pass with both AI and funding signals."""
        assert _is_relevant("AI startup raises $10M", [], "funding")
        assert _is_relevant("GenAI company secures Series B", [], "funding")

    def test_funding_tier_rejects_without_funding_signal(self):
        """Funding-tier feeds should reject without funding signal."""
        assert not _is_relevant("AI startup announcement", [], "funding")
        assert not _is_relevant("Machine learning research", [], "funding")
        assert not _is_relevant("LLM models explained", [], "funding")

    def test_funding_tier_uses_category_tags(self):
        """Funding-tier feeds should use category tags as signals."""
        # Category contains funding signal
        assert _is_relevant("Article content", ["Venture Capital"], "funding")
        assert _is_relevant("Some news", ["Investment"], "funding")

    # --- General tier tests ---

    def test_general_tier_requires_both_ai_and_funding(self):
        """General-tier feeds should require both AI and funding signals."""
        assert _is_relevant("AI company raises $5M", [], "general")
        assert _is_relevant("GenAI startup secures funding", [], "general")
        assert _is_relevant("Machine learning startup raises Series A", [], "general")

    def test_general_tier_rejects_only_ai(self):
        """General-tier feeds should reject AI-only articles."""
        assert not _is_relevant("AI research announcement", [], "general")
        assert not _is_relevant("New LLM model released", [], "general")
        assert not _is_relevant("Deep learning tutorial", [], "general")

    def test_general_tier_rejects_only_funding(self):
        """General-tier feeds should reject funding-only articles."""
        assert not _is_relevant("Startup raises $10M", [], "general")
        assert not _is_relevant("Series B funding announced", [], "general")
        assert not _is_relevant("Venture capital news", [], "general")

    def test_general_tier_rejects_neither(self):
        """General-tier feeds should reject articles with neither signal."""
        assert not _is_relevant("Company hires new CEO", [], "general")
        assert not _is_relevant("Market update", [], "general")

    def test_general_tier_uses_category_tags(self):
        """General-tier feeds should use category tags for both signals."""
        # Both AI and funding in categories
        assert _is_relevant(
            "Article",
            ["Artificial Intelligence", "Venture Capital"],
            "general",
        )
        # AI in category, funding in text
        assert _is_relevant("Company raises $5M", ["Machine Learning"], "general")

    # --- Edge cases ---

    def test_is_relevant_empty_text(self):
        """Empty text should be handled gracefully."""
        assert not _is_relevant("", [], "funding")
        assert not _is_relevant("", [], "general")

    def test_is_relevant_empty_categories(self):
        """Empty categories should work."""
        assert _is_relevant("AI company raises $10M", [], "funding")
        assert _is_relevant("AI company raises $10M", [], "general")

    def test_is_relevant_unknown_tier(self):
        """Unknown tier should return False."""
        assert not _is_relevant("AI company raises $10M", [], "unknown")
        assert not _is_relevant("News", [], "invalid_tier")

    def test_is_relevant_multiple_categories(self):
        """Should handle multiple categories correctly."""
        categories = [
            "Technology",
            "Machine Learning",
            "Startups",
            "Venture Capital",
        ]
        assert _is_relevant("Article text", categories, "funding")
        assert _is_relevant("Article text", categories, "general")

    def test_is_relevant_case_insensitive_full_flow(self):
        """Full relevance check should be case-insensitive."""
        # Funding tier
        assert _is_relevant("AI COMPANY RAISES $10M", [], "funding")
        assert _is_relevant("genai startup SECURES funding", [], "funding")

        # General tier
        assert _is_relevant("AI COMPANY RAISES $10M", [], "general")
        assert _is_relevant("gEnAi startup SECURES FUNDING", [], "general")


# ============================================================================
# Integration tests: realistic scenarios
# ============================================================================


class TestRealisticScenarios:
    """Test realistic article scenarios."""

    def test_realistic_funding_feed_article(self):
        """Realistic article from funding-tier feed (e.g., sifted.eu)."""
        title = "European AI startup secures $5M seed funding"
        description = (
            "A new AI company focused on NLP has raised seed funding from top VCs."
        )
        combined = f"{title} {description}"
        assert _is_relevant(combined, [], "funding")

    def test_realistic_general_feed_article_with_both_signals(self):
        """Realistic TechCrunch article with both AI and funding."""
        title = "GenAI unicorn raises $200M Series C"
        description = "The AI company reaches new heights with massive Series C round."
        combined = f"{title} {description}"
        assert _is_relevant(combined, [], "general")

    def test_realistic_general_feed_article_no_ai(self):
        """Realistic article from general feed without AI signal (should fail)."""
        title = "Startup raises $10M funding"
        description = "A new e-commerce platform announced a Series A round."
        combined = f"{title} {description}"
        assert not _is_relevant(combined, [], "general")

    def test_realistic_general_feed_article_no_funding(self):
        """Realistic article about AI but no funding (should fail on general tier)."""
        title = "How Large Language Models are Changing Industry"
        description = "LLM and deep learning are transforming software development."
        combined = f"{title} {description}"
        assert not _is_relevant(combined, [], "general")

    def test_realistic_article_with_rich_categories(self):
        """Realistic article with category tags from tech.eu style feed."""
        title = "AI Platform Raises Series A"
        description = "New machine learning startup announces funding."
        categories = ["Artificial Intelligence", "Startups", "Funding"]
        assert _is_relevant(f"{title} {description}", categories, "funding")

    def test_word_boundary_ai_in_realistic_context(self):
        """Word-boundary 'AI' should match in realistic headlines."""
        assert _is_relevant("AI startup raises $10M", [], "general")
        assert _is_relevant("Top 5 AI companies seeking funding", [], "funding")
        assert _is_relevant("AI tools for developers secures $5M", [], "funding")

    def test_false_positive_avoidance_said(self):
        """Should NOT match 'said' which contains 'ai'."""
        text = "CEO said the company will focus on new markets. Raises $5M."
        # For general tier, needs AI signal - should fail because 'ai' in 'said' is not word
        assert not _is_relevant(text, [], "general")
        # For funding tier, should still pass (has funding keyword)
        assert _is_relevant(text, [], "funding")

    def test_false_positive_avoidance_email(self):
        """Should NOT match 'email' which contains 'ai'."""
        text = "Company email system upgraded. Secures $5M funding."
        assert _is_relevant(text, [], "funding")  # funding signal present
        assert not _is_relevant(text, [], "general")  # no AI signal
