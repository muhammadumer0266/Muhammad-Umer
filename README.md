# Muhammad Umer — portfolio

Personal site for Muhammad Umer, Django developer and AI engineer:
production-grade Django, a retrieval-augmented "Ask" demo, and a
self-hosted Three.js scene, all server-rendered and readable with
JavaScript disabled. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how a request flows
through the system.

## Requirements

- Python 3.12+, [`uv`](https://docs.astral.sh/uv/)
- Docker + Docker Compose (for Postgres/pgvector, Redis, and the full stack)
- Node 20+ (build stage only — never required at runtime)

## Quickstart

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Visit `http://localhost:8000/healthz/`. SQLite is fine for this first run;
everything else (CI, tests that touch `apps.ai`, production) uses Postgres
with pgvector — bring it up with:

```bash
docker compose up db redis
```

## Common tasks

| Command | Does |
|---|---|
| `make dev` | migrate + run the dev server |
| `make test` | run the test suite with coverage |
| `make lint` | Ruff, djlint, mypy |
| `make fmt` | auto-fix lint/format issues |
| `make seed` | load `fixtures/sample_entries.json` |
| `make e2e` | Playwright end-to-end tests |

## Project status

16. Placeholder content is never invented; anything unknown is tracked in
[`docs/TODO_OWNER.md`](docs/TODO_OWNER.md) and visibly labeled "Sample" in
the UI.
