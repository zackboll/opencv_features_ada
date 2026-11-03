#!/usr/bin/env python3
"""Fail closed unless old/new sites differ only by the reviewed enhancer transition.

Both sites must be enhanced from byte-identical native input. The transition
table below is reviewed source, never read from either site: v0.1.0 -> v0.1.5
changes exactly the API index search label, the packaged navigation script and
the presentation manifest's version and output digests. Every other file must
be byte-identical.
"""
import argparse
import json
from pathlib import Path

import gnatdoc_enhancer_support as support
import check_pages_site as pages

OLD_VERSION, NEW_VERSION = "0.1.0", "0.1.5"
NAVIGATION = "api/gnatdoc-navigation.js"
# v0.1.0 and v0.1.5 Git blobs of src/ada_gnatdoc_enhancer/assets/gnatdoc-navigation.js.
OLD_NAVIGATION = "b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd"
NEW_NAVIGATION = "e32e0a9fcbccffbe94268ff933905e5616a52d4d89969c52e7d539acdb102522"
# Upstream renamed the visible label of the navigation filter (no behavior change).
OLD_LABEL = '<label for="package-search">Search documentation</label>'
NEW_LABEL = '<label for="package-search">Filter navigation links</label>'
CHANGED = ["api/gnatdoc-navigation.js", "api/index.html", "api/presentation.json"]
REFERENCES = 248


def compare(old: Path, new: Path) -> dict:
    before, after = support.tree_hashes(old), support.tree_hashes(new)
    if set(before) != set(after) or set(after) != pages.expected_files():
        raise support.SupportError("old/new site inventory differs from the approved inventory")
    differences = sorted(name for name in before if before[name] != after[name])
    if differences != CHANGED:
        raise support.SupportError(f"unexpected output differences: {differences}")
    if (before[NAVIGATION], after[NAVIGATION]) != (OLD_NAVIGATION, NEW_NAVIGATION):
        raise support.SupportError("navigation script is not the reviewed v0.1.0 -> v0.1.5 blob")
    old_index = (old / "api/index.html").read_text()
    if old_index.count(OLD_LABEL) != 1 or \
            old_index.replace(OLD_LABEL, NEW_LABEL) != (new / "api/index.html").read_text():
        raise support.SupportError("api/index.html changed beyond the reviewed label")
    # Byte comparison: each substitution must occur exactly once in the old manifest.
    manifest = (old / "api/presentation.json").read_text()
    for value, replacement in ((f'"enhancer_version": "{OLD_VERSION}"',
                                f'"enhancer_version": "{NEW_VERSION}"'),
                               (f'"api/index.html": "{before["api/index.html"]}"',
                                f'"api/index.html": "{after["api/index.html"]}"'),
                               (f'"{NAVIGATION}": "{OLD_NAVIGATION}"', f'"{NAVIGATION}": "{NEW_NAVIGATION}"')):
        if manifest.count(value) != 1:
            raise support.SupportError(f"old manifest lacks a unique {value}")
        manifest = manifest.replace(value, replacement)
    if manifest != (new / "api/presentation.json").read_text():
        raise support.SupportError("manifest changed beyond the version and output digests")
    report = {"files": {name: {"old_sha256": before[name], "new_sha256": after[name],
                              "classification": "reviewed transition" if name in differences
                              else "byte-identical"} for name in before}, "census": {}}
    for label, site in (("old", old), ("release", new)):
        html = list(site.rglob("*.html"))
        refs = sum(len(support.collect(path).references) for path in html)
        checked = pages.check(site.resolve(), pages.expected_files(), pages.routes())
        # The old site's navigation script is no longer the authorized Pages blob.
        errors = [e for e in checked["errors"] if label == "release" or not e.startswith(NAVIGATION)]
        if len(html) != 13 or refs != REFERENCES or errors:
            raise support.SupportError(f"{label}: page/reference census or link errors: {errors}")
        report["census"][label] = {"html_pages": len(html), "files": len(before),
                                   "resolved_references": refs, "link_errors": errors}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.old, args.new)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {len(report['files']) - len(CHANGED)} byte-identical files; reviewed "
          f"{OLD_VERSION} -> {NEW_VERSION} changes only in {', '.join(CHANGED)}; "
          f"{REFERENCES} references in each site")


if __name__ == "__main__":
    main()
