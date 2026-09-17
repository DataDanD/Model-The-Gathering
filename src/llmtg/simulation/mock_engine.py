from __future__ import annotations

import random
from collections.abc import Sequence

from llmtg.decks.models import Deck
from llmtg.policies.base import PlayerPolicy
from llmtg.simulation.engine import SimulationEngine
from llmtg.simulation.result import GameResult


class MockEngine(SimulationEngine):
    """Deterministic seeded engine used to test experiment plumbing.

    It does not simulate Magic rules. Every player has an equal chance to win.
    """

    engine_id = "mock-v1"

    def play_game(
        self,
        decks: Sequence[Deck],
        policies: Sequence[PlayerPolicy],
        *,
        seed: int,
    ) -> GameResult:
        if len(decks) < 2:
            raise ValueError("At least two decks are required")
        if len(decks) != len(policies):
            raise ValueError("Each deck must have a corresponding policy")

        rng = random.Random(seed)
        winner_index = rng.randrange(len(decks))
        turns = rng.randint(4, 15)
        return GameResult(
            winner_index=winner_index,
            turns=turns,
            seed=seed,
            deck_ids=tuple(deck.deck_id for deck in decks),
            policy_ids=tuple(policy.policy_id for policy in policies),
        )
