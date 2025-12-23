# ============================================
# Multi-stage Dockerfile for Chatbot Tiles v2
# Stage 1: Builder - Install dependencies and build
# Stage 2: Runtime - Minimal image with only runtime dependencies
# ============================================

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY docker/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.10-slim as runtime

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security (before copying files)
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder stage to user's home
COPY --from=builder /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY app/ ./app/

# Set working directory to app
WORKDIR /app

# Change ownership to appuser
RUN chown -R appuser:appuser /app /home/appuser/.local

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application using uvicorn
CMD ["uvicorn", "app.src.bootstrap.main:app", "--host", "0.0.0.0", "--port", "8080"]

