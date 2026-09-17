from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt

from llmtg.decks.models import Deck
from llmtg.policies.base import PlayerPolicy
from llmtg.simulation.engine import SimulationEngine
from llmtg.simulation.result import GameResult


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class ExperimentSummary:
    games: int
    wins_by_deck: dict[str, int]
    win_rates_by_deck: dict[str, float]
    confidence_intervals_by_deck: dict[str, ConfidenceInterval]
    average_turns: float
    results: tuple[GameResult, ...]


def wilson_interval(wins: int, games: int, *, z: float = 1.96) -> ConfidenceInterval:
    """Return a Wilson score interval for a binomial proportion."""
    if games < 1:
        raise ValueError("games must be at least 1")
    if not 0 <= wins <= games:
        raise ValueError("wins must be between 0 and games")

    proportion = wins / games
    z2 = z * z
    denominator = 1 + z2 / games
    center = (proportion + z2 / (2 * games)) / denominator
    margin = (
        z
        * sqrt((proportion * (1 - proportion) / games) + (z2 / (4 * games * games)))
        / denominator
    )
    return ConfidenceInterval(low=max(0.0, center - margin), high=min(1.0, center + margin))


def _rotate[T](items: Sequence[T], offset: int) -> tuple[T, ...]:
    if not items:
        return ()
    shift = offset % len(items)
    return tuple(items[shift:]) + tuple(items[:shift])


def run_experiment(
    engine: SimulationEngine,
    decks: Sequence[Deck],
    policies: Sequence[PlayerPolicy],
    *,
    games: int,
    seed: int = 1,
    rotate_seats: bool = True,
) -> ExperimentSummary:
    if games < 1:
        raise ValueError("games must be at least 1")
    if len(decks) != len(policies):
        raise ValueError("Each deck must have a corresponding policy")
    if not decks:
        raise ValueError("At least one deck is required")

    results: list[GameResult] = []
    for game_number in range(games):
        offset = game_number if rotate_seats else 0
        game_decks = _rotate(decks, offset)
        game_policies = _rotate(policies, offset)
        results.append(
            engine.play_game(game_decks, game_policies, seed=seed + game_number)
        )

    result_tuple = tuple(results)
    wins = Counter(result.deck_ids[result.winner_index] for result in result_tuple)
    wins_by_deck = {deck.deck_id: wins.get(deck.deck_id, 0) for deck in decks}
    win_rates = {
        deck_id: win_count / games
        for deck_id, win_count in wins_by_deck.items()
    }
    confidence_intervals = {
        deck_id: wilson_interval(win_count, games)
        for deck_id, win_count in wins_by_deck.items()
    }
    average_turns = sum(result.turns for result in result_tuple) / games

    return ExperimentSummary(
        games=games,
        wins_by_deck=wins_by_deck,
        win_rates_by_deck=win_rates,
        confidence_intervals_by_deck=confidence_intervals,
        average_turns=average_turns,
        results=result_tuple,
    )
