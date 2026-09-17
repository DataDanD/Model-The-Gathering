from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from llmtg.cards.models import Card
from llmtg.cards.provider import CardNotFoundError

BULK_METADATA_URL = "https://api.scryfall.com/bulk-data/oracle_cards"
DEFAULT_BULK_PATH = Path("data/scryfall/oracle-cards.json")


class BulkDataError(RuntimeError):
    """Raised when the local Scryfall catalog cannot be prepared."""


def _request(url: str) -> Request:
    return Request(
        url,
        headers={
            "User-Agent": "Model-The-Gathering/0.1",
            "Accept": "application/json;q=0.9,*/*;q=0.8",
        },
    )


def _download_json(url: str) -> object:
    try:
        with urlopen(_request(url), timeout=60) as response:  # noqa: S310 - Scryfall URLs only
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 429:
            raise BulkDataError(
                "Scryfall returned HTTP 429 while preparing the local catalog. "
                "Do not retry repeatedly; wait for the rate limit to clear and run again."
            ) from exc
        raise


def ensure_oracle_bulk_data(
    path: str | Path = DEFAULT_BULK_PATH,
    *,
    max_age: timedelta = timedelta(days=1),
    force: bool = False,
) -> Path:
    """Ensure a reasonably fresh local Oracle Cards bulk-data file exists.

    Only the metadata request uses api.scryfall.com. The large card file is served
    from Scryfall's static-file host and then reused by later validations.
    """

    destination = Path(path)
    if destination.exists() and not force:
        modified = datetime.fromtimestamp(destination.stat().st_mtime, tz=timezone.utc)
        if datetime.now(timezone.utc) - modified <= max_age:
            return destination

    metadata = _download_json(BULK_METADATA_URL)
    if not isinstance(metadata, dict):
        raise BulkDataError("Scryfall bulk-data metadata was not a JSON object")

    download_uri = metadata.get("download_uri")
    if not download_uri:
        object_type = metadata.get("object")
        details = metadata.get("details")
        suffix = ""
        if object_type or details:
            suffix = f" (object={object_type!r}, details={details!r})"
        raise BulkDataError(
            "Scryfall Oracle Cards metadata did not include a download_uri" + suffix
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(_request(str(download_uri)), timeout=180) as response:  # noqa: S310 - URI supplied by Scryfall
            destination.write_bytes(response.read())
    except HTTPError as exc:
        raise BulkDataError(f"Could not download Scryfall bulk data: HTTP {exc.code}") from exc

    return destination


def _card_from_payload(payload: dict) -> Card:
    return Card(
        name=payload["name"],
        oracle_id=payload.get("oracle_id", payload["id"]),
        type_line=payload.get("type_line", ""),
        oracle_text=payload.get("oracle_text", ""),
        color_identity=frozenset(payload.get("color_identity", [])),
        legalities=dict(payload.get("legalities", {})),
    )


@dataclass(slots=True)
class BulkScryfallProvider:
    """Card provider backed by Scryfall's local Oracle Cards bulk-data file."""

    cards_by_name: dict[str, Card]

    @classmethod
    def from_file(cls, path: str | Path) -> "BulkScryfallProvider":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise BulkDataError("Expected Scryfall Oracle Cards bulk data to be a JSON list")

        cards: dict[str, Card] = {}
        for item in payload:
            if not isinstance(item, dict) or "name" not in item or "id" not in item:
                continue
            card = _card_from_payload(item)
            cards[card.name.casefold()] = card

        if not cards:
            raise BulkDataError("Scryfall bulk-data file contained no usable cards")
        return cls(cards_by_name=cards)

    @classmethod
    def synced(
        cls,
        path: str | Path = DEFAULT_BULK_PATH,
        *,
        force: bool = False,
    ) -> "BulkScryfallProvider":
        return cls.from_file(ensure_oracle_bulk_data(path, force=force))

    def get_card(self, name: str) -> Card:
        key = name.strip().casefold()
        if not key:
            raise ValueError("Card name cannot be empty")
        try:
            return self.cards_by_name[key]
        except KeyError as exc:
            raise CardNotFoundError(name) from exc
