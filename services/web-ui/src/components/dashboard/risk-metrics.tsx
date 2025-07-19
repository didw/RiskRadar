"use client";

import { Building2, AlertTriangle, TrendingUp, Activity } from "lucide-react";
import { RiskSummaryCard } from "./risk-summary-card";

interface RiskMetrics {
  totalCompanies: number;
  totalCompaniesChange: number;
  highRiskCompanies: number;
  highRiskChange: number;
  newRisks: number;
  averageRiskScore: number;
  averageRiskChange: number;
}

interface RiskMetricsProps {
  metrics?: RiskMetrics;
  loading?: boolean;
}

const defaultMetrics: RiskMetrics = {
  totalCompanies: 1234,
  totalCompaniesChange: 12,
  highRiskCompanies: 23,
  highRiskChange: 2,
  newRisks: 145,
  averageRiskScore: 42.3,
  averageRiskChange: -2.1,
};

export function RiskMetrics({ metrics = defaultMetrics, loading = false }: RiskMetricsProps) {
  if (loading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      <RiskSummaryCard
        title="전체 모니터링 기업"
        value={metrics.totalCompanies.toLocaleString()}
        change={metrics.totalCompaniesChange}
        changeLabel="% from last month"
        icon={<Building2 className="h-4 w-4" />}
        trend={metrics.totalCompaniesChange > 0 ? "up" : "neutral"}
      />
      
      <RiskSummaryCard
        title="고위험 기업"
        value={metrics.highRiskCompanies}
        change={metrics.highRiskChange}
        changeLabel=" from yesterday"
        icon={<AlertTriangle className="h-4 w-4" />}
        trend={metrics.highRiskChange > 0 ? "up" : "neutral"}
        variant="danger"
      />
      
      <RiskSummaryCard
        title="신규 리스크"
        value={metrics.newRisks}
        changeLabel="Last 24 hours"
        icon={<TrendingUp className="h-4 w-4" />}
        variant="warning"
      />
      
      <RiskSummaryCard
        title="평균 리스크 점수"
        value={metrics.averageRiskScore}
        change={metrics.averageRiskChange}
        changeLabel=" from last week"
        icon={<Activity className="h-4 w-4" />}
        trend={metrics.averageRiskChange < 0 ? "down" : "up"}
        variant={metrics.averageRiskChange < 0 ? "success" : "warning"}
      />
    </div>
  );
}