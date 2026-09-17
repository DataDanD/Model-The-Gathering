from llmtg.decks.loader import parse_deck_text
from llmtg.experiments.runner import run_experiment
from llmtg.experiments.storage import SQLiteExperimentStore
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.mock_engine import MockEngine


def _deck(name: str):
    return parse_deck_text("1 Sol Ring", name=name)


def test_sqlite_store_round_trips_experiment(tmp_path) -> None:
    decks = [_deck("A"), _deck("B"), _deck("C"), _deck("D")]
    policies = [RandomPolicy(index) for index, _ in enumerate(decks)]
    engine = MockEngine()
    summary = run_experiment(engine, decks, policies, games=8, seed=20, rotate_seats=True)

    store = SQLiteExperimentStore(tmp_path / "experiments.sqlite3")
    experiment_id = store.save_experiment(
        summary,
        decks,
        policies,
        engine_id=engine.engine_id,
        seed=20,
        rotate_seats=True,
    )

    loaded = store.load_experiment(experiment_id)
    assert loaded is not None
    assert loaded["experiment"]["games"] == 8
    assert loaded["experiment"]["engine_id"] == "mock-v1"
    assert loaded["experiment"]["rotate_seats"] == 1
    assert len(loaded["games"]) == 8
    assert loaded["games"][0]["seed"] == 20
