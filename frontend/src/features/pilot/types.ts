/**
 * TypeScript types for Phase 9 Controlled Pilot.
 */

export interface PilotDistrict {
  code: string;
  name_bn: string;
  name_en: string;
  focus: string;
}

export interface PilotCrop {
  code: string;
  name_bn: string;
  season: string;
}

export interface OnboardingStep {
  step: string;
  desc_bn: string;
}

export interface PilotDistrictCropConfig {
  pilot_name: string;
  pilot_phase: string;
  approved_districts: PilotDistrict[];
  approved_crops: PilotCrop[];
  onboarding_checklist: OnboardingStep[];
  ai_limitations_notice: string;
}

export interface PilotFeedbackCreateInput {
  task_type: string;
  ease_of_use_rating: number;
  bangla_comprehension_rating: number;
  ai_limitations_understood: boolean;
  device_category: string;
  network_type: string;
  latency_ms?: number;
  comments?: string;
  district?: string;
  upazila?: string;
}

export interface PilotFeedback {
  id: string;
  user_id: string;
  task_type: string;
  ease_of_use_rating: number;
  bangla_comprehension_rating: number;
  ai_limitations_understood: boolean;
  device_category: string;
  network_type: string;
  latency_ms: number | null;
  comments: string | null;
  district: string | null;
  upazila: string | null;
  created_at: string;
}

export interface ActivationAndTasksMetrics {
  total_users: number;
  completed_crop_cases: number;
  created_rental_requests: number;
  created_crop_listings: number;
  processed_sync_records: number;
}

export interface AIEscalationMetrics {
  total_crop_cases: number;
  uncertain_or_unsupported_cases: number;
  escalated_cases: number;
  corrective_feedback_count: number;
  escalation_rate_pct: number;
}

export interface RentalConversionMetrics {
  total_rental_requests: number;
  accepted_rentals: number;
  conversion_rate_pct: number;
}

export interface OfflineSyncReliabilityMetrics {
  total_sync_operations: number;
  successful_syncs: number;
  sync_success_rate_pct: number;
}

export interface ModerationVolumeMetrics {
  total_messages: number;
  total_reports: number;
  pending_reports: number;
  report_rate_pct: number;
}

export interface NetworkAndLatencyMetrics {
  avg_latency_ms: number;
  total_latency_samples: number;
  network_breakdown: Record<string, number>;
  device_breakdown: Record<string, number>;
}

export interface ComprehensionAndUsabilityMetrics {
  total_feedback_submissions: number;
  avg_ease_of_use: number;
  avg_bangla_comprehension: number;
  ai_limitations_comprehension_pct: number;
}

export interface GoNoGoReadinessChecklist {
  security_safety_ok: boolean;
  core_journeys_ok: boolean;
  moderation_capacity_ok: boolean;
  ai_limitations_understood_ok: boolean;
  architecture_bottlenecks_measured: boolean;
  overall_status: 'READY_FOR_GO_NO_GO' | 'PILOT_IN_PROGRESS';
}

export interface PilotTelemetryMetrics {
  activation_and_tasks: ActivationAndTasksMetrics;
  ai_escalation: AIEscalationMetrics;
  rental_conversion: RentalConversionMetrics;
  offline_sync_reliability: OfflineSyncReliabilityMetrics;
  moderation_volume: ModerationVolumeMetrics;
  network_and_latency: NetworkAndLatencyMetrics;
  comprehension_and_usability: ComprehensionAndUsabilityMetrics;
  go_no_go_checklist: GoNoGoReadinessChecklist;
}
