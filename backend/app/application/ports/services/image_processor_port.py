"""Image processor service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompositeOptions:
    """Options for composite image generation."""
    include_date: bool = True
    include_logo: bool = True
    background_color: str = "#FFFFFF"


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
