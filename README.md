# DrivePulse Lakehouse

A usage-based auto-insurance (UBI) **data mesh** on Azure Databricks — built end-to-end with
streaming telematics, batch policy/claims data, lakehouse federation, Lakeflow declarative
pipelines, Unity Catalog governance, and a set of **GenAI agents** on top.

> **Honesty note:** this project uses *real public datasets* that are *synthetically linked*
> with deterministic keys (no public dataset connects telematics → policy → claims). The
> live vehicle stream is simulated by replaying real trip data into Event Hubs at 50–100×.
> Both are standard portfolio-demo practices and are called out explicitly throughout.

## Architecture at a glance

Three domain teams, three Unity Catalog catalogs, medallion inside each, agents on gold:

```
prod_telematics  (IoT team)        prod_policy  (Underwriting)     prod_claims  (Claims Ops)
  bronze/silver/gold/docs            bronze/silver/gold/docs         bronze/silver/gold/docs
        │                                   │                              │
        └──────────── three-part-name reads (the mesh) ────────────────────┘
                                   │
                         GenAI agents (Mosaic AI) — gold/docs only
```

- **Streaming:** Event Hubs → Structured Streaming → telematics bronze
- **Batch:** Auto Loader (`cloudFiles`) for policies, claims, recalls
- **Federation:** weather (Postgres), vPIC (Postgres/SQL Server), OSM (PostGIS) — queried, not ingested
- **Silver:** Lakeflow Declarative Pipelines with expectations + quarantine; SCD2 + CDC
- **Gold:** Kimball star schemas per domain + cross-domain marts (`mart_claim_360`, etc.)
- **Governance:** UC row filters (per-insurer tenancy), column masks (PII), tags, lineage

Full detail lives in [`CLAUDE.md`](./CLAUDE.md) and [`docs/architecture.md`](./docs/architecture.md).

---

## SETUP — do this once before running Claude Code

### 1. Tools
```bash
# Databricks CLI (macOS/Linux)
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
databricks --version
# Windows: winget install Databricks.DatabricksCLI
```

### 2. Generate a Databricks Personal Access Token (PAT)
1. Open your Azure Databricks workspace in the browser.
2. Top-right → your name → **Settings**.
3. **Developer** → **Access tokens** → **Manage** → **Generate new token**.
4. Comment: `claude-code-dev`. Lifetime: e.g. 90 days. **Generate**.
5. **Copy it now** — you can't see it again.

> A PAT is valid for one workspace only, up to 600 per workspace, and is auto-revoked after
> 90 days of non-use. OAuth (`databricks auth login`) is the more secure alternative if you
> prefer it.

### 3. Create a CLI profile (the token is stored in `~/.databrickscfg`, never in this repo)
```bash
databricks configure --profile drivepulse
# Databricks Host: https://adb-XXXXXXXXXXXXXXXX.0.azuredatabricks.net
# Personal Access Token: <paste the PAT>

# verify
databricks auth describe --profile drivepulse
```

### 4. Point the bundle at your workspace
Edit `databricks.yml` → replace both `host:` values (`adb-REPLACE_ME...`) with your real
workspace URL. The CLI matches that host to the `drivepulse` profile automatically.

### 5. First validate
```bash
databricks bundle validate -t dev
```

### 6. GitHub Actions secrets (for CI/CD)
In the repo: **Settings → Secrets and variables → Actions** → add
`DATABRICKS_HOST` and `DATABRICKS_TOKEN`.

### 7. Local Python (for the download / replay scripts)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values; .env is gitignored
```

---

## Then: hand it to Claude Code (Max account)

```bash
cd drivepulse-lakehouse
claude
```
Paste the contents of [`FIRST_TASK.md`](./FIRST_TASK.md) as your first prompt. Claude Code
reads `CLAUDE.md`, then builds the telematics vertical slice first, then the rest.

## Deploy commands
```bash
databricks bundle validate -t dev
databricks bundle deploy   -t dev
databricks bundle run bootstrap_uc -t dev
```

## Repo layout
See [`CLAUDE.md` §8](./CLAUDE.md). Datasets & links: [`docs/datasets.md`](./docs/datasets.md).
