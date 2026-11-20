import pytest

from app.core.rate_limit import RateLimiter
from tests.conftest import NO_AUTH


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_limiter_allows_up_to_limit_then_reports_wait():
    clock = FakeClock()
    limiter = RateLimiter(clock=clock)

    results = [limiter.hit("k", limit=3, window=60) for _ in range(4)]

    assert results[:3] == [None, None, None]
    assert results[3] == 60  # seconds until the oldest hit leaves the window


def test_limiter_window_slides():
    clock = FakeClock()
    limiter = RateLimiter(clock=clock)
    for _ in range(3):
        limiter.hit("k", limit=3, window=60)

    clock.now += 61

    assert limiter.hit("k", limit=3, window=60) is None


def test_keys_are_independent():
    limiter = RateLimiter(clock=FakeClock())
    limiter.hit("a", limit=1, window=60)

    assert limiter.hit("b", limit=1, window=60) is None


def login(client, email, password="wrong-password"):
    return client.post(
        "/auth/login", data={"username": email, "password": password}, headers=NO_AUTH
    )


def test_login_is_limited_per_email(client):
    for _ in range(5):
        assert login(client, "victim@example.com").status_code == 401

    blocked = login(client, "victim@example.com")

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
    assert blocked.json()["detail"] == "Too many attempts, try again later"
    assert login(client, "someone-else@example.com").status_code == 401  # other email fine


def test_login_is_limited_per_ip(client):
    statuses = [login(client, f"user{i}@example.com").status_code for i in range(21)]

    assert statuses[:20] == [401] * 20
    assert statuses[20] == 429


def test_register_is_limited_per_ip(client):
    def register(i):
        return client.post(
            "/auth/register",
            json={"email": f"new{i}@example.com", "password": "long-enough-1", "full_name": "N"},
            headers=NO_AUTH,
        )

    statuses = [register(i).status_code for i in range(11)]

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429


@pytest.mark.parametrize("path", ["/medicines", "/health"])
def test_other_routes_are_not_limited(client, path):
    assert all(client.get(path).status_code == 200 for _ in range(30))
