# GenAI agents (Mosaic AI Agent Framework)
Build AFTER gold is solid. Each agent reads gold/docs only, is served as a Model Serving
endpoint, and ships with an MLflow Agent Evaluation harness.

- `claims_fnol_copilot/`   — crash signal → assemble context → draft First Notice of Loss
- `underwriting_copilot/`  — new quote → explainable premium citing the policy-form PDF
- `fleet_ops_genie/`       — natural-language Q&A across the whole mesh (Genie Space + tools)

Build order: Claims FNOL Copilot first.
