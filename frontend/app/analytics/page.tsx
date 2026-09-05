"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Activity, ShieldAlert, CheckCircle, Clock, XCircle, PieChart as PieChartIcon, Filter, Download } from "lucide-react";
import { DashboardMetricsResponse } from "@/types/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<DashboardMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<DashboardMetricsResponse>("/api/v1/dashboard/metrics")
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load analytics", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-8 w-8 border-4 border-fintech-blue border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-fintech-muted font-medium">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center">
        <ShieldAlert className="h-10 w-10 text-red-500 mb-2" />
        <h3 className="text-red-700 font-semibold text-lg">Failed to load analytics</h3>
        <p className="text-red-500 text-sm mt-1">Unable to fetch metrics from backend.</p>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value / 100);
  };

  const getInterventionData = () => {
    return Object.entries(metrics.intervention_metrics).map(([name, data]) => ({
      name: name.replace(/_/g, ' '),
      recoveries: data.recoveries,
      revenue: data.recovered_revenue / 100, // INR
    }));
  };

  const getDiagnosisData = () => {
    return Object.entries(metrics.diagnosis_metrics).map(([name, data]) => ({
      name: name.replace(/_/g, ' '),
      revenue: data.recovered_revenue / 100, // INR
    }));
  };

  const getPolicyData = () => {
    return Object.entries(metrics.policy_decisions).map(([name, value]) => ({
      name,
      value
    }));
  };

  // Fintech operations color palette
  const INTERVENTION_COLORS = ['#146BFF', '#0B3B78', '#64748B', '#94A3B8'];
  const DIAGNOSIS_COLORS = ['#16A34A', '#22C55E', '#86EFAC'];
  const POLICY_COLORS: Record<string, string> = { 'ALLOW': '#16A34A', 'DENY': '#E11D48', 'ESCALATE': '#F59E0B' };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-fintech-navy tracking-tight">Recovery Analytics</h1>
          <p className="text-sm text-fintech-muted mt-1">Deep dive into intervention performance and recovery metrics.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 bg-white border border-fintech-border text-fintech-navy px-3 py-2 rounded-lg text-sm font-medium hover:bg-fintech-bg transition-all shadow-sm">
            <Download className="w-4 h-4 text-fintech-muted" />
            Export
          </button>
        </div>
      </div>

      {/* Top Aggregates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-muted tracking-wider uppercase">Overall Recovery Rate</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-3xl font-bold text-fintech-navy">{metrics.recovery_rate.toFixed(1)}%</div>
            <p className="text-xs text-fintech-muted mt-1">Of total failed cases</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-muted tracking-wider uppercase">Total Recovered</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-3xl font-bold text-fintech-success">{formatCurrency(metrics.recovered_revenue)}</div>
            <p className="text-xs text-fintech-muted mt-1">Successfully recovered</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-muted tracking-wider uppercase">Failed Attempts</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-3xl font-bold text-fintech-danger">{metrics.total_failed_attempts}</div>
            <p className="text-xs text-fintech-muted mt-1">Tracked by REVIVE</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recovery by Intervention */}
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
            <CardTitle className="text-base font-semibold text-fintech-navy">Recovery by Intervention</CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-6 min-h-[300px]">
            {getInterventionData().length > 0 && getInterventionData().some(d => d.revenue > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getInterventionData()} layout="vertical" margin={{ top: 0, right: 30, left: 30, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#E6EAF0" />
                  <XAxis type="number" tickFormatter={(val) => `₹${val/1000}k`} stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis dataKey="name" type="category" width={100} stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                  <RechartsTooltip
                    cursor={{ fill: '#F6F8FC' }}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #E6EAF0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(value: any) => [`₹${value}`, "Recovered"]}
                  />
                  <Bar dataKey="revenue" fill="#146BFF" radius={[0, 4, 4, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-fintech-muted">
                <PieChartIcon className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm font-medium">No recovery data available for this period</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recovery by Diagnosis */}
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
            <CardTitle className="text-base font-semibold text-fintech-navy">Recovery by Diagnosis</CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-6 min-h-[300px] flex items-center justify-center">
            {getDiagnosisData().length > 0 && getDiagnosisData().some(d => d.revenue > 0) ? (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getDiagnosisData()}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="revenue"
                    >
                      {getDiagnosisData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={DIAGNOSIS_COLORS[index % DIAGNOSIS_COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ borderRadius: '8px', border: '1px solid #E6EAF0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      formatter={(value: any) => [`₹${value}`, "Recovered"]}
                    />
                  </PieChart>
                </ResponsiveContainer>

                {/* Custom Legend */}
                <div className="w-1/3 flex flex-col gap-3">
                  {getDiagnosisData().map((entry, index) => (
                    <div key={entry.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: DIAGNOSIS_COLORS[index % DIAGNOSIS_COLORS.length] }}></div>
                      <div className="text-xs text-fintech-navy font-medium truncate capitalize">{entry.name.toLowerCase()}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-fintech-muted">
                <Activity className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm font-medium">No diagnosis data available for this period</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policy Decisions */}
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
            <CardTitle className="text-base font-semibold text-fintech-navy">Policy Execution Outcomes</CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-6">
            {getPolicyData().length > 0 && getPolicyData().some(d => d.value > 0) ? (
              <div className="flex items-center h-[300px]">
                <ResponsiveContainer width="60%" height="100%">
                  <PieChart>
                    <Pie
                      data={getPolicyData()}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      dataKey="value"
                      labelLine={false}
                      label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                    >
                      {getPolicyData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={POLICY_COLORS[entry.name] || '#94A3B8'} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ borderRadius: '8px', border: '1px solid #E6EAF0' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-40 ml-auto space-y-4">
                  <div className="text-sm">
                    <div className="text-fintech-muted font-medium mb-1 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-fintech-success"></span>
                      ALLOW
                    </div>
                    <div className="font-bold text-fintech-navy">{metrics.policy_decisions['ALLOW'] || 0} cases</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-fintech-muted font-medium mb-1 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-fintech-danger"></span>
                      DENY
                    </div>
                    <div className="font-bold text-fintech-navy">{metrics.policy_decisions['DENY'] || 0} cases</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-fintech-muted font-medium mb-1 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-fintech-warning"></span>
                      ESCALATE
                    </div>
                    <div className="font-bold text-fintech-navy">{metrics.policy_decisions['ESCALATE'] || 0} cases</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-fintech-muted">
                <ShieldAlert className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm font-medium">No policy data available for this period</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
