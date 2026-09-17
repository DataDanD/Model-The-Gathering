# Architecture notes

Model the Gathering separates four concerns:

1. **Card and deck data** normalize inputs and validate Commander lists.
2. **Policies** choose among actions without owning game rules.
3. **Simulation engines** execute games and return normalized `GameResult` records.
4. **Experiments** repeat games, rotate seats, aggregate statistics, and persist results.

This separation is intentional. Forge can provide high-fidelity rules while future fast simulators or learned policies can plug into the same experiment layer.
