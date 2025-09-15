# Multi-stage build for Vue.js Manager Web Application
# Use modern Dockerfile syntax if you later enable BuildKit:
# syntax=docker/dockerfile:1.6

# ---- Stage 1: Build ----
FROM node:18-alpine AS build

WORKDIR /app
# Tools sometimes needed by node-gyp; keep minimal
RUN apk add --no-cache python3 make g++ git

# Copy deps first (layer caching)
COPY package*.json ./
# Prefer reproducible installs; legacy-peer-deps kept if you need it
RUN npm ci --legacy-peer-deps

# Copy source
COPY public/ ./public/
COPY src/ ./src/
COPY babel.config.js ./
COPY vue.config.js ./
# If you truly need env files at build time, uncomment next line,
# but avoid shipping secrets into the image:
# COPY .env* ./

# Build-time environment (Vue CLI reads process.env.* at build)
ENV NODE_ENV=production
ENV VUE_APP_USE_CDN=false
ENV VUE_APP_PUBLIC_PATH=/
ENV VUE_APP_API_BASE_URL=/toy
ENV VUE_APP_TITLE=cheeko

# Build
RUN npm run build

# ---- Stage 2: Runtime (Nginx) ----
FROM nginx:1.27-alpine AS production

# Install curl for healthcheck (tiny)
RUN apk add --no-cache curl

# Replace default site config
RUN rm -f /etc/nginx/conf.d/default.conf
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Non-root user (optional; Nginx runs as nginx by default on Alpine)
RUN addgroup -g 1001 -S webgroup \
    && adduser -S webuser -G webgroup -u 1001 \
    && chown -R webuser:webgroup /usr/share/nginx/html
USER webuser

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
