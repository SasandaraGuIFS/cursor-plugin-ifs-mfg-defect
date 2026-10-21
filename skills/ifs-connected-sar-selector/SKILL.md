---
name: ifs-connected-sar-selector
description: >-
  Deterministic Connected-SAR analyzers (parse_diff, resolve_sar_candidates,
  impact_graph, area_map) that map IFS source changes to SAR/TAR .mkd suites.
  Use when selecting which Script-A-Rest tests to run for a changed file, PR,
  or git diff; when NZD MCP analyzers are unavailable; or when the Connected
  SAR Selector Agent needs tool output with file:line evidence.
---

# IFS Connected SAR Selector (Local Analyzers)

## Why this exists

The Connected SAR Selector Agent contract requires deterministic tools:

| Tool | Purpose |
|------|---------|
| `parse_diff` | changed files → entities / packages / `.svc` |
| `resolve_sar_candidates` | entity/svc/package → `.mkd` hits with `file:line` |
| `impact_graph` | static callers + coupled services |
| `area_map` | component → SAR product area + seed |

These are **not** on the NZD MCP server (`list_nzd_tools` only returns EBR tools).
This skill provides the same contract via a local Python CLI.

## Command

Run from the workspace root (`c:\Dev\Master\workspace`):

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py <subcommand> ...
```

All subcommands emit **JSON** on stdout (ground truth for the agent).

## Subcommands

### One-shot retrieve (preferred first call)

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py select --files ordstr/source/ordstr/database/InterimCtpManager.plsql
```

Or from a git range:

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py select --base origin/master --head HEAD
```

### Individual tools (agent contract)

```powershell
# Layer 0
py -3 .../connected_sar_analyzers.py parse_diff --files path/to/File.plsql

# Layer 1
py -3 .../connected_sar_analyzers.py resolve_sar_candidates --entity InterimCtpManager
py -3 .../connected_sar_analyzers.py resolve_sar_candidates --svc CustomerOrderHandling.svc
py -3 .../connected_sar_analyzers.py resolve_sar_candidates --package INTERIM_CTP_MANAGER_API

# Layer 2
py -3 .../connected_sar_analyzers.py impact_graph --package INTERIM_CTP_MANAGER_API --depth 1

# Area
py -3 .../connected_sar_analyzers.py area_map --component ordstr

# Inspect a candidate script
py -3 .../connected_sar_analyzers.py read_script --path inttst/test/inttst/6.4.2.1/RunCapabilityCheck/RunCapabilityCheck.mkd --start 1 --end 40
```

## Agent workflow

1. **Always** run `select` (or `parse_diff` + `resolve_sar_candidates` + `impact_graph`) **before** LLM ranking.
2. Treat JSON `evidence[].file` + `evidence[].line` as the only citeable proof.
3. Select **suite** `.mkd` files (orchestrators), not individual test cases.
4. If `candidates` is empty → apply `area_map` fallback (area-seed), never return an empty set silently.
5. Ranking-only: `sar_jenkins_report` MCP for age>1 history — do not use it for selection.

## Do not

- Call `list_nzd_tools` / `call_nzd_tool` for Connected-SAR selection (those are EBR-only).
- Invent candidates without JSON evidence from this CLI.
- Select at test-case granularity.

## Map file

`references/component-map.yaml` — component → product area + seed folder (CIIMP-151 stand-in).
