"""Image processing service for photo manipulation and composite generation."""

import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Service for image processing operations."""

    # 4x6 inch at 300 DPI
    COMPOSITE_WIDTH = 1200
    COMPOSITE_HEIGHT = 1800

    # 4-cut layout: 2x2 grid with padding
    PADDING = 20
    PHOTO_WIDTH = (COMPOSITE_WIDTH - 3 * PADDING) // 2
    PHOTO_HEIGHT = (COMPOSITE_HEIGHT - 4 * PADDING - 60) // 2  # 60px for date strip

    def __init__(self):
        self.thumbnail_size = settings.thumbnail_size
        self.composite_quality = settings.composite_quality
        self.photo_quality = settings.photo_quality

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

    def validate_image(
        self, image_data: bytes
    ) -> Tuple[bool, str, Optional[Tuple[int, int]]]:
        """Validate image data.

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
    ) -> bytes:
        """Create a 4-cut composite image.

        Args:
            photos: List of 4 photo image bytes
            include_date: Whether to add date stamp
            include_logo: Whether to add logo (not implemented yet)
            date_text: Custom date text, defaults to current date

        Returns:
            Composite image as JPEG bytes
        """
        if len(photos) != 4:
            raise ValueError(f"Expected 4 photos, got {len(photos)}")

        # Create white canvas
        composite = Image.new(
            "RGB", (self.COMPOSITE_WIDTH, self.COMPOSITE_HEIGHT), "white"
        )

        # Calculate positions for 2x2 grid
        positions = [
            (self.PADDING, self.PADDING),  # Top-left
            (self.PADDING * 2 + self.PHOTO_WIDTH, self.PADDING),  # Top-right
            (self.PADDING, self.PADDING * 2 + self.PHOTO_HEIGHT),  # Bottom-left
            (
                self.PADDING * 2 + self.PHOTO_WIDTH,
                self.PADDING * 2 + self.PHOTO_HEIGHT,
            ),  # Bottom-right
        ]

        # Place each photo
        for i, (photo_data, pos) in enumerate(zip(photos, positions)):
            try:
                photo = Image.open(io.BytesIO(photo_data))
                # Resize and crop to fit
                photo = self._resize_and_crop(
                    photo, (self.PHOTO_WIDTH, self.PHOTO_HEIGHT)
                )
                composite.paste(photo, pos)
            except Exception as e:
                logger.error(f"Failed to process photo {i}: {e}")
                raise

        # Add date stamp
        if include_date:
            date_text = date_text or datetime.now().strftime("%Y.%m.%d")
            self._add_date_stamp(composite, date_text)

        # Add logo (placeholder for future implementation)
        if include_logo:
            # TODO: Implement logo addition
            pass

        # Save to bytes
        output = io.BytesIO()
        composite.save(output, format="JPEG", quality=self.composite_quality)
        output.seek(0)

        logger.info("Created composite image")
        return output.getvalue()

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

    def _add_date_stamp(self, img: Image.Image, date_text: str) -> None:
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

        # Calculate position (center bottom)
        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.COMPOSITE_WIDTH - text_width) // 2
        y = self.COMPOSITE_HEIGHT - 50

        # Draw text with slight shadow for readability
        draw.text((x + 2, y + 2), date_text, font=font, fill="#888888")
        draw.text((x, y), date_text, font=font, fill="#333333")

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
