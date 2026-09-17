from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from llmtg.decks.models import Deck
from llmtg.experiments.runner import ExperimentSummary
from llmtg.policies.base import PlayerPolicy


class SQLiteExperimentStore:
    """Persist experiment summaries and per-game seat assignments in SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    engine_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    rotate_seats INTEGER NOT NULL,
                    games INTEGER NOT NULL,
                    average_turns REAL NOT NULL,
                    deck_ids_json TEXT NOT NULL,
                    policy_ids_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS game_results (
                    experiment_id TEXT NOT NULL,
                    game_number INTEGER NOT NULL,
                    seed INTEGER NOT NULL,
                    winner_index INTEGER NOT NULL,
                    winning_deck_id TEXT NOT NULL,
                    turns INTEGER NOT NULL,
                    deck_ids_json TEXT NOT NULL,
                    policy_ids_json TEXT NOT NULL,
                    PRIMARY KEY (experiment_id, game_number),
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
                );
                """
            )

    def save_experiment(
        self,
        summary: ExperimentSummary,
        decks: Sequence[Deck],
        policies: Sequence[PlayerPolicy],
        *,
        engine_id: str,
        seed: int,
        rotate_seats: bool,
    ) -> str:
        if len(decks) != len(policies):
            raise ValueError("Each deck must have a corresponding policy")

        experiment_id = uuid4().hex
        original_deck_ids = [deck.deck_id for deck in decks]
        original_policy_ids = [policy.policy_id for policy in policies]

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO experiments (
                    experiment_id, engine_id, seed, rotate_seats, games,
                    average_turns, deck_ids_json, policy_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    engine_id,
                    seed,
                    int(rotate_seats),
                    summary.games,
                    summary.average_turns,
                    json.dumps(original_deck_ids),
                    json.dumps(original_policy_ids),
                ),
            )

            connection.executemany(
                """
                INSERT INTO game_results (
                    experiment_id, game_number, seed, winner_index,
                    winning_deck_id, turns, deck_ids_json, policy_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        experiment_id,
                        game_number,
                        result.seed,
                        result.winner_index,
                        result.deck_ids[result.winner_index],
                        result.turns,
                        json.dumps(result.deck_ids),
                        json.dumps(result.policy_ids),
                    )
                    for game_number, result in enumerate(summary.results)
                ],
            )

        return experiment_id

    def load_experiment(self, experiment_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            experiment = connection.execute(
                "SELECT * FROM experiments WHERE experiment_id = ?",
                (experiment_id,),
            ).fetchone()
            if experiment is None:
                return None

            games = connection.execute(
                """
                SELECT * FROM game_results
                WHERE experiment_id = ?
                ORDER BY game_number
                """,
                (experiment_id,),
            ).fetchall()

        return {
            "experiment": dict(experiment),
            "games": [dict(game) for game in games],
        }
