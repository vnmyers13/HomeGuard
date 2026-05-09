"""Pydantic models for the Playwright Executor Service."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Action Types ---
class ActionType(str, Enum):
    NAVIGATE = "navigate"
    FILL_FORM = "fill_form"
    CLICK = "click"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    SUBMIT = "submit"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE_TEXT = "type_text"
    CHECK_TEXT = "check_text"
    UNCHECK_TEXT = "uncheck_text"
    DOWNLOAD = "download"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    EXECUTE_JS = "execute_js"


# --- Failure Handling ---
class OnFailure(str, Enum):
    STOP = "stop"
    SKIP_PHASE = "skip_phase"
    MARK_MANUAL = "mark_manual"


# --- Job Status ---
class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    REQUIRES_MANUAL = "requires_manual"
    CANCELLED = "cancelled"


# --- Error Types ---
class ErrorType(str, Enum):
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    NAVIGATION_FAILED = "navigation_failed"
    CAPTCHA_DETECTED = "captcha_detected"
    NETWORK_ERROR = "network_error"
    JAVASCRIPT_ERROR = "javascript_error"
    UNKNOWN = "unknown"


# --- PlaybookStep (executor input) ---
class PlaybookStep(BaseModel):
    """A single playbook step to be executed by the executor."""
    name: str
    description: Optional[str] = None
    actions: list[dict] = []
    screenshot: bool = False
    requires_confirmation: bool = False
    confirmation_timeout: Optional[int] = None


# --- Step Definition (mirrors playbook step structure) ---
class Step(BaseModel):
    """A single action step within a phase."""
    action: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    wait_ms: Optional[int] = None
    text: Optional[str] = None
    script: Optional[str] = None
    screenshot: bool = False
    on_failure: OnFailure = OnFailure.STOP
    condition: Optional[str] = None
    max_iterations: Optional[int] = None
    loop_var: Optional[str] = None


# --- Phase Definition (mirrors playbook phase structure) ---
class Phase(BaseModel):
    """A phase in a broker playbook."""
    name: str
    steps: list[Step] = []


# --- Playbook Structure ---
class Playbook(BaseModel):
    """Broker playbook loaded from JSON."""
    broker_id: str
    version: str = "1.0"
    phases: list[Phase] = []


# --- Step Result ---
class ScreenshotRecord(BaseModel):
    """Reference to a captured screenshot."""
    path: str
    size_bytes: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StepResult(BaseModel):
    """Result of executing a single step."""
    action: ActionType
    status: str = "ok"  # ok | error | skipped
    message: Optional[str] = None
    screenshot: Optional[ScreenshotRecord] = None
    duration_ms: int = 0


# --- Error Result ---
class ErrorResult(BaseModel):
    """Structured error information."""
    error_type: ErrorType = ErrorType.UNKNOWN
    message: str = ""
    recovery_hint: Optional[str] = None
    screenshot: Optional[ScreenshotRecord] = None


# --- Job Result ---
class JobResult(BaseModel):
    """Final result of a scan or optout job."""
    job_id: str
    profile_id: str
    broker_id: str
    job_type: str  # scan | optout
    status: JobStatus = JobStatus.QUEUED
    step_results: list[StepResult] = []
    error: Optional[ErrorResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    screenshots: list[ScreenshotRecord] = []


# --- Job Request Models ---
class ScanJobRequest(BaseModel):
    """Request to execute a scan job."""
    profile_id: str
    broker_id: str
    playbook: Playbook
    tokens: dict[str, Any] = {}
    dry_run: bool = False


class OptoutJobRequest(BaseModel):
    """Request to execute an optout job."""
    profile_id: str
    broker_id: str
    playbook: Playbook
    tokens: dict[str, Any] = {}


# --- Job Submission Response ---
class JobSubmissionResponse(BaseModel):
    """Response when a job is submitted."""
    job_id: str
    status: JobStatus = JobStatus.QUEUED


# --- Health Response ---
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    pool_size: int = 3
    pool_available: int = 3
    pool_busy: int = 0
    chromium_version: Optional[str] = None


# --- Job State (internal tracking) ---
class JobState(BaseModel):
    """Internal state for a running job."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: Optional[JobResult] = None
    task: Any = None  # asyncio.Task reference
    context: Any = None  # browser context reference
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- List Jobs Response ---
class JobListResponse(BaseModel):
    """Response for listing jobs."""
    jobs: list[dict[str, Any]] = []
    total: int = 0


# --- Retry Response (503) ---
class RetryResponse(BaseModel):
    """Response when pool is exhausted."""
    error: str = "pool_exhausted"
    retry_after_ms: int = 10000


# --- Execution State (internal) ---
class ExecutionState(BaseModel):
    """Internal state for playbook execution."""
    job_id: str
    context: dict[str, Any] = {}  # token resolution context
    results: list[dict] = []
    screenshots: list[ScreenshotRecord] = []
    captcha_detected: bool = False


# --- Job Request (unified) ---
class JobRequest(BaseModel):
    """Unified job request for scan or optout."""
    job_id: str
    profile_id: str
    broker_id: str
    job_type: str  # scan | optout
    playbook_steps: list[PlaybookStep] = []
    tokens: dict[str, Any] = {}
    dry_run: bool = False