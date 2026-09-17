from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class PlayerPolicy(ABC):
    """Strategy interface used by simulation engines."""

    policy_id = "base"

    @abstractmethod
    def choose_action(self, game_state: Any, legal_actions: Sequence[Any]) -> Any:
        """Choose exactly one legal action for the current game state."""
        raise NotImplementedError
