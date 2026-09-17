# Deck text format

The lightweight deck loader accepts section headings followed by `quantity card name` lines.

```text
Commander
1 Talrand, Sky Summoner

Deck
36 Island
1 Sol Ring
```

Blank lines and lines beginning with `#` are ignored. The parser is intentionally simple; provider-backed validation handles card existence, color identity, legality, and Commander deck constraints separately.
