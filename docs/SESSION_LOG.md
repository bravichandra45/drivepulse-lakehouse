# SESSION_LOG — DrivePulse Lakehouse

> Append-only narrative log of work sessions. Newest entry at the bottom.
> `PROJECT_STATE.md` stays the short "where we are now" file — this is the long-form history.

---

## 2026-06-26 · Session 3 — Environment setup & infra analysis

**Goal:** Adopt Option 1 (Claude drives via authenticated CLIs; user provides browser logins).
Review current state across repo + GitHub + Azure + Databricks, wire everything up, keep docs current.

### Tooling installed (via winget)
Machine had only `git` + a Python stub. Installed:
- GitHub CLI `gh` 2.95.0
- Azure CLI `az` 2.87.0
- Databricks CLI 1.5.0
- Python 3.11.9

### Authentication — all three surfaces wired
- **Azure** ✅ — device-code login (completed in Chrome). Account
  `balantrapu.ravichandra@gmail.com`, "Azure subscription 1" (`93a8c829…`), tenant `2bb692f9…`. Admin.
- **GitHub** ✅ — `gh auth login` as `bravichandra45`; token in Windows keyring;
  scopes `repo`, `workflow`, `read:org`, `gist`.
- **Databricks** ✅ — `~/.databrickscfg` profile `drivepulse` using `auth_type = azure-cli`
  (reuses the az token — no PAT, no workspace browser login). User is a workspace **admin**
  (allow-cluster-create).

**Learnings:**
- Browser/device login flows are flaky in this sandboxed setup; azure-cli passthrough is the
  reliable path for Databricks.
- Claude's shell commands run **sandboxed without network** by default; cloud-touching calls
  (az/databricks/gh against their APIs) need the sandbox disabled per-invocation.
- `DATABRICKS_CONFIG_PROFILE=drivepulse` is set in `.claude/settings.json`, so the profile must
  be named `drivepulse` (not `DEFAULT`).

### Infrastructure analysis (verified via `az`)
**Workspace (exists, healthy):** `databricks_mission_2026_dataai` · premium · East US ·
state Succeeded · URL `adb-7405605467002690.10.azuredatabricks.net`.

**Resource group `rg_mission_2026_dataai` inventory:**

| Resource | Type | Region | Ours? |
|---|---|---|---|
| `databricks_mission_2026_dataai` | Databricks workspace | eastus | yes |
| `adls4missiondataai` | ADLS Gen2 storage | eastus | yes — our lake |
| `adls_connect_databricks` | Databricks access connector | eastus | yes — UC→ADLS identity |
| `adls_connect_databricks_finanace` | Databricks access connector | eastus | no — finance mission |
| `adlsfinancemission2026` | Storage | eastasia | no — finance mission |
| `app-mission-sql` (+ `app_mission_db`) | Azure SQL server + DB | eastasia | no — other app |

**Three findings that mattered:**
1. **Shared RG** — a parallel "finance mission" + a SQL app share `rg_mission_2026_dataai`.
   Rule: touch only DrivePulse resources; prefix anything new `drivepulse_*`; never modify finance/SQL.
2. **No Event Hubs namespace yet** — required later for telematics streaming.
3. **Workspace is premium, not free/trial** — old docs were wrong. Premium is good: it enables
   row filters, column masks, and serverless that the governance patterns need.

### Bundle wired & validated
- Set `databricks.yml` **dev** workspace host to the real URL (was `REPLACE_ME`).
- `databricks bundle validate` PASSES against the workspace (only 4 harmless `sync.exclude`
  pattern warnings).
- `prod` host still `REPLACE_ME` — no separate prod workspace exists yet.

### Docs updated (show-then-apply rule)
- **CLAUDE.md §12** — corrected free/trial → premium; added real workspace URL/subscription;
  flagged the shared resource group.
- **PROJECT_STATE.md** — added verified s3 environment audit; updated Next action + Changelog.

### Git checkpoints (branch `master`, no remote yet)
- `ee09670` — docs: record verified Azure/Databricks environment + CLI auth state
- `e5faac4` — chore: wire bundle to real workspace; mark environment fully authenticated

### State at end of session
- ✅ Environment fully stood up & verified: tooling, auth, infra mapped, bundle validated, docs current.
- Open (not blocking): repo is local-only (never pushed); Event Hubs not provisioned; all domain
  code is still scaffold/stubs; **new architecture / sources / requirements to be locked shortly**
  — current CLAUDE.md design is provisional until that lock.
- Next: user drops new requirements → propose doc changes → approve → re-baseline → build
  (bootstrap UC → telematics vertical slice first).
