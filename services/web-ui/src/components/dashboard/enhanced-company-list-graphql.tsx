"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@apollo/client";
import { GET_COMPANY_RISKS } from "@/graphql/queries/risk";
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
import { Skeleton } from "@/components/ui/skeleton";
import { CompanyRiskFilter, CompanyRiskSort } from "@/graphql/types";

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

type SortField = "name" | "riskScore" | "change" | "lastUpdated";
type SortOrder = "asc" | "desc";

export function EnhancedCompanyListGraphQL() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedRiskLevels, setSelectedRiskLevels] = useState<string[]>([]);
  const [sortField, setSortField] = useState<SortField>("riskScore");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(1);
  const limit = 10;

  // Build filter and sort objects for GraphQL query
  const filter: CompanyRiskFilter = {
    ...(searchTerm && { searchTerm }),
    ...(selectedIndustries.length > 0 && { industries: selectedIndustries }),
    ...(selectedRiskLevels.length > 0 && { riskLevels: selectedRiskLevels }),
  };

  const sort: CompanyRiskSort = {
    field: sortField,
    order: sortOrder,
  };

  const { data, loading, error, refetch } = useQuery(GET_COMPANY_RISKS, {
    variables: {
      filter,
      sort,
      pagination: { page, limit },
    },
    pollInterval: 30000, // Poll every 30 seconds
  });

  // Extract unique industries from the data
  const uniqueIndustries = useMemo(() => {
    if (!data?.companyRisks?.items) return [];
    const industries = new Set(data.companyRisks.items.map((c: any) => c.industry));
    return Array.from(industries).sort();
  }, [data]);

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
    setPage(1);
  };

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

  if (loading && !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (error) {
    console.error("Error loading company risks:", error);
    return <EmptyState title="오류가 발생했습니다" description="데이터를 불러올 수 없습니다" />;
  }

  const companies = data?.companyRisks?.items || [];
  const pageInfo = data?.companyRisks?.pageInfo;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="기업명 또는 산업으로 검색..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="pl-10"
            />
          </div>
        </div>
        <CompanyFilters
          industries={uniqueIndustries}
          selectedIndustries={selectedIndustries}
          onIndustryChange={(industries) => {
            setSelectedIndustries(industries);
            setPage(1);
          }}
          selectedRiskLevels={selectedRiskLevels}
          onRiskLevelChange={(levels) => {
            setSelectedRiskLevels(levels);
            setPage(1);
          }}
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
              <TableHead 
                className="cursor-pointer select-none"
                onClick={() => handleSort("lastUpdated")}
              >
                <div className="flex items-center gap-1">
                  업데이트
                  {getSortIcon("lastUpdated")}
                </div>
              </TableHead>
              <TableHead className="text-right">작업</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {companies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  <EmptyState />
                </TableCell>
              </TableRow>
            ) : (
              companies.map((company: any) => (
              <TableRow key={company.id}>
                <TableCell className="font-medium">{company.name}</TableCell>
                <TableCell>{company.industry}</TableCell>
                <TableCell className="text-center">
                  <span className="font-semibold">{company.riskScore}</span>
                </TableCell>
                <TableCell>
                  <Badge className={riskLevelConfig[company.riskLevel as keyof typeof riskLevelConfig].className}>
                    {riskLevelConfig[company.riskLevel as keyof typeof riskLevelConfig].label}
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

      {pageInfo && pageInfo.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            전체 {data.companyRisks.totalCount}개 중 {(page - 1) * limit + 1}-{Math.min(page * limit, data.companyRisks.totalCount)}개 표시
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={!pageInfo.hasPreviousPage}
            >
              이전
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={!pageInfo.hasNextPage}
            >
              다음
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}