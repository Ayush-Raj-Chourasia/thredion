# Dockerfile for Thredion Engine — Railway Deployment
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY thredion-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY thredion-engine/ .

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ || exit 1

# Expose PORT (will be set by Railway)
EXPOSE ${PORT:-8000}

# Start the application
CMD ["sh", "-c", "gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120"]
