### Stage 1: Build ###
FROM node:22-slim AS builder

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy lockfile and manifest first for layer caching
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY . .
# VITE_API_BASE_URL is baked into the static bundle at build time.
# Default is /api (nginx proxies it to the backend on the same origin).
# Override with --build-arg VITE_API_BASE_URL=http://host:8000/api for
# deployments where the frontend and backend are on different origins.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN pnpm build

### Stage 2: Serve ###
FROM nginx:alpine AS serve

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx:alpine's entrypoint runs envsubst on *.template files in /etc/nginx/templates/
# at startup, writing the result to /etc/nginx/conf.d/ — no custom entrypoint needed.
# BACKEND_URL defaults to the Docker Compose service name; override at runtime with
# -e BACKEND_URL=http://192.168.1.x:8000 for non-Compose deployments.
ENV BACKEND_URL=http://backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
