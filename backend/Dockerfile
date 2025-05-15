# Use a more robust base image with build tools pre-installed
FROM python:3.9

# Set environment variables for Python optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# Copy application code
COPY . .

# Install Uvicorn explicitly (needed for FastAPI with Gunicorn)
RUN pip install uvicorn

# Verify critical dependencies
RUN python -c "import gunicorn, uvicorn" && \
    which gunicorn

# Run as non-root user for security
RUN useradd -u 1001 -m appuser && \
    chown -R appuser:appuser /app
USER 1001

# Use Uvicorn workers for FastAPI
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "app:app"]