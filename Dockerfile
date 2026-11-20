# syntax=docker/dockerfile:1
FROM python:3.15-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first so code changes do not invalidate this layer.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Run as an unprivileged user; uploads go to a writable volume.
RUN useradd --create-home --uid 10001 instamed \
    && mkdir -p /app/uploads \
    && chown instamed:instamed /app/uploads
USER instamed

ENV UPLOAD_DIR=/app/uploads
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

# One process per container: rate-limit counters live in memory, so scale with more
# containers behind a load balancer only after moving them to a shared store.
# --proxy-headers trusts X-Forwarded-For only from FORWARDED_ALLOW_IPS (default 127.0.0.1).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
