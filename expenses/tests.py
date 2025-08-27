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


@pytest.mark.django_db
def test_participant_name_trim_and_not_empty(client):
    """Trims whitespace and rejects empty participant name."""
    # login and create event
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]

    # whitespace name -> should be trimmed
    r = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "  Karel  ", "email": "k@example.com"}),
        content_type="application/json",
    )
    assert r.status_code in (200, 201)
    assert r.json()["name"] == "Karel"

    # empty/whitespace only -> 400
    r2 = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "   ", "email": "x@example.com"}),
        content_type="application/json",
    )
    assert r2.status_code == 400
    body = r2.json()
    # Either field-specific or non-field errors depending on form binding
    assert ("name" in body) or ("non_field_errors" in body)


@pytest.mark.django_db
def test_participant_unique_name_per_event(client):
    """Same name cannot be added twice within the same event, but can in different events."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200

    # Create two events
    r1 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip A", "description": "X"}),
        content_type="application/json",
    )
    r2 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip B", "description": "Y"}),
        content_type="application/json",
    )
    e1, e2 = r1.json()["id"], r2.json()["id"]

    # Add Karel twice to event A -> second should fail with 400
    ok = client.post(
        reverse("event-add-participant", args=[e1]),
        data=json.dumps({"name": "Karel", "email": "k1@example.com"}),
        content_type="application/json",
    )
    assert ok.status_code in (200, 201)
    dup = client.post(
        reverse("event-add-participant", args=[e1]),
        data=json.dumps({"name": "Karel", "email": "k2@example.com"}),
        content_type="application/json",
    )
    assert dup.status_code == 400

    # But adding Karel to event B is OK
    ok2 = client.post(
        reverse("event-add-participant", args=[e2]),
        data=json.dumps({"name": "Karel", "email": "k3@example.com"}),
        content_type="application/json",
    )
    assert ok2.status_code in (200, 201)


@pytest.mark.django_db
def test_expense_amount_must_be_positive(client):
    """Expense amount must be > 0 (model + serializer + DB check)."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200

    # Event + participants
    r_event = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "Trip", "description": "X"}),
        content_type="application/json",
    )
    event_id = r_event.json()["id"]
    pa = client.post(
        reverse("event-add-participant", args=[event_id]),
        data=json.dumps({"name": "A", "email": "a@example.com"}),
        content_type="application/json",
    ).json()

    # amount = 0 -> 400
    r0 = client.post(
        reverse("expense-list"),
        data=json.dumps({
            "description": "Lunch",
            "amount": 0,
            "event": event_id,
            "payer": pa["id"],
            "split_between_ids": [pa["id"]],
        }),
        content_type="application/json",
    )
    assert r0.status_code == 400
    assert "amount" in r0.json()

    # amount > 0 -> OK
    r_ok = client.post(
        reverse("expense-list"),
        data=json.dumps({
            "description": "Lunch",
            "amount": 123.45,
            "event": event_id,
            "payer": pa["id"],
            "split_between_ids": [pa["id"]],
        }),
        content_type="application/json",
    )
    assert r_ok.status_code in (200, 201)


@pytest.mark.django_db
def test_expense_payer_must_belong_to_event(client):
    """Payer must be a participant of the same event."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200

    # Two events
    e1 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "E1", "description": "X"}),
        content_type="application/json",
    ).json()["id"]
    e2 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "E2", "description": "Y"}),
        content_type="application/json",
    ).json()["id"]

    # Participant in E2 only
    p2 = client.post(
        reverse("event-add-participant", args=[e2]),
        data=json.dumps({"name": "B", "email": "b@example.com"}),
        content_type="application/json",
    ).json()

    # Try to create expense in E1 with payer from E2 -> 400
    r = client.post(
        reverse("expense-list"),
        data=json.dumps({
            "description": "Bad payer",
            "amount": 10,
            "event": e1,
            "payer": p2["id"],
            "split_between_ids": [],
        }),
        content_type="application/json",
    )
    assert r.status_code == 400
    body = r.json()
    assert "payer" in body


@pytest.mark.django_db
def test_expense_split_between_must_belong_to_event(client):
    """All split participants must belong to the same event as the expense."""
    User.objects.create_user("luke", password="secret")
    assert jpost(client, "api_login", {"username": "luke", "password": "secret"}).status_code == 200

    # Two events with one participant each
    e1 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "E1", "description": "X"}),
        content_type="application/json",
    ).json()["id"]
    e2 = client.post(
        reverse("event-list"),
        data=json.dumps({"title": "E2", "description": "Y"}),
        content_type="application/json",
    ).json()["id"]

    p1 = client.post(
        reverse("event-add-participant", args=[e1]),
        data=json.dumps({"name": "A", "email": "a@example.com"}),
        content_type="application/json",
    ).json()
    p2 = client.post(
        reverse("event-add-participant", args=[e2]),
        data=json.dumps({"name": "B", "email": "b@example.com"}),
        content_type="application/json",
    ).json()

    # Try to create expense in E1 split between A (ok) and B (wrong event) -> 400
    r = client.post(
        reverse("expense-list"),
        data=json.dumps({
            "description": "Split cross-event",
            "amount": 10,
            "event": e1,
            "payer": p1["id"],
            "split_between_ids": [p1["id"], p2["id"]],
        }),
        content_type="application/json",
    )
    assert r.status_code == 400
    body = r.json()
    # We expect the serializer/view to expose `split_between_ids`
    assert "split_between_ids" in body


@pytest.mark.django_db
def test_api_404_returns_json(client):
    """Unknown API path returns JSON error with handler404."""
    r = client.get("/api/this-endpoint-does-not-exist")
    assert r.status_code == 404
    data = r.json()
    assert data.get("status") == 404
    assert data.get("detail") == "Nenalezeno"
