from pathlib import Path

from django.conf import settings


def test_dashboard_never_uses_no_referrer():
    """Regression: <meta name="referrer" content="no-referrer"> makes browsers
    send `Origin: null` on POSTs, which Django's CSRF check rejects -- the
    login form silently 403'd in a real browser while the test client (which
    sends no Origin) passed."""
    for template in (Path(settings.BASE_DIR) / "templates" / "dashboard").glob("*.html"):
        assert 'content="no-referrer"' not in template.read_text(encoding="utf-8"), template.name
