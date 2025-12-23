# Alternative: Use full Python image instead of slim
# If slim version still has issues, use this Dockerfile
FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify basic packages
RUN python -c "import fastapi; import transformers; import numpy; print('✅ Core packages installed successfully')"

# Copy application files
COPY app.py .
COPY model_loader.py .

# Create model directory
RUN mkdir -p /app/models

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 7000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7000/health || exit 1

# Run service
CMD ["python", "app.py"]

