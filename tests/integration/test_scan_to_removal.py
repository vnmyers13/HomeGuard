"""Integration tests for the Scan -> Exposure -> Removal Request flow.

These tests verify end-to-end data integrity across the three core domains:
- Scanning (ScanRun, Exposure)
- Identity (Profile, Household)
- Requests (RemovalRequest)

Each test creates a full chain of related records and verifies that
relationships are maintained correctly through the database layer.

Fixtures defined here use `scope="class"` to share a single database
transaction across all test methods in each class, reducing setup overhead.
"""

from datetime import datetime, timezone, timedelta
import pytest
# Import models with fallback for Docker container (code at /app, not /app/api)
try:
    from api.models.auth import User, Household
    from api.models.registry import Broker
    from api.models.scanning import ScanRun, Exposure, ScanResult
    from api.models.identity import Profile
    from api.models.requests import RemovalRequest, Followup, RequestStatusLog, VerificationScan
    from api.models.audit import SystemEvent, AuditLog
    from api.models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent
except ImportError:
    from models.auth import User, Household
    from models.registry import Broker
    from models.scanning import ScanRun, Exposure, ScanResult
    from models.identity import Profile
    from models.requests import RemovalRequest, Followup, RequestStatusLog, VerificationScan
    from models.audit import SystemEvent, AuditLog
    from models.reporting import ExposureScore, DailyBrokerSnapshot, RelistingEvent

@pytest.fixture(scope="class")
def db(session):
    """Alias for the session fixture to match test convention."""
    return session


@pytest.fixture(scope="class")
def user(db):
    """Create a test User."""

    user = User(
        username="testuser",
        password_hash="hashed_pw",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture(scope="class")
def household(db, user):
    """Create a test Household linked to the user."""

    household = Household(
        name="Test Household",
    )
    db.add(household)
    db.flush()
    return household


@pytest.fixture(scope="class")
def broker(db):
    """Create a test Broker."""

    broker = Broker(
        canonical_domain="example.com",
        display_name="Example Broker",
    )
    db.add(broker)
    db.flush()
    return broker


@pytest.fixture(scope="class")
def scan(db, profile):
    """Create a test ScanRun."""

    scan = ScanRun(
        profile_id=profile.id,
        run_type="manual",
        status="completed",
    )
    db.add(scan)
    db.flush()
    return scan


@pytest.fixture(scope="class")
def profile(db, household):
    """Create a test Profile."""

    profile = Profile(
        display_name="John Doe",
        full_legal_name="John Doe",
        household_id=household.id,
        date_of_birth=datetime(1990, 1, 15).date(),
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture(scope="class")
def exposure(db, scan, profile, broker):
    """Create a test Exposure."""

    exposure = Exposure(
        scan_run_id=scan.id,
        profile_id=profile.id,
        broker_id=broker.id,
        is_active=True,
        is_removed=False,
    )
    db.add(exposure)
    db.flush()
    return exposure


@pytest.fixture(scope="class")
def removal_request(db, profile, exposure, broker):
    """Create a test RemovalRequest."""

    request = RemovalRequest(
        profile_id=profile.id,
        exposure_id=exposure.id,
        broker_id=broker.id,
        removal_method="generic_removal",
        status="queued",
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

        saved = db.query(User).filter_by(id=user.id).first()
        assert saved is not None
        assert saved.username == "testuser"
        assert saved.is_active

    def test_household_fixture(self, db, household):
        """Verify Household fixture creates a valid record."""

        saved = db.query(Household).filter_by(id=household.id).first()
        assert saved is not None

    def test_broker_fixture(self, db, broker):
        """Verify Broker fixture creates a valid record."""

        saved = db.query(Broker).filter_by(id=broker.id).first()
        assert saved is not None
        assert saved.is_active is True

    def test_scan_fixture(self, db, scan, profile):
        """Verify ScanRun fixture links to Profile correctly."""

        saved = db.query(ScanRun).filter_by(id=scan.id).first()
        assert saved is not None
        assert saved.profile_id == profile.id

    def test_profile_fixture(self, db, profile, household):
        """Verify Profile fixture links to Household correctly."""

        saved = db.query(Profile).filter_by(id=profile.id).first()
        assert saved is not None
        assert saved.household_id == household.id

    def test_exposure_fixture(self, db, exposure, scan):
        """Verify Exposure fixture links to ScanRun correctly."""

        saved = db.query(Exposure).filter_by(id=exposure.id).first()
        assert saved is not None
        assert saved.scan_run_id == scan.id

    def test_removal_request_fixture(self, db, removal_request, profile):
        """Verify RemovalRequest fixture links to Profile correctly."""

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved is not None
        assert saved.profile_id == profile.id


# ============================================================================
# Relationship Integrity Tests
# ============================================================================

class TestRelationshipIntegrity:
    """Verify that relationships between entities are maintained."""

    def test_scan_links_to_profile(self, db, scan, profile):
        """Verify ScanRun -> Profile relationship is intact."""

        saved = db.query(ScanRun).filter_by(id=scan.id).first()
        assert saved.profile_id == profile.id

    def test_exposure_links_to_scan(self, db, exposure, scan):
        """Verify Exposure -> ScanRun relationship is intact."""

        saved = db.query(Exposure).filter_by(id=exposure.id).first()
        assert saved.scan_run_id == scan.id

    def test_removal_request_links_to_exposure(self, db, removal_request, exposure):
        """Verify RemovalRequest -> Exposure relationship is intact."""

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.exposure_id == exposure.id

    def test_full_chain_traceability(self, db, scan, exposure, removal_request):
        """Verify full chain: ScanRun -> Exposure -> RemovalRequest."""



        # Get scan
        s = db.query(ScanRun).filter_by(id=scan.id).first()
        assert s is not None

        # Get exposure linked to scan
        e = db.query(Exposure).filter_by(id=exposure.id).first()
        assert e is not None
        assert e.scan_run_id == s.id

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
        """Verify ScanRun status can transition from pending to completed."""

        scan.status = "running"
        db.flush()
        running_scan = db.query(ScanRun).filter_by(id=scan.id).first()
        assert running_scan.status == "running"

        scan.status = "completed"
        db.flush()
        completed_scan = db.query(ScanRun).filter_by(id=scan.id).first()
        assert completed_scan.status == "completed"

    def test_removal_request_status_transition(self, db, removal_request):
        """Verify RemovalRequest status transitions."""


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


        now = datetime.now(timezone.utc)
        removal_request.next_action_at = now + timedelta(hours=24)
        db.flush()

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.next_action_at == now + timedelta(hours=24)

    def test_removal_request_followup_count(self, db, removal_request):
        """Verify RemovalRequest follow-up count is tracked."""


        now = datetime.now(timezone.utc)
        removal_request.next_action_at = now - timedelta(hours=1)
        removal_request.followup_count = 2
        db.flush()

        saved = db.query(RemovalRequest).filter_by(id=removal_request.id).first()
        assert saved.next_action_at is not None
        assert saved.followup_count == 2

    def test_request_confirmation(self, db, removal_request):
        """CP-05: Verify confirmation message is tracked."""

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

    def test_scan_exposure_count(self, db, scan, profile, broker):
        """Verify exposure count is tracked per scan."""

        for i in range(5):
            exposure = Exposure(
                scan_run_id=scan.id,
                profile_id=profile.id,
                broker_id=broker.id,
                is_active=True,
                is_removed=False,
            )
            db.add(exposure)
        db.flush()

        exposures = db.query(Exposure).filter_by(scan_run_id=scan.id).all()
        assert len(exposures) == 5

    def test_risk_level_distribution(self, db, scan, profile, broker):
        """Verify risk levels are properly distributed."""

        # Exposure model doesn't have risk_level, uses data_fields_found (JSONB) instead
        # This test verifies exposures can be created with different data_fields_found
        data_sets = [
            {"type": "email", "severity": "high"},
            {"type": "phone", "severity": "medium"},
            {"type": "address", "severity": "low"},
        ]
        for i, data in enumerate(data_sets):
            exposure = Exposure(
                scan_run_id=scan.id,
                profile_id=profile.id,
                broker_id=broker.id,
                data_fields_found=data,
                is_active=True,
                is_removed=False,
            )
            db.add(exposure)
        db.flush()
    
        exposures = db.query(Exposure).filter_by(scan_run_id=scan.id).all()
        # 5 from test_scan_exposure_count + 3 new = 8 total (class-scoped fixtures)
        assert len(exposures) == 8


# ============================================================================
# Full Scan-to-Removal Integration Test
# ============================================================================

class TestFullScanToRemovalIntegration:
    """End-to-end integration test for the complete flow."""

    def test_complete_scan_to_removal_flow(self, db, user, household, broker):
        """Test complete flow: ScanRun -> Exposures -> Requests."""




        # 1. Create profile
        profile = Profile(
            display_name="John Doe",
            full_legal_name="John Doe",
            household_id=household.id,
            date_of_birth=datetime(1990, 1, 15).date(),
        )
        db.add(profile)
        db.flush()

        # 2. Create scan run
        scan = ScanRun(
            profile_id=profile.id,
            run_type="manual",
            status="running",
        )
        db.add(scan)
        db.flush()

        # 3. Create exposures from scan
        exposures = []
        for i in range(3):
            exposure = Exposure(
                scan_run_id=scan.id,
                profile_id=profile.id,
                broker_id=broker.id,
                is_active=True,
                is_removed=False,
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
                broker_id=broker.id,
                removal_method="generic_removal",
                status="queued",
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
            assert exposure.scan_run_id == scan.id

        # Mark scan as completed
        scan.status = "completed"
        db.flush()
        assert scan.status == "completed"
