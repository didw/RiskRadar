import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskOverviewChart } from "@/components/charts/risk-overview-chart";
import { CompanyList } from "@/components/dashboard/company-list";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground">
          기업 리스크 현황을 한눈에 확인하세요
        </p>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              전체 모니터링 기업
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              고위험 기업
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">23</div>
            <p className="text-xs text-muted-foreground">
              +2 from yesterday
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              신규 리스크
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">145</div>
            <p className="text-xs text-muted-foreground">
              Last 24 hours
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              평균 리스크 점수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">42.3</div>
            <p className="text-xs text-muted-foreground">
              -2.1 from last week
            </p>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
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
            <CardTitle>주요 모니터링 기업</CardTitle>
            <CardDescription>
              실시간 리스크 현황
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CompanyList />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}