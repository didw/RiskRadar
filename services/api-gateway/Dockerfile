# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Install all dependencies (including dev)
COPY package*.json ./
RUN npm ci

# Copy TypeScript config and source code
COPY tsconfig.json ./
COPY src ./src

# Build TypeScript
RUN npm run build

# Verify build output
RUN ls -la dist/

# Copy GraphQL schema files to dist
RUN mkdir -p dist/graphql/schema && \
    cp -r src/graphql/schema/*.graphql dist/graphql/schema/

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install production dependencies only
COPY package*.json ./
RUN npm ci --production

# Copy built application from builder stage
COPY --from=builder /app/dist ./dist

# Verify the files are copied
RUN ls -la dist/

# Set environment variables
ENV NODE_ENV=production
ENV PORT=8004

EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8004/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

CMD ["node", "dist/index.js"]