from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

from llmtg.simulation.forge_runtime import (
    ForgeRuntimeConfig,
    required_checks_pass,
    run_forge_doctor,
)


def _path(value: str | None) -> Path | None:
    return Path(value).expanduser().resolve() if value else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the local Java/Forge runtime used by Model the Gathering."
    )
    parser.add_argument("--forge-home", help="Card-Forge/forge source checkout")
    parser.add_argument("--forge-jar", help="Built forge-gui-desktop JAR")
    parser.add_argument("--working-dir", help="Forge working directory, usually forge-gui")
    parser.add_argument("--bridge", help="Forge bridge Python script, JAR, or executable")
    parser.add_argument("--java", help="Java executable name/path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    config = ForgeRuntimeConfig.from_environment()
    config = replace(
        config,
        java_executable=args.java or config.java_executable,
        forge_home=_path(args.forge_home) if args.forge_home else config.forge_home,
        forge_jar=_path(args.forge_jar) if args.forge_jar else config.forge_jar,
        working_dir=_path(args.working_dir) if args.working_dir else config.working_dir,
        bridge_path=_path(args.bridge) if args.bridge else config.bridge_path,
    )

    checks = run_forge_doctor(config)
    ok = required_checks_pass(checks)

    if args.json:
        print(
            json.dumps(
                {
                    "ok": ok,
                    "checks": [asdict(check) for check in checks],
                    "forge_desktop_command": config.forge_desktop_command(),
                    "bridge_command": config.bridge_command(),
                },
                indent=2,
            )
        )
    else:
        print("Model the Gathering - Forge doctor")
        for check in checks:
            marker = "OK" if check.ok else ("FAIL" if check.required else "INFO")
            print(f"[{marker:4}] {check.name:12} {check.detail}")

        if ok:
            print("\nRequired runtime checks passed.")
        else:
            print("\nRequired runtime checks failed. Fix the FAIL items above.")

        if config.forge_desktop_command() is not None:
            print("Forge desktop command:", " ".join(config.forge_desktop_command() or ()))
        if config.bridge_command() is not None:
            print("Bridge command:", " ".join(config.bridge_command() or ()))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
