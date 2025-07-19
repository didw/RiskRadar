import { Context } from './index.js';

const mockCompanies = [
  {
    id: '1',
    name: 'Samsung Electronics',
    industry: 'Technology',
    sector: 'Consumer Electronics',
    description: 'Global leader in consumer electronics and semiconductors',
    riskScore: 3.2,
    marketCap: 350000000000,
    employees: 287000,
    founded: 1969,
    headquarters: 'Seoul, South Korea',
    website: 'https://www.samsung.com',
    lastUpdated: new Date().toISOString(),
    createdAt: new Date('2024-01-01').toISOString(),
  },
  {
    id: '2',
    name: 'Hyundai Motor Company',
    industry: 'Automotive',
    sector: 'Automobile Manufacturing',
    description: 'South Korean multinational automotive manufacturer',
    riskScore: 2.8,
    marketCap: 45000000000,
    employees: 120000,
    founded: 1967,
    headquarters: 'Seoul, South Korea',
    website: 'https://www.hyundai.com',
    lastUpdated: new Date().toISOString(),
    createdAt: new Date('2024-01-02').toISOString(),
  },
  {
    id: '3',
    name: 'SK Hynix',
    industry: 'Technology',
    sector: 'Semiconductors',
    description: 'Memory semiconductor supplier',
    riskScore: 3.5,
    marketCap: 80000000000,
    employees: 33000,
    founded: 1983,
    headquarters: 'Icheon, South Korea',
    website: 'https://www.skhynix.com',
    lastUpdated: new Date().toISOString(),
    createdAt: new Date('2024-01-03').toISOString(),
  },
];

export const companyResolvers = {
  Query: {
    company: (_: any, { id }: { id: string }, context: Context) => {
      return context.loaders.company.load(id);
    },
    
    companies: (_: any, args: any, _context: Context) => {
      const { first = 10, filter, sort } = args;
      let filteredCompanies = [...mockCompanies];
      
      // Apply filters
      if (filter) {
        if (filter.name) {
          filteredCompanies = filteredCompanies.filter(c => 
            c.name.toLowerCase().includes(filter.name.toLowerCase())
          );
        }
        if (filter.industry) {
          filteredCompanies = filteredCompanies.filter(c => 
            c.industry === filter.industry
          );
        }
        if (filter.minRiskScore !== undefined) {
          filteredCompanies = filteredCompanies.filter(c => 
            c.riskScore >= filter.minRiskScore
          );
        }
        if (filter.maxRiskScore !== undefined) {
          filteredCompanies = filteredCompanies.filter(c => 
            c.riskScore <= filter.maxRiskScore
          );
        }
      }
      
      // Apply sorting
      if (sort) {
        filteredCompanies.sort((a, b) => {
          let aVal: any, bVal: any;
          
          switch (sort.field) {
            case 'NAME':
              aVal = a.name;
              bVal = b.name;
              break;
            case 'RISK_SCORE':
              aVal = a.riskScore;
              bVal = b.riskScore;
              break;
            case 'MARKET_CAP':
              aVal = a.marketCap;
              bVal = b.marketCap;
              break;
            default:
              aVal = a.createdAt;
              bVal = b.createdAt;
          }
          
          if (sort.direction === 'ASC') {
            return aVal > bVal ? 1 : -1;
          } else {
            return aVal < bVal ? 1 : -1;
          }
        });
      }
      
      // Pagination
      const paginatedCompanies = filteredCompanies.slice(0, first);
      
      return {
        edges: paginatedCompanies.map((company, index) => ({
          node: company,
          cursor: Buffer.from(`company:${index}`).toString('base64'),
        })),
        pageInfo: {
          hasNextPage: filteredCompanies.length > first,
          hasPreviousPage: false,
          startCursor: paginatedCompanies.length > 0 
            ? Buffer.from('company:0').toString('base64') 
            : null,
          endCursor: paginatedCompanies.length > 0 
            ? Buffer.from(`company:${paginatedCompanies.length - 1}`).toString('base64')
            : null,
        },
        totalCount: filteredCompanies.length,
      };
    },
    
    searchCompanies: (_: any, { query, limit = 10 }: any, _context: Context) => {
      return mockCompanies
        .filter(company => 
          company.name.toLowerCase().includes(query.toLowerCase()) ||
          company.description.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, limit);
    },
  },
};