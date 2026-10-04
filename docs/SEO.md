# SEO

## Realistic goal

"Umer" and "Muhammad Umer" are common names. No one can guarantee first
place for a bare common name, and this project never uses spam, hidden
text, link schemes or misleading markup. The achievable goals:

1. Rank first for branded queries: `Muhammad Umer Django developer`,
   `Muhammad Umer AI engineer`, `Muhammad Umer portfolio`,
   `muhammadumer0266`, and the site's own domain.
2. Get indexed within days, with a correct title/description/sitelinks for
   the home page.
3. Connect the site, GitHub profile and other profiles as one entity.
4. Rank for long-tail technical topics through case studies and posts,
   over time.
5. Report real Search Console numbers after launch, not promises.

## What's implemented (`apps/seo`)

- **Identity**: `Person`/`WebSite`/`ProfilePage` JSON-LD (`apps/seo/jsonld.py`),
  present on every page via `{% site_jsonld %}`, all sharing one `@id`.
  `<link rel="me">` for every social link flagged `rel_me=True`.
- **Canonical URLs**: self-referencing, absolute, query-string-stripped on
  every page (`apps/seo/context_processors.py`).
- **Sitemap** (`/sitemap.xml`): home/work/about/contact, published
  non-sample case studies, and tag pages with 2+ published entries.
- **robots.txt**: allows all public paths, disallows the admin path and
  `/api/`/`/ask/`, references the sitemap.
- **llms.txt**: a concise, honest Markdown summary linking the key pages.
- **noindex**: admin and `/api/` carry an `X-Robots-Tag: noindex` header
  (`apps/core/middleware.py`); sample entries carry a `noindex` meta tag.
- **Verification tags**: `GOOGLE_SITE_VERIFICATION`/`BING_SITE_VERIFICATION`
  env vars render meta tags when set.
- **Test suite** (`tests/seo/test_seo_suite.py`): title/description length
  and uniqueness, canonical presence, exactly one `h1`, JSON-LD validity,
  robots.txt/sitemap hygiene, noindex coverage, www/http redirects.

## Deferred (see `docs/TODO_OWNER.md`)

- **OG images**: per-page/per-case-study social images (Pillow + Celery
  task) are not built yet. Pages currently have no `og:image` at all.
- **Blog feed** (`/feed.xml`): the blog app doesn't exist yet (deferred by
  owner decision until there's real content).
- **IndexNow**: not wired up -- pinging it before a real domain exists
  would have nothing to point at.

## Off-site checklist (manual, cannot be automated)

1. Set the GitHub profile "Website" field to the new domain once bought;
   add a link and one factual sentence to the `Muhammad-Umer` profile
   README.
2. Add the site to LinkedIn (Contact info and Featured) and any other
   profile used, with the same name form ("Muhammad Umer").
3. Add the site as the homepage URL on the `xl-diff` repository and in its
   package metadata (`Cargo.toml`, Python package metadata).
4. Verify the domain in Google Search Console and Bing Webmaster Tools,
   submit `sitemap.xml`, request indexing of the home page.
5. Publish 2-3 posts on dev.to/Hashnode with canonical links back to the
   site's own post, once it's republished there.
6. Earn a small number of genuine links: open-source contributions with a
   profile link, talks, community posts. No purchased links.
7. Keep `umerg.pythonanywhere.com` alive only as a redirect once the new
   domain is live (see `docs/RUNBOOK.md`, to be written at M9).
8. Recheck Search Console monthly; adjust titles/content from real queries.
