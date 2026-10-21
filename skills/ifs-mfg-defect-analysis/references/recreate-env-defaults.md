# Bnt recreate defaults (template)

**Not used for manufacturing recreate SAR runs.** Recreate ScriptARest uses one MASTER CMB (prefer DEV, fall back to DEP) as `alain`/`alain`. See [recreate-sar.md](recreate-sar.md).

Kept as a template only if a later flow needs Bnt. Copy to `docs/mfg-recreate-defaults.md` on the **first** confirmed Bnt run. Later chats read that workspace file and do not re-ask unless the user says the env is wrong.

Do **not** put live URLs or user ids in this skill file. Fill values only in `docs/mfg-recreate-defaults.md`.

```markdown
# Manufacturing recreate SAR — Bnt defaults

Used by ifs-mfg-defect-analysis (same-chat SAR-first) / ifs-test-data-creator when seeding ticket-local recreate data.

## Connection

| Item | Value |
| --- | --- |
| Bnt Aurena URL | |
| Connect user | |

## Basic data to reuse (this site)

| Field | Value | Notes |
| --- | --- | --- |
| Site | | |
| Company | | |
| Location No | | |
| Sales Price Group | | |
| Sales Group | | |
| Configuration Family | | optional default |
| Customer | | default to reuse |
| Persons | | default to reuse |
| Supplier | | default to reuse |

Ticket-specific overrides go in `docs/<KEY>/recreate/`. Do not store part numbers here — parts are created from scratch per ticket.
```
