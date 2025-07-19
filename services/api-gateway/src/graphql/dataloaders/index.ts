import DataLoader from 'dataloader';
import { graphServiceClient } from '../../services/graph.client.js';
import { mlServiceClient } from '../../services/ml.client.js';
import logger from '../../utils/logger.js';

// Company DataLoader
export const createCompanyLoader = () => {
  return new DataLoader<string, any>(async (ids) => {
    try {
      const companies = await graphServiceClient.getCompaniesByIds([...ids]);
      
      // Create a map for O(1) lookup
      const companyMap = new Map(
        companies.map(company => [company.id, company])
      );
      
      // Return companies in the same order as requested IDs
      return ids.map(id => companyMap.get(id) || null);
    } catch (error) {
      logger.error('Company DataLoader error:', error);
      // Return null for all requested IDs on error
      return ids.map(() => null);
    }
  }, {
    cache: true,
    maxBatchSize: 100,
  });
};

// Connected Companies DataLoader
export const createConnectedCompaniesLoader = () => {
  return new DataLoader<string, any[]>(async (companyIds) => {
    try {
      const results = await Promise.all(
        companyIds.map(id => graphServiceClient.getConnectedCompanies(id))
      );
      
      return results;
    } catch (error) {
      logger.error('Connected Companies DataLoader error:', error);
      return companyIds.map(() => []);
    }
  }, {
    cache: true,
    maxBatchSize: 50,
  });
};

// Network Risk DataLoader
export const createNetworkRiskLoader = () => {
  return new DataLoader<string, any>(async (companyIds) => {
    try {
      const results = await Promise.all(
        companyIds.map(id => graphServiceClient.getNetworkRisk(id))
      );
      
      return results;
    } catch (error) {
      logger.error('Network Risk DataLoader error:', error);
      return companyIds.map(() => null);
    }
  }, {
    cache: true,
    maxBatchSize: 50,
  });
};

// Risk Predictions DataLoader
export const createRiskPredictionsLoader = () => {
  return new DataLoader<string, any[]>(async (companyIds) => {
    try {
      const results = await Promise.all(
        companyIds.map(id => mlServiceClient.predictRisk(id))
      );
      
      return results;
    } catch (error) {
      logger.error('Risk Predictions DataLoader error:', error);
      return companyIds.map(() => []);
    }
  }, {
    cache: true,
    maxBatchSize: 30,
  });
};

// Sentiment Trends DataLoader
export const createSentimentTrendsLoader = () => {
  return new DataLoader<string, any[]>(async (companyIds) => {
    try {
      const results = await Promise.all(
        companyIds.map(id => mlServiceClient.getSentimentTrends(id))
      );
      
      return results;
    } catch (error) {
      logger.error('Sentiment Trends DataLoader error:', error);
      return companyIds.map(() => []);
    }
  }, {
    cache: true,
    maxBatchSize: 30,
  });
};

// Risk Insights DataLoader
export const createRiskInsightsLoader = () => {
  return new DataLoader<string, any[]>(async (companyIds) => {
    try {
      const results = await Promise.all(
        companyIds.map(id => mlServiceClient.getRiskInsights(id))
      );
      
      return results;
    } catch (error) {
      logger.error('Risk Insights DataLoader error:', error);
      return companyIds.map(() => []);
    }
  }, {
    cache: true,
    maxBatchSize: 30,
  });
};

// Create all loaders for a single request context
export const createLoaders = () => {
  return {
    company: createCompanyLoader(),
    connectedCompanies: createConnectedCompaniesLoader(),
    networkRisk: createNetworkRiskLoader(),
    riskPredictions: createRiskPredictionsLoader(),
    sentimentTrends: createSentimentTrendsLoader(),
    riskInsights: createRiskInsightsLoader(),
  };
};

export type Loaders = ReturnType<typeof createLoaders>;