"""
Email Classification Engine
Classifies inbound emails into removal-related categories using rule-based patterns
and optional AI enhancement via OpenAI-compatible APIs.

Patterns are loaded from patterns.yml and support hot-reload on file modification.
Two-stage classification: Stage 1 pre-filter keywords for fast rejection,
Stage 2 detailed regex patterns for accurate classification.
"""
import json
import logging
import os
import re
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


class Classification(str, Enum):
    """Email classification categories."""
    CONFIRMED_REMOVAL = "confirmed_removal"
    REJECTION = "rejection"
    INFO_REQUESTED = "info_requested"
    VERIFICATION_LINK = "verification_link"
    UNCLASSIFIED = "unclassified"


# Default patterns path relative to this module
_DEFAULT_PATTERNS_PATH = os.path.join(os.path.dirname(__file__), "patterns.yml")


class PatternsLoader:
    """Loads and caches classification patterns from YAML, with hot-reload on mtime."""

    def __init__(self, patterns_path: Optional[str] = None):
        self.patterns_path = patterns_path or _DEFAULT_PATTERNS_PATH
        self._patterns_cache: Optional[dict] = None
        self._mtime: float = 0

    def load(self) -> dict:
        """Load patterns from YAML file, respecting mtime for hot-reload."""
        current_mtime = os.path.getmtime(self.patterns_path)
        if self._patterns_cache is not None and current_mtime == self._mtime:
            return self._patterns_cache

        with open(self.patterns_path, "r") as f:
            patterns = yaml.safe_load(f)

        self._patterns_cache = patterns
        self._mtime = current_mtime
        logger.info("Loaded classification patterns from %s", self.patterns_path)
        return self._patterns_cache

    def reload_if_changed(self) -> bool:
        """Check if patterns file has changed and reload if needed. Returns True if reloaded."""
        current_mtime = os.path.getmtime(self.patterns_path)
        if current_mtime != self._mtime:
            self.load()
            return True
        return False


class ClassificationResult:
    """Result of classifying an email."""

    def __init__(
        self,
        classification: str,
        confidence: int = 0,
        matched_pattern: Optional[str] = None,
        extracted_data: Optional[dict] = None,
    ):
        self.classification = classification
        self.confidence = max(0, min(100, confidence))
        self.matched_pattern = matched_pattern
        self.extracted_data = extracted_data or {}

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "confidence": self.confidence,
            "matched_pattern": self.matched_pattern,
            "extracted_data": self.extracted_data,
        }


class EmailClassifier:
    """
    Classifies inbound emails into removal-related categories.

    Uses a two-tier, two-stage approach:
    1. Rule-based pattern matching (always active)
       - Stage 1: Pre-filter keywords for fast rejection
       - Stage 2: Detailed regex patterns for classification
    2. Optional AI classification via OpenAI-compatible API

    Patterns are loaded from patterns.yml and hot-reloaded on mtime change.
    """

    def __init__(
        self,
        patterns_path: Optional[str] = None,
        ai_enabled: bool = False,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        ai_threshold: int = 60,
    ):
        """
        Args:
            patterns_path: Path to patterns.yml file. Defaults to module directory.
            ai_enabled: Enable AI-based classification fallback.
            api_key: API key for OpenAI-compatible service.
            base_url: Base URL for custom OpenAI-compatible endpoint.
            model: Model name to use for AI classification.
            ai_threshold: Minimum rule-based confidence to skip AI fallback.
        """
        self.patterns_loader = PatternsLoader(patterns_path)
        self.ai_enabled = ai_enabled
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.ai_threshold = ai_threshold

        # Pre-compiled patterns cache (invalidated on reload)
        self._compiled_patterns: dict = {}
        self._prefilter_keywords: dict = {}

        # Initial load and compile
        self._compile_patterns()

    def _compile_patterns(self):
        """Load patterns from YAML and compile regexes."""
        raw = self.patterns_loader.load()

        # Compile prefilter keywords (Stage 1)
        raw_keywords = raw.get("prefilter_keywords", {})
        self._prefilter_keywords = {}
        for category, keywords in raw_keywords.items():
            # Build a single regex that matches any keyword (case-insensitive word boundary)
            escaped = [re.escape(kw) for kw in keywords]
            pattern_str = r"\b(?:%s)\b" % "|".join(escaped)
            self._prefilter_keywords[category] = re.compile(pattern_str, re.IGNORECASE)

        # Compile detailed patterns (Stage 2)
        raw_patterns = raw.get("patterns", {})
        self._compiled_patterns = {}
        for classification in Classification:
            patterns = raw_patterns.get(classification.value, [])
            self._compiled_patterns[classification] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def reload_patterns(self):
        """Force reload of patterns from YAML file."""
        self._compile_patterns()

    def check_and_reload(self) -> bool:
        """Check if patterns file changed and reload if needed. Returns True if reloaded."""
        if self.patterns_loader.reload_if_changed():
            self._compile_patterns()
            return True
        return False

    def classify(
        self, subject: str, body_text: str, from_address: str = ""
    ) -> ClassificationResult:
        """
        Classify an email using two-stage rule-based patterns, with optional AI fallback.

        Stage 1: Pre-filter keywords for fast classification/rejection
        Stage 2: Detailed regex patterns for accurate classification

        Args:
            subject: Email subject line.
            body_text: Plain text body of the email.
            from_address: Sender address (used for AI context).

        Returns:
            ClassificationResult with category, confidence, and metadata.
        """
        # Combine subject and body for pattern matching
        text = f"{subject} {body_text}".strip()

        # Step 1: Rule-based classification (two-stage)
        result = self._classify_rules(text)

        # Step 2: AI fallback if confidence is low
        if result.confidence < self.ai_threshold and self.ai_enabled:
            ai_result = self._classify_ai(text, from_address)
            if ai_result and ai_result.confidence > result.confidence:
                result = ai_result

        return result

    def _classify_rules(self, text: str) -> ClassificationResult:
        """Classify using two-stage approach: prefilter keywords then detailed regex."""
        best_classification = Classification.UNCLASSIFIED
        best_confidence = 0
        best_pattern = None

        # Stage 1: Pre-filter keywords (fast path)
        prefilter_match = None
        for category, pattern in self._prefilter_keywords.items():
            if pattern.search(text):
                prefilter_match = category
                break

        # Stage 2: Detailed regex patterns
        if prefilter_match:
            # If pre-filter matched, prioritize that category but still check all
            for classification, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    match = pattern.search(text)
                    if match:
                        # Boost confidence for pre-filter matched category
                        confidence = min(100, 50 + len(match.group()) * 2)
                        if classification == prefilter_match:
                            confidence = min(100, confidence + 10)
                        if confidence > best_confidence:
                            best_classification = classification
                            best_confidence = confidence
                            best_pattern = pattern.pattern
        else:
            # No pre-filter match, check all patterns normally
            for classification, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    match = pattern.search(text)
                    if match:
                        confidence = min(100, 50 + len(match.group()) * 2)
                        if confidence > best_confidence:
                            best_classification = classification
                            best_confidence = confidence
                            best_pattern = pattern.pattern

        return ClassificationResult(
            classification=best_classification.value,
            confidence=best_confidence,
            matched_pattern=best_pattern,
        )

    def _classify_ai(self, text: str, from_address: str = "") -> Optional[ClassificationResult]:
        """Classify using AI (OpenAI-compatible API)."""
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not available for AI classification, skipping")
            return None

        if not self.api_key:
            logger.warning("AI classification enabled but no API key provided")
            return None

        prompt = self._build_classification_prompt(text, from_address)

        client_kwargs = {
            "api_key": self.api_key,
            "timeout": 30.0,
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        try:
            with httpx.Client(**client_kwargs) as client:
                response = client.post(
                    "/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self._SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)

            return ClassificationResult(
                classification=result.get("classification", "unclassified"),
                confidence=int(result.get("confidence", 50)),
                matched_pattern=result.get("reasoning"),
                extracted_data=result.get("extracted_data"),
            )

        except Exception as e:
            logger.error("AI classification failed: %s", e)
            return None

    def _build_classification_prompt(self, text: str, from_address: str = "") -> str:
        """Build the prompt for AI classification."""
        prompt = f"""Classify this email into one of these categories:
- confirmed_removal: The listing/profile has been successfully removed
- rejection: The removal request was denied or cannot be processed
- info_requested: Additional information is needed from the user
- verification_link: Contains a verification link or OTP code
- unclassified: Does not fit any of the above categories

Email Details:
From: {from_address}
Subject: {text[:200]}

Body (first 1500 chars):
{text[200:1700]}

Return JSON with: classification, confidence (0-100), reasoning, extracted_data (if any)"""
        return prompt

    @property
    def _SYSTEM_PROMPT(self) -> str:
        return (
            "You are an email classification assistant for a data removal management system. "
            "Classify emails related to opt-out and data removal requests from people-search brokers. "
            "Return only valid JSON matching the specified schema."
        )


# Singleton instance for module-level use
_default_classifier = EmailClassifier()


def classify_email(
    subject: str, body_text: str, from_address: str = ""
) -> ClassificationResult:
    """Convenience function to classify an email using the default classifier."""
    return _default_classifier.classify(subject, body_text, from_address)