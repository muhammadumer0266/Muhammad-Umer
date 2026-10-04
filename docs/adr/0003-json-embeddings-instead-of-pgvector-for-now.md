# ADR 0003: JSON-stored embeddings and Python cosine similarity instead of pgvector, for now

Date: 2026-09-30
Status: Accepted (revisit once Postgres+pgvector is available)

## Context

The original project brief specifies PostgreSQL with the pgvector
extension for `RagChunk.embedding`, with an HNSW or IVFFlat index and a
pgvector cosine-distance query for retrieval. Building M7 in this dev
sandbox, there is no running Postgres instance and no way to start one:
Docker is installed but its daemon is not reachable (`docker ps` fails to
connect to the Docker Desktop engine), and there is no other Postgres
available. The owner was asked directly (2026-09-30) and chose to proceed
with a fallback now rather than block M7 entirely or skip it.

## Decision

`RagChunk.embedding` is a `JSONField` storing a plain list of floats.
Retrieval (`apps/ai/retrieval.py`) fetches all chunks and computes cosine
similarity in Python, sorting for the top-k above a similarity threshold.
This runs on SQLite (dev/test here) and Postgres alike, with no
Postgres-specific extension required.

At the scale this site actually has -- one person's portfolio content,
realistically a few hundred chunks at most -- a full Python scan is not a
real performance problem. It only becomes one at a scale this project will
never reach without also needing a much bigger rethink than pgvector alone.

## Consequences

- Nothing in the retrieval *behavior* differs from the pgvector design:
  same cosine-similarity ranking, same top-k, same threshold logic. Only
  where the similarity math runs (Python vs. the database) changes.
- `FakeProvider.embed()` (`apps/ai/providers/fake.py`) uses a small
  feature-hashing bag-of-words vectorizer specifically so that cosine
  similarity between fake embeddings still correlates with real lexical
  overlap -- this keeps retrieval tests and the golden eval set
  (`tests/ai/golden.yaml`) meaningful without needing a real embedding
  model or a paid API key.
- **Before scale ever became a real concern, or once Postgres+pgvector is
  actually available** (e.g. `docker compose up db` once Docker Desktop's
  engine is running): swap `RagChunk.embedding` to pgvector's `VectorField`,
  add the HNSW/IVFFlat index, and replace the Python cosine-similarity scan
  in `apps/ai/retrieval.py` with a pgvector `<=>` query. The chunking,
  provider interface, generation, safety and budget logic are all
  independent of this and do not need to change. Tracked in
  `docs/TODO_OWNER.md`.
