from pathlib import Path

from llmtg.decks.loader import load_deck


def test_bundled_real_decklists_have_100_cards() -> None:
    for path in (Path("decks/goreclaw.txt"), Path("decks/talrand.txt")):
        deck = load_deck(path)
        total = deck.card_count + sum(entry.quantity for entry in deck.commanders)
        assert total == 100, f"{path} has {total} cards"
        assert len(deck.commanders) == 1
