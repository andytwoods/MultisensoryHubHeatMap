import pytest
from django.test import Client
from django.contrib.auth.models import User, Permission

@pytest.fixture
def staff_client(db):
    user = User.objects.create_user("staff", password="pass", is_staff=True)
    # Add view_dashboard permission
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
    resp = anon_client.get("/concept-analytics/dashboard/")
    assert resp.status_code == 302  # redirect to login

@pytest.mark.django_db
def test_dashboard_accessible_to_staff(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_dashboard_contains_title(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/")
    assert b"Concept Analytics" in resp.content

@pytest.mark.django_db
def test_dashboard_metric_toggle(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/?metric=total_visible_seconds")
    assert resp.status_code == 200
