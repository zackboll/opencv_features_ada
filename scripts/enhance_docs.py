#!/usr/bin/env python3
"""Enhance an isolated copy of the qualified native GNATdoc site.

Run after scripts/generate_docs.sh. The pristine native site (default
``_site``) is never modified; the enhanced copy is written to ``_site-enhanced``
(rebuilt) or to a new directory. The driver:

1. re-checks the installed enhancer against the pinned revision and its
   recorded provenance, and the packaged assets against
   docs/gnatdoc-enhanced-assets.json;
2. stages byte-identical copies of the docs_api.gpr specifications under
   obj/docs/enhancer-sources (discovery is recursive; src/internal is never
   published) and runs inventory, a dry run, enhance and verify;
3. requires byte-idempotent re-enhancement, an identical fresh second
   enhancement, preserved native identities, resolved local links, no
   external URL and exactly the inventoried added files and scripts;
4. confirms the pristine native site is unchanged.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gnatdoc_enhancer_support as support  # noqa: E402

ROOT = support.ROOT
CONFIG = "docs/gnatdoc-enhance.toml"
ASSETS = "docs/gnatdoc-enhanced-assets.json"
STAGE = "obj/docs/enhancer-sources"


class EnhanceError(RuntimeError):
    pass


def enhance(environment: Path, native: Path, output: Path, root: Path = ROOT) -> dict:
    manifest = json.loads((root / ASSETS).read_text())
    tool, provenance = support.verified_tool(environment, manifest["enhancer_revision"])
    if provenance["version"] != manifest["enhancer_version"]:
        raise EnhanceError(f"enhancer version {provenance['version']} differs")
    for name, digest in manifest["packaged_assets"].items():
        if provenance["files"].get(f"assets/{name}") != digest:
            raise EnhanceError(f"packaged asset {name} differs from the inventory")
    pristine = support.tree_hashes(native)
    stage = root / STAGE
    if stage.exists():
        shutil.rmtree(stage)
    specs = support.stage_public_sources(stage, root)
    if output.exists():
        if output != root / "_site-enhanced":
            raise EnhanceError(f"{output} exists; use a new directory")
        shutil.rmtree(output)
    shutil.copytree(native, output)
    report = {"enhancer": {"revision": provenance["revision"], "version": provenance["version"]},
              "staged_specifications": specs}
    report["inventory"] = support.enhancer(tool, "inventory", root, CONFIG, output)
    if report["inventory"].get("public_packages") != manifest["public_packages"]:
        raise EnhanceError(f"enhancer inventory {report['inventory']} differs")
    before = support.tree_hashes(output)
    report["dry_run"] = support.enhancer(tool, "enhance", root, CONFIG, output, "--dry-run")
    if support.tree_hashes(output) != before:
        raise EnhanceError("dry run modified the site")
    report["enhance"] = support.enhancer(tool, "enhance", root, CONFIG, output)
    report["verify"] = support.enhancer(tool, "verify", root, CONFIG, output)
    once = support.tree_hashes(output)
    support.enhancer(tool, "enhance", root, CONFIG, output)
    if support.tree_hashes(output) != once:
        raise EnhanceError("re-enhancement is not byte-idempotent")
    with tempfile.TemporaryDirectory() as directory:
        fresh = Path(directory) / "site"
        shutil.copytree(native, fresh)
        support.enhancer(tool, "enhance", root, CONFIG, fresh)
        if support.tree_hashes(fresh) != once:
            raise EnhanceError("a fresh enhancement differs")
    comparison = support.compare_native(native / "api", output / "api")
    if comparison["errors"]:
        raise EnhanceError(f"native comparison failed: {comparison['errors']}")
    if comparison["added_files"] != sorted(manifest["added_files"]):
        raise EnhanceError(f"added files {comparison['added_files']} differ from the inventory")
    if comparison["scripts"] != manifest["scripts"]:
        raise EnhanceError(f"scripts {comparison['scripts']} differ from the inventory")
    for name, digest in manifest["packaged_assets"].items():
        if support.sha256(output / "api" / name) != digest:
            raise EnhanceError(f"published {name} differs from the packaged asset")
    if support.tree_hashes(native) != pristine:
        raise EnhanceError("the pristine native site changed")
    report.update(native_comparison=comparison, byte_idempotent=True,
                  fresh_enhancement_identical=True, pristine_unchanged=True,
                  enhanced_site=once)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--venv", type=Path, required=True,
                        help="environment created by scripts/install_gnatdoc_enhancer.py")
    parser.add_argument("--native", type=Path, default=ROOT / "_site")
    parser.add_argument("--output", type=Path, default=ROOT / "_site-enhanced")
    parser.add_argument("--report", type=Path, default=ROOT / "obj/docs/enhancement.json")
    args = parser.parse_args(argv)
    try:
        report = enhance(args.venv.resolve(), args.native.resolve(), args.output.resolve())
    except (EnhanceError, support.SupportError, OSError, KeyError,
            json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("PASS: enhanced copy verified; byte-idempotent; fresh run identical; native "
          f"identities preserved; added {report['native_comparison']['added_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
