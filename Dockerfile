FROM python:3.11-slim

WORKDIR /app

# Dépendances d'abord pour profiter du cache Docker
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# Code source
COPY app ./app

# Dossier persistant pour la base SQLite (monté comme volume sur Railway)
RUN mkdir -p /data

EXPOSE 8000

# $PORT est injecté par Railway — fallback 8000 en local
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
