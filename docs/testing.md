# Testing

Run the full offline suite with:

```bash
pytest
```

Tests should avoid network access unless explicitly marked as integration tests. External systems such as Scryfall and Forge should be exercised through injected fakes or local smoke scripts where practical.

Useful smoke checks:

```bash
python scripts/validate_deck.py decks/goreclaw.txt
python scripts/run_forge_stub.py
python scripts/forge_doctor.py
```
