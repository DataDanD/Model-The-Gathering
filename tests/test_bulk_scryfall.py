from __future__ import annotations

import gzip
import json

import pytest

from llmtg.cards.bulk import (
    BULK_METADATA_URL,
    BulkDataError,
    BulkScryfallProvider,
    _download_uri_from_metadata,
)
from llmtg.cards.provider import CardNotFoundError


def _card_payloads() -> list[dict]:
    return [
        {
            "id": "card-1",
            "oracle_id": "oracle-1",
            "name": "Goreclaw, Terror of Qal Sisma",
            "type_line": "Legendary Creature — Bear",
            "oracle_text": "Creature spells you cast with power 4 or greater cost {2} less to cast.",
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        },
        {
            "id": "card-2",
            "oracle_id": "oracle-2",
            "name": "Forest",
            "type_line": "Basic Land — Forest",
            "oracle_text": "",
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        },
    ]


def _write_catalog(path) -> None:
    path.write_text(json.dumps(_card_payloads()), encoding="utf-8")


def _write_jsonl_gz_catalog(path) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for item in _card_payloads():
            handle.write(json.dumps(item))
            handle.write("\n")


def test_oracle_bulk_metadata_endpoint_uses_scryfall_type_slug() -> None:
    assert BULK_METADATA_URL.endswith("/bulk-data/oracle_cards")


def test_current_metadata_prefers_jsonl_download_uri() -> None:
    metadata = {
        "object": "bulk_data",
        "type": "oracle_cards",
        "jsonl_download_uri": "https://data.scryfall.io/oracle-cards/current.jsonl.gz",
    }
    assert _download_uri_from_metadata(metadata).endswith("current.jsonl.gz")


def test_legacy_metadata_still_accepts_download_uri() -> None:
    metadata = {
        "object": "bulk_data",
        "type": "oracle_cards",
        "download_uri": "https://data.scryfall.io/oracle-cards/current.json",
    }
    assert _download_uri_from_metadata(metadata).endswith("current.json")


def test_bulk_provider_loads_cards_from_local_json_file(tmp_path) -> None:
    catalog = tmp_path / "oracle-cards.json"
    _write_catalog(catalog)

    provider = BulkScryfallProvider.from_file(catalog)

    goreclaw = provider.get_card("goreclaw, terror of qal sisma")
    assert goreclaw.name == "Goreclaw, Terror of Qal Sisma"
    assert goreclaw.commander_legal
    assert goreclaw.can_be_commander
    assert goreclaw.color_identity == frozenset({"G"})
    assert provider.get_card("Forest").is_basic_land


def test_bulk_provider_loads_current_gzipped_jsonl_format(tmp_path) -> None:
    catalog = tmp_path / "oracle-cards.jsonl.gz"
    _write_jsonl_gz_catalog(catalog)

    provider = BulkScryfallProvider.from_file(catalog)

    assert provider.get_card("Forest").is_basic_land
    assert provider.get_card("Goreclaw, Terror of Qal Sisma").can_be_commander


def test_bulk_provider_reports_missing_card(tmp_path) -> None:
    catalog = tmp_path / "oracle-cards.json"
    _write_catalog(catalog)
    provider = BulkScryfallProvider.from_file(catalog)

    with pytest.raises(CardNotFoundError):
        provider.get_card("Definitely Not A Magic Card")


def test_bulk_provider_rejects_non_list_payload(tmp_path) -> None:
    catalog = tmp_path / "bad.json"
    catalog.write_text(json.dumps({"name": "not bulk data"}), encoding="utf-8")

    with pytest.raises(BulkDataError):
        BulkScryfallProvider.from_file(catalog)
