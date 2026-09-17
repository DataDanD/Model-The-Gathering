from llmtg.decks.loader import parse_deck_text
from llmtg.experiments.runner import run_experiment
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.mock_engine import MockEngine


def _deck(name: str):
    return parse_deck_text("1 Sol Ring", name=name)


def test_mock_engine_is_reproducible_by_seed() -> None:
    decks = [_deck("A"), _deck("B"), _deck("C"), _deck("D")]
    policies = [RandomPolicy(1) for _ in decks]
    engine = MockEngine()

    first = engine.play_game(decks, policies, seed=42)
    second = engine.play_game(decks, policies, seed=42)

    assert first == second


def test_run_experiment_aggregates_results() -> None:
    decks = [_deck("A"), _deck("B"), _deck("C"), _deck("D")]
    policies = [RandomPolicy(index) for index, _ in enumerate(decks)]

    summary = run_experiment(MockEngine(), decks, policies, games=100, seed=1000)

    assert summary.games == 100
    assert sum(summary.wins_by_deck.values()) == 100
    assert round(sum(summary.win_rates_by_deck.values()), 10) == 1.0
    assert 4 <= summary.average_turns <= 15
    assert len(summary.results) == 100
