# Forge bridge

`ForgeEngine` is the Python-side seam between Model the Gathering and the Forge/Java rules engine.

## Why a bridge

The experiment runner should not know how Forge is installed, launched, or implemented. It sends one game request to an external process and receives one structured result. That process can be a Java CLI, a thin wrapper around Forge, or another local service without changing experiment code.

## Protocol v1

The bridge reads one JSON object from stdin:

```json
{
  "protocol_version": 1,
  "seed": 42,
  "players": [
    {
      "seat": 0,
      "policy_id": "random-v1",
      "deck": {
        "deck_id": "...",
        "name": "Goreclaw",
        "commanders": [{"name": "Goreclaw, Terror of Qal Sisma", "quantity": 1}],
        "mainboard": [{"name": "Forest", "quantity": 30}]
      }
    }
  ]
}
```

It writes exactly one JSON object to stdout:

```json
{
  "protocol_version": 1,
  "winner_index": 0,
  "turns": 9
}
```

Diagnostic text belongs on stderr so stdout remains machine-readable.

## Runtime configuration

Model the Gathering now keeps Forge installation details in `ForgeRuntimeConfig`. The preferred variables are:

```text
LLMTG_JAVA=java
LLMTG_FORGE_HOME=D:/code/forge
LLMTG_FORGE_JAR=
LLMTG_FORGE_WORKING_DIR=
LLMTG_FORGE_BRIDGE=scripts/forge_bridge_stub.py
```

When `LLMTG_FORGE_HOME` points to a Card-Forge/forge source checkout, llmtg recognizes the checkout from its Maven root and core modules. It also attempts to find a built desktop JAR under `forge-gui-desktop/target` and uses `forge-gui` as the working directory when present.

The older donor variables `FORGE_JAR_PATH` and `FORGE_WORKING_DIR` remain accepted as migration aliases, but new configuration should use the `LLMTG_` names.

## Forge doctor

Run the diagnostic before wiring a real bridge:

```bash
python scripts/forge_doctor.py --forge-home D:/code/forge
```

Or configure the environment first and run:

```bash
python scripts/forge_doctor.py
```

The required checks are Java and a recognizable Forge source checkout. Built desktop JAR, working directory, and bridge status are reported separately because a source checkout may not have been built yet and the real llmtg bridge is the next integration layer.

For automation/debugging:

```bash
python scripts/forge_doctor.py --forge-home D:/code/forge --json
```

## Local bridge smoke test

No Forge installation is required to validate the subprocess protocol itself. The development stub implements protocol v1 but chooses a fake deterministic winner rather than simulating Magic.

```bash
python scripts/run_forge_stub.py
```

Expected output resembles:

```text
Forge bridge smoke test OK: winner='goreclaw', turns=..., seed=42
```

The exact winner/turn count is deterministic for a given seed but is not a Magic result.

## Current boundary

- `ForgeRuntimeConfig` identifies the Java executable, Forge checkout, desktop JAR, working directory, and bridge.
- `ForgeEngine.from_runtime_config(...)` converts that configuration into the subprocess-backed simulation engine.
- protocol v1 transports decks, seats, policies, seed, winner, and turn count.
- the next layer is the actual Java-side bridge that starts a headless/automated Forge Commander game and returns a real result.

`policy_id` is metadata in protocol v1. The bridge does not yet call back into Python `PlayerPolicy.choose_action`; exposing real Forge game states and legal actions is a later protocol version.
