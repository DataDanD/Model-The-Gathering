from __future__ import annotations

from pathlib import Path

from llmtg.decks.models import CardEntry, Deck


def _parse_card_line(line: str) -> CardEntry:
    quantity_text, separator, name = line.strip().partition(" ")
    if not separator or not quantity_text.isdigit() or not name.strip():
        raise ValueError(f"Invalid deck line: {line!r}")
    return CardEntry(name=name.strip(), quantity=int(quantity_text))


def parse_deck_text(text: str, *, name: str = "Untitled Deck") -> Deck:
    section = "deck"
    commanders: list[CardEntry] = []
    cards: list[CardEntry] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        heading = line.rstrip(":").lower()
        if heading in {"commander", "commanders"}:
            section = "commander"
            continue
        if heading in {"deck", "mainboard", "main"}:
            section = "deck"
            continue

        entry = _parse_card_line(line)
        if section == "commander":
            commanders.append(entry)
        else:
            cards.append(entry)

    if not cards:
        raise ValueError("Deck must contain at least one main-deck card")

    return Deck(name=name, commanders=tuple(commanders), cards=tuple(cards))


def load_deck(path: str | Path, *, name: str | None = None) -> Deck:
    deck_path = Path(path)
    return parse_deck_text(
        deck_path.read_text(encoding="utf-8"),
        name=name or deck_path.stem,
    )
