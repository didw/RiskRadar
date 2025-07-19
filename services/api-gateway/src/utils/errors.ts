import { GraphQLError } from 'graphql';

export enum ErrorCode {
  // Authentication & Authorization
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  FORBIDDEN = 'FORBIDDEN',
  
  // Input Validation
  INVALID_INPUT = 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  
  // Resource Management
  NOT_FOUND = 'NOT_FOUND',
  ALREADY_EXISTS = 'ALREADY_EXISTS',
  
  // External Services
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
  
  // Rate Limiting
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // Internal Errors
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
}

export class CustomError extends GraphQLError {
  constructor(
    message: string,
    code: ErrorCode,
    extensions?: Record<string, any>
  ) {
    super(message, {
      extensions: {
        code,
        timestamp: new Date().toISOString(),
        ...extensions,
      },
    });
  }
}

export class AuthenticationError extends CustomError {
  constructor(message = 'Authentication required') {
    super(message, ErrorCode.UNAUTHENTICATED);
  }
}

export class ForbiddenError extends CustomError {
  constructor(message = 'Insufficient permissions') {
    super(message, ErrorCode.FORBIDDEN);
  }
}

export class ValidationError extends CustomError {
  constructor(message: string, field?: string) {
    super(message, ErrorCode.INVALID_INPUT, { field });
  }
}

export class NotFoundError extends CustomError {
  constructor(resource: string, identifier?: string) {
    const message = identifier 
      ? `${resource} with identifier "${identifier}" not found`
      : `${resource} not found`;
    super(message, ErrorCode.NOT_FOUND, { resource, identifier });
  }
}

export class ServiceUnavailableError extends CustomError {
  constructor(service: string, details?: string) {
    const message = `${service} service is currently unavailable`;
    super(message, ErrorCode.SERVICE_UNAVAILABLE, { service, details });
  }
}

export class ExternalAPIError extends CustomError {
  constructor(api: string, status?: number, details?: string) {
    const message = `External API error from ${api}${status ? ` (${status})` : ''}`;
    super(message, ErrorCode.EXTERNAL_API_ERROR, { api, status, details });
  }
}

export class RateLimitError extends CustomError {
  constructor(limit: number, window: string) {
    super(
      `Rate limit exceeded: ${limit} requests per ${window}`,
      ErrorCode.RATE_LIMIT_EXCEEDED,
      { limit, window }
    );
  }
}

// Error formatting for production
export const formatError = (error: GraphQLError) => {
  // Log all errors for monitoring
  console.error('GraphQL Error:', {
    message: error.message,
    code: error.extensions?.code,
    path: error.path,
    timestamp: error.extensions?.timestamp,
    ...(process.env.NODE_ENV !== 'production' && { stack: error.stack }),
  });

  // In production, hide internal error details
  if (process.env.NODE_ENV === 'production') {
    // Only expose safe error codes
    const safeCodes = [
      ErrorCode.UNAUTHENTICATED,
      ErrorCode.FORBIDDEN,
      ErrorCode.INVALID_INPUT,
      ErrorCode.MISSING_REQUIRED_FIELD,
      ErrorCode.NOT_FOUND,
      ErrorCode.ALREADY_EXISTS,
      ErrorCode.RATE_LIMIT_EXCEEDED,
    ];

    const code = error.extensions?.code as ErrorCode;
    if (!safeCodes.includes(code)) {
      return new CustomError(
        'An internal error occurred',
        ErrorCode.INTERNAL_ERROR
      );
    }
  }

  return error;
};

// Utility functions for error handling
export const throwIfNotFound = <T>(
  item: T | null | undefined,
  resource: string,
  identifier?: string
): T => {
  if (!item) {
    throw new NotFoundError(resource, identifier);
  }
  return item;
};

export const throwIfNotAuthenticated = (user: any) => {
  if (!user) {
    throw new AuthenticationError();
  }
};

export const throwIfNotAuthorized = (condition: boolean, message?: string) => {
  if (!condition) {
    throw new ForbiddenError(message);
  }
};

export const validateInput = (condition: boolean, message: string, field?: string) => {
  if (!condition) {
    throw new ValidationError(message, field);
  }
};

// Service availability checker
export const checkServiceAvailability = async (
  serviceName: string,
  healthCheck: () => Promise<boolean>
): Promise<void> => {
  try {
    const isHealthy = await healthCheck();
    if (!isHealthy) {
      throw new ServiceUnavailableError(serviceName);
    }
  } catch (error) {
    if (error instanceof CustomError) {
      throw error;
    }
    throw new ServiceUnavailableError(serviceName, (error as Error).message);
  }
};

// Retry mechanism with exponential backoff
export const withRetry = async <T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> => {
  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        break;
      }

      // Exponential backoff: 1s, 2s, 4s, etc.
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
};