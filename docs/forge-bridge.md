# Forge bridge

`ForgeEngine` is the Python-side seam between Model the Gathering and a future Forge/Java rules-engine integration.

## Why a bridge

The experiment runner should not know how Forge is installed, launched, or implemented. It sends one game request to an external process and receives one structured result. That process can later be a Java CLI, a thin wrapper around Forge, or another local service without changing experiment code.

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

## Local smoke test

No Forge installation is required to validate the subprocess plumbing. The development stub implements protocol v1 but chooses a fake deterministic winner rather than simulating Magic.

```bash
python scripts/run_forge_stub.py
```

Expected output resembles:

```text
Forge bridge smoke test OK: winner='goreclaw', turns=..., seed=42
```

The exact winner/turn count is deterministic for a given seed but is not a Magic result.

## What this PR does not do

- install or bundle Forge
- start a real Forge Commander game
- translate `PlayerPolicy.choose_action` calls into in-game Forge decisions
- expose Forge game states or legal actions to Python

Those are deliberately the next layer. The current seam first proves that experiments can talk to an external high-fidelity engine through a stable, versioned contract.
