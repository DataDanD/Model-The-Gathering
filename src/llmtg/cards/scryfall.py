from __future__ import annotations

import json
import time
from collections.abc import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from llmtg.cards.models import Card
from llmtg.cards.provider import CardNotFoundError

JsonFetcher = Callable[[str], dict]


def _default_fetch_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "Model-The-Gathering/0.1",
            "Accept": "application/json;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed Scryfall host
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            raise CardNotFoundError(url) from exc
        raise


class ScryfallProvider:
    base_url = "https://api.scryfall.com"

    def __init__(
        self,
        fetch_json: JsonFetcher | None = None,
        *,
        minimum_interval_seconds: float = 0.1,
    ) -> None:
        self._fetch_json = fetch_json or _default_fetch_json
        self._cache: dict[str, Card] = {}
        self._minimum_interval_seconds = minimum_interval_seconds
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._minimum_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get_card(self, name: str) -> Card:
        key = name.strip().casefold()
        if not key:
            raise ValueError("Card name cannot be empty")
        if key in self._cache:
            return self._cache[key]

        self._throttle()
        url = f"{self.base_url}/cards/named?exact={quote(name.strip())}"
        payload = self._fetch_json(url)
        self._last_request_at = time.monotonic()
        if payload.get("object") == "error":
            raise CardNotFoundError(name)

        card = Card(
            name=payload["name"],
            oracle_id=payload.get("oracle_id", payload["id"]),
            type_line=payload.get("type_line", ""),
            oracle_text=payload.get("oracle_text", ""),
            color_identity=frozenset(payload.get("color_identity", [])),
            legalities=dict(payload.get("legalities", {})),
        )
        self._cache[key] = card
        self._cache[card.name.casefold()] = card
        return card
