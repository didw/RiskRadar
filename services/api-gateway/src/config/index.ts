import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '8004', 10),
  env: process.env.NODE_ENV || 'development',
  
  services: {
    graphServiceUrl: process.env.GRAPH_SERVICE_URL || 'http://localhost:8003',
    mlServiceUrl: process.env.ML_SERVICE_URL || 'http://localhost:8002',
    dataServiceUrl: process.env.DATA_SERVICE_URL || 'http://localhost:8001',
  },
  
  auth: {
    jwtSecret: process.env.JWT_SECRET || 'default-secret-key',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '7d',
    jwtRefreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '30d',
  },
  
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
  },
  
  logging: {
    level: process.env.LOG_LEVEL || 'info',
  },
  
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  },
  
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10), // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
  },
};