export interface ActionMetrics {
  total: number;
  successful: number;
  failed: number;
  pending: number;
}

export interface InterventionMetric {
  recoveries: number;
  recovered_revenue: number;
}

export interface DashboardMetricsResponse {
  total_failed_attempts: number;
  total_cases: number;
  open_cases: number;
  recovered_cases: number;
  recovery_rate: number;
  revenue_at_risk: number;
  recovered_revenue: number;
  attributed_revenue: number;
  unattributed_revenue: number;
  actions: ActionMetrics;
  policy_decisions: Record<string, number>;
  intervention_metrics: Record<string, InterventionMetric>;
  diagnosis_metrics: Record<string, InterventionMetric>;
  method_metrics: Record<string, InterventionMetric>;
}

export interface RecoveryCaseSummary {
  id: string;
  scenario: string;
  status: string;
  revenue_at_risk: number;
  currency: string;
  created_at: string;
  closed_at: string | null;
  razorpay_order_id: string | null;
}

export interface PaginatedCasesResponse {
  items: RecoveryCaseSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface PaymentAttemptDetail {
  id: string;
  method: string;
  status: string;
  error_code: string | null;
  error_reason: string | null;
  attempted_at: string;
}

export interface DiagnosisDetail {
  id: string;
  failure_category: string;
  is_retryable: boolean;
  root_cause_summary: string;
  diagnosed_at: string;
}

export interface PredictionDetail {
  id: string;
  risk_score: number;
  recovery_probability_retry: number;
  recovery_probability_link: number;
  recovery_probability_nudge: number;
  predicted_at: string;
}

export interface RecommendationDetail {
  id: string;
  recommended_intervention: string;
  expected_recoverable_amount: number;
  recommended_at: string;
}

export interface PolicyDecisionDetail {
  id: string;
  decision: string;
  evaluated_intervention: string;
  rejection_reasons: Record<string, any>;
  evaluated_at: string;
}

export interface RecoveryActionDetail {
  id: string;
  action_type: string;
  status: string;
  scheduled_for: string;
  executed_at: string | null;
  error_message: string | null;
}

export interface RecoveryMeasurementDetail {
  id: string;
  attribution_status: string;
  verified_recovered_amount: number;
  time_to_recovery_seconds: number | null;
  attribution_basis: Record<string, any>;
  measured_at: string;
}

export interface RecoveryCaseDetail {
  id: string;
  merchant_id: string;
  scenario: string;
  status: string;
  revenue_at_risk: number;
  currency: string;
  created_at: string;
  closed_at: string | null;

  payment_attempt: PaymentAttemptDetail | null;
  diagnoses: DiagnosisDetail[];
  predictions: PredictionDetail[];
  recommendations: RecommendationDetail[];
  policy_decisions: PolicyDecisionDetail[];
  recovery_actions: RecoveryActionDetail[];
  measurement: RecoveryMeasurementDetail | null;
}
