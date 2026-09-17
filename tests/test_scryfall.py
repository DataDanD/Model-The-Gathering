from llmtg.cards.provider import CardNotFoundError
from llmtg.cards.scryfall import ScryfallProvider


def test_scryfall_provider_normalizes_and_caches_cards() -> None:
    calls = []

    def fetch_json(url: str) -> dict:
        calls.append(url)
        return {
            "id": "print-id",
            "oracle_id": "oracle-id",
            "name": "Goreclaw, Terror of Qal Sisma",
            "type_line": "Legendary Creature — Bear",
            "oracle_text": "Creature spells you cast with power 4 or greater cost {2} less to cast.",
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        }

    provider = ScryfallProvider(fetch_json=fetch_json)
    first = provider.get_card("Goreclaw, Terror of Qal Sisma")
    second = provider.get_card("goreclaw, terror of qal sisma")

    assert first is second
    assert first.oracle_id == "oracle-id"
    assert first.color_identity == frozenset({"G"})
    assert first.can_be_commander
    assert len(calls) == 1
    assert "cards/named?exact=" in calls[0]


def test_scryfall_provider_raises_for_error_payload() -> None:
    provider = ScryfallProvider(fetch_json=lambda _: {"object": "error"})

    try:
        provider.get_card("Definitely Not A Card")
    except CardNotFoundError:
        pass
    else:
        raise AssertionError("Expected CardNotFoundError")
