# Databricks notebook source
# MAGIC %md
# MAGIC # Dynamic row-count validation (reusable across all domains)
# MAGIC
# MAGIC A single, config-driven notebook to validate table row counts anywhere in the lakehouse
# MAGIC (telematics / policy / claims · bronze / silver / gold). Three ways to call it — pick one:
# MAGIC
# MAGIC 1. **Expectations** — `expectations` = JSON `{ "<fqn>": <expected_rows>, ... }` → PASS/FAIL per table.
# MAGIC 2. **Table list** — `tables` = comma-separated fully-qualified names → reports counts (COUNT only).
# MAGIC 3. **Whole schema** — `catalog` + `schema` → counts every table in that schema (COUNT only).
# MAGIC
# MAGIC `fail_on_mismatch=true` raises (fails the job) if any expectation FAILs. Returns a JSON summary
# MAGIC via `dbutils.notebook.exit` so a caller can read the result programmatically.

# COMMAND ----------
# DBTITLE 1,Parameters
dbutils.widgets.text("expectations", "", "Expectations JSON {fqn: expected_rows}")
dbutils.widgets.text("tables", "", "Comma-separated FQNs (count-only)")
dbutils.widgets.text("catalog", "", "Catalog (+ schema => validate all tables)")
dbutils.widgets.text("schema", "", "Schema")
dbutils.widgets.text("fail_on_mismatch", "true", "Raise on any FAIL (true/false)")

# COMMAND ----------
# DBTITLE 1,Parse inputs
import json
from pyspark.sql import Row

expectations = {}
_raw = dbutils.widgets.get("expectations").strip()
if _raw:
    expectations = json.loads(_raw)

tables = [t.strip() for t in dbutils.widgets.get("tables").split(",") if t.strip()]
catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
fail_on_mismatch = dbutils.widgets.get("fail_on_mismatch").strip().lower() == "true"

# COMMAND ----------
# DBTITLE 1,Resolve targets -> {fqn: expected_or_None}
targets = {}
for fqn, exp in expectations.items():
    targets[fqn] = int(exp)
for fqn in tables:
    targets.setdefault(fqn, None)
if not targets and catalog and schema:
    for r in spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect():
        targets[f"{catalog}.{schema}.{r['tableName']}"] = None

if not targets:
    raise ValueError("Provide one of: 'expectations' JSON, 'tables' list, or 'catalog'+'schema'.")

# COMMAND ----------
# DBTITLE 1,Count + compare
results = []
for fqn, expected in targets.items():
    try:
        actual = spark.table(fqn).count()
        if expected is None:
            status = "COUNT"
        elif actual == expected:
            status = "PASS"
        else:
            status = "FAIL"
    except Exception as e:  # missing table / no access -> surfaced, not hidden
        actual, status = None, f"ERROR:{e.__class__.__name__}"
    results.append({"table": fqn, "expected": expected, "actual": actual, "status": status})

# COMMAND ----------
# DBTITLE 1,Report
display(spark.createDataFrame([Row(**r) for r in results]))
for r in results:
    print(f"{r['status']:>7}  {r['table']}  actual={r['actual']} expected={r['expected']}")

# COMMAND ----------
# DBTITLE 1,Summary + gate
fails = [r for r in results if not (r["status"] in ("PASS", "COUNT"))]
summary = {
    "total": len(results),
    "pass": sum(1 for r in results if r["status"] == "PASS"),
    "count_only": sum(1 for r in results if r["status"] == "COUNT"),
    "fail": len(fails),
    "results": results,
}
print(json.dumps(summary, indent=2))

if fail_on_mismatch and fails:
    raise Exception(f"Row-count validation FAILED for {len(fails)} table(s): {json.dumps(fails)}")

dbutils.notebook.exit(json.dumps(summary))
