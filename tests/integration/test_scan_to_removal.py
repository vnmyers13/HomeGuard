"""Integration tests for the Scan -> Exposure -> Removal Request flow.

These tests verify end-to-end data integrity across the three core domains:
- Scanning (Scan, Exposure)
- Identity (Profile, Household)
- Requests (RemovalRequest)

Each test creates a full chain of related records and verifies that
relationships are maintained correctly through the database layer.

Fixtures defined here use `scope="class"` to share a single database
transaction across all test methods in each class, reducing setup overhead.
"""

from datetime import datetime, timezone, timedelta
import pytest


@pytest.fixture(scope="class")
def db(session):
    """Alias for the session fixture to match test convention."""
    return session


@pytest.fixture(scope="class")
def user(db):
    """Create a test User."""
    from api.models.auth import User
    user = User(
        email="test@example.com",
        hashed_password="hashed_pw",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture(scope="class")
def household(db, user):
    """Create a test Household linked to the user."""
    from api.models.identity import Household
    household = Household(
        name="Test Household",
        user_id=user.id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(household)
    db.flush()
    return household


@pytest.fixture(scope="class")
def broker(db):
    """Create a test Broker."""
    from api.models.registry import Broker
    broker = Broker(
        domain="example.com",
        name="Example Broker",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    db.add(broker)
    db.flush()
    return broker


@pytest.fixture(scope="class")
def scan(db, household, user):
    """Create a test Scan."""
    from api.models.scanning import Scan
    scan = Scan(
        household_id=household.id,
        user_id=user.id,
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    db.add(scan)
    db.flush()
    return scan


@pytest.fixture(scope="class")
def profile(db, household):
    """Create a test Profile."""
    from api.models.identity import Profile
    profile = Profile(
        full_name="John Doe",
        household_id=household.id,
        dob=datetime(1990, 1, 15),
        created_at=datetime.now(timezone.utc)
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture(scope="class")
def exposure(db, scan, broker):
    """Create a test Exposure."""
    from api.models.scanning import Exposure
    exposure = Exposure(
        scan_id=scan.id,
        broker_id=broker.id,
        url="https://example.com/profile/1",
        risk_level="high",
        status="new",
        created_at=datetime.now(timezone.utc)
    )
    db.add(exposure)
    db.flush()
    return exposure


@pytest.fixture(scope="class")
def removal_request(db, profile, exposure, broker):
    """Create a test RemovalRequest."""
    from api.models.requests import RemovalRequest
    request = RemovalRequest(
        profile_id=profile.id,
        exposure_id=exposure.id,
        broker_id=broker.id,
        removal_method="generic_removal",
        status="queued",
        created_at=datetime.now(timezone.utc)
    )
    db.add(request)
    db.flush()
    return request


# ============================================================================
# Fixtures Verification
# ============================================================================

class TestFixtures:
    """Verify that all fixtures create valid database records."""

    def test_user_fixture(self, db, user):
        """Verify User fixture creates a valid record."""
        from api.models.auth import User
        saved = db.query(User).filter_by(id=user.id).first()
        assert saved is not None
        assert saved.email == "test@example.com"
        assert saved.is_active

    def test_household_fixture(self, db, household, user):
        """Verify Household fixture links to User correctly."""
        from api.models.identity import Household
        saved = db.query(Household).filter_by(id=household.id).first()
        assert saved is not None
        assert saved.user_id == user.id

    def test_broker_fixture(self, db, broker):
        """Verify Broker fixture creates a valid record."""
        from api.models.registry import Broker
        saved = db.query(Broker).filter_by(id=broker.id).first()
        assert saved is not None
        assert saved.status == "active"

    def test_scan_fixture(self, db, scan, household):
        """Verify Scan fixture links to Household correctly."""
        from api.models.scanning import Scan
        saved = db.query(Scan).filter_by(id=scan.id).first()
        assert saved is not None
        assert saved.household_id == household.id

    def test_profile_fixture(self, db, profile, household):
        """Verify Profile fixture links to Household correctly."""
        from api.models.identity import Profile
        saved = db.query(Profile).filter_by(id=profile.id).first()
        assert saved is not None
        assert saved.household_id == household.id

    def test_exposure_fixture(self, db, exposure, scan):
        """Verify Exposure fixture links to Scan correctly."""
        from api.models.scanning import Exposure
        saved = db.query(Exposure).filter_by(id=exposure.id).first()
        assert saved is not None
        assert saved.scan_id == scan.id

    def test_removal_request_fixture(self, db, removal_request, profile):
        """Verify RemovalRequest fixture links to Profile correctly."""
        from api.models.requests import RemovalRequest
        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved is not None
        assert saved.profile_id == profile.id


# ============================================================================
# Relationship Integrity Tests
# ============================================================================

class TestRelationshipIntegrity:
    """Verify that relationships between entities are maintained."""

    def test_scan_links_to_household(self, db, scan, household):
        """Verify Scan -> Household relationship is intact."""
        from api.models.scanning import Scan
        saved = db.query(Scan).filter_by(id=scan.id).first()
        assert saved.household_id == household.id

    def test_exposure_links_to_scan(self, db, exposure, scan):
        """Verify Exposure -> Scan relationship is intact."""
        from api.models.scanning import Exposure
        saved = db.query(Exposure).filter_by(id=exposure.id).first()
        assert saved.scan_id == scan.id

    def test_removal_request_links_to_exposure(self, db, removal_request, exposure):
        """Verify RemovalRequest -> Exposure relationship is intact."""
        from api.models.requests import RemovalRequest
        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.exposure_id == exposure.id

    def test_full_chain_traceability(self, db, scan, exposure, removal_request):
        """Verify full chain: Scan -> Exposure -> RemovalRequest."""
        from api.models.scanning import Scan, Exposure
        from api.models.requests import RemovalRequest

        # Get scan
        s = db.query(Scan).filter_by(id=scan.id).first()
        assert s is not None

        # Get exposure linked to scan
        e = db.query(Exposure).filter_by(id=exposure.id).first()
        assert e is not None
        assert e.scan_id == s.id

        # Get removal request linked to exposure
        r = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert r is not None
        assert r.exposure_id == e.id


# ============================================================================
# Status Transition Tests
# ============================================================================

class TestStatusTransitions:
    """Verify status transitions work correctly."""

    def test_scan_status_transition(self, db, scan):
        """Verify Scan status can transition from running to completed."""
        from api.models.scanning import Scan
        scan.status = "running"
        db.flush()
        running_scan = db.query(Scan).filter_by(id=scan.id).first()
        assert running_scan.status == "running"

        scan.status = "completed"
        db.flush()
        completed_scan = db.query(Scan).filter_by(id=scan.id).first()
        assert completed_scan.status == "completed"

    def test_removal_request_status_transition(self, db, removal_request):
        """Verify RemovalRequest status transitions."""
        from api.models.requests import RemovalRequest

        # queued -> submitted
        removal_request.status = "submitted"
        db.flush()
        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.status == "submitted"

        # submitted -> confirmed_removed
        removal_request.status = "confirmed_removed"
        db.flush()
        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.status == "confirmed_removed"

    def test_removal_request_timeline(self, db, removal_request):
        """Verify RemovalRequest timeline fields are tracked."""
        from api.models.requests import RemovalRequest

        now = datetime.now(timezone.utc)
        removal_request.submitted_at = now
        removal_request.next_action_at = now + timedelta(hours=24)
        db.flush()

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.submitted_at == now
        assert saved.next_action_at == now + timedelta(hours=24)

    def test_removal_request_followup_count(self, db, removal_request):
        """Verify RemovalRequest follow-up count is tracked."""
        from api.models.requests import RemovalRequest

        now = datetime.now(timezone.utc)
        removal_request.next_action_at = now - timedelta(hours=1)
        removal_request.followup_count = 2
        db.flush()

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.next_action_at is not None
        assert saved.followup_count == 2

    def test_request_confirmation(self, db, removal_request):
        """CP-05: Verify confirmation message is tracked."""
        from api.models.requests import RemovalRequest
        removal_request.status = "confirmed_removed"
        removal_request.confirmation_message = "Data removed successfully"
        db.flush()

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.status == "confirmed_removed"
        assert saved.confirmation_message == "Data removed successfully"


# ============================================================================
# Scan Result Aggregation Tests
# ============================================================================

class TestScanResultAggregation:
    """Tests for scan result aggregation and statistics."""

    def test_scan_exposure_count(self, db, scan, broker):
        """Verify exposure count is tracked per scan."""
        from api.models.scanning import Exposure
        for i in range(5):
            exposure = Exposure(
                scan_id=scan.id,
                broker_id=broker.id,
                url=f"https://example.com/profile/{i}",
                risk_level="high" if i % 2 == 0 else "low",
                status="new",
                created_at=datetime.now(timezone.utc)
            )
            db.add(exposure)
        db.flush()

        exposures = db.query(Exposure).filter_by(scan_id=scan.id).all()
        assert len(exposures) == 5

    def test_risk_level_distribution(self, db, scan, broker):
        """Verify risk levels are properly distributed."""
        from api.models.scanning import Exposure
        risk_levels = ["high", "medium", "low"]
        for i, level in enumerate(risk_levels):
            exposure = Exposure(
                scan_id=scan.id,
                broker_id=broker.id,
                url=f"https://example.com/profile/{i}",
                risk_level=level,
                status="new",
                created_at=datetime.now(timezone.utc)
            )
            db.add(exposure)
        db.flush()

        high_count = db.query(Exposure).filter_by(
            scan_id=scan.id,
            risk_level="high"
        ).count()
        assert high_count == 1


# ============================================================================
# Full Scan-to-Removal Integration Test
# ============================================================================

class TestFullScanToRemovalIntegration:
    """End-to-end integration test for the complete flow."""

    def test_complete_scan_to_removal_flow(self, db, user, household, broker):
        """Test complete flow: Scan -> Exposures -> Requests."""
        from api.models.scanning import Scan, Exposure
        from api.models.identity import Profile
        from api.models.requests import RemovalRequest

        now = datetime.now(timezone.utc)

        # 1. Create scan
        scan = Scan(
            household_id=household.id,
            user_id=user.id,
            status="running",
            created_at=now
        )
        db.add(scan)
        db.flush()

        # 2. Create profile
        profile = Profile(
            full_name="John Doe",
            household_id=household.id,
            dob=datetime(1990, 1, 15),
            created_at=now
        )
        db.add(profile)
        db.flush()

        # 3. Create exposures from scan
        exposures = []
        for i in range(3):
            exposure = Exposure(
                scan_id=scan.id,
                broker_id=broker.id,
                url=f"https://example.com/profile/{i}",
                risk_level="high",
                status="new",
                created_at=now
            )
            db.add(exposure)
            exposures.append(exposure)
        db.flush()

        # 4. Create removal requests from exposures
        requests = []
        for exposure in exposures:
            request = RemovalRequest(
                profile_id=profile.id,
                exposure_id=exposure.id,
                broker_id=exposure.broker_id,
                removal_method="generic_removal",
                status="queued",
                created_at=now
            )
            db.add(request)
            requests.append(request)
        db.flush()

        # 5. Verify complete chain
        assert len(exposures) == 3
        assert len(requests) == 3

        # Verify all requests link back to scan
        for req in requests:
            assert req.exposure_id is not None
            exposure = db.query(Exposure).filter_by(id=req.exposure_id).first()
            assert exposure.scan_id == scan.id

        # Mark scan as completed
        scan.status = "completed"
        db.flush()
        assert scan.status == "completed"