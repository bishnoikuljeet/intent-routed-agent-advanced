FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and README
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir -e .

# Copy application
COPY app ./app
COPY main.py .
COPY data ./data

# Create directories
RUN mkdir -p /app/logs/sessions /app/logs/system /app/data/sessions

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
