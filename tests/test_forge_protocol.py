from llmtg.decks.loader import parse_deck_text
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.forge_protocol import (
    FORGE_PROTOCOL_VERSION,
    ForgeProtocolError,
    build_game_request,
    parse_game_response,
)


def _deck(name: str):
    return parse_deck_text(
        """Commander:
1 Goreclaw, Terror of Qal Sisma
Deck:
1 Sol Ring
2 Forest
""",
        name=name,
    )


def test_build_game_request_preserves_seats_decks_and_policies() -> None:
    decks = [_deck("A"), _deck("B")]
    policies = [RandomPolicy(1), RandomPolicy(2)]

    payload = build_game_request(decks, policies, seed=42)

    assert payload["protocol_version"] == FORGE_PROTOCOL_VERSION
    assert payload["seed"] == 42
    assert [player["seat"] for player in payload["players"]] == [0, 1]
    assert payload["players"][0]["deck"]["deck_id"] == decks[0].deck_id
    assert payload["players"][0]["deck"]["commanders"][0]["name"] == "Goreclaw, Terror of Qal Sisma"
    assert payload["players"][0]["deck"]["mainboard"][1] == {
        "name": "Forest",
        "quantity": 2,
    }
    assert payload["players"][0]["policy_id"] == policies[0].policy_id


def test_parse_game_response_validates_contract() -> None:
    assert parse_game_response(
        {"protocol_version": 1, "winner_index": 1, "turns": 8},
        player_count=4,
    ) == (1, 8)


def test_parse_game_response_rejects_wrong_version() -> None:
    try:
        parse_game_response(
            {"protocol_version": 999, "winner_index": 0, "turns": 1},
            player_count=2,
        )
    except ForgeProtocolError as exc:
        assert "protocol version" in str(exc)
    else:
        raise AssertionError("Expected ForgeProtocolError")
