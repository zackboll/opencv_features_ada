#!/bin/sh
# Research only. One installed-ORB evidence run; no target matrix.
set -eu
[ "$#" -eq 1 ] || { echo 'usage: run_orb_r3e.sh OUTPUT_DIR' >&2; exit 1; }
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
exec "${PYTHON:-python3}" "$root/docs/research/orb_r3e_harness.py" "$1"
