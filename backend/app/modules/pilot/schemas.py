"""Pydantic v2 schemas for Phase 9 Controlled Pilot."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PilotFeedbackCreate(BaseModel):
    """Input payload for a farmer or pilot participant submitting task feedback."""

    model_config = ConfigDict(extra="forbid")

    task_type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="e.g. crop_diagnosis, equipment_rental, weather_plan, crop_marketplace, offline_sync, general_onboarding",
    )
    ease_of_use_rating: int = Field(
        ..., ge=1, le=5, description="1 (very difficult) to 5 (very easy)"
    )
    bangla_comprehension_rating: int = Field(
        ..., ge=1, le=5, description="1 (unclear) to 5 (crystal clear)"
    )
    ai_limitations_understood: bool = Field(
        default=True,
        description="User acknowledges AI is decision support, not agricultural officer replacement",
    )
    device_category: str = Field(
        default="low_end_android",
        max_length=50,
        description="low_end_android, mid_android, feature_browser, desktop, other",
    )
    network_type: str = Field(
        default="4g_wifi",
        max_length=50,
        description="2g_slow, 3g, 4g_wifi, offline_intermittent",
    )
    latency_ms: Optional[int] = Field(
        default=None, ge=0, le=60000, description="Observed action latency in ms"
    )
    comments: Optional[str] = Field(
        default=None, max_length=1000, description="Optional qualitative feedback"
    )
    district: Optional[str] = Field(default=None, max_length=100)
    upazila: Optional[str] = Field(default=None, max_length=100)


class PilotFeedbackResponse(BaseModel):
    """Output representation of stored pilot feedback."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    task_type: str
    ease_of_use_rating: int
    bangla_comprehension_rating: int
    ai_limitations_understood: bool
    device_category: str
    network_type: str
    latency_ms: Optional[int]
    comments: Optional[str]
    district: Optional[str]
    upazila: Optional[str]
    created_at: datetime


class PilotDistrictCropConfig(BaseModel):
    """Configuration and guidelines for the controlled pilot."""

    pilot_name: str
    pilot_phase: str
    approved_districts: List[Dict[str, str]]
    approved_crops: List[Dict[str, str]]
    onboarding_checklist: List[Dict[str, str]]
    ai_limitations_notice: str


class ActivationAndTasksMetrics(BaseModel):
    total_users: int
    completed_crop_cases: int
    created_rental_requests: int
    created_crop_listings: int
    processed_sync_records: int


class AIEscalationMetrics(BaseModel):
    total_crop_cases: int
    uncertain_or_unsupported_cases: int
    escalated_cases: int
    corrective_feedback_count: int
    escalation_rate_pct: float


class RentalConversionMetrics(BaseModel):
    total_rental_requests: int
    accepted_rentals: int
    conversion_rate_pct: float


class OfflineSyncReliabilityMetrics(BaseModel):
    total_sync_operations: int
    successful_syncs: int
    sync_success_rate_pct: float


class ModerationVolumeMetrics(BaseModel):
    total_messages: int
    total_reports: int
    pending_reports: int
    report_rate_pct: float


class NetworkAndLatencyMetrics(BaseModel):
    avg_latency_ms: float
    total_latency_samples: int
    network_breakdown: Dict[str, int]
    device_breakdown: Dict[str, int]


class ComprehensionAndUsabilityMetrics(BaseModel):
    total_feedback_submissions: int
    avg_ease_of_use: float
    avg_bangla_comprehension: float
    ai_limitations_comprehension_pct: float


class GoNoGoReadinessChecklist(BaseModel):
    security_safety_ok: bool
    core_journeys_ok: bool
    moderation_capacity_ok: bool
    ai_limitations_understood_ok: bool
    architecture_bottlenecks_measured: bool
    overall_status: str  # "READY_FOR_GO_NO_GO" | "PILOT_IN_PROGRESS"


class PilotTelemetryMetrics(BaseModel):
    """Authoritative platform telemetry for Phase 9 Controlled Pilot."""

    activation_and_tasks: ActivationAndTasksMetrics
    ai_escalation: AIEscalationMetrics
    rental_conversion: RentalConversionMetrics
    offline_sync_reliability: OfflineSyncReliabilityMetrics
    moderation_volume: ModerationVolumeMetrics
    network_and_latency: NetworkAndLatencyMetrics
    comprehension_and_usability: ComprehensionAndUsabilityMetrics
    go_no_go_checklist: GoNoGoReadinessChecklist
