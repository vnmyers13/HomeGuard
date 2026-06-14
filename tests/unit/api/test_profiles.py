"""Unit tests for profile endpoints."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date, datetime


class TestProfileService:
    """Tests for profile service layer."""

    def test_update_profile_partial(self):
        """Test partial profile update."""
        from schemas.profile import ProfileUpdate

        updates = ProfileUpdate(full_legal_name="Updated Name")
        assert updates.full_legal_name == "Updated Name"
        assert updates.date_of_birth is None

    def test_update_profile_full(self):
        """Test full profile update."""
        from schemas.profile import ProfileUpdate
        from datetime import datetime

        dob = datetime(1990, 2, 2)
        updates = ProfileUpdate(
            full_legal_name="Full Updated",
            date_of_birth=dob,
        )
        assert updates.full_legal_name == "Full Updated"
        assert updates.date_of_birth == dob


class TestProfileSchemas:
    """Tests for profile schema validation."""

    def test_profile_response_schema(self):
        """Test ProfileResponse schema."""
        from schemas.profile import ProfileResponse, ProfileFieldResponse
        from datetime import datetime

        field = ProfileFieldResponse(
            id="field-1",
            field_type="address",
            value="123 Main St",
            is_current=True,
            effective_from=datetime.now(),
            effective_to=None,
        )

        profile = ProfileResponse(
            id="prof-1",
            full_legal_name="Test User",
            date_of_birth=datetime(1990, 1, 1),
            exposure_score=0.5,
            is_current=True,
            created_at=datetime.now(),
            fields=[field],
        )
        assert profile.id == "prof-1"
        assert len(profile.fields) == 1

    def test_profile_update_minimal(self):
        """Test ProfileUpdate with minimal fields."""
        from schemas.profile import ProfileUpdate

        update = ProfileUpdate(full_legal_name="Just Name")
        assert update.full_legal_name == "Just Name"
        assert update.date_of_birth is None

    def test_profile_create_required_fields(self):
        """Test ProfileCreate requires full_legal_name."""
        from schemas.profile import ProfileCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProfileCreate(full_legal_name="")

    def test_profile_field_type_validation(self):
        """Test ProfileFieldCreate field_type validation."""
        from schemas.profile import ProfileFieldCreate
        from pydantic import ValidationError

        # Valid field type
        field = ProfileFieldCreate(field_type="address", value="123 Main St")
        assert field.field_type == "address"

        # Invalid field type
        with pytest.raises(ValidationError):
            ProfileFieldCreate(field_type="invalid", value="test")
