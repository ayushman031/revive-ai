"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { ShieldAlert, Download, Activity, Target, Zap, ArrowUpRight, ArrowDownRight, Info } from "lucide-react";
import { EvaluationResponse } from "@/types/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from "recharts";

export default function EvaluationPage() {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<EvaluationResponse>("/api/v1/evaluation")
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load evaluation results", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-8 w-8 border-4 border-fintech-blue border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-fintech-muted font-medium">Loading evaluation metrics...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center">
        <ShieldAlert className="h-10 w-10 text-red-500 mb-2" />
        <h3 className="text-red-700 font-semibold text-lg">Failed to load evaluation</h3>
        <p className="text-red-500 text-sm mt-1">Unable to fetch evaluation artifact from backend.</p>
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

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getDeltaValue = (key: string) => data.deltas[key]?.absolute_delta ?? 0;
  
  // Chart Data
  const rateChartData = [
    {
      name: "Recovery Rate",
      Baseline: data.baseline.recovery_rate * 100,
      REVIVE: data.revive.recovery_rate * 100,
    }
  ];

  const revenueChartData = [
    {
      name: "Recovered Revenue",
      Baseline: data.baseline.recovered_revenue / 100,
      REVIVE: data.revive.recovered_revenue / 100,
    },
    {
      name: "Net Recovered",
      Baseline: data.baseline.net_recovered_revenue / 100,
      REVIVE: data.revive.net_recovered_revenue / 100,
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-fintech-blue/10 text-fintech-blue px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">PHASE 7</span>
            <h1 className="text-3xl font-bold text-fintech-navy tracking-tight">Evaluation</h1>
          </div>
          <p className="text-sm text-fintech-muted mt-1">Reproducible comparison of REVIVE against a deterministic baseline.</p>
        </div>
      </div>

      {/* Top Aggregates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-muted tracking-wider uppercase">Transactions Evaluated</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-2xl font-bold text-fintech-navy">{data.metadata.dataset_size.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-muted tracking-wider uppercase">Revenue At Risk</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-2xl font-bold text-fintech-navy">{formatCurrency(data.metadata.revenue_at_risk)}</div>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-fintech-success/30 rounded-xl bg-green-50/50">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-success tracking-wider uppercase flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5" />
              Recovery Rate
            </CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-2xl font-bold text-fintech-success">+{getDeltaValue("Recovery Rate").toFixed(2)} pp</div>
            <p className="text-xs text-fintech-muted mt-1">Absolute improvement</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-fintech-success/30 rounded-xl bg-green-50/50">
          <CardHeader className="px-5 pt-5 pb-2">
            <CardTitle className="text-[11px] font-bold text-fintech-success tracking-wider uppercase flex items-center gap-1">
              <ArrowUpRight className="w-3.5 h-3.5" />
              Net Recovered Revenue
            </CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-2xl font-bold text-fintech-success">+{formatCurrency(getDeltaValue("Net Recovered Revenue") * 100)}</div>
            <p className="text-xs text-fintech-muted mt-1">Incremental net revenue</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recovery Rate Chart */}
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
            <CardTitle className="text-base font-semibold text-fintech-navy">Recovery Rate Comparison</CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-6 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rateChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6EAF0" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}%`} />
                <RechartsTooltip cursor={{ fill: '#F6F8FC' }} formatter={(val: any) => [`${Number(val).toFixed(2)}%`, ""]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} maxBarSize={60} />
                <Bar dataKey="REVIVE" fill="#146BFF" radius={[4, 4, 0, 0]} maxBarSize={60} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Revenue Comparison Chart */}
        <Card className="shadow-sm border-fintech-border rounded-xl">
          <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
            <CardTitle className="text-base font-semibold text-fintech-navy">Revenue Comparison</CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-6 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueChartData} margin={{ top: 20, right: 30, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6EAF0" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val/1000}k`} />
                <RechartsTooltip cursor={{ fill: '#F6F8FC' }} formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, ""]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} maxBarSize={60} />
                <Bar dataKey="REVIVE" fill="#16A34A" radius={[4, 4, 0, 0]} maxBarSize={60} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Comparison Table */}
        <div className="lg:col-span-2">
          <Card className="shadow-sm border-fintech-border rounded-xl h-full">
            <CardHeader className="px-5 pt-5 pb-4 border-b border-fintech-border bg-white">
              <CardTitle className="text-base font-semibold text-fintech-navy">Metric Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-[#F8FAFC] text-fintech-muted border-b border-fintech-border">
                  <tr>
                    <th className="px-5 py-3 font-semibold uppercase tracking-wider text-[11px]">Metric</th>
                    <th className="px-5 py-3 font-semibold uppercase tracking-wider text-[11px]">Baseline</th>
                    <th className="px-5 py-3 font-semibold uppercase tracking-wider text-[11px]">REVIVE</th>
                    <th className="px-5 py-3 font-semibold uppercase tracking-wider text-[11px] text-right">Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-fintech-border text-fintech-navy">
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium">Recovery Rate</td>
                    <td className="px-5 py-4">{formatPercentage(data.baseline.recovery_rate)}</td>
                    <td className="px-5 py-4 font-semibold text-fintech-blue">{formatPercentage(data.revive.recovery_rate)}</td>
                    <td className="px-5 py-4 text-right font-semibold text-fintech-success">+{getDeltaValue("Recovery Rate").toFixed(2)} pp</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium">Recovered Revenue</td>
                    <td className="px-5 py-4">{formatCurrency(data.baseline.recovered_revenue)}</td>
                    <td className="px-5 py-4 font-semibold">{formatCurrency(data.revive.recovered_revenue)}</td>
                    <td className="px-5 py-4 text-right font-semibold text-fintech-success">+{formatCurrency(getDeltaValue("Recovered Revenue") * 100)}</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium">Intervention Cost</td>
                    <td className="px-5 py-4">{formatCurrency(data.baseline.intervention_cost)}</td>
                    <td className="px-5 py-4">{formatCurrency(data.revive.intervention_cost)}</td>
                    <td className="px-5 py-4 text-right font-semibold text-fintech-danger">+{formatCurrency(getDeltaValue("Intervention Cost") * 100)}</td>
                  </tr>
                  <tr className="bg-[#F0FDF4] hover:bg-[#E8FCEE] transition-colors border-y-2 border-green-100">
                    <td className="px-5 py-4 font-bold text-green-800">Net Recovered Revenue</td>
                    <td className="px-5 py-4 font-semibold text-green-700">{formatCurrency(data.baseline.net_recovered_revenue)}</td>
                    <td className="px-5 py-4 font-bold text-green-700">{formatCurrency(data.revive.net_recovered_revenue)}</td>
                    <td className="px-5 py-4 text-right font-bold text-fintech-success">+{formatCurrency(getDeltaValue("Net Recovered Revenue") * 100)}</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium flex items-center gap-1">Unnecessary Intervention Rate</td>
                    <td className="px-5 py-4">{formatPercentage(data.baseline.unnecessary_intervention_rate)}</td>
                    <td className="px-5 py-4 font-semibold">{formatPercentage(data.revive.unnecessary_intervention_rate)}</td>
                    <td className="px-5 py-4 text-right font-semibold text-fintech-blue">{getDeltaValue("Unnecessary Interventions Rate").toFixed(2)} pp</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium">Policy Violations</td>
                    <td className="px-5 py-4">{data.baseline.policy_violations}</td>
                    <td className="px-5 py-4">{data.revive.policy_violations}</td>
                    <td className="px-5 py-4 text-right text-fintech-muted">0</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-medium flex items-center gap-1">Average Simulated Recovery Latency</td>
                    <td className="px-5 py-4">{data.baseline.average_recovery_latency.toFixed(1)} min</td>
                    <td className="px-5 py-4">{data.revive.average_recovery_latency.toFixed(1)} min</td>
                    <td className="px-5 py-4 text-right text-fintech-warning">+{getDeltaValue("Average Recovery Latency").toFixed(1)} min</td>
                  </tr>
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>

        {/* Side Panel: Efficiency & Methodology */}
        <div className="space-y-6">
          <Card className="shadow-sm border-fintech-border rounded-xl">
            <CardHeader className="px-5 pt-5 pb-2">
              <CardTitle className="text-base font-semibold text-fintech-navy">Efficiency</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <div className="bg-blue-50/50 rounded-lg p-4 border border-blue-100 flex flex-col items-center justify-center text-center">
                <Target className="w-8 h-8 text-fintech-blue mb-3" />
                <div className="text-sm text-fintech-muted font-medium mb-1 uppercase tracking-wider">Unnecessary Intervention Rate</div>
                <div className="flex items-center justify-center gap-3 w-full my-2">
                  <span className="text-xl font-bold text-slate-500 line-through">{formatPercentage(data.baseline.unnecessary_intervention_rate)}</span>
                  <ArrowDownRight className="w-5 h-5 text-fintech-blue" />
                  <span className="text-2xl font-bold text-fintech-blue">{formatPercentage(data.revive.unnecessary_intervention_rate)}</span>
                </div>
                <div className="text-sm font-semibold text-fintech-blue bg-white px-3 py-1 rounded-full shadow-sm border border-blue-100">
                  {getDeltaValue("Unnecessary Interventions Rate").toFixed(2)} pp
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-fintech-border rounded-xl">
            <CardHeader className="px-5 pt-5 pb-2 bg-slate-50 rounded-t-xl border-b border-fintech-border">
              <CardTitle className="text-[13px] font-bold text-slate-700 tracking-wider flex items-center gap-2">
                <Info className="w-4 h-4 text-fintech-muted" />
                Methodology & Assumptions
              </CardTitle>
            </CardHeader>
            <CardContent className="px-5 py-4 text-xs text-slate-600 space-y-3 leading-relaxed bg-white rounded-b-xl">
              <div>
                <span className="font-semibold text-slate-800">Dataset:</span> {data.metadata.dataset_size.toLocaleString()} deterministic synthetic transaction scenarios.
              </div>
              <div>
                <span className="font-semibold text-slate-800">Baseline:</span> <code>AlwaysRetryBaseline</code>.
              </div>
              <div>
                <span className="font-semibold text-slate-800">REVIVE:</span> Existing diagnosis + ML inference + intervention selection + frozen policy gate.
              </div>
              <div>
                <span className="font-semibold text-slate-800">Ground truth:</span> Synthetic intervention-specific targets generated independently of model predictions.
              </div>
              <div className="border-t border-slate-100 pt-2 mt-2">
                <span className="font-bold text-slate-700 block mb-1">Evaluation assumptions (Costs):</span>
                <ul className="list-disc pl-4 space-y-0.5">
                  <li>retry = ₹{data.metadata.assumptions.costs.retry}</li>
                  <li>link = ₹{data.metadata.assumptions.costs.link}</li>
                  <li>nudge = ₹{data.metadata.assumptions.costs.nudge}</li>
                </ul>
              </div>
              <div className="border-t border-slate-100 pt-2">
                <span className="font-bold text-slate-700 block mb-1">Simulated recovery latency — not observed production latency:</span>
                <ul className="list-disc pl-4 space-y-0.5">
                  <li>retry = {data.metadata.assumptions.latency_minutes.retry} min</li>
                  <li>link = {data.metadata.assumptions.latency_minutes.link} min</li>
                  <li>nudge = {data.metadata.assumptions.latency_minutes.nudge} min</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Disclaimer */}
      <div className="mt-8 text-center p-4 bg-slate-50 rounded-lg border border-slate-200">
        <p className="text-xs text-slate-500 max-w-4xl mx-auto">
          <span className="font-bold uppercase tracking-wider mr-2">Important Disclaimer:</span>
          This evaluation uses deterministic synthetic transaction scenarios. Results demonstrate simulated comparative behavior and should not be interpreted as production performance.
        </p>
      </div>
    </div>
  );
}
