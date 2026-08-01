from __future__ import annotations

import socket

import pytest

from recipe_grabber import fetcher
from recipe_grabber.errors import FetchError
from recipe_grabber.fetcher import ensure_public_destination, fetch_html, normalize_url

PUBLIC_IP = "93.184.216.34"


@pytest.fixture(autouse=True)
def clear_robots_cache():
    fetcher._ROBOTS.clear()
    yield
    fetcher._ROBOTS.clear()


def resolver_for(address: str):
    def resolve(host: str, port: int, *, type: int):
        return [(socket.AF_INET, type, socket.IPPROTO_TCP, "", (address, port))]

    return resolve


class StubResponse:
    def __init__(self, status_code=200, headers=None, body=b"", url="") -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.content = body
        self.url = url
        self.encoding = "utf-8"

    @property
    def text(self) -> str:
        return self.content.decode()

    def iter_content(self, chunk_size: int = 8192):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]

    def close(self) -> None:
        pass


class StubSession:
    """Answers robots.txt from `robots`, everything else from `pages`."""

    def __init__(self, robots: str = "", pages: dict | None = None, robots_status: int = 200):
        self.robots = robots
        self.robots_status = robots_status
        self.pages = pages or {}
        self.requested: list[str] = []

    def get(self, url: str, **kwargs) -> StubResponse:
        self.requested.append(url)
        if url.endswith("/robots.txt"):
            return StubResponse(self.robots_status, {}, self.robots.encode(), url)
        return self.pages.get(url) or StubResponse(404, {}, b"", url)

    def close(self) -> None:
        pass


def html_page(url: str, body: bytes = b"<html><h1>Soup</h1></html>") -> StubResponse:
    return StubResponse(200, {"content-type": "text/html; charset=utf-8"}, body, url)


def test_normalize_url_accepts_bare_www_and_removes_fragments() -> None:
    assert normalize_url("www.example.com/recipe#ingredients") == "https://www.example.com/recipe"


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.8", "169.254.169.254", "192.168.1.2"])
def test_private_destinations_are_blocked(address: str) -> None:
    with pytest.raises(FetchError, match="public internet address"):
        ensure_public_destination("https://example.test/recipe", resolver=resolver_for(address))


def test_fetch_html_reads_a_public_html_response() -> None:
    url = "https://example.test/soup"
    session = StubSession(pages={url: html_page(url)})

    html, final_url = fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert "Soup" in html
    assert final_url == url


def test_fetch_html_caps_response_size() -> None:
    url = "https://example.test/large"
    session = StubSession(pages={url: html_page(url, b"x" * 32)})

    with pytest.raises(FetchError, match="too large"):
        fetch_html(url, max_bytes=16, resolver=resolver_for(PUBLIC_IP), session=session)


def test_redirect_is_followed_to_the_final_page() -> None:
    start, final = "https://example.test/start", "https://example.test/final"
    session = StubSession(
        pages={
            start: StubResponse(302, {"location": "/final"}, b"", start),
            final: html_page(final),
        }
    )

    html, final_url = fetch_html(start, resolver=resolver_for(PUBLIC_IP), session=session)

    assert "Soup" in html
    assert final_url == final


def test_redirect_without_a_location_is_rejected() -> None:
    url = "https://example.test/start"
    session = StubSession(pages={url: StubResponse(302, {}, b"", url)})

    with pytest.raises(FetchError, match="invalid redirect"):
        fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)


def test_redirect_chain_is_capped() -> None:
    class Redirecting(StubSession):
        def get(self, url: str, **kwargs) -> StubResponse:
            if url.endswith("/robots.txt"):
                return StubResponse(200, {}, b"", url)
            self.requested.append(url)
            return StubResponse(302, {"location": f"/hop{len(self.requested)}"}, b"", url)

    session = Redirecting()

    with pytest.raises(FetchError, match="redirected too many times"):
        fetch_html("https://example.test/start", resolver=resolver_for(PUBLIC_IP), session=session)

    assert len(session.requested) == fetcher.MAX_REDIRECTS + 1


def test_robots_disallow_blocks_the_fetch() -> None:
    url = "https://example.test/private/recipe"
    session = StubSession(
        robots="User-agent: *\nDisallow: /private/",
        pages={url: html_page(url)},
    )

    with pytest.raises(FetchError, match=r"robots\.txt") as caught:
        fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert caught.value.code == "blocked_by_robots"
    assert not any("/private/recipe" in requested for requested in session.requested)


def test_robots_allow_permits_an_unlisted_path() -> None:
    url = "https://example.test/recipe/soup"
    session = StubSession(
        robots="User-agent: *\nDisallow: /private/",
        pages={url: html_page(url)},
    )

    html, _ = fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert "Soup" in html


def test_robots_missing_is_treated_as_allow_all() -> None:
    url = "https://example.test/recipe/soup"
    session = StubSession(robots_status=404, pages={url: html_page(url)})

    html, _ = fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert "Soup" in html


def test_robots_server_error_refuses_to_guess() -> None:
    url = "https://example.test/recipe/soup"
    session = StubSession(robots_status=503, pages={url: html_page(url)})

    with pytest.raises(FetchError, match=r"robots\.txt could not be read") as caught:
        fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert caught.value.code == "robots_unavailable"


def test_robots_is_fetched_once_per_origin() -> None:
    url = "https://example.test/recipe/soup"
    session = StubSession(pages={url: html_page(url)})

    fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)
    fetch_html(url, resolver=resolver_for(PUBLIC_IP), session=session)

    assert session.requested.count("https://example.test/robots.txt") == 1
