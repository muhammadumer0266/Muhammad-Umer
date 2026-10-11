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
- **robots.txt**: allows all public paths, disallows the dashboard path, `/resume/download/` and
  `/api/`/`/ask/`, references the sitemap.
- **llms.txt**: a concise, honest Markdown summary linking the key pages.
- **noindex**: the dashboard and `/api/` carry an `X-Robots-Tag: noindex` header
  (`apps/core/middleware.py`); sample entries carry a `noindex` meta tag.
- **Verification tags**: `GOOGLE_SITE_VERIFICATION`/`BING_SITE_VERIFICATION`
  env vars render meta tags when set.
- **Test suite** (`tests/seo/test_seo_suite.py`): title/description length
  and uniqueness, canonical presence, exactly one `h1`, JSON-LD validity,
  robots.txt/sitemap hygiene, noindex coverage, www/http redirects.

## Deferred (see `docs/TODO_OWNER.md`)

- **Generated OG images**: per-case-study social cards (Pillow + Celery) are
  not built. Pages use the profile photo (gallery: the first photo) as
  `og:image`.
- **Blog feed** (`/feed.xml`): the blog app doesn't exist yet (deferred by
  owner decision until there's real content).
- **IndexNow**: not wired up -- pinging it before a real domain exists
  would have nothing to point at.

## Go-live for search: muhammadumer.tech

Do these in order once the site is deployed.

1. **DNS at your registrar** (where you bought the .tech domain): add an
   `A` record for `muhammadumer.tech` pointing to the server's IPv4 address
   (plus `AAAA` for IPv6 if you have one), and the same for `www`. Caddy then
   gets the HTTPS certificate on its own; `www` redirects to the bare domain.
2. **Server `.env`**: `SITE_URL=https://muhammadumer.tech`,
   `SITE_DOMAIN=muhammadumer.tech`, `ALLOWED_HOSTS=muhammadumer.tech`,
   `CSRF_TRUSTED_ORIGINS=https://muhammadumer.tech` (see `.env.example`).
3. **Google Search Console** (search.google.com/search-console) → *Add
   property* → **Domain** → `muhammadumer.tech` → it gives you a `TXT` record;
   add it at the registrar and click Verify. (A Domain property covers http,
   https and www at once. The alternative URL-prefix property can be verified
   with the `GOOGLE_SITE_VERIFICATION` env var instead.)
4. In Search Console → **Sitemaps**: submit `sitemap.xml` and
   `sitemap-images.xml`. Then use **URL inspection** on `/`, `/about/` and
   `/photos/` and click *Request indexing*.
5. **Bing Webmaster Tools** (bing.com/webmasters): *Import from Google Search
   Console*. This also covers DuckDuckGo and Yahoo, which use Bing's index.
6. **Dashboard content that drives ranking** (Dashboard → Profile & summary):
   - Profile: exact name, `headline`, `bio_short` (shown as the search
     snippet), `alternate_names` (e.g. `Umer`), and a clear headshot photo.
   - Social links with **rel=me** ticked: GitHub, LinkedIn, etc. These become
     the Person `sameAs` links that tie your profiles into one entity
     (what a Google knowledge panel is built from).
   - **Photos** (Dashboard → Photos): see below.

### Getting your photos into Google Images

- Upload in **Dashboard → Photos**. Give each a real *title* and an
  *alt text* that names you and says what's in it ("Muhammad Umer presenting
  a Django talk at …"). The file is saved as
  `muhammad-umer-<title>-xxxxxx.jpg`, and the photo appears on `/photos/`,
  in the `ImageGallery` structured data (creator, credit and copyright set to
  you) and in `sitemap-images.xml`.
- The **profile photo** is used on Home and About, in link previews
  (Open Graph/Twitter cards) and as the Person `image`. Use the **same photo**
  on LinkedIn, GitHub and other profiles: the same face across linked
  profiles is a strong signal that they are one person.
- Prefer original photos at least 1200px wide; JPG/PNG/WebP, max 5 MB.
- `/media/` images are served indexable and embeddable by search engines;
  résumé and certificate PDFs stay `noindex`.

### Expectations

New domains usually take days to get indexed and weeks to rank. "Muhammad
Umer" is a very common name, so no one can promise position 1 for the bare
name. What moves it: the steps above, the site linked from every profile
you own (GitHub *Website* field, LinkedIn *Contact info*), and real content
(case studies, posts) over time. Watch Search Console → *Performance* for
the queries you actually show up for.

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
