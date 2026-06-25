# FIRST_TASK.md — paste this as your first prompt to Claude Code

You are working in the DrivePulse Lakehouse repo. Before doing anything, read `CLAUDE.md`
in full — it is the source of truth for architecture, the three-catalog mesh, conventions,
patterns, and build order. Also skim `README.md`, `databricks.yml`, and everything under
`resources/` and `docs/`.

## Your first session: prove the telematics vertical slice end-to-end

Do NOT build all three domains at once. Build one domain fully first so the pattern is
proven, then we replicate. Work in this order and stop for my review after step 5.

1. **Confirm setup.** Run `databricks bundle validate -t dev`. If it fails, tell me exactly
   what's missing (most likely the `host:` in `databricks.yml` still says REPLACE_ME).

2. **Bootstrap Unity Catalog.** Finish `src/drivepulse/common/bootstrap_uc.py` so it creates
   the three catalogs and the bronze/silver/gold/docs schemas idempotently, with comments and
   sensible grants. Deploy and run the `bootstrap_uc` job on `dev`.

3. **Get the data.** Implement `ingestion/seed_data/download_datasets.py` for the telematics
   source (Vehicle Energy Dataset / Extended VED) per `docs/datasets.md`. Land it to ADLS /
   a bronze landing path. Aim for ≥ 50k rows.

4. **Stream it.** Implement `ingestion/eventhubs_simulator/replay_telemetry.py` (replay VED
   into Event Hubs at 50×, reading the connection string from a secret scope) and
   `domains/telematics/bronze/stream_telemetry_bronze.py` (Structured Streaming → bronze Delta,
   checkpointed, append-only).

5. **Silver + gold for telematics only.** Implement the Lakeflow pipeline
   (`trip_sessionization.py` with expectations + quarantine, `dim_driver_scd2.py` via
   `apply_changes` SCD2) and `gold/build_fact_trip.py`. Then **stop and show me**:
   - `fact_trip` row count and a sample,
   - the quarantine table,
   - the Lakeflow pipeline graph.

## Rules (from CLAUDE.md — re-read if unsure)
- Never hardcode catalog names, hosts, tokens, or connection strings. Use bundle variables
  and secret scopes.
- Cross-domain reads are three-part-name only; never copy another domain's data.
- Quarantine failed rows, never drop silently.
- Write an ADR in `docs/adr/` for any architecture decision you make.
- Keep clusters tiny / serverless — this is a trial workspace.
- Notebooks stay as `.py` (Databricks source format) for clean git diffs.

When step 5 is reviewed and good, the next sessions are: Policy domain, Claims domain,
federation sources, UC governance (row filters + column masks), `docs` + Vector Search, then
the agents (start with Claims FNOL Copilot) with MLflow Agent Evaluation.
