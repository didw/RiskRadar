import { withFilter, PubSub } from 'graphql-subscriptions';
import { Context } from './index.js';

// PubSub 인스턴스 생성 (프로덕션에서는 Redis PubSub 사용)
export const pubsub = new PubSub() as any;

// Subscription 이벤트 타입
export const SUBSCRIPTION_EVENTS = {
  NEWS_UPDATE: 'NEWS_UPDATE',
  RISK_ALERT: 'RISK_ALERT',
  RISK_SCORE_UPDATE: 'RISK_SCORE_UPDATE',
  SYSTEM_STATUS: 'SYSTEM_STATUS',
} as const;

export const subscriptionResolvers = {
  Subscription: {
    // 실시간 뉴스 업데이트
    newsUpdate: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([SUBSCRIPTION_EVENTS.NEWS_UPDATE]),
        (payload: any, variables: any, context?: Context) => {
          // 인증 확인
          if (!context?.user) {
            return false;
          }

          const { filters } = variables;
          const newsUpdate = payload.newsUpdate;
          const article = newsUpdate.article;

          // 필터링 로직
          if (filters) {
            // 회사 ID 필터
            if (filters.companyIds?.length > 0) {
              const hasMatchingCompany = article.mentionedCompanies.some((company: any) =>
                filters.companyIds.includes(company.id)
              );
              if (!hasMatchingCompany) return false;
            }

            // 산업 필터
            if (filters.industries?.length > 0) {
              const hasMatchingIndustry = article.mentionedCompanies.some((company: any) =>
                filters.industries.includes(company.industry)
              );
              if (!hasMatchingIndustry) return false;
            }

            // 최소 리스크 점수 필터 (relevanceScore 사용)
            if (filters.minRiskScore && article.relevanceScore < filters.minRiskScore) {
              return false;
            }

            // 뉴스 소스 필터
            if (filters.sources?.length > 0 && !filters.sources.includes(article.source)) {
              return false;
            }
          }

          return true;
        }
      ),
    },

    // 리스크 알림
    riskAlert: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([SUBSCRIPTION_EVENTS.RISK_ALERT]),
        (payload: any, variables: any, context?: Context) => {
          // 인증 확인
          if (!context?.user) {
            return false;
          }

          const { companyIds } = variables;
          const riskAlert = payload.riskAlert;

          // 사용자가 관심있는 회사의 알림만 전송
          return companyIds.includes(riskAlert.company.id);
        }
      ),
    },

    // 리스크 점수 업데이트
    riskScoreUpdate: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([SUBSCRIPTION_EVENTS.RISK_SCORE_UPDATE]),
        (payload: any, variables: any, context?: Context) => {
          // 인증 확인
          if (!context?.user) {
            return false;
          }

          const { companyId } = variables;
          const scoreUpdate = payload.riskScoreUpdate;

          return scoreUpdate.companyId === companyId;
        }
      ),
    },

    // 시스템 상태 업데이트
    systemStatus: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([SUBSCRIPTION_EVENTS.SYSTEM_STATUS]),
        (payload: any, variables: any, context?: Context) => {
          // 관리자만 시스템 상태 구독 가능
          return context?.user?.role === 'admin';
        }
      ),
    },
  },
};

// 이벤트 발행 헬퍼 함수들
export const publishNewsUpdate = (newsUpdate: any) => {
  pubsub.publish(SUBSCRIPTION_EVENTS.NEWS_UPDATE, { newsUpdate });
};

export const publishRiskAlert = (riskAlert: any) => {
  pubsub.publish(SUBSCRIPTION_EVENTS.RISK_ALERT, { riskAlert });
};

export const publishRiskScoreUpdate = (scoreUpdate: any) => {
  pubsub.publish(SUBSCRIPTION_EVENTS.RISK_SCORE_UPDATE, { riskScoreUpdate: scoreUpdate });
};

export const publishSystemStatus = (systemStatus: any) => {
  pubsub.publish(SUBSCRIPTION_EVENTS.SYSTEM_STATUS, { systemStatus });
};

// Mock 데이터 생성기 (테스트용)
export const startMockDataGenerator = () => {
  // 30초마다 Mock 뉴스 업데이트 발행
  setInterval(() => {
    const mockNewsUpdate = {
      article: {
        id: `news-${Date.now()}`,
        title: `실시간 뉴스: ${new Date().toLocaleTimeString()}`,
        content: '실시간으로 업데이트되는 뉴스 내용입니다.',
        summary: '뉴스 요약',
        url: 'https://example.com/news/mock',
        source: 'Mock News',
        author: 'Mock Author',
        publishedAt: new Date().toISOString(),
        crawledAt: new Date().toISOString(),
        category: 'Technology',
        tags: ['테스트', '실시간', '업데이트'],
        sentiment: Math.random() * 2 - 1, // -1 ~ 1
        relevanceScore: Math.random() * 10, // 0 ~ 10
        mentionedCompanies: [
          {
            id: '1',
            name: 'Samsung Electronics',
            industry: 'Technology'
          }
        ],
        detectedRisks: [],
        language: 'ko',
        imageUrl: null
      },
      updateType: 'NEW_ARTICLE',
      timestamp: new Date().toISOString(),
    };

    publishNewsUpdate(mockNewsUpdate);
  }, 30000); // 30초

  // 60초마다 Mock 리스크 알림 발행
  setInterval(() => {
    const mockRiskAlert = {
      id: `alert-${Date.now()}`,
      type: 'SCORE_CHANGE',
      severity: 'MEDIUM',
      company: {
        id: '1',
        name: 'Samsung Electronics',
        industry: 'Technology'
      },
      message: '리스크 점수가 변경되었습니다.',
      details: {
        previousScore: 3.2,
        currentScore: 3.8,
        changePercentage: 18.75,
        triggerEvent: '새로운 뉴스 발생',
        affectedMetrics: ['sentiment', 'volume'],
        relatedNews: []
      },
      timestamp: new Date().toISOString(),
      acknowledged: false,
    };

    publishRiskAlert(mockRiskAlert);
  }, 60000); // 60초
};