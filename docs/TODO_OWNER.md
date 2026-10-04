# Owner TODOs

Facts the site needs that only Muhammad Umer can supply. Nothing below is
guessed or invented — placeholders are marked `TODO(owner)` in code until
these are answered. Answer whenever; only items marked **(blocks M2)** need
answering before the design-system milestone starts writing real page copy.

## Identity & profiles
- [ ] Confirm exact public name form and any alternate name to register as `alternateName` (default assumed: "Muhammad Umer" / "Umer").
- [ ] LinkedIn URL.
- [ ] Any other public profiles (Stack Overflow, dev.to, Hashnode, PyPI, crates.io, X, YouTube).
- [ ] Professional photo (or decide: no photo).
- [ ] Resume PDF.
- [ ] Bio: one-line, one-paragraph, and long versions. **(blocks M2 about/home copy)**

## Work & status
- [ ] 2–4 real projects with: problem, stack, role, real result/metric, live URL, repo URL. `xl-diff` is a candidate — need its real benchmark numbers before any number is published. **(blocks M2/M3 entry content)**
- [ ] Current status: open to work / freelance / both, and any public preferred roles/regions.
- [ ] Should the contact email be shown publicly, or only via the form? (Profile.public_email_visible)

## Domain & deployment
- [x] Deploy target: VPS + Docker Compose + Caddy (decided 2026-09-30).
- [ ] Domain name, once purchased (site is built domain-agnostic via `SITE_URL` until then — decided 2026-09-30).
- [ ] Registrar/DNS provider, once domain is bought.

## AI "Ask" feature
- [ ] LLM + embeddings provider choice and monthly budget cap — undecided as of 2026-09-30. Built against `FakeProvider` until this is answered; no cost incurred either way.

## Content
- [ ] Blog: building the app now, keeping it unlinked/unindexed until real posts exist (decided 2026-09-30). Need 3–5 topic ideas when ready to write.
- [ ] `docs/eval/golden.yaml` questions for the Ask feature evaluation — needs the owner's input on what visitors should be able to ask.

## Tooling
- [ ] Tailwind CLI could not be run in the dev sandbox that built M2 (no Node, no reachable standalone binary). Site currently ships hand-authored plain CSS with the same design tokens instead (`docs/adr/0002-plain-css-instead-of-tailwind-for-now.md`). Confirm before M9 launch: get Tailwind compiling in CI/Docker (Node is available there), or formally drop it from the stack.
- [ ] The 3D scene (M4) ships the full, non-tree-shaken `three.js` build (`static/js/vendor/three.module.min.js`) as a native ES module import, since esbuild wasn't available either. Combined with `stage.js`/`audio.js` this currently measures ~172 KB gzip against the 180 KB budget (`tests/perf/test_bundle_budget.py`) -- it passes, but with very little headroom, and that test gzips the raw source directly rather than a real minified/tree-shaken build. Before M9: build with esbuild importing only the specific three.js modules used (`WebGLRenderer`, `Scene`, `PerspectiveCamera`, `IcosahedronGeometry`, `ShaderMaterial`, `Points`, `BufferGeometry`, `TorusGeometry`, `SphereGeometry`), which should cut this substantially.
- [ ] The 3D scene has been verified with a headless-Chromium smoke test (loads, zero console/page errors, canvas renders, sound toggle works, reduced-motion path works) -- see screenshots taken during M4. What is **not** verified: real mid-range-phone fps, the quality-governor step-down actually triggering under load, or a real Lighthouse score. Report real numbers only once measured on real devices/CI.

## Contact (M6)
- [ ] Production email: `prod.py` uses SMTP (`EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` env vars) but no real SMTP provider is configured yet. Contact-form notifications land in the console backend in dev and are sent for real only once these are set.
- [ ] `DEFAULT_FROM_EMAIL` is Django's default (`webmaster@localhost`) -- set a real sending address once a domain/mailbox exists.

## Hardening & launch (M9)
- [ ] **django-otp admin 2FA is not wired up yet**, despite the project requirements. django-axes (lockout after repeated failed logins) is done and tested. Full TOTP enrollment needs a real owner decision (which authenticator app, backup-codes policy) and, if enforced via `OTPAdminSite`, would need every admin test in the suite reworked to authenticate through a verified OTP device -- rather than half-implement something that could silently disable itself in tests or lock out the real owner, this is flagged for a dedicated pass once you're ready to enroll a device.
- [ ] CSP's `style-src` includes `'unsafe-inline'` (script-src does not, and never should). Root cause and full rationale is a comment on `CONTENT_SECURITY_POLICY` in `config/settings/base.py`: the vendored three.js sets `.style.display` on an internal capability-probe canvas, which CSP treats as inline style. Revisit if a future three.js release fixes this internally.
- [ ] `tests/perf/locustfile.py` (`make loadtest`) is written and mechanically verified against the local dev server only -- **no real load test has been run against a deployed instance.** The single-threaded dev server cannot demonstrate the "50 req/s, p95 < 200ms" target; that needs a real server.
- [ ] Lighthouse CI (`make lhci`) needs Node/Chrome tooling not available in the sandbox that built this -- no Lighthouse score has been measured. Run it against the built Docker image once CI has Node.
- [ ] Backups: no nightly `pg_dump` cron job exists yet (no production Postgres to back up). No restore drill has been run -- `docs/RUNBOOK.md`'s restore section is unverified procedure, not a tested one.
- [ ] `.github/workflows/deploy.yml` is a template with the real deploy steps commented out -- needs `DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_SSH_KEY` (or a registry) as repository secrets once a real server exists.
- [ ] DNS, TLS and the redirect from `umerg.pythonanywhere.com` all need a real domain first (see the Domain decision above).
- [ ] No automated axe-core/accessibility test suite exists (no reliable browser automation for it during M2-M4; ad hoc Playwright checks were used instead for spot verification). `docs/RUNBOOK.md` has a manual keyboard/screen-reader pass to run before launch.

## API (M8)
- [ ] `/api/v1/posts/` isn't built -- waiting on the blog app, same as `/feed.xml` (deferred by owner decision 2026-09-30).

## Ask / RAG (M7)
- [ ] `RagChunk.embedding` is JSON + Python cosine similarity, not pgvector, because Docker's engine wasn't reachable in the dev sandbox that built this (see `docs/adr/0003-json-embeddings-instead-of-pgvector-for-now.md`). Swap to a real pgvector `VectorField` + HNSW/IVFFlat index once Postgres is available -- the chunking/provider/generation/safety/budget logic doesn't need to change.
- [ ] `tests/ai/golden.yaml` only has refusal-correctness cases right now, because sample/placeholder entries are deliberately excluded from the RAG index (so the demo never presents fake content as real) and there's no real content indexed yet. Add "should answer" cases with `expected_title_contains` once real projects/case studies exist, written with the owner.
- [ ] Run `python manage.py reindex_rag` after adding real content, and re-run `make eval` to get a real hit-rate number.
- [ ] `AI_PROVIDER` is still "fake" -- no real LLM/embeddings provider chosen yet (see the AI provider decision above). `apps/ai/providers/get_provider()` raises loudly on any other value, so this can't silently ship broken.

## SEO (M5 follow-ups, see docs/SEO.md)
- [ ] OG image generation (Pillow + Celery task) not built yet -- pages have no `og:image` currently.
- [ ] IndexNow not wired up -- no real domain to ping yet; add once one exists.
- [ ] `/feed.xml` not built -- waiting on the blog app (deferred by owner decision 2026-09-30).

## Analytics
- [ ] Confirm privacy-friendly, cookieless, self-hosted Plausible or Umami (default assumption; no cookie banner needed either way).
