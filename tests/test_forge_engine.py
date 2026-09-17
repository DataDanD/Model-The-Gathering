from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

import pytest

from llmtg.decks.loader import parse_deck_text
from llmtg.policies.random_policy import RandomPolicy
from llmtg.simulation.forge import (
    ForgeConfigurationError,
    ForgeEngine,
    ForgeExecutionError,
)


def _deck(name: str):
    return parse_deck_text("1 Sol Ring", name=name)


@dataclass
class _Completed:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def test_forge_engine_translates_bridge_result_to_game_result() -> None:
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured["request"] = json.loads(kwargs["input"])
        return _Completed(
            stdout=json.dumps(
                {"protocol_version": 1, "winner_index": 1, "turns": 7}
            )
        )

    decks = [_deck("A"), _deck("B")]
    policies = [RandomPolicy(1), RandomPolicy(2)]
    engine = ForgeEngine(["forge-bridge"], runner=runner)

    result = engine.play_game(decks, policies, seed=99)

    assert captured["command"] == ["forge-bridge"]
    assert captured["request"]["seed"] == 99
    assert result.winner_index == 1
    assert result.turns == 7
    assert result.seed == 99
    assert result.deck_ids == tuple(deck.deck_id for deck in decks)


def test_forge_engine_reports_missing_executable() -> None:
    def runner(*args, **kwargs):
        raise FileNotFoundError("nope")

    engine = ForgeEngine(["missing-forge"], runner=runner)

    with pytest.raises(ForgeConfigurationError, match="not found"):
        engine.play_game(
            [_deck("A"), _deck("B")],
            [RandomPolicy(1), RandomPolicy(2)],
            seed=1,
        )


def test_forge_engine_reports_nonzero_exit() -> None:
    def runner(*args, **kwargs):
        return _Completed(returncode=3, stderr="Forge exploded")

    engine = ForgeEngine(["forge"], runner=runner)

    with pytest.raises(ForgeExecutionError, match="Forge exploded"):
        engine.play_game(
            [_deck("A"), _deck("B")],
            [RandomPolicy(1), RandomPolicy(2)],
            seed=1,
        )


def test_forge_engine_reports_timeout() -> None:
    def runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="forge", timeout=2)

    engine = ForgeEngine(["forge"], timeout_seconds=2, runner=runner)

    with pytest.raises(ForgeExecutionError, match="timed out"):
        engine.play_game(
            [_deck("A"), _deck("B")],
            [RandomPolicy(1), RandomPolicy(2)],
            seed=1,
        )


def test_forge_engine_rejects_invalid_json() -> None:
    def runner(*args, **kwargs):
        return _Completed(stdout="not-json")

    engine = ForgeEngine(["forge"], runner=runner)

    with pytest.raises(ForgeExecutionError, match="invalid JSON"):
        engine.play_game(
            [_deck("A"), _deck("B")],
            [RandomPolicy(1), RandomPolicy(2)],
            seed=1,
        )
