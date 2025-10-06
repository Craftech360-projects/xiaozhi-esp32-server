# Development/Production Dockerfile for Vue.js manager-web
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Create a startup script to handle environment variables
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'echo "Starting Vue.js development server..."' >> /docker-entrypoint.sh && \
    echo 'echo "API Base URL: $VUE_APP_API_BASE_URL"' >> /docker-entrypoint.sh && \
    echo 'npm run serve -- --host 0.0.0.0 --port 8002' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8002/ || exit 1

# Start the development server
CMD ["/docker-entrypoint.sh"]