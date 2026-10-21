#!/usr/bin/env node
/**
 * IFS Cloud Code Deployment via SQLcl
 *
 * Thin Node.js wrapper that deploys generated files using the same
 * child_process.spawn pattern as the IFS Cloud Development Kit extension.
 *
 * Usage:
 *   node ifs-deploy.mjs <connection_string> <file1> [file2] [file3] ...
 *   node ifs-deploy.mjs <connection_string> --script <master_script.sql>
 *
 * Examples:
 *   node ifs-deploy.mjs "ifsapp/pwd@host:1521/IFSPDB" build/gen/db/person/database/person/AccessAttribute.cpi
 *   node ifs-deploy.mjs "ifsapp/pwd@host:1521/IFSPDB" --script /tmp/deploy.sql
 */

import { spawn } from "node:child_process";
import { writeFileSync, readFileSync, unlinkSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, basename } from "node:path";
import { homedir } from "node:os";

// ---------------------------------------------------------------------------
// Tablespace variable resolution (mirrors the VS Code extension's Ly function)
// ---------------------------------------------------------------------------

const TABLESPACE_REPLACEMENTS = {
  "&IFSAPP_DATA": "IFSAPP_DATA",
  "&IFSAPP_INDEX": "IFSAPP_INDEX",
  "&IFSAPP_LOB": "IFSAPP_LOB",
};

/**
 * Read each file, replace &IFSAPP_DATA / &IFSAPP_INDEX / &IFSAPP_LOB with
 * actual tablespace names, and write the resolved content to temp files.
 * Returns an array of { originalPath, tempPath } objects.
 */
function resolveTablespaceVars(filePaths) {
  const results = [];

  for (const filePath of filePaths) {
    let content = readFileSync(filePath, "utf8");

    for (const [variable, value] of Object.entries(TABLESPACE_REPLACEMENTS)) {
      content = content.replaceAll(variable, value);
    }

    const tempPath = join(tmpdir(), `resolved_${Date.now()}_${basename(filePath)}`);
    writeFileSync(tempPath, content, "utf8");
    results.push({ originalPath: filePath, tempPath });
  }

  return results;
}

// ---------------------------------------------------------------------------
// Find SQLcl
// ---------------------------------------------------------------------------

// Path to the SQLcl install root (folder containing bin/sql[.exe]).
// Leave as null to auto-detect from ~/tools/sqlcl/.
// port-to-cursor.bat overwrites this line when porting to a Cursor project.
const SQLCL_ROOT = String.raw`C:\sqlcl`; // port-to-cursor: SQLCL_ROOT

function findSqlcl() {
  const root = SQLCL_ROOT || join(homedir(), "tools", "sqlcl");
  const candidates = [
    join(root, "bin", "sql.exe"),
    join(root, "bin", "sql"),
  ];
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Deploy â€” same pattern as the IFS Cloud Dev Kit extension
// ---------------------------------------------------------------------------

function deploy(sqlclPath, connectionString, scriptPath) {
  return new Promise((resolve, reject) => {
    const proc = spawn(sqlclPath, [connectionString]);

    if (!proc.stdout || !proc.stdin || !proc.stderr) {
      reject(new Error("Failed to create SQLcl process streams"));
      return;
    }

    let oracleErrors = [];
    let stderrOutput = "";
    let stdinOpen = true;

    // Java module warnings from SQLcl startup â€” harmless, not deployment errors
    const STDERR_IGNORE = /^WARNING: (A restricted method|java\.lang\.System|Use --enable-native-access|Restricted methods)/;

    proc.stdin.on("error", (err) => {
      console.error(`[stdin error] ${err.message}`);
      stdinOpen = false;
    });

    proc.stdout.on("data", (data) => {
      const text = data.toString();
      process.stdout.write(text);
      if (/(ORA-|PLS-|SP2-)\d{5}/.test(text)) {
        oracleErrors.push(text.trim());
      }
    });

    proc.stderr.on("data", (data) => {
      const text = data.toString();
      process.stderr.write(text);
      const meaningful = text.split(/\r?\n/).filter((l) => l.trim() && !STDERR_IGNORE.test(l.trim())).join("\n");
      if (meaningful) stderrOutput += meaningful;
    });

    proc.on("close", (code) => {
      stdinOpen = false;
      if (oracleErrors.length > 0) {
        reject(new Error(oracleErrors.join("\n")));
      } else if (code !== 0 && stderrOutput) {
        reject(new Error(stderrOutput));
      } else {
        resolve();
      }
    });

    proc.on("error", (err) => {
      stdinOpen = false;
      reject(new Error(`Failed to start SQLcl: ${err.message}`));
    });

    // Wait 1 second for connection to establish, then send the script
    setTimeout(() => {
      if (stdinOpen && proc.stdin) {
        proc.stdin.write(`@"${scriptPath}"\n`);
        proc.stdin.end();
      }
    }, 1000);
  });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error("Usage: node ifs-deploy.mjs <connection_string> <file1> [file2] ...");
    console.error("       node ifs-deploy.mjs <connection_string> --script <script.sql>");
    process.exit(1);
  }

  const connectionString = args[0];
  let scriptPath;
  let tempScript = false;
  let cleanupFiles = [];

  if (args[1] === "--script" && args[2]) {
    scriptPath = resolve(args[2]);
  } else {
    // Build a master deployment script from the file list
    const files = args.slice(1).map((f) => resolve(f));

    // Resolve tablespace substitution variables (&IFSAPP_DATA, etc.)
    // â€” mirrors the VS Code extension's pre-processing step
    const resolved = await resolveTablespaceVars(files);
    const tempResolvedFiles = resolved.map((r) => r.tempPath);

    const lines = [
      "-- IFS DB DEPLOYMENT SCRIPT",
    ];
    for (const r of resolved) {
      const name = r.originalPath.split(/[\\/]/).pop();
      lines.push(`PROMPT >>> Deploying: ${name}`);
      lines.push(`@"${r.tempPath.replace(/\\/g, "/")}"`);
      lines.push(";");
      lines.push("/");
      lines.push("");
    }
    lines.push("", "EXIT;");

    scriptPath = join(tmpdir(), `ifs_deploy_${Date.now()}.sql`);
    writeFileSync(scriptPath, lines.join("\n"), "utf8");
    tempScript = true;

    // Track temp resolved files for cleanup
    cleanupFiles = tempResolvedFiles;
  }

  const sqlclPath = process.env.SQLCL_PATH || findSqlcl();
  if (!sqlclPath) {
    console.error("Error: SQLcl not found. Set SQLCL_PATH or install to ~/tools/sqlcl/");
    process.exit(1);
  }

  console.log(`SQLcl: ${sqlclPath}`);
  console.log(`Connection: ${connectionString.replace(/\/[^@]+@/, "/***@")}`);
  console.log(`Script: ${scriptPath}`);
  console.log("---");

  try {
    await deploy(sqlclPath, connectionString, scriptPath);
    console.log("\n--- Deployment completed successfully ---");
  } catch (err) {
    console.error(`\n--- Deployment failed: ${err.message} ---`);
    process.exit(1);
  } finally {
    if (tempScript) {
      try { unlinkSync(scriptPath); } catch {}
    }
    for (const f of cleanupFiles) {
      try { unlinkSync(f); } catch {}
    }
  }
}

main();

