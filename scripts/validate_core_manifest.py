#!/usr/bin/env python3
"""Validate the resolved Core manifest before consumer installation (Python 3.11+)."""
from pathlib import Path
import re
import sys
import tomllib


# Stable SemVer only: canonical numeric components, no prerelease. Build
# metadata does not affect compatibility and follows SemVer identifier syntax.
STABLE_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def validate_core_manifest(manifest: Path) -> str:
    """Return the parsed version for stable opencv_core >=0.5.0 and <0.6.0."""
    with manifest.open("rb") as stream:
        data = tomllib.load(stream)
    return validate_core_release(data)


def validate_core_release(data: dict) -> str:
    """Apply the same identity/version policy to structured Alire metadata."""
    if not isinstance(data, dict):
        raise ValueError("resolved Core metadata must be a table")
    if data.get("name") != "opencv_core":
        raise ValueError("resolved manifest must identify crate opencv_core")
    version = data.get("version")
    match = STABLE_VERSION.fullmatch(version) if isinstance(version, str) else None
    # Compare canonical components without converting arbitrarily large numbers.
    if match is None or match.group(1, 2) != ("0", "5"):
        raise ValueError("resolved Core must be a stable version >=0.5.0 and <0.6.0")
    return version


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_core_manifest.py MANIFEST", file=sys.stderr)
        return 1
    try:
        version = validate_core_manifest(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        print(f"error: invalid resolved Core manifest: {error}", file=sys.stderr)
        return 1
    print(f'Resolved opencv_core version = "{version}" (stable ~0.5.0)')
    return 0


if __name__ == "__main__":
    sys.exit(main())