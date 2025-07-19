import { companyResolvers } from './company.js';
import { riskResolvers } from './risk.js';
import { userResolvers } from './user.js';
import { newsResolvers } from './news.js';
import { Loaders } from '../dataloaders/index.js';
import { graphServiceClient } from '../../services/graph.client.js';
import { mlServiceClient } from '../../services/ml.client.js';

export interface Context {
  user?: {
    id: string;
    email: string;
    role: string;
  };
  loaders: Loaders;
  services: {
    graph: typeof graphServiceClient;
    ml: typeof mlServiceClient;
  };
}

const baseResolvers = {
  Query: {
    _empty: () => 'empty',
  },
  Mutation: {
    _empty: () => 'empty',
  },
  Subscription: {
    _empty: {
      subscribe: () => {
        throw new Error('Subscriptions not implemented yet');
      },
    },
  },
};

export const resolvers = [
  baseResolvers,
  companyResolvers,
  riskResolvers,
  userResolvers,
  newsResolvers,
];