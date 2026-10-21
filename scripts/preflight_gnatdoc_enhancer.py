#!/usr/bin/env python3
"""Optional, isolated compatibility preflight of the shared GNATdoc enhancer.

Nothing here is a production or documentation-build dependency. Given a local
ada-gnatdoc-enhancer Git checkout and an exact reviewed revision, the driver:

1. exports that revision with ``git archive`` into a new workspace, installs it
   (non-editable) into a private virtual environment and proves that every
   installed module and asset is byte-identical to the reviewed Git blobs;
2. stages byte-identical copies of the four public specifications listed in
   docs_api.gpr (the enhancer's discovery is recursive, and src/internal holds
   internal units that are never published);
3. runs the supported inventory, dry-run, enhance and verify operations with a
   conservative profile (theme, highlighting, local package navigation; no type
   links, external Core links, generic-instance augmentation or guides);
4. independently compares native identities (h1/h4 text and ids, native ids
   and hrefs, declaration code text, native CSS), local links and URLs, checks
   byte-idempotence and two-fresh-copy determinism, and confirms that source,
   native HTML, asset and manifest mutations are rejected by ``verify``.

The pristine native site is never modified; every operation uses copies.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gnatdoc_enhancer_support import (  # noqa: E402
    SupportError as PreflightError, compare_native, install, public_specifications,
    run, sha256, tree_hashes)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = """schema_version = 1
project = "OpenCV Features Ada"
[gnatdoc]
version = "26.0.0"
[sources]
directories = ["qualification-public/src"]
packages = [{packages}]
comment_style = "leading"
[navigation]
mode = "packages"
[presentation]
theme = true
syntax_highlighting = true
type_links = {type_links}
[guides]
mode = "none"
[security]
external_hosts = []
"""


def project(workspace: Path, name: str, site: Path, specs: list[str], type_links: bool) -> Path:
    root = workspace / name
    (root / "docs").mkdir(parents=True)
    staged = root / "qualification-public/src"
    staged.mkdir(parents=True)
    for spec in specs:
        shutil.copyfile(ROOT / "src" / spec, staged / spec)
        if sha256(staged / spec) != sha256(ROOT / "src" / spec):
            raise PreflightError(f"staged {spec} differs")
    packages = ", ".join(f'"{p}"' for p in sorted(_package_names(staged)))
    (root / "docs/gnatdoc-enhance.toml").write_text(
        CONFIG.format(packages=packages, type_links=str(type_links).lower()))
    shutil.copytree(site, root / "_site")
    return root


def _package_names(directory: Path) -> list[str]:
    names = []
    for path in directory.glob("*.ads"):
        match = re.search(r"^package\s+([\w.]+)\s+is\b", path.read_text(), re.M)
        names.append(match[1])
    return names


def enhancer(tool: Path, command: str, root: Path, *extra: str, check: bool = True):
    result = run(str(tool), command, "--source-root", str(root), "--config",
                 "docs/gnatdoc-enhance.toml", "--site", "_site", *extra, check=check)
    return json.loads(result.stdout) if result.returncode == 0 else result


MUTATIONS = (
    ("native anchor id", "page", lambda t: re.sub(r"<h4 id=([0-9a-f]{8})", r"<h4 id=00000000", t, count=1)),
    ("native heading text", "page", lambda t: t.replace("</h4>", "X</h4>", 1)),
    ("native stylesheet", "api/gnatdoc.css", lambda t: t + "\n/* altered */\n"),
    ("theme asset", "api/gnatdoc-theme.css", lambda t: t + "\n/* altered */\n"),
    ("navigation asset", "api/gnatdoc-navigation.js", lambda t: t + "\n// altered\n"),
    ("presentation manifest", "api/presentation.json", lambda t: t.replace('"', "'", 1)),
    ("injected script", "page", lambda t: t.replace("<h1>", "<script>alert(1)</script><h1>", 1)),
    ("injected external URL", "page", lambda t: t.replace("<h1>", "<a href=https://example.com>x</a><h1>", 1)),
    ("staged source default value", "source", lambda t: t.replace(":= 500;", ":= 501;", 1)),
    ("staged source comment", "source", lambda t: t.replace("--", "-- altered", 1)),
)


def mutations(tool: Path, enhanced: Path, workspace: Path, page: str) -> dict:
    result = {}
    for label, target, change in MUTATIONS:
        copy = workspace / "mutation"
        if copy.exists():
            shutil.rmtree(copy)
        shutil.copytree(enhanced, copy)
        if target == "page":
            path = copy / "_site/api" / page
        elif target == "source":
            path = copy / "qualification-public/src/opencv-features-orb.ads"
        else:
            path = copy / "_site" / target
        original = path.read_text()
        altered = change(original)
        if altered == original:
            raise PreflightError(f"mutation {label!r} did not apply")
        path.write_text(altered)
        outcome = enhancer(tool, "verify", copy, check=False)
        rejected = not isinstance(outcome, dict)
        result[label] = (outcome.stderr.strip().splitlines() or ["rejected"])[-1] \
            if rejected else "NOT REJECTED"
    extra = workspace / "mutation"
    shutil.rmtree(extra)
    shutil.copytree(enhanced, extra)
    (extra / "_site/api/extra.html").write_text("<!DOCTYPE html>")
    outcome = enhancer(tool, "verify", extra, check=False)
    result["unapproved extra file"] = ("NOT REJECTED" if isinstance(outcome, dict)
                                       else outcome.stderr.strip().splitlines()[-1])
    shutil.rmtree(extra)
    return result


def preflight(checkout: Path, revision: str, site: Path, workspace: Path) -> dict:
    if workspace.exists():
        raise PreflightError(f"{workspace} must not exist")
    workspace.mkdir(parents=True)
    pristine_hashes = tree_hashes(site)
    tool = install(checkout, revision, workspace / "venv")
    record = json.loads((workspace / "venv/gnatdoc-enhancer-provenance.json").read_text())
    provenance = {"revision": revision, "version": record["version"],
                  "installed_files": len(record["files"]), "installed_equals_revision": True,
                  "assets": {k: v for k, v in record["files"].items() if k.startswith("assets/")}}
    specs = public_specifications()
    report = {"enhancer": provenance, "staged_public_specifications": specs,
              "pristine_site": pristine_hashes}
    # The real layout, unstaged, exercises recursive discovery of src/internal.
    layout = workspace / "unstaged"
    (layout / "docs").mkdir(parents=True)
    shutil.copytree(ROOT / "src", layout / "src")
    shutil.copytree(site, layout / "_site")
    (layout / "docs/gnatdoc-enhance.toml").write_text(
        CONFIG.replace("qualification-public/src", "src").format(
            packages=", ".join(f'"{p}"' for p in sorted(_package_names(ROOT / "src"))),
            type_links="false"))
    outcome = enhancer(tool, "inventory", layout, check=False)
    report["unstaged_repository_layout"] = (
        "accepted" if isinstance(outcome, dict) else outcome.stderr.strip())
    profiles = {}
    for name, type_links in (("conservative", False), ("local-type-links", True)):
        root = project(workspace, name, site, specs, type_links)
        entry = {"inventory": enhancer(tool, "inventory", root)}
        before = tree_hashes(root / "_site")
        entry["dry_run"] = enhancer(tool, "enhance", root, "--dry-run")
        entry["dry_run_left_site_unchanged"] = tree_hashes(root / "_site") == before
        entry["enhance"] = enhancer(tool, "enhance", root)
        entry["verify"] = enhancer(tool, "verify", root)
        once = tree_hashes(root / "_site")
        enhancer(tool, "enhance", root)
        entry["byte_idempotent"] = tree_hashes(root / "_site") == once
        fresh = project(workspace, f"{name}-fresh", site, specs, type_links)
        enhancer(tool, "enhance", fresh)
        entry["two_fresh_runs_identical"] = tree_hashes(fresh / "_site") == once
        entry["native_comparison"] = compare_native(site / "api", root / "_site/api")
        entry["enhanced_site"] = once
        if name == "conservative":
            native_page = json.loads((ROOT / "docs/gnatdoc-native-anchors.json").read_text())[
                "packages"]["OpenCV.Features.ORB"]["page"]
            entry["mutations"] = mutations(tool, root, workspace, native_page)
        profiles[name] = entry
    report["profiles"] = profiles
    report["pristine_site_unchanged"] = tree_hashes(site) == pristine_hashes
    failures = []
    for name, entry in profiles.items():
        for key in ("dry_run_left_site_unchanged", "byte_idempotent", "two_fresh_runs_identical"):
            if not entry[key]:
                failures.append(f"{name}: {key}")
        failures += [f"{name}: {e}" for e in entry["native_comparison"]["errors"]]
        failures += [f"{name}: mutation accepted: {k}" for k, v in entry.get("mutations", {}).items()
                     if v == "NOT REJECTED"]
    if not report["pristine_site_unchanged"]:
        failures.append("pristine site changed")
    report["result"] = "pass" if not failures else "fail"
    report["failures"] = failures
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--enhancer", type=Path, required=True, help="enhancer Git checkout")
    parser.add_argument("--revision", required=True, help="full reviewed commit SHA")
    parser.add_argument("--site", type=Path, default=ROOT / "_site",
                        help="pristine native site containing api/ (default _site)")
    parser.add_argument("--workspace", type=Path, required=True, help="new directory")
    parser.add_argument("--report", type=Path, help="JSON report destination")
    args = parser.parse_args(argv)
    try:
        report = preflight(args.enhancer.resolve(), args.revision, args.site.resolve(),
                           args.workspace.resolve())
    except (PreflightError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(f"{report['result'].upper()}: {len(report['failures'])} failures")
    for failure in report["failures"]:
        print(f"  {failure}")
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
