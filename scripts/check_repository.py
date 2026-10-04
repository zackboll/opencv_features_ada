#!/usr/bin/env python3
"""Static repository consistency checks; this is not an Ada/native build."""
from pathlib import Path
import re
import sys
import tomllib

from workflow_topology import check_workflows

ROOT = Path(__file__).resolve().parent.parent

def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def check_bridge_ownership(root: Path) -> None:
    # Alire fetches the authoritative bridge into ignored dependency caches.
    # Prune those directories, but reject copies anywhere in repository source.
    import os
    for directory, children, files in os.walk(root):
        children[:] = [name for name in children if name not in {".git", "alire"}]
        check("opencv_core_module_bridge.hpp" not in files,
              "do not vendor Core's bridge")

def main() -> None:
    manifests = [tomllib.loads((ROOT / p).read_text()) for p in
                 ("alire.toml", "tests/alire.toml", "examples/alire.toml")]
    production = manifests[0]
    dependencies = {k for group in production["depends-on"] for k in group}
    check({"opencv_core", "opencv", "pkg_config"} <= dependencies, "missing production dependency")
    check(not dependencies & {"aunit", "gnatprove", "gnatcov", "opencv_imgproc", "opencv_geometry"},
          "production dependency boundary changed")
    commits = [m["pins"][0]["opencv_core"]["commit"] for m in manifests]
    check(len(set(commits)) == 1 and re.fullmatch(r"[0-9a-f]{40}", commits[0]) is not None,
          "Core pins must be the same full commit in all three roots")
    header = (ROOT / "cpp/opencv_features_shim.h").read_text()
    ada = (ROOT / "src/internal/opencv-features-internal-c_api.ads").read_text()
    cpp = (ROOT / "cpp/opencv_features_shim.cpp").read_text()
    declared = set(re.findall(r"\b(opencv_features_\w+)\s*\(", header))
    imported = set(re.findall(r'External_Name\s*=>\s*"(opencv_features_\w+)"', ada))
    check(declared == imported, f"C/Ada import mismatch: {declared ^ imported}")
    check(all(re.search(r"\b" + n + r"\s*\(", cpp) for n in declared), "missing C++ export")
    check_bridge_ownership(ROOT)
    check_workflows(ROOT / ".github/workflows")
    check(not list((ROOT / "src").rglob("opencv.ads")), "do not redeclare Core's root package")
    tests = (ROOT / "tests/src/features_tests.adb").read_text()
    registrations = re.findall(r"Result\.Add_Test\s*\(Caller\.Create", tests)
    check(len(registrations) == 44, "update the documented AUnit inventory when changing tests")
    for path in list((ROOT / "src").rglob("*.ads")) + list((ROOT / "src").rglob("*.adb")):
        check("pragma Import" not in path.read_text() or "/internal/" in path.as_posix(),
              f"C import leaked into public Ada: {path}")
    print(f"PASS: manifests, shared Core pin, {len(declared)} ABI declarations/imports, ownership layout, 44 AUnit registrations, CI topology")

if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
