import { companyResolvers } from '../../../src/graphql/resolvers/company';
import { Context } from '../../../src/graphql/resolvers';

// Mock the context with DataLoader
const createMockContext = () => ({
  loaders: {
    company: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'company',
    },
    connectedCompanies: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'connectedCompanies',
    },
    networkRisk: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'networkRisk',
    },
    riskPredictions: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'riskPredictions',
    },
    sentimentTrends: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'sentimentTrends',
    },
    riskInsights: {
      load: jest.fn(),
      loadMany: jest.fn(),
      clear: jest.fn(),
      clearAll: jest.fn(),
      prime: jest.fn(),
      name: 'riskInsights',
    },
  },
  services: {
    graph: {} as any,
    ml: {} as any,
  },
}) as any;

const mockCompany = {
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
};

describe('Company Resolvers', () => {
  describe('Query.company', () => {
    it('should return company by id using DataLoader', async () => {
      const context = createMockContext();
      const mockLoad = context.loaders.company.load as jest.Mock;
      mockLoad.mockResolvedValue(mockCompany);

      const result = await companyResolvers.Query.company(
        {},
        { id: '1' },
        context
      );

      expect(mockLoad).toHaveBeenCalledWith('1');
      expect(result).toEqual(mockCompany);
    });

    it('should return null for non-existent company', async () => {
      const context = createMockContext();
      const mockLoad = context.loaders.company.load as jest.Mock;
      mockLoad.mockResolvedValue(null);

      const result = await companyResolvers.Query.company(
        {},
        { id: 'non-existent' },
        context
      );

      expect(mockLoad).toHaveBeenCalledWith('non-existent');
      expect(result).toBeNull();
    });
  });

  describe('Query.companies', () => {
    it('should return paginated companies with filtering', () => {
      const context = createMockContext();
      const args = {
        first: 5,
        filter: {
          industry: 'Technology',
          minRiskScore: 3.0,
        },
      };

      const result = companyResolvers.Query.companies({}, args, context);

      expect(result).toHaveProperty('edges');
      expect(result).toHaveProperty('pageInfo');
      expect(result).toHaveProperty('totalCount');
      expect(Array.isArray(result.edges)).toBe(true);
    });

    it('should apply name filter correctly', () => {
      const context = createMockContext();
      const args = {
        first: 10,
        filter: {
          name: 'Samsung',
        },
      };

      const result = companyResolvers.Query.companies({}, args, context);
      
      // Check that filtered results contain only companies with 'Samsung' in name
      const filteredCompanies = result.edges.map((edge: any) => edge.node);
      filteredCompanies.forEach((company: any) => {
        expect(company.name.toLowerCase()).toContain('samsung');
      });
    });

    it('should apply risk score filter correctly', () => {
      const context = createMockContext();
      const args = {
        first: 10,
        filter: {
          minRiskScore: 3.0,
          maxRiskScore: 4.0,
        },
      };

      const result = companyResolvers.Query.companies({}, args, context);
      
      const filteredCompanies = result.edges.map((edge: any) => edge.node);
      filteredCompanies.forEach((company: any) => {
        expect(company.riskScore).toBeGreaterThanOrEqual(3.0);
        expect(company.riskScore).toBeLessThanOrEqual(4.0);
      });
    });

    it('should sort companies by risk score descending', () => {
      const context = createMockContext();
      const args = {
        first: 10,
        sort: {
          field: 'RISK_SCORE',
          direction: 'DESC',
        },
      };

      const result = companyResolvers.Query.companies({}, args, context);
      
      const companies = result.edges.map((edge: any) => edge.node);
      for (let i = 0; i < companies.length - 1; i++) {
        expect(companies[i].riskScore).toBeGreaterThanOrEqual(companies[i + 1].riskScore);
      }
    });

    it('should sort companies by name ascending', () => {
      const context = createMockContext();
      const args = {
        first: 10,
        sort: {
          field: 'NAME',
          direction: 'ASC',
        },
      };

      const result = companyResolvers.Query.companies({}, args, context);
      
      const companies = result.edges.map((edge: any) => edge.node);
      for (let i = 0; i < companies.length - 1; i++) {
        expect(companies[i].name <= companies[i + 1].name).toBe(true);
      }
    });

    it('should respect pagination limit', () => {
      const context = createMockContext();
      const args = { first: 2 };

      const result = companyResolvers.Query.companies({}, args, context);

      expect(result.edges.length).toBeLessThanOrEqual(2);
    });

    it('should return correct pagination info', () => {
      const context = createMockContext();
      const args = { first: 2 };

      const result = companyResolvers.Query.companies({}, args, context);

      expect(result.pageInfo).toHaveProperty('hasNextPage');
      expect(result.pageInfo).toHaveProperty('hasPreviousPage');
      expect(result.pageInfo).toHaveProperty('startCursor');
      expect(result.pageInfo).toHaveProperty('endCursor');
      expect(typeof result.pageInfo.hasNextPage).toBe('boolean');
      expect(typeof result.pageInfo.hasPreviousPage).toBe('boolean');
    });
  });

  describe('Query.searchCompanies', () => {
    it('should search companies by name', () => {
      const context = createMockContext();
      const args = {
        query: 'Samsung',
        limit: 5,
      };

      const result = companyResolvers.Query.searchCompanies({}, args, context);

      expect(Array.isArray(result)).toBe(true);
      result.forEach((company: any) => {
        const matchesName = company.name.toLowerCase().includes('samsung');
        const matchesDescription = company.description.toLowerCase().includes('samsung');
        expect(matchesName || matchesDescription).toBe(true);
      });
    });

    it('should search companies by description', () => {
      const context = createMockContext();
      const args = {
        query: 'electronics',
        limit: 5,
      };

      const result = companyResolvers.Query.searchCompanies({}, args, context);

      expect(Array.isArray(result)).toBe(true);
      result.forEach((company: any) => {
        const matchesName = company.name.toLowerCase().includes('electronics');
        const matchesDescription = company.description.toLowerCase().includes('electronics');
        expect(matchesName || matchesDescription).toBe(true);
      });
    });

    it('should respect search limit', () => {
      const context = createMockContext();
      const args = {
        query: 'company',
        limit: 1,
      };

      const result = companyResolvers.Query.searchCompanies({}, args, context);

      expect(result.length).toBeLessThanOrEqual(1);
    });

    it('should return empty array for no matches', () => {
      const context = createMockContext();
      const args = {
        query: 'nonexistentcompany',
        limit: 10,
      };

      const result = companyResolvers.Query.searchCompanies({}, args, context);

      expect(result).toEqual([]);
    });
  });
});