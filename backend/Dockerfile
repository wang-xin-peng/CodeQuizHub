FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir PyJWT passlib[bcrypt] bcrypt \
    fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    pydantic[email] pydantic-settings redis python-multipart \
    slowapi openpyxl docker httpx websockets

COPY . .

# Install docker-entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Run as non-root
RUN groupadd -r app && useradd -r -g app app && \
    chown -R app:app /app
USER app

ENTRYPOINT ["docker-entrypoint.sh"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
