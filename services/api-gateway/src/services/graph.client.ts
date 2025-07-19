import { GraphQLClient } from 'graphql-request';
import { gql } from 'graphql-tag';
import { config } from '../config/index.js';
import logger from '../utils/logger.js';

interface Company {
  id: string;
  name: string;
  industry?: string;
  sector?: string;
  description?: string;
  riskScore?: number;
  marketCap?: number;
  employees?: number;
  founded?: number;
  headquarters?: string;
  website?: string;
  lastUpdated: string;
  createdAt: string;
}

interface NetworkRisk {
  id: string;
  companyId: string;
  networkScore: number;
  centralityScore: number;
  connectedCompanies: Company[];
  riskPropagation: {
    directRisk: number;
    indirectRisk: number;
    maxDepth: number;
  };
  analyzedAt: string;
}

interface GraphConnection {
  sourceId: string;
  targetId: string;
  connectionType: string;
  strength: number;
  metadata?: Record<string, any>;
}

export class GraphServiceClient {
  private client: GraphQLClient;
  private healthCheckUrl: string;

  constructor() {
    this.client = new GraphQLClient(config.services.graphServiceUrl);
    this.healthCheckUrl = `${config.services.graphServiceUrl.replace('/graphql', '')}/health`;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(this.healthCheckUrl);
      return response.ok;
    } catch (error) {
      logger.error('Graph service health check failed:', error);
      return false;
    }
  }

  async getCompany(id: string): Promise<Company | null> {
    try {
      const query = gql`
        query GetCompany($id: ID!) {
          company(id: $id) {
            id
            name
            industry
            sector
            description
            riskScore
            marketCap
            employees
            founded
            headquarters
            website
            lastUpdated
            createdAt
          }
        }
      `;

      const data = await this.client.request(query, { id }) as any;
      return data.company;
    } catch (error) {
      logger.error(`Failed to get company ${id}:`, error);
      return null;
    }
  }

  async getCompanies(filter?: {
    industry?: string;
    minRiskScore?: number;
    maxRiskScore?: number;
  }, limit = 10, offset = 0): Promise<Company[]> {
    try {
      const query = gql`
        query GetCompanies($filter: CompanyFilter, $limit: Int, $offset: Int) {
          companies(filter: $filter, limit: $limit, offset: $offset) {
            edges {
              node {
                id
                name
                industry
                sector
                riskScore
                marketCap
                employees
                lastUpdated
                createdAt
              }
            }
          }
        }
      `;

      const data = await this.client.request(query, { filter, limit, offset }) as any;
      return data.companies.edges.map((edge: any) => edge.node);
    } catch (error) {
      logger.error('Failed to get companies:', error);
      return [];
    }
  }

  async getCompaniesByIds(ids: string[]): Promise<Company[]> {
    try {
      // Batch query for multiple companies
      const queries = ids.map((id, index) => `
        company${index}: company(id: "${id}") {
          id
          name
          industry
          sector
          riskScore
          marketCap
          employees
          lastUpdated
          createdAt
        }
      `).join('\n');

      const query = gql`
        query GetCompaniesByIds {
          ${queries}
        }
      `;

      const data = await this.client.request(query) as any;
      
      // Extract companies from the response
      const companies: Company[] = [];
      Object.values(data).forEach((company: any) => {
        if (company) {
          companies.push(company);
        }
      });

      return companies;
    } catch (error) {
      logger.error('Failed to get companies by IDs:', error);
      return [];
    }
  }

  async getNetworkRisk(companyId: string): Promise<NetworkRisk | null> {
    try {
      const query = gql`
        query GetNetworkRisk($companyId: ID!) {
          networkRisk(companyId: $companyId) {
            id
            companyId
            networkScore
            centralityScore
            connectedCompanies {
              id
              name
              industry
              riskScore
            }
            riskPropagation {
              directRisk
              indirectRisk
              maxDepth
            }
            analyzedAt
          }
        }
      `;

      const data = await this.client.request(query, { companyId }) as any;
      return data.networkRisk;
    } catch (error) {
      logger.error(`Failed to get network risk for company ${companyId}:`, error);
      return null;
    }
  }

  async getConnectedCompanies(companyId: string, depth = 1): Promise<Company[]> {
    try {
      const query = gql`
        query GetConnectedCompanies($companyId: ID!, $depth: Int) {
          connectedCompanies(companyId: $companyId, depth: $depth) {
            id
            name
            industry
            riskScore
            lastUpdated
          }
        }
      `;

      const data = await this.client.request(query, { companyId, depth }) as any;
      return data.connectedCompanies || [];
    } catch (error) {
      logger.error(`Failed to get connected companies for ${companyId}:`, error);
      return [];
    }
  }

  async getGraphConnections(companyId: string): Promise<GraphConnection[]> {
    try {
      const query = gql`
        query GetGraphConnections($companyId: ID!) {
          graphConnections(companyId: $companyId) {
            sourceId
            targetId
            connectionType
            strength
            metadata
          }
        }
      `;

      const data = await this.client.request(query, { companyId }) as any;
      return data.graphConnections || [];
    } catch (error) {
      logger.error(`Failed to get graph connections for ${companyId}:`, error);
      return [];
    }
  }

  async searchCompanies(query: string, limit = 10): Promise<Company[]> {
    try {
      const searchQuery = gql`
        query SearchCompanies($query: String!, $limit: Int) {
          searchCompanies(query: $query, limit: $limit) {
            id
            name
            industry
            sector
            riskScore
            description
          }
        }
      `;

      const data = await this.client.request(searchQuery, { query, limit }) as any;
      return data.searchCompanies || [];
    } catch (error) {
      logger.error(`Failed to search companies with query "${query}":`, error);
      return [];
    }
  }

  async addCompany(companyData: Partial<Company>): Promise<Company | null> {
    try {
      const mutation = gql`
        mutation AddCompany($input: CompanyInput!) {
          addCompany(input: $input) {
            id
            name
            industry
            sector
            description
            riskScore
            marketCap
            employees
            founded
            headquarters
            website
            lastUpdated
            createdAt
          }
        }
      `;

      const data = await this.client.request(mutation, { input: companyData }) as any;
      return data.addCompany;
    } catch (error) {
      logger.error('Failed to add company:', error);
      return null;
    }
  }

  async updateCompany(id: string, updates: Partial<Company>): Promise<Company | null> {
    try {
      const mutation = gql`
        mutation UpdateCompany($id: ID!, $input: CompanyUpdateInput!) {
          updateCompany(id: $id, input: $input) {
            id
            name
            industry
            sector
            description
            riskScore
            marketCap
            employees
            founded
            headquarters
            website
            lastUpdated
            createdAt
          }
        }
      `;

      const data = await this.client.request(mutation, { id, input: updates }) as any;
      return data.updateCompany;
    } catch (error) {
      logger.error(`Failed to update company ${id}:`, error);
      return null;
    }
  }

  // Additional methods for analytics support
  async getCompaniesByIndustry(industry: string, limit = 50): Promise<Company[]> {
    try {
      return await this.getCompanies({ industry }, limit);
    } catch (error) {
      logger.error(`Failed to get companies by industry ${industry}:`, error);
      return [];
    }
  }

  async getCompetitors(companyId: string): Promise<Company[]> {
    try {
      // Mock implementation - would get actual competitors based on industry/market analysis
      const company = await this.getCompany(companyId);
      if (!company?.industry) {
        return [];
      }

      const competitors = await this.getCompaniesByIndustry(company.industry, 10);
      return competitors.filter(c => c.id !== companyId);
    } catch (error) {
      logger.error(`Failed to get competitors for company ${companyId}:`, error);
      return [];
    }
  }
}

export const graphServiceClient = new GraphServiceClient();