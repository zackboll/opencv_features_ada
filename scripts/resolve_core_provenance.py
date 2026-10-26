#!/usr/bin/env python3
"""Fail-closed Alire 2.1.1 shared-cache provenance for the Windows harness.

The lock selects a release; indexed JSON authenticates its declared origin.
The inherited Alire environment and recorded build hashes associate that release
with the build used by Features. The vault manifest is NOT a build manifest.
This verifies Alire's provenance records, not arbitrary cache tamper resistance.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

from validate_core_manifest import validate_core_manifest, validate_core_release

UPSTREAM = "git+https://github.com/zackboll/opencv_core_ada.git"


def load(path):
    with path.open("rb") as stream:
        return tomllib.load(stream)


def table(value):
    if not isinstance(value, dict):
        raise ValueError("invalid Alire provenance table")
    return value


def alire_json(source, *args):
    # Metadata queries only: never re-export an already established environment.
    result = subprocess.run(["alr", "-n", *args], cwd=source,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(f"Alire provenance command failed: {args[0]}: {result.stderr.strip()}")
    def unique_object(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("ambiguous duplicate Alire JSON field")
        return result
    return json.loads(result.stdout, object_pairs_hook=unique_object)


def resolve_core_provenance(source, core):
    """Resolve only the selected shared-cache dependency; never scan caches."""
    manifest = load(source / "alire.toml")
    pins = manifest.get("pins", [])
    if not isinstance(pins, list) or any(not isinstance(pin, dict) for pin in pins):
        raise ValueError("invalid workspace pin metadata")
    if any("opencv_core" in pin for pin in pins):
        raise ValueError("Core workspace/Git pins are forbidden")
    solution = table(load(source / "alire/alire.lock").get("solution", {}))
    if table(solution.get("context", {})).get("solved") is not True:
        raise ValueError("require solved Alire lock metadata")
    all_states = solution.get("state", [])
    if not isinstance(all_states, list) or any(not isinstance(s, dict) for s in all_states):
        raise ValueError("invalid Alire dependency states")
    states = [s for s in all_states if s.get("crate") == "opencv_core"]
    if len(states) != 1:
        raise ValueError("missing/ambiguous selected Core dependency")
    state = states[0]
    if (state.get("fulfilment") != "solved" or state.get("pinned") is not False
            or state.get("transitivity") != "direct" or state.get("versions") != "~0.5.0"
            or "pin" in state or "link" in state):
        raise ValueError("require unpinned indexed Core ~0.5.0 solution")
    release = state.get("release", {})
    version = validate_core_release(release)
    origin = table(release.get("origin", {}))
    if (set(origin) != {"url", "commit"} or origin.get("url") != UPSTREAM
            or not isinstance(origin.get("commit"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", origin["commit"])):
        raise ValueError("require indexed Core public Git origin and immutable commit")
    indexed = alire_json(source, "--format=JSON", "show", f"opencv_core={version}")
    if validate_core_release(indexed) != version or indexed.get("origin") != origin:
        raise ValueError("selected Core disagrees with indexed provenance")

    rows = alire_json(source, "--format=JSON", "version")
    if (not isinstance(rows, list) or any(not isinstance(row, dict) or
            not isinstance(row.get("key"), str) or not isinstance(row.get("value"), str)
            for row in rows)):
        raise ValueError("invalid Alire version metadata")
    info = {row["key"]: row["value"] for row in rows}
    if len(info) != len(rows) or info.get("alr version") != "2.1.1":
        raise ValueError("require unambiguous reviewed Alire 2.1.1 metadata")
    if (info.get("root status") != "VALID" or not info.get("root folder")
            or not Path(info["root folder"]).is_absolute() or
            Path(info.get("root folder", "")).resolve() != source.resolve()):
        raise ValueError("Alire provenance belongs to a different workspace")
    # The caller already runs inside the authoritative Alire execution context.
    # Re-exporting with exec hashes the exported PATH on MSYS2 and conflicts
    # with the inherited resource prefix. Validate it independently instead.
    keys = ("OPENCV_CORE_ALIRE_PREFIX", "OPENCV_FEATURES_ALIRE_PREFIX")
    inherited = {key: os.environ.get(key) for key in keys}
    if (not all(inherited[k] and Path(inherited[k]).is_absolute() for k in keys)
            or Path(inherited[keys[0]]).resolve() != core.resolve()
            or Path(inherited[keys[1]]).resolve() != source.resolve()):
        raise ValueError("Core build prefix/environment is unrelated to selected workspace")
    deployment = f"opencv_core_{version.split('+')[0]}_{origin['commit'][:8]}"
    for key in ("build folder", "vault folder"):
        if not info.get(key) or not Path(info[key]).is_absolute():
            raise ValueError("missing absolute Alire cache location")
    build_parent = (Path(info["build folder"]) / deployment).resolve()
    if core.parent.resolve() != build_parent or not re.fullmatch(r"[0-9a-f]{64}", core.name):
        raise ValueError("Core build prefix does not match selected Alire deployment")
    inputs = (core / "alire/build_hash_inputs").read_text(encoding="utf-8").splitlines()
    if not inputs or inputs != sorted(set(inputs)):
        raise ValueError("missing/inconsistent Core build hash inputs")
    digest = hashlib.sha256(b"".join(line.encode() + b"\0" for line in inputs)).hexdigest()
    dependencies = [line for line in (source / "alire/build_hash_inputs").read_text(
        encoding="utf-8").splitlines() if line.startswith("dependency:opencv_core=")]
    if digest != core.name or dependencies != [f"dependency:opencv_core={version}={digest}"]:
        raise ValueError("Core build hash is unrelated to Features dependency")
    checkout = (Path(info["vault folder"]) / deployment).resolve()
    actual = checkout / "alire.toml"
    if validate_core_manifest(actual) != version or load(actual).get("origin") != origin:
        raise ValueError("Core source manifest disagrees with selected provenance")
    # If present, contradictory build metadata must not be silently ignored.
    build_manifest = core / "alire.toml"
    if build_manifest.exists() and (validate_core_manifest(build_manifest) != version
                                   or load(build_manifest).get("origin") != origin):
        raise ValueError("Core build manifest disagrees with selected provenance")
    for name in ("opencv_core_module_bridge.hpp", "opencv_core_shim.h"):
        authoritative = (checkout / "cpp" / name).read_bytes()
        if authoritative != (core / "cpp" / name).read_bytes():
            raise ValueError("Core build bridge disagrees with verified source deployment")
        installed = core / "include" / name
        if installed.exists() and installed.read_bytes() != authoritative:
            raise ValueError("Core include bridge disagrees with verified source deployment")
    return {"version": version, "origin": origin, "build_prefix": str(core),
            "source_prefix": str(checkout), "build_hash": digest,
            "mechanism": "Alire 2.1.1 lock/index JSON/inherited-environment/build-hash/vault"}
