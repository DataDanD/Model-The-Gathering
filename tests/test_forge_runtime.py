from __future__ import annotations

import sys
from pathlib import Path

import pytest

from llmtg.simulation import forge_runtime
from llmtg.simulation.forge_runtime import (
    ForgeRuntimeConfig,
    find_desktop_jar,
    looks_like_forge_source,
    required_checks_pass,
    run_forge_doctor,
)


def _make_forge_tree(root: Path) -> None:
    (root / "pom.xml").write_text("<project />", encoding="utf-8")
    for directory in ("forge-game", "forge-ai", "forge-gui-desktop", "forge-gui"):
        (root / directory).mkdir(parents=True, exist_ok=True)


def test_runtime_config_discovers_jar_and_working_dir(tmp_path: Path) -> None:
    _make_forge_tree(tmp_path)
    target = tmp_path / "forge-gui-desktop" / "target"
    target.mkdir()
    jar = target / "forge-gui-desktop-2.0.14-SNAPSHOT-jar-with-dependencies.jar"
    jar.write_text("fake", encoding="utf-8")

    config = ForgeRuntimeConfig.from_environment({"LLMTG_FORGE_HOME": str(tmp_path)})

    assert config.forge_home == tmp_path.resolve()
    assert config.forge_jar == jar.resolve()
    assert config.working_dir == (tmp_path / "forge-gui").resolve()
    assert config.forge_desktop_command() == ("java", "-jar", str(jar.resolve()))


def test_runtime_config_accepts_legacy_commander_lab_names(tmp_path: Path) -> None:
    jar = tmp_path / "forge.jar"
    workdir = tmp_path / "forge-gui"
    jar.write_text("fake", encoding="utf-8")
    workdir.mkdir()

    config = ForgeRuntimeConfig.from_environment(
        {
            "FORGE_JAR_PATH": str(jar),
            "FORGE_WORKING_DIR": str(workdir),
        }
    )

    assert config.forge_jar == jar.resolve()
    assert config.working_dir == workdir.resolve()


def test_bridge_command_uses_python_for_python_script(tmp_path: Path) -> None:
    bridge = tmp_path / "bridge.py"
    bridge.write_text("print('hi')", encoding="utf-8")

    config = ForgeRuntimeConfig(bridge_path=bridge)

    assert config.bridge_command() == (sys.executable, str(bridge))


def test_bridge_command_uses_java_for_jar(tmp_path: Path) -> None:
    bridge = tmp_path / "bridge.jar"
    bridge.write_text("fake", encoding="utf-8")

    config = ForgeRuntimeConfig(java_executable="java17", bridge_path=bridge)

    assert config.bridge_command() == ("java17", "-jar", str(bridge))


def test_find_desktop_jar_prefers_fat_jar(tmp_path: Path) -> None:
    target = tmp_path / "forge-gui-desktop" / "target"
    target.mkdir(parents=True)
    ordinary = target / "forge-gui-desktop-2.0.14.jar"
    fat = target / "forge-gui-desktop-2.0.14-jar-with-dependencies.jar"
    ordinary.write_text("ordinary", encoding="utf-8")
    fat.write_text("fat", encoding="utf-8")

    assert find_desktop_jar(tmp_path) == fat


def test_looks_like_current_forge_source_tree(tmp_path: Path) -> None:
    assert not looks_like_forge_source(tmp_path)
    _make_forge_tree(tmp_path)
    assert looks_like_forge_source(tmp_path)


def test_doctor_reports_required_java_and_source_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_forge_tree(tmp_path)
    monkeypatch.setattr(forge_runtime.shutil, "which", lambda _: "/fake/java")

    class Result:
        returncode = 0
        stdout = ""
        stderr = 'openjdk version "21.0.1"'

    def runner(*args, **kwargs):  # noqa: ANN002, ANN003
        return Result()

    checks = run_forge_doctor(
        ForgeRuntimeConfig(java_executable="java", forge_home=tmp_path),
        runner=runner,
    )

    assert required_checks_pass(checks)
    assert {check.name: check.ok for check in checks}["java"] is True
    assert {check.name: check.ok for check in checks}["forge_home"] is True


def test_doctor_fails_when_forge_home_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forge_runtime.shutil, "which", lambda _: "/fake/java")

    class Result:
        returncode = 0
        stdout = ""
        stderr = 'openjdk version "21"'

    checks = run_forge_doctor(
        ForgeRuntimeConfig(),
        runner=lambda *args, **kwargs: Result(),  # noqa: ARG005
    )

    assert not required_checks_pass(checks)
