"""Unit tests for TestPatternGenerator."""

import os

import pytest
from PIL import Image

from app.infrastructure.services.test_pattern import (TestPatternGenerator,
                                                      TestPatternType)


class TestTestPatternGenerator:
    """Tests for TestPatternGenerator."""

    @pytest.fixture
    def generator(self, tmp_path, monkeypatch):
        """Create generator with temp storage path."""
        monkeypatch.setattr(
            "app.infrastructure.services.test_pattern.settings",
            type("Settings", (), {"storage_path": str(tmp_path)})(),
        )
        return TestPatternGenerator()

    def test_init_creates_directory(self, generator):
        """Generator creates test_prints directory on init."""
        assert generator.test_prints_dir.exists()

    def test_generate_color_bars(self, generator):
        """Generate color bars pattern."""
        result = generator.generate(TestPatternType.COLOR_BARS)

        assert result is not None
        assert os.path.exists(result)
        assert "color_bars" in result

        # Verify image dimensions
        img = Image.open(result)
        assert img.size == (1200, 1800)
        assert img.mode == "RGB"

    def test_generate_alignment(self, generator):
        """Generate alignment grid pattern."""
        result = generator.generate(TestPatternType.ALIGNMENT)

        assert result is not None
        assert os.path.exists(result)
        assert "alignment" in result

        img = Image.open(result)
        assert img.size == (1200, 1800)

    def test_generate_gradient(self, generator):
        """Generate gradient pattern."""
        result = generator.generate(TestPatternType.GRADIENT)

        assert result is not None
        assert os.path.exists(result)
        assert "gradient" in result

        img = Image.open(result)
        assert img.size == (1200, 1800)

    def test_generate_full(self, generator):
        """Generate full test pattern."""
        result = generator.generate(TestPatternType.FULL)

        assert result is not None
        assert os.path.exists(result)
        assert "full" in result

        img = Image.open(result)
        assert img.size == (1200, 1800)

    def test_generate_default_is_full(self, generator):
        """Default pattern type is full."""
        result = generator.generate()

        assert result is not None
        assert "full" in result

    def test_generate_unique_filenames(self, generator):
        """Each generation creates unique filename."""
        result1 = generator.generate(TestPatternType.FULL)
        result2 = generator.generate(TestPatternType.FULL)

        assert result1 != result2
        assert os.path.exists(result1)
        assert os.path.exists(result2)

    def test_cleanup_old_test_prints(self, generator, tmp_path):
        """Cleanup removes old files."""
        # Create some old test files
        old_file = generator.test_prints_dir / "test_pattern_old.jpg"
        old_file.touch()

        # Set modification time to 48 hours ago
        import time

        old_time = time.time() - (48 * 3600)
        os.utime(old_file, (old_time, old_time))

        # Create a new file
        new_file = generator.generate(TestPatternType.FULL)

        # Cleanup with 24 hour threshold
        deleted = generator.cleanup_old_test_prints(max_age_hours=24)

        assert deleted == 1
        assert not old_file.exists()
        assert os.path.exists(new_file)

    def test_image_quality(self, generator):
        """Generated images have proper quality settings."""
        result = generator.generate(TestPatternType.FULL)

        img = Image.open(result)
        # Check that image is in RGB mode (no alpha)
        assert img.mode == "RGB"

        # Check file is reasonably sized (should be JPEG compressed)
        file_size = os.path.getsize(result)
        # Should be at least 100KB but not overly large
        assert 100_000 < file_size < 5_000_000


class TestTestPatternType:
    """Tests for TestPatternType enum."""

    def test_all_pattern_types_exist(self):
        """All expected pattern types exist."""
        assert TestPatternType.COLOR_BARS.value == "color_bars"
        assert TestPatternType.ALIGNMENT.value == "alignment"
        assert TestPatternType.GRADIENT.value == "gradient"
        assert TestPatternType.FULL.value == "full"

    def test_pattern_type_from_string(self):
        """Can create pattern type from string value."""
        assert TestPatternType("color_bars") == TestPatternType.COLOR_BARS
        assert TestPatternType("full") == TestPatternType.FULL

    def test_invalid_pattern_type_raises(self):
        """Invalid pattern type raises ValueError."""
        with pytest.raises(ValueError):
            TestPatternType("invalid")
