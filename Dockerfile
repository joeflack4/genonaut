# Genonaut Production Dockerfile
# This single image can run all three services (API, Celery, Image Gen Mock)
# The service type is determined by the command override in ECS task definitions

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# gcc and build-essential are needed for some Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package in editable mode so genonaut.* imports work
# This makes the genonaut package available on PYTHONPATH
RUN pip install -e .

# Expose ports
# 8001 - API service
# 8189 - Image generation mock service
# Celery worker doesn't need exposed ports
EXPOSE 8001 8189

# Default command (will be overridden by ECS task definitions)
# This is mainly for local testing
CMD ["python", "-m", "genonaut.cli_main", "--help"]
