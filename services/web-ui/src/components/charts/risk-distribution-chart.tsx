"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Card } from "@/components/ui/card";

const pieData = [
  { name: "저위험", value: 45, count: 556 },
  { name: "중위험", value: 35, count: 432 },
  { name: "고위험", value: 20, count: 246 },
];

const barData = [
  { industry: "IT", low: 23, medium: 15, high: 8 },
  { industry: "금융", low: 18, medium: 22, high: 12 },
  { industry: "제조", low: 30, medium: 25, high: 15 },
  { industry: "유통", low: 15, medium: 18, high: 10 },
  { industry: "바이오", low: 10, medium: 20, high: 25 },
];

const COLORS = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
};

interface RiskDistributionChartProps {
  variant?: "pie" | "bar";
}

export function RiskDistributionChart({ variant = "pie" }: RiskDistributionChartProps) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Card className="p-3 shadow-lg">
          <p className="text-sm font-medium">{payload[0].name || payload[0].payload.industry}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-xs mt-1">
              <span className="flex items-center gap-1">
                <span 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color || entry.fill }}
                />
                {entry.name === "value" ? entry.payload.name : entry.dataKey}
              </span>
              <span className="font-medium">
                {entry.value} {entry.payload?.count ? `(${entry.payload.count}개)` : '개'}
              </span>
            </div>
          ))}
        </Card>
      );
    }
    return null;
  };

  const renderCustomLabel = (entry: any) => {
    return `${entry.value}%`;
  };

  if (variant === "bar") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={barData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="industry" 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
            label={{ value: '기업 수', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="rect"
          />
          <Bar dataKey="low" stackId="a" fill={COLORS.low} name="저위험" />
          <Bar dataKey="medium" stackId="a" fill={COLORS.medium} name="중위험" />
          <Bar dataKey="high" stackId="a" fill={COLORS.high} name="고위험" />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={pieData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderCustomLabel}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {pieData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={
                entry.name === "저위험" ? COLORS.low :
                entry.name === "중위험" ? COLORS.medium :
                COLORS.high
              } 
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          verticalAlign="bottom" 
          height={36}
          formatter={(value, entry: any) => `${value} (${entry?.payload?.count || 0}개)`}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}