FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Render (e outros PaaS) injetam a porta real via $PORT; localmente cai no 8000.
CMD ["sh", "-c", "RUN_EMBEDDED_SCHEDULER=${RUN_EMBEDDED_SCHEDULER:-true} uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
