import { Context } from './index';

const mockNewsArticles = [
  {
    id: 'news-1',
    title: 'Samsung Reports Strong Q2 Earnings Despite Market Challenges',
    content: 'Samsung Electronics reported better-than-expected second-quarter earnings...',
    summary: 'Samsung beats Q2 expectations with strong semiconductor demand',
    url: 'https://example.com/news/samsung-q2-earnings',
    source: 'Reuters',
    author: 'John Doe',
    publishedAt: new Date('2024-07-19T10:00:00Z').toISOString(),
    crawledAt: new Date('2024-07-19T10:15:00Z').toISOString(),
    category: 'Business',
    tags: ['samsung', 'earnings', 'technology', 'semiconductors'],
    sentiment: 0.7,
    relevanceScore: 0.9,
    mentionedCompanies: [],
    detectedRisks: [],
    language: 'en',
    imageUrl: 'https://example.com/images/samsung-hq.jpg',
  },
  {
    id: 'news-2',
    title: 'Korean Auto Industry Faces Supply Chain Disruptions',
    content: 'Major Korean automotive manufacturers are experiencing supply chain challenges...',
    summary: 'Supply chain issues impact Korean auto production',
    url: 'https://example.com/news/korea-auto-supply-chain',
    source: 'Korea Times',
    author: 'Jane Smith',
    publishedAt: new Date('2024-07-18T14:30:00Z').toISOString(),
    crawledAt: new Date('2024-07-18T14:45:00Z').toISOString(),
    category: 'Industry',
    tags: ['automotive', 'supply-chain', 'korea', 'manufacturing'],
    sentiment: -0.4,
    relevanceScore: 0.8,
    mentionedCompanies: [],
    detectedRisks: [],
    language: 'en',
    imageUrl: null,
  },
  {
    id: 'news-3',
    title: 'SK Hynix Announces Major Investment in AI Chip Development',
    content: 'SK Hynix unveiled plans for a $10 billion investment in next-generation AI chips...',
    summary: 'SK Hynix invests heavily in AI semiconductor technology',
    url: 'https://example.com/news/sk-hynix-ai-investment',
    source: 'TechCrunch',
    author: 'Mike Johnson',
    publishedAt: new Date('2024-07-17T09:00:00Z').toISOString(),
    crawledAt: new Date('2024-07-17T09:30:00Z').toISOString(),
    category: 'Technology',
    tags: ['sk-hynix', 'ai', 'semiconductors', 'investment'],
    sentiment: 0.8,
    relevanceScore: 0.95,
    mentionedCompanies: [],
    detectedRisks: [],
    language: 'en',
    imageUrl: 'https://example.com/images/sk-hynix-chips.jpg',
  },
];

export const newsResolvers = {
  Query: {
    newsArticle: (_: any, { id }: { id: string }, _context: Context) => {
      return mockNewsArticles.find(article => article.id === id) || null;
    },
    
    newsArticles: (_: any, { filter, sort, limit = 50, offset = 0 }: any, _context: Context) => {
      let filteredArticles = [...mockNewsArticles];
      
      if (filter) {
        if (filter.sources && filter.sources.length > 0) {
          filteredArticles = filteredArticles.filter(a => 
            filter.sources.includes(a.source)
          );
        }
        
        if (filter.categories && filter.categories.length > 0) {
          filteredArticles = filteredArticles.filter(a => 
            filter.categories.includes(a.category)
          );
        }
        
        if (filter.tags && filter.tags.length > 0) {
          filteredArticles = filteredArticles.filter(a => 
            filter.tags.some((tag: string) => a.tags.includes(tag))
          );
        }
        
        if (filter.dateFrom) {
          filteredArticles = filteredArticles.filter(a => 
            new Date(a.publishedAt) >= new Date(filter.dateFrom)
          );
        }
        
        if (filter.dateTo) {
          filteredArticles = filteredArticles.filter(a => 
            new Date(a.publishedAt) <= new Date(filter.dateTo)
          );
        }
        
        if (filter.minRelevanceScore !== undefined) {
          filteredArticles = filteredArticles.filter(a => 
            a.relevanceScore >= filter.minRelevanceScore
          );
        }
        
        if (filter.sentiment) {
          filteredArticles = filteredArticles.filter(a => 
            a.sentiment >= filter.sentiment.min && 
            a.sentiment <= filter.sentiment.max
          );
        }
        
        if (filter.language) {
          filteredArticles = filteredArticles.filter(a => 
            a.language === filter.language
          );
        }
      }
      
      // Sort
      if (sort) {
        filteredArticles.sort((a, b) => {
          switch (sort) {
            case 'PUBLISHED_AT':
              return new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime();
            case 'RELEVANCE_SCORE':
              return b.relevanceScore - a.relevanceScore;
            case 'SENTIMENT':
              return b.sentiment - a.sentiment;
            case 'CRAWLED_AT':
              return new Date(b.crawledAt).getTime() - new Date(a.crawledAt).getTime();
            default:
              return 0;
          }
        });
      }
      
      return filteredArticles.slice(offset, offset + limit);
    },
    
    latestNews: (_: any, { _companyIds, limit = 20 }: any, _context: Context) => {
      // In real app, filter by company mentions
      return mockNewsArticles
        .sort((a, b) => 
          new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
        )
        .slice(0, limit);
    },
    
    newsSources: (_: any, __: any, _context: Context) => {
      return ['Reuters', 'Korea Times', 'TechCrunch', 'Bloomberg', 'Financial Times'];
    },
    
    newsCategories: (_: any, __: any, _context: Context) => {
      return ['Business', 'Technology', 'Industry', 'Finance', 'Politics'];
    },
  },
  
  NewsArticle: {
    mentionedCompanies: (_parent: any, _: any, _context: Context) => {
      // In real app, resolve mentioned companies
      return [];
    },
    
    detectedRisks: (_parent: any, _: any, _context: Context) => {
      // In real app, resolve detected risks
      return [];
    },
  },
};