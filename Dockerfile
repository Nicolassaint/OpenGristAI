# ============================================================================
# OpenGristAI - Production Dockerfile
# ============================================================================
# Combines backend (FastAPI) and frontend (SvelteKit) in a single image
# ============================================================================

# ============================================================================
# Stage 1: Build Frontend
# ============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend dependencies
COPY frontend/package*.json ./
COPY frontend/svelte.config.js ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./
COPY frontend/tailwind.config.ts ./
COPY frontend/postcss.config.js ./

# Install dependencies
RUN npm ci

# Install adapter-static for production build
RUN npm install -D @sveltejs/adapter-static

# Copy frontend source
COPY frontend/src ./src
COPY frontend/static ./static

# Create .env file for build (relative path since frontend is served by backend)
RUN echo "PUBLIC_CHAT_URL=/api/v1/chat" > .env

# Build frontend for production
RUN npm run build

# ============================================================================
# Stage 2: Backend Base (for dev & prod)
# ============================================================================
FROM python:3.10-slim AS backend-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ============================================================================
# Stage 3: Development (for docker-compose)
# ============================================================================
FROM backend-base AS backend-dev

# Copy backend application (volumes will override in docker-compose)
COPY backend/app ./app

# Expose port
EXPOSE 8000

# Development command (will be overridden in docker-compose)
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# Stage 4: Production (default - combined backend + frontend)
# ============================================================================
FROM backend-base AS production

# Copy backend application
COPY backend/app ./app

# Copy frontend build from first stage
COPY --from=frontend-builder /frontend/build ./static

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

