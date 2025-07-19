import { config } from '../config';
import logger from '../utils/logger';

interface MLServiceStatus {
  status: 'healthy' | 'degraded' | 'down';
  lastUpdated: string;
  queueSize: number;
  processing: {
    newsAnalysis: boolean;
    riskDetection: boolean;
    sentimentAnalysis: boolean;
  };
  metrics: {
    processedToday: number;
    averageProcessingTime: number;
    errorRate: number;
  };
}

interface NewsAnalysisRequest {
  id: string;
  title: string;
  content: string;
  url: string;
  source: string;
  publishedAt: string;
}

interface NewsAnalysisResult {
  id: string;
  sentiment: number;
  relevanceScore: number;
  extractedEntities: {
    companies: string[];
    keywords: string[];
    locations: string[];
  };
  detectedRisks: {
    type: string;
    confidence: number;
    description: string;
  }[];
  summary: string;
  processedAt: string;
}

interface RiskPrediction {
  companyId: string;
  riskType: string;
  probability: number;
  severity: number;
  confidence: number;
  factors: {
    factor: string;
    impact: number;
    weight: number;
  }[];
  timeframe: string;
  predictedAt: string;
}

export class MLServiceClient {
  private baseUrl: string;
  private healthCheckUrl: string;

  constructor() {
    this.baseUrl = config.services.mlServiceUrl;
    this.healthCheckUrl = `${this.baseUrl}/health`;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(this.healthCheckUrl);
      return response.ok;
    } catch (error) {
      logger.error('ML service health check failed:', error);
      return false;
    }
  }

  async getStatus(): Promise<MLServiceStatus | null> {
    try {
      const response = await fetch(`${this.baseUrl}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const status = await response.json() as MLServiceStatus;
      return status;
    } catch (error) {
      logger.error('Failed to get ML service status:', error);
      return null;
    }
  }

  async analyzeNews(newsData: NewsAnalysisRequest): Promise<NewsAnalysisResult | null> {
    try {
      const response = await fetch(`${this.baseUrl}/analyze/news`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newsData),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json() as NewsAnalysisResult;
      return result;
    } catch (error) {
      logger.error('Failed to analyze news:', error);
      return null;
    }
  }

  async batchAnalyzeNews(newsItems: NewsAnalysisRequest[]): Promise<NewsAnalysisResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/analyze/news/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: newsItems }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const results = await response.json() as any;
      return results.items || [];
    } catch (error) {
      logger.error('Failed to batch analyze news:', error);
      return [];
    }
  }

  async predictRisk(companyId: string, timeframe = '30d'): Promise<RiskPrediction[]> {
    try {
      const response = await fetch(`${this.baseUrl}/predict/risk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ companyId, timeframe }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const predictions = await response.json() as any;
      return predictions.risks || [];
    } catch (error) {
      logger.error(`Failed to predict risk for company ${companyId}:`, error);
      return [];
    }
  }

  async getSentimentTrends(companyId: string, days = 30): Promise<{
    date: string;
    sentiment: number;
    volume: number;
  }[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/sentiment/trends?companyId=${companyId}&days=${days}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const trends = await response.json() as any;
      return trends.data || [];
    } catch (error) {
      logger.error(`Failed to get sentiment trends for company ${companyId}:`, error);
      return [];
    }
  }

  async getEntityExtraction(text: string): Promise<{
    companies: string[];
    keywords: string[];
    locations: string[];
    persons: string[];
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/extract/entities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const entities = await response.json() as any;
      return entities;
    } catch (error) {
      logger.error('Failed to extract entities:', error);
      return {
        companies: [],
        keywords: [],
        locations: [],
        persons: [],
      };
    }
  }

  async getRiskInsights(companyId: string): Promise<{
    id: string;
    type: string;
    title: string;
    description: string;
    importance: number;
    confidence: number;
    createdAt: string;
  }[]> {
    try {
      const response = await fetch(`${this.baseUrl}/insights/risk?companyId=${companyId}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const insights = await response.json() as any;
      return insights.data || [];
    } catch (error) {
      logger.error(`Failed to get risk insights for company ${companyId}:`, error);
      return [];
    }
  }

  async getModelMetrics(): Promise<{
    models: {
      name: string;
      version: string;
      accuracy: number;
      lastTrained: string;
      status: 'active' | 'training' | 'deprecated';
    }[];
    performance: {
      requestsPerSecond: number;
      averageLatency: number;
      errorRate: number;
    };
  } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics/models`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const metrics = await response.json() as any;
      return metrics;
    } catch (error) {
      logger.error('Failed to get model metrics:', error);
      return null;
    }
  }

  async trainModel(modelType: string, trainingData: any): Promise<{
    jobId: string;
    status: string;
    estimatedDuration: number;
  } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/train/${modelType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trainingData),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const job = await response.json() as any;
      return job;
    } catch (error) {
      logger.error(`Failed to train model ${modelType}:`, error);
      return null;
    }
  }

  async getTrainingJob(jobId: string): Promise<{
    id: string;
    modelType: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    startedAt: string;
    completedAt?: string;
    metrics?: {
      accuracy: number;
      loss: number;
      validationAccuracy: number;
    };
  } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/train/jobs/${jobId}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const job = await response.json() as any;
      return job;
    } catch (error) {
      logger.error(`Failed to get training job ${jobId}:`, error);
      return null;
    }
  }
}

export const mlServiceClient = new MLServiceClient();