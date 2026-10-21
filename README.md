# IFS Manufacturing Defect Analyzer — Cursor plugin

End-to-end agent flow for IFS Cloud manufacturing defects (MFZ-\* Jira tickets):
fetch Jira + attachments → plain explanation → from-scratch recreate SAR with bug asserts →
investigate + drafted fix → deploy → unit tests → verify with fix asserts → RCA draft →
standalone fix-flow SAR matrix → release notes draft.

The agent **never writes Jira**. Everything is drafted in chat and in
`docs/<KEY>/analysis.md` only.

## What's inside

```
.cursor-plugin/plugin.json    Cursor manifest
.claude-plugin/plugin.json    Claude Code manifest
.claude-plugin/marketplace.json
plugin.json                   Agent-plugin manifest (agent-plugins.org schema)
commands/mfg-defect.md        /mfg-defect <JIRA-KEY> slash command
skills/
  ifs-mfg-defect-analysis/    Orchestrator (Steps 1-8)
  ifs-jira-reader/            Step 1 Jira fetch + attachment processor
  ifs-codegen/                Step 5b code generation + deploy
  ifs-code-review/            Step 5 pre-apply A-Z review
  ifs-plsql-patterns/         PL/SQL patterns reference
  ifs-test-writing/           .pltst discovery for Step 5b
  ifs-history-comments/       YYMMDD history line placement
  ifs-sar-generator/          Recreate + fix SAR authoring rules
  ifs-connected-sar-selector/ Step 7 analyzers (flow discovery)
  ifs-standalone-fix-sar/     Step 7 fix-flow SAR matrix + runner
  ifs-jira-rca/               Step 6 RCA draft
  ifs-jira-release-notes/     Step 8 release notes draft
  ifs-master-commit/          27R1 commit flow after fix verified
  ifs-track-backport/         Backport to 26R2 / 26R1 / 25R2 / ...
shared/
  docs/bnd-environment-urls.md
  docs/bnd-environment-connections.json
  scripts/fast-deploy-plsql.ps1
  scripts/connected_sar_analyzers.py
  scripts/process_jira_attachments.py
tools/
  verify-links.ps1            CI gate: broken intra-plugin markdown links
  package.ps1                 Builds dist/ifs-mfg-defect-<version>.zip
```

## Prerequisites

The plugin **only ships skills + prompts + helper scripts**. It re-uses MCP servers
you already have in Cursor. Install these from Cursor Settings > MCP before running:

| Purpose                           | MCP namespace                        |
| --------------------------------- | ------------------------------------ |
| Jira read + attachments           | `user-Atlassian-MCP-Server`          |
| Database (SQLcl)                  | `user-sqlcl`                         |
| IFS codegen / deploy / live DB    | `user-ifs-f1-codegen-dev`            |
| Browser verification (optional)   | `user-Playwright-MCP-Server`         |
| PR / branch management (optional) | `user-Bitbucket-MCP-Server`          |

You also need:

- **Python 3.10+** on `PATH` (for `process_jira_attachments.py`, `connected_sar_analyzers.py`).
- **PowerShell 5.1 or 7+** (for `fast-deploy-plsql.ps1` and `tools/*`).
- **SQLcl** connections named per `shared/docs/bnd-environment-connections.json`
  (`MASTER DEV CMB`, `MASTER DEP CMB`, etc.). Each teammate configures these in
  their own SQLcl.

### Per-workspace files

The skills read env URLs/connections from `docs/bnd-environment-urls.md` and
`docs/bnd-environment-connections.json` **in the IFS workspace repo** (not from
the plugin). The plugin ships copies under `shared/docs/` as a template/fallback —
copy them into each workspace that doesn't already have them:

```powershell
Copy-Item <plugin>\shared\docs\bnd-environment-*.* <ifs-workspace>\docs\
```

## Install

### Option 1 — via git plugin (recommended)

In Cursor: **Settings > Plugins > Add plugin from git** and paste:

```
<internal-bitbucket-url>/cursor-plugin-ifs-mfg-defect.git
```

Cursor clones to `%USERPROFILE%\.cursor\plugins\cache\<slug>\...` and auto-registers
every `skills/*/SKILL.md` and `commands/*.md`.

### Option 2 — via zip

1. Download `ifs-mfg-defect-<version>.zip` from the Bitbucket release.
2. Unzip into `%USERPROFILE%\.cursor\plugins\local\ifs-mfg-defect\`.
3. Restart Cursor.

## Usage

In a Cursor chat on the IFS workspace repo:

```
/mfg-defect MFZ-31273
```

The agent will:

1. Rename the chat to `MFZ-31273`.
2. Run Step 1 (fetch Jira + attachments, write the plain explanation).
3. Progress through Steps 2–8, stopping only when it needs a decision.

If `docs/MFZ-31273/analysis.md` already exists, it resumes at the first
unfinished gate.

## Verify and build

```powershell
# Link + reference sanity check
powershell -ExecutionPolicy Bypass -File tools\verify-links.ps1

# Build release zip into dist/
powershell -ExecutionPolicy Bypass -File tools\package.ps1
```

Both scripts are safe to run inside CI (exit 0 on success).

## Known limitations

- **Subagents are not bundled.** The skills `ifs-jira-rca`, `ifs-standalone-fix-sar`
  and `ifs-track-backport` sometimes launch Task subagents (`jira-rca`,
  `standalone-fix-sar`, `track-backport`). Without them the skills still work —
  the agent performs the step inline in the same chat.
- **No new MCP server.** All tool calls go through the existing MCPs listed above.
- **One Python helper per task.** The three helper scripts under `shared/scripts/`
  are the only scripts the flow needs. Each skill folder also keeps its own copy
  so existing path references continue to resolve.

## Versioning

- Version lives in `.cursor-plugin/plugin.json`, `plugin.json`,
  `.claude-plugin/marketplace.json`, and `CHANGELOG.md`. Bump all four together.
- `tools/package.ps1` names the zip `ifs-mfg-defect-<version>.zip`.

## License

Proprietary — IFS R&D internal use only.
