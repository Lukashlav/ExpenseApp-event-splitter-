"""
Pytest test suite for ExpenseApp.
Covers auth (signup/login/me), event creation, and adding participants.
Each test has a one-line docstring to satisfy the documentation requirement.
"""

import json
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from http.cookies import SimpleCookie


def ensure_csrf(client):
    """Ensure CSRF cookie is set and return its value."""
    client.get(reverse("api_csrf"))
    token = client.cookies.get("csrftoken")
    return token.value if token else None


def jpost_csrf(client, url_name, payload=None, url_kwargs=None):
    """POST JSON with CSRF header; useful when view enforces CSRF."""
    payload = payload or {}
    token = ensure_csrf(client)
    url = reverse(url_name, kwargs=url_kwargs or {})
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        **({"HTTP_X_CSRFTOKEN": token} if token else {})
    )


def login_user(client, username="luke", password="secret"):
    """Create and login a user via API with CSRF; return (username, password)."""
    User.objects.create_user(username, password=password)
    r = jpost_csrf(client, "api_login", {"username": username, "password": password})
    assert r.status_code == 200
    return username, password


def jpost(client, url_name, payload=None, url_kwargs=None):
    """Helper: POST JSON with correct content_type, return response."""
    payload = payload or {}
    url = reverse(url_name, kwargs=url_kwargs or {})
    return client.post(url, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_signup_success(client):
    """Registers a new user successfully via API."""
    r = jpost(client, "api_signup", {"username": "luke", "password": "secret"})
    assert r.status_code in (200, 201)


@pytest.mark.django_db
def test_login_fail_wrong_credentials(client):
    """Rejects login with invalid credentials."""
    # no such user yet
    r = jpost(client, "api_login", {"username": "foo", "password": "bar"})
    assert r.status_code == 401


@pytest.mark.django_db
def test_login_and_me_authenticated_flag(client):
    """Logs in and returns authenticated=True on /api/me/."""
    User.objects.create_user("luke", password="secret")
    r = jpost(client, "api_login", {"username": "luke", "password": "secret"})
    assert r.status_code == 200
    r = client.get(reverse("api_me"))
    assert r.status_code == 200
    assert r.json().get("authenticated") is True


@pytest.mark.django_db
def test_create_event_requires_auth(client):
    """Blocks unauthenticated users from creating events."""
    r = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "Test"}),
        content_type="application/json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_event_ok_when_authenticated(client):
    """Allows authenticated user to create an event and returns its payload."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200
    r = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "Test"}),
        content_type="application/json",
    )
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["title"] == "Trip"
    event_id = data["id"]
    assert isinstance(event_id, int)


@pytest.mark.django_db
def test_add_participant_requires_auth(client):
    """Blocks unauthenticated POST to add_participant action."""
    # create an event via ORM
    owner = User.objects.create_user("luke", password="secret")
    # create event through API to keep serializer shape consistent
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    # logout
    client.post(reverse("api_logout"))
    # try to add participant while unauthenticated
    r = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "Karel", "email": "karel@example.com"}),
        content_type="application/json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_add_participant_ok_when_authenticated(client):
    """Allows authenticated user to add a participant to an event."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    r = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "Karel", "email": "karel@example.com"}),
        content_type="application/json",
    )
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["name"] == "Karel"


@pytest.mark.django_db
def test_signup_missing_fields_returns_400(client):
    """Rejects signup without username/password."""
    r = jpost_csrf(client, "api_signup", {"username": "", "password": ""})
    assert r.status_code == 400


@pytest.mark.django_db
def test_me_unauthenticated(client):
    """Returns authenticated=False for anonymous user."""
    r = client.get(reverse("api_me"))
    assert r.status_code == 200
    assert r.json().get("authenticated") is False


@pytest.mark.django_db
def test_logout_requires_auth(client):
    """Rejects logout when user is not authenticated."""
    r = jpost_csrf(client, "api_logout")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_logout_ok_clears_session(client):
    """Logs out authenticated user and /api/me/ shows authenticated=False."""
    login_user(client)
    r = jpost_csrf(client, "api_logout")
    assert r.status_code == 200
    r = client.get(reverse("api_me"))
    assert r.status_code == 200
    assert r.json().get("authenticated") is False


@pytest.mark.django_db
def test_event_list_public_access(client):
    """Allows public listing of events."""
    r = client.get(reverse("event-list"))
    assert r.status_code == 200


@pytest.mark.django_db
def test_event_retrieve_public_access(client):
    """Allows public retrieval of an event by id."""
    login_user(client)
    r = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r.json()["id"]
    r2 = client.get(reverse("event-detail", args=[event_id]))
    assert r2.status_code == 200


@pytest.mark.django_db
def test_expense_create_requires_auth(client):
    """Blocks unauthenticated users from creating expenses."""
    r = client.post(
        reverse("expense-list"),
        data=json.dumps({"description": "Lunch", "amount": 100}),
        content_type="application/json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_balance_and_settlement_endpoints(client):
    """Computes balance and settlement for a simple case."""
    login_user(client)
    # create event
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    # add two participants
    client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "A", "email": "a@example.com"}),
        content_type="application/json",
    )
    client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "B", "email": "b@example.com"}),
        content_type="application/json",
    )
    # fetch balances & settlements
    r_bal = client.get(reverse("event-balance", args=[event_id]))
    r_set = client.get(reverse("event-settlement", args=[event_id]))
    assert r_bal.status_code == 200
    assert r_set.status_code == 200
    assert isinstance(r_bal.json(), dict)
    assert isinstance(r_set.json(), list)


@pytest.mark.django_db
def test_delete_participant_ok(client):
    """Deletes participant via dedicated endpoint when authenticated."""
    login_user(client)
    # create event
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    # add participant
    r_p = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "Z", "email": "z@example.com"}),
        content_type="application/json",
    )
    participant_id = r_p.json()["id"]
    # delete participant
    r_del = client.delete(reverse("delete_participant", args=[participant_id]))
    assert r_del.status_code == 204


@pytest.mark.django_db
def test_delete_event_ok(client):
    """Deletes event via dedicated endpoint when authenticated."""
    login_user(client)
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    r_del = client.delete(reverse("delete_event", kwargs={"event_id": event_id}))
    assert r_del.status_code == 204
