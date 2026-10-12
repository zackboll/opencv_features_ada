#!/bin/sh
# Research only; caller selects native metadata/runtime environment.
set -eu
[ "$#" -eq 1 ] || { echo 'usage: run_orb_levels_probe.sh OUTPUT_DIR' >&2; exit 1; }
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$1"
output=$(CDPATH= cd -- "$1" && pwd)
package=
for candidate in opencv5 opencv4 opencv; do
    if pkg-config --exists "$candidate"; then package=$candidate; break; fi
done
[ -n "$package" ] || { echo 'missing OpenCV metadata' >&2; exit 1; }
case "${OPT:-2}" in 0|1|2|3) ;; *) echo 'OPT must be 0..3' >&2; exit 1 ;; esac
# Upstream headers are system includes; research-source warnings stay errors.
${CXX:-g++} -std=c++17 "-O${OPT:-2}" -Wall -Wextra -Wpedantic -Werror \
    "$root/docs/research/orb_levels_probe.cpp" \
    $(pkg-config --cflags "$package" | sed 's/-I/-isystem /g') \
    $(pkg-config --libs "$package") -o "$output/probe"
"$output/probe" > "$output/probe.log"
python3 "$root/docs/research/orb_levels_certificate.py" "$output/probe.log" \
    > "$output/certificate.log"
cat "$output/probe.log" "$output/certificate.log"
