from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from llmtg.cards.models import Card
from llmtg.cards.provider import CardNotFoundError, CardProvider
from llmtg.decks.models import Deck


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def _resolve(provider: CardProvider, name: str, issues: list[ValidationIssue]) -> Card | None:
    try:
        return provider.get_card(name)
    except CardNotFoundError:
        issues.append(ValidationIssue("card_not_found", f"Card not found: {name}"))
        return None


def validate_commander_deck(deck: Deck, provider: CardProvider) -> ValidationReport:
    issues: list[ValidationIssue] = []
    commander_count = sum(entry.quantity for entry in deck.commanders)
    total_cards = commander_count + deck.card_count

    if total_cards != 100:
        issues.append(
            ValidationIssue(
                "deck_size",
                f"Commander decks must contain exactly 100 cards including commander(s); found {total_cards}",
            )
        )
    if commander_count not in {1, 2}:
        issues.append(
            ValidationIssue(
                "commander_count",
                f"Expected one commander or a supported two-card command zone; found {commander_count}",
            )
        )

    resolved_commanders = [
        card
        for entry in deck.commanders
        for card in [_resolve(provider, entry.name, issues)]
        if card is not None
    ]

    for card in resolved_commanders:
        if not card.commander_legal:
            issues.append(ValidationIssue("commander_illegal", f"{card.name} is not legal in Commander"))
        if not card.can_be_commander:
            issues.append(ValidationIssue("not_a_commander", f"{card.name} cannot normally be a commander"))

    # V1 supports a single commander fully. Two-card command zones are resolved and
    # checked individually, but compatibility rules such as Partner/Background are deferred.
    commander_identity = frozenset().union(*(card.color_identity for card in resolved_commanders))

    counts = Counter()
    resolved_main: list[tuple[Card, int]] = []
    for entry in deck.cards:
        counts[entry.name.casefold()] += entry.quantity
        card = _resolve(provider, entry.name, issues)
        if card is not None:
            resolved_main.append((card, entry.quantity))

    for card, quantity in resolved_main:
        if not card.commander_legal:
            issues.append(ValidationIssue("card_illegal", f"{card.name} is not legal in Commander"))
        if not card.color_identity.issubset(commander_identity):
            issues.append(
                ValidationIssue(
                    "color_identity",
                    f"{card.name} has color identity {sorted(card.color_identity)} outside commander identity {sorted(commander_identity)}",
                )
            )
        if counts[card.name.casefold()] > 1 and not card.is_basic_land and not card.allows_any_number:
            issues.append(
                ValidationIssue(
                    "singleton",
                    f"{card.name} appears {counts[card.name.casefold()]} times but Commander is singleton",
                )
            )

    return ValidationReport(tuple(issues))
