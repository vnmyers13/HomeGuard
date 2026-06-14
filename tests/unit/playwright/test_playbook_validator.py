"""Unit tests for playbook model validation and structure."""

import json
import pytest

playwright_models = pytest.importorskip("gw_playwright.models", reason="gw_playwright module not available")

from models import (
    ActionType,
    ErrorType,
    JobStatus,
    OnFailure,
    Phase,
    Playbook,
    PlaybookStep,
    Step,
)


class TestPlaybookModel:
    """Tests for Playbook Pydantic model validation."""

    def test_minimal_playbook(self):
        pb = Playbook(broker_id="spokeo.com")
        assert pb.broker_id == "spokeo.com"
        assert pb.version == "1.0"
        assert pb.phases == []

    def test_playbook_with_phases(self):
        phase = Phase(name="search", steps=[])
        pb = Playbook(broker_id="spokeo.com", version="2.0", phases=[phase])
        assert len(pb.phases) == 1
        assert pb.phases[0].name == "search"

    def test_playbook_from_dict(self):
        data = {
            "broker_id": "whitepages.com",
            "version": "1.5",
            "phases": [
                {
                    "name": "navigate",
                    "steps": [
                        {
                            "action": "navigate",
                            "url": "https://example.com/search",
                        }
                    ],
                }
            ],
        }
        pb = Playbook.model_validate(data)
        assert pb.broker_id == "whitepages.com"
        assert len(pb.phases) == 1

    def test_playbook_json_roundtrip(self):
        pb = Playbook(broker_id="test.com", version="1.0")
        json_str = pb.model_dump_json()
        restored = Playbook.model_validate_json(json_str)
        assert restored.broker_id == "test.com"

    def test_playbook_missing_broker_id_fails(self):
        with pytest.raises(Exception):
            Playbook.model_validate({"version": "1.0"})


class TestStepModel:
    """Tests for Step Pydantic model."""

    def test_minimal_step(self):
        step = Step(action=ActionType.NAVIGATE)
        assert step.action == ActionType.NAVIGATE
        assert step.screenshot is False
        assert step.on_failure == OnFailure.STOP

    def test_step_with_all_fields(self):
        step = Step(
            action=ActionType.FILL_FORM,
            selector="#name",
            value="{{full_name}}",
            screenshot=True,
            on_failure=OnFailure.SKIP_PHASE,
        )
        assert step.selector == "#name"
        assert step.value == "{{full_name}}"
        assert step.screenshot is True

    def test_step_from_dict(self):
        data = {"action": "click", "selector": "#submit-btn"}
        step = Step.model_validate(data)
        assert step.action == ActionType.CLICK

    def test_invalid_action_raises(self):
        with pytest.raises(Exception):
            Step.model_validate({"action": "invalid_action_type"})


class TestPhaseModel:
    """Tests for Phase Pydantic model."""

    def test_phase_with_steps(self):
        step = Step(action=ActionType.NAVIGATE, url="https://example.com")
        phase = Phase(name="search", steps=[step])
        assert len(phase.steps) == 1
        assert phase.steps[0].url == "https://example.com"

    def test_phase_empty_steps(self):
        phase = Phase(name="empty")
        assert phase.steps == []


class TestPlaybookStepModel:
    """Tests for PlaybookStep executor input model."""

    def test_minimal_playbook_step(self):
        step = PlaybookStep(name="navigate")
        assert step.name == "navigate"
        assert step.actions == []
        assert step.screenshot is False

    def test_playbook_step_with_actions(self):
        actions = [{"type": "navigate", "params": {"url": "https://example.com"}}]
        step = PlaybookStep(
            name="go_to_site",
            description="Navigate to broker site",
            actions=actions,
            screenshot=True,
        )
        assert len(step.actions) == 1
        assert step.screenshot is True


class TestEnums:
    """Tests for enum values matching expected strings."""

    def test_action_type_values(self):
        assert ActionType.NAVIGATE.value == "navigate"
        assert ActionType.FILL_FORM.value == "fill_form"
        assert ActionType.CLICK.value == "click"
        assert ActionType.SCREENSHOT.value == "screenshot"

    def test_job_status_values(self):
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.ERROR.value == "error"

    def test_error_type_values(self):
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.CAPTCHA_DETECTED.value == "captcha_detected"

    def test_on_failure_values(self):
        assert OnFailure.STOP.value == "stop"
        assert OnFailure.SKIP_PHASE.value == "skip_phase"
        assert OnFailure.MARK_MANUAL.value == "mark_manual"


class TestPlaybookFromFile:
    """Tests loading real playbook JSON files and extracting phases."""

    def test_load_spokeo_playbook_json(self):
        """Verify raw JSON structure has expected keys."""
        with open("playbooks/brokers/spokeo.com.json") as f:
            data = json.load(f)
        assert data["canonical_domain"] == "spokeo.com"
        assert len(data["phases"]) >= 1

    def test_load_whitepages_playbook_json(self):
        with open("playbooks/brokers/whitepages.com.json") as f:
            data = json.load(f)
        assert "canonical_domain" in data
        assert len(data["phases"]) >= 1

    def test_playbook_phases_have_steps(self):
        with open("playbooks/brokers/spokeo.com.json") as f:
            data = json.load(f)
        for phase in data["phases"]:
            assert len(phase["steps"]) >= 1
            for step in phase["steps"]:
                assert "step_id" in step
                assert "action" in step

    def test_playbook_model_with_converted_data(self):
        """Build a Playbook model from playbook JSON phases."""
        with open("playbooks/brokers/spokeo.com.json") as f:
            raw = json.load(f)

        # Convert playbook JSON phases to model-compatible format
        phases = []
        for phase_data in raw["phases"]:
            steps = []
            for step_data in phase_data["steps"]:
                # Map action string to Step model
                step_dict = {"action": step_data["action"]}
                if "selector" in step_data:
                    step_dict["selector"] = step_data["selector"]
                if "timeout_ms" in step_data:
                    step_dict["wait_ms"] = step_data["timeout_ms"]
                steps.append(Step.model_validate(step_dict))
            phases.append(Phase(name=phase_data["name"], steps=steps))

        pb = Playbook(broker_id=raw["canonical_domain"], phases=phases)
        assert pb.broker_id == "spokeo.com"
        assert len(pb.phases) >= 1