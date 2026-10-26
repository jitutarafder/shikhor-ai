/**
 * TypeScript types for Expert Case-Review Portal.
 */

export interface ExpertCaseReviewCreateInput {
  reviewedDiagnosis: string;
  prescribedTreatment: string;
  severityLevel?: string;
  expertNotes?: string;
}

export interface ExpertCaseReview {
  id: string;
  cropCaseId: string;
  expertId: string;
  expertName: string;
  reviewedDiagnosis: string;
  prescribedTreatment: string;
  severityLevel: string;
  expertNotes: string | null;
  createdAt: string;
}
