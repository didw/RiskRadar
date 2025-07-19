"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Building2,
  AlertTriangle,
  LineChart,
  Settings,
  Users,
} from "lucide-react";

const navigation = [
  {
    name: "대시보드",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "기업 관리",
    href: "/companies",
    icon: Building2,
  },
  {
    name: "리스크 모니터링",
    href: "/risks",
    icon: AlertTriangle,
  },
  {
    name: "인사이트",
    href: "/insights",
    icon: LineChart,
  },
  {
    name: "사용자 관리",
    href: "/users",
    icon: Users,
  },
  {
    name: "설정",
    href: "/settings",
    icon: Settings,
  },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="h-full flex flex-col">
        <div className="flex items-center h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold">RiskRadar</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <ul className="p-4 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-gray-100"
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </nav>
  );
}