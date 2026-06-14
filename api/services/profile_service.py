"""Profile service - CRUD, encryption, versioning for household member profiles."""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet, InvalidToken

from models.identity import Profile, ProfileField, Alias
from schemas.profile import (
    ProfileCreate,
    ProfileUpdate as ProfileUpdateSchema,
    ProfileDeleteResponse,
    ProfileFieldCreate,
    ProfileFieldResponse,
)


class EncryptionService:
    """Fernet symmetric encryption for PII fields."""

    def __init__(self, key: Optional[str] = None):
        if key:
            # Ensure key is bytes (Fernet expects base64-encoded 32-byte key)
            if isinstance(key, str):
                key = key.encode()
            self.cipher = Fernet(key)
        else:
            self.cipher = Fernet.generate_key()
            if isinstance(self.cipher, bytes):
                self.cipher = Fernet(self.cipher)

    def encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return ""
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()

    def decrypt(self, token: str) -> str:
        """Decrypt a token."""
        if not token:
            return ""
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except InvalidToken:
            return ""


class ProfileService:
    """Business logic for profile CRUD, encryption, and versioning."""

    def __init__(self):
        self.encryption = EncryptionService()

    async def create_profile(
        self,
        data: ProfileCreate,
        household_id: Optional[uuid.UUID],
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> Profile:
        """Create a new household member profile."""
        encrypted_name = self.encryption.encrypt(data.full_legal_name)

        profile = Profile(
            id=uuid.uuid4(),
            household_id=household_id,
            owner_id=user_id,
            full_legal_name_encrypted=encrypted_name,
            date_of_birth=data.date_of_birth,
            display_name=data.full_legal_name.split()[0] if data.full_legal_name else "User",
            is_admin=False,
            exposure_score=0.0,
        )

        session.add(profile)
        await session.flush()
        return profile

    async def get_profile(
        self,
        profile_id: uuid.UUID,
        session: AsyncSession,
    ) -> Optional[Profile]:
        """Get a profile by ID (owner only)."""
        result = await session.execute(
            select(Profile).where(
                Profile.id == profile_id,
                Profile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_profiles(
        self,
        household_id: uuid.UUID,
        session: AsyncSession,
    ) -> List[Profile]:
        """List all active profiles in a household."""
        result = await session.execute(
            select(Profile).where(
                Profile.household_id == household_id,
                Profile.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def update_profile(
        self,
        profile_id: uuid.UUID,
        data: ProfileUpdateSchema,
        session: AsyncSession,
    ) -> Optional[Profile]:
        """Update a profile with encryption for PII changes."""
        profile = await self.get_profile(profile_id, session)
        if not profile:
            return None

        if data.full_legal_name is not None:
            # Archive previous name as alias before updating
            if profile.full_legal_name_encrypted:
                current_name = self.encryption.decrypt(profile.full_legal_name_encrypted)
                if current_name:
                    alias = Alias(
                        id=uuid.uuid4(),
                        profile_id=profile.id,
                        alias_name=current_name,
                        alias_type="former_name",
                    )
                    session.add(alias)

            profile.full_legal_name_encrypted = self.encryption.encrypt(data.full_legal_name)
            profile.display_name = data.full_legal_name.split()[0]

        if data.date_of_birth is not None:
            profile.date_of_birth = data.date_of_birth

        await session.flush()
        return profile

    async def add_profile_field(
        self,
        profile_id: uuid.UUID,
        data: ProfileFieldCreate,
        session: AsyncSession,
    ) -> ProfileField:
        """Add a profile field (address/phone/email) with encryption."""
        # Deactivate previous fields of same type (versioning)
        await session.execute(
            text("""
                UPDATE identity.profile_fields 
                SET is_current = false, effective_to = NOW()
                WHERE profile_id = :pid AND field_type = :ftype AND is_current = true
            """),
            {"pid": str(profile_id), "ftype": data.field_type},
        )

        encrypted_value = self.encryption.encrypt(data.value)

        field = ProfileField(
            id=uuid.uuid4(),
            profile_id=profile_id,
            field_type=data.field_type,
            field_value_encrypted=encrypted_value,
            is_current=True,
        )

        session.add(field)
        await session.flush()
        return field

    async def get_profile_fields(
        self,
        profile_id: uuid.UUID,
        session: AsyncSession,
    ) -> List[ProfileField]:
        """Get all current fields for a profile (decrypted)."""
        result = await session.execute(
            select(ProfileField).where(
                ProfileField.profile_id == profile_id,
                ProfileField.is_current.is_(True),
            )
        )
        fields = list(result.scalars().all())

        # Decrypt values for response
        for field in fields:
            field.field_value = self.encryption.decrypt(field.field_value_encrypted)

        return fields

    async def delete_profile(
        self,
        profile_id: uuid.UUID,
        session: AsyncSession,
    ) -> ProfileDeleteResponse:
        """Soft-delete a profile (set deleted_at)."""
        profile = await self.get_profile(profile_id, session)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        # Archive non-current fields
        await session.execute(
            text("""
                UPDATE identity.profile_fields 
                SET archived = true, effective_to = NOW()
                WHERE profile_id = :pid AND is_current = false
            """),
            {"pid": str(profile_id)},
        )

        profile.deleted_at = datetime.utcnow()
        await session.flush()

        return ProfileDeleteResponse(
            message="Profile deleted successfully",
            archived_profile_id=str(profile.id),
        )

    async def calculate_exposure_score(
        self,
        profile_id: uuid.UUID,
        session: AsyncSession,
    ) -> float:
        """Calculate exposure score based on data points."""
        # Count active fields (more data = higher exposure)
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM identity.profile_fields 
                WHERE profile_id = :pid AND is_current = true
            """),
            {"pid": str(profile_id)},
        )
        field_count = result.scalar() or 0

        # Count aliases (identity complexity)
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM identity.aliases 
                WHERE profile_id = :pid
            """),
            {"pid": str(profile_id)},
        )
        alias_count = result.scalar() or 0

        # Base score: 10 points per field, 5 per alias (max 100)
        score = min(100.0, (field_count * 10 + alias_count * 5))
        return round(score, 2)

    async def batch_create_profiles(
        self,
        profiles_data: List[ProfileCreate],
        household_id: Optional[uuid.UUID],
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> dict:
        """Batch create profiles. Returns summary with per-profile results."""
        results = []
        created = 0
        failed = 0

        for idx, data in enumerate(profiles_data):
            try:
                encrypted_name = self.encryption.encrypt(data.full_legal_name)

                profile = Profile(
                    id=uuid.uuid4(),
                    household_id=household_id,
                    owner_id=user_id,
                    full_legal_name_encrypted=encrypted_name,
                    date_of_birth=data.date_of_birth,
                    display_name=data.full_legal_name.split()[0] if data.full_legal_name else "User",
                    is_admin=False,
                    exposure_score=0.0,
                )

                session.add(profile)
                await session.flush()
                created += 1
                results.append(BatchCreateResult(
                    index=idx,
                    success=True,
                    profile_id=str(profile.id),
                ))
            except Exception as e:
                failed += 1
                results.append(BatchCreateResult(
                    index=idx,
                    success=False,
                    error=str(e),
                ))

        await session.commit()

        return {
            "success": failed == 0,
            "total": len(profiles_data),
            "created": created,
            "failed": failed,
            "results": results,
        }