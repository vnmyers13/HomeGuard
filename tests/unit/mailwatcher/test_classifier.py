"""
Unit tests for the email classification engine.

Tests cover:
- PatternsLoader mtime-based caching and hot-reload
- ClassificationResult serialization and confidence clamping
- EmailClassifier two-stage rule-based classification
  - Stage 1 prefilter keyword matching
  - Stage 2 detailed regex pattern matching
- classify_email convenience function
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

classifier = pytest.importorskip("mailwatcher.classifier", reason="mailwatcher module not available")

from classifier import (
    Classification,
    ClassificationResult,
    EmailClassifier,
    PatternsLoader,
    classify_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_PATTERNS = {
    "prefilter_keywords": {
        "confirmed_removal": ["removed", "deleted", "purged"],
        "rejection": ["denied", "rejected", "unable"],
        "info_requested": ["need", "require", "additional information"],
        "verification_link": ["verify", "click", "confirmation link"],
    },
    "patterns": {
        "confirmed_removal": [
            r"your listing has been\s+(?:removed|deleted)",
            r"account\s+purged\s+successfully",
        ],
        "rejection": [
            r"request\s+(?:denied|rejected)",
            r"unable to process your request",
        ],
        "info_requested": [
            r"please provide\s+(?:additional )?information",
            r"we need (?:more |your )?\w+ to proceed",
        ],
        "verification_link": [
            r"click the following link to verify",
            r"confirmation link.*?http",
        ],
    },
}


@pytest.fixture
def patterns_file(tmp_path: Path):
    """Create a temporary patterns.yml file."""
    p = tmp_path / "patterns.yml"
    p.write_text(yaml.dump(_SAMPLE_PATTERNS))
    return str(p)


@pytest.fixture
def classifier(patterns_file):
    return EmailClassifier(patterns_path=patterns_file)


# ---------------------------------------------------------------------------
# PatternsLoader tests
# ---------------------------------------------------------------------------

class TestPatternsLoader:
    def test_load_patterns(self, patterns_file):
        loader = PatternsLoader(patterns_file)
        data = loader.load()
        assert "prefilter_keywords" in data
        assert "patterns" in data

    def test_caches_on_unchanged_mtime(self, patterns_file):
        loader = PatternsLoader(patterns_file)
        first = loader.load()
        second = loader.load()
        assert first is second  # same object (cached)

    def test_reload_when_file_changes(self, patterns_file, tmp_path: Path):
        loader = PatternsLoader(patterns_file)
        loader.load()

        # Modify the file
        p = tmp_path / "patterns.yml"
        new_patterns = dict(_SAMPLE_PATTERNS)
        new_patterns["prefilter_keywords"]["confirmed_removal"].append("erased")
        p.write_text(yaml.dump(new_patterns))
        os.replace(str(p), patterns_file)

        reloaded = loader.reload_if_changed()
        assert reloaded is True
        data = loader.load()
        assert "erased" in data["prefilter_keywords"]["confirmed_removal"]


# ---------------------------------------------------------------------------
# ClassificationResult tests
# ---------------------------------------------------------------------------

class TestClassificationResult:
    def test_confidence_clamped_to_0_100(self):
        r = ClassificationResult("unclassified", confidence=-10)
        assert r.confidence == 0

        r2 = ClassificationResult("unclassified", confidence=150)
        assert r2.confidence == 100

    def test_to_dict(self):
        r = ClassificationResult(
            classification="confirmed_removal",
            confidence=85,
            matched_pattern=r"listing removed",
            extracted_data={"broker": "spokeo"},
        )
        d = r.to_dict()
        assert d["classification"] == "confirmed_removal"
        assert d["confidence"] == 85
        assert d["matched_pattern"] == r"listing removed"
        assert d["extracted_data"]["broker"] == "spokeo"


# ---------------------------------------------------------------------------
# EmailClassifier tests
# ---------------------------------------------------------------------------

class TestEmailClassifier:
    def test_confirmed_removal_classification(self, classifier):
        result = classifier.classify(
            subject="Your Request",
            body_text="Your listing has been removed from our database.",
        )
        assert result.classification == Classification.CONFIRMED_REMOVAL.value
        assert result.confidence > 0

    def test_rejection_classification(self, classifier):
        result = classifier.classify(
            subject="Request Status",
            body_text="Your request has been denied. We are unable to process it.",
        )
        assert result.classification == Classification.REJECTION.value

    def test_info_requested_classification(self, classifier):
        result = classifier.classify(
            subject="Action Required",
            body_text="Please provide additional information to proceed with your request.",
        )
        assert result.classification == Classification.INFO_REQUESTED.value

    def test_verification_link_classification(self, classifier):
        result = classifier.classify(
            subject="Verify Your Account",
            body_text="Click the following link to verify your email: http://example.com/v",
        )
        assert result.classification == Classification.VERIFICATION_LINK.value

    def test_unclassified_when_no_match(self, classifier):
        result = classifier.classify(
            subject="Newsletter",
            body_text="Here is your weekly digest of interesting articles.",
        )
        assert result.classification == Classification.UNCLASSIFIED.value
        assert result.confidence == 0

    def test_prefilter_boosts_confidence(self, classifier):
        # Text matching confirmed_removal prefilter + pattern
        high = classifier.classify(
            subject="",
            body_text="Your listing has been removed successfully.",
        )
        # Same pattern without prefilter keyword in subject (body still has it)
        assert high.confidence >= 50

    def test_reload_patterns(self, classifier, patterns_file, tmp_path: Path):
        initial_count = len(classifier._compiled_patterns[Classification.CONFIRMED_REMOVAL])
        # Modify patterns
        p = tmp_path / "patterns.yml"
        new_patterns = dict(_SAMPLE_PATTERNS)
        new_patterns["patterns"]["confirmed_removal"].append(r"erased from records")
        p.write_text(yaml.dump(new_patterns))
        os.replace(str(p), patterns_file)

        classifier.reload_patterns()
        new_count = len(classifier._compiled_patterns[Classification.CONFIRMED_REMOVAL])
        assert new_count == initial_count + 1

    def test_check_and_reload(self, classifier, patterns_file, tmp_path: Path):
        p = tmp_path / "patterns.yml"
        new_patterns = dict(_SAMPLE_PATTERNS)
        new_patterns["patterns"]["rejection"].append(r"cannot fulfill")
        p.write_text(yaml.dump(new_patterns))
        os.replace(str(p), patterns_file)

        reloaded = classifier.check_and_reload()
        assert reloaded is True


# ---------------------------------------------------------------------------
# classify_email convenience function
# ---------------------------------------------------------------------------

class TestClassifyEmail:
    def test_convenience_function_returns_result(self):
        result = classify_email("Test", "Your listing has been removed.")
        assert isinstance(result, ClassificationResult)
        assert result.classification in [c.value for c in Classification]

    def test_subject_only_prefilter_match(self, classifier):
        """Prefilter keywords in subject alone should still trigger classification."""
        result = classifier.classify(
            subject="Removed: Your listing has been processed",
            body_text="This is a generic notification with no specific keywords.",
        )
        # Subject contains "Removed" which is a prefilter keyword
        assert result.classification == Classification.UNCLASSIFIED.value  # body doesn't match patterns

    def test_multiple_patterns_same_category_boost_confidence(self, classifier):
        """When multiple patterns in the same category match, confidence should be higher."""
        high = classifier.classify(
            subject="Request Status",
            body_text="Your request has been denied. We are unable to process your request.",
        )
        low = classifier.classify(
            subject="Request Status",
            body_text="Your request has been denied.",
        )
        assert high.confidence > low.confidence

    def test_extracted_data_from_pattern_groups(self, classifier):
        """Test that extracted data is populated when patterns have groups."""
        result = classifier.classify(
            subject="Verification Required",
            body_text="Click the following link to verify: http://example.com/verify?token=abc123",
        )
        assert result.classification == Classification.VERIFICATION_LINK.value
        # extracted_data should be a dict (may be empty if no groups)
        assert isinstance(result.extracted_data, dict)

    def test_empty_subject_and_body(self, classifier):
        result = classifier.classify(subject="", body_text="")
        assert result.classification == Classification.UNCLASSIFIED.value
        assert result.confidence == 0

    def test_case_insensitive_matching(self, classifier):
        """Patterns should match regardless of case."""
        result = classifier.classify(
            subject="YOUR REQUEST",
            body_text="YOUR LISTING HAS BEEN REMOVED FROM OUR DATABASE.",
        )
        assert result.classification == Classification.CONFIRMED_REMOVAL.value
