"""Image processing service for photo manipulation and composite generation."""

import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import aiofiles
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path

from ...application.ports.services.image_processor_port import (
    CompositeOptions, CompositeResult, FrameType, ImageProcessorPort)
from ...domain.value_objects import LayoutType

# Assets directory path
ASSETS_DIR = Path(__file__).parent.parent / "assets"
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ImageProcessor(ImageProcessorPort):
    """Service for image processing operations."""

    # 4x6 inch at 300 DPI
    COMPOSITE_WIDTH = 1200
    COMPOSITE_HEIGHT = 1800

    # Standardized frame template configurations
    # All frames use IDENTICAL photo sizing, gaps, and text positioning for consistency
    # Only visual styling (background, corners, effects) differs between frames

    # Standard values for all frames
    STANDARD_PADDING = 50  # Increased padding = smaller photos
    STANDARD_PHOTO_GAP = 30  # Larger gap between photos
    STANDARD_BOTTOM_MARGIN = 200  # More space for custom text + date
    STANDARD_CORNER_RADIUS = 12

    FRAME_CONFIGS = {
        FrameType.CLASSIC: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": 0,  # Classic has no rounded corners
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.FILM_STRIP: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": 0,
            "has_film_holes": True,
            "background_color": "#1A1A1A",
        },
        FrameType.POLAROID: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": 0,
            "has_film_holes": False,
            "background_color": "#FAFAFA",
        },
        FrameType.MINIMAL: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": 0,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.ROUNDED: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.RWANDA_DIAGONAL: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "is_diagonal_gradient": True,
        },
        # Rwanda mission background templates
        FrameType.RWANDA_GRID_1X4: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "use_background_image": True,
            "background_image": "rwanda-grid-1x4.png",
        },
        FrameType.RWANDA_MISSION_1: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "use_background_image": True,
            "background_image": "rwanda-full-grid-1.png",
        },
        FrameType.RWANDA_MISSION_2: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "use_background_image": True,
            "background_image": "rwanda-full-grid-2.png",
        },
        FrameType.RWANDA_MISSION_3: {
            "padding": STANDARD_PADDING,
            "photo_gap": STANDARD_PHOTO_GAP,
            "bottom_margin": STANDARD_BOTTOM_MARGIN,
            "corner_radius": STANDARD_CORNER_RADIUS,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "use_background_image": True,
            "background_image": "rwanda-full-grid-3.png",
        },
    }

    # Standardized text sizes (larger for better visibility)
    CUSTOM_TEXT_FONT_SIZE = 48  # For custom text (2x2 layout)
    CUSTOM_TEXT_1X4_FONT_SIZE = 42  # For custom text (1x4 layout)
    DATE_FONT_SIZE = 40  # For date stamp (2x2 layout) - smaller than custom text
    DATE_1X4_FONT_SIZE = 36  # For date stamp (1x4 layout) - smaller than custom text

    # Rwanda flag colors
    RWANDA_COLORS = {
        "blue": "#00A1DE",
        "yellow": "#FAD201",
        "green": "#20603D",
    }

    def __init__(self):
        self.thumbnail_size = settings.thumbnail_size
        self.composite_quality = settings.composite_quality
        self.photo_quality = settings.photo_quality

    def _get_frame_config(self, frame_type: FrameType) -> dict:
        """Get configuration for a specific frame type."""
        return self.FRAME_CONFIGS.get(frame_type, self.FRAME_CONFIGS[FrameType.CLASSIC])

    def _calculate_photo_dimensions(self, frame_config: dict) -> Tuple[int, int]:
        """Calculate photo dimensions based on frame configuration."""
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        bottom_margin = frame_config["bottom_margin"]

        # Calculate available space for photos
        available_width = self.COMPOSITE_WIDTH - (2 * padding) - photo_gap
        available_height = self.COMPOSITE_HEIGHT - (2 * padding) - photo_gap - bottom_margin

        photo_width = available_width // 2
        photo_height = available_height // 2

        return photo_width, photo_height

    def _calculate_photo_positions(
        self, frame_config: dict, photo_width: int, photo_height: int
    ) -> List[Tuple[int, int]]:
        """Calculate positions for 4 photos in 2x2 grid."""
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]

        return [
            (padding, padding),  # Top-left
            (padding + photo_width + photo_gap, padding),  # Top-right
            (padding, padding + photo_height + photo_gap),  # Bottom-left
            (padding + photo_width + photo_gap, padding + photo_height + photo_gap),  # Bottom-right
        ]

    def _calculate_1x4_dimensions(self, frame_config: dict) -> Tuple[int, int]:
        """Calculate photo dimensions for 1x4 strip layout (two strips side-by-side).

        Each strip contains 4 landscape photos stacked vertically.
        Photos should be wider than tall to look good in this layout.
        """
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        bottom_margin = frame_config["bottom_margin"]
        strip_gap = 24  # Gap between two strips

        # Two strips side by side
        available_width = self.COMPOSITE_WIDTH - (2 * padding) - strip_gap
        strip_width = available_width // 2
        photo_width = strip_width - 8  # Small inner margin

        # Four photos stacked vertically
        available_height = self.COMPOSITE_HEIGHT - (2 * padding) - (3 * photo_gap) - bottom_margin
        photo_height = available_height // 4

        return photo_width, photo_height

    def _calculate_1x4_positions(
        self, frame_config: dict, photo_width: int, photo_height: int
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Calculate positions for 1x4 layout (returns left and right positions for each photo).

        Returns list of tuples: [(left_pos, right_pos), ...]
        """
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        strip_gap = 24

        available_width = self.COMPOSITE_WIDTH - (2 * padding) - strip_gap
        strip_width = available_width // 2

        # Center photos within each strip
        left_x = padding + (strip_width - photo_width) // 2
        right_x = padding + strip_width + strip_gap + (strip_width - photo_width) // 2

        positions = []
        for i in range(4):
            y = padding + i * (photo_height + photo_gap)
            positions.append(((left_x, y), (right_x, y)))

        return positions

    def create_thumbnail(self, image_data: bytes) -> Tuple[bytes, int, int]:
        """Create a thumbnail from image data.

        Returns: (thumbnail_data, original_width, original_height)
        """
        img = Image.open(io.BytesIO(image_data))
        original_size = img.size

        # Convert RGBA to RGB (JPEG doesn't support alpha channel)
        if img.mode == "RGBA":
            img = img.convert("RGB")

        # Create thumbnail maintaining aspect ratio
        img.thumbnail(
            (self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS
        )

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85)
        output.seek(0)

        return output.getvalue(), original_size[0], original_size[1]

    def validate_image_bytes(
        self, image_data: bytes
    ) -> Tuple[bool, str, Optional[Tuple[int, int]]]:
        """Validate image data from bytes (internal method).

        Returns: (is_valid, error_message, dimensions)
        """
        try:
            img = Image.open(io.BytesIO(image_data))

            # Check format
            if img.format not in ("JPEG", "JPG"):
                return False, "Image must be JPEG format", None

            # Check dimensions
            width, height = img.size
            if width < 640 or height < 480:
                return (
                    False,
                    f"Image too small: {width}x{height}, minimum 640x480",
                    None,
                )

            # Check file size (already in bytes)
            if len(image_data) > settings.max_photo_size_bytes:
                return False, f"Image too large: {len(image_data)} bytes", None

            return True, "", (width, height)

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False, f"Invalid image data: {str(e)}", None

    def create_composite(
        self,
        photos: List[bytes],
        include_date: bool = True,
        include_logo: bool = False,
        date_text: Optional[str] = None,
        frame_type: FrameType = FrameType.CLASSIC,
        layout_type: LayoutType = LayoutType.GRID_2X2,
        include_custom_text: bool = True,
        custom_text: Optional[str] = None,
    ) -> bytes:
        """Create a composite image.

        Args:
            photos: List of photo image bytes (1 for 1x1, 4 for 2x2/1x4)
            include_date: Whether to add date stamp
            include_logo: Whether to add logo (not implemented yet)
            date_text: Custom date text, defaults to current date
            frame_type: Frame template to use
            layout_type: Layout arrangement (1x1 single, 2x2 grid, or 1x4 strip)
            include_custom_text: Whether to add custom text (e.g., "2026 Somang Youth")
            custom_text: Custom text to display, defaults to mission text

        Returns:
            Composite image as JPEG bytes
        """
        # Validate photo count based on layout
        expected_count = layout_type.required_photos
        if len(photos) != expected_count:
            raise ValueError(f"Expected {expected_count} photos for {layout_type.value} layout, got {len(photos)}")

        # Default custom text
        if custom_text is None:
            custom_text = "2026 Somang Youth\nRwanda missionary"

        # Route to appropriate layout generator
        if layout_type == LayoutType.SINGLE_1X1:
            return self._create_1x1_composite(
                photos, include_date, include_logo, date_text, frame_type,
                include_custom_text, custom_text
            )
        elif layout_type == LayoutType.STRIP_1X4:
            return self._create_1x4_composite(
                photos, include_date, include_logo, date_text, frame_type,
                include_custom_text, custom_text
            )
        else:
            return self._create_2x2_composite(
                photos, include_date, include_logo, date_text, frame_type,
                include_custom_text, custom_text
            )

    def _load_background_image(self, image_name: str) -> Optional[Image.Image]:
        """Load and resize a background image from assets to fill the entire canvas.

        Uses 'cover' mode: scales the image to fill the entire area while
        maintaining aspect ratio, then center-crops any overflow.
        """
        try:
            image_path = ASSETS_DIR / image_name
            if not image_path.exists():
                logger.warning(f"Background image not found: {image_path}")
                return None

            bg_img = Image.open(image_path)

            # Convert to RGB if necessary (do this first to avoid issues)
            if bg_img.mode != "RGB":
                bg_img = bg_img.convert("RGB")

            # Calculate scale factor to COVER the target area (fill completely)
            img_width, img_height = bg_img.size
            target_width, target_height = self.COMPOSITE_WIDTH, self.COMPOSITE_HEIGHT

            # Scale to cover: use the larger scale factor so image fills entire area
            scale = max(target_width / img_width, target_height / img_height)

            # Resize maintaining aspect ratio
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center crop to exact target dimensions
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            bg_img = bg_img.crop((left, top, right, bottom))

            return bg_img
        except Exception as e:
            logger.error(f"Failed to load background image {image_name}: {e}")
            return None

    def _create_2x2_composite(
        self,
        photos: List[bytes],
        include_date: bool,
        include_logo: bool,
        date_text: Optional[str],
        frame_type: FrameType,
        include_custom_text: bool = True,
        custom_text: Optional[str] = None,
    ) -> bytes:
        """Create a 2x2 grid composite image (original layout)."""
        # Get frame configuration
        frame_config = self._get_frame_config(frame_type)
        photo_width, photo_height = self._calculate_photo_dimensions(frame_config)
        positions = self._calculate_photo_positions(frame_config, photo_width, photo_height)

        # Create canvas with frame background color
        bg_color = frame_config["background_color"]
        composite = Image.new(
            "RGB", (self.COMPOSITE_WIDTH, self.COMPOSITE_HEIGHT), bg_color
        )

        # Load background image if configured
        if frame_config.get("use_background_image"):
            bg_image_name = frame_config.get("background_image")
            if bg_image_name:
                bg_img = self._load_background_image(bg_image_name)
                if bg_img:
                    composite.paste(bg_img, (0, 0))

        # Apply diagonal gradient background for Rwanda style
        elif frame_config.get("is_diagonal_gradient"):
            try:
                self._draw_rwanda_diagonal_background_fast(composite)
            except ImportError:
                # Fallback if numpy not available
                self._draw_rwanda_diagonal_background(composite)

        # Add film strip holes if applicable
        if frame_config["has_film_holes"]:
            self._add_film_holes(composite)

        # Place each photo
        corner_radius = frame_config["corner_radius"]
        for i, (photo_data, pos) in enumerate(zip(photos, positions)):
            try:
                photo = Image.open(io.BytesIO(photo_data))
                # Resize and crop to fit
                photo = self._resize_and_crop(photo, (photo_width, photo_height))

                # Apply rounded corners if needed
                if corner_radius > 0:
                    photo = self._apply_rounded_corners(photo, corner_radius)
                    # Use alpha composite for rounded corners
                    composite.paste(photo, pos, photo if photo.mode == "RGBA" else None)
                else:
                    composite.paste(photo, pos)
            except Exception as e:
                logger.error(f"Failed to process photo {i}: {e}")
                raise

        # Determine text colors based on background
        dark_bg_frames = (
            FrameType.FILM_STRIP, FrameType.RWANDA_DIAGONAL,
            FrameType.RWANDA_MISSION_1, FrameType.RWANDA_MISSION_2
        )
        if frame_type in dark_bg_frames:
            text_color = "#FFFFFF"
            shadow_color = "#000000"
        else:
            text_color = "#333333"
            shadow_color = "#888888"

        # Add custom text if enabled (above date)
        if include_custom_text and custom_text:
            self._add_custom_text_2x2(
                composite, custom_text, frame_config, text_color, shadow_color
            )

        # Add date stamp
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d %H:%M")
            self._add_date_stamp(
                composite, date_text, frame_config, text_color, shadow_color,
                has_custom_text=include_custom_text and bool(custom_text)
            )

        # Add logo (placeholder for future implementation)
        if include_logo:
            # TODO: Implement logo addition
            pass

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="JPEG", quality=self.composite_quality)
        output.seek(0)

        logger.info(f"Created 2x2 composite image with frame type: {frame_type.value}")
        return output.getvalue()

    def _create_1x4_composite(
        self,
        photos: List[bytes],
        include_date: bool,
        include_logo: bool,
        date_text: Optional[str],
        frame_type: FrameType,
        include_custom_text: bool = True,
        custom_text: Optional[str] = None,
    ) -> bytes:
        """Create a 1x4 strip composite image (two identical strips side-by-side)."""
        # Get frame configuration
        frame_config = self._get_frame_config(frame_type)
        photo_width, photo_height = self._calculate_1x4_dimensions(frame_config)
        positions = self._calculate_1x4_positions(frame_config, photo_width, photo_height)

        # Create canvas with frame background color
        bg_color = frame_config["background_color"]
        composite = Image.new(
            "RGB", (self.COMPOSITE_WIDTH, self.COMPOSITE_HEIGHT), bg_color
        )

        # Load background image if configured
        if frame_config.get("use_background_image"):
            bg_image_name = frame_config.get("background_image")
            if bg_image_name:
                bg_img = self._load_background_image(bg_image_name)
                if bg_img:
                    composite.paste(bg_img, (0, 0))

        # Apply diagonal gradient background for Rwanda style
        elif frame_config.get("is_diagonal_gradient"):
            try:
                self._draw_rwanda_diagonal_background_fast(composite)
            except ImportError:
                # Fallback if numpy not available
                self._draw_rwanda_diagonal_background(composite)

        # Place each photo on both left and right strips (duplicated)
        corner_radius = frame_config["corner_radius"]
        for i, photo_data in enumerate(photos):
            try:
                photo = Image.open(io.BytesIO(photo_data))
                # Resize and crop to fit (landscape orientation)
                photo = self._resize_and_crop(photo, (photo_width, photo_height))

                # Apply rounded corners if needed
                if corner_radius > 0:
                    photo = self._apply_rounded_corners(photo, corner_radius)
                    mask = photo if photo.mode == "RGBA" else None
                    # Place on left strip
                    composite.paste(photo, positions[i][0], mask)
                    # Place on right strip (duplicate)
                    composite.paste(photo, positions[i][1], mask)
                else:
                    # Place on left strip
                    composite.paste(photo, positions[i][0])
                    # Place on right strip (duplicate)
                    composite.paste(photo, positions[i][1])
            except Exception as e:
                logger.error(f"Failed to process photo {i}: {e}")
                raise

        # Determine text colors based on background
        dark_bg_frames = (
            FrameType.FILM_STRIP, FrameType.RWANDA_DIAGONAL,
            FrameType.RWANDA_MISSION_1, FrameType.RWANDA_MISSION_2
        )
        if frame_type in dark_bg_frames:
            text_color = "#FFFFFF"
            shadow_color = "#000000"
        else:
            text_color = "#333333"
            shadow_color = "#888888"

        # Add custom text if enabled (above date, on both sides)
        if include_custom_text and custom_text:
            self._add_custom_text_1x4(
                composite, custom_text, frame_config, text_color, shadow_color
            )

        # Add date stamp (on both left and right strips)
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d %H:%M")
            self._add_date_stamp_1x4(
                composite, date_text, frame_config, text_color, shadow_color,
                has_custom_text=include_custom_text and bool(custom_text)
            )

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="JPEG", quality=self.composite_quality)
        output.seek(0)

        logger.info(f"Created 1x4 composite image with frame type: {frame_type.value}")
        return output.getvalue()

    def _calculate_1x1_dimensions(self, frame_config: dict) -> Tuple[int, int]:
        """Calculate photo dimensions for 1x1 single photo layout.

        The photo fills most of the canvas with minimal padding,
        leaving space at the bottom for text/date.
        """
        padding = frame_config["padding"]
        bottom_margin = frame_config["bottom_margin"]

        # Photo fills the available area
        photo_width = self.COMPOSITE_WIDTH - (2 * padding)
        photo_height = self.COMPOSITE_HEIGHT - (2 * padding) - bottom_margin

        return photo_width, photo_height

    def _create_1x1_composite(
        self,
        photos: List[bytes],
        include_date: bool,
        include_logo: bool,
        date_text: Optional[str],
        frame_type: FrameType,
        include_custom_text: bool = True,
        custom_text: Optional[str] = None,
    ) -> bytes:
        """Create a 1x1 single photo composite image (full page)."""
        # Get frame configuration
        frame_config = self._get_frame_config(frame_type)
        photo_width, photo_height = self._calculate_1x1_dimensions(frame_config)
        padding = frame_config["padding"]

        # Create canvas with frame background color
        bg_color = frame_config["background_color"]
        composite = Image.new(
            "RGB", (self.COMPOSITE_WIDTH, self.COMPOSITE_HEIGHT), bg_color
        )

        # Load background image if configured
        if frame_config.get("use_background_image"):
            bg_image_name = frame_config.get("background_image")
            if bg_image_name:
                bg_img = self._load_background_image(bg_image_name)
                if bg_img:
                    composite.paste(bg_img, (0, 0))

        # Apply diagonal gradient background for Rwanda style
        elif frame_config.get("is_diagonal_gradient"):
            try:
                self._draw_rwanda_diagonal_background_fast(composite)
            except ImportError:
                self._draw_rwanda_diagonal_background(composite)

        # Add film strip holes if applicable
        if frame_config["has_film_holes"]:
            self._add_film_holes(composite)

        # Place the single photo
        corner_radius = frame_config["corner_radius"]
        try:
            photo = Image.open(io.BytesIO(photos[0]))
            # Resize and crop to fit
            photo = self._resize_and_crop(photo, (photo_width, photo_height))

            # Apply rounded corners if needed
            if corner_radius > 0:
                photo = self._apply_rounded_corners(photo, corner_radius)
                composite.paste(photo, (padding, padding), photo if photo.mode == "RGBA" else None)
            else:
                composite.paste(photo, (padding, padding))
        except Exception as e:
            logger.error(f"Failed to process photo: {e}")
            raise

        # Determine text colors based on background
        dark_bg_frames = (
            FrameType.FILM_STRIP, FrameType.RWANDA_DIAGONAL,
            FrameType.RWANDA_MISSION_1, FrameType.RWANDA_MISSION_2
        )
        if frame_type in dark_bg_frames:
            text_color = "#FFFFFF"
            shadow_color = "#000000"
        else:
            text_color = "#333333"
            shadow_color = "#888888"

        # Add custom text if enabled
        if include_custom_text and custom_text:
            self._add_custom_text_1x1(
                composite, custom_text, frame_config, text_color, shadow_color
            )

        # Add date stamp
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d %H:%M")
            self._add_date_stamp_1x1(
                composite, date_text, frame_config, text_color, shadow_color,
                has_custom_text=include_custom_text and bool(custom_text)
            )

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="JPEG", quality=self.composite_quality)
        output.seek(0)

        logger.info(f"Created 1x1 composite image with frame type: {frame_type.value}")
        return output.getvalue()

    def _add_custom_text_1x1(
        self,
        img: Image.Image,
        custom_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
    ) -> None:
        """Add custom text to bottom of 1x1 composite image."""
        draw = ImageDraw.Draw(img)

        # Use 2x2 font size for 1x1 layout
        font = self._load_font(self.CUSTOM_TEXT_FONT_SIZE)

        # Calculate Y position
        padding = frame_config["padding"]
        photo_height = self._calculate_1x1_dimensions(frame_config)[1]
        photos_bottom = padding + photo_height

        # Split text into lines
        lines = custom_text.split('\n')
        line_height = int(self.CUSTOM_TEXT_FONT_SIZE * 1.3)

        # Start position for custom text
        start_y = photos_bottom + 20

        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.COMPOSITE_WIDTH - text_width) // 2
            y = start_y + line_idx * line_height

            # Draw text with shadow
            draw.text((x + 2, y + 2), line, font=font, fill=shadow_color)
            draw.text((x, y), line, font=font, fill=text_color)

    def _add_date_stamp_1x1(
        self,
        img: Image.Image,
        date_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
        has_custom_text: bool = False,
    ) -> None:
        """Add date stamp to bottom of 1x1 composite image."""
        draw = ImageDraw.Draw(img)

        # Use 2x2 date font size
        font = self._load_font(self.DATE_FONT_SIZE)

        # Calculate position
        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.COMPOSITE_WIDTH - text_width) // 2

        padding = frame_config["padding"]
        bottom_margin = frame_config["bottom_margin"]
        photo_height = self._calculate_1x1_dimensions(frame_config)[1]
        photos_bottom = padding + photo_height

        if has_custom_text:
            # Date goes at the bottom, below custom text
            y = photos_bottom + bottom_margin - text_height - 15
        else:
            y = photos_bottom + (bottom_margin - text_height) // 2

        # Draw text with slight shadow
        draw.text((x + 2, y + 2), date_text, font=font, fill=shadow_color)
        draw.text((x, y), date_text, font=font, fill=text_color)

    def _add_date_stamp_1x4(
        self,
        img: Image.Image,
        date_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
        has_custom_text: bool = False,
    ) -> None:
        """Add date stamp to bottom of 1x4 composite image (on both left and right strips)."""
        draw = ImageDraw.Draw(img)

        # Use standardized font size
        font = self._load_font(self.DATE_1X4_FONT_SIZE)

        # Calculate strip positions
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        strip_gap = 24
        available_width = self.COMPOSITE_WIDTH - (2 * padding) - strip_gap
        strip_width = available_width // 2

        # Calculate Y position
        photo_width, photo_height = self._calculate_1x4_dimensions(frame_config)
        photos_bottom = padding + (4 * photo_height) + (3 * photo_gap)
        bottom_margin = frame_config["bottom_margin"]

        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # If custom text is present, date goes below it
        if has_custom_text:
            # Custom text takes upper portion, date takes lower portion
            y = photos_bottom + bottom_margin - text_height - 15
        else:
            y = photos_bottom + (bottom_margin - text_height) // 2

        # Draw on LEFT strip
        left_center_x = padding + strip_width // 2
        left_x = left_center_x - text_width // 2
        draw.text((left_x + 1, y + 1), date_text, font=font, fill=shadow_color)
        draw.text((left_x, y), date_text, font=font, fill=text_color)

        # Draw on RIGHT strip
        right_center_x = padding + strip_width + strip_gap + strip_width // 2
        right_x = right_center_x - text_width // 2
        draw.text((right_x + 1, y + 1), date_text, font=font, fill=shadow_color)
        draw.text((right_x, y), date_text, font=font, fill=text_color)

    def _add_custom_text_1x4(
        self,
        img: Image.Image,
        custom_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
    ) -> None:
        """Add custom text to bottom of 1x4 composite image (on both strips)."""
        draw = ImageDraw.Draw(img)

        # Use standardized font size for custom text
        font = self._load_font(self.CUSTOM_TEXT_1X4_FONT_SIZE)

        # Calculate strip positions
        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        strip_gap = 24
        available_width = self.COMPOSITE_WIDTH - (2 * padding) - strip_gap
        strip_width = available_width // 2

        # Calculate Y position (above date)
        photo_width, photo_height = self._calculate_1x4_dimensions(frame_config)
        photos_bottom = padding + (4 * photo_height) + (3 * photo_gap)

        # Split text into lines
        lines = custom_text.split('\n')
        line_height = int(self.CUSTOM_TEXT_1X4_FONT_SIZE * 1.3)  # Dynamic line height based on font size

        # Start position for custom text
        start_y = photos_bottom + 20

        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            y = start_y + line_idx * line_height

            # Draw on LEFT strip
            left_center_x = padding + strip_width // 2
            left_x = left_center_x - text_width // 2
            draw.text((left_x + 1, y + 1), line, font=font, fill=shadow_color)
            draw.text((left_x, y), line, font=font, fill=text_color)

            # Draw on RIGHT strip
            right_center_x = padding + strip_width + strip_gap + strip_width // 2
            right_x = right_center_x - text_width // 2
            draw.text((right_x + 1, y + 1), line, font=font, fill=shadow_color)
            draw.text((right_x, y), line, font=font, fill=text_color)

    def _draw_rwanda_diagonal_background(self, img: Image.Image) -> None:
        """Draw Rwanda flag diagonal gradient background.

        Creates a diagonal gradient from top-left to bottom-right
        with blue -> yellow -> green bands.
        """
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # Rwanda colors
        blue = (0, 161, 222)    # #00A1DE
        yellow = (250, 210, 1)  # #FAD201
        green = (32, 96, 61)    # #20603D

        # Diagonal bands - from top-left to bottom-right
        # Total diagonal distance
        total_diag = width + height

        # Define band positions (as fraction of diagonal)
        # Blue: 0-35%, Yellow: 35-50%, Green: 50-100%
        blue_end = 0.35
        yellow_end = 0.50

        for y in range(height):
            for x in range(width):
                # Calculate position along diagonal (0 to 1)
                diag_pos = (x + y) / total_diag

                if diag_pos < blue_end:
                    # Blue zone with slight gradient
                    color = blue
                elif diag_pos < yellow_end:
                    # Yellow zone (narrow band like the sun ray)
                    color = yellow
                else:
                    # Green zone
                    color = green

                draw.point((x, y), fill=color)

    def _draw_rwanda_diagonal_background_fast(self, img: Image.Image) -> None:
        """Draw Rwanda flag diagonal gradient background (optimized version).

        Uses numpy-like approach with PIL for better performance.
        """
        import numpy as np

        width, height = img.size

        # Rwanda colors
        blue = np.array([0, 161, 222], dtype=np.uint8)    # #00A1DE
        yellow = np.array([250, 210, 1], dtype=np.uint8)  # #FAD201
        green = np.array([32, 96, 61], dtype=np.uint8)    # #20603D

        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:height, 0:width]

        # Calculate diagonal position (0 to 1)
        total_diag = width + height
        diag_pos = (x_coords + y_coords) / total_diag

        # Create output array
        output = np.zeros((height, width, 3), dtype=np.uint8)

        # Blue zone: 0 - 0.35
        blue_mask = diag_pos < 0.35
        output[blue_mask] = blue

        # Yellow zone: 0.35 - 0.50
        yellow_mask = (diag_pos >= 0.35) & (diag_pos < 0.50)
        output[yellow_mask] = yellow

        # Green zone: 0.50 - 1.0
        green_mask = diag_pos >= 0.50
        output[green_mask] = green

        # Convert numpy array to PIL image and paste
        gradient_img = Image.fromarray(output, mode='RGB')
        img.paste(gradient_img)

    def _add_film_holes(self, img: Image.Image) -> None:
        """Add film strip sprocket holes to the edges."""
        draw = ImageDraw.Draw(img)
        hole_width = 20
        hole_height = 30
        hole_spacing = 60
        margin = 10

        # Draw holes on left and right edges
        for y in range(30, self.COMPOSITE_HEIGHT - 30, hole_spacing):
            # Left side
            draw.rounded_rectangle(
                [margin, y, margin + hole_width, y + hole_height],
                radius=5,
                fill="#2A2A2A",
            )
            # Right side
            draw.rounded_rectangle(
                [
                    self.COMPOSITE_WIDTH - margin - hole_width,
                    y,
                    self.COMPOSITE_WIDTH - margin,
                    y + hole_height,
                ],
                radius=5,
                fill="#2A2A2A",
            )

    def _apply_rounded_corners(
        self, img: Image.Image, radius: int
    ) -> Image.Image:
        """Apply rounded corners to an image."""
        # Convert to RGBA for transparency
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Create mask with rounded corners
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)

        # Apply mask
        img.putalpha(mask)
        return img

    def _resize_and_crop(
        self, img: Image.Image, target_size: Tuple[int, int]
    ) -> Image.Image:
        """Resize and center-crop image to target size."""
        target_width, target_height = target_size
        img_width, img_height = img.size

        # Calculate scaling factor to cover target area
        scale = max(target_width / img_width, target_height / img_height)

        # Resize
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        return img.crop((left, top, right, bottom))

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load a bold font with the specified size from project assets."""
        # Use bundled Pretendard font from assets directory
        font_path = ASSETS_DIR / "Pretendard-Bold.ttf"
        try:
            return ImageFont.truetype(str(font_path), size)
        except OSError:
            logger.warning(f"Could not load font from {font_path}, trying fallback fonts")
            # Fallback to other bundled or system fonts
            fallback_paths = [
                ASSETS_DIR / "ArialBold.ttf",  # Bundled fallback
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "C:/Windows/Fonts/arialbd.ttf",  # Windows
            ]
            for path in fallback_paths:
                try:
                    return ImageFont.truetype(str(path), size)
                except OSError:
                    continue
            logger.error(f"Could not load any font with size {size}")
            return ImageFont.load_default()

    def _add_custom_text_2x2(
        self,
        img: Image.Image,
        custom_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
    ) -> None:
        """Add custom text to bottom of 2x2 composite image (above date)."""
        draw = ImageDraw.Draw(img)

        # Use standardized font size for custom text
        font = self._load_font(self.CUSTOM_TEXT_FONT_SIZE)

        # Calculate Y position
        padding = frame_config["padding"]
        photo_height = self._calculate_photo_dimensions(frame_config)[1]
        photos_bottom = padding + (photo_height * 2) + frame_config["photo_gap"]

        # Split text into lines
        lines = custom_text.split('\n')
        line_height = int(self.CUSTOM_TEXT_FONT_SIZE * 1.3)  # Dynamic line height based on font size

        # Start position for custom text (at top of bottom margin area)
        start_y = photos_bottom + 20

        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.COMPOSITE_WIDTH - text_width) // 2
            y = start_y + line_idx * line_height

            # Draw text with shadow
            draw.text((x + 2, y + 2), line, font=font, fill=shadow_color)
            draw.text((x, y), line, font=font, fill=text_color)

    def _add_date_stamp(
        self,
        img: Image.Image,
        date_text: str,
        frame_config: Optional[dict] = None,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
        has_custom_text: bool = False,
    ) -> None:
        """Add date stamp to bottom of image."""
        draw = ImageDraw.Draw(img)

        # Use standardized font size for date
        font = self._load_font(self.DATE_FONT_SIZE)

        # Calculate position (center bottom, respecting bottom margin)
        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.COMPOSITE_WIDTH - text_width) // 2

        # Position text in the center of bottom margin area
        if frame_config:
            bottom_margin = frame_config["bottom_margin"]
            padding = frame_config["padding"]
            photo_height = self._calculate_photo_dimensions(frame_config)[1]
            photos_bottom = padding + (photo_height * 2) + frame_config["photo_gap"]

            if has_custom_text:
                # Date goes at the bottom, below custom text
                y = photos_bottom + bottom_margin - text_height - 15
            else:
                y = photos_bottom + (bottom_margin - text_height) // 2
        else:
            y = self.COMPOSITE_HEIGHT - 60

        # Draw text with slight shadow for readability
        draw.text((x + 2, y + 2), date_text, font=font, fill=shadow_color)
        draw.text((x, y), date_text, font=font, fill=text_color)

    def compress_image(self, image_data: bytes, quality: int = 85) -> bytes:
        """Compress an image to reduce file size."""
        img = Image.open(io.BytesIO(image_data))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)
        return output.getvalue()

    def get_image_dimensions(self, image_data: bytes) -> Tuple[int, int]:
        """Get image dimensions."""
        img = Image.open(io.BytesIO(image_data))
        return img.size

    # ─────────────────────────────────────────────────────────────────
    # ImageProcessorPort interface implementation
    # ─────────────────────────────────────────────────────────────────

    async def generate_composite(
        self,
        photo_paths: List[str],
        output_path: str,
        options: Optional[CompositeOptions] = None,
    ) -> CompositeResult:
        """Generate a 4-cut composite image from individual photos (Port interface)."""
        try:
            # Read all photos
            photos_data = []
            for path in photo_paths:
                async with aiofiles.open(path, "rb") as f:
                    photos_data.append(await f.read())

            # Create composite using existing method
            opts = options or CompositeOptions()
            composite_data = self.create_composite(
                photos=photos_data,
                include_date=opts.include_date,
                include_logo=opts.include_logo,
                frame_type=opts.frame_type,
                layout_type=opts.layout_type,
                include_custom_text=opts.include_custom_text,
                custom_text=opts.custom_text,
            )

            # Write to output path
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(composite_data)

            return CompositeResult(success=True, output_path=output_path)

        except Exception as e:
            logger.error(f"Failed to generate composite: {e}")
            return CompositeResult(success=False, error_message=str(e))

    async def generate_thumbnail(
        self, source_path: str, output_path: str, max_size: int = 300
    ) -> str:
        """Generate a thumbnail from an image (Port interface)."""
        # Read source image
        async with aiofiles.open(source_path, "rb") as f:
            image_data = await f.read()

        # Generate thumbnail using existing method
        old_size = self.thumbnail_size
        self.thumbnail_size = max_size
        thumbnail_data, _, _ = self.create_thumbnail(image_data)
        self.thumbnail_size = old_size

        # Write to output path
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(thumbnail_data)

        return output_path

    async def generate_test_pattern(self, pattern_type: str, output_path: str) -> str:
        """Generate a test pattern image for printer calibration (Port interface)."""
        # Import test pattern generator
        from .test_pattern import TestPatternGenerator, TestPatternType

        generator = TestPatternGenerator()

        # Convert string to TestPatternType enum
        try:
            pattern_enum = TestPatternType(pattern_type)
        except ValueError:
            # Default to FULL if invalid pattern type
            pattern_enum = TestPatternType.FULL

        # generate() returns the file path, not bytes
        generated_path = generator.generate(pattern_enum)

        if generated_path is None:
            raise RuntimeError(f"Failed to generate test pattern: {pattern_type}")

        # Copy to output path if different
        if generated_path != output_path:
            import shutil
            shutil.copy(generated_path, output_path)

        return output_path

    async def validate_image(self, image_path: str) -> bool:
        """Validate that an image file is readable and properly formatted (Port interface)."""
        try:
            async with aiofiles.open(image_path, "rb") as f:
                image_data = await f.read()

            is_valid, _, _ = self.validate_image_bytes(image_data)
            return is_valid

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False
