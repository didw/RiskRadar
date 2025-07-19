import { Context } from './index.js';

const mockRisks = [
  {
    id: 'risk-1',
    type: 'FINANCIAL',
    severity: 'HIGH',
    probability: 0.7,
    impact: 0.8,
    description: 'Significant revenue decline in Q4 due to market conditions',
    source: 'Financial Report Analysis',
    detectedAt: new Date('2024-07-15').toISOString(),
    resolvedAt: null,
    status: 'ACTIVE',
    affectedCompanies: [],
    metadata: {
      quarter: 'Q4',
      expectedLoss: 15000000,
    },
  },
  {
    id: 'risk-2',
    type: 'SUPPLY_CHAIN',
    severity: 'MEDIUM',
    probability: 0.5,
    impact: 0.6,
    description: 'Potential disruption in semiconductor supply chain',
    source: 'Industry News',
    detectedAt: new Date('2024-07-18').toISOString(),
    resolvedAt: null,
    status: 'MONITORING',
    affectedCompanies: [],
    metadata: {
      suppliers: ['TSMC', 'ASML'],
      estimatedDelay: '2-3 weeks',
    },
  },
];

const mockRiskEvents = [
  {
    id: 'event-1',
    title: 'Major Tech Company Announces Layoffs',
    description: 'Samsung Electronics announces 5% workforce reduction',
    eventType: 'LAYOFF',
    severity: 'HIGH',
    source: 'Reuters',
    sourceUrl: 'https://reuters.com/example',
    publishedAt: new Date('2024-07-19').toISOString(),
    companies: [],
    keywords: ['layoffs', 'restructuring', 'cost-cutting'],
    sentiment: -0.7,
    location: 'Seoul, South Korea',
  },
  {
    id: 'event-2',
    title: 'New Environmental Regulations in Korea',
    description: 'South Korea implements stricter emissions standards',
    eventType: 'REGULATORY',
    severity: 'MEDIUM',
    source: 'Korea Times',
    sourceUrl: 'https://koreatimes.co.kr/example',
    publishedAt: new Date('2024-07-18').toISOString(),
    companies: [],
    keywords: ['regulation', 'environment', 'compliance'],
    sentiment: -0.3,
    location: 'South Korea',
  },
];

export const riskResolvers = {
  Query: {
    risk: (_: any, { id }: { id: string }, _context: Context) => {
      return mockRisks.find(risk => risk.id === id) || null;
    },
    
    risks: (_: any, { filter, limit = 50, offset = 0 }: any, _context: Context) => {
      let filteredRisks = [...mockRisks];
      
      if (filter) {
        if (filter.types && filter.types.length > 0) {
          filteredRisks = filteredRisks.filter(r => filter.types.includes(r.type));
        }
        if (filter.severities && filter.severities.length > 0) {
          filteredRisks = filteredRisks.filter(r => filter.severities.includes(r.severity));
        }
        if (filter.statuses && filter.statuses.length > 0) {
          filteredRisks = filteredRisks.filter(r => filter.statuses.includes(r.status));
        }
      }
      
      return filteredRisks.slice(offset, offset + limit);
    },
    
    riskAnalysis: (_: any, { companyId }: { companyId: string }, _context: Context) => {
      return {
        id: `analysis-${companyId}`,
        companyId,
        company: null, // Will be resolved by Company resolver
        overallScore: 3.2,
        financialRisk: 2.8,
        operationalRisk: 3.5,
        marketRisk: 3.1,
        reputationalRisk: 2.9,
        regulatoryRisk: 3.4,
        networkRisk: 3.8,
        risks: mockRisks,
        analyzedAt: new Date().toISOString(),
        confidence: 0.85,
      };
    },
    
    riskEvents: (_: any, { filter, sort, limit = 50, offset = 0 }: any, _context: Context) => {
      let filteredEvents = [...mockRiskEvents];
      
      if (filter) {
        if (filter.severities && filter.severities.length > 0) {
          filteredEvents = filteredEvents.filter(e => filter.severities.includes(e.severity));
        }
        if (filter.keywords && filter.keywords.length > 0) {
          filteredEvents = filteredEvents.filter(e => 
            filter.keywords.some((keyword: string) => 
              e.keywords.includes(keyword) || 
              e.title.toLowerCase().includes(keyword.toLowerCase()) ||
              e.description.toLowerCase().includes(keyword.toLowerCase())
            )
          );
        }
      }
      
      // Sort
      if (sort) {
        filteredEvents.sort((a, b) => {
          switch (sort) {
            case 'PUBLISHED_AT':
              return new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime();
            case 'SEVERITY': {
              const severityOrder = { CRITICAL: 5, HIGH: 4, MEDIUM: 3, LOW: 2, INFO: 1 };
              return severityOrder[b.severity as keyof typeof severityOrder] - 
                     severityOrder[a.severity as keyof typeof severityOrder];
            }
            case 'SENTIMENT':
              return (b.sentiment || 0) - (a.sentiment || 0);
            default:
              return 0;
          }
        });
      }
      
      return filteredEvents.slice(offset, offset + limit);
    },
    
    riskAlerts: (_: any, { _acknowledged, limit = 50, offset = 0 }: any, _context: Context) => {
      return [
        {
          id: 'alert-1',
          riskId: 'risk-1',
          risk: mockRisks[0],
          alertType: 'NEW_RISK',
          message: 'High financial risk detected for Samsung Electronics',
          createdAt: new Date().toISOString(),
          acknowledged: false,
          acknowledgedAt: null,
          acknowledgedBy: null,
        },
      ].slice(offset, offset + limit);
    },
  },
  
  Mutation: {
    acknowledgeRiskAlert: (_: any, { alertId }: { alertId: string }, _context: Context) => {
      return {
        id: alertId,
        riskId: 'risk-1',
        risk: mockRisks[0],
        alertType: 'NEW_RISK',
        message: 'High financial risk detected for Samsung Electronics',
        createdAt: new Date().toISOString(),
        acknowledged: true,
        acknowledgedAt: new Date().toISOString(),
        acknowledgedBy: _context.user || null,
      };
    },
    
    updateRiskStatus: (_: any, { riskId, status }: any, _context: Context) => {
      const risk = mockRisks.find(r => r.id === riskId);
      if (!risk) {
        throw new Error('Risk not found');
      }
      
      return {
        ...risk,
        status,
      };
    },
  },
  
  RiskAnalysis: {
    company: (parent: any, _: any, context: Context) => {
      return context.loaders.company.load(parent.companyId);
    },
  },
};