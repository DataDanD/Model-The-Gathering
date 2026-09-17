# Contributing

Model the Gathering is an experimental Commander simulation and research toolkit.

## Local setup

```bash
pip install -e ".[dev]"
pytest
```

Keep active code under `src/llmtg/`. Code under `archive/` is reference material only and should not be imported by active modules.

## Pull requests

Prefer small PRs with one clear purpose. Include tests for behavior changes and document any new local setup steps or external dependencies.
