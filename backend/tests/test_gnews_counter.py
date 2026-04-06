import pytest
from unittest.mock import patch
from datetime import date


class TestGNewsCounter:
    def test_counter_resets_on_new_day(self):
        """GNews counter resets when date changes."""
        import app.pipeline.sources.gnews as gnews_module
        gnews_module._daily_count = 79
        gnews_module._count_date = date(2000, 1, 1)  # old date

        # Calling _check_and_increment should detect the date mismatch and reset
        result = gnews_module._check_and_increment()
        assert gnews_module._daily_count == 1  # reset to 0 then incremented
        assert gnews_module._count_date == date.today()
        assert result is True  # request should be allowed

    def test_counter_blocks_at_limit(self):
        """GNews counter blocks requests once daily limit is reached."""
        import app.pipeline.sources.gnews as gnews_module
        gnews_module._daily_count = gnews_module.MAX_DAILY_REQUESTS
        gnews_module._count_date = date.today()

        result = gnews_module._check_and_increment()
        assert result is False  # blocked

    def test_counter_allows_before_limit(self):
        """GNews counter allows requests before daily limit."""
        import app.pipeline.sources.gnews as gnews_module
        gnews_module._daily_count = 0
        gnews_module._count_date = date.today()

        result = gnews_module._check_and_increment()
        assert result is True
        assert gnews_module._daily_count == 1

    def test_imports_ok(self):
        from app.pipeline.sources.gnews import fetch_gnews
        assert callable(fetch_gnews)
