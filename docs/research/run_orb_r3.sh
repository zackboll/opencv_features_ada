#!/bin/sh
# Research only; subprocess evidence and finalization are owned by Python.
set -eu
[ "$#" -eq 1 ] || { echo 'usage: run_orb_r3.sh OUTPUT_DIR' >&2; exit 1; }
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
exec "${PYTHON:-python3}" "$root/docs/research/orb_r3_harness.py" "$1"