# Model the Gathering

**Model the Gathering** (`llmtg`) is an experimental toolkit for measuring, simulating, and eventually optimizing Magic: The Gathering Commander decks and player policies.

The long-term direction is a common decision layer that can support large-scale deck experiments, AI pilots, digital play assistance, and eventually multimodal physical-table copilots. The active code starts deliberately small so future engines and agents can plug into stable interfaces instead of inheriting the archived prototype code directly.

## Current scope

The active vertical slice provides:

- lightweight Commander deck models and text parsing
- bundled real 100-card Commander deck fixtures in `decks/`
- a cached local Scryfall Oracle Cards bulk-data provider for deck validation
- an optional live Scryfall exact-name provider for one-off card lookups
- Commander validation for deck size, commander eligibility, legality, singleton rules, and color identity
- stable deck fingerprints for experiment tracking
- a `PlayerPolicy` interface for heuristic, LLM, and learned pilots
- a `SimulationEngine` interface for mock, Forge, or future fast simulators
- a deterministic seeded `MockEngine`
- repeated-game experiments with automatic cyclic seat rotation
- win rates, average turn count, and Wilson 95% confidence intervals
- SQLite persistence for experiment metadata and per-game results
- pytest coverage for deck parsing, validation, reproducibility, statistics, seat rotation, persistence, and card-provider behavior

The mock engine **does not simulate Magic**. It exists only to prove that the experiment plumbing is reproducible before a real rules engine is connected.

## Project layout

```text
src/llmtg/
  cards/          normalized card data and providers
  decks/          deck models, parsers, and Commander validation
  policies/       player decision interfaces and baselines
  simulation/     simulation contracts and engines
  experiments/    orchestration, statistics, and persistence

decks/            real Commander deck fixtures
tests/            unit tests
scripts/          small developer/CLI utilities
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

## Validate a real Commander deck

Two real 100-card example lists are included:

```text
decks/goreclaw.txt
decks/talrand.txt
```

Validate one with the local Scryfall bulk catalog:

```bash
python scripts/validate_deck.py decks/goreclaw.txt
```

On the first run, Model the Gathering fetches Scryfall's Oracle Cards bulk-data metadata once and downloads the static catalog to `data/scryfall/oracle-cards.json`. Later validations reuse that local file instead of performing one live API request per card.

Force a fresh catalog download:

```bash
python scripts/validate_deck.py decks/goreclaw.txt --refresh
```

The old per-card live API behavior is still available for debugging or one-off checks:

```bash
python scripts/validate_deck.py decks/goreclaw.txt --live
```

The validator currently checks:

- exactly 100 cards including commander(s)
- one commander or a two-card command zone
- commander legality and basic commander eligibility
- Commander legality for each main-deck card
- singleton rules, while allowing basic lands and cards whose Oracle text allows any number
- every card's color identity against the command zone's combined color identity

Two-card command zones are intentionally conservative in this version: both cards are resolved and their color identities are combined, but Partner, Background, Doctor's companion, and other compatibility rules are not yet fully modeled.

## Scryfall providers

For repeated deck validation, use the bulk provider:

```python
from llmtg.cards import BulkScryfallProvider

provider = BulkScryfallProvider.synced()
card = provider.get_card("Rhystic Study")
print(card.type_line, card.color_identity)
```

For one-off live lookups:

```python
from llmtg.cards import ScryfallProvider

provider = ScryfallProvider()
card = provider.get_card("Rhystic Study")
```

The live provider caches repeated lookups, but high-volume validation should use bulk data rather than repeated requests to `api.scryfall.com`.

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

1. Implement a Forge-backed `SimulationEngine` adapter.
2. Fully model multi-card Commander eligibility rules such as Partner and Background.
3. Add matchup/meta sampling and richer experiment queries.
4. Add an LLM deck-scientist that proposes mutations for A/B testing.
5. Add stronger player policies and policy-vs-policy evaluation.
6. Add learned policies and self-play datasets.

## Archive

`archive/` contains imported code from the projects used as references while designing Model the Gathering. Active code should depend on `src/llmtg`, not import directly from `archive/`.
