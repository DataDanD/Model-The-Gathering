from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameResult:
    winner_index: int
    turns: int
    seed: int
    deck_ids: tuple[str, ...]
    policy_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.winner_index < len(self.deck_ids):
            raise ValueError("winner_index must identify one of the supplied decks")
        if len(self.deck_ids) != len(self.policy_ids):
            raise ValueError("Each deck must have a corresponding policy")
        if self.turns < 1:
            raise ValueError("turns must be at least 1")
