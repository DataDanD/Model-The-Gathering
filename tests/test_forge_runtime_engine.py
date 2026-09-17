from __future__ import annotations

from pathlib import Path

import pytest

from llmtg.simulation.forge import ForgeConfigurationError, ForgeEngine
from llmtg.simulation.forge_runtime import ForgeRuntimeConfig


def test_engine_from_runtime_config_uses_bridge_and_working_dir(tmp_path: Path) -> None:
    bridge = tmp_path / "bridge.py"
    bridge.write_text("", encoding="utf-8")
    working_dir = tmp_path / "forge-gui"
    working_dir.mkdir()

    config = ForgeRuntimeConfig(
        bridge_path=bridge,
        working_dir=working_dir,
    )

    engine = ForgeEngine.from_runtime_config(config)

    assert engine.command[-1] == str(bridge)
    assert engine.working_dir == working_dir.resolve()


def test_engine_from_runtime_config_requires_bridge() -> None:
    with pytest.raises(ForgeConfigurationError, match="LLMTG_FORGE_BRIDGE"):
        ForgeEngine.from_runtime_config(ForgeRuntimeConfig())
