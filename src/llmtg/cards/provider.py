from __future__ import annotations

from typing import Protocol

from llmtg.cards.models import Card


class CardNotFoundError(LookupError):
    pass


class CardProvider(Protocol):
    def get_card(self, name: str) -> Card:
        """Return one normalized card by exact name."""
        ...
