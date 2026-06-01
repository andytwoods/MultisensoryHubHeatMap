import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

User = get_user_model()

@pytest.fixture
def staff_client(db):
    username_field = User.USERNAME_FIELD
    if username_field == "email":
        kwargs = {"email": "staff@example.com", "password": "pass"}
    else:
        kwargs = {"username": "staff", "password": "pass"}
    if hasattr(User, "multisensory_admin"):
        kwargs["multisensory_admin"] = True
    user = User.objects.create_user(**kwargs)
    perm = Permission.objects.get(codename="view_dashboard")
    user.user_permissions.add(perm)
    client = Client()
    client.force_login(user)
    return client

@pytest.fixture
def anon_client():
    return Client()

@pytest.mark.django_db
def test_dashboard_requires_login(anon_client):
    resp = anon_client.get(reverse("concept_analytics_dashboard"))
    assert resp.status_code != 200  # must not be publicly accessible

@pytest.mark.django_db
def test_dashboard_accessible_to_staff(staff_client):
    resp = staff_client.get(reverse("concept_analytics_dashboard"))
    assert resp.status_code == 200

@pytest.mark.django_db
def test_dashboard_contains_title(staff_client):
    resp = staff_client.get(reverse("concept_analytics_dashboard"))
    assert b"Concept Analytics" in resp.content

@pytest.mark.django_db
def test_dashboard_metric_toggle(staff_client):
    resp = staff_client.get(reverse("concept_analytics_dashboard") + "?metric=total_visible_seconds")
    assert resp.status_code == 200
