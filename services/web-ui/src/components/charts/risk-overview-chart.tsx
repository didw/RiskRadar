"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { date: "1월 1일", score: 45 },
  { date: "1월 5일", score: 48 },
  { date: "1월 10일", score: 42 },
  { date: "1월 15일", score: 51 },
  { date: "1월 20일", score: 46 },
  { date: "1월 25일", score: 43 },
  { date: "1월 30일", score: 42 },
];

export function RiskOverviewChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis 
          dataKey="date" 
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis 
          className="text-xs"
          tick={{ fill: 'currentColor' }}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
          }}
        />
        <Line
          type="monotone"
          dataKey="score"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={{ fill: 'hsl(var(--primary))' }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}