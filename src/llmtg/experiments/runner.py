from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from llmtg.decks.models import Deck
from llmtg.policies.base import PlayerPolicy
from llmtg.simulation.engine import SimulationEngine
from llmtg.simulation.result import GameResult


@dataclass(frozen=True, slots=True)
class ExperimentSummary:
    games: int
    wins_by_deck: dict[str, int]
    win_rates_by_deck: dict[str, float]
    average_turns: float
    results: tuple[GameResult, ...]


def run_experiment(
    engine: SimulationEngine,
    decks: Sequence[Deck],
    policies: Sequence[PlayerPolicy],
    *,
    games: int,
    seed: int = 1,
) -> ExperimentSummary:
    if games < 1:
        raise ValueError("games must be at least 1")
    if len(decks) != len(policies):
        raise ValueError("Each deck must have a corresponding policy")

    results = tuple(
        engine.play_game(decks, policies, seed=seed + game_number)
        for game_number in range(games)
    )

    wins = Counter(result.deck_ids[result.winner_index] for result in results)
    wins_by_deck = {deck.deck_id: wins.get(deck.deck_id, 0) for deck in decks}
    win_rates = {
        deck_id: win_count / games
        for deck_id, win_count in wins_by_deck.items()
    }
    average_turns = sum(result.turns for result in results) / games

    return ExperimentSummary(
        games=games,
        wins_by_deck=wins_by_deck,
        win_rates_by_deck=win_rates,
        average_turns=average_turns,
        results=results,
    )
