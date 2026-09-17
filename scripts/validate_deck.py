from __future__ import annotations

import argparse
from pathlib import Path

from llmtg.cards.scryfall import ScryfallProvider
from llmtg.decks.loader import load_deck
from llmtg.decks.validation import validate_commander_deck


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Commander deck with Scryfall card data")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    deck = load_deck(args.path)
    report = validate_commander_deck(deck, ScryfallProvider())

    if report.is_valid:
        print(f"VALID: {deck.name}")
        return 0

    print(f"INVALID: {deck.name}")
    for issue in report.issues:
        print(f"- [{issue.code}] {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
