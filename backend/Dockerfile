# PhotoBooth Backend Dockerfile
# Multi-stage build to minimize final image size

# ─────────────────────────────────────────────────────────────────
# Stage 1: Builder - compile native extensions
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install system dependencies (including build tools for pycups, psutil)
# Install build dependencies (gcc, python3-dev for pycups/psutil)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libcups2-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to /install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────
# Stage 2: Runtime - minimal image without gcc
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies only (no gcc/python3-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcups2 \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /data/storage/photos /data/storage/composites /data/storage/thumbnails /data/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
