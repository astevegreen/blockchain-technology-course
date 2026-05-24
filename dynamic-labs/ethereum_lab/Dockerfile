# Ethereum Immersive Trainer - Docker Image
# Supports two modes: instructor (full blockchain node) and student (frontend only)

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Copy lab docs tree so they're served under /docs/... and displayed in GUI
COPY docs/ ./public/docs/

# Build frontend for production
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH
RUN npm run build

# ============================================
# Stage 2: Build CLI Labs
# ============================================
FROM node:20-alpine AS cli-builder

WORKDIR /app/scripts/cli-labs/standalone

# Copy CLI labs package files
COPY scripts/cli-labs/standalone/package*.json ./
RUN npm ci --only=production

# ============================================
# Stage 3: Production Image
# ============================================
# Use Debian slim instead of Alpine: node-pty has known issues with Alpine (musl libc).
# Debian/glibc provides reliable PTY support for the Lab Terminal in Docker.
FROM node:20-slim

LABEL maintainer="Ethereum Immersive Trainer"
LABEL description="Interactive blockchain training environment"

WORKDIR /app

# Keep Hardhat's compiler cache in a shared image path so runtime shells do
# not need network access to pull compiler metadata or binaries.
ENV HARDHAT_USER_HOME=/opt/hardhat-user-home

# Install curl for health checks, bash for scripts, build deps for node-pty, nginx for in-container routing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash python3 make g++ nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy blockchain dependencies (needed for instructor mode)
# Use --ignore-scripts to skip postinstall (frontend is built separately)
COPY package*.json ./
RUN npm ci --ignore-scripts \
 && npm rebuild node-pty \
 && apt-get purge -y --auto-remove make g++ \
 && rm -rf /var/lib/apt/lists/*

# Copy blockchain contracts and scripts
COPY contracts/ ./contracts/
COPY scripts/ ./scripts/
COPY server/ ./server/
COPY hardhat.config.js ./
# Reuse the repo's checked-in Hardhat outputs so runtime startup doesn't need
# to compile the whole project before the node becomes ready.
COPY artifacts/ ./artifacts/
COPY cache/ ./cache/
# PoS ABI for Hardhat console / example scripts (image has no frontend/src)
COPY frontend/src/PoS.json ./abi/PoS.json

# Pre-download the Solidity compiler so students can compile offline
RUN mkdir -p "${HARDHAT_USER_HOME}" \
 && npx hardhat compile \
 && chmod -R a+rX "${HARDHAT_USER_HOME}"

# Copy CLI labs with pre-installed dependencies
COPY --from=cli-builder /app/scripts/cli-labs/standalone/node_modules ./scripts/cli-labs/standalone/node_modules

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure all app files are world-readable (git checkout umask can produce 600)
RUN chmod -R a+rX /app/

# Create directories for runtime data
RUN usermod -l student -d /home/student -m node \
 && groupmod -n student node \
 && mkdir -p /app/data /app/contracts/student /app/frontend/public /app/frontend/dist/api \
 && mkdir -p /opt/student-home-seed/workspace /opt/student-home-seed/.cache /opt/student-home-seed/.config /opt/student-home-seed/.local/share \
 && cp package*.json hardhat.config.js /opt/student-home-seed/workspace/ \
 && cp -a contracts scripts abi artifacts cache /opt/student-home-seed/workspace/ \
 && cp -a /root/.cache/hardhat-nodejs /opt/student-home-seed/.cache/hardhat-nodejs \
 && cp -a /root/.config/hardhat-nodejs /opt/student-home-seed/.config/hardhat-nodejs \
 && cp -a /root/.local/share/hardhat-nodejs /opt/student-home-seed/.local/share/hardhat-nodejs \
 && rm -rf /opt/student-home-seed/workspace/scripts/cli-labs/standalone/node_modules \
 && ln -s /app/scripts/cli-labs/standalone/node_modules /opt/student-home-seed/workspace/scripts/cli-labs/standalone/node_modules \
 && ln -s /app/node_modules /opt/student-home-seed/workspace/node_modules \
 && mkdir -p /opt/student-home-seed/workspace/frontend/public /opt/student-home-seed/workspace/frontend/src/contracts /opt/student-home-seed/workspace/frontend/dist/api \
 && cp -a /opt/student-home-seed/. /home/student/ \
 && printf 'cd ~/workspace\n' >> /opt/student-home-seed/.bashrc \
 && printf 'cd ~/workspace\n' >> /home/student/.bashrc \
 && chown -R student:student /home/student /opt/student-home-seed

# Copy startup scripts and configs
COPY docker-entrypoint.sh /usr/local/bin/
COPY nginx-internal.conf /etc/nginx/nginx-internal.conf
COPY instructor-config.json student-config.json ./
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && chmod 755 /usr/local/bin/docker-entrypoint.sh

# Environment variables
ENV MODE=instructor
ENV RPC_PORT=8545
ENV FRONTEND_PORT=5173
ENV CONTRACT_ADDRESS=""
ENV INSTRUCTOR_RPC_URL=""

# Expose ports: 8080 (nginx when NGINX_ENABLED=1), 8545 5173 3002-3004 (direct when nginx disabled)
EXPOSE 8080 8545 5173 3002 3003 3004

# Health check - checks frontend (or nginx when NGINX_ENABLED=1)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${HEALTHCHECK_PORT:-5173}/ || exit 1

ENTRYPOINT ["bash", "/usr/local/bin/docker-entrypoint.sh"]
