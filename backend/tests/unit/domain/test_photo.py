"""Unit tests for Photo entity."""

from datetime import datetime

import pytest

from app.domain.entities import Photo
from app.domain.exceptions import InvalidPhotoError


class TestPhotoCreation:
    """Tests for Photo creation."""

    def test_valid_photo_creation(self, session_id):
        """Valid photo is created successfully."""
        photo = Photo.create(
            session_id=session_id,
            index=0,
            file_path="/tmp/photo.jpg",
            thumbnail_path="/tmp/thumb.jpg",
            width=1920,
            height=1080,
            size_bytes=500000,
        )

        assert photo.id is not None
        assert photo.session_id == session_id
        assert photo.index == 0
        assert photo.file_path == "/tmp/photo.jpg"
        assert photo.width == 1920
        assert photo.height == 1080
        assert photo.captured_at is not None

    def test_create_with_custom_timestamp(self, session_id):
        """Photo can be created with custom timestamp."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)

        photo = Photo.create(
            session_id=session_id,
            index=0,
            file_path="/tmp/photo.jpg",
            thumbnail_path="/tmp/thumb.jpg",
            width=1920,
            height=1080,
            size_bytes=500000,
            captured_at=timestamp,
        )

        assert photo.captured_at == timestamp


class TestPhotoValidation:
    """Tests for Photo validation."""

    def test_invalid_index_negative(self, session_id):
        """Index cannot be negative."""
        with pytest.raises(InvalidPhotoError, match="Index must be 0-3"):
            Photo.create(
                session_id=session_id,
                index=-1,
                file_path="/tmp/photo.jpg",
                thumbnail_path="/tmp/thumb.jpg",
                width=1920,
                height=1080,
                size_bytes=500000,
            )

    def test_invalid_index_too_high(self, session_id):
        """Index cannot be greater than 3."""
        with pytest.raises(InvalidPhotoError, match="Index must be 0-3"):
            Photo.create(
                session_id=session_id,
                index=4,
                file_path="/tmp/photo.jpg",
                thumbnail_path="/tmp/thumb.jpg",
                width=1920,
                height=1080,
                size_bytes=500000,
            )

    def test_valid_indices(self, session_id):
        """Valid indices are 0, 1, 2, 3."""
        for index in [0, 1, 2, 3]:
            photo = Photo.create(
                session_id=session_id,
                index=index,
                file_path=f"/tmp/photo_{index}.jpg",
                thumbnail_path=f"/tmp/thumb_{index}.jpg",
                width=1920,
                height=1080,
                size_bytes=500000,
            )
            assert photo.index == index

    def test_photo_exceeds_max_size(self, session_id):
        """Photo size cannot exceed 5MB."""
        with pytest.raises(InvalidPhotoError, match="exceeds max size"):
            Photo.create(
                session_id=session_id,
                index=0,
                file_path="/tmp/photo.jpg",
                thumbnail_path="/tmp/thumb.jpg",
                width=1920,
                height=1080,
                size_bytes=6 * 1024 * 1024,  # 6MB
            )

    def test_photo_at_max_size(self, session_id):
        """Photo at exactly 5MB is valid."""
        photo = Photo.create(
            session_id=session_id,
            index=0,
            file_path="/tmp/photo.jpg",
            thumbnail_path="/tmp/thumb.jpg",
            width=1920,
            height=1080,
            size_bytes=5 * 1024 * 1024,  # Exactly 5MB
        )
        assert photo.size_bytes == 5 * 1024 * 1024

    def test_photo_width_below_minimum(self, session_id):
        """Width cannot be below 640 pixels."""
        with pytest.raises(InvalidPhotoError, match="below minimum"):
            Photo.create(
                session_id=session_id,
                index=0,
                file_path="/tmp/photo.jpg",
                thumbnail_path="/tmp/thumb.jpg",
                width=320,
                height=480,
                size_bytes=50000,
            )

    def test_photo_height_below_minimum(self, session_id):
        """Height cannot be below 480 pixels."""
        with pytest.raises(InvalidPhotoError, match="below minimum"):
            Photo.create(
                session_id=session_id,
                index=0,
                file_path="/tmp/photo.jpg",
                thumbnail_path="/tmp/thumb.jpg",
                width=640,
                height=240,
                size_bytes=50000,
            )

    def test_photo_at_minimum_dimensions(self, session_id):
        """Photo at exactly minimum dimensions is valid."""
        photo = Photo.create(
            session_id=session_id,
            index=0,
            file_path="/tmp/photo.jpg",
            thumbnail_path="/tmp/thumb.jpg",
            width=640,
            height=480,
            size_bytes=50000,
        )
        assert photo.width == 640
        assert photo.height == 480


class TestPhotoConstants:
    """Tests for Photo constants."""

    def test_max_size_constant(self):
        """MAX_SIZE_BYTES is 5MB."""
        assert Photo.MAX_SIZE_BYTES == 5 * 1024 * 1024

    def test_min_dimensions(self):
        """Minimum dimensions are 640x480."""
        assert Photo.MIN_WIDTH == 640
        assert Photo.MIN_HEIGHT == 480

    def test_valid_indices_constant(self):
        """Valid indices are 0-3."""
        assert Photo.VALID_INDICES == (0, 1, 2, 3)
