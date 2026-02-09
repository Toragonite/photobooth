"""Image processor service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FrameType(str, Enum):
    """Available frame templates for composite images."""
    CLASSIC = "classic"        # Simple white frame, minimal padding
    FILM_STRIP = "film_strip"  # Film strip style with sprocket holes
    POLAROID = "polaroid"      # Polaroid style with large bottom margin
    MINIMAL = "minimal"        # Edge-to-edge photos, thin borders
    ROUNDED = "rounded"        # Rounded corners on photos
    RWANDA_DIAGONAL = "rwanda_diagonal"  # Rwanda flag diagonal gradient
    # New Rwanda mission background templates
    RWANDA_GRID_2X2 = "rwanda_grid_2x2"      # Mountain + cross scenery (2x2)
    RWANDA_GRID_1X4 = "rwanda_grid_1x4"      # 4-panel Rwanda scenes (1x4)
    RWANDA_MISSION_1 = "rwanda_mission_1"    # Rwanda flag + mission theme
    RWANDA_MISSION_2 = "rwanda_mission_2"    # Rwanda flag wave pattern
    RWANDA_MISSION_3 = "rwanda_mission_3"    # Cross + landscape (2x2)


class LayoutType(str, Enum):
    """Photo layout arrangement types."""
    STRIP_1X4 = "1x4"   # 4 photos in vertical strip, duplicated side-by-side
    GRID_2X2 = "2x2"    # 4 photos in standard 2x2 grid


@dataclass
class CompositeOptions:
    """Options for composite image generation."""
    include_date: bool = True
    include_logo: bool = True
    include_custom_text: bool = True
    custom_text: str = "2026 Somang Youth\nRwanda missionary"
    background_color: str = "#FFFFFF"
    frame_type: FrameType = FrameType.CLASSIC
    layout_type: LayoutType = LayoutType.GRID_2X2
    bottom_margin: int = 60  # Extra margin at bottom for date/logo (in pixels)


@dataclass
class CompositeResult:
    """Result of composite generation."""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None


class ImageProcessorPort(ABC):
    """Abstract port for image processing operations."""

    @abstractmethod
    async def generate_composite(
        self,
        photo_paths: List[str],
        output_path: str,
        options: Optional[CompositeOptions] = None,
    ) -> CompositeResult:
        """Generate a 4-cut composite image from individual photos."""
        ...

    @abstractmethod
    async def generate_thumbnail(
        self, source_path: str, output_path: str, max_size: int = 300
    ) -> str:
        """Generate a thumbnail from an image."""
        ...

    @abstractmethod
    async def generate_test_pattern(self, pattern_type: str, output_path: str) -> str:
        """Generate a test pattern image for printer calibration."""
        ...

    @abstractmethod
    async def validate_image(self, image_path: str) -> bool:
        """Validate that an image file is readable and properly formatted."""
        ...
