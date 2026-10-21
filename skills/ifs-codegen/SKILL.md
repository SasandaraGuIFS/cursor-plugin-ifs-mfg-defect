---
name: ifs-codegen
description: This skill should be used when generating deployable code from IFS Cloud model files (.entity, .client, .projection, .fragment, .plsvc, .views, .storage) or deploying generated code to an IFS Cloud database. Use it after modifying model files during defect fixes or development tasks.
---

# IFS Cloud Code Generation & Deployment

This skill provides the ability to generate deployable SQL/PL/SQL from IFS Cloud model files and deploy them to a database — fully from the command line.

## When to Use This Skill

- After modifying an IFS model file (`.entity`, `.client`, `.projection`, `.fragment`, `.plsvc`, `.views`, `.storage`) during a defect fix or development task
- When the user asks to generate code, deploy code, or "build" a model file
- When deploying generated files or `.plsql` files to a database

## Path Placeholders

This document uses two placeholders in examples:
- `<skill_dir>` — the directory containing this SKILL.md (e.g. `.claude/skills/ifs-codegen/` or `.cursor/skills/ifs-codegen/` under your project root).
- `<workspace>` — your IFS Cloud workspace root (the folder containing components like `person/`, `accrul/`, etc.).

## Tool Locations

```
<skill_dir>/tools/
  ifs-codegen.py    # Code generation (Python, uses Marble LSP)
  ifs-deploy.mjs    # Deployment (Node.js, spawns SQLcl)
```

## Prerequisites

- **Java JDK 11+** on PATH — for code generation
- **Node.js** on PATH — for deployment
- **IFS Code Generator JAR** — downloaded via the IFS Cloud Development Kit VS Code extension (`IFS: Select Code Generator Target version`)
- **SQLcl** — auto-detected at `~/tools/sqlcl/bin/sql`

## Generate and Deploy Model Files (Primary Workflow)

### Step 1: Generate Code and Get Deploy Order

```bash
python <skill_dir>/tools/ifs-codegen.py generate <model-file> --json
```

This performs two LSP calls:
1. **`generateCode`** — produces all generated files from the model file
2. **`getFilesToDeploy`** — returns **only the files that need deployment, in the correct order** (a filtered subset of generated files)

It also builds a **master deploy script** that combines the deploy files in the correct order.

Example:
```bash
python <skill_dir>/tools/ifs-codegen.py generate \
  <workspace>/person/model/person/PersonInfo.entity --json
```

The `--json` output includes:
- `generatedFiles` — all files produced by code generation
- `deployFiles` — the ordered subset that should actually be deployed
- `masterScript` — path to the combined deploy SQL script

**IMPORTANT:** Do NOT deploy all generated files. Only deploy the files listed in `deployFiles` / the `masterScript`. Some generated files (e.g. `-Base.plsql`) are intermediate artifacts that should not be deployed directly — deploying them causes annotation parsing errors in SQLcl.

### Step 2: Deploy via Master Script

Use the `masterScript` path from Step 1 with `ifs-deploy.mjs`:

```bash
node <skill_dir>/tools/ifs-deploy.mjs "<connection_string>" --script "<masterScript>"
```

The connection string format is: `username/password@hostname:port/serviceName`

Example:
```bash
node <skill_dir>/tools/ifs-deploy.mjs \
  "ifsapp/ifsapp@host:1521/IFSPDB" \
  --script "/tmp/marble_deploy_1234567890.sql"
```

## Deploying .plsql Files (No Generation Needed)

`.plsql` files are directly deployable — skip the generation step:

```bash
node <skill_dir>/tools/ifs-deploy.mjs "<conn>" "<workspace>/person/source/person/database/PersonInfo.plsql"
```

Or use the sqlcl MCP `run-sql` tool with the file content if the MCP server is connected.

## Connection Details

To find connection details, use the sqlcl MCP `list-connections` tool (shows saved connections with hostnames and ports). The connection string format for deployment is:

```
username/password@hostname:port/serviceName
```

Example: `ifsapp/ifsapp@host:1521/IFSPDB`

## File Types That Require Code Generation

| File Type | Generated Output |
|-----------|-----------------|
| `.entity` | `.api`, `.apy`, `.apv`, `-Base.plsql`, `-Base.views`, `.ins`, `.tst` |
| `.client` | `-Base.client`, `.cpi`, client metadata JSON |
| `.projection` | Projection metadata, PL/SQL service stubs |
| `.fragment` | Fragment metadata |
| `.plsvc` | PL/SQL service implementation stubs |
| `.views` | View definitions |
| `.storage` | Storage scripts |

## File Types That Do NOT Need Code Generation

Deploy directly via `ifs-deploy.mjs` or the sqlcl MCP server:

- `.plsql` — PL/SQL package body
- `.ins` — Installation scripts
- `.upg` — Upgrade scripts
- `.cdb` — Component database scripts

## Full Workflow Example (Defect Fix)

```bash
# 1. Generate code and get deploy order (use --json to get masterScript path)
python <skill_dir>/tools/ifs-codegen.py generate \
  <workspace>/person/model/person/PersonInfo.entity --json

# 2. Deploy using the master script from step 1
node <skill_dir>/tools/ifs-deploy.mjs "ifsapp/pwd@host:1521/IFSPDB" \
  --script "/tmp/marble_deploy_1234567890.sql"

# 3. Deploy a .plsql file (no generation needed)
node <skill_dir>/tools/ifs-deploy.mjs "ifsapp/pwd@host:1521/IFSPDB" \
  <workspace>/person/source/person/database/PersonInfo.plsql

# 4. Verify — use sqlcl MCP run-sql to check USER_ERRORS
```

## How It Works

**Code generation** (`ifs-codegen.py`): Communicates with the Marble code generator JAR (`ifs-dev-buildtasks.jar`) using the Language Server Protocol (LSP) over stdio. The `generateCode` LSP call produces all files, and `getFilesToDeploy` returns the filtered, ordered subset needed for deployment. A master deploy script is built from the deploy files with resolved content.

**Deployment** (`ifs-deploy.mjs`): Uses the same `child_process.spawn` pattern as the IFS Cloud Development Kit VS Code extension — spawns SQLcl with the connection string, waits for connection, then writes `@"<script>"` to stdin.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No active code generator version" | Open VS Code, run `IFS: Select Code Generator Target version` to download |
| Java not found | Set `--java` flag or ensure Java is on PATH |
| SQLcl not found | Set `SQLCL_PATH` env var or install to `~/tools/sqlcl/` |
| ORA- errors during deploy | Check the output — may be schema mismatch or missing dependencies |
| Generation produces 0 files | Ensure the file is a valid model type |
| Annotation errors (`@UncheckedAccess`, `@SecurityCheck`) | You deployed raw generated files instead of using the master script from `getFilesToDeploy` |
