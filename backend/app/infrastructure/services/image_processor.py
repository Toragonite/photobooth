"""Image processing service for photo manipulation and composite generation."""

import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import aiofiles
from PIL import Image, ImageDraw, ImageFont

from ...application.ports.services.image_processor_port import (
    CompositeOptions, CompositeResult, FrameType, ImageProcessorPort, LayoutType)
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ImageProcessor(ImageProcessorPort):
    """Service for image processing operations."""

    # 4x6 inch at 300 DPI
    COMPOSITE_WIDTH = 1200
    COMPOSITE_HEIGHT = 1800

    # Frame template configurations
    # Each template defines: padding, photo_gap, bottom_margin, corner_radius, has_film_holes
    FRAME_CONFIGS = {
        FrameType.CLASSIC: {
            "padding": 20,
            "photo_gap": 20,
            "bottom_margin": 100,  # Increased from 60
            "corner_radius": 0,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.FILM_STRIP: {
            "padding": 40,
            "photo_gap": 15,
            "bottom_margin": 80,
            "corner_radius": 0,
            "has_film_holes": True,
            "background_color": "#1A1A1A",
        },
        FrameType.POLAROID: {
            "padding": 30,
            "photo_gap": 25,
            "bottom_margin": 150,  # Large bottom margin like real polaroid
            "corner_radius": 0,
            "has_film_holes": False,
            "background_color": "#FAFAFA",
        },
        FrameType.MINIMAL: {
            "padding": 8,
            "photo_gap": 8,
            "bottom_margin": 60,
            "corner_radius": 0,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.ROUNDED: {
            "padding": 25,
            "photo_gap": 20,
            "bottom_margin": 90,
            "corner_radius": 20,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
        },
        FrameType.RWANDA_DIAGONAL: {
            "padding": 30,
            "photo_gap": 20,
            "bottom_margin": 100,
            "corner_radius": 12,
            "has_film_holes": False,
            "background_color": "#FFFFFF",
            "is_diagonal_gradient": True,
        },
    }

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
    ) -> bytes:
        """Create a 4-cut composite image.

        Args:
            photos: List of 4 photo image bytes
            include_date: Whether to add date stamp
            include_logo: Whether to add logo (not implemented yet)
            date_text: Custom date text, defaults to current date
            frame_type: Frame template to use
            layout_type: Layout arrangement (2x2 grid or 1x4 strip)

        Returns:
            Composite image as JPEG bytes
        """
        if len(photos) != 4:
            raise ValueError(f"Expected 4 photos, got {len(photos)}")

        # Route to appropriate layout generator
        if layout_type == LayoutType.STRIP_1X4:
            return self._create_1x4_composite(
                photos, include_date, include_logo, date_text, frame_type
            )
        else:
            return self._create_2x2_composite(
                photos, include_date, include_logo, date_text, frame_type
            )

    def _create_2x2_composite(
        self,
        photos: List[bytes],
        include_date: bool,
        include_logo: bool,
        date_text: Optional[str],
        frame_type: FrameType,
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

        # Apply diagonal gradient background for Rwanda style
        if frame_config.get("is_diagonal_gradient"):
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

        # Add date stamp
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d")
            # White text for dark backgrounds
            if frame_type in (FrameType.FILM_STRIP, FrameType.RWANDA_DIAGONAL):
                text_color = "#FFFFFF"
                shadow_color = "#000000"
            else:
                text_color = "#333333"
                shadow_color = "#888888"
            self._add_date_stamp(composite, date_text, frame_config, text_color, shadow_color)

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

        # Apply diagonal gradient background for Rwanda style
        if frame_config.get("is_diagonal_gradient"):
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

        # Add date stamp (centered at bottom)
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d")
            # White text for dark backgrounds
            if frame_type in (FrameType.FILM_STRIP, FrameType.RWANDA_DIAGONAL):
                text_color = "#FFFFFF"
                shadow_color = "#000000"
            else:
                text_color = "#333333"
                shadow_color = "#888888"
            self._add_date_stamp_1x4(composite, date_text, frame_config, text_color, shadow_color)

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="JPEG", quality=self.composite_quality)
        output.seek(0)

        logger.info(f"Created 1x4 composite image with frame type: {frame_type.value}")
        return output.getvalue()

    def _add_date_stamp_1x4(
        self,
        img: Image.Image,
        date_text: str,
        frame_config: dict,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
    ) -> None:
        """Add date stamp to bottom of 1x4 composite image."""
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", 28)
            except OSError:
                font = ImageFont.load_default()

        # Calculate position (center bottom)
        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.COMPOSITE_WIDTH - text_width) // 2

        padding = frame_config["padding"]
        photo_gap = frame_config["photo_gap"]
        photo_width, photo_height = self._calculate_1x4_dimensions(frame_config)
        photos_bottom = padding + (4 * photo_height) + (3 * photo_gap)
        bottom_margin = frame_config["bottom_margin"]
        y = photos_bottom + (bottom_margin - text_height) // 2

        # Draw text with slight shadow for readability
        draw.text((x + 1, y + 1), date_text, font=font, fill=shadow_color)
        draw.text((x, y), date_text, font=font, fill=text_color)

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

    def _add_date_stamp(
        self,
        img: Image.Image,
        date_text: str,
        frame_config: Optional[dict] = None,
        text_color: str = "#333333",
        shadow_color: str = "#888888",
    ) -> None:
        """Add date stamp to bottom of image."""
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fall back to default
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
            )
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except OSError:
                font = ImageFont.load_default()

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
            y = photos_bottom + (bottom_margin - text_height) // 2
        else:
            y = self.COMPOSITE_HEIGHT - 50

        # Draw text with slight shadow for readability
        draw.text((x + 2, y + 2), date_text, font=font, fill=shadow_color)
        draw.text((x, y), date_text, font=font, fill=text_color)

    def compress_image(self, image_data: bytes, quality: int = 85) -> bytes:
        """Compress an image to reduce file size."""
        img = Image.open(io.BytesIO(image_data))
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
        from .test_pattern import TestPatternGenerator

        generator = TestPatternGenerator()
        pattern_data = generator.generate(pattern_type)

        # Write to output path
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(pattern_data)

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
