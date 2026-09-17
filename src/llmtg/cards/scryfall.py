from __future__ import annotations

import json
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
            "Accept": "application/json",
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

    def __init__(self, fetch_json: JsonFetcher | None = None) -> None:
        self._fetch_json = fetch_json or _default_fetch_json
        self._cache: dict[str, Card] = {}

    def get_card(self, name: str) -> Card:
        key = name.strip().casefold()
        if not key:
            raise ValueError("Card name cannot be empty")
        if key in self._cache:
            return self._cache[key]

        url = f"{self.base_url}/cards/named?exact={quote(name.strip())}"
        payload = self._fetch_json(url)
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
