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

RUN python manage.py collectstatic --noinput --settings=config.settings.prod \
    && chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz/')"

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
