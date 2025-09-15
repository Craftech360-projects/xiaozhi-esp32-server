# Node.js MQTT Gateway Docker Image
FROM node:18-alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Create app user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -G appgroup -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --no-audit --no-fund

# Copy application files
COPY . .

# Create config directory if it doesn't exist
RUN mkdir -p config

# Change ownership of the app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 1883 8884

# Environment variables with defaults
ENV NODE_ENV=production
ENV DEBUG=""
ENV MQTT_PORT=1883
ENV UDP_PORT=8884

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8884/health || exit 1

# Start the application
CMD ["node", "app.js"]