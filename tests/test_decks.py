from llmtg.decks.loader import parse_deck_text


def test_parse_deck_text_with_commander_section() -> None:
    deck = parse_deck_text(
        """
        Commander
        1 Kinnan, Bonder Prodigy

        Deck
        1 Sol Ring
        2 Forest
        """,
        name="Kinnan Test",
    )

    assert deck.name == "Kinnan Test"
    assert deck.commanders[0].name == "Kinnan, Bonder Prodigy"
    assert deck.card_count == 3
    assert len(deck.deck_id) == 16


def test_deck_id_changes_when_cards_change() -> None:
    first = parse_deck_text("1 Sol Ring", name="Test")
    second = parse_deck_text("1 Arcane Signet", name="Test")

    assert first.deck_id != second.deck_id
