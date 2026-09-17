from __future__ import annotations

import sys
from pathlib import Path

from llmtg.decks.loader import load_deck
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.forge import ForgeEngine


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    decks = [
        load_deck(repo_root / "decks" / "goreclaw.txt"),
        load_deck(repo_root / "decks" / "talrand.txt"),
    ]
    policies = [RandomPolicy(1), RandomPolicy(2)]
    engine = ForgeEngine([sys.executable, str(repo_root / "scripts" / "forge_bridge_stub.py")])

    result = engine.play_game(decks, policies, seed=42)
    winner = decks[result.winner_index]
    print(
        f"Forge bridge smoke test OK: winner={winner.name!r}, "
        f"turns={result.turns}, seed={result.seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
