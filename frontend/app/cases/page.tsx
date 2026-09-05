"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { PaginatedCasesResponse, RecoveryCaseSummary } from "@/types/api";
import Link from "next/link";
import { Search, Filter, AlertCircle, MoreHorizontal } from "lucide-react";

export default function CasesPage() {
  const [data, setData] = useState<PaginatedCasesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<PaginatedCasesResponse>("/api/v1/cases?limit=50")
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch cases:", err);
        setError("Failed to load recovery cases");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-8 w-8 border-4 border-fintech-blue border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-fintech-muted font-medium">Loading recovery cases...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center">
        <AlertCircle className="h-10 w-10 text-red-500 mb-2" />
        <h3 className="text-red-700 font-semibold text-lg">Failed to load data</h3>
        <p className="text-red-500 text-sm mt-1">{error}</p>
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-fintech-navy tracking-tight">Recovery Cases</h1>
          <p className="text-sm text-fintech-muted mt-1">Manage and track all payment recovery attempts.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-fintech-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search cases..."
              className="pl-9 pr-4 py-2 bg-white border border-fintech-border rounded-lg text-sm text-fintech-navy focus:outline-none focus:ring-1 focus:ring-fintech-blue transition-all w-64 shadow-sm"
            />
          </div>
          <button className="flex items-center gap-2 bg-white border border-fintech-border text-fintech-navy px-3 py-2 rounded-lg text-sm font-medium hover:bg-fintech-bg transition-all shadow-sm">
            <Filter className="w-4 h-4 text-fintech-muted" />
            Filter
          </button>
        </div>
      </div>

      <Card className="shadow-sm border-fintech-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-fintech-muted bg-fintech-bg/50 uppercase border-b border-fintech-border">
              <tr>
                <th className="px-6 py-4 font-medium">Case ID</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Revenue at Risk</th>
                <th className="px-6 py-4 font-medium">Scenario</th>
                <th className="px-6 py-4 font-medium">Created</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-fintech-border bg-white">
              {data.items.length > 0 ? (
                data.items.map((caseItem) => (
                  <tr key={caseItem.id} className="hover:bg-fintech-bg/50 transition-colors group">
                    <td className="px-6 py-4 font-medium text-fintech-navy whitespace-nowrap">
                      {caseItem.id}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        caseItem.status === 'RECOVERED' ? 'bg-green-50 text-fintech-success border-green-100' :
                        caseItem.status === 'FAILED' ? 'bg-red-50 text-fintech-danger border-red-100' :
                        caseItem.status === 'IN_PROGRESS' ? 'bg-amber-50 text-fintech-warning border-amber-100' :
                        'bg-blue-50 text-fintech-blue border-blue-100'
                      }`}>
                        {caseItem.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-fintech-navy">
                      {formatCurrency(caseItem.revenue_at_risk)}
                    </td>
                    <td className="px-6 py-4 text-fintech-muted capitalize">
                      {caseItem.scenario.replace(/_/g, ' ').toLowerCase()}
                    </td>
                    <td className="px-6 py-4 text-fintech-muted">
                      {new Date(caseItem.created_at).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link href={`/cases/${caseItem.id}`} className="text-fintech-blue font-medium hover:text-blue-700 bg-blue-50 opacity-0 group-hover:opacity-100 px-3 py-1.5 rounded transition-all">
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-fintech-muted">
                    No recovery cases found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data.items.length > 0 && (
          <div className="px-6 py-4 border-t border-fintech-border bg-fintech-bg/30 flex items-center justify-between">
            <span className="text-sm text-fintech-muted">
              Showing <span className="font-medium text-fintech-navy">{data.items.length}</span> of <span className="font-medium text-fintech-navy">{data.total}</span> cases
            </span>
            <div className="flex gap-2">
              <button disabled className="px-3 py-1 border border-fintech-border rounded text-sm text-fintech-muted bg-white opacity-50 cursor-not-allowed">Previous</button>
              <button disabled className="px-3 py-1 border border-fintech-border rounded text-sm text-fintech-muted bg-white opacity-50 cursor-not-allowed">Next</button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
