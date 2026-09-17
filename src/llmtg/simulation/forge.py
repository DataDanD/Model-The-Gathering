from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from llmtg.decks.models import Deck
from llmtg.policies.base import PlayerPolicy
from llmtg.simulation.engine import SimulationEngine
from llmtg.simulation.forge_protocol import (
    ForgeProtocolError,
    build_game_request,
    parse_game_response,
)
from llmtg.simulation.forge_runtime import ForgeRuntimeConfig
from llmtg.simulation.result import GameResult


class ForgeConfigurationError(RuntimeError):
    """Raised when the configured Forge bridge cannot be started."""


class ForgeExecutionError(RuntimeError):
    """Raised when the Forge bridge starts but cannot complete a game."""


class CompletedProcessLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[..., CompletedProcessLike]


@dataclass(slots=True)
class ForgeEngine(SimulationEngine):
    """Simulation engine that delegates one game to an external Forge bridge.

    The bridge reads one JSON request from stdin and writes one JSON response to
    stdout. This keeps Forge/Java integration behind a stable Python contract.
    """

    command: Sequence[str]
    timeout_seconds: float = 120.0
    working_dir: str | Path | None = None
    runner: Runner = subprocess.run

    engine_id = "forge-bridge-v1"

    def __post_init__(self) -> None:
        self.command = tuple(self.command)
        if not self.command:
            raise ForgeConfigurationError("Forge bridge command cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if self.working_dir is not None:
            self.working_dir = Path(self.working_dir).expanduser().resolve()

    @classmethod
    def from_runtime_config(
        cls,
        config: ForgeRuntimeConfig,
        *,
        timeout_seconds: float = 120.0,
        runner: Runner = subprocess.run,
    ) -> "ForgeEngine":
        command = config.bridge_command()
        if command is None:
            raise ForgeConfigurationError(
                "No Forge bridge configured; set LLMTG_FORGE_BRIDGE"
            )
        return cls(
            command=command,
            timeout_seconds=timeout_seconds,
            working_dir=config.working_dir,
            runner=runner,
        )

    def play_game(
        self,
        decks: Sequence[Deck],
        policies: Sequence[PlayerPolicy],
        *,
        seed: int,
    ) -> GameResult:
        request_payload = build_game_request(decks, policies, seed=seed)

        try:
            completed = self.runner(
                list(self.command),
                input=json.dumps(request_payload),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                cwd=str(self.working_dir) if self.working_dir is not None else None,
            )
        except FileNotFoundError as exc:
            raise ForgeConfigurationError(
                f"Forge bridge executable was not found: {self.command[0]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ForgeExecutionError(
                f"Forge bridge timed out after {self.timeout_seconds:g} seconds"
            ) from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "no stderr output"
            raise ForgeExecutionError(
                f"Forge bridge exited with code {completed.returncode}: {stderr}"
            )

        stdout = completed.stdout.strip()
        if not stdout:
            raise ForgeExecutionError("Forge bridge returned no JSON response")

        try:
            response_payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ForgeExecutionError(
                f"Forge bridge returned invalid JSON: {stdout[:200]!r}"
            ) from exc

        try:
            winner_index, turns = parse_game_response(
                response_payload,
                player_count=len(decks),
            )
        except ForgeProtocolError as exc:
            raise ForgeExecutionError(f"Invalid Forge bridge response: {exc}") from exc

        return GameResult(
            winner_index=winner_index,
            turns=turns,
            seed=seed,
            deck_ids=tuple(deck.deck_id for deck in decks),
            policy_ids=tuple(policy.policy_id for policy in policies),
        )
