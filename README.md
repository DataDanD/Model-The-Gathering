# Model the Gathering

**Model the Gathering** (`llmtg`) is an experimental toolkit for measuring, simulating, and eventually optimizing Magic: The Gathering Commander decks and player policies.

The long-term direction is a common decision layer that can support large-scale deck experiments, AI pilots, digital play assistance, and eventually multimodal physical-table copilots. The active code starts deliberately small so future engines and agents can plug into stable interfaces instead of inheriting the archived prototype code directly.

## Current scope

The active vertical slice provides:

- lightweight Commander deck models and text parsing
- stable deck fingerprints for experiment tracking
- a `PlayerPolicy` interface for heuristic, LLM, and learned pilots
- a `SimulationEngine` interface for mock, Forge, or future fast simulators
- a deterministic seeded `MockEngine`
- repeated-game experiments with automatic cyclic seat rotation
- win rates, average turn count, and Wilson 95% confidence intervals
- SQLite persistence for experiment metadata and per-game results
- pytest coverage for deck parsing, reproducibility, statistics, seat rotation, and persistence

The mock engine **does not simulate Magic**. It exists only to prove that the experiment plumbing is reproducible before a real rules engine is connected.

## Project layout

```text
src/llmtg/
  decks/          deck models and parsers
  policies/       player decision interfaces and baselines
  simulation/     simulation contracts and engines
  experiments/    orchestration, statistics, and persistence

tests/            unit tests
archive/          donor/reference code from earlier projects
```

## Setup

Python 3.11+ is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e ".[dev]"
pytest
```

## Run an experiment

```python
from llmtg.decks.loader import parse_deck_text
from llmtg.experiments.runner import run_experiment
from llmtg.experiments.storage import SQLiteExperimentStore
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.mock_engine import MockEngine

names = ["Blue Farm", "Kinnan", "Tivit", "RogSi"]
decks = [parse_deck_text("1 Sol Ring", name=name) for name in names]
policies = [RandomPolicy(seed=i) for i in range(4)]
engine = MockEngine()

summary = run_experiment(
    engine,
    decks,
    policies,
    games=10_000,
    seed=42,
    rotate_seats=True,
)

for deck in decks:
    rate = summary.win_rates_by_deck[deck.deck_id]
    interval = summary.confidence_intervals_by_deck[deck.deck_id]
    print(deck.name, rate, (interval.low, interval.high))
```

With the mock engine, sufficiently large runs should converge near 25% for each deck because winners are selected uniformly at random. Seat rotation cycles each deck through every seat so future engines do not accidentally bake seat-position bias into matchup estimates.

## Persist results

```python
store = SQLiteExperimentStore("data/experiments.sqlite3")
experiment_id = store.save_experiment(
    summary,
    decks,
    policies,
    engine_id=engine.engine_id,
    seed=42,
    rotate_seats=True,
)

record = store.load_experiment(experiment_id)
```

The database stores an experiment header plus every game's ordered deck and policy IDs, seed, winner, and turn count. That keeps enough information for later seat-position, matchup, and policy analysis.

## Next milestones

1. Add real Commander decklists and validation.
2. Add a card-data provider backed by Scryfall/local catalog data.
3. Implement a Forge-backed `SimulationEngine` adapter.
4. Add matchup/meta sampling and richer experiment queries.
5. Add an LLM deck-scientist that proposes mutations for A/B testing.
6. Add stronger player policies and policy-vs-policy evaluation.
7. Add learned policies and self-play datasets.

## Archive

`archive/` contains imported code from the projects used as references while designing Model the Gathering. Active code should depend on `src/llmtg`, not import directly from `archive/`.
