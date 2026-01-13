"""Test pattern generator for printer testing."""

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TestPatternType(str, Enum):
    """Types of test patterns."""

    COLOR_BARS = "color_bars"
    ALIGNMENT = "alignment"
    GRADIENT = "gradient"
    FULL = "full"


class TestPatternGenerator:
    """Generates test patterns for printer testing."""

    # 4x6 inch at 300 DPI
    WIDTH = 1200
    HEIGHT = 1800

    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.test_prints_dir = self.storage_path / "test_prints"
        self.test_prints_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self, pattern_type: TestPatternType = TestPatternType.FULL
    ) -> Optional[str]:
        """Generate a test pattern image.

        Args:
            pattern_type: Type of test pattern to generate

        Returns:
            Path to generated image file
        """
        try:
            if pattern_type == TestPatternType.COLOR_BARS:
                image = self._generate_color_bars()
            elif pattern_type == TestPatternType.ALIGNMENT:
                image = self._generate_alignment_grid()
            elif pattern_type == TestPatternType.GRADIENT:
                image = self._generate_gradient()
            else:  # FULL - combines all patterns
                image = self._generate_full_test()

            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"test_pattern_{pattern_type.value}_{timestamp}.jpg"
            filepath = self.test_prints_dir / filename

            image.save(str(filepath), "JPEG", quality=95)
            logger.info(f"Test pattern generated: {filepath}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate test pattern: {e}")
            return None

    def _generate_color_bars(self) -> Image.Image:
        """Generate color bars pattern (SMPTE-like)."""
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        # Primary colors for the main section (top 75%)
        colors = [
            (192, 192, 192),  # Gray
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
            (0, 255, 0),  # Green
            (255, 0, 255),  # Magenta
            (255, 0, 0),  # Red
            (0, 0, 255),  # Blue
        ]

        bar_width = self.WIDTH // len(colors)
        main_height = int(self.HEIGHT * 0.75)

        for i, color in enumerate(colors):
            x0 = i * bar_width
            x1 = (i + 1) * bar_width if i < len(colors) - 1 else self.WIDTH
            draw.rectangle([x0, 0, x1, main_height], fill=color)

        # Secondary bars (next 8%)
        secondary_height = int(self.HEIGHT * 0.08)
        secondary_y = main_height
        secondary_colors = [
            (0, 0, 255),  # Blue
            (19, 19, 19),  # Super black
            (255, 0, 255),  # Magenta
            (19, 19, 19),  # Super black
            (0, 255, 255),  # Cyan
            (19, 19, 19),  # Super black
            (192, 192, 192),  # Gray
        ]

        for i, color in enumerate(secondary_colors):
            x0 = i * bar_width
            x1 = (i + 1) * bar_width if i < len(colors) - 1 else self.WIDTH
            draw.rectangle(
                [x0, secondary_y, x1, secondary_y + secondary_height], fill=color
            )

        # Black/gray gradient section (remaining)
        gradient_y = secondary_y + secondary_height

        section_width = self.WIDTH // 4

        # Super black
        draw.rectangle([0, gradient_y, section_width, self.HEIGHT], fill=(0, 0, 0))

        # Black
        draw.rectangle(
            [section_width, gradient_y, section_width * 2, self.HEIGHT],
            fill=(19, 19, 19),
        )

        # Gray
        draw.rectangle(
            [section_width * 2, gradient_y, section_width * 3, self.HEIGHT],
            fill=(128, 128, 128),
        )

        # White
        draw.rectangle(
            [section_width * 3, gradient_y, self.WIDTH, self.HEIGHT],
            fill=(255, 255, 255),
        )

        # Add label
        self._add_label(draw, "COLOR BARS TEST", 50)

        return image

    def _generate_alignment_grid(self) -> Image.Image:
        """Generate alignment/registration grid."""
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        # Draw grid lines
        line_color = (0, 0, 0)
        grid_spacing = 100  # pixels

        # Vertical lines
        for x in range(0, self.WIDTH + 1, grid_spacing):
            width = 3 if x % 300 == 0 else 1
            draw.line([(x, 0), (x, self.HEIGHT)], fill=line_color, width=width)

        # Horizontal lines
        for y in range(0, self.HEIGHT + 1, grid_spacing):
            width = 3 if y % 300 == 0 else 1
            draw.line([(0, y), (self.WIDTH, y)], fill=line_color, width=width)

        # Center crosshair
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        crosshair_size = 50
        crosshair_color = (255, 0, 0)

        draw.line(
            [
                (center_x - crosshair_size, center_y),
                (center_x + crosshair_size, center_y),
            ],
            fill=crosshair_color,
            width=3,
        )
        draw.line(
            [
                (center_x, center_y - crosshair_size),
                (center_x, center_y + crosshair_size),
            ],
            fill=crosshair_color,
            width=3,
        )

        # Corner markers
        marker_size = 80
        for corner in [
            (0, 0),
            (self.WIDTH, 0),
            (0, self.HEIGHT),
            (self.WIDTH, self.HEIGHT),
        ]:
            cx, cy = corner
            # Adjust for corner position
            dx = marker_size if cx == 0 else -marker_size
            dy = marker_size if cy == 0 else -marker_size

            draw.line([(cx, cy), (cx + dx, cy)], fill=crosshair_color, width=3)
            draw.line([(cx, cy), (cx, cy + dy)], fill=crosshair_color, width=3)

        # Border rectangle
        margin = 50
        draw.rectangle(
            [margin, margin, self.WIDTH - margin, self.HEIGHT - margin],
            outline=(0, 0, 255),
            width=3,
        )

        # Add label
        self._add_label(draw, "ALIGNMENT GRID", 50)

        return image

    def _generate_gradient(self) -> Image.Image:
        """Generate gradient test pattern."""
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        section_height = self.HEIGHT // 4

        # Grayscale gradient (top section)
        for x in range(self.WIDTH):
            gray = int((x / self.WIDTH) * 255)
            draw.line([(x, 0), (x, section_height)], fill=(gray, gray, gray))

        # Red gradient
        for x in range(self.WIDTH):
            red = int((x / self.WIDTH) * 255)
            draw.line([(x, section_height), (x, section_height * 2)], fill=(red, 0, 0))

        # Green gradient
        for x in range(self.WIDTH):
            green = int((x / self.WIDTH) * 255)
            draw.line(
                [(x, section_height * 2), (x, section_height * 3)], fill=(0, green, 0)
            )

        # Blue gradient
        for x in range(self.WIDTH):
            blue = int((x / self.WIDTH) * 255)
            draw.line([(x, section_height * 3), (x, self.HEIGHT)], fill=(0, 0, blue))

        # Add labels for each section
        labels = ["GRAYSCALE", "RED", "GREEN", "BLUE"]
        for i, label in enumerate(labels):
            y = i * section_height + 20
            self._add_label(draw, label, y, font_size=30)

        return image

    def _generate_full_test(self) -> Image.Image:
        """Generate full test pattern combining all elements."""
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        # Header section (10%)
        header_height = int(self.HEIGHT * 0.1)
        draw.rectangle(
            [0, 0, self.WIDTH, header_height], fill=(0, 161, 222)
        )  # Rwanda blue

        # Title
        self._add_label(
            draw,
            "PHOTOBOOTH PRINTER TEST",
            header_height // 2 - 20,
            font_size=40,
            color=(255, 255, 255),
        )

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._add_label(
            draw,
            timestamp,
            header_height // 2 + 20,
            font_size=20,
            color=(255, 255, 255),
        )

        # Color bars section (25%)
        color_section_start = header_height
        color_section_height = int(self.HEIGHT * 0.25)
        colors = [
            (255, 0, 0),  # Red
            (255, 165, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),  # Green
            (0, 255, 255),  # Cyan
            (0, 0, 255),  # Blue
            (128, 0, 128),  # Purple
            (255, 255, 255),  # White
            (0, 0, 0),  # Black
        ]

        bar_width = self.WIDTH // len(colors)
        for i, color in enumerate(colors):
            x0 = i * bar_width
            x1 = (i + 1) * bar_width if i < len(colors) - 1 else self.WIDTH
            draw.rectangle(
                [
                    x0,
                    color_section_start,
                    x1,
                    color_section_start + color_section_height,
                ],
                fill=color,
            )

        # Gradient section (20%)
        gradient_start = color_section_start + color_section_height
        gradient_height = int(self.HEIGHT * 0.2)

        for x in range(self.WIDTH):
            gray = int((x / self.WIDTH) * 255)
            draw.line(
                [(x, gradient_start), (x, gradient_start + gradient_height // 2)],
                fill=(gray, gray, gray),
            )

        # RGB gradients in thirds
        third_width = self.WIDTH // 3
        for x in range(self.WIDTH):
            intensity = int((x % third_width) / third_width * 255)
            y_start = gradient_start + gradient_height // 2
            y_end = gradient_start + gradient_height

            if x < third_width:
                color = (intensity, 0, 0)
            elif x < third_width * 2:
                color = (0, intensity, 0)
            else:
                color = (0, 0, intensity)

            draw.line([(x, y_start), (x, y_end)], fill=color)

        # Grid section (25%)
        grid_start = gradient_start + gradient_height
        grid_height = int(self.HEIGHT * 0.25)

        # Draw grid
        grid_spacing = 60
        for x in range(0, self.WIDTH, grid_spacing):
            draw.line(
                [(x, grid_start), (x, grid_start + grid_height)], fill=(200, 200, 200)
            )
        for y in range(grid_start, grid_start + grid_height, grid_spacing):
            draw.line([(0, y), (self.WIDTH, y)], fill=(200, 200, 200))

        # Center circle for alignment
        center_x = self.WIDTH // 2
        center_y = grid_start + grid_height // 2
        for radius in [50, 100, 150]:
            draw.ellipse(
                [
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                ],
                outline=(0, 0, 0),
                width=2,
            )

        # Crosshairs
        draw.line(
            [(center_x - 180, center_y), (center_x + 180, center_y)],
            fill=(255, 0, 0),
            width=2,
        )
        draw.line(
            [(center_x, center_y - 180), (center_x, center_y + 180)],
            fill=(255, 0, 0),
            width=2,
        )

        # Footer section (20%) - info panel
        footer_start = grid_start + grid_height

        draw.rectangle([0, footer_start, self.WIDTH, self.HEIGHT], fill=(240, 240, 240))

        # Test info
        info_lines = [
            "Printer: Canon Selphy CP1500",
            "Paper: 4x6 inch (Postcard)",
            f"Resolution: {self.WIDTH}x{self.HEIGHT} @ 300 DPI",
            "Check: Colors, alignment, gradients",
        ]

        y = footer_start + 30
        for line in info_lines:
            self._add_label(draw, line, y, font_size=28, color=(60, 60, 60))
            y += 40

        # Rwanda flag colors indicator
        rwanda_colors = [
            ((0, 161, 222), "Sky Blue"),
            ((32, 96, 61), "Green"),
            ((250, 210, 1), "Yellow"),
        ]

        color_box_size = 50
        color_x = 50
        color_y = self.HEIGHT - 80

        for color, name in rwanda_colors:
            draw.rectangle(
                [color_x, color_y, color_x + color_box_size, color_y + color_box_size],
                fill=color,
                outline=(0, 0, 0),
            )
            color_x += color_box_size + 10

        return image

    def _add_label(
        self,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font_size: int = 36,
        color: tuple = (0, 0, 0),
    ):
        """Add a centered text label."""
        try:
            # Try to use system font
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
        except (OSError, IOError):
            try:
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", font_size
                )
            except (OSError, IOError):
                font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.WIDTH - text_width) // 2

        draw.text((x, y), text, font=font, fill=color)

    def cleanup_old_test_prints(self, max_age_hours: int = 24) -> int:
        """Clean up old test print files.

        Args:
            max_age_hours: Maximum age of test print files to keep

        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        for filepath in self.test_prints_dir.glob("test_pattern_*.jpg"):
            if filepath.stat().st_mtime < cutoff:
                try:
                    filepath.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {filepath}: {e}")

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old test print files")

        return deleted
