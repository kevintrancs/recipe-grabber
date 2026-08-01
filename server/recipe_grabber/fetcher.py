from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from curl_cffi import CurlError, requests

from .errors import FetchError

Resolver = Callable[..., list[tuple]]

TIMEOUT = (5, 12)  # connect, read
MAX_REDIRECTS = 5
REDIRECT_CODES = {301, 302, 303, 307, 308}  # listed out: 304 and 305 are 3xx but not redirects

# Bot management fingerprints the TLS handshake and refuses Python's, so borrow Chrome's.
IMPERSONATE = "chrome"

# We present as Chrome, so we obey the rules written for everyone.
ROBOTS_AGENT = "*"

_ROBOTS_UNAVAILABLE = "That site's robots.txt could not be read, so the recipe was left alone."

# ponytail: no TTL, cached for the process lifetime. Add one if this ever long-runs.
_ROBOTS: dict[str, RobotFileParser] = {}


def normalize_url(value: str) -> str:
    candidate = value.strip()
    if candidate.lower().startswith("www."):
        candidate = f"https://{candidate}"

    parsed = urlsplit(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise FetchError(
            "Only HTTP and HTTPS recipe links are supported.", code="invalid_url", status=400
        )
    if not parsed.hostname or parsed.username or parsed.password:
        raise FetchError("Enter a valid public recipe URL.", code="invalid_url", status=400)

    try:
        port = parsed.port
        host = parsed.hostname.encode("idna").decode("ascii")
    except ValueError as error:  # bad port, or UnicodeError from the idna codec
        raise FetchError(
            "Enter a valid public recipe URL.", code="invalid_url", status=400
        ) from error

    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port else host
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def ensure_public_destination(url: str, *, resolver: Resolver = socket.getaddrinfo) -> str:
    normalized = normalize_url(url)
    parsed = urlsplit(normalized)
    assert parsed.hostname is not None

    default_port = 443 if parsed.scheme == "https" else 80
    try:
        addresses = {
            ipaddress.ip_address(result[4][0])
            for result in resolver(
                parsed.hostname, parsed.port or default_port, type=socket.SOCK_STREAM
            )
        }
    except (OSError, ValueError) as error:
        raise FetchError("The recipe site's address could not be resolved.") from error

    if not addresses or any(not address.is_global for address in addresses):
        raise FetchError(
            "Recipe links must resolve to a public internet address.",
            code="unsafe_url",
            status=400,
        )
    return normalized


def _robots_for(session: Any, origin: str) -> RobotFileParser:
    """Fetch and parse one origin's robots.txt, following RFC 9309 status handling."""
    cached = _ROBOTS.get(origin)
    if cached is not None:
        return cached

    try:
        # No redirects: a redirected robots.txt would escape the SSRF check. The main
        # fetch re-checks robots per hop, so the final origin's rules still get applied.
        response = session.get(f"{origin}/robots.txt", timeout=TIMEOUT, allow_redirects=False)
        if response.status_code >= 500:
            raise FetchError(_ROBOTS_UNAVAILABLE, code="robots_unavailable")
    except (CurlError, OSError) as error:
        raise FetchError(_ROBOTS_UNAVAILABLE, code="robots_unavailable") from error

    rules = RobotFileParser()
    # 4xx and redirects mean "no usable rules", which RFC 9309 treats as allow-all.
    rules.parse(response.text.splitlines() if response.status_code < 300 else [])
    _ROBOTS[origin] = rules
    return rules


def _ensure_robots_allows(session: Any, url: str) -> None:
    parsed = urlsplit(url)
    if not _robots_for(session, f"{parsed.scheme}://{parsed.netloc}").can_fetch(ROBOTS_AGENT, url):
        raise FetchError(
            "That site's robots.txt asks automated tools not to read this page.",
            code="blocked_by_robots",
            status=403,
        )


def fetch_html(
    url: str,
    *,
    max_bytes: int = 2_000_000,
    resolver: Resolver = socket.getaddrinfo,
    session: Any | None = None,
) -> tuple[str, str]:
    owned_session = session is None
    session = session or requests.Session(impersonate=IMPERSONATE)
    current_url = url

    try:
        # Each hop is re-validated, so a redirect cannot smuggle us onto a private
        # address or past a robots.txt rule the first host did not have.
        for _ in range(MAX_REDIRECTS + 1):
            current_url = ensure_public_destination(current_url, resolver=resolver)
            _ensure_robots_allows(session, current_url)

            response = session.get(
                current_url, stream=True, allow_redirects=False, timeout=TIMEOUT
            )
            try:
                if response.status_code in REDIRECT_CODES:
                    location = response.headers.get("location")
                    if not location:
                        raise FetchError("The recipe site returned an invalid redirect.")
                    current_url = urljoin(current_url, location)
                    continue

                if response.status_code >= 400:
                    raise FetchError(
                        f"The recipe site returned HTTP {response.status_code}.",
                        code="upstream_error",
                    )

                content_type = response.headers.get("content-type", "").lower()
                if content_type and "html" not in content_type:
                    raise FetchError("That link did not return an HTML recipe page.")

                content = bytearray()
                for chunk in response.iter_content():
                    content.extend(chunk)
                    if len(content) > max_bytes:
                        raise FetchError("The recipe page is too large to process safely.")

                return content.decode(response.encoding or "utf-8", errors="replace"), str(
                    response.url
                )
            finally:
                response.close()
    except FetchError:
        raise
    except (CurlError, OSError) as error:
        raise FetchError(
            "The recipe site could not be reached. Please check the link and try again."
        ) from error
    finally:
        if owned_session:
            session.close()

    raise FetchError("The recipe site redirected too many times.")
