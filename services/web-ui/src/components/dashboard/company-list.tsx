"use client";

import { Badge } from "@/components/ui/badge";

const companies = [
  {
    id: 1,
    name: "삼성전자",
    industry: "반도체",
    riskScore: 25,
    riskLevel: "low",
    change: -2,
  },
  {
    id: 2,
    name: "SK하이닉스",
    industry: "반도체",
    riskScore: 42,
    riskLevel: "medium",
    change: 5,
  },
  {
    id: 3,
    name: "현대자동차",
    industry: "자동차",
    riskScore: 38,
    riskLevel: "medium",
    change: -1,
  },
  {
    id: 4,
    name: "카카오",
    industry: "IT",
    riskScore: 67,
    riskLevel: "high",
    change: 12,
  },
  {
    id: 5,
    name: "네이버",
    industry: "IT",
    riskScore: 31,
    riskLevel: "low",
    change: 0,
  },
];

const riskLevelConfig: Record<string, { label: string; className: string }> = {
  low: {
    label: "낮음",
    className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  },
  medium: {
    label: "중간",
    className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  },
  high: {
    label: "높음",
    className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  },
};

export function CompanyList() {
  return (
    <div className="space-y-4">
      {companies.map((company) => (
        <div
          key={company.id}
          className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
        >
          <div className="flex-1">
            <h4 className="font-medium">{company.name}</h4>
            <p className="text-sm text-muted-foreground">{company.industry}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="font-medium">{company.riskScore}</div>
              <div className={`text-xs ${company.change > 0 ? 'text-red-600' : company.change < 0 ? 'text-green-600' : 'text-gray-500'}`}>
                {company.change > 0 ? '+' : ''}{company.change}
              </div>
            </div>
            
            <Badge className={riskLevelConfig[company.riskLevel].className}>
              {riskLevelConfig[company.riskLevel].label}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  );
}