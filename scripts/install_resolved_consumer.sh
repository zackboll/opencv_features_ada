#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Install resolved indexed Core and the Features candidate into one prefix.
# Invoked as: alr exec -- sh <this> <evidence-directory>
# A separate file avoids MSYS Git Bash reparsing escaped quotes inside sh -c.
set -eu
work=$1
printf 'Resolved Core source: %s\n' "$OPENCV_CORE_ALIRE_PREFIX"
case "$OPENCV_CORE_ALIRE_PREFIX" in
    "$work/candidate"*|"$work/unavailable-candidate"*|"$work/features_clean_consumer"*|"$work/unavailable-source-consumer"*)
        echo 'error: Core resolved through a Features workspace pin' >&2
        exit 1 ;;
esac
manifest=$OPENCV_CORE_ALIRE_PREFIX/alire.toml
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python=python3
case "$(uname -s)" in
    MINGW*|MSYS*) python=python ;;
esac
# Parse the entire manifest before evidence writes or either gprinstall call.
"$python" "$script_dir/validate_core_manifest.py" "$manifest"
if git -C "$OPENCV_CORE_ALIRE_PREFIX" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "$OPENCV_CORE_ALIRE_PREFIX" rev-parse HEAD
fi
printf '%s\n' "$OPENCV_CORE_ALIRE_PREFIX" > "$work/core-source.txt"
printf '%s\n' "$PATH" > "$work/toolchain-path.txt"
gprinstall -f -p -r --prefix="$work/prefix-a" -P "$OPENCV_CORE_ALIRE_PREFIX/opencv_core.gpr"
gprinstall -f -p -r --prefix="$work/prefix-a" -P "$work/candidate/opencv_features.gpr"
