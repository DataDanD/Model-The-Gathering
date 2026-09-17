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
        {
            "id": "llanowar-upcoming",
            "oracle_id": "llanowar-oracle",
            "name": "Llanowar Elves",
            "type_line": "Creature — Elf Druid",
            "oracle_text": "{T}: Add {G}.",
            "color_identity": ["G"],
            "legalities": {"commander": "not_legal"},
        },
        {
            "id": "llanowar-released",
            "oracle_id": "llanowar-oracle",
            "name": "Llanowar Elves",
            "type_line": "Creature — Elf Druid",
            "oracle_text": "{T}: Add {G}.",
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        },
        {
            "id": "bala-ged",
            "oracle_id": "bala-ged-oracle",
            "name": "Bala Ged Recovery // Bala Ged Sanctuary",
            "type_line": "Sorcery // Land",
            "oracle_text": "",
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
            "card_faces": [
                {"name": "Bala Ged Recovery"},
                {"name": "Bala Ged Sanctuary"},
            ],
        },
    ]


def _write_catalog(path) -> None:
    path.write_text(json.dumps(_card_payloads()), encoding="utf-8")


def _write_jsonl_gz_catalog(path) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for item in _card_payloads():
            handle.write(json.dumps(item))
            handle.write("\n")


def test_default_bulk_metadata_endpoint_uses_scryfall_type_slug() -> None:
    assert BULK_METADATA_URL.endswith("/bulk-data/default_cards")


def test_current_metadata_prefers_jsonl_download_uri() -> None:
    metadata = {
        "object": "bulk_data",
        "type": "default_cards",
        "jsonl_download_uri": "https://data.scryfall.io/default-cards/current.jsonl.gz",
    }
    assert _download_uri_from_metadata(metadata).endswith("current.jsonl.gz")


def test_legacy_metadata_still_accepts_download_uri() -> None:
    metadata = {
        "object": "bulk_data",
        "type": "default_cards",
        "download_uri": "https://data.scryfall.io/default-cards/current.json",
    }
    assert _download_uri_from_metadata(metadata).endswith("current.json")


def test_bulk_provider_loads_cards_from_local_json_file(tmp_path) -> None:
    catalog = tmp_path / "default-cards.json"
    _write_catalog(catalog)

    provider = BulkScryfallProvider.from_file(catalog)

    goreclaw = provider.get_card("goreclaw, terror of qal sisma")
    assert goreclaw.name == "Goreclaw, Terror of Qal Sisma"
    assert goreclaw.commander_legal
    assert goreclaw.can_be_commander
    assert goreclaw.color_identity == frozenset({"G"})
    assert provider.get_card("Forest").is_basic_land


def test_bulk_provider_loads_current_gzipped_jsonl_format(tmp_path) -> None:
    catalog = tmp_path / "default-cards.jsonl.gz"
    _write_jsonl_gz_catalog(catalog)

    provider = BulkScryfallProvider.from_file(catalog)

    assert provider.get_card("Forest").is_basic_land
    assert provider.get_card("Goreclaw, Terror of Qal Sisma").can_be_commander


def test_bulk_provider_prefers_a_commander_legal_printing() -> None:
    provider = BulkScryfallProvider.from_file(_catalog_path_from_payloads(_card_payloads()))
    assert provider.get_card("Llanowar Elves").commander_legal


def test_bulk_provider_indexes_individual_card_face_names() -> None:
    provider = BulkScryfallProvider.from_file(_catalog_path_from_payloads(_card_payloads()))
    assert provider.get_card("Bala Ged Recovery").name == "Bala Ged Recovery // Bala Ged Sanctuary"
    assert provider.get_card("Bala Ged Sanctuary").commander_legal


def _catalog_path_from_payloads(payloads: list[dict]):
    # Avoid pytest fixtures in these compact behavioral tests by using a temporary file.
    import tempfile
    from pathlib import Path

    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(payloads, handle)
        handle.close()
        return Path(handle.name)
    except Exception:
        handle.close()
        raise


def test_bulk_provider_reports_missing_card(tmp_path) -> None:
    catalog = tmp_path / "default-cards.json"
    _write_catalog(catalog)
    provider = BulkScryfallProvider.from_file(catalog)

    with pytest.raises(CardNotFoundError):
        provider.get_card("Definitely Not A Magic Card")


def test_bulk_provider_rejects_non_list_payload(tmp_path) -> None:
    catalog = tmp_path / "bad.json"
    catalog.write_text(json.dumps({"name": "not bulk data"}), encoding="utf-8")

    with pytest.raises(BulkDataError):
        BulkScryfallProvider.from_file(catalog)
