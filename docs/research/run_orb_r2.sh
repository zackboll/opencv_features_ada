#!/bin/sh
# Research only. Run in the actual selected platform runtime, not an emulator.
set -eu
[ "$#" -eq 1 ] || { echo 'usage: run_orb_r2.sh OUTPUT_DIR' >&2; exit 1; }
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$1"
output=$(CDPATH= cd -- "$1" && pwd)
package=${OPENCV_PACKAGE:-opencv4}
cxx=${CXX:-g++}
opt=${OPT:-2}
case "$opt" in 0|1|2|3) ;; *) exit 1 ;; esac
{
    uname -a
    "$cxx" --version
    pkg-config --modversion "$package"
    pkg-config --cflags --libs "$package"
    printf 'probe flags: C++17 -O%s; no fast-math; native flags in numerical.log\n' "$opt"
} > "$output/environment.log"
"$cxx" -std=c++17 "-O$opt" -Wall -Wextra -Wpedantic -Werror \
    "$root/docs/research/orb_r2_numerics.cpp" \
    $(pkg-config --cflags "$package" | sed 's/-I/-isystem /g') \
    $(pkg-config --libs "$package") -o "$output/numerics"
"$output/numerics" > "$output/numerical.log"
"${PYTHON:-python3}" "$root/docs/research/orb_r2_independent.py" "$output/numerical.log" \
    > "$output/independent.log"
# Preserve R1 sources while selecting exactly the same native metadata/Python.
mkdir -p "$output/r1"
"$cxx" -std=c++17 "-O$opt" -Wall -Wextra -Wpedantic -Werror \
    "$root/docs/research/orb_levels_probe.cpp" \
    $(pkg-config --cflags "$package" | sed 's/-I/-isystem /g') \
    $(pkg-config --libs "$package") -o "$output/r1/probe"
"$output/r1/probe" > "$output/r1/probe.log"
"${PYTHON:-python3}" "$root/docs/research/orb_levels_certificate.py" "$output/r1/probe.log" \
    > "$output/r1/certificate.log"
cat "$output/r1/probe.log" "$output/r1/certificate.log" > "$output/r1.log"
case "$(uname -s)" in
    Darwin) otool -L "$output/numerics" > "$output/linkage.log" ;;
    MINGW*|MSYS*) "$(dirname "$cxx")/objdump.exe" -p "$output/numerics.exe" > "$output/linkage.log" ;;
    Linux) ldd "$output/numerics" > "$output/linkage.log" ;;
    *) echo 'unqualified host' >&2; exit 1 ;;
esac
echo 'PASS research probes; platform qualification still requires native build/rounding-path review'