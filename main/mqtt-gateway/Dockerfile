# Node.js MQTT Gateway Docker Image
FROM node:18-alpine AS production

# Install curl (for health checks) and tini (clean PID1 signal handling)
RUN apk add --no-cache curl tini

# Create non-root user/group
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -G appgroup -u 1001

# Workdir
WORKDIR /app

# Copy only package files first for better layer caching
COPY --chown=appuser:appgroup package*.json ./

# Install prod deps
# Use --omit=dev (npm9+) instead of deprecated --only=production
RUN npm ci --omit=dev --no-audit --no-fund

# Copy application source
COPY --chown=appuser:appgroup . .

# (Optional) ensure config dir exists
RUN mkdir -p config

# Switch to non-root
USER appuser

# Environment
ENV NODE_ENV=production
# Expose a clear HTTP port (for health endpoint) separate from MQTT if needed
ENV HTTP_PORT=8884
ENV MQTT_PORT=1883
# If you actually have debug toggles, keep empty by default
ENV DEBUG=""

# Ports:
# - MQTT over TCP (standard): 1883
# - HTTP health endpoint: 8884
EXPOSE 1883/tcp
EXPOSE 8884/tcp

# Health check (HTTP endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${HTTP_PORT}/health" || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Start the app
CMD ["node", "app.js"]
