# ADR 0001: Core stack choices

Date: 2026-09-30
Status: Accepted

## Context

This is a solo-maintained personal portfolio that must also serve as a
demonstration of production-grade Django engineering. It needs a small
retrieval-augmented Q&A demo, a 3D visual identity, strong SEO, and a
deployment path the owner can run and afford alone.

## Decisions

1. **Django 5.2 (current LTS) over a newer non-LTS release.** LTS gives
   security-patch coverage through 2028, which matters more here than early
   access to new Django features. Re-verify against djangoproject.com before
   upgrading.
2. **PostgreSQL + pgvector over a dedicated vector database (Pinecone,
   Weaviate, etc.).** One database to operate and back up; the corpus is
   small (one person's portfolio content), so a dedicated vector DB is
   unjustified operational overhead.
3. **Django templates + HTMX over a SPA framework.** Progressive enhancement
   is a hard project rule; server-rendered HTML with
   HTMX partials satisfies it directly, a client-side SPA would fight it.
4. **Deploy target: VPS + Docker Compose + Caddy**, decided with the owner
   2026-09-30, over a managed platform (Fly.io/Railway/Render). Full control
   over Celery/pgvector and predictable cost at this scale; the tradeoff is
   the owner manages the box (documented in `docs/RUNBOOK.md`).
5. **AI provider left undecided at project start** (owner call, 2026-09-30).
   The RAG pipeline (M7) is built against a `FakeProvider` behind a provider
   interface (`apps/ai/providers/`) so no milestone is blocked and no cost is
   incurred until a real provider is chosen.
6. **Domain left unset at project start.** Everything reads the canonical
   host from `SITE_URL`, so buying a domain later is a config change, not a
   code change.

## Consequences

- Postgres is required for pgvector even in environments that would
  otherwise be fine with SQLite; SQLite remains allowed only for a first
   quick local run, never for CI or prod.
- Swapping AI providers later means adding one adapter class, not touching
  call sites.
