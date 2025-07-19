import express from 'express';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { ApolloServerPluginLandingPageLocalDefault } from '@apollo/server/plugin/landingPage/default';
import http from 'http';
import cors from 'cors';
import helmet from 'helmet';
import { json } from 'body-parser';

import { config } from './config';
import logger from './utils/logger';
import { typeDefs } from './graphql/schema';
import { resolvers } from './graphql/resolvers';
import { authMiddleware } from './middleware/auth';
import { errorHandler } from './middleware/error';

async function startServer() {
  const app = express();
  const httpServer = http.createServer(app);

  // Security middleware
  app.use(helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        scriptSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"],
      },
    },
  }));

  // Health check endpoint
  app.get('/health', (_req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      service: 'api-gateway',
      version: '0.1.0',
    });
  });

  // Create Apollo Server
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    plugins: [
      ApolloServerPluginDrainHttpServer({ httpServer }),
      ApolloServerPluginLandingPageLocalDefault({ embed: true }),
    ],
    formatError: (err) => {
      const { formatError } = require('./utils/errors');
      return formatError(err);
    },
  });

  await server.start();

  // Apply middleware
  app.use(
    '/graphql',
    cors({
      origin: config.cors.origin,
      credentials: true,
    }),
    json(),
    authMiddleware,
    expressMiddleware(server, {
      context: async ({ req }) => {
        const { createLoaders } = await import('./graphql/dataloaders');
        const { graphServiceClient } = await import('./services/graph.client');
        const { mlServiceClient } = await import('./services/ml.client');
        
        return {
          user: (req as any).user,
          loaders: createLoaders(),
          services: {
            graph: graphServiceClient,
            ml: mlServiceClient,
          },
        };
      },
    })
  );

  // Error handling
  app.use(errorHandler);

  // Start server
  httpServer.listen(config.port, () => {
    logger.info(`🚀 Server ready at http://localhost:${config.port}/graphql`);
    logger.info(`📊 Health check at http://localhost:${config.port}/health`);
  });
}

// Start the server
startServer().catch((err) => {
  logger.error('Failed to start server:', err);
  process.exit(1);
});