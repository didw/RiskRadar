"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowDownIcon, ArrowUpIcon, MinusIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskSummaryCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  variant?: "default" | "danger" | "warning" | "success";
}

const variantStyles = {
  default: "border-gray-200 dark:border-gray-700",
  danger: "border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950",
  warning: "border-yellow-200 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-950",
  success: "border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-950",
};

export function RiskSummaryCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  trend = "neutral",
  variant = "default",
}: RiskSummaryCardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <ArrowUpIcon className="h-4 w-4" />;
      case "down":
        return <ArrowDownIcon className="h-4 w-4" />;
      default:
        return <MinusIcon className="h-4 w-4" />;
    }
  };

  const getTrendColor = () => {
    if (variant === "danger") {
      return trend === "up" ? "text-red-600" : "text-green-600";
    }
    return trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-gray-500";
  };

  return (
    <Card className={cn("transition-all hover:shadow-md", variantStyles[variant])}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </CardTitle>
        {icon && <div className="text-gray-500 dark:text-gray-400">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <div className={cn("flex items-center text-xs mt-1", getTrendColor())}>
            {getTrendIcon()}
            <span className="ml-1">
              {change > 0 ? "+" : ""}{change}{changeLabel || ""}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}