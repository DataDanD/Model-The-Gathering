from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence


class CompletedProcessLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    name: str
    ok: bool
    detail: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ForgeRuntimeConfig:
    """Local configuration needed to launch or bridge into Forge."""

    java_executable: str = "java"
    forge_home: Path | None = None
    forge_jar: Path | None = None
    working_dir: Path | None = None
    bridge_path: Path | None = None

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "ForgeRuntimeConfig":
        env = os.environ if environ is None else environ

        forge_home = _optional_path(env.get("LLMTG_FORGE_HOME"))
        forge_jar = _optional_path(
            env.get("LLMTG_FORGE_JAR") or env.get("FORGE_JAR_PATH")
        )
        working_dir = _optional_path(
            env.get("LLMTG_FORGE_WORKING_DIR") or env.get("FORGE_WORKING_DIR")
        )
        bridge_path = _optional_path(env.get("LLMTG_FORGE_BRIDGE"))

        if forge_home is not None:
            if working_dir is None:
                candidate = forge_home / "forge-gui"
                if candidate.is_dir():
                    working_dir = candidate
            if forge_jar is None:
                forge_jar = find_desktop_jar(forge_home)

        return cls(
            java_executable=env.get("LLMTG_JAVA", "java"),
            forge_home=forge_home,
            forge_jar=forge_jar,
            working_dir=working_dir,
            bridge_path=bridge_path,
        )

    def bridge_command(self) -> tuple[str, ...] | None:
        if self.bridge_path is None:
            return None
        suffix = self.bridge_path.suffix.lower()
        if suffix == ".py":
            return (sys.executable, str(self.bridge_path))
        if suffix == ".jar":
            return (self.java_executable, "-jar", str(self.bridge_path))
        return (str(self.bridge_path),)

    def forge_desktop_command(self) -> tuple[str, ...] | None:
        if self.forge_jar is None:
            return None
        return (self.java_executable, "-jar", str(self.forge_jar))


def _optional_path(value: str | None) -> Path | None:
    if value is None or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def looks_like_forge_source(path: Path) -> bool:
    """Recognize the current Card-Forge source-tree shape."""

    return (
        (path / "pom.xml").is_file()
        and (path / "forge-game").is_dir()
        and (path / "forge-ai").is_dir()
        and (path / "forge-gui-desktop").is_dir()
    )


def find_desktop_jar(forge_home: Path) -> Path | None:
    """Find a built Forge desktop JAR, preferring the self-contained fat JAR."""

    target = forge_home / "forge-gui-desktop" / "target"
    if not target.is_dir():
        return None

    patterns = (
        "forge-gui-desktop-*-jar-with-dependencies.jar",
        "forge-gui-desktop-*.jar",
    )
    for pattern in patterns:
        candidates = [
            path
            for path in target.glob(pattern)
            if path.is_file()
            and not path.name.endswith("-sources.jar")
            and not path.name.endswith("-javadoc.jar")
        ]
        if candidates:
            return max(candidates, key=lambda path: path.stat().st_mtime)

    return None


def run_forge_doctor(
    config: ForgeRuntimeConfig,
    *,
    runner=subprocess.run,
) -> tuple[DiagnosticCheck, ...]:
    checks: list[DiagnosticCheck] = []

    java_on_path = shutil.which(config.java_executable) is not None
    java_detail = f"executable={config.java_executable!r}"
    if java_on_path:
        try:
            completed: CompletedProcessLike = runner(
                [config.java_executable, "-version"],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            version_text = (completed.stderr or completed.stdout).strip().splitlines()
            if version_text:
                java_detail = version_text[0]
            java_on_path = completed.returncode == 0
        except (OSError, subprocess.SubprocessError) as exc:
            java_on_path = False
            java_detail = str(exc)
    checks.append(DiagnosticCheck("java", java_on_path, java_detail))

    if config.forge_home is None:
        checks.append(
            DiagnosticCheck(
                "forge_home",
                False,
                "Set LLMTG_FORGE_HOME to a Card-Forge/forge source checkout",
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                "forge_home",
                looks_like_forge_source(config.forge_home),
                str(config.forge_home),
            )
        )

    checks.append(
        DiagnosticCheck(
            "forge_jar",
            config.forge_jar is not None and config.forge_jar.is_file(),
            str(config.forge_jar) if config.forge_jar else "No built desktop JAR found/configured",
            required=False,
        )
    )

    checks.append(
        DiagnosticCheck(
            "working_dir",
            config.working_dir is not None and config.working_dir.is_dir(),
            str(config.working_dir) if config.working_dir else "No Forge working directory resolved",
            required=False,
        )
    )

    bridge_command = config.bridge_command()
    if bridge_command is None:
        checks.append(
            DiagnosticCheck(
                "bridge",
                False,
                "Set LLMTG_FORGE_BRIDGE to a Python script, JAR, or executable",
                required=False,
            )
        )
    else:
        bridge_exists = config.bridge_path is not None and config.bridge_path.is_file()
        checks.append(
            DiagnosticCheck(
                "bridge",
                bridge_exists,
                " ".join(bridge_command),
                required=False,
            )
        )

    return tuple(checks)


def required_checks_pass(checks: Sequence[DiagnosticCheck]) -> bool:
    return all(check.ok for check in checks if check.required)
