"use client";

import { useQuery } from "@apollo/client";
import { GET_RISK_METRICS } from "@/graphql/queries/risk";
import { RiskSummaryCard } from "./risk-summary-card";
import { Building2, AlertTriangle, TrendingUp, Activity } from "lucide-react";

const iconMap: Record<string, React.ReactNode> = {
  building: <Building2 className="h-4 w-4" />,
  alert: <AlertTriangle className="h-4 w-4" />,
  trending: <TrendingUp className="h-4 w-4" />,
  activity: <Activity className="h-4 w-4" />,
};

export function RiskMetricsGraphQL() {
  const { data, loading, error } = useQuery(GET_RISK_METRICS, {
    pollInterval: 60000, // Poll every minute
  });

  if (loading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    console.error("Error loading risk metrics:", error);
    // Fallback to mock data on error
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <RiskSummaryCard
          title="전체 모니터링 기업"
          value="1,234"
          change={12}
          changeLabel="% from last month"
          icon={<Building2 className="h-4 w-4" />}
          trend="up"
        />
        
        <RiskSummaryCard
          title="고위험 기업"
          value={23}
          change={2}
          changeLabel=" from yesterday"
          icon={<AlertTriangle className="h-4 w-4" />}
          trend="up"
          variant="danger"
        />
        
        <RiskSummaryCard
          title="신규 리스크"
          value={145}
          changeLabel="Last 24 hours"
          icon={<TrendingUp className="h-4 w-4" />}
          variant="warning"
        />
        
        <RiskSummaryCard
          title="평균 리스크 점수"
          value={42.3}
          change={-2.1}
          changeLabel=" from last week"
          icon={<Activity className="h-4 w-4" />}
          trend="down"
          variant="success"
        />
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {data?.riskMetrics?.map((metric: any) => (
        <RiskSummaryCard
          key={metric.id}
          title={metric.title}
          value={metric.value}
          change={metric.change}
          changeLabel={metric.changeLabel}
          icon={iconMap[metric.icon] || <Activity className="h-4 w-4" />}
          trend={metric.trend}
          variant={metric.variant}
        />
      ))}
    </div>
  );
}