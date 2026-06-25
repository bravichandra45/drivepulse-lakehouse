# Claims domain → `prod_claims`
Owner: Claims Operations team. Primary ingestion: **Auto Loader** + **CDC**.
- bronze/ — claims/FNOL/payment landings
- silver/ — `claim_status_cdc.py` (FNOL→investigating→settled→closed history)
- gold/   — fact_claim, fact_claim_status_history, fact_claim_payment, **mart_claim_360** (cross-domain)
- docs/   — ODI complaint narratives for RAG
