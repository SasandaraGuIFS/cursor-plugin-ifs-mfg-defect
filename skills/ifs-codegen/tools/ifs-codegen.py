#!/usr/bin/env python3
"""
IFS Cloud Code Generator CLI

Wraps the Marble LSP code generator JAR for use from the command line or AI agents.
Generates deployable SQL/PL/SQL from IFS Cloud model files.

Usage:
  python ifs-codegen.py generate <file>
  python ifs-codegen.py generate <file> --json

Examples:
  python ifs-codegen.py generate workspace/person/model/person/PersonInfo.entity
  python ifs-codegen.py generate workspace/accrul/model/accrul/Account.entity --json
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration â€” auto-detect paths
# ---------------------------------------------------------------------------

# Path to the IFS Cloud Dev Kit extension's globalStorage folder
# (contains active-version.json + per-version subfolders with the codegen JAR).
# Leave as None to auto-detect from VS Code's %APPDATA%\Code location.
# port-to-cursor.bat overwrites this line when porting to a Cursor project.
IFS_DEVKIT_PATH = str(
    Path(os.environ.get("APPDATA", ""))
    / "Cursor"
    / "User"
    / "globalStorage"
    / "ifs.ifsclouddevelopmentkit"
)  # port-to-cursor: IFS_DEVKIT_PATH


def find_codegen_jar():
    """Locate the active code generator JAR from the IFS Cloud Dev Kit extension."""
    if IFS_DEVKIT_PATH:
        global_storage = Path(IFS_DEVKIT_PATH)
    else:
        global_storage = Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "ifs.ifsclouddevelopmentkit"

    active_version_file = global_storage / "active-version.json"
    if not active_version_file.exists():
        return None, "No active code generator version configured. Run 'IFS: Select Code Generator Target version' in VS Code."

    with open(active_version_file) as f:
        version = json.load(f).get("version")

    if not version:
        return None, "active-version.json is empty."

    jar_path = global_storage / version / "ifs-dev-buildtasks.jar"
    if not jar_path.exists():
        return None, f"Code generator JAR not found at {jar_path}. Re-download via VS Code."

    metadata_path = global_storage / version / "metadata.json"
    if not metadata_path.exists():
        return None, f"metadata.json missing for version {version}. Code generator may be corrupt."

    return str(jar_path), None


# ---------------------------------------------------------------------------
# Workspace root detection
# ---------------------------------------------------------------------------

def find_workspace_root(file_path):
    """Detect the IFS workspace root from a file path.

    The VS Code extension sets rootUri to the workspace folder so the LSP
    server can resolve cross-file dependencies (e.g. finding client/projection
    files that reference a fragment).  We replicate this by walking up from
    the given file until we find the 'workspace/' directory.

    Example:
        .../IFSCloud-master/workspace/person/model/person/Foo.fragment
        â†’ .../IFSCloud-master/workspace
    """
    p = Path(file_path).resolve()
    for parent in p.parents:
        if parent.name == "workspace" and (parent / "fndbas").is_dir():
            return str(parent)
    # Fallback: look for workspace/ in the path parts
    parts = p.parts
    for i, part in enumerate(parts):
        if part == "workspace" and i > 0:
            return str(Path(*parts[:i + 1]))
    return None


# ---------------------------------------------------------------------------
# LSP Client â€” communicates with the Marble code generator JAR
# ---------------------------------------------------------------------------

class LSPClient:
    """Minimal LSP client for the IFS Marble code generator."""

    def __init__(self, jar_path, java_cmd="java"):
        self.jar_path = jar_path
        self.java_cmd = java_cmd
        self.process = None
        self._request_id = 0

    def start(self, workspace_root=None):
        """Launch the LSP server subprocess.

        Args:
            workspace_root: Absolute path to the workspace root directory.
                The LSP server needs this to find cross-file dependencies
                (e.g. client/projection files that reference a fragment).
                If None, the server cannot resolve fragment dependencies.
        """
        self.workspace_root = workspace_root
        cmd = [self.java_cmd, "-jar", self.jar_path, "-lsp"]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._initialize()

    def stop(self):
        """Shutdown the LSP server."""
        if self.process:
            try:
                self._send_request("shutdown", None)
                self._send_notification("exit", None)
            except Exception:
                pass
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    def _next_id(self):
        self._request_id += 1
        return self._request_id

    def _send_message(self, message):
        """Send a JSON-RPC message with LSP Content-Length framing."""
        body = json.dumps(message).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.process.stdin.write(header + body)
        self.process.stdin.flush()

    def _read_message(self):
        """Read a JSON-RPC message from the LSP server."""
        headers = {}
        while True:
            line = self.process.stdout.readline().decode("ascii")
            if not line or line.strip() == "":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        content_length = int(headers.get("Content-Length", 0))
        if content_length == 0:
            return None

        body = self.process.stdout.read(content_length)
        return json.loads(body.decode("utf-8"))

    def _send_request(self, method, params):
        """Send an LSP request and wait for the response."""
        req_id = self._next_id()
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params

        self._send_message(message)

        # Read responses until we get the one matching our request ID.
        # The server may send notifications (no id) in between.
        while True:
            response = self._read_message()
            if response is None:
                raise RuntimeError(f"LSP server closed connection during '{method}' request")
            if "id" in response and response["id"] == req_id:
                if "error" in response:
                    raise RuntimeError(f"LSP error: {response['error']}")
                return response.get("result")
            # else: notification or different response â€” skip

    def _send_notification(self, method, params):
        """Send an LSP notification (no response expected)."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            message["params"] = params
        self._send_message(message)

    def _initialize(self):
        """Perform the LSP initialize handshake."""
        root_uri = Path(self.workspace_root).as_uri() if self.workspace_root else None
        result = self._send_request("initialize", {
            "processId": os.getpid(),
            "capabilities": {},
            "rootPath": self.workspace_root,
            "rootUri": root_uri,
            "workspaceFolders": [{"uri": root_uri, "name": Path(self.workspace_root).name}] if root_uri else None,
            "initializationOptions": {
                "launchCodeGenerator": f"java -jar {self.jar_path}"
            },
        })
        self._send_notification("initialized", {})
        return result

    def generate_code(self, file_path):
        """Generate code for an IFS model file.

        Args:
            file_path: Absolute path to the model file.

        Returns:
            List of generated file paths.
        """
        file_uri = Path(file_path).as_uri()
        result = self._send_request("generateCode", file_uri)

        if result is None:
            raise RuntimeError("generateCode returned no result")

        if "error" in result and result["error"]:
            raise RuntimeError(f"Code generation failed: {result['error']}")

        return result.get("generatedFiles", [])

    def get_files_to_deploy(self, file_path, generated_files):
        """Get the ordered list of files to deploy with their content.

        Calls the LSP server's getFilesToDeploy method with both required
        parameters (file URI + generated files list), matching how the
        IFS Cloud Dev Kit extension calls it.

        Args:
            file_path: Absolute path to the model file.
            generated_files: List of generated file paths from generate_code().

        Returns:
            List of {uri, content} dicts, or the generated_files list as fallback.
        """
        file_uri = Path(file_path).as_uri()
        result = self._send_request("getFilesToDeploy", [file_uri, generated_files])
        return result if result else generated_files


# ---------------------------------------------------------------------------
# Master Script Generation (mirrors IFS Dev Kit extension's generateMasterScript)
# ---------------------------------------------------------------------------

def generate_master_script(deploy_files, output_path=None):
    """Generate a master deployment SQL script.

    Replicates the IFS Dev Kit extension's generateMasterScript logic:
    - For each file: write content to temp, add @"path" ; /
    - Append EXIT;

    Args:
        deploy_files: List of {uri, content} dicts or file path strings.
        output_path: Optional path for the master script. Auto-generated if None.

    Returns:
        Tuple of (master_script_path, list_of_temp_files_to_clean_up).
    """
    import tempfile
    import time

    temp_files = []
    lines = ["-- IFS DB DEPLOYMENT SCRIPT", ""]

    for entry in deploy_files:
        if isinstance(entry, dict) and "content" in entry:
            # {uri, content} from getFilesToDeploy â€” write content to temp file
            filename = os.path.basename(entry.get("uri", "unknown"))
            temp_path = os.path.join(tempfile.gettempdir(), f"resolved_{int(time.time()*1000)}_{filename}")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(entry["content"])
            temp_files.append(temp_path)
            file_ref = temp_path
        else:
            # Plain file path string
            file_ref = entry if isinstance(entry, str) else str(entry)
            filename = os.path.basename(file_ref)

        lines.append(f"PROMPT >>> Deploying: {filename}")
        lines.append(f'@"{file_ref.replace(os.sep, "/")}"')
        lines.append(";")
        lines.append("/")
        lines.append("")

    lines.append("EXIT;")

    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), f"marble_deploy_{int(time.time()*1000)}.sql")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    temp_files.append(output_path)
    return output_path, temp_files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_generate(args):
    """Handle the 'generate' subcommand."""
    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    jar_path, err = find_codegen_jar()
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    java_cmd = args.java or "java"
    workspace_root = find_workspace_root(file_path)
    print(f"Code generator: {jar_path}")
    print(f"Generating code for: {file_path}")
    if workspace_root:
        print(f"Workspace root: {workspace_root}")

    client = LSPClient(jar_path, java_cmd)
    try:
        client.start(workspace_root=workspace_root)
        generated = client.generate_code(file_path)

        if not generated:
            print("No files were generated.")
            return 1

        print(f"\nGenerated {len(generated)} file(s):")
        for gf in generated:
            print(f"  > {gf}")

        # Get the ordered deploy file list from the LSP server.
        # getFilesToDeploy returns only the subset of generated files that
        # should actually be deployed, in the correct deployment order.
        deploy_files = client.get_files_to_deploy(file_path, generated)

        if deploy_files and isinstance(deploy_files, list):
            print(f"\nFiles to deploy ({len(deploy_files)}, in order):")
            for df in deploy_files:
                if isinstance(df, dict):
                    print(f"  > {os.path.basename(df.get('uri', 'unknown'))}")
                else:
                    print(f"  > {os.path.basename(df)}")

            # Build master deploy script (resolves content from getFilesToDeploy)
            master_script, _ = generate_master_script(deploy_files)
            print(f"\nMaster deploy script: {master_script}")
        else:
            master_script = None
            print("\ngetFilesToDeploy returned no files; falling back to generated list.")

        # Output as JSON for machine consumption
        if args.json:
            deploy_uris = []
            if deploy_files and isinstance(deploy_files, list):
                for df in deploy_files:
                    if isinstance(df, dict):
                        deploy_uris.append(df.get("uri", ""))
                    else:
                        deploy_uris.append(df)
            result = {
                "generatedFiles": generated,
                "deployFiles": deploy_uris,
            }
            if master_script:
                result["masterScript"] = master_script
            print(json.dumps(result, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        client.stop()


def main():
    parser = argparse.ArgumentParser(
        description="IFS Cloud Code Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--java", help="Path to java executable (default: java on PATH)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate code from an IFS model file")
    gen_parser.add_argument("file", help="Path to the model file (.entity, .client, .projection, etc.)")
    gen_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    # deploy
    dep_parser = subparsers.add_parser("deploy", help="Generate code, build master script, and deploy via Node.js")
    dep_parser.add_argument("file", help="Path to the model file")
    dep_parser.add_argument("--conn", required=True, help="SQLcl connection string (user/pass@host:port/service)")

    args = parser.parse_args()

    if args.command == "generate":
        sys.exit(cmd_generate(args))
    elif args.command == "deploy":
        sys.exit(cmd_deploy(args))


def cmd_deploy(args):
    """Generate code, get deploy files, build master script, and deploy via ifs-deploy.mjs."""
    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    jar_path, err = find_codegen_jar()
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    java_cmd = args.java or "java"
    workspace_root = find_workspace_root(file_path)
    print(f"Code generator: {jar_path}")
    print(f"Generating code for: {file_path}")
    if workspace_root:
        print(f"Workspace root: {workspace_root}")

    client = LSPClient(jar_path, java_cmd)
    temp_files = []
    try:
        client.start(workspace_root=workspace_root)

        # Step 1: Generate code
        generated = client.generate_code(file_path)
        if not generated:
            print("No files were generated.")
            return 1

        print(f"\nGenerated {len(generated)} file(s):")
        for gf in generated:
            print(f"  > {os.path.basename(gf)}")

        # Step 2: Get files to deploy (with both params, matching extension)
        deploy_files = client.get_files_to_deploy(file_path, generated)

        if not deploy_files:
            print("No files to deploy (getFilesToDeploy returned empty). Using generated files.")
            deploy_files = generated

        print(f"\nFiles to deploy: {len(deploy_files) if isinstance(deploy_files, list) else '?'}")

        # Step 3: Build master deployment script
        master_script, temp_files = generate_master_script(deploy_files)
        print(f"Master script: {master_script}")

        # Step 4: Deploy via ifs-deploy.mjs
        deploy_mjs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ifs-deploy.mjs")
        print(f"\nDeploying to: {args.conn.split('@')[1] if '@' in args.conn else args.conn}")
        sys.stdout.flush()

        result = subprocess.run(
            ["node", deploy_mjs, args.conn, "--script", master_script],
            timeout=300,
        )
        return result.returncode

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        client.stop()
        for f in temp_files:
            try:
                os.unlink(f)
            except OSError:
                pass


if __name__ == "__main__":
    main()

