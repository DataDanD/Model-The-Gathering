# Model the Gathering

**Model the Gathering** (`llmtg`) is an experimental toolkit for measuring, simulating, and eventually optimizing Magic: The Gathering Commander decks and player policies.

The long-term direction is a common decision layer that can support large-scale deck experiments, AI pilots, digital play assistance, and eventually multimodal physical-table copilots. The active code starts deliberately small so future engines and agents can plug into stable interfaces instead of inheriting the archived prototype code directly.

## V1 scope

The first vertical slice provides:

- lightweight Commander deck models and text parsing
- stable deck fingerprints for experiment tracking
- a `PlayerPolicy` interface for heuristic, LLM, and learned pilots
- a `SimulationEngine` interface for mock, Forge, or future fast simulators
- a deterministic seeded `MockEngine`
- an experiment runner with win-rate and average-turn aggregation
- pytest coverage for deck parsing and repeatable simulations

The mock engine **does not simulate Magic**. It exists only to prove that the experiment plumbing is reproducible before a real rules engine is connected.

## Project layout

```text
src/llmtg/
  decks/          deck models and parsers
  policies/       player decision interfaces and baselines
  simulation/     simulation contracts and engines
  experiments/    repeated-game experiment orchestration

tests/            V1 unit tests
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

## Minimal example

```python
from llmtg.decks.loader import parse_deck_text
from llmtg.experiments.runner import run_experiment
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.mock_engine import MockEngine

names = ["Blue Farm", "Kinnan", "Tivit", "RogSi"]
decks = [parse_deck_text("1 Sol Ring", name=name) for name in names]
policies = [RandomPolicy(seed=i) for i in range(4)]

summary = run_experiment(
    MockEngine(),
    decks,
    policies,
    games=10_000,
    seed=42,
)

for deck in decks:
    print(deck.name, summary.win_rates_by_deck[deck.deck_id])
```

With the mock engine, sufficiently large runs should converge near 25% for each seat because winners are selected uniformly at random.

## Next milestones

1. Add real Commander decklists and validation.
2. Add a card-data provider backed by Scryfall/local catalog data.
3. Add persistent experiment storage and confidence intervals.
4. Implement a Forge-backed `SimulationEngine` adapter.
5. Add seat rotation and matchup/meta sampling.
6. Add an LLM deck-scientist that proposes mutations for A/B testing.
7. Add stronger player policies and policy-vs-policy evaluation.

## Archive

`archive/` contains imported code from the projects used as references while designing Model the Gathering. Active code should depend on `src/llmtg`, not import directly from `archive/`.
