# Policy domain → `prod_policy`
Owner: Underwriting team. Primary ingestion: **Auto Loader** (batch CSV/JSON).
Also owns vehicle reference (vPIC) as reference tables or federation.
- bronze/ — policy/endorsement/vehicle-ref landings
- silver/ — `dim_policy_scd2.py`, `endorsements_cdc.py`
- gold/   — fact_policy_inforce_monthly, fact_policy_transaction, dim_coverage
- docs/   — state DOI sample policy forms for RAG
