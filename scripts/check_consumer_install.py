#!/usr/bin/env python3
"""Audit actual project/link traces and installed metadata, not binary debug text."""
from pathlib import Path
import re
import sys


def audit(work: Path) -> None:
    forbidden = [str(work / "candidate"), str(work / "features_clean_consumer"),
                 (work / "core-source.txt").read_text().strip()]
    prefix = work / "relocated-longer-prefix-b"
    if (work / "original-source.txt").exists():
        forbidden.append((work / "original-source.txt").read_text().strip())
    findings = []
    for path in prefix.rglob("*"):
        if not path.is_file() or path.suffix not in {".gpr", ".cgpr", ".pc", ".json"}:
            continue
        for line in path.read_text().splitlines():
            if any(p.replace("\\", "/") in line.replace("\\", "/")
                   for p in forbidden + [str(work / "prefix-a")]):
                # GPRINSTALL retains this evaluated, unused variable but drops
                # the Compiler package. It cannot drive an installed build.
                if ("Common_Cxx_Switches :=" in line
                        and path.read_text().count("Common_Cxx_Switches") == 1
                        and "package Compiler" not in path.read_text()):
                    findings.append(f"non-load-bearing unused build variable: {path}: {line}")
                else:
                    raise ValueError(f"unreviewed source/original-prefix metadata: {path}: {line}")
    for mode, name in (("installed", "prefix-a"), ("relocated", "relocated-longer-prefix-b")):
        trace = (work / f"{mode}-resolution.log").read_text().replace("\\", "/")
        expected = str(work / name).replace("\\", "/")
        # Windows tool output uses drive-letter paths; suffix matching still
        # verifies the unique work root and prefix, independent of MSYS spelling.
        expected = expected[expected.index("features-consumer."):]
        for project in ("opencv_features", "opencv_core"):
            if not re.search(re.escape(expected) + r"/share/gpr/" + project + r"(?:\.gpr)?", trace):
                raise ValueError(f"missing resolved {project} project under {name}")
            if not re.search(re.escape(expected) + r"/lib/" + project + r"/", trace):
                raise ValueError(f"missing linked {project} library under {name}")
        for original in forbidden + ([str(work / "prefix-a")] if mode == "relocated" else []):
            if original in trace:
                raise ValueError(f"source/original prefix in {mode} resolution trace: {original}")
    (work / "path-audit.log").write_text("\n".join(findings) + "\n")
    print("\n".join(findings) or "No source-path metadata findings")
    print("Installed/relocated project and library resolution VERIFIED")


if __name__ == "__main__":
    try:
        audit(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        sys.exit(f"FAIL: {error}")