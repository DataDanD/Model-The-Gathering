from __future__ import annotations

import json

import pytest

from llmtg.cards.bulk import BulkDataError, BulkScryfallProvider
from llmtg.cards.provider import CardNotFoundError


def _write_catalog(path) -> None:
    path.write_text(
        json.dumps(
            [
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
        ),
        encoding="utf-8",
    )


def test_bulk_provider_loads_cards_from_local_file(tmp_path) -> None:
    catalog = tmp_path / "oracle-cards.json"
    _write_catalog(catalog)

    provider = BulkScryfallProvider.from_file(catalog)

    goreclaw = provider.get_card("goreclaw, terror of qal sisma")
    assert goreclaw.name == "Goreclaw, Terror of Qal Sisma"
    assert goreclaw.commander_legal
    assert goreclaw.can_be_commander
    assert goreclaw.color_identity == frozenset({"G"})
    assert provider.get_card("Forest").is_basic_land


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
