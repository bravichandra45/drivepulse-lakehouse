# validation/

Reusable, cross-domain data-quality notebooks. Domain-agnostic — usable for
telematics / policy / claims at any medallion layer.

## `dynamic_row_count_validation.py`
Config-driven row-count check. Call it one of three ways via widgets / job parameters:

| Mode | Set | Behaviour |
|---|---|---|
| Expectations | `expectations` = `{"<fqn>": <rows>, ...}` (JSON) | PASS/FAIL each table vs expected |
| Table list | `tables` = `cat.sch.t1, cat.sch.t2` | reports counts (COUNT only) |
| Whole schema | `catalog` + `schema` | counts every table in the schema |

`fail_on_mismatch=true` (default) raises and fails the job on any FAIL. Returns a JSON
summary via `dbutils.notebook.exit`.

**Example — validate Claims bronze:**
```json
{
  "prod_claims.bronze.raw_insurance_claims": 1000,
  "prod_claims.bronze.raw_carclaims": 15420,
  "prod_claims.bronze.raw_claims_by_type": 7366,
  "prod_claims.bronze.raw_claim_severity": 26639
}
```
