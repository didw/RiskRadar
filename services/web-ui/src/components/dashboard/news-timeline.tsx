"use client";

import { useQuery, useSubscription } from "@apollo/client";
import { gql } from "@apollo/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDistanceToNow } from "date-fns";
import { ko } from "date-fns/locale";
import { AlertCircle, TrendingUp, TrendingDown, Newspaper } from "lucide-react";
import { useEffect, useState } from "react";

const GET_NEWS_FEED = gql`
  query GetNewsFeed($limit: Int, $offset: Int) {
    newsFeed(limit: $limit, offset: $offset) {
      items {
        id
        title
        summary
        source
        publishedAt
        sentiment
        riskImpact
        relatedCompanies {
          id
          name
          riskScoreChange
        }
        tags
      }
      totalCount
    }
  }
`;

const NEWS_UPDATE_SUBSCRIPTION = gql`
  subscription OnNewsUpdate {
    newsUpdate {
      id
      title
      summary
      source
      publishedAt
      sentiment
      riskImpact
      relatedCompanies {
        id
        name
        riskScoreChange
      }
      tags
    }
  }
`;

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  riskImpact: 'high' | 'medium' | 'low';
  relatedCompanies: Array<{
    id: string;
    name: string;
    riskScoreChange: number;
  }>;
  tags: string[];
}

const sentimentConfig = {
  positive: { label: '긍정적', color: 'bg-green-100 text-green-800' },
  negative: { label: '부정적', color: 'bg-red-100 text-red-800' },
  neutral: { label: '중립', color: 'bg-gray-100 text-gray-800' },
};

const impactConfig = {
  high: { label: '높음', icon: AlertCircle, color: 'text-red-600' },
  medium: { label: '중간', icon: TrendingUp, color: 'text-yellow-600' },
  low: { label: '낮음', icon: TrendingDown, color: 'text-green-600' },
};

export function NewsTimeline() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  
  const { data, loading, error } = useQuery(GET_NEWS_FEED, {
    variables: { limit: 20, offset: 0 },
  });

  const { data: subscriptionData } = useSubscription(NEWS_UPDATE_SUBSCRIPTION);

  useEffect(() => {
    if (data?.newsFeed?.items) {
      setNewsItems(data.newsFeed.items);
    }
  }, [data]);

  useEffect(() => {
    if (subscriptionData?.newsUpdate) {
      setNewsItems(prev => [subscriptionData.newsUpdate, ...prev].slice(0, 20));
    }
  }, [subscriptionData]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5" />
            실시간 뉴스
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    // Fallback to mock data
    const mockNews: NewsItem[] = [
      {
        id: '1',
        title: 'SK하이닉스, HBM 생산 확대로 실적 개선 전망',
        summary: 'SK하이닉스가 고대역폭 메모리(HBM) 생산을 확대하며 AI 반도체 시장 공략에 나섰다.',
        source: '한국경제',
        publishedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        sentiment: 'positive',
        riskImpact: 'low',
        relatedCompanies: [
          { id: '2', name: 'SK하이닉스', riskScoreChange: -3 }
        ],
        tags: ['반도체', 'AI', 'HBM'],
      },
      {
        id: '2',
        title: '카카오, 규제 리스크 증가로 주가 하락',
        summary: '금융당국의 핀테크 규제 강화로 카카오페이 등 금융 계열사 실적 우려 확대',
        source: '매일경제',
        publishedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        sentiment: 'negative',
        riskImpact: 'high',
        relatedCompanies: [
          { id: '4', name: '카카오', riskScoreChange: 8 }
        ],
        tags: ['핀테크', '규제', '금융'],
      },
      {
        id: '3',
        title: '현대자동차, 전기차 시장 점유율 확대',
        summary: '아이오닉 시리즈 글로벌 판매 호조로 전기차 시장 점유율 상승',
        source: '조선일보',
        publishedAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        sentiment: 'positive',
        riskImpact: 'medium',
        relatedCompanies: [
          { id: '3', name: '현대자동차', riskScoreChange: -2 }
        ],
        tags: ['전기차', '자동차', '친환경'],
      },
    ];

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5" />
            실시간 뉴스
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-4">
              {mockNews.map((news) => (
                <NewsCard key={news.id} news={news} />
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5" />
          실시간 뉴스
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="space-y-4">
            {newsItems.map((news) => (
              <NewsCard key={news.id} news={news} />
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function NewsCard({ news }: { news: NewsItem }) {
  const Impact = impactConfig[news.riskImpact].icon;
  
  return (
    <div className="border rounded-lg p-4 space-y-3 hover:bg-accent/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <h4 className="font-medium text-sm leading-tight">{news.title}</h4>
        <Impact className={`h-4 w-4 flex-shrink-0 ${impactConfig[news.riskImpact].color}`} />
      </div>
      
      <p className="text-xs text-muted-foreground line-clamp-2">{news.summary}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={sentimentConfig[news.sentiment].color}>
            {sentimentConfig[news.sentiment].label}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {news.source}
          </span>
        </div>
        <span className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(news.publishedAt), { addSuffix: true, locale: ko })}
        </span>
      </div>
      
      {news.relatedCompanies.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {news.relatedCompanies.map((company) => (
            <Badge
              key={company.id}
              variant="secondary"
              className="text-xs"
            >
              {company.name}
              <span className={company.riskScoreChange > 0 ? 'text-red-600 ml-1' : 'text-green-600 ml-1'}>
                {company.riskScoreChange > 0 ? '+' : ''}{company.riskScoreChange}
              </span>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}