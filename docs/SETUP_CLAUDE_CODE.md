# Setting up the isolated DrivePulse project in Claude Code

Goal: a Claude Code workspace that knows **only** DrivePulse — no bleed-through from your
job-search skills (`resume-tailor`, `linkedin-scout`) or other global setup.

## How Claude Code scopes context (the key fact)
- **User scope** `~/.claude/` (CLAUDE.md, skills/, agents/, settings.json) loads in **every** project.
- **Project scope** `.claude/` + the repo's root `CLAUDE.md` loads **only in that repo**.
- So isolation = put project things in the project, and keep global things truly global-neutral.
- Settings precedence (high→low): `.claude/settings.local.json` → `.claude/settings.json` (project)
  → `~/.claude/settings.json` (user). `deny` rules have the highest safety precedence.

## One-time setup

1. **Put the repo on disk and open Claude Code in it**
   ```bash
   cd /path/to/drivepulse-lakehouse
   git init && git add . && git commit -m "scaffold + claude code config"
   claude
   ```
   Claude Code auto-loads the root `CLAUDE.md`. It does **not** auto-load `PROJECT_STATE.md`
   or `PROJECT_INSTRUCTIONS.md` — `CLAUDE.md` §0 tells it to read `PROJECT_STATE.md` first.

2. **Make sure job-search skills are NOT global.** If `resume-tailor` / `linkedin-scout`
   live in `~/.claude/skills/`, they load here too. Move them into their own repo:
   ```bash
   mkdir -p /path/to/job-search/.claude/skills
   mv ~/.claude/skills/resume-tailor  /path/to/job-search/.claude/skills/
   mv ~/.claude/skills/linkedin-scout /path/to/job-search/.claude/skills/
   ```
   Then they only activate when you run `claude` inside the job-search repo.

3. **Keep `~/.claude/CLAUDE.md` neutral.** It loads everywhere — no DrivePulse or job-search
   specifics in it. Personal preferences only (e.g. "use conventional commits").

4. **Project config is already in this repo:**
   - `.claude/settings.json` — permissions (validate/test auto-allowed; deploy/run/push/commit
     require confirmation), secret-file deny rules, and `DATABRICKS_CONFIG_PROFILE=drivepulse`.
   - `.claude/settings.local.json` — copy from the `.example`, add personal overrides; gitignored.
   ```bash
   cp .claude/settings.local.json.example .claude/settings.local.json
   ```

5. **Verify isolation by behavior (don't trust self-reports).** In the DrivePulse repo:
   ```
   > tailor my resume for a data engineer role at Acme
   ```
   Claude Code should NOT invoke `resume-tailor`. If it does, the skill is still global —
   redo step 2. Asking it to "list loaded skills" is a weaker check; self-reported context
   isn't fully reliable.

6. **Confirm the bundle still validates** (needs the `drivepulse` CLI profile from README SETUP):
   ```bash
   databricks bundle validate -t dev
   ```

## Optional hard lock (enterprise only)
`strictPluginOnlyCustomization` blocks all user/project skills/agents/hooks/MCP, but it is a
**managed-settings-only** key (system `managed-settings.json`, Claude Code v2.1.82+). It is
overkill for a solo setup and silently does nothing in a project file — directory scoping
(steps 2–3) is the correct, sufficient solution.

## A note on `deny` rules
`deny` reduces risk but isn't a vault — there are reports of read-denies being bypassed. The
real protection is that secrets never enter the repo (see `.gitignore`) and live only in
Databricks secret scopes / your local `.env`.
