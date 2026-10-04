# Runbook

Operational procedures for running this site. Written for the VPS +
Docker Compose + Caddy deployment target (decided 2026-09-30). Commands
assume you're in the repo root on the server, with `.env` populated from
`.env.example`.

## Deploy

1. `git pull` (or check out the tag being released).
2. `docker compose build web worker beat`
3. `docker compose run --rm web python manage.py migrate`
4. `docker compose up -d`
5. Smoke test: `curl -f https://<domain>/healthz/` should return
   `{"status": "ok", "database": true}`.

A tagged release (`vX.Y.Z`) is meant to trigger this automatically via
`.github/workflows/deploy.yml` once a real server and its SSH/deploy
credentials exist (not yet configured -- see `docs/TODO_OWNER.md`).

## Rollback

1. `git checkout <previous-tag>`
2. `docker compose build web worker beat`
3. `docker compose run --rm web python manage.py migrate` (only if the
   previous tag's migrations differ -- check `git log` on
   `*/migrations/*` between the tags first; never blindly roll a
   migration backward without checking it's safe)
4. `docker compose up -d`
5. Re-run the `/healthz/` smoke test.

## Restore from backup

**Not yet drilled end-to-end** -- there is no production database to
restore from yet. Procedure, once backups exist:

1. Stop the app: `docker compose stop web worker beat`
2. Restore: `gunzip -c backup.sql.gz | docker compose exec -T db psql -U portfolio portfolio`
3. Run `docker compose run --rm web python manage.py migrate` in case
   the backup predates the currently-deployed migrations.
4. `docker compose up -d`
5. Verify `/healthz/` and spot-check `/admin/` for the expected content.

**TODO(owner):** set up the nightly `pg_dump` cron job to encrypted
off-server storage and run one real restore drill
before launch, then update this section with what actually happened.

## Rotate secrets

1. Generate a new value (e.g. `DJANGO_SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(50))"`).
2. Update `.env` on the server (never commit it).
3. `docker compose up -d` to restart with the new value.
4. Rotating `DJANGO_SECRET_KEY` invalidates all existing sessions --
   users are logged out, which is expected and fine for a low-traffic
   personal site.

## Renew DNS / TLS

Caddy (see `docker/Caddyfile`) renews Let's Encrypt certificates
automatically -- no manual TLS renewal should be needed. If DNS changes
(new registrar, new records): update the A/AAAA records at the
registrar, then restart Caddy (`docker compose restart caddy`) so it
picks up the new domain if `SITE_DOMAIN` changed.

## Add a project through the admin

1. Log into `/<ADMIN_URL>/` (non-default path, see `.env`).
2. Portfolio > Entries > Add entry.
3. Fill in `kind=project`, `date` (any day in the month -- it's
   normalized to the 1st on save), `summary`, and `body_md` if it should
   get its own case-study page.
4. Leave `is_published` unchecked until ready; check `featured` for at
   most a few entries (home page shows all featured ones).
5. Once published with real content, run `reindex_rag` (below) so the
   Ask feature can find it.

## Re-index the Ask corpus

```
docker compose exec web python manage.py reindex_rag
```

Idempotent -- skips documents whose content hash hasn't changed. Run
after publishing or editing any entry with `body_md`, or the profile bio.

## Import and export entries

```
docker compose exec web python manage.py export_entries /tmp/entries.json
docker compose exec web python manage.py import_entries /tmp/entries.json
```

Both are idempotent (upsert by slug). See the import command documentation for the
JSON shape.

## Rebuild OG images

**Not built yet** -- see `docs/TODO_OWNER.md` and `docs/SEO.md`. Pages
currently have no `og:image`.

## Update Three.js safely

The self-hosted vendor file (`static/js/vendor/three.module.min.js`) was
downloaded directly (no npm/esbuild pipeline in the sandbox that built
M4 -- see `docs/adr/0003`... actually see the M4 commit and
`docs/TODO_OWNER.md`'s bundle-size entry). To update it:

1. Download the new minified ES module build from a trusted source
   (`https://unpkg.com/three@<version>/build/three.module.min.js`),
   replacing the vendored file.
2. Check the CSP comment in `config/settings/base.py` still applies --
   if a new three.js version fixes the internal canvas
   `.style.display` mutation that currently requires `style-src
   'unsafe-inline'`, remove that exception and tighten the policy.
3. Re-run `tests/perf/test_bundle_budget.py` (180 KB gzip budget for
   the 3D chunk) and the manual browser smoke test (load the home page,
   check the console for errors, confirm the orb renders).
4. If esbuild/Node becomes available, switch to a tree-shaken build
   importing only the specific three.js modules used (see
   `docs/TODO_OWNER.md`) instead of the full vendored file.

## Manual accessibility pass

No automated axe-core/Playwright accessibility suite exists yet (no
browser automation was reliably available in the sandbox that built
M2-M4 -- ad hoc Playwright checks were used instead, see commit
history). Before launch, manually verify on the built site:

- Tab through every page with a keyboard only: skip link works, focus
  order is logical, every interactive control (nav links, filter chips,
  sound toggle, forms) is reachable and has a visible focus ring.
- Turn on a screen reader (VoiceOver/NVDA) and confirm headings,
  landmarks and form labels are announced sensibly.
- Set `prefers-reduced-motion: reduce` in the OS and confirm the 3D
  scene slows/stops appropriately and scroll-reveal shows content
  immediately.
