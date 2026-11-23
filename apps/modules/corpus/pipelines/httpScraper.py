# apps/modules/corpus/pipelines/httpScraper.py
"""Small JSON-over-HTTP client shared by API based scrapers."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ...shared.kernel.exceptions import RiahAppError
from .baseScraper import BaseScraper

DEFAULT_USER_AGENT = "RiahCodeBot/0.1"
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_DELAY_SECONDS = 0.1


class HttpScraper(BaseScraper):
    """Base scraper exposing a minimal, dependency free JSON fetcher."""

    def _fetchJson(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Fetch and decode a JSON payload, wrapping network errors."""
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        request = urllib.request.Request(
            f"{url}{query}",
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            raise RiahAppError(
                f"Requete HTTP echouee: {url}",
                details={"reason": str(error)},
            ) from error
        time.sleep(REQUEST_DELAY_SECONDS)
        return payload
