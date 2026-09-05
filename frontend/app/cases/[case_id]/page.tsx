"use client";

import { useEffect, useState, use } from "react";
import { fetchApi } from "../../lib/api";
import { RecoveryCaseDetail } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { CheckCircle2, AlertCircle, Clock, Zap, ArrowRight, Shield, ArrowLeft, BrainCircuit, Activity } from "lucide-react";
import Link from "next/link";

export default function CaseDetailPage({ params }: { params: Promise<{ case_id: string }> }) {
  const unwrappedParams = use(params);
  const [caseData, setCaseData] = useState<RecoveryCaseDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<RecoveryCaseDetail>(`/api/v1/cases/${unwrappedParams.case_id}`)
      .then((data) => {
        setCaseData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load case", err);
        setLoading(false);
      });
  }, [unwrappedParams.case_id]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value / 100);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-8 w-8 border-4 border-fintech-blue border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-fintech-muted font-medium">Loading case details...</p>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center">
        <AlertCircle className="h-10 w-10 text-red-500 mb-2" />
        <h3 className="text-red-700 font-semibold text-lg">Failed to load case</h3>
        <p className="text-red-500 text-sm mt-1">Unable to fetch details for this case.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link href="/cases" className="text-fintech-muted hover:text-fintech-blue transition-colors flex items-center bg-white border border-fintech-border rounded-md px-2 py-1 text-sm font-medium shadow-sm">
              <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </Link>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${
              caseData.status === 'RECOVERED' ? 'bg-green-50 text-fintech-success border-green-100' :
              caseData.status === 'FAILED' ? 'bg-red-50 text-fintech-danger border-red-100' :
              caseData.status === 'IN_PROGRESS' ? 'bg-amber-50 text-fintech-warning border-amber-100' :
              'bg-blue-50 text-fintech-blue border-blue-100'
            }`}>
              {caseData.status.replace(/_/g, ' ')}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-fintech-navy tracking-tight flex items-center gap-2">
            Case <span className="text-fintech-muted font-normal text-xl">#{caseData.id.split('-')[0]}</span>
          </h1>
          <p className="text-sm text-fintech-muted mt-1">Initiated on {formatDate(caseData.created_at)}</p>
        </div>

        <div className="bg-white border border-fintech-border rounded-xl p-4 flex flex-col items-end shadow-sm">
          <span className="text-xs text-fintech-muted font-medium uppercase tracking-wider mb-1">Revenue at Risk</span>
          <span className="text-2xl font-bold text-fintech-navy">{formatCurrency(caseData.revenue_at_risk)}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-sm border-fintech-border rounded-xl">
            <CardHeader className="px-6 py-5 border-b border-fintech-border bg-white">
              <CardTitle className="text-lg font-semibold text-fintech-navy">Recovery Operations Timeline</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="relative border-l-2 border-fintech-border/50 ml-4 space-y-8 pb-4">

                {/* 1. Payment Failure */}
                {caseData.payment_attempt && (
                  <div className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-danger rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Payment Failed</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(caseData.payment_attempt.attempted_at)}</span>
                    </div>
                    <div className="bg-fintech-bg/50 border border-fintech-border rounded-lg p-4 text-sm mt-2">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-fintech-muted text-xs mb-1">Method</div>
                          <div className="font-medium text-fintech-navy">{caseData.payment_attempt.method}</div>
                        </div>
                        <div className="md:col-span-3">
                          <div className="text-fintech-muted text-xs mb-1">Error Reason</div>
                          <div className="font-medium text-fintech-danger">{caseData.payment_attempt.error_reason || caseData.payment_attempt.error_code || "Unknown Gateway Error"}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Diagnosis */}
                {caseData.diagnoses.map((diag, i) => (
                  <div key={diag.id} className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-warning rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Automated Diagnosis</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(diag.diagnosed_at)}</span>
                    </div>
                    <div className="bg-white border border-fintech-border shadow-sm rounded-lg p-4 text-sm mt-2">
                      <div className="flex items-start gap-3">
                        <Activity className="w-5 h-5 text-fintech-warning shrink-0 mt-0.5" />
                        <div>
                          <span className="font-medium text-fintech-navy block mb-1">{diag.failure_category.replace(/_/g, ' ')}</span>
                          <span className="text-fintech-muted">{diag.root_cause_summary}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* 3. ML Prediction */}
                {caseData.predictions.map((pred, i) => (
                  <div key={pred.id} className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-indigo-500 rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Propensity Scoring</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(pred.predicted_at)}</span>
                    </div>
                    <div className="bg-indigo-50/50 border border-indigo-100 rounded-lg p-4 text-sm mt-2">
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="text-indigo-800/60 text-xs mb-1">Retry Prob.</div>
                          <div className="font-medium text-indigo-900">{(pred.recovery_probability_retry * 100).toFixed(1)}%</div>
                        </div>
                        <div>
                          <div className="text-indigo-800/60 text-xs mb-1">Link Prob.</div>
                          <div className="font-medium text-indigo-900">{(pred.recovery_probability_link * 100).toFixed(1)}%</div>
                        </div>
                        <div>
                          <div className="text-indigo-800/60 text-xs mb-1">Risk Score</div>
                          <div className="font-medium text-indigo-900">{(pred.risk_score * 100).toFixed(1)}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* 4. Recommendation */}
                {caseData.recommendations.map((rec, i) => (
                  <div key={rec.id} className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-blue rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Intervention Recommended</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(rec.recommended_at)}</span>
                    </div>
                    <div className="bg-white border border-fintech-border shadow-sm rounded-lg p-4 text-sm mt-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-fintech-blue" />
                          <span className="font-semibold text-fintech-navy">{rec.recommended_intervention.replace(/_/g, ' ')}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-fintech-muted uppercase block">Expected Value</span>
                          <span className="font-semibold text-fintech-success">{formatCurrency(rec.expected_recoverable_amount)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* 5. Policy Decision */}
                {caseData.policy_decisions.map((pol, i) => (
                  <div key={pol.id} className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-muted rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Policy Gate Evaluation</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(pol.evaluated_at)}</span>
                    </div>
                    <div className="bg-white border border-fintech-border shadow-sm rounded-lg p-4 text-sm mt-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-fintech-muted" />
                        <span className="text-fintech-navy font-medium">Intervention: {pol.evaluated_intervention.replace(/_/g, ' ')}</span>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                        pol.decision === 'ALLOW' ? 'bg-green-50 text-fintech-success border border-green-200' :
                        pol.decision === 'DENY' ? 'bg-red-50 text-fintech-danger border border-red-200' :
                        'bg-amber-50 text-fintech-warning border border-amber-200'
                      }`}>
                        {pol.decision}
                      </span>
                    </div>
                  </div>
                ))}

                {/* 6. Execution */}
                {caseData.recovery_actions.map((act, i) => (
                  <div key={act.id} className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-blue rounded-full -left-[9px] top-1 ring-4 ring-white" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Action Executed</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(act.executed_at || act.scheduled_for)}</span>
                    </div>
                    <div className="bg-white border border-fintech-border shadow-sm rounded-lg p-4 text-sm mt-2 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="bg-blue-50 p-2 rounded-full">
                          <Zap className="w-4 h-4 text-fintech-blue" />
                        </div>
                        <div>
                          <span className="font-semibold text-fintech-navy block">{act.action_type.replace(/_/g, ' ')}</span>
                          <span className="text-xs text-fintech-muted">
                            {act.status === 'COMPLETED' ? 'Executed successfully' : act.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* 7. Measurement & Attribution */}
                {caseData.measurement && (
                  <div className="relative pl-8">
                    <div className="absolute w-4 h-4 bg-fintech-success rounded-full -left-[9px] top-1 ring-4 ring-white shadow-[0_0_0_4px_white,0_0_10px_rgba(22,163,74,0.4)]" />
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-fintech-navy">Payment Recovered</h3>
                      </div>
                      <span className="text-xs text-fintech-muted font-medium">{formatDate(caseData.measurement.measured_at)}</span>
                    </div>
                    <div className="bg-green-50/50 border border-green-100 rounded-lg p-5 text-sm mt-2">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-fintech-success">
                          <CheckCircle2 className="w-5 h-5" />
                          <span className="font-bold">Recovery Successful</span>
                        </div>
                        <span className="text-xl font-bold text-fintech-navy">{formatCurrency(caseData.measurement.verified_recovered_amount)}</span>
                      </div>
                      <div className="bg-white rounded p-3 border border-green-100 flex items-center justify-between">
                        <span className="text-xs text-fintech-muted font-medium uppercase tracking-wide">Attribution</span>
                        <span className="text-xs font-bold text-fintech-success bg-green-100 px-2 py-0.5 rounded">
                          {caseData.measurement.attribution_status.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <Card className="shadow-sm border-fintech-border rounded-xl">
            <CardHeader className="px-5 pt-5 pb-3 bg-white border-b border-fintech-border">
              <CardTitle className="text-sm font-semibold text-fintech-navy">Case Summary</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-fintech-border/50 text-sm">
                <div className="px-5 py-3 flex justify-between">
                  <span className="text-fintech-muted">Scenario</span>
                  <span className="font-medium text-fintech-navy capitalize">{caseData.scenario.replace(/_/g, ' ').toLowerCase()}</span>
                </div>
                <div className="px-5 py-3 flex justify-between">
                  <span className="text-fintech-muted">Currency</span>
                  <span className="font-medium text-fintech-navy">{caseData.currency}</span>
                </div>
                {caseData.closed_at && (
                  <div className="px-5 py-3 flex justify-between">
                    <span className="text-fintech-muted">Closed</span>
                    <span className="font-medium text-fintech-navy">{new Date(caseData.closed_at).toLocaleDateString()}</span>
                  </div>
                )}
                {caseData.measurement?.time_to_recovery_seconds && (
                  <div className="px-5 py-3 flex justify-between">
                    <span className="text-fintech-muted">Time to recover</span>
                    <span className="font-medium text-fintech-navy">
                      {Math.round(caseData.measurement.time_to_recovery_seconds / 60)} minutes
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-fintech-border rounded-xl">
            <CardHeader className="px-5 pt-5 pb-3 bg-white border-b border-fintech-border">
              <CardTitle className="text-sm font-semibold text-fintech-navy">System Information</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-fintech-border/50 text-sm">
                <div className="px-5 py-3 flex justify-between">
                  <span className="text-fintech-muted">Case ID</span>
                  <span className="font-mono text-xs text-fintech-navy">{caseData.id.split('-')[0]}</span>
                </div>
                <div className="px-5 py-3 flex justify-between">
                  <span className="text-fintech-muted">Merchant ID</span>
                  <span className="font-mono text-xs text-fintech-navy">{caseData.merchant_id}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
