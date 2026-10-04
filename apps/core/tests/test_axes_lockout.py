import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_admin_locks_out_after_repeated_failed_logins(client, django_user_model, settings):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="correct-horse-battery-staple"
    )
    login_url = reverse("admin:login")

    for _ in range(settings.AXES_FAILURE_LIMIT - 1):
        response = client.post(login_url, {"username": "admin", "password": "wrong"})
        assert response.status_code == 200  # re-shows the login form

    # This attempt reaches the failure limit itself, so axes locks out
    # immediately rather than re-showing the form one more time.
    final_failure_response = client.post(login_url, {"username": "admin", "password": "wrong"})
    assert final_failure_response.status_code == 429

    # Even the correct password is now rejected -- axes is blocking by
    # ip_address/username, not just counting bad passwords.
    locked_out_response = client.post(
        login_url, {"username": "admin", "password": "correct-horse-battery-staple"}
    )
    assert locked_out_response.status_code == 429


@pytest.mark.django_db
def test_admin_login_succeeds_under_the_failure_limit(client, django_user_model, settings):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="correct-horse-battery-staple"
    )
    login_url = reverse("admin:login")

    for _ in range(settings.AXES_FAILURE_LIMIT - 1):
        client.post(login_url, {"username": "admin", "password": "wrong"})

    response = client.post(
        login_url, {"username": "admin", "password": "correct-horse-battery-staple"}
    )

    assert response.status_code == 302
