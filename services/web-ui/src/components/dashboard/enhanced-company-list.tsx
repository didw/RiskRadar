"use client";

import { useState, useMemo } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ChevronDown,
  ChevronUp,
  Search,
  MoreHorizontal,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CompanyFilters } from "./company-filters";
import { EmptyState } from "./empty-state";

interface Company {
  id: string;
  name: string;
  industry: string;
  riskScore: number;
  riskLevel: "low" | "medium" | "high";
  change: number;
  marketCap?: string;
  lastUpdated: string;
}

const mockCompanies: Company[] = [
  {
    id: "1",
    name: "삼성전자",
    industry: "반도체",
    riskScore: 25,
    riskLevel: "low",
    change: -2,
    marketCap: "₩400조",
    lastUpdated: "5분 전",
  },
  {
    id: "2",
    name: "SK하이닉스",
    industry: "반도체",
    riskScore: 42,
    riskLevel: "medium",
    change: 5,
    marketCap: "₩100조",
    lastUpdated: "10분 전",
  },
  {
    id: "3",
    name: "현대자동차",
    industry: "자동차",
    riskScore: 38,
    riskLevel: "medium",
    change: -1,
    marketCap: "₩80조",
    lastUpdated: "15분 전",
  },
  {
    id: "4",
    name: "카카오",
    industry: "IT",
    riskScore: 67,
    riskLevel: "high",
    change: 12,
    marketCap: "₩30조",
    lastUpdated: "방금",
  },
  {
    id: "5",
    name: "네이버",
    industry: "IT",
    riskScore: 31,
    riskLevel: "low",
    change: 0,
    marketCap: "₩50조",
    lastUpdated: "30분 전",
  },
  {
    id: "6",
    name: "LG화학",
    industry: "화학",
    riskScore: 55,
    riskLevel: "medium",
    change: 3,
    marketCap: "₩45조",
    lastUpdated: "20분 전",
  },
  {
    id: "7",
    name: "셀트리온",
    industry: "바이오",
    riskScore: 72,
    riskLevel: "high",
    change: 8,
    marketCap: "₩25조",
    lastUpdated: "1시간 전",
  },
  {
    id: "8",
    name: "삼성바이오로직스",
    industry: "바이오",
    riskScore: 28,
    riskLevel: "low",
    change: -5,
    marketCap: "₩50조",
    lastUpdated: "45분 전",
  },
  {
    id: "9",
    name: "KB금융",
    industry: "금융",
    riskScore: 45,
    riskLevel: "medium",
    change: 2,
    marketCap: "₩22조",
    lastUpdated: "2시간 전",
  },
  {
    id: "10",
    name: "신한금융",
    industry: "금융",
    riskScore: 78,
    riskLevel: "high",
    change: 15,
    marketCap: "₩20조",
    lastUpdated: "10분 전",
  },
  {
    id: "11",
    name: "CJ대한통운",
    industry: "물류",
    riskScore: 33,
    riskLevel: "low",
    change: -3,
    marketCap: "₩3조",
    lastUpdated: "25분 전",
  },
  {
    id: "12",
    name: "한진칼",
    industry: "물류",
    riskScore: 62,
    riskLevel: "high",
    change: 7,
    marketCap: "₩5조",
    lastUpdated: "방금",
  },
];

const riskLevelConfig = {
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

type SortField = "name" | "riskScore" | "change";
type SortOrder = "asc" | "desc";

export function EnhancedCompanyList() {
  const [companies, setCompanies] = useState(mockCompanies);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>("riskScore");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedRiskLevels, setSelectedRiskLevels] = useState<string[]>([]);

  // Extract unique industries
  const uniqueIndustries = useMemo(() => {
    const industries = new Set(companies.map(c => c.industry));
    return Array.from(industries).sort();
  }, [companies]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const handleResetFilters = () => {
    setSelectedIndustries([]);
    setSelectedRiskLevels([]);
    setSearchTerm("");
  };

  const filteredAndSortedCompanies = useMemo(() => {
    let filtered = [...companies];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(company =>
        company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        company.industry.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply industry filter
    if (selectedIndustries.length > 0) {
      filtered = filtered.filter(company =>
        selectedIndustries.includes(company.industry)
      );
    }

    // Apply risk level filter
    if (selectedRiskLevels.length > 0) {
      filtered = filtered.filter(company =>
        selectedRiskLevels.includes(company.riskLevel)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      const modifier = sortOrder === "asc" ? 1 : -1;
      
      if (typeof aValue === "string" && typeof bValue === "string") {
        return aValue.localeCompare(bValue) * modifier;
      }
      return ((aValue as number) - (bValue as number)) * modifier;
    });

    return filtered;
  }, [companies, searchTerm, selectedIndustries, selectedRiskLevels, sortField, sortOrder]);

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortOrder === "asc" ? 
      <ChevronUp className="h-4 w-4" /> : 
      <ChevronDown className="h-4 w-4" />;
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-red-500" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-green-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="기업명 또는 산업으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <CompanyFilters
          industries={uniqueIndustries}
          selectedIndustries={selectedIndustries}
          onIndustryChange={setSelectedIndustries}
          selectedRiskLevels={selectedRiskLevels}
          onRiskLevelChange={setSelectedRiskLevels}
          onReset={handleResetFilters}
        />
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead 
                className="cursor-pointer select-none"
                onClick={() => handleSort("name")}
              >
                <div className="flex items-center gap-1">
                  기업명
                  {getSortIcon("name")}
                </div>
              </TableHead>
              <TableHead>산업</TableHead>
              <TableHead 
                className="cursor-pointer select-none text-center"
                onClick={() => handleSort("riskScore")}
              >
                <div className="flex items-center justify-center gap-1">
                  리스크 점수
                  {getSortIcon("riskScore")}
                </div>
              </TableHead>
              <TableHead>리스크 레벨</TableHead>
              <TableHead 
                className="cursor-pointer select-none text-center"
                onClick={() => handleSort("change")}
              >
                <div className="flex items-center justify-center gap-1">
                  변화
                  {getSortIcon("change")}
                </div>
              </TableHead>
              <TableHead>시가총액</TableHead>
              <TableHead>업데이트</TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedCompanies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  <EmptyState />
                </TableCell>
              </TableRow>
            ) : (
              filteredAndSortedCompanies.map((company) => (
              <TableRow key={company.id}>
                <TableCell className="font-medium">{company.name}</TableCell>
                <TableCell>{company.industry}</TableCell>
                <TableCell className="text-center">
                  <span className="font-semibold">{company.riskScore}</span>
                </TableCell>
                <TableCell>
                  <Badge className={riskLevelConfig[company.riskLevel].className}>
                    {riskLevelConfig[company.riskLevel].label}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-center gap-1">
                    {getTrendIcon(company.change)}
                    <span className={cn(
                      "text-sm font-medium",
                      company.change > 0 ? "text-red-600" : 
                      company.change < 0 ? "text-green-600" : 
                      "text-gray-500"
                    )}>
                      {company.change > 0 ? "+" : ""}{company.change}
                    </span>
                  </div>
                </TableCell>
                <TableCell>{company.marketCap}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {company.lastUpdated}
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>작업</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>상세 보기</DropdownMenuItem>
                      <DropdownMenuItem>리포트 생성</DropdownMenuItem>
                      <DropdownMenuItem>알림 설정</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}