"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { X, Filter } from "lucide-react";

interface CompanyFiltersProps {
  industries: string[];
  selectedIndustries: string[];
  onIndustryChange: (industries: string[]) => void;
  selectedRiskLevels: string[];
  onRiskLevelChange: (levels: string[]) => void;
  onReset: () => void;
}

const riskLevels = [
  { value: "low", label: "저위험", color: "bg-green-100 text-green-800" },
  { value: "medium", label: "중위험", color: "bg-yellow-100 text-yellow-800" },
  { value: "high", label: "고위험", color: "bg-red-100 text-red-800" },
];

export function CompanyFilters({
  industries,
  selectedIndustries,
  onIndustryChange,
  selectedRiskLevels,
  onRiskLevelChange,
  onReset,
}: CompanyFiltersProps) {
  const [isIndustryOpen, setIsIndustryOpen] = useState(false);
  const [isRiskOpen, setIsRiskOpen] = useState(false);

  const handleIndustryToggle = (industry: string) => {
    if (selectedIndustries.includes(industry)) {
      onIndustryChange(selectedIndustries.filter((i) => i !== industry));
    } else {
      onIndustryChange([...selectedIndustries, industry]);
    }
  };

  const handleRiskLevelToggle = (level: string) => {
    if (selectedRiskLevels.includes(level)) {
      onRiskLevelChange(selectedRiskLevels.filter((l) => l !== level));
    } else {
      onRiskLevelChange([...selectedRiskLevels, level]);
    }
  };

  const activeFilterCount = selectedIndustries.length + selectedRiskLevels.length;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <DropdownMenu open={isIndustryOpen} onOpenChange={setIsIndustryOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            산업 분야
            {selectedIndustries.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {selectedIndustries.length}
              </Badge>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuLabel>산업 분야 선택</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {industries.map((industry) => (
            <DropdownMenuCheckboxItem
              key={industry}
              checked={selectedIndustries.includes(industry)}
              onCheckedChange={() => handleIndustryToggle(industry)}
            >
              {industry}
            </DropdownMenuCheckboxItem>
          ))}
          {industries.length === 0 && (
            <div className="px-2 py-1.5 text-sm text-muted-foreground">
              산업 분야가 없습니다
            </div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu open={isRiskOpen} onOpenChange={setIsRiskOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            리스크 레벨
            {selectedRiskLevels.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {selectedRiskLevels.length}
              </Badge>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuLabel>리스크 레벨 선택</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {riskLevels.map((level) => (
            <DropdownMenuCheckboxItem
              key={level.value}
              checked={selectedRiskLevels.includes(level.value)}
              onCheckedChange={() => handleRiskLevelToggle(level.value)}
            >
              <div className="flex items-center gap-2">
                <Badge className={level.color}>{level.label}</Badge>
              </div>
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {activeFilterCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="h-8 px-2 lg:px-3"
        >
          필터 초기화
          <X className="ml-1 h-4 w-4" />
        </Button>
      )}

      {/* Active filter badges */}
      <div className="flex flex-wrap gap-1">
        {selectedIndustries.map((industry) => (
          <Badge
            key={industry}
            variant="secondary"
            className="cursor-pointer"
            onClick={() => handleIndustryToggle(industry)}
          >
            {industry}
            <X className="ml-1 h-3 w-3" />
          </Badge>
        ))}
        {selectedRiskLevels.map((level) => {
          const riskLevel = riskLevels.find((r) => r.value === level);
          return (
            <Badge
              key={level}
              variant="secondary"
              className="cursor-pointer"
              onClick={() => handleRiskLevelToggle(level)}
            >
              {riskLevel?.label}
              <X className="ml-1 h-3 w-3" />
            </Badge>
          );
        })}
      </div>
    </div>
  );
}