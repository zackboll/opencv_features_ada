#!/usr/bin/env python3
"""Fail closed unless old/new sites differ only in the release version field."""
import argparse
import json
from pathlib import Path

import gnatdoc_enhancer_support as support
import check_pages_site as pages


def compare(old: Path, new: Path) -> dict:
    before, after = support.tree_hashes(old), support.tree_hashes(new)
    if set(before) != set(after) or set(after) != pages.expected_files():
        raise support.SupportError("old/new site inventory differs from the approved inventory")
    differences = [name for name in before if before[name] != after[name]]
    if differences != ["api/presentation.json"]:
        raise support.SupportError(f"unexpected output differences: {differences}")
    manifest = "api/presentation.json"
    old_text, new_text = (old / manifest).read_text(), (new / manifest).read_text()
    if old_text.replace('"enhancer_version": "0.1.0.dev0"',
                        '"enhancer_version": "0.1.0"', 1) != new_text:
        raise support.SupportError("manifest changed beyond the release version transition")
    report = {"files": {name: {"old_sha256": before[name], "new_sha256": after[name],
                              "classification": "release version only" if name in differences
                              else "byte-identical"} for name in before}, "census": {}}
    for label, site in (("old", old), ("release", new)):
        html = list(site.rglob("*.html"))
        refs = sum(len(support.collect(path).references) for path in html)
        checked = pages.check(site.resolve(), pages.expected_files(), pages.routes())
        if len(html) != 13 or refs != 248 or checked["errors"]:
            raise support.SupportError(f"{label}: page/reference census or link errors: {checked}")
        report["census"][label] = {"html_pages": len(html), "files": len(before),
                                   "resolved_references": refs, "link_errors": checked["errors"]}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.old, args.new)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("PASS: 17 byte-identical files; manifest release version only; 248 references in each site")


if __name__ == "__main__":
    main()