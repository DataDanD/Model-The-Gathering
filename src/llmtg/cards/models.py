from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Card:
    """Provider-neutral card data needed by deck validation and simulation setup."""

    name: str
    oracle_id: str
    type_line: str
    oracle_text: str = ""
    color_identity: frozenset[str] = field(default_factory=frozenset)
    legalities: dict[str, str] = field(default_factory=dict)

    @property
    def is_basic_land(self) -> bool:
        return "Basic Land" in self.type_line

    @property
    def commander_legal(self) -> bool:
        return self.legalities.get("commander") == "legal"

    @property
    def can_be_commander(self) -> bool:
        type_line = self.type_line.lower()
        text = self.oracle_text.lower()
        return (
            "legendary creature" in type_line
            or "can be your commander" in text
        )

    @property
    def allows_any_number(self) -> bool:
        return "a deck can have any number of cards named" in self.oracle_text.lower()
