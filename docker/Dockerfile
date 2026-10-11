# syntax=docker/dockerfile:1

# ---- Stage 1: frontend build (Node only here, never in the final image) ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python dependencies via uv ----
FROM python:3.12-slim AS python-deps
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- Stage 3: runtime ----
FROM python:3.12-slim AS runtime
RUN groupadd -r app && useradd -r -g app -d /app app
WORKDIR /app

COPY --from=python-deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .
COPY --from=frontend /app/frontend/dist ./frontend/dist

# prod settings fail fast without these, so collectstatic gets throwaway
# values that exist only for this build step. Code stays root-owned and
# read-only for the runtime user; only the two upload dirs are writable.
RUN DJANGO_SECRET_KEY=collectstatic-only ALLOWED_HOSTS=localhost \
    CSRF_TRUSTED_ORIGINS=https://localhost \
    python manage.py collectstatic --noinput --settings=config.settings.prod \
    && mkdir -p /app/media /app/private_media \
    && chown -R app:app /app/media /app/private_media \
    && chmod 700 /app/private_media

USER app

# Sends the canonical Host and Caddy's X-Forwarded-Proto, so host validation
# and the HTTPS redirect don't fail the probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request as u; h=os.environ['ALLOWED_HOSTS'].split(',')[0]; u.urlopen(u.Request('http://127.0.0.1:8000/healthz/', headers={'Host': h, 'X-Forwarded-Proto': 'https'}), timeout=4)"

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
