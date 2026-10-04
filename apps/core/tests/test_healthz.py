from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_returns_200_and_ok_status(client):
    response = client.get(reverse("core:healthz"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True}


@pytest.mark.django_db
def test_healthz_requires_no_auth(client):
    response = client.get(reverse("core:healthz"))

    assert "WWW-Authenticate" not in response.headers


@pytest.mark.django_db
def test_healthz_returns_503_when_database_unavailable(client):
    with patch("apps.core.views.connections") as mock_connections:
        mock_connections.__getitem__.return_value.cursor.side_effect = OperationalError
        response = client.get(reverse("core:healthz"))

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": False}
