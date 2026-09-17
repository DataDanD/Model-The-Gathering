from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from llmtg.simulation.forge_runtime import (
    ForgeRuntimeConfig,
    required_checks_pass,
    run_forge_doctor,
)


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

    env = dict(os.environ)
    overrides = {
        "LLMTG_FORGE_HOME": args.forge_home,
        "LLMTG_FORGE_JAR": args.forge_jar,
        "LLMTG_FORGE_WORKING_DIR": args.working_dir,
        "LLMTG_FORGE_BRIDGE": args.bridge,
        "LLMTG_JAVA": args.java,
    }
    for key, value in overrides.items():
        if value:
            env[key] = value

    config = ForgeRuntimeConfig.from_environment(env)
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

        desktop_command = config.forge_desktop_command()
        if desktop_command is not None:
            print("Forge desktop command:", " ".join(desktop_command))
        bridge_command = config.bridge_command()
        if bridge_command is not None:
            print("Bridge command:", " ".join(bridge_command))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
