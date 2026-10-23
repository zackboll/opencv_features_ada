#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# External harness: SOURCE and OUTPUT may belong to a different checkout.
set -eu
case "$(uname -s)" in
    MINGW*|MSYS*) ;;
    *) echo 'error: Windows/MSYS2 native boundary runner only' >&2; exit 1 ;;
esac
[ "$#" -eq 2 ] || [ "$#" -eq 4 ] || {
    echo 'usage: run_windows_native_boundary.sh SOURCE OUTPUT [COMMIT TREE]' >&2
    exit 1
}
harness=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source=$(cygpath -m "$1")
output=$(cygpath -m "$2")
shift 2
mkdir -p "$output"
rm -f "$output/qualification.json"
log="$output/campaign.log"
python "$(cygpath -m "$harness/scripts/windows_native_boundary.py")" "$source" "$output" "$@" \
    > "$log" 2>&1 || { cat "$log"; exit 1; }
cat "$log"
# Do not accept exit zero from a bypassed or partial campaign.
grep -Fx 'WINDOWS_NATIVE_BOUNDARY_PRODUCTION_PASS' "$log"
grep -Fx 'WINDOWS_NATIVE_BOUNDARY_FAULT_PASS' "$log"