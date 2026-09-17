from __future__ import annotations

import random
from typing import Any, Sequence

from llmtg.policies.base import PlayerPolicy


class RandomPolicy(PlayerPolicy):
    """Minimal baseline policy for engines that expose legal actions."""

    policy_id = "random-v1"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def choose_action(self, game_state: Any, legal_actions: Sequence[Any]) -> Any:
        if not legal_actions:
            raise ValueError("RandomPolicy requires at least one legal action")
        return self._rng.choice(list(legal_actions))
