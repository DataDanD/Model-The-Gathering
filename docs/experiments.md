# Experiment conventions

Every experiment should be reproducible enough to answer three questions later: which decks played, which policies piloted them, and which random seeds were used.

Prefer seat rotation for multiplayer comparisons. Record deck fingerprints rather than relying on mutable display names, and keep engine identity with persisted results so Forge, mock, and future fast-engine results are not accidentally mixed.
