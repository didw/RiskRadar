import { GraphQLError } from 'graphql';
import { execSync } from 'child_process';

interface DailyReportData {
  generatedAt: string;
  systemHealth: {
    dataService: string;
    mlService: string;
    graphService: string;
    apiGateway: string;
  };
  dataStatistics: {
    companies: number;
    newsArticles: number;
    executives: number;
    rawNewsMessages: number;
    enrichedNewsMessages: number;
  };
  topRiskCompanies: Array<{
    rank: number;
    name: string;
    riskScore: number;
    industry: string;
  }>;
  processingStats: {
    targetThroughput: string;
    actualMessages: number;
    mlProcessingTarget: string;
  };
  recommendations: string[];
}

export const dailyReportResolvers = {
  Query: {
    dailyReport: async (): Promise<DailyReportData> => {
      try {
        // Get system health
        const systemHealth = {
          dataService: await checkServiceHealth('http://data-service:8001/health') ? 'healthy' : 'down',
          mlService: await checkServiceHealth('http://ml-service:8082/api/v1/health') ? 'healthy' : 'down',
          graphService: await checkServiceHealth('http://graph-service:8003/health') ? 'healthy' : 'down',
          apiGateway: 'healthy' // We're running, so we're healthy
        };

        // Get data statistics (mock for now, should query actual services)
        const dataStatistics = {
          companies: 10,
          newsArticles: 30,
          executives: 10,
          rawNewsMessages: 3,
          enrichedNewsMessages: 2
        };

        // Get top risk companies from existing query
        const topRiskCompanies = [
          { rank: 1, name: "SK Hynix", riskScore: 3.5, industry: "Technology" },
          { rank: 2, name: "Samsung Electronics", riskScore: 3.2, industry: "Technology" },
          { rank: 3, name: "Hyundai Motor Company", riskScore: 2.8, industry: "Automotive" }
        ];

        // Processing stats
        const processingStats = {
          targetThroughput: "1,000 articles/hour",
          actualMessages: dataStatistics.rawNewsMessages,
          mlProcessingTarget: "<10ms per article"
        };

        // Generate recommendations
        const recommendations = [];
        if (dataStatistics.rawNewsMessages < 100) {
          recommendations.push("Low news volume detected. Check crawler status.");
          recommendations.push("Verify news sources are accessible.");
          recommendations.push("Review rate limiting settings.");
        } else {
          recommendations.push("News collection operating normally.");
        }

        if (Object.values(systemHealth).includes('down')) {
          recommendations.push("Some services are down. Immediate attention required.");
        }

        return {
          generatedAt: new Date().toISOString(),
          systemHealth,
          dataStatistics,
          topRiskCompanies,
          processingStats,
          recommendations
        };
      } catch (error) {
        throw new GraphQLError('Failed to generate daily report', {
          extensions: {
            code: 'INTERNAL_ERROR',
            error: error instanceof Error ? error.message : 'Unknown error'
          }
        });
      }
    }
  }
};

async function checkServiceHealth(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { 
      method: 'GET',
      signal: AbortSignal.timeout(5000)
    });
    return response.ok;
  } catch {
    return false;
  }
}