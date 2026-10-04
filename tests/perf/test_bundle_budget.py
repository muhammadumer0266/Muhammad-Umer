"""Bundle-size budgets for the frontend.

These measure the raw source files directly with a plain gzip pass. That is
an honest proxy, not a real production measurement: the actual build (M9)
compiles CSS with Tailwind and tree-shakes/minifies JS with esbuild, which
would only shrink these numbers further. There is currently no Node/esbuild
pipeline available to produce that real build in this environment (see
docs/adr/0002-plain-css-instead-of-tailwind-for-now.md and
docs/TODO_OWNER.md) -- treat these as a floor check against regressions,
not a substitute for a real Lighthouse/CI bundle report.
"""

import gzip
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent.parent / "static"

# Bundle budget for the 3D chunk: 180 KB gzip maximum.
STAGE_CHUNK_FILES = [
    "js/vendor/three.module.min.js",
    "js/stage.js",
    "js/audio.js",
]
STAGE_CHUNK_BUDGET_BYTES = 180 * 1024

# Initial HTML plus critical CSS plus JS excluding
# the 3D chunk: 100 KB gzip or lower."
CRITICAL_PATH_FILES = [
    "css/app.css",
    "js/htmx.min.js",
    "js/main.js",
    "js/tilt.js",
    "js/reveal.js",
]
CRITICAL_PATH_BUDGET_BYTES = 100 * 1024


def _gzip_size(paths: list[str]) -> int:
    raw = b"".join((STATIC / p).read_bytes() for p in paths)
    return len(gzip.compress(raw, compresslevel=9))


def test_3d_chunk_stays_within_gzip_budget():
    size = _gzip_size(STAGE_CHUNK_FILES)
    assert size <= STAGE_CHUNK_BUDGET_BYTES, (
        f"3D chunk is {size / 1024:.1f} KB gzip, budget is "
        f"{STAGE_CHUNK_BUDGET_BYTES / 1024:.0f} KB"
    )


def test_critical_path_stays_within_gzip_budget():
    size = _gzip_size(CRITICAL_PATH_FILES)
    assert size <= CRITICAL_PATH_BUDGET_BYTES, (
        f"Critical path is {size / 1024:.1f} KB gzip, budget is "
        f"{CRITICAL_PATH_BUDGET_BYTES / 1024:.0f} KB"
    )
