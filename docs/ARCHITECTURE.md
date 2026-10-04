# Architecture

## Settings strategy

`config/settings/base.py` holds everything environment-independent. `dev.py`,
`test.py` and `prod.py` each import `base` and override only what must differ.
`prod.py` calls `env.str(...)`/`env.list(...)` **without** a default for
anything required, so a missing var fails fast at startup instead of silently
running with an insecure default.

## App boundaries

- `apps.core` — base templates, middleware, `/healthz/`, error pages, shared
  utilities. Depends on nothing else in `apps.*`.
- `apps.portfolio` — Profile, SocialLink, Entry, Tag, SkillGroup, Skill.
- `apps.blog` — Post, feed, tag pages.
- `apps.contact` — ContactMessage, form, spam controls, email tasks.
- `apps.ai` — RAG pipeline: chunking, embeddings, retrieval, generation, eval.
- `apps.seo` — meta context processor, JSON-LD builders, sitemaps, robots,
  `llms.txt`, OG images, IndexNow.
- `apps.api` — read-only DRF API.

Business logic lives in each app's `services.py` (writes) or `selectors.py`
(reads); views stay thin and templates contain no logic.

## How a request travels

```
Visitor
  -> Caddy (TLS termination, HTTP/2/3, gzip/brotli, security headers, www redirect)
    -> Gunicorn -> Django (CanonicalHostMiddleware, CSP, CSRF, session)
      -> apps.* views (thin) -> services/selectors -> PostgreSQL (+ pgvector for Ask)
      -> Celery (Redis broker) for email, embeddings, OG image rendering, IndexNow pings
      -> (Ask only) provider adapter -> Anthropic/OpenAI/Fake, gated by budget + rate limits
  <- Server-rendered HTML (readable with JS disabled) + optional HTMX partial
```

This diagram must stay in sync with the "How a request travels" section on
the site itself (`/about/` or `/`, built in M2/M5) — update both together.

## Why Postgres + pgvector instead of a separate vector DB

One database to operate, back up and restore; `RagChunk.embedding` lives next
to the content it was chunked from, so retrieval joins are plain SQL. See
`docs/adr/0001-stack-choices.md`.
