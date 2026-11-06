# syntax=docker/dockerfile:1

# ---- Build stage: type-check + production bundle --------------------------
FROM node:20-alpine AS build
WORKDIR /app

# package-lock.json is optional (glob) so the build also works before a lockfile is committed.
# Commit one: it makes installs reproducible and lets `npm ci` run.
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

COPY . .
# `npm run build` = tsc -b && vite build
RUN npm run build

# ---- Runtime stage: nginx serving the static bundle -----------------------
FROM nginx:1.27-alpine AS runtime

# The official nginx image runs envsubst over /etc/nginx/templates/*.template at start-up.
ENV BACKEND_UPSTREAM=http://backend:8000
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/healthz >/dev/null || exit 1
