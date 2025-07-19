import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskOverviewChart } from "@/components/charts/risk-overview-chart";
import { RiskDistributionChart } from "@/components/charts/risk-distribution-chart";
import { RiskMetrics } from "@/components/dashboard/risk-metrics";
import { EnhancedCompanyList } from "@/components/dashboard/enhanced-company-list";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground">
          기업 리스크 현황을 한눈에 확인하세요
        </p>
      </div>
      
      <RiskMetrics />
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>리스크 추이</CardTitle>
            <CardDescription>
              최근 30일간 리스크 점수 변화
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RiskOverviewChart />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>리스크 분포</CardTitle>
            <CardDescription>
              전체 기업의 리스크 레벨 분포
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>산업별 리스크 현황</CardTitle>
            <CardDescription>
              산업별 리스크 레벨 분포 비교
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart variant="bar" />
          </CardContent>
        </Card>
        
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>주요 모니터링 기업</CardTitle>
            <CardDescription>
              실시간 리스크 현황 및 변화 추이
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <EnhancedCompanyList />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}