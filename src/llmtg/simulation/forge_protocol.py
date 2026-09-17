from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from llmtg.decks.models import CardEntry, Deck
from llmtg.policies.base import PlayerPolicy

FORGE_PROTOCOL_VERSION = 1


class ForgeProtocolError(ValueError):
    """Raised when a Forge bridge request or response violates the protocol."""


def _card_entry(entry: CardEntry) -> dict[str, Any]:
    return {"name": entry.name, "quantity": entry.quantity}


def deck_payload(deck: Deck) -> dict[str, Any]:
    return {
        "deck_id": deck.deck_id,
        "name": deck.name,
        "commanders": [_card_entry(entry) for entry in deck.commanders],
        "mainboard": [_card_entry(entry) for entry in deck.cards],
    }


def build_game_request(
    decks: Sequence[Deck],
    policies: Sequence[PlayerPolicy],
    *,
    seed: int,
) -> dict[str, Any]:
    if len(decks) < 2:
        raise ForgeProtocolError("At least two decks are required")
    if len(decks) != len(policies):
        raise ForgeProtocolError("Each deck must have a corresponding policy")

    return {
        "protocol_version": FORGE_PROTOCOL_VERSION,
        "seed": seed,
        "players": [
            {
                "seat": seat,
                "policy_id": policy.policy_id,
                "deck": deck_payload(deck),
            }
            for seat, (deck, policy) in enumerate(zip(decks, policies, strict=True))
        ],
    }


def parse_game_response(payload: object, *, player_count: int) -> tuple[int, int]:
    if not isinstance(payload, dict):
        raise ForgeProtocolError("Forge bridge response must be a JSON object")

    version = payload.get("protocol_version")
    if version != FORGE_PROTOCOL_VERSION:
        raise ForgeProtocolError(
            f"Unsupported Forge protocol version: {version!r}; "
            f"expected {FORGE_PROTOCOL_VERSION}"
        )

    winner_index = payload.get("winner_index")
    turns = payload.get("turns")

    if not isinstance(winner_index, int) or not 0 <= winner_index < player_count:
        raise ForgeProtocolError("winner_index must identify one of the supplied players")
    if not isinstance(turns, int) or turns < 1:
        raise ForgeProtocolError("turns must be an integer greater than zero")

    return winner_index, turns
