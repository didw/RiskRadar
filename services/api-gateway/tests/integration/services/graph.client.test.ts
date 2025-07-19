import { GraphServiceClient } from '../../../src/services/graph.client';

// Mock GraphQL client
jest.mock('graphql-request', () => ({
  GraphQLClient: jest.fn().mockImplementation(() => ({
    request: jest.fn(),
  })),
}));

// Mock fetch for health checks
global.fetch = jest.fn();

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

const mockNetworkRisk = {
  id: 'network-risk-1',
  companyId: '1',
  networkScore: 3.5,
  centralityScore: 0.75,
  connectedCompanies: [mockCompany],
  riskPropagation: {
    directRisk: 3.2,
    indirectRisk: 2.8,
    maxDepth: 3,
  },
  analyzedAt: new Date().toISOString(),
};

describe('GraphServiceClient', () => {
  let client: GraphServiceClient;
  let mockRequest: jest.Mock;

  beforeEach(() => {
    const { GraphQLClient } = require('graphql-request');
    mockRequest = jest.fn();
    GraphQLClient.mockImplementation(() => ({
      request: mockRequest,
    }));

    client = new GraphServiceClient();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('healthCheck', () => {
    it('should return true for healthy service', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      const result = await client.healthCheck();

      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/health'));
    });

    it('should return false for unhealthy service', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
      });

      const result = await client.healthCheck();

      expect(result).toBe(false);
    });

    it('should return false on network error', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const result = await client.healthCheck();

      expect(result).toBe(false);
    });
  });

  describe('getCompany', () => {
    it('should return company data for valid ID', async () => {
      mockRequest.mockResolvedValue({
        company: mockCompany,
      });

      const result = await client.getCompany('1');

      expect(result).toEqual(mockCompany);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object), // GraphQL query
        { id: '1' }
      );
    });

    it('should return null for non-existent company', async () => {
      mockRequest.mockResolvedValue({
        company: null,
      });

      const result = await client.getCompany('non-existent');

      expect(result).toBeNull();
    });

    it('should return null on GraphQL error', async () => {
      mockRequest.mockRejectedValue(new Error('GraphQL error'));

      const result = await client.getCompany('1');

      expect(result).toBeNull();
    });
  });

  describe('getCompanies', () => {
    it('should return list of companies', async () => {
      mockRequest.mockResolvedValue({
        companies: {
          edges: [
            { node: mockCompany },
          ],
        },
      });

      const result = await client.getCompanies();

      expect(result).toEqual([mockCompany]);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { filter: undefined, limit: 10, offset: 0 }
      );
    });

    it('should apply filters correctly', async () => {
      mockRequest.mockResolvedValue({
        companies: {
          edges: [],
        },
      });

      const filter = {
        industry: 'Technology',
        minRiskScore: 3.0,
        maxRiskScore: 4.0,
      };

      await client.getCompanies(filter, 20, 10);

      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { filter, limit: 20, offset: 10 }
      );
    });

    it('should return empty array on error', async () => {
      mockRequest.mockRejectedValue(new Error('Service error'));

      const result = await client.getCompanies();

      expect(result).toEqual([]);
    });
  });

  describe('getCompaniesByIds', () => {
    it('should return companies for multiple IDs', async () => {
      mockRequest.mockResolvedValue({
        company0: mockCompany,
        company1: { ...mockCompany, id: '2', name: 'Hyundai' },
      });

      const result = await client.getCompaniesByIds(['1', '2']);

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual(mockCompany);
      expect(result[1].name).toBe('Hyundai');
    });

    it('should handle null companies in batch response', async () => {
      mockRequest.mockResolvedValue({
        company0: mockCompany,
        company1: null,
      });

      const result = await client.getCompaniesByIds(['1', 'non-existent']);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual(mockCompany);
    });

    it('should return empty array on error', async () => {
      mockRequest.mockRejectedValue(new Error('Batch query failed'));

      const result = await client.getCompaniesByIds(['1', '2']);

      expect(result).toEqual([]);
    });
  });

  describe('getNetworkRisk', () => {
    it('should return network risk analysis', async () => {
      mockRequest.mockResolvedValue({
        networkRisk: mockNetworkRisk,
      });

      const result = await client.getNetworkRisk('1');

      expect(result).toEqual(mockNetworkRisk);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { companyId: '1' }
      );
    });

    it('should return null for company without network risk', async () => {
      mockRequest.mockResolvedValue({
        networkRisk: null,
      });

      const result = await client.getNetworkRisk('1');

      expect(result).toBeNull();
    });

    it('should return null on service error', async () => {
      mockRequest.mockRejectedValue(new Error('Network analysis failed'));

      const result = await client.getNetworkRisk('1');

      expect(result).toBeNull();
    });
  });

  describe('getConnectedCompanies', () => {
    it('should return connected companies with default depth', async () => {
      mockRequest.mockResolvedValue({
        connectedCompanies: [mockCompany],
      });

      const result = await client.getConnectedCompanies('1');

      expect(result).toEqual([mockCompany]);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { companyId: '1', depth: 1 }
      );
    });

    it('should use custom depth parameter', async () => {
      mockRequest.mockResolvedValue({
        connectedCompanies: [],
      });

      await client.getConnectedCompanies('1', 3);

      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { companyId: '1', depth: 3 }
      );
    });

    it('should return empty array on error', async () => {
      mockRequest.mockRejectedValue(new Error('Connection query failed'));

      const result = await client.getConnectedCompanies('1');

      expect(result).toEqual([]);
    });
  });

  describe('searchCompanies', () => {
    it('should search companies by query', async () => {
      mockRequest.mockResolvedValue({
        searchCompanies: [mockCompany],
      });

      const result = await client.searchCompanies('Samsung');

      expect(result).toEqual([mockCompany]);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { query: 'Samsung', limit: 10 }
      );
    });

    it('should use custom limit', async () => {
      mockRequest.mockResolvedValue({
        searchCompanies: [],
      });

      await client.searchCompanies('test', 5);

      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { query: 'test', limit: 5 }
      );
    });

    it('should return empty array on search error', async () => {
      mockRequest.mockRejectedValue(new Error('Search failed'));

      const result = await client.searchCompanies('test');

      expect(result).toEqual([]);
    });
  });

  describe('addCompany', () => {
    it('should add new company successfully', async () => {
      const newCompanyData = {
        name: 'New Company',
        industry: 'Technology',
      };

      mockRequest.mockResolvedValue({
        addCompany: { ...mockCompany, ...newCompanyData },
      });

      const result = await client.addCompany(newCompanyData);

      expect(result?.name).toBe('New Company');
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { input: newCompanyData }
      );
    });

    it('should return null on add error', async () => {
      mockRequest.mockRejectedValue(new Error('Add company failed'));

      const result = await client.addCompany({ name: 'Test' });

      expect(result).toBeNull();
    });
  });

  describe('updateCompany', () => {
    it('should update company successfully', async () => {
      const updates = { riskScore: 3.5 };

      mockRequest.mockResolvedValue({
        updateCompany: { ...mockCompany, ...updates },
      });

      const result = await client.updateCompany('1', updates);

      expect(result?.riskScore).toBe(3.5);
      expect(mockRequest).toHaveBeenCalledWith(
        expect.any(Object),
        { id: '1', input: updates }
      );
    });

    it('should return null on update error', async () => {
      mockRequest.mockRejectedValue(new Error('Update failed'));

      const result = await client.updateCompany('1', { name: 'Updated' });

      expect(result).toBeNull();
    });
  });
});