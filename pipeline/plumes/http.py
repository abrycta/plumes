"""A polite HTTP client for the crawlers: at most one request per second per host, retries, and the pinned LAVA chain.

PHIVOLCS-LAVA sends only its leaf certificate (no GlobalSign intermediate), so `certifi` alone fails; the intermediate
is pinned in plumes/certs/ (DECISIONS S2). The leaf on wovodat.phivolcs.dost.gov.ph expires 2026-11-19: if the renewed
leaf is issued by a different intermediate, fetch it from the new certificate's AIA URL and replace the pinned file.
"""

from __future__ import annotations

import pathlib
import ssl
import time
from urllib.parse import urlsplit

import certifi
import httpx

UA = "plumes-pipeline/0.1 (+https://github.com/abrycta/plumes; retrospective volcano record; 1 req/s)"
PINNED = pathlib.Path(__file__).parent / "certs" / "globalsign-rsa-ov-ssl-ca-2018.pem"


def ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.load_verify_locations(cafile=str(PINNED))
    return ctx


class Polite:
    """httpx.Client wrapper: min_interval seconds between requests to the same host; retries 429/5xx with backoff."""

    def __init__(self, min_interval: float = 1.0, timeout: float = 60, retries: int = 3, retry_statuses=(429, 502, 503, 504)):
        self.min_interval, self.retries, self.retry_statuses = min_interval, retries, set(retry_statuses)
        self.client = httpx.Client(headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True, verify=ssl_context())
        self._last: dict[str, float] = {}
        self.requests = 0

    def get(self, url: str, **kw) -> httpx.Response:
        host = urlsplit(url).hostname or ""
        for attempt in range(self.retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last.get(host, 0.0))
            if wait > 0:
                time.sleep(wait)
            try:
                r = self.client.get(url, **kw)
            except httpx.TransportError:
                r = None
            finally:
                self._last[host] = time.monotonic()
                self.requests += 1
            if r is not None and r.status_code not in self.retry_statuses:
                return r
            if attempt < self.retries:
                time.sleep(5 * 2**attempt)
        if r is None:
            raise httpx.ConnectError(f"giving up on {url}")
        return r

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
