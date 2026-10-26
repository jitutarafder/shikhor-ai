/**
 * Admin, Moderation, and Operational Readiness types.
 * Strictly complies with:
 * - AGENTS.md Rule 12: Object-level authorization (Admin/Moderator roles only).
 * - AGENTS.md Rule 26: Immutable audit logs with actor and request ID.
 * - AGENTS.md Rule 31: Real data only without fake metrics.
 */

export interface AdminMetrics {
  totalUsers: number;
  farmersCount: number;
  buyersCount: number;
  ownersCount: number;
  expertsCount: number;
  activeCropListings: number;
  totalRentalRequests: number;
  pendingModerationReports: number;
  totalAuditEvents: number;
  systemStatus: string;
  timestamp: string;
}

export interface ModerationReportDetail {
  id: string;
  reporterId: string;
  reporterName: string;
  reportedUserId: string;
  reportedUserName: string;
  contentType: string;
  contentId: string;
  reason: string;
  details?: string | null;
  status: string;
  createdAt: string;
}

export interface AdminUser {
  id: string;
  phone: string;
  email?: string | null;
  fullName: string;
  role: string;
  isActive: boolean;
  isVerified: boolean;
  district?: string | null;
  upazila?: string | null;
  nid?: string | null;
  dob?: string | null;
  nidFrontImage?: string | null;
  nidBackImage?: string | null;
  isNidVerified: boolean;
  nidVerificationStatus: string;
  nidRejectionReason?: string | null;
  createdAt: string;
}

export interface AuditLogItem {
  id: string;
  actorId?: string | null;
  actorPhone: string;
  actorRole: string;
  action: string;
  resourceType: string;
  resourceId: string;
  details: string;
  requestId?: string | null;
  createdAt: string;
}

export interface KnowledgeArticleCreateInput {
  cropType: string;
  category: string;
  titleBn: string;
  titleEn?: string;
  summaryBn: string;
  contentBn: string;
  recommendedPracticesBn?: string;
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'dead_letter' | 'cancelled';

export interface BackgroundJob {
  id: string;
  jobType: string;
  payload: Record<string, unknown>;
  status: JobStatus;
  priority: number;
  attempts: number;
  maxAttempts: number;
  lastError?: string | null;
  resultData?: Record<string, unknown> | null;
  lockedBy?: string | null;
  scheduledAt: string;
  createdAt: string;
  completedAt?: string | null;
}

export interface JobStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  deadLetter: number;
  activeWorkers: number;
}
