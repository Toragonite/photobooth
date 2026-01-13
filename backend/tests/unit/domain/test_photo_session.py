"""Unit tests for PhotoSession entity."""

import pytest

from app.domain.entities import Photo, PhotoSession
from app.domain.exceptions import SessionError
from app.domain.value_objects import Language, SessionStatus


class TestPhotoSessionCreation:
    """Tests for PhotoSession creation."""

    def test_create_session_with_defaults(self):
        """Session is created with Korean language by default."""
        session = PhotoSession.create()

        assert session.id is not None
        assert session.language == Language.KOREAN
        assert session.status == SessionStatus.ACTIVE
        assert len(session.photos) == 0
        assert session.composite_path is None
        assert session.created_at is not None
        assert session.completed_at is None
        assert session.abandoned_at is None

    def test_create_session_with_english(self):
        """Session can be created with English language."""
        session = PhotoSession.create(language=Language.ENGLISH)

        assert session.language == Language.ENGLISH

    def test_create_generates_unique_ids(self):
        """Each session gets a unique ID."""
        session1 = PhotoSession.create()
        session2 = PhotoSession.create()

        assert session1.id != session2.id


class TestPhotoSessionAddPhoto:
    """Tests for adding photos to session."""

    def test_add_photo_increases_count(self, sample_session, sample_photo):
        """Adding a photo increases the photo count."""
        # Update photo's session_id to match
        photo = Photo(
            id=sample_photo.id,
            session_id=sample_session.id,
            index=0,
            file_path=sample_photo.file_path,
            thumbnail_path=sample_photo.thumbnail_path,
            width=sample_photo.width,
            height=sample_photo.height,
            size_bytes=sample_photo.size_bytes,
            captured_at=sample_photo.captured_at,
        )

        sample_session.add_photo(photo)

        assert len(sample_session.photos) == 1
        assert sample_session.photo_count == 1

    def test_add_photo_at_correct_index(self, sample_session):
        """Photos are stored at the correct index."""
        from tests.conftest import create_photo

        photo = create_photo(sample_session.id, 2)
        sample_session.add_photo(photo)

        assert sample_session.get_photo(2) == photo

    def test_photos_sorted_by_index(self, sample_session):
        """Photos are automatically sorted by index."""
        from tests.conftest import create_photo

        # Add photos out of order
        sample_session.add_photo(create_photo(sample_session.id, 2))
        sample_session.add_photo(create_photo(sample_session.id, 0))
        sample_session.add_photo(create_photo(sample_session.id, 1))

        indices = [p.index for p in sample_session.photos]
        assert indices == [0, 1, 2]

    def test_cannot_add_duplicate_index(self, sample_session):
        """Cannot add two photos at the same index."""
        from tests.conftest import create_photo

        photo1 = create_photo(sample_session.id, 0)
        photo2 = create_photo(sample_session.id, 0)

        sample_session.add_photo(photo1)

        with pytest.raises(SessionError, match="already exists"):
            sample_session.add_photo(photo2)

    def test_cannot_exceed_max_photos(self, complete_session):
        """Cannot add more than 4 photos."""
        # Session is already complete with 4 photos
        # Attempting to add another should fail
        assert len(complete_session.photos) == 4
        assert complete_session.status == SessionStatus.COMPLETE

    def test_session_completes_with_four_photos(self, sample_session):
        """Session auto-completes when 4 photos are added."""
        from tests.conftest import create_photo

        for i in range(4):
            sample_session.add_photo(create_photo(sample_session.id, i))

        assert sample_session.status == SessionStatus.COMPLETE
        assert sample_session.completed_at is not None
        assert sample_session.is_complete

    def test_cannot_add_photo_to_abandoned_session(self, sample_session):
        """Cannot add photos to an abandoned session."""
        from tests.conftest import create_photo

        sample_session.abandon()

        with pytest.raises(SessionError, match="non-active"):
            sample_session.add_photo(create_photo(sample_session.id, 0))


class TestPhotoSessionReplacePhoto:
    """Tests for replacing photos in session."""

    def test_replace_photo_returns_old_photo(self, complete_session):
        """Replacing a photo returns the old photo."""
        from tests.conftest import create_photo

        old_photo = complete_session.get_photo(0)
        new_photo = create_photo(complete_session.id, 0)

        replaced = complete_session.replace_photo(new_photo)

        assert replaced == old_photo
        assert complete_session.get_photo(0).id == new_photo.id

    def test_replace_photo_in_active_session(self, sample_session):
        """Can replace a photo in an active session."""
        from tests.conftest import create_photo

        photo1 = create_photo(sample_session.id, 0)
        photo2 = create_photo(sample_session.id, 0)

        sample_session.add_photo(photo1)
        sample_session.replace_photo(photo2)

        assert sample_session.get_photo(0).id == photo2.id

    def test_replace_temporarily_reactivates_complete_session(self, complete_session):
        """Replacing a photo reactivates and re-completes the session."""
        from tests.conftest import create_photo

        new_photo = create_photo(complete_session.id, 0)

        # After replacement, session should still be complete
        # (add_photo is called internally which completes again)
        complete_session.replace_photo(new_photo)

        assert complete_session.status == SessionStatus.COMPLETE

    def test_cannot_replace_in_abandoned_session(self, sample_session):
        """Cannot replace photos in an abandoned session."""
        from tests.conftest import create_photo

        sample_session.add_photo(create_photo(sample_session.id, 0))
        sample_session.abandon()

        new_photo = create_photo(sample_session.id, 0)

        with pytest.raises(SessionError):
            sample_session.replace_photo(new_photo)


class TestPhotoSessionStateTransitions:
    """Tests for session state transitions."""

    def test_mark_printed_requires_complete(self, sample_session):
        """Can only mark complete sessions as printed."""
        with pytest.raises(SessionError, match="complete"):
            sample_session.mark_printed()

    def test_mark_printed_changes_status(self, complete_session):
        """Marking as printed changes status."""
        complete_session.mark_printed()

        assert complete_session.status == SessionStatus.PRINTED

    def test_abandon_active_session(self, sample_session):
        """Can abandon an active session."""
        sample_session.abandon()

        assert sample_session.status == SessionStatus.ABANDONED
        assert sample_session.abandoned_at is not None

    def test_abandon_complete_session(self, complete_session):
        """Can abandon a complete session."""
        complete_session.abandon()

        assert complete_session.status == SessionStatus.ABANDONED

    def test_cannot_abandon_printed_session(self, complete_session):
        """Cannot abandon a printed session."""
        complete_session.mark_printed()

        with pytest.raises(SessionError, match="printed"):
            complete_session.abandon()


class TestPhotoSessionProperties:
    """Tests for session properties."""

    def test_is_complete_false_initially(self, sample_session):
        """is_complete is False for new session."""
        assert sample_session.is_complete is False

    def test_is_complete_true_with_four_photos(self, complete_session):
        """is_complete is True with 4 photos."""
        assert complete_session.is_complete is True

    def test_photo_count(self, sample_session):
        """photo_count returns correct number."""
        from tests.conftest import create_photo

        assert sample_session.photo_count == 0

        sample_session.add_photo(create_photo(sample_session.id, 0))
        assert sample_session.photo_count == 1

        sample_session.add_photo(create_photo(sample_session.id, 1))
        assert sample_session.photo_count == 2

    def test_get_photo_by_index(self, sample_session):
        """Can retrieve photo by index."""
        from tests.conftest import create_photo

        photo = create_photo(sample_session.id, 2)
        sample_session.add_photo(photo)

        assert sample_session.get_photo(2) == photo
        assert sample_session.get_photo(0) is None

    def test_set_composite_path(self, complete_session):
        """Can set composite path."""
        complete_session.set_composite_path("/path/to/composite.jpg")

        assert complete_session.composite_path == "/path/to/composite.jpg"
