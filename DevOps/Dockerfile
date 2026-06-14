# MT5 REST API Bridge — Railway / Production
# Lightweight FastAPI bridge — no Wine, no MT5 desktop binaries required.
# Local Wine build (requires mt5/terminal/): use Dockerfile.mt5-wine

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0

WORKDIR /app

# ── Dependencies ─────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir "fastapi[standard]>=0.115.0" "uvicorn[standard]>=0.30.0"

# ── Application code ─────────────────────────────────────────────────────────
COPY scripts/mt5_rest.py ./scripts/
COPY pages/api/mt5_bridge.py ./pages/api/
COPY frontend/ ./frontend/

RUN mkdir -p /app/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

EXPOSE 8080

CMD ["python", "scripts/mt5_rest.py"]
