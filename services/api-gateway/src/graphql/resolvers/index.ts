import { companyResolvers } from './company';
import { riskResolvers } from './risk';
import { userResolvers } from './user';
import { newsResolvers } from './news';
import { Loaders } from '../dataloaders';
import { graphServiceClient } from '../../services/graph.client';
import { mlServiceClient } from '../../services/ml.client';

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