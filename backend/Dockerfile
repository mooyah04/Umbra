FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: psycopg3 needs libpq; curl for healthcheck.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY bootstrap_db.py .
COPY scripts ./scripts
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Non-root user for security.
RUN useradd --create-home --shell /usr/sbin/nologin umbra \
 && chown -R umbra:umbra /app
USER umbra

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
# Bind :: (dual-stack), not 0.0.0.0. Railway's private network — which the
# deploy healthcheck probes over — is IPv6-only; an IPv4-only socket passes
# public ingress but fails the internal healthcheck. On Linux dual-stack
# (bindv6only=0) :: still accepts IPv4-mapped connections, so localhost/127.x
# healthchecks and public traffic keep working.
CMD ["uvicorn", "app.main:app", "--host", "::", "--port", "8000"]
