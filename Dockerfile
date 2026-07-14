# Multi-stage build for smaller image size with explicit platform support
FROM --platform=linux/amd64 python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM --platform=linux/amd64 python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/home/appuser/.local/bin:$PATH

# Set work directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy project files
COPY --chown=appuser:appuser . .

# Create directories for uploads and data
RUN mkdir -p /app/uploads /app/data /app/logs /app/tiktoken_cache \
    && chown -R appuser:appuser /app

USER appuser

# Expose port (Render overrides this with $PORT env var)
EXPOSE 8000

# Health check (uses PORT env var; default 8000)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application — scripts/render_start.sh handles migrations first
CMD ["/bin/bash", "/app/scripts/render_start.sh"]
