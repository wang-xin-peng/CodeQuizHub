FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir redis asyncpg docker

COPY . .

CMD ["python", "judge_worker.py"]
