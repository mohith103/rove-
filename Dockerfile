# ROVE Backend — FastAPI + simulation + RL agents
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps — install first to cache this layer
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install "fastapi>=0.110.0" "uvicorn[standard]>=0.29.0" "httpx>=0.27.0" "websockets>=12.0" && \
    pip install "torch>=2.2.0" --index-url https://download.pytorch.org/whl/cpu && \
    pip install "stable-baselines3>=2.2.0" "tensorboard>=2.15.0"

# Copy source
COPY backend/ ./backend/
COPY simulation/ ./simulation/
COPY agents/ ./agents/
COPY reinforcement_learning/ ./reinforcement_learning/
COPY experiments/ ./experiments/
COPY configs/ ./configs/
COPY tests/ ./tests/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
