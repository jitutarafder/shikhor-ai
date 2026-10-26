export type CropCaseStatus = 'possible_match' | 'uncertain' | 'unsupported' | 'failed';

export type FeedbackType = 'helpful' | 'not_helpful' | 'incorrect' | 'unsafe';

export interface CropCase {
  id: string;
  userId: string;
  cropType: string;
  symptomsDescription?: string | null;
  imageFilename: string;
  status: CropCaseStatus;
  possibleCondition?: string | null;
  confidence: number;
  confidenceBand: 'high' | 'medium' | 'low' | 'expert_verified';
  reasonSummary: string[];
  primarySolution?: string | null;
  guidance: string[];
  avoid?: string | null;
  prevention?: string | null;
  specialWarning?: string | null;
  isHealthy?: boolean;
  escalationRecommended: boolean;
  modelVersion: string;
  disclaimer: string;
  isReviewedByExpert?: boolean;
  createdAt: string;
}

export interface TopPrediction {
  class: string;
  crop: string;
  disease: string;
  crop_bn: string;
  disease_bn: string;
  confidence: number;
}

export interface CropDiseasePredictionResult {
  success: boolean;
  is_plant_leaf?: boolean;
  selected_crop?: string;
  selected_crop_bn?: string;
  crop: string;
  crop_bn: string;
  disease: string;
  disease_bn: string;
  raw_class?: string;
  confidence: number;
  uncertain?: boolean;
  sources_used?: string[];
  primary_solution?: string;
  guidance: string[];
  avoid?: string | null;
  prevention?: string | null;
  special_warning?: string | null;
  is_healthy?: boolean;
  final_decision?: {
    crop: string;
    crop_bn: string;
    disease: string;
    disease_bn: string;
    confidence: number;
    uncertain?: boolean;
    primary_solution?: string;
    guidance?: string[];
    avoid?: string | null;
    prevention?: string | null;
    special_warning?: string | null;
    is_healthy?: boolean;
    reason_summary?: string[];
    decision_source?: string;
  };
  vision_result?: Record<string, unknown>;
  banglish_result?: Record<string, unknown>;
  gemini_result?: Record<string, unknown>;
  gemini_available?: boolean;
  banglish_used?: boolean;
  model_used?: string;
  model_name?: string;
  top_predictions: TopPrediction[];
  reason_summary: string[];
  escalation_recommended: boolean;
  disclaimer: string;
}

export interface CropFeedback {
  id: string;
  cropCaseId: string;
  feedbackType: FeedbackType;
  comments?: string | null;
  createdAt: string;
}



