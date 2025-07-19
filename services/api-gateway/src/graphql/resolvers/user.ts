import { Context } from './index.js';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { config } from '../../config/index.js';

const mockUsers = [
  {
    id: 'user-1',
    email: 'admin@riskradar.com',
    name: 'Admin User',
    role: 'ADMIN',
    department: 'Risk Management',
    preferences: {
      emailNotifications: true,
      alertThreshold: 'MEDIUM',
      dashboardLayout: 'default',
      language: 'en',
      timezone: 'Asia/Seoul',
    },
    watchlist: [],
    createdAt: new Date('2024-01-01').toISOString(),
    updatedAt: new Date().toISOString(),
    lastLoginAt: new Date().toISOString(),
    password: '$2a$10$dummyhashedpassword', // In real app, this would be hashed
  },
];

export const userResolvers = {
  Query: {
    me: (_: any, __: any, context: Context) => {
      if (!context.user) {
        return null;
      }
      return mockUsers.find(u => u.id === context.user!.id);
    },
    
    user: (_: any, { id }: { id: string }, _context: Context) => {
      return mockUsers.find(user => user.id === id) || null;
    },
    
    users: (_: any, { role, limit = 50, offset = 0 }: any, _context: Context) => {
      let filteredUsers = [...mockUsers];
      
      if (role) {
        filteredUsers = filteredUsers.filter(u => u.role === role);
      }
      
      return filteredUsers.slice(offset, offset + limit);
    },
    
    dashboard: (_: any, __: any, context: Context) => {
      return {
        id: 'dashboard-1',
        userId: context.user?.id || 'user-1',
        totalCompanies: 125,
        highRiskCompanies: 12,
        recentAlerts: [],
        riskTrends: [
          {
            date: new Date('2024-07-19').toISOString(),
            riskType: 'FINANCIAL',
            count: 15,
            averageSeverity: 3.2,
          },
          {
            date: new Date('2024-07-18').toISOString(),
            riskType: 'OPERATIONAL',
            count: 8,
            averageSeverity: 2.8,
          },
        ],
        topRisks: [],
        watchlistUpdates: [
          {
            company: null,
            updateType: 'RISK_INCREASE',
            description: 'Risk score increased by 15%',
            timestamp: new Date().toISOString(),
          },
        ],
      };
    },
    
    insights: (_: any, { _companyId, _type, limit = 20 }: any, _context: Context) => {
      return [
        {
          id: 'insight-1',
          type: 'RISK_PATTERN',
          title: 'Increasing Financial Risk Pattern Detected',
          description: 'Multiple indicators suggest increasing financial risk over the past 30 days',
          importance: 0.85,
          relatedCompanies: [],
          relatedRisks: [],
          createdAt: new Date().toISOString(),
        },
        {
          id: 'insight-2',
          type: 'CORRELATION',
          title: 'Supply Chain Risk Correlation',
          description: 'Strong correlation detected between semiconductor suppliers and tech manufacturers',
          importance: 0.75,
          relatedCompanies: [],
          relatedRisks: [],
          createdAt: new Date().toISOString(),
        },
      ].slice(0, limit);
    },
  },
  
  Mutation: {
    signUp: async (_: any, { input }: any, _context: Context) => {
      const { email, password, name, department } = input;
      
      // Check if user exists (in real app, check database)
      if (mockUsers.find(u => u.email === email)) {
        throw new Error('User already exists');
      }
      
      // Hash password (in real app)
      const hashedPassword = await bcrypt.hash(password, 10);
      
      const newUser = {
        id: `user-${Date.now()}`,
        email,
        name,
        role: 'VIEWER' as const,
        department,
        preferences: {
          emailNotifications: true,
          alertThreshold: 'MEDIUM' as const,
          dashboardLayout: 'default',
          language: 'en',
          timezone: 'UTC',
        },
        watchlist: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        password: hashedPassword,
      };
      
      mockUsers.push(newUser);
      
      const token = jwt.sign(
        { userId: newUser.id, email: newUser.email, role: newUser.role },
        config.auth.jwtSecret
      );
      
      const refreshToken = jwt.sign(
        { userId: newUser.id, type: 'refresh' },
        config.auth.jwtSecret
      );
      
      return {
        user: newUser,
        token,
        refreshToken,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };
    },
    
    login: async (_: any, { input }: any, _context: Context) => {
      const { email } = input;
      
      const user = mockUsers.find(u => u.email === email);
      if (!user) {
        throw new Error('Invalid credentials');
      }
      
      // In real app, compare hashed passwords
      // const valid = await bcrypt.compare(password, user.password);
      // if (!valid) throw new Error('Invalid credentials');
      
      const token = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        config.auth.jwtSecret
      );
      
      const refreshToken = jwt.sign(
        { userId: user.id, type: 'refresh' },
        config.auth.jwtSecret
      );
      
      return {
        user,
        token,
        refreshToken,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };
    },
    
    logout: (_: any, __: any, _context: Context) => {
      // In real app, invalidate token/session
      return true;
    },
    
    refreshToken: (_: any, { token }: { token: string }, _context: Context) => {
      try {
        const decoded = jwt.verify(token, config.auth.jwtSecret) as any;
        
        if (decoded.type !== 'refresh') {
          throw new Error('Invalid token type');
        }
        
        const user = mockUsers.find(u => u.id === decoded.userId);
        if (!user) {
          throw new Error('User not found');
        }
        
        const newToken = jwt.sign(
          { userId: user.id, email: user.email, role: user.role },
          config.auth.jwtSecret
        );
        
        const newRefreshToken = jwt.sign(
          { userId: user.id, type: 'refresh' },
          config.auth.jwtSecret
        );
        
        return {
          user,
          token: newToken,
          refreshToken: newRefreshToken,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        };
      } catch (error) {
        throw new Error('Invalid refresh token');
      }
    },
    
    updateProfile: (_: any, { name, department }: any, context: Context) => {
      if (!context.user) {
        throw new Error('Not authenticated');
      }
      
      const user = mockUsers.find(u => u.id === context.user!.id);
      if (!user) {
        throw new Error('User not found');
      }
      
      if (name) user.name = name;
      if (department) user.department = department;
      user.updatedAt = new Date().toISOString();
      
      return user;
    },
    
    updatePreferences: (_: any, { input }: any, context: Context) => {
      if (!context.user) {
        throw new Error('Not authenticated');
      }
      
      const user = mockUsers.find(u => u.id === context.user!.id);
      if (!user) {
        throw new Error('User not found');
      }
      
      user.preferences = { ...user.preferences, ...input };
      user.updatedAt = new Date().toISOString();
      
      return user;
    },
    
    addToWatchlist: (_: any, { companyId: _companyId }: { companyId: string }, context: Context) => {
      if (!context.user) {
        throw new Error('Not authenticated');
      }
      
      const user = mockUsers.find(u => u.id === context.user!.id);
      if (!user) {
        throw new Error('User not found');
      }
      
      // In real app, add company to watchlist
      user.updatedAt = new Date().toISOString();
      
      return user;
    },
    
    removeFromWatchlist: (_: any, { companyId: _companyId }: { companyId: string }, context: Context) => {
      if (!context.user) {
        throw new Error('Not authenticated');
      }
      
      const user = mockUsers.find(u => u.id === context.user!.id);
      if (!user) {
        throw new Error('User not found');
      }
      
      // In real app, remove company from watchlist
      user.updatedAt = new Date().toISOString();
      
      return user;
    },
    
    subscribeToAlerts: (_: any, { companyIds, alertTypes }: any, context: Context) => {
      if (!context.user) {
        throw new Error('Not authenticated');
      }
      
      return {
        id: `sub-${Date.now()}`,
        userId: context.user.id,
        companyIds,
        alertTypes,
        active: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    },
  },
};