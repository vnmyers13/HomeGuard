"""
Seed first household member for HomeGuard sign-off.
Creates a test user, household, and profile to demonstrate the platform.

Usage:
  docker compose run --rm api python scripts/seed_first_household.py
  # or locally:
  python scripts/seed_first_household.py
"""
import asyncio
import os
import sys
from datetime import date

sys.path.insert(0, "/app")

from sqlalchemy import text

try:
    from api.database import engine
    from api.models.auth import User, Household
    from api.models.identity import Profile
except ImportError:
    from database import engine
    from models.auth import User, Household
    from models.identity import Profile


# First household member data
FIRST_MEMBER = {
    "username": "admin",
    "password": os.environ.get("ADMIN_PASSWORD", "change-me-in-production"),
    "household_name": "My Household",
    "display_name": "John Doe",
    "full_legal_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0100",
    "date_of_birth": date(1990, 6, 15),
    "ssn_last_four": "1234",
    "address_line1": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
}


async def seed_first_household():
    """Create the first household and profile for sign-off."""
    async with engine.begin() as conn:
        # Check if admin user already exists
        check_user = text(
            "SELECT id FROM auth.users WHERE username = :username"
        )
        result = await conn.execute(check_user, {"username": FIRST_MEMBER["username"]})
        user_row = result.fetchone()

        if user_row:
            print(f"Admin user '{FIRST_MEMBER['username']}' already exists (id={user_row[0]})")
            user_id = user_row[0]
        else:
            # Create admin user
            insert_user = text("""
                INSERT INTO auth.users (
                    username, password_hash, is_active, is_admin,
                    email_verified, created_at, updated_at
                ) VALUES (:username, :password_hash, true, true, true, now(), now())
                RETURNING id
            """)
            # Use a dummy hash - in production, use bcrypt
            user_result = await conn.execute(
                insert_user,
                {
                    "username": FIRST_MEMBER["username"],
                    "password_hash": "hashed_pw_placeholder",
                },
            )
            user_id = user_result.scalar()
            print(f"Created admin user '{FIRST_MEMBER['username']}' (id={user_id})")

        # Check if household already exists
        check_household = text(
            "SELECT id FROM auth.households WHERE name = :name"
        )
        household_result = await conn.execute(
            check_household, {"name": FIRST_MEMBER["household_name"]}
        )
        household_row = household_result.fetchone()

        if household_row:
            household_id = household_row[0]
            print(f"Household '{FIRST_MEMBER['household_name']}' already exists (id={household_id})")
        else:
            insert_household = text("""
                INSERT INTO auth.households (
                    name, user_id, created_at, updated_at
                ) VALUES (:name, :user_id, now(), now())
                RETURNING id
            """)
            household_result = await conn.execute(
                insert_household,
                {
                    "name": FIRST_MEMBER["household_name"],
                    "user_id": user_id,
                },
            )
            household_id = household_result.scalar()
            print(f"Created household '{FIRST_MEMBER['household_name']}' (id={household_id})")

        # Check if profile already exists
        check_profile = text(
            "SELECT id FROM identity.profiles WHERE household_id = :hid AND is_current = true LIMIT 1"
        )
        profile_result = await conn.execute(
            check_profile, {"hid": household_id}
        )
        profile_row = profile_result.fetchone()

        if profile_row:
            profile_id = profile_row[0]
            print(f"Profile already exists for household (id={profile_id})")
        else:
            insert_profile = text("""
                INSERT INTO identity.profiles (
                    display_name, full_legal_name, email, phone_number,
                    date_of_birth, ssn_last_four, address_line1, address_city,
                    address_state, address_zip, household_id, is_current,
                    created_at, updated_at
                ) VALUES (
                    :display_name, :full_legal_name, :email, :phone,
                    :dob, :ssn, :addr1, :city, :state, :zip,
                    :household_id, true, now(), now()
                )
                RETURNING id
            """)
            profile_result = await conn.execute(
                insert_profile,
                {
                    "display_name": FIRST_MEMBER["display_name"],
                    "full_legal_name": FIRST_MEMBER["full_legal_name"],
                    "email": FIRST_MEMBER["email"],
                    "phone": FIRST_MEMBER["phone"],
                    "dob": FIRST_MEMBER["date_of_birth"],
                    "ssn": FIRST_MEMBER["ssn_last_four"],
                    "addr1": FIRST_MEMBER["address_line1"],
                    "city": FIRST_MEMBER["city"],
                    "state": FIRST_MEMBER["state"],
                    "zip": FIRST_MEMBER["zip"],
                    "household_id": household_id,
                },
            )
            profile_id = profile_result.scalar()
            print(f"Created profile '{FIRST_MEMBER['display_name']}' (id={profile_id})")

        # Verify broker count
        broker_count = await conn.execute(
            text("SELECT COUNT(*) FROM registry.brokers WHERE is_active = true")
        )
        brokers = broker_count.scalar()
        print(f"\nBroker registry: {brokers} active brokers")

        # Verify household stats
        profile_count = await conn.execute(
            text("SELECT COUNT(*) FROM identity.profiles WHERE is_current = true")
        )
        profiles = profile_count.scalar()

        request_count = await conn.execute(
            text("SELECT COUNT(*) FROM requests.removal_requests")
        )
        requests = request_count.scalar()

        print(f"\nHousehold stats:")
        print(f"  Profiles: {profiles}")
        print(f"  Removal requests: {requests}")
        print(f"  Brokers monitored: {brokers}")

    print("\nFirst household member seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_first_household())
