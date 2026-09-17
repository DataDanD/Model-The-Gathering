from llmtg.decks.loader import parse_deck_text
from llmtg.experiments.runner import run_experiment, wilson_interval
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.mock_engine import MockEngine


def _deck(name: str):
    return parse_deck_text("1 Sol Ring", name=name)


def test_wilson_interval_contains_observed_rate() -> None:
    interval = wilson_interval(25, 100)
    assert interval.low < 0.25 < interval.high
    assert 0.0 <= interval.low <= interval.high <= 1.0


def test_run_experiment_rotates_seats() -> None:
    decks = [_deck("A"), _deck("B"), _deck("C"), _deck("D")]
    policies = [RandomPolicy(index) for index, _ in enumerate(decks)]

    summary = run_experiment(MockEngine(), decks, policies, games=4, seed=7, rotate_seats=True)

    expected = [
        tuple(deck.deck_id for deck in decks),
        tuple(deck.deck_id for deck in decks[1:] + decks[:1]),
        tuple(deck.deck_id for deck in decks[2:] + decks[:2]),
        tuple(deck.deck_id for deck in decks[3:] + decks[:3]),
    ]
    assert [result.deck_ids for result in summary.results] == expected


def test_confidence_intervals_created_for_every_deck() -> None:
    decks = [_deck("A"), _deck("B"), _deck("C"), _deck("D")]
    policies = [RandomPolicy(index) for index, _ in enumerate(decks)]

    summary = run_experiment(MockEngine(), decks, policies, games=100, seed=11)

    assert set(summary.confidence_intervals_by_deck) == {deck.deck_id for deck in decks}
