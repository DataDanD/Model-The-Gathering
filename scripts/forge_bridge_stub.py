"""Development-only stand-in for the future Java/Forge bridge.

Reads one protocol-v1 JSON game request from stdin and returns a deterministic
fake result. It proves subprocess wiring only; it does not simulate Magic.
"""

from __future__ import annotations

import json
import random
import sys

PROTOCOL_VERSION = 1


def main() -> int:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid request JSON: {exc}"}), file=sys.stderr)
        return 2

    if request.get("protocol_version") != PROTOCOL_VERSION:
        print("unsupported protocol version", file=sys.stderr)
        return 2

    players = request.get("players")
    seed = request.get("seed")
    if not isinstance(players, list) or len(players) < 2 or not isinstance(seed, int):
        print("invalid players or seed", file=sys.stderr)
        return 2

    rng = random.Random(seed)
    response = {
        "protocol_version": PROTOCOL_VERSION,
        "winner_index": rng.randrange(len(players)),
        "turns": rng.randint(4, 15),
    }
    json.dump(response, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
