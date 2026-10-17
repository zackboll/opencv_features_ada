#!/usr/bin/env python3
"""Prove that a documentation change leaves production semantics untouched.

Compares two Git revisions (default: BASE against HEAD):

* Ada and GPR files (.ads, .adb, .gpr) must have identical non-comment token
  streams. The lexer is the documentation model's real Ada lexer, so string
  literals containing "--", character literals and attributes are preserved;
  this is not a regular-expression comment strip.
* Every other existing file must be byte-identical.
* Deletions are rejected. Additions are rejected unless they are in the
  explicit documentation allowlist below (reviewed in this file, never read
  from a manifest that a change could edit).

The comparison is of committed trees, so staged-only or untracked changes do
not influence the result. Token equality is necessary, not sufficient:
documentation PRs must still build and run the native test suite.
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gnatdoc_source as source  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ADA_SUFFIXES = (".ads", ".adb", ".gpr")
DOCUMENTATION = (
    "docs/*",
    "README.md",
    ".gitignore",
    "docs_api.gpr",
    ".github/workflows/documentation.yml",
    "scripts/check_doc_source_integrity.py",
    "scripts/check_gnatdoc.py",
    "scripts/enhance_docs.py",
    "scripts/gnatdoc_enhancer_support.py",
    "scripts/gnatdoc_native.py",
    "scripts/gnatdoc_source.py",
    "scripts/preflight_gnatdoc_enhancer.py",
    "scripts/generate_docs.sh",
    "scripts/install_gnatdoc_enhancer.py",
    "tests/documentation/*",
)


class IntegrityError(ValueError):
    pass


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout


def tree(root: Path, revision: str) -> dict[str, str]:
    """Path -> blob identity for every file in a committed revision."""
    output = _git(root, "ls-tree", "-r", "-z", "--full-tree", revision)
    result = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        if kind != "blob":
            raise IntegrityError(f"unsupported tree entry {path.decode()} ({kind})")
        result[path.decode()] = f"{mode} {blob}"
    return result


def documentation_path(path: str) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in DOCUMENTATION)


def tokens(text: str) -> list[tuple[str, str]]:
    return [(token.kind, token.text) for token in source.code(source.lex(text))]


def compare(root: Path, base: str, head: str) -> dict[str, list[str]]:
    old, new = tree(root, base), tree(root, head)
    result: dict[str, list[str]] = {"comment-only": [], "documentation": [],
                                    "added-documentation": []}
    errors = []
    for path in sorted(old.keys() - new.keys()):
        errors.append(f"deleted: {path}")
    for path in sorted(new.keys() - old.keys()):
        if documentation_path(path):
            result["added-documentation"].append(path)
        else:
            errors.append(f"added outside the documentation allowlist: {path}")
    for path in sorted(old.keys() & new.keys()):
        if old[path] == new[path]:
            continue
        if old[path].split()[0] != new[path].split()[0]:
            errors.append(f"file mode changed: {path}")
            continue
        if documentation_path(path):
            result["documentation"].append(path)
            continue
        if path.endswith(ADA_SUFFIXES):
            before = _git(root, "show", f"{base}:{path}").decode("utf-8")
            after = _git(root, "show", f"{head}:{path}").decode("utf-8")
            try:
                same = tokens(before) == tokens(after)
            except source.SourceError as error:
                raise IntegrityError(f"{path}: {error}") from error
            if same:
                result["comment-only"].append(path)
            else:
                errors.append(f"Ada/GPR tokens changed: {path}")
        else:
            errors.append(f"production file changed: {path}")
    if errors:
        raise IntegrityError("\n  ".join(["source integrity violations:"] + errors))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", help="base revision (for example the PR base SHA)")
    parser.add_argument("head", nargs="?", default="HEAD")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = compare(args.root, args.base, args.head)
    except (IntegrityError, subprocess.CalledProcessError, UnicodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for kind, paths in result.items():
        for path in paths:
            print(f"{kind}: {path}")
    print(f"PASS: {sum(map(len, result.values()))} changed paths; production tokens and "
          "bytes unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
