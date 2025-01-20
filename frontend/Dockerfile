# Build stage
FROM node:18-slim AS build

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy workspace config
COPY pnpm-workspace.yaml package.json ./

# Copy shared package first
COPY shared /app/shared/

# Copy frontend files
COPY frontend /app/frontend/

# Install dependencies
WORKDIR /app/frontend
RUN pnpm install

# Set environment variables for the build
ENV VITE_CONFIG_API_URL=http://localhost:8001
ENV VITE_PROCESS_API_URL=http://localhost:8003
ENV VITE_COMMUNICATION_API_URL=http://localhost:8002
ENV VITE_DATA_COLLECTION_API_URL=http://localhost:8004

# Build the application
RUN pnpm build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Add nginx config for SPA routing with CORS
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    \
    location / { \
        root /usr/share/nginx/html; \
        try_files $uri $uri/ /index.html; \
        \
        # CORS headers \
        add_header Access-Control-Allow-Origin "*"; \
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"; \
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"; \
        add_header Access-Control-Expose-Headers "Content-Length,Content-Range"; \
        \
        # Handle preflight requests \
        if ($request_method = "OPTIONS") { \
            add_header Access-Control-Allow-Origin "*"; \
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"; \
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"; \
            add_header Access-Control-Max-Age 1728000; \
            add_header Content-Type "text/plain charset=UTF-8"; \
            add_header Content-Length 0; \
            return 204; \
        } \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1 