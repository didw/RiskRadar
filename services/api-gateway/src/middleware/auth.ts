import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config/index.js';
import logger from '../utils/logger.js';

export interface AuthRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
  };
}

export const authMiddleware = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader) {
      // No auth header, continue without user context
      return next();
    }
    
    const token = authHeader.replace('Bearer ', '');
    
    if (!token) {
      return next();
    }
    
    try {
      const decoded = jwt.verify(token, config.auth.jwtSecret) as any;
      
      req.user = {
        id: decoded.userId,
        email: decoded.email,
        role: decoded.role,
      };
      
      logger.debug('User authenticated:', req.user.email);
    } catch (error) {
      logger.debug('Invalid token:', error);
      // Invalid token, continue without user context
    }
    
    next();
  } catch (error) {
    logger.error('Auth middleware error:', error);
    next(error);
  }
};