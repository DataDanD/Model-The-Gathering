from llmtg.cards.models import Card
from llmtg.cards.provider import CardNotFoundError
from llmtg.decks.models import CardEntry, Deck
from llmtg.decks.validation import validate_commander_deck


class FakeProvider:
    def __init__(self, cards: dict[str, Card]) -> None:
        self.cards = {name.casefold(): card for name, card in cards.items()}

    def get_card(self, name: str) -> Card:
        try:
            return self.cards[name.casefold()]
        except KeyError as exc:
            raise CardNotFoundError(name) from exc


def _card(name: str, *, type_line: str = "Creature", identity=frozenset({"G"}), text: str = "") -> Card:
    return Card(
        name=name,
        oracle_id=name.casefold(),
        type_line=type_line,
        oracle_text=text,
        color_identity=frozenset(identity),
        legalities={"commander": "legal"},
    )


def _valid_deck_and_provider() -> tuple[Deck, FakeProvider]:
    commander = _card("Goreclaw, Terror of Qal Sisma", type_line="Legendary Creature — Bear")
    forest = _card("Forest", type_line="Basic Land — Forest")
    sol_ring = _card("Sol Ring", type_line="Artifact", identity=frozenset())
    filler_cards = [_card(f"Green Card {index}") for index in range(62)]

    deck = Deck(
        name="Fixture",
        commanders=(CardEntry(commander.name),),
        cards=(
            CardEntry("Forest", 36),
            CardEntry("Sol Ring"),
            *(CardEntry(card.name) for card in filler_cards),
        ),
    )
    provider = FakeProvider(
        {card.name: card for card in [commander, forest, sol_ring, *filler_cards]}
    )
    return deck, provider


def test_valid_commander_deck_passes() -> None:
    deck, provider = _valid_deck_and_provider()
    report = validate_commander_deck(deck, provider)
    assert report.is_valid
    assert report.issues == ()


def test_validation_reports_size_singleton_and_color_identity() -> None:
    deck, provider = _valid_deck_and_provider()
    blue = _card("Blue Intruder", identity=frozenset({"U"}))
    provider.cards[blue.name.casefold()] = blue

    broken = Deck(
        name="Broken",
        commanders=deck.commanders,
        cards=deck.cards + (CardEntry("Blue Intruder", 2),),
    )
    report = validate_commander_deck(broken, provider)
    codes = {issue.code for issue in report.issues}

    assert "deck_size" in codes
    assert "singleton" in codes
    assert "color_identity" in codes
