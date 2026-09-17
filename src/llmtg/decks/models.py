from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class CardEntry:
    name: str
    quantity: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Card name cannot be empty")
        if self.quantity < 1:
            raise ValueError("Card quantity must be at least 1")


@dataclass(frozen=True, slots=True)
class Deck:
    name: str
    commanders: tuple[CardEntry, ...]
    cards: tuple[CardEntry, ...]

    @property
    def card_count(self) -> int:
        return sum(card.quantity for card in self.cards)

    @property
    def deck_id(self) -> str:
        normalized = [self.name.strip().lower()]
        normalized.extend(
            f"commander:{card.quantity}:{card.name.strip().lower()}"
            for card in sorted(self.commanders, key=lambda entry: entry.name.lower())
        )
        normalized.extend(
            f"card:{card.quantity}:{card.name.strip().lower()}"
            for card in sorted(self.cards, key=lambda entry: entry.name.lower())
        )
        return sha256("\n".join(normalized).encode("utf-8")).hexdigest()[:16]
