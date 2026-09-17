from __future__ import annotations

import argparse
from pathlib import Path

from llmtg.cards.bulk import BulkDataError, BulkScryfallProvider, DEFAULT_BULK_PATH
from llmtg.cards.scryfall import ScryfallProvider
from llmtg.decks.loader import load_deck
from llmtg.decks.validation import validate_commander_deck


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Commander deck with Scryfall card data")
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use per-card live Scryfall API lookups instead of the local bulk catalog",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force a fresh Scryfall Oracle Cards bulk-data download",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_BULK_PATH,
        help=f"Bulk catalog path (default: {DEFAULT_BULK_PATH})",
    )
    args = parser.parse_args()

    deck = load_deck(args.path)

    try:
        if args.live:
            provider = ScryfallProvider()
        else:
            print(f"Preparing local Scryfall catalog at {args.catalog} ...")
            provider = BulkScryfallProvider.synced(args.catalog, force=args.refresh)
    except BulkDataError as exc:
        print(f"ERROR: {exc}")
        return 2

    report = validate_commander_deck(deck, provider)

    if report.is_valid:
        print(f"VALID: {deck.name}")
        return 0

    print(f"INVALID: {deck.name}")
    for issue in report.issues:
        print(f"- [{issue.code}] {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
