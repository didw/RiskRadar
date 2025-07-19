"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from "recharts";
import { Card } from "@/components/ui/card";

const data = [
  { date: "1월 1일", average: 45, high: 62, medium: 38, low: 15 },
  { date: "1월 5일", average: 48, high: 65, medium: 42, low: 18 },
  { date: "1월 10일", average: 42, high: 58, medium: 35, low: 12 },
  { date: "1월 15일", average: 51, high: 70, medium: 45, low: 20 },
  { date: "1월 20일", average: 46, high: 63, medium: 40, low: 16 },
  { date: "1월 25일", average: 43, high: 60, medium: 36, low: 14 },
  { date: "1월 30일", average: 42, high: 59, medium: 35, low: 13 },
];

interface RiskOverviewChartProps {
  variant?: "line" | "area";
}

export function RiskOverviewChart({ variant = "area" }: RiskOverviewChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Card className="p-3 shadow-lg">
          <p className="text-sm font-medium mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-xs">
              <span className="flex items-center gap-1">
                <span 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                />
                {entry.name}
              </span>
              <span className="font-medium">{entry.value}</span>
            </div>
          ))}
        </Card>
      );
    }
    return null;
  };

  if (variant === "line") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="date" 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis 
            className="text-xs"
            tick={{ fill: 'currentColor' }}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="average"
            stroke="hsl(var(--primary))"
            strokeWidth={3}
            dot={{ fill: 'hsl(var(--primary))', r: 4 }}
            activeDot={{ r: 6 }}
            name="평균"
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="고위험"
          />
          <Line
            type="monotone"
            dataKey="medium"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="중위험"
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#10b981"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="저위험"
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis 
          dataKey="date" 
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis 
          className="text-xs"
          tick={{ fill: 'currentColor' }}
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          wrapperStyle={{ paddingTop: '20px' }}
          iconType="rect"
        />
        <Area
          type="monotone"
          dataKey="low"
          stackId="1"
          stroke="#10b981"
          fill="#10b981"
          fillOpacity={0.6}
          name="저위험"
        />
        <Area
          type="monotone"
          dataKey="medium"
          stackId="1"
          stroke="#f59e0b"
          fill="#f59e0b"
          fillOpacity={0.6}
          name="중위험"
        />
        <Area
          type="monotone"
          dataKey="high"
          stackId="1"
          stroke="#ef4444"
          fill="#ef4444"
          fillOpacity={0.6}
          name="고위험"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}