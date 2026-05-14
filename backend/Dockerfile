FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir -r requirements.txt 2>/dev/null; \
    pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    pydantic[email] pydantic-settings pyjwt passlib[bcrypt] bcrypt redis python-multipart \
    slowapi openpyxl docker httpx websockets

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
