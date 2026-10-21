#!/usr/bin/env python3
"""
Local Connected-SAR analyzers (stand-in for planned NZD MCP tools).

Subcommands match the Connected SAR Selector Agent contract:
  parse_diff, resolve_sar_candidates, impact_graph, area_map, read_script

Usage (from workspace root):
  py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py <cmd> ...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError:  # minimal YAML loader for our simple map file
    yaml = None


SVC_RE = re.compile(
    r"(?P<svc>[A-Za-z][A-Za-z0-9_]*(?:Handling|Assistant|Service)?\.svc)",
    re.IGNORECASE,
)
ODATA_SVC_RE = re.compile(
    r"(?:Action|Get|Post|Patch|Delete|Batch)\s+([A-Za-z][A-Za-z0-9_]*\.svc)/",
    re.IGNORECASE,
)
API_CALL_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+_API)\b"
)
PROJECTION_FETCH_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_]*(?:_API|_SVC))\.[A-Za-z0-9_]+",
)


def find_workspace_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "inttst").is_dir() and (p / ".cursor").is_dir():
            return p
        if (p / "inttst").is_dir() and (p / "components.json").is_file():
            return p
    return cur


ROOT = find_workspace_root()
INTTST = ROOT / "inttst" / "test" / "inttst"
MAP_PATH = (
    ROOT
    / ".cursor"
    / "skills"
    / "ifs-connected-sar-selector"
    / "references"
    / "component-map.yaml"
)


def emit(obj: Any) -> None:
    json.dump(obj, sys.stdout, indent=2)
    sys.stdout.write("\n")


def pascal_to_snake_api(stem: str) -> str:
    """InterimCtpManager → INTERIM_CTP_MANAGER_API (normalized upper)."""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", stem)
    s = re.sub(r"_+", "_", s)
    return f"{s.upper()}_API"


def pascal_to_ifs_api(stem: str) -> str:
    """InterimCtpManager → Interim_Ctp_Manager_API (IFS source call form)."""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", stem)
    s = re.sub(r"_+", "_", s)
    parts = s.split("_")
    return "_".join(p[:1].upper() + p[1:].lower() if p else p for p in parts) + "_API"


def api_search_forms(package: str) -> list[str]:
    """Return case variants used in IFS sources and searches."""
    pkg = package.strip()
    if not pkg:
        return []
    upper = pkg.upper()
    if not upper.endswith("_API") and not upper.endswith("_SVC"):
        upper = pascal_to_snake_api(pkg)
    # Interim_Ctp_Manager_API from INTERIM_CTP_MANAGER_API
    body = re.sub(r"_API$|_SVC$", "", upper)
    suffix = "_API" if upper.endswith("_API") else "_SVC"
    title = "_".join(p[:1] + p[1:].lower() for p in body.split("_") if p) + suffix
    forms = [title, upper]
    # Also bare entity Pascal for projections
    entity_pascal = "".join(p.capitalize() for p in body.lower().split("_"))
    return list(dict.fromkeys([f for f in forms + [entity_pascal] if f]))


def load_component_map() -> dict[str, Any]:
    if not MAP_PATH.is_file():
        return {"areas": {}, "defaults": {}, "priority": []}
    text = MAP_PATH.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    # Minimal fallback: only parse our simple structure via regex-ish lines
    return _parse_map_fallback(text)


def _parse_map_fallback(text: str) -> dict[str, Any]:
    """Very small YAML subset parser for component-map.yaml when PyYAML missing."""
    areas: dict[str, Any] = {}
    shared: list[str] = []
    priority: list[dict[str, str]] = []
    current_area: str | None = None
    in_components = False
    in_shared = False
    in_priority = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("areas:"):
            in_shared = in_priority = False
            continue
        if line.startswith("defaults:") or line.strip() == "shared_infra:":
            in_shared = "shared_infra" in line or line.startswith("defaults:")
            in_priority = False
            current_area = None
            in_components = False
            continue
        if line.startswith("priority:"):
            in_priority = True
            in_shared = False
            current_area = None
            in_components = False
            continue
        m_area = re.match(r"^  ([a-z0-9]+):\s*$", line)
        if m_area and not in_priority:
            current_area = m_area.group(1)
            areas[current_area] = {
                "display_name": current_area,
                "seed": "",
                "components": [],
            }
            in_components = False
            in_shared = False
            continue
        if current_area:
            if re.match(r"^    display_name:\s*(.+)$", line):
                areas[current_area]["display_name"] = re.match(
                    r"^    display_name:\s*(.+)$", line
                ).group(1).strip()
            elif re.match(r"^    seed:\s*(.+)$", line):
                areas[current_area]["seed"] = re.match(
                    r"^    seed:\s*(.+)$", line
                ).group(1).strip()
            elif line.strip() == "components:":
                in_components = True
            elif in_components and line.strip().startswith("- "):
                areas[current_area]["components"].append(
                    line.strip()[2:].split()[0]
                )
        if in_shared and line.strip().startswith("- "):
            shared.append(line.strip()[2:].split()[0])
        if in_priority and line.strip().startswith("- "):
            # - purch: procurement
            body = line.strip()[2:]
            if ":" in body:
                k, v = body.split(":", 1)
                priority.append({k.strip(): v.strip()})
    return {
        "areas": areas,
        "defaults": {"shared_infra": shared, "blast_radius": "full-suite"},
        "priority": priority,
    }


def component_of_path(rel: str) -> str | None:
    parts = Path(rel).parts
    if not parts:
        return None
    # e.g. ordstr/source/ordstr/database/Foo.plsql
    return parts[0].lower()


def classify_file(rel: str) -> dict[str, Any]:
    """Layer 0 mapping: any file kind → entity/package/svc candidates."""
    p = Path(rel.replace("\\", "/"))
    stem = p.stem
    suffix = p.suffix.lower()
    component = component_of_path(rel)
    mapped: dict[str, Any] = {
        "path": rel.replace("\\", "/"),
        "component": component,
        "kind": suffix.lstrip(".") or "unknown",
        "entities": [],
        "packages": [],
        "services": [],
        "projections": [],
    }
    if suffix in {".plsql", ".views", ".utility", ".storage", ".entity", ".enumeration"}:
        api = pascal_to_snake_api(stem)
        mapped["entities"].append(stem)
        mapped["packages"].append(api)
        # Also without _API if already ends with API naming
        if stem.upper().endswith("_API"):
            mapped["packages"].append(stem.upper())
    elif suffix == ".plsvc":
        mapped["entities"].append(stem)
        mapped["packages"].append(f"{pascal_to_snake_api(stem)[:-4]}_SVC" if False else pascal_to_snake_api(stem).replace("_API", "_SVC"))
        # plsvc often named like RunCapabilityCheck → RunCapabilityCheck.svc via projection
        mapped["services"].append(f"{stem}.svc")
        mapped["projections"].append(stem)
    elif suffix == ".projection":
        mapped["projections"].append(stem)
        mapped["services"].append(f"{stem}.svc")
        # Conventional Handling projection name
        if not stem.endswith("Handling"):
            mapped["services"].append(f"{stem}Handling.svc")
    elif suffix in {".client", ".fragment"}:
        mapped["projections"].append(stem)
    elif suffix == ".cdb" or suffix == ".upg" or "database" in str(p).lower():
        mapped["entities"].append(stem)
        mapped["packages"].append(pascal_to_snake_api(stem))
    else:
        # Still map stem as weak entity for search
        mapped["entities"].append(stem)
    # de-dupe
    for k in ("entities", "packages", "services", "projections"):
        mapped[k] = sorted(set(mapped[k]))
    return mapped


def git_changed_files(base: str | None, head: str | None, files: list[str] | None) -> list[str]:
    if files:
        return [f.replace("\\", "/") for f in files]
    if not base and not head:
        # Working tree changes
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        names = [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        names += [ln.strip().replace("\\", "/") for ln in untracked.splitlines() if ln.strip()]
        return sorted(set(names))
    base = base or "HEAD~1"
    head = head or "HEAD"
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        text=True,
    )
    return [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]


def cmd_parse_diff(args: argparse.Namespace) -> None:
    changed = git_changed_files(args.base, args.head, args.files)
    mapped_files = [classify_file(f) for f in changed]
    areas = []
    cmap = load_component_map()
    for mf in mapped_files:
        am = area_for_component(mf.get("component"), cmap)
        if am and am not in areas:
            areas.append(am)
    emit(
        {
            "tool": "parse_diff",
            "workspace": str(ROOT),
            "base": args.base,
            "head": args.head,
            "changed_file_count": len(changed),
            "changed_files": mapped_files,
            "product_areas": areas,
            "zero_map": [
                mf["path"]
                for mf in mapped_files
                if not (mf["packages"] or mf["services"] or mf["entities"])
            ],
        }
    )


def area_for_component(component: str | None, cmap: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not component:
        return None
    cmap = cmap or load_component_map()
    component = component.lower()
    shared = (cmap.get("defaults") or {}).get("shared_infra") or []
    if component in shared:
        return {
            "component": component,
            "product_area": "shared_infra",
            "display_name": "Shared Infrastructure",
            "seed": None,
            "blast_radius": (cmap.get("defaults") or {}).get("blast_radius", "full-suite"),
            "confidence": "LOW",
        }
    # priority overrides
    for item in cmap.get("priority") or []:
        if isinstance(item, dict) and component in item:
            slug = item[component]
            area = (cmap.get("areas") or {}).get(slug, {})
            return {
                "component": component,
                "product_area": slug,
                "display_name": area.get("display_name", slug),
                "seed": area.get("seed"),
                "confidence": "MED",
                "via": "priority",
            }
    for slug, area in (cmap.get("areas") or {}).items():
        comps = [c.lower() for c in (area.get("components") or [])]
        if component in comps:
            return {
                "component": component,
                "product_area": slug,
                "display_name": area.get("display_name", slug),
                "seed": area.get("seed"),
                "confidence": "HIGH",
            }
    return {
        "component": component,
        "product_area": None,
        "display_name": None,
        "seed": None,
        "confidence": "LOW",
        "note": "unmapped component — apply area-seed fallback or tag your area",
    }


def cmd_area_map(args: argparse.Namespace) -> None:
    emit(
        {
            "tool": "area_map",
            "result": area_for_component(args.component),
            "map_path": str(MAP_PATH.relative_to(ROOT)).replace("\\", "/"),
        }
    )


def _rg_bin() -> str:
    rg = os.environ.get(
        "RG_PATH",
        r"c:\Program Files\cursor\resources\app\node_modules\@vscode\ripgrep\bin\rg.exe",
    )
    return rg if Path(rg).is_file() else "rg"


def rg_search(
    pattern: str,
    roots: list[Path],
    glob: str | None = None,
    max_hits: int = 200,
    extra_globs: list[str] | None = None,
) -> list[dict[str, Any]]:
    cmd = [
        _rg_bin(),
        "-n",
        "--no-heading",
        "-S",
        "-i",  # IFS mixes Interim_Ctp_Manager_API / INTERIM_CTP_MANAGER_API
        "--max-count",
        "3",  # per-file early stop
        pattern,
    ]
    if glob:
        # support brace-less multi-glob via repeated --glob
        if glob.startswith("*.{") and glob.endswith("}"):
            inner = glob[3:-1]
            for ext in inner.split(","):
                cmd.extend(["--glob", f"*.{ext.strip()}"])
        else:
            cmd.extend(["--glob", glob])
    for g in extra_globs or []:
        cmd.extend(["--glob", g])
    cmd.extend(
        [
            "--glob",
            "!**/node_modules/**",
            "--glob",
            "!**/.git/**",
            "--glob",
            "!**/bin/**",
            "--glob",
            "!**/build/**",
            "--glob",
            "!**/generated/**",
        ]
    )
    for root in roots:
        if root.exists():
            cmd.append(str(root))
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    hits: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        # path:line:content  (paths relative when cwd=ROOT and root is relative)
        m = re.match(r"^(.*?):(\d+):(.*)$", line)
        if not m:
            continue
        path, lineno, content = m.group(1), int(m.group(2)), m.group(3)
        rel = path.replace("\\", "/")
        if Path(rel).is_absolute():
            try:
                rel = str(Path(rel).relative_to(ROOT)).replace("\\", "/")
            except Exception:
                pass
        hits.append({"path": rel, "line": lineno, "text": content.strip()})
        if len(hits) >= max_hits:
            break
    return hits


def suite_for_mkd(path: str) -> str | None:
    """Map a util/test .mkd to its suite orchestrator .mkd when possible."""
    p = Path(path.replace("\\", "/"))
    parts = list(p.parts)
    if "inttst" not in parts:
        return None
    # .../<num>/<Feature>/tests|util/Foo.mkd → .../<num>/<Feature>/<Feature>.mkd
    try:
        idx = parts.index("inttst")
    except ValueError:
        return None
    # inttst/test/inttst/<num>/<Feature>/...
    if len(parts) < idx + 5:
        # maybe already a suite file
        if path.endswith(".mkd"):
            return path
        return None
    num = parts[idx + 3] if parts[idx + 1] == "test" else parts[idx + 1]
    # normalize: find Feature folder
    # path like inttst/test/inttst/6.4.2.1/RunCapabilityCheck/util/X.mkd
    base_parts = parts[: idx + 4]  # through numbered folder
    # next part is Feature
    if len(parts) <= idx + 4:
        return path
    feature = parts[idx + 4]
    suite = ROOT.joinpath(*base_parts, feature, f"{feature}.mkd")
    # Sometimes suite is at <num>/<Feature>.mkd (collection)
    if suite.is_file():
        return str(suite.relative_to(ROOT)).replace("\\", "/")
    coll = ROOT.joinpath(*base_parts, f"{feature}.mkd")
    if coll.is_file():
        return str(coll.relative_to(ROOT)).replace("\\", "/")
    # If the hit is already the suite file
    if Path(ROOT, path).is_file() and "/tests/" not in path and "/util/" not in path:
        return path
    return path


def resolve_terms(terms: Iterable[str], max_hits_per_term: int = 80) -> dict[str, Any]:
    """One ripgrep pass over inttst (OR of all terms) — full scans are ~1min each on Windows."""
    if not INTTST.is_dir():
        return {"error": f"inttst not found at {INTTST}", "candidates": []}

    term_list = [t.strip() for t in terms if t and t.strip()]
    # de-dupe, drop very short / noisy tokens
    seen: set[str] = set()
    uniq: list[str] = []
    for t in term_list:
        if len(t) < 4 or t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    if not uniq:
        return {"candidates": [], "term_count": 0}

    # Two-pass search: precise CTP/CC terms first (avoid CO-line .svc flooding the budget)
    def _precise(t: str) -> bool:
        tl = t.lower()
        return any(
            k in tl
            for k in (
                "capabilitycheck",
                "runcapability",
                "performcapability",
                "interimctp",
                "interim_ctp",
                "interimorderheader",
                "salesinterim",
            )
        )

    precise = [t for t in uniq if _precise(t)]
    broad = [t for t in uniq if t not in precise]
    # Prefer .svc among broad, but keep them secondary
    broad_svc = [t for t in broad if t.endswith(".svc")]
    broad_other = [t for t in broad if t not in broad_svc]

    hits: list[dict[str, Any]] = []
    search_terms: list[str] = []
    for batch, budget in (
        (precise[:10], max(80, max_hits_per_term)),
        ((broad_svc + broad_other)[:6], 40),
    ):
        if not batch:
            continue
        search_terms.extend(batch)
        pattern = "|".join(re.escape(t) for t in batch)
        hits.extend(rg_search(pattern, [INTTST], glob="*.mkd", max_hits=budget))

    candidates: dict[str, dict[str, Any]] = {}
    for h in hits:
        matched = [t for t in search_terms if t in h["text"]]
        if not matched:
            # regex word-ish fallback: substring match case-sensitive as mkd uses PascalCase
            matched = [t for t in search_terms if t.lower() in h["text"].lower()]
        suite = suite_for_mkd(h["path"]) or h["path"]
        entry = candidates.setdefault(
            suite,
            {
                "script": suite,
                "evidence": [],
                "matched_terms": set(),
                "hit_files": set(),
            },
        )
        for t in matched or ["(pattern)"]:
            entry["matched_terms"].add(t)
        entry["hit_files"].add(h["path"])
        if len(entry["evidence"]) < 8:
            entry["evidence"].append(
                {
                    "file": h["path"],
                    "line": h["line"],
                    "text": h["text"][:240],
                    "term": matched[0] if matched else search_terms[0],
                }
            )

    out = []
    for suite, data in candidates.items():
        out.append(
            {
                "script": suite,
                "matched_terms": sorted(data["matched_terms"]),
                "evidence": data["evidence"],
                "supporting_files": sorted(data["hit_files"])[:20],
                "evidence_count": len(data["evidence"]),
            }
        )
    def _score(c: dict[str, Any]) -> tuple:
        terms = " ".join(c["matched_terms"]).lower()
        script = c["script"].lower()
        score = 0
        for key in (
            "capabilitycheck",
            "runcapability",
            "interimorder",
            "ctp",
            "performcapability",
        ):
            if key in terms or key in script:
                score += 10
        # Broad CO/quotation Handling matches are weak unless script also looks CTP-related
        for weak in ("customerorderlineshandling", "salesquotationlineshandling"):
            if weak in terms and score < 10:
                score -= 5
        score += min(c["evidence_count"], 5)
        return (-score, -c["evidence_count"], c["script"])

    out.sort(key=_score)
    for c in out:
        c["rank_score"] = -_score(c)[0]
    return {
        "candidates": out,
        "term_count": len(uniq),
        "searched_terms": search_terms,
        "hit_count": len(hits),
    }


def cmd_resolve_sar_candidates(args: argparse.Namespace) -> None:
    terms: list[str] = []
    if args.svc:
        svc = args.svc if args.svc.endswith(".svc") else f"{args.svc}.svc"
        terms.append(svc)
        terms.append(svc.replace(".svc", ""))
    if args.package:
        terms.append(args.package.upper())
    if args.entity:
        terms.append(args.entity)
        terms.append(pascal_to_snake_api(args.entity))
        # Only invent Handling.svc when --svc not given and name already looks like a projection
        if args.entity.endswith("Handling"):
            terms.append(f"{args.entity}.svc")
    if args.term:
        terms.extend(args.term)

    seen = set()
    uniq = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    result = resolve_terms(uniq, max_hits_per_term=args.max_hits)
    for c in result.get("candidates", []):
        c["suite_dir"] = str(Path(c["script"]).parent).replace("\\", "/")
    emit(
        {
            "tool": "resolve_sar_candidates",
            "terms": uniq,
            "candidate_count": len(result.get("candidates", [])),
            **result,
        }
    )


def _impact_search_roots(hint_components: list[str] | None = None) -> list[Path]:
    """Keep impact_graph fast: only scan likely IFS component trees."""
    preferred = [
        "order",
        "ordstr",
        "purch",
        "invent",
        "manuf",
        "mrp",
        "crp",
        "dop",
        "shopor",
        "shpopr",
        "mfgstd",
        "mpccom",
        "pdmcon",
        "partca",
        "proj",
        "equip",
        "wo",
        "person",
        "accrul",
        "invoic",
        "genled",
        "adcom",
        "crm",
    ]
    names = list(hint_components or [])
    for n in preferred:
        if n not in names:
            names.append(n)
    roots: list[Path] = []
    for name in names:
        p = ROOT / name
        if p.is_dir():
            # Prefer source/model only when present
            for sub in ("source", "model"):
                sp = p / sub
                if sp.is_dir():
                    roots.append(sp)
            if not any((p / s).is_dir() for s in ("source", "model")):
                roots.append(p)
    return roots or [ROOT]


def find_callers(
    package: str,
    depth: int,
    max_per_hop: int = 60,
    hint_components: list[str] | None = None,
) -> dict[str, Any]:
    """Static impact graph via ripgrep (no DB ALL_DEPENDENCIES required)."""
    package = package.upper()
    if not package.endswith("_API") and not package.endswith("_SVC"):
        package = package if "_" in package else pascal_to_snake_api(package)

    visited: set[str] = set()
    layers: list[dict[str, Any]] = []
    frontier = [package]
    search_roots = _impact_search_roots(hint_components)

    for hop in range(1, depth + 1):
        hop_nodes = []
        next_frontier: list[str] = []
        for pkg in frontier:
            if pkg in visited:
                continue
            visited.add(pkg)
            forms = api_search_forms(pkg)
            # Prefer IFS title-case form in alternation
            pattern = "|".join(re.escape(f) for f in forms[:3])
            hits = rg_search(
                pattern,
                search_roots,
                glob="*.{plsql,plsvc,projection,views}",
                max_hits=max_per_hop,
            )
            entity = re.sub(r"_API$|_SVC$", "", pkg)
            entity_pascal = "".join(p.capitalize() for p in entity.lower().split("_"))
            # Extract caller packages / services from hit paths + text
            pkg_forms_l = [f.lower() for f in forms]
            for h in hits:
                text_l = h["text"].lower()
                # Skip hits that only matched the Pascal entity token in unrelated text
                if not any(f in text_l for f in pkg_forms_l if "_" in f or f.endswith("_api")):
                    # allow projection/plsvc filename matches for the entity itself
                    if entity_pascal.lower() not in Path(h["path"]).stem.lower():
                        if not any(f.lower() in text_l for f in forms):
                            continue
                caller_pkg = None
                caller_svc = None
                path = h["path"]
                stem = Path(path).stem
                suf = Path(path).suffix.lower()
                if suf == ".plsql":
                    caller_pkg = pascal_to_snake_api(stem)
                    # Skip self-edges for the root package body
                    if caller_pkg == package.upper():
                        continue
                elif suf == ".plsvc":
                    caller_svc = f"{stem}.svc"
                    caller_pkg = pascal_to_snake_api(stem).replace("_API", "_SVC")
                elif suf == ".projection":
                    # Only attribute .svc when this projection text references the API
                    if any(f.lower() in text_l for f in forms if "_api" in f.lower() or "_API" in f):
                        caller_svc = f"{stem}.svc"
                    elif any(f in text_l for f in pkg_forms_l):
                        caller_svc = f"{stem}.svc"
                for m in API_CALL_RE.finditer(h["text"]):
                    api = m.group(1).upper()
                    if api != package.upper() and api not in visited:
                        next_frontier.append(api)
                hop_nodes.append(
                    {
                        "from": pkg,
                        "path": path,
                        "line": h["line"],
                        "text": h["text"][:200],
                        "caller_package": caller_pkg,
                        "caller_service": caller_svc,
                        "entity_hint": entity_pascal,
                    }
                )
                if caller_pkg and caller_pkg not in visited:
                    next_frontier.append(caller_pkg)
        layers.append({"hop": hop, "edge_count": len(hop_nodes), "edges": hop_nodes[:120]})
        frontier = []
        for n in next_frontier:
            if n not in visited and n not in frontier:
                frontier.append(n)
        # Cap fan-out to keep select interactive
        frontier = frontier[:25]
        if not frontier:
            break

    packages = sorted(visited)
    services = sorted(
        {
            e["caller_service"]
            for layer in layers
            for e in layer["edges"]
            if e.get("caller_service")
        }
    )
    return {
        "root_package": package,
        "depth": depth,
        "packages_seen": packages,
        "services_seen": services,
        "layers": layers,
        "search_roots": [str(r.relative_to(ROOT)).replace("\\", "/") for r in search_roots[:12]],
        "note": "Static ripgrep graph (not DB ALL_DEPENDENCIES). Cite edge path:line as evidence.",
    }


def cmd_impact_graph(args: argparse.Namespace) -> None:
    target = args.package or args.entity
    if not target:
        emit({"error": "Provide --package or --entity"})
        return
    graph = find_callers(target, depth=args.depth, max_per_hop=args.max_per_hop)
    # Auto-resolve SAR candidates for discovered services + root
    terms = [graph["root_package"], *graph.get("services_seen", [])]
    if args.entity:
        terms.append(args.entity)
    sar = resolve_terms(terms[:30], max_hits_per_term=40)
    emit(
        {
            "tool": "impact_graph",
            "graph": graph,
            "sar_candidates_from_graph": sar.get("candidates", [])[:40],
            "sar_candidate_count": len(sar.get("candidates", [])),
        }
    )


def cmd_read_script(args: argparse.Namespace) -> None:
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        emit({"error": f"not found: {args.path}"})
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    start = max(1, args.start or 1)
    end = min(len(lines), args.end or len(lines))
    snippet = "\n".join(
        f"{i}:{lines[i - 1]}" for i in range(start, end + 1)
    )
    emit(
        {
            "tool": "read_script",
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "start": start,
            "end": end,
            "total_lines": len(lines),
            "content": snippet,
        }
    )


def cmd_select(args: argparse.Namespace) -> None:
    """One-shot retrieve pipeline: parse → impact (source) → resolve (one inttst pass)."""
    changed = git_changed_files(args.base, args.head, args.files)
    mapped = [classify_file(f) for f in changed]
    cmap = load_component_map()
    packages: list[str] = []
    seed_terms: list[str] = []
    areas = []
    for mf in mapped:
        packages.extend(mf["packages"])
        seed_terms.extend(mf["packages"])
        seed_terms.extend(mf["services"])
        seed_terms.extend(mf["entities"])
        am = area_for_component(mf.get("component"), cmap)
        if am and am not in areas:
            areas.append(am)

    hint_comps = sorted(
        {mf.get("component") for mf in mapped if mf.get("component")}
    )
    # Expand hint with manufacturing/order neighbors when ordstr/order touched
    if any(c in ("ordstr", "order") for c in hint_comps):
        hint_comps = sorted(set(hint_comps) | {"ordstr", "order", "dop", "mrp", "crp", "invent"})

    graphs = []
    for pkg in packages[:2]:
        graphs.append(
            find_callers(
                pkg,
                depth=args.depth,
                max_per_hop=50,
                hint_components=hint_comps,
            )
        )

    terms: list[str] = []
    # Prefer precise .svc from impact edges that actually call the API
    for g in graphs:
        for svc in g.get("services_seen", []):
            terms.append(svc)
        for layer in g.get("layers") or []:
            for e in layer.get("edges") or []:
                if e.get("caller_service"):
                    terms.append(e["caller_service"])
    # Seed packages / entities last (low precision in .mkd)
    for t in seed_terms:
        if t.endswith(".svc") or t.endswith("_API") or t.endswith("_SVC"):
            terms.append(t)
    # Title-case API form helps when mkd embeds SQL/PL fragments
    for pkg in packages[:2]:
        for form in api_search_forms(pkg):
            if "_" in form:
                terms.append(form)

    seen = set()
    uniq_terms = []
    for t in terms:
        if t and t not in seen:
            seen.add(t)
            uniq_terms.append(t)

    # If CC engine services appear, also resolve the CO action entry-point
    if any("CapabilityCheck" in t or "RunCapability" in t for t in uniq_terms):
        for extra in (
            "CustomerOrderHandling.svc",
            "PerformCapabilityCheck",
            "CapabilityCheckResultHandling.svc",
            "RunCapabilityCheck.svc",
        ):
            if extra not in seen:
                uniq_terms.append(extra)
                seen.add(extra)

    resolved = resolve_terms(uniq_terms, max_hits_per_term=80)
    # Keep high-signal suites first; still return broad list for agent prune
    strong = [c for c in resolved.get("candidates", []) if c.get("rank_score", 0) >= 10]
    weak = [c for c in resolved.get("candidates", []) if c.get("rank_score", 0) < 10]
    emit(
        {
            "tool": "select",
            "changed_files": mapped,
            "product_areas": areas,
            "terms": uniq_terms,
            "impact_graphs": [
                {
                    "root_package": g["root_package"],
                    "packages_seen": g["packages_seen"],
                    "services_seen": g["services_seen"],
                    "hop1_edge_count": (g["layers"][0]["edge_count"] if g["layers"] else 0),
                    "sample_edges": (g["layers"][0]["edges"][:15] if g["layers"] else []),
                }
                for g in graphs
            ],
            "recommended_candidates": strong,
            "candidates": resolved.get("candidates", []),
            "candidate_count": len(resolved.get("candidates", [])),
            "recommended_count": len(strong),
            "weak_candidate_count": len(weak),
            "searched_terms": resolved.get("searched_terms", []),
            "fallback": (
                "area-seed"
                if not resolved.get("candidates") and areas
                else "none"
            ),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Connected SAR local analyzers")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_diff = sub.add_parser("parse_diff", help="Map changed files → entities/services")
    p_diff.add_argument("--base")
    p_diff.add_argument("--head")
    p_diff.add_argument("--files", nargs="*", help="Explicit file list (skip git)")
    p_diff.set_defaults(func=cmd_parse_diff)

    p_res = sub.add_parser(
        "resolve_sar_candidates", help="Find .mkd scripts referencing entity/svc/package"
    )
    p_res.add_argument("--entity")
    p_res.add_argument("--svc")
    p_res.add_argument("--package")
    p_res.add_argument("--term", nargs="*", help="Extra search terms")
    p_res.add_argument("--max-hits", type=int, default=80)
    p_res.set_defaults(func=cmd_resolve_sar_candidates)

    p_imp = sub.add_parser("impact_graph", help="Static caller graph + SAR candidates")
    p_imp.add_argument("--package")
    p_imp.add_argument("--entity")
    p_imp.add_argument("--depth", type=int, default=1)
    p_imp.add_argument("--max-per-hop", type=int, default=60)
    p_imp.set_defaults(func=cmd_impact_graph)

    p_area = sub.add_parser("area_map", help="Component → product area")
    p_area.add_argument("--component", required=True)
    p_area.set_defaults(func=cmd_area_map)

    p_read = sub.add_parser("read_script", help="Read .mkd with line numbers")
    p_read.add_argument("--path", required=True)
    p_read.add_argument("--start", type=int)
    p_read.add_argument("--end", type=int)
    p_read.set_defaults(func=cmd_read_script)

    p_sel = sub.add_parser("select", help="One-shot retrieve pipeline")
    p_sel.add_argument("--base")
    p_sel.add_argument("--head")
    p_sel.add_argument("--files", nargs="*")
    p_sel.add_argument("--depth", type=int, default=1)
    p_sel.set_defaults(func=cmd_select)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
