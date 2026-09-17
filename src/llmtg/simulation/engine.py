from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from llmtg.decks.models import Deck
from llmtg.policies.base import PlayerPolicy
from llmtg.simulation.result import GameResult


class SimulationEngine(ABC):
    """Backend-agnostic interface for one Commander game."""

    engine_id = "base"

    @abstractmethod
    def play_game(
        self,
        decks: Sequence[Deck],
        policies: Sequence[PlayerPolicy],
        *,
        seed: int,
    ) -> GameResult:
        raise NotImplementedError
