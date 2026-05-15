FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for asyncpg (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy judge worker code
COPY . .

# Use root for Docker socket access (sandbox containers provide isolation)
CMD ["python", "judge_worker.py"]
