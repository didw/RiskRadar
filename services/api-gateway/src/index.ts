import express from 'express';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { ApolloServerPluginLandingPageLocalDefault } from '@apollo/server/plugin/landingPage/default';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { WebSocketServer } from 'ws';
// WebSocket setup will be done dynamically inside the function
import http from 'http';
import cors from 'cors';
import helmet from 'helmet';
import bodyParser from 'body-parser';

import { config } from './config/index.js';
import logger from './utils/logger.js';
import { typeDefs } from './graphql/schema/index.js';
import { resolvers } from './graphql/resolvers/index.js';
import { authMiddleware } from './middleware/auth.js';
import { errorHandler } from './middleware/error.js';
import { formatError } from './utils/errors.js';
import { startMockDataGenerator } from './graphql/resolvers/subscription.js';
import { createLoaders } from './graphql/dataloaders/index.js';
import { graphServiceClient } from './services/graph.client.js';
import { mlServiceClient } from './services/ml.client.js';

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

  // Create GraphQL schema for WebSocket
  const schema = makeExecutableSchema({
    typeDefs,
    resolvers,
  });

  // Create WebSocket server
  const wsServer = new WebSocketServer({
    server: httpServer,
    path: '/graphql',
  });

  // Configure GraphQL WebSocket server (dynamic import)
  let useServer: any;
  try {
    // @ts-ignore - temporary fix for ES module resolution
    const wsModule = await import('graphql-ws/use/ws');
    useServer = wsModule.useServer;
  } catch (error) {
    logger.error('Failed to load WebSocket server:', error);
    throw error;
  }
  const serverCleanup = useServer(
    {
      schema,
      context: async (ctx: any, msg: any, args: any) => {
        // WebSocket 인증 처리
        const token = ctx.connectionParams?.authorization?.replace('Bearer ', '');
        let user = null;
        
        if (token) {
          try {
            const jwt = await import('jsonwebtoken');
            const payload = jwt.default.verify(token, config.auth.jwtSecret) as any;
            user = { id: payload.userId, email: payload.email, role: payload.role };
          } catch (error) {
            logger.warn('WebSocket authentication failed:', error);
          }
        }

        return {
          user,
          loaders: createLoaders(),
          services: {
            graph: graphServiceClient,
            ml: mlServiceClient,
          },
        };
      },
      onConnect: async (ctx: any) => {
        logger.info('WebSocket client connected');
        return true;
      },
      onDisconnect: (ctx: any) => {
        logger.info('WebSocket client disconnected');
      },
    },
    wsServer
  );

  // Create Apollo Server (HTTP only)
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    plugins: [
      ApolloServerPluginDrainHttpServer({ httpServer }),
      ApolloServerPluginLandingPageLocalDefault({ embed: true }),
      // WebSocket cleanup plugin
      {
        async serverWillStart() {
          return {
            async drainServer() {
              await serverCleanup.dispose();
            },
          };
        },
      },
    ],
    formatError,
  });

  await server.start();

  // Apply middleware
  app.use(
    '/graphql',
    cors({
      origin: config.cors.origin,
      credentials: true,
    }),
    bodyParser.json(),
    authMiddleware,
    expressMiddleware(server, {
      context: async ({ req }) => {
        const { createLoaders } = await import('./graphql/dataloaders/index.js');
        const { graphServiceClient } = await import('./services/graph.client.js');
        const { mlServiceClient } = await import('./services/ml.client.js');
        
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

  // Start Mock data generator for testing
  if (config.env === 'development') {
    startMockDataGenerator();
    logger.info('Mock data generator started for development');
  }

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