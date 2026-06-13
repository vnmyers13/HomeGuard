"""Unit tests for email/legal template rendering service."""

import base64
from datetime import datetime, timezone

import pytest


@pytest.fixture
def template_context():
    """Standard template context for testing."""
    return {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St, Anytown, ST 12345",
        "dob": "01/15/1985",
        "broker_name": "PeopleSearch.com",
        "broker_domain": "peoplesearch.com",
        "broker_contact_email": "privacy@peoplesearch.com",
        "broker_address": "456 Broker St, Data City, DC 54321",
        "data_types": ["Full Name", "Address", "Phone Number", "Date of Birth"],
        "user_name": "John",
        "profile_count": 12,
        "high_risk_count": 3,
        "requests_submitted": 10,
    }


# ---------------------------------------------------------------------------
# Opt-out Email Tests
# ---------------------------------------------------------------------------

class TestRenderOptOutEmail:
    """Test opt-out email template rendering."""

    def test_render_opt_out_email_returns_string(self, template_context):
        """Test opt-out email renders to a string."""
        from services.templates import render_opt_out_email

        result = render_opt_out_email(template_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_opt_out_email_contains_full_name(self, template_context):
        """Test opt-out email contains the full name."""
        from services.templates import render_opt_out_email

        result = render_opt_out_email(template_context)
        assert "John Doe" in result

    def test_render_opt_out_email_contains_address(self, template_context):
        """Test opt-out email contains the address."""
        from services.templates import render_opt_out_email

        result = render_opt_out_email(template_context)
        assert "123 Main St" in result

    def test_render_opt_out_email_contains_dob(self, template_context):
        """Test opt-out email contains date of birth."""
        from services.templates import render_opt_out_email

        result = render_opt_out_email(template_context)
        assert "01/15/1985" in result

    def test_render_opt_out_email_with_missing_optional_fields(self):
        """Test templates handle missing optional fields gracefully."""
        from services.templates import render_opt_out_email

        minimal_context = {
            "full_name": "John Doe",
            "email": "john@example.com",
        }

        result = render_opt_out_email(minimal_context)
        assert isinstance(result, str)
        assert "John Doe" in result


# ---------------------------------------------------------------------------
# CCPA Deletion Tests
# ---------------------------------------------------------------------------

class TestRenderCCPADeletion:
    """Test CCPA deletion request template rendering."""

    def test_render_ccpa_deletion_returns_string(self, template_context):
        """Test CCPA deletion renders to a string."""
        from services.templates import render_ccpa_deletion

        result = render_ccpa_deletion(template_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_ccpa_deletion_contains_name(self, template_context):
        """Test CCPA deletion contains the consumer name."""
        from services.templates import render_ccpa_deletion

        result = render_ccpa_deletion(template_context)
        assert "John Doe" in result

    def test_render_ccpa_deletion_contains_legal_references(self, template_context):
        """Test CCPA deletion contains legal references."""
        from services.templates import render_ccpa_deletion

        result = render_ccpa_deletion(template_context)
        assert "CCPA" in result

    def test_render_ccpa_deletion_with_empty_data_types(self, template_context):
        """Test templates handle empty data types list."""
        from services.templates import render_ccpa_deletion

        template_context["data_types"] = []
        result = render_ccpa_deletion(template_context)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# GDPR Erasure Tests
# ---------------------------------------------------------------------------

class TestRenderGDPRERasure:
    """Test GDPR erasure request template rendering."""

    def test_render_gdpr_erasure_returns_string(self, template_context):
        """Test GDPR erasure renders to a string."""
        from services.templates import render_gdpr_erasure

        result = render_gdpr_erasure(template_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_gdpr_erasure_contains_name(self, template_context):
        """Test GDPR erasure contains the data subject name."""
        from services.templates import render_gdpr_erasure

        result = render_gdpr_erasure(template_context)
        assert "John Doe" in result

    def test_render_gdpr_erasure_contains_gdpr_references(self, template_context):
        """Test GDPR erasure contains GDPR references."""
        from services.templates import render_gdpr_erasure

        result = render_gdpr_erasure(template_context)
        assert "GDPR" in result


# ---------------------------------------------------------------------------
# Legal Demand Tests
# ---------------------------------------------------------------------------

class TestRenderLegalDemand:
    """Test legal demand letter template rendering."""

    def test_render_legal_demand_returns_html(self, template_context):
        """Test legal demand renders HTML."""
        from services.templates import render_legal_demand

        result = render_legal_demand(template_context)
        assert "<html" in result.lower()

    def test_render_legal_demand_contains_name(self, template_context):
        """Test legal demand contains the client name."""
        from services.templates import render_legal_demand

        result = render_legal_demand(template_context)
        assert "John Doe" in result

    def test_render_legal_demand_contains_date(self, template_context):
        """Test legal demand includes a date."""
        from services.templates import render_legal_demand

        result = render_legal_demand(template_context)
        now = datetime.now(timezone.utc).strftime("%B %d, %Y")
        assert now in result

    def test_render_legal_demand_contains_deadline(self, template_context):
        """Test legal demand includes deadline."""
        from services.templates import render_legal_demand

        result = render_legal_demand(template_context)
        assert "10" in result  # default deadline_days


# ---------------------------------------------------------------------------
# Scan Complete Tests
# ---------------------------------------------------------------------------

class TestRenderScanComplete:
    """Test scan completion notification template rendering."""

    def test_render_scan_complete_returns_string(self, template_context):
        """Test scan complete notification renders to a string."""
        from services.templates import render_scan_complete

        result = render_scan_complete(template_context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_scan_complete_contains_user_info(self, template_context):
        """Test scan complete notification contains user info."""
        from services.templates import render_scan_complete

        result = render_scan_complete(template_context)
        assert "John" in result

    def test_render_scan_complete_contains_profile_count(self, template_context):
        """Test scan complete notification contains profile count."""
        from services.templates import render_scan_complete

        result = render_scan_complete(template_context)
        assert "12" in result


# ---------------------------------------------------------------------------
# PDF Encoding Tests
# ---------------------------------------------------------------------------

class TestEncodePdfForEmail:
    """Test PDF encoding for email attachments."""

    def test_encode_pdf_for_email(self):
        """Test PDF bytes are correctly base64 encoded."""
        from services.templates import encode_pdf_for_email

        pdf_bytes = b"%PDF-1.4 mock pdf content"
        result = encode_pdf_for_email(pdf_bytes)

        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded == pdf_bytes

    def test_encode_pdf_for_email_with_filename(self):
        """Test PDF encoding with custom filename."""
        from services.templates import encode_pdf_for_email

        pdf_bytes = b"%PDF-1.4 test content"
        result = encode_pdf_for_email(pdf_bytes, filename="custom_demand.pdf")

        decoded = base64.b64decode(result)
        assert decoded == pdf_bytes


# ---------------------------------------------------------------------------
# PDF Context Tests
# ---------------------------------------------------------------------------

class TestRenderLegalDemandPdfContext:
    """Test PDF context preparation for legal demand."""

    def test_render_legal_demand_pdf_context_sets_date(self):
        """Test that date is set when not provided."""
        from services.templates import render_legal_demand_pdf_context

        context = {"full_name": "John Doe"}
        result = render_legal_demand_pdf_context(context)

        assert "date" in result
        assert result["full_name"] == "John Doe"

    def test_render_legal_demand_pdf_context_sets_deadline(self):
        """Test that deadline_days defaults to 10."""
        from services.templates import render_legal_demand_pdf_context

        context = {}
        result = render_legal_demand_pdf_context(context)

        assert result.get("deadline_days") == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])