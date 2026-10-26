#!/usr/bin/env python3
"""Prepare and enter one Alire environment, without an intervening MSYS shell.

Build and exec must see the same native parent PATH. Neither command is nested
inside the other's environment. The resolver still rejects any mismatch with
the generated configuration; this launcher does not choose a cache build.
"""
from pathlib import Path
import os
import subprocess
import sys


def prepare(source, output, expected=()):
    output.mkdir(parents=True, exist_ok=True)
    for name in ("qualification.json", "qualification-failure.log", "compiler-target.log",
                 "compiler-version.log", "native-campaign.log", "alire-build.log"):
        (output / name).unlink(missing_ok=True)
    for variant in ("production", "fault-injection"):
        for name in ("features.o", "boundary.o", "native_boundary.exe", "features-compile.log",
                     "boundary-compile.log", "link.log", "symbols.log", "execution.log"):
            (output / variant / name).unlink(missing_ok=True)
    if any(os.environ.get(key) for key in
           ("OPENCV_CORE_ALIRE_PREFIX", "OPENCV_FEATURES_ALIRE_PREFIX")):
        raise ValueError("preparation requires an outer environment, not nested Alire execution")
    # Both are native subprocesses with the identical, unmodified parent env.
    # Alire's own Windows initialization occurs once in each sibling process.
    commands = (
        (["alr", "-n", "build"], output / "alire-build.log"),
        (["alr", "-n", "exec", "--", sys.executable,
          str(Path(__file__).with_name("windows_native_boundary.py").resolve()),
          str(source), str(output), *expected], output / "native-campaign.log"),
    )
    for args, log in commands:
        print("+ " + subprocess.list2cmdline(args), flush=True)
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(args, cwd=source, stdout=stream, stderr=subprocess.STDOUT)
        print(log.read_text(encoding="utf-8"), end="", flush=True)
        if result.returncode:
            raise ValueError(f"Windows preparation command failed ({result.returncode}): {args[2]}")


if __name__ == "__main__":
    try:
        if sys.platform != "win32":
            raise ValueError("real Windows Python required for Alire preparation")
        if len(sys.argv) not in (3, 5):
            raise ValueError("usage: prepare_windows_boundary.py SOURCE OUTPUT [COMMIT TREE]")
        prepare(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3:])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"WINDOWS_NATIVE_BOUNDARY_FAILED: {error}", file=sys.stderr)
        sys.exit(1)
