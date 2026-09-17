# Forge local setup

Model the Gathering treats Forge as an external high-fidelity rules engine.

A local setup normally needs:

- a Card-Forge/forge checkout
- a Java runtime compatible with the Forge build
- Maven for building Forge from source
- `LLMTG_FORGE_HOME` pointing at the checkout

Use the runtime diagnostic before attempting bridge work:

```bash
python scripts/forge_doctor.py
```

The doctor reports Java, Forge checkout, desktop JAR, working-directory, and bridge status independently so environment problems are visible before simulation code runs.
