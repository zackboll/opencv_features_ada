#!/usr/bin/env python3
"""Windows native qualification, not a production build or a sanitizer substitute."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tomllib

from validate_core_manifest import validate_core_manifest


VARIANTS = ("production", "fault-injection")
FINAL = "PASS: actual Features shim / Core bridge / ORB boundary on "
FAULT = "PASS: radius fault stages 15/16/17/18 x five exception categories, empty cleanup"
MARKERS = {"production": "WINDOWS_NATIVE_BOUNDARY_PRODUCTION_PASS",
           "fault-injection": "WINDOWS_NATIVE_BOUNDARY_FAULT_PASS"}


def run(args, log=None, cwd=None, env=None):
    # Mixed (forward-slash) paths work with native MinGW tools AND the MSYS shell.
    args = [arg.as_posix() if isinstance(arg, Path) else str(arg) for arg in args]
    print("+ " + subprocess.list2cmdline(args), flush=True)
    result = subprocess.run(args, cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if log is not None:
        log.write_text(result.stdout, encoding="utf-8")
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise ValueError(f"command failed ({result.returncode}): {args[0]}")
    return result.stdout


def source_identity(source, expected=None):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()
    identity = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}
    if expected is not None and (identity["commit"], identity["tree"]) != tuple(expected):
        raise ValueError("release source commit/tree identity mismatch")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("qualification source must have no tracked edits or unignored files")
    return identity


def configuration(source, core):
    text = (source / "config/opencv_features_install.gpr").read_text(encoding="utf-8")
    def field(name):
        matches = re.findall(r'^\s*' + name + r'(?:\s*:\s*\w+)?\s*:= "([^"\n]*)";\s*$', text, re.M)
        if len(matches) != 1 or not matches[0]:
            raise ValueError(f"missing/ambiguous generated setting: {name}")
        return matches[0]
    if field("Shim_Build") != "External_Relocatable" or field("Cxx_Toolchain") != "GNU":
        raise ValueError("require configured Windows external GNU toolchain")
    driver = Path(field("Cxx_Driver"))
    if (driver.name not in ("g++", "g++.exe") or driver.parent.name != "bin"
            or driver.parent.parent.name != "mingw64" or "gnat_native" in str(driver).lower()
            or not driver.is_absolute()):
        raise ValueError("require configured external MSYS2 MinGW64 g++")
    include = field("Include_Switch")
    bridge = field("Core_Bridge_Include_Switch")
    if not include.startswith("-I") or not bridge.startswith("-I"):
        raise ValueError("invalid configured include switch")
    bridge_dir = Path(bridge[2:]).resolve()
    if bridge_dir not in ((core / "cpp").resolve(), (core / "include").resolve()):
        raise ValueError("Core bridge does not belong to resolved Core")
    backend = field("Native_Backend")
    version = field("Native_Version")
    if not ((re.fullmatch(r"4\.(?:[1-9]|[1-9][0-9]+)\.[0-9]+", version) and backend == "features2d")
            or (re.fullmatch(r"5\.0\.[0-9]+", version) and backend == "features")):
        raise ValueError("unsupported configured native version/backend")
    libraries = [Path(field(name)) for name in
                 ("OpenCV_Features_Link_Option", "OpenCV_Core_Link_Option", "Core_Shim_Link_Option")]
    expected = [driver.parent.parent / "lib" / f"libopencv_{backend}.dll.a",
                driver.parent.parent / "lib/libopencv_core.dll.a",
                core / "lib/libopencv_core_shim.dll.a"]
    if [p.resolve() for p in libraries] != [p.resolve() for p in expected]:
        raise ValueError("native/Core import libraries must match configured MinGW64 and resolved Core")
    nm = driver.parent / "nm.exe"
    for path in [driver, nm, Path(include[2:]) / f"opencv2/{backend}.hpp",
                 bridge_dir / "opencv_core_module_bridge.hpp", bridge_dir / "opencv_core_shim.h",
                 core / "lib/libopencv_core_shim.dll", *libraries]:
        if not path.is_file():
            raise ValueError(f"missing Windows boundary input: {path}")
    return driver, nm, include, bridge, libraries, version


def validate_output(variant, text, version):
    for marker in ("PASS: matcher Hamming", "PASS: KNN2 Hamming/Hamming2",
                   "PASS: radius raw negatives", FINAL + version):
        if marker not in text:
            raise ValueError(f"{variant}: missing native execution marker: {marker}")
    if variant == "fault-injection" and FAULT not in text:
        raise ValueError("fault-injection: injected exception paths did not complete")
    if variant == "production" and FAULT in text:
        raise ValueError("production unexpectedly executed fault controls")


def require_complete(results):
    if set(results) != set(MARKERS) or any(results[v] != MARKERS[v] for v in MARKERS):
        raise ValueError("both successful Windows native-boundary variants are mandatory")


def qualify(source, output, expected=None):
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "qualification.json"
    report_path.unlink(missing_ok=True)
    identity = source_identity(source, expected)
    core = Path(os.environ["OPENCV_CORE_ALIRE_PREFIX"]).resolve()
    core_version = validate_core_manifest(core / "alire.toml")
    with (core / "alire.toml").open("rb") as stream:
        origin = tomllib.load(stream).get("origin", {})
    if (origin.get("url") != "git+https://github.com/zackboll/opencv_core_ada.git"
            or not re.fullmatch(r"[0-9a-f]{40}", origin.get("commit", ""))):
        raise ValueError("require indexed Core public Git origin and immutable commit")
    with (source / "alire.toml").open("rb") as stream:
        manifest = tomllib.load(stream)
    if any("opencv_core" in pin for pin in manifest.get("pins", [])):
        raise ValueError("Core workspace/Git pins are forbidden")
    driver, nm, include, bridge, libraries, version = configuration(source, core)
    env = os.environ.copy()
    for name in ("CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "LIBRARY_PATH",
                 "GCC_EXEC_PREFIX", "COMPILER_PATH"):
        env.pop(name, None)
    target = run([driver, "-dumpmachine"], output / "compiler-target.log", env=env).strip()
    if target != "x86_64-w64-mingw32":
        raise ValueError("compiler is not the native x86_64 MinGW64 target")
    compiler = run([driver, "--version"], output / "compiler-version.log", env=env)
    harness = Path(__file__).resolve().parents[1]
    harness_identity = source_identity(harness) if harness != source else identity
    report = {"source": identity, "harness": harness_identity,
              "core": {"version": core_version, "origin": origin}, "compiler": str(driver),
              "compiler_version": compiler, "compiler_target": target, "opencv": version,
              "import_libraries": [str(p) for p in libraries], "results": {}}
    print(json.dumps(report, indent=2), flush=True)
    for variant in VARIANTS:
        directory = output / variant
        directory.mkdir(exist_ok=True)
        binary = directory / "native_boundary.exe"
        objects = [directory / "features.o", directory / "boundary.o"]
        for path in [binary, *objects]:
            path.unlink(missing_ok=True)
        flags = ["-std=c++17", "-g", "-O1", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                 "-DOPENCV_FEATURES_BUILDING", "-I" + str(source / "cpp"), include, bridge]
        # Standalone EXE owns the Features implementation: no dllimport of itself.
        # Core remains a real imported DLL. Neither variant links the Features DLL.
        if variant == "fault-injection":
            flags.append("-DOPENCV_FEATURES_TEST_HOOKS")
        for unit, obj in zip((source / "cpp/opencv_features_shim.cpp",
                              source / "tests/cpp/native_boundary.cpp"), objects):
            run([driver, *flags, "-c", unit, "-o", obj], directory / (obj.stem + "-compile.log"), env=env)
        run([driver, *objects, *libraries, "-o", binary], directory / "link.log", env=env)
        symbols = run([nm, "--defined-only", binary], directory / "symbols.log", env=env)
        hooks = bool(re.search(r"\bopencv_features_test_fail\b", symbols))
        if hooks != (variant == "fault-injection"):
            raise ValueError(f"{variant}: unexpected fault-control symbol presence")
        text = run(["sh", source / "scripts/run_native.sh", binary], directory / "execution.log",
                   cwd=source, env=env)
        validate_output(variant, text, version)
        report["results"][variant] = MARKERS[variant]
        print(MARKERS[variant], flush=True)
    require_complete(report["results"])
    if source_identity(source, expected) != identity:
        raise ValueError("tested source identity changed during qualification")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main():
    if sys.platform != "win32":
        raise ValueError("real Windows Python required; fixtures are not native qualification")
    if len(sys.argv) not in (3, 5):
        raise ValueError("usage: windows_native_boundary.py SOURCE OUTPUT [COMMIT TREE]")
    qualify(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(),
            sys.argv[3:] if len(sys.argv) == 5 else None)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"WINDOWS_NATIVE_BOUNDARY_FAILED: {error}", file=sys.stderr)
        if len(sys.argv) in (3, 5):
            output = Path(sys.argv[2])
            output.mkdir(parents=True, exist_ok=True)
            (output / "qualification-failure.log").write_text(str(error) + "\n", encoding="utf-8")
        sys.exit(1)