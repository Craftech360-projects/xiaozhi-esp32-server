# Dockerfile for MQTT Gateway Node.js service
FROM node:18-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies for native modules
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    libasound2-dev \
    libasound2 \
    alsa-utils \
    libopus-dev \
    libopus0 \
    libpulse-dev \
    libpulse0 \
    && ldconfig \
    && ln -sf /usr/lib/x86_64-linux-gnu/libasound.so.2 /usr/lib/libasound.so.2 \
    && rm -rf /var/lib/apt/lists/*

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Set environment variables for correct platform detection
ENV LIBC=gnu
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Install dependencies
RUN npm install --production

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p logs config

# Create a startup script
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'echo "Starting MQTT Gateway..."' >> /docker-entrypoint.sh && \
    echo 'echo "MQTT Broker: $MQTT_BROKER_URL"' >> /docker-entrypoint.sh && \
    echo 'echo "LiveKit URL: $LIVEKIT_URL"' >> /docker-entrypoint.sh && \
    echo 'ldconfig' >> /docker-entrypoint.sh && \
    echo 'node app.js' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8004/health', (res) => process.exit(res.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))" || exit 1

# Start the service
CMD ["/docker-entrypoint.sh"]