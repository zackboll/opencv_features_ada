#!/bin/sh
# Focused hosted research; no Ada build or production qualification.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$1"
output=$(CDPATH= cd -- "$1" && pwd)
case "$(uname -s)" in
    Darwin) cxx=$(xcrun --find clang++); suffix= ;;
    MINGW*|MSYS*) suffix=.exe ;;
    Linux) cxx=${CXX:-g++}; suffix= ;;
    *) exit 1 ;;
esac
python=${PYTHON:-python3}
pkg_config=pkg-config
case "$(uname -s)" in
    MINGW*|MSYS*)
        if command -v x86_64-w64-mingw32-pkg-config >/dev/null; then
            pkg_config=x86_64-w64-mingw32-pkg-config
        fi ;;
esac
package=
for candidate in opencv5 opencv4 opencv; do
    if "$pkg_config" --exists "$candidate"; then package=$candidate; break; fi
done
test -n "$package"
case "$(uname -s)" in
    MINGW*|MSYS*)
        prefix=$(dirname "$("$pkg_config" --variable=libdir "$package")")
        cxx="$prefix/bin/g++.exe"
        case "$cxx" in *mingw64*/bin/g++*) ;; *) echo 'Expected managed MinGW64' >&2; exit 1;; esac
        test -f "$cxx"
        PATH="$prefix/bin:$PATH"; export PATH ;;
esac
{
    uname -a
    "$cxx" --version
    "$cxx" -dumpmachine
    "$pkg_config" --modversion "$package"
    "$pkg_config" --cflags --libs "$package"
    printf 'SHA=%s run=%s attempt=%s runner=%s arch=%s image=%s/%s\n' \
        "${GITHUB_SHA:-local}" "${GITHUB_RUN_ID:-local}" "${GITHUB_RUN_ATTEMPT:-local}" \
        "${RUNNER_OS:-local}" "${RUNNER_ARCH:-local}" "${ImageOS:-unknown}" "${ImageVersion:-unknown}"
    if command -v sw_vers >/dev/null; then sw_vers; fi
    if command -v pacman >/dev/null; then
        pacman -Q mingw-w64-x86_64-gcc mingw-w64-x86_64-opencv mingw-w64-x86_64-crt
    fi
} > "$output/provenance.log" 2>&1
include=$("$pkg_config" --variable=includedir "$package")
for header in "$include/opencv2/core/fast_math.hpp" "$include/opencv4/opencv2/core/fast_math.hpp"; do
    if [ -f "$header" ]; then cp "$header" "$output/selected-fast-math.txt"; break; fi
done
status=0
for opt in 0 2 3; do
    dir="$output/O$opt"
    mkdir -p "$dir"
    flags=$("$pkg_config" --cflags "$package" | sed 's/-I/-isystem /g')
    libs=$("$pkg_config" --libs "$package")
    printf '%s -std=c++17 -O%s -Wall -Wextra -Wpedantic -Werror %s %s\n' \
        "$cxx" "$opt" "$flags" "$libs" > "$dir/compile.log"
    # All failed steps are retained. Do not mask a failure as probe success.
    for source in orb_r2_numerics orb_r3_trace orb_levels_probe; do
        if "$cxx" -std=c++17 "-O$opt" -Wall -Wextra -Wpedantic -Werror \
            "$root/docs/research/$source.cpp" $flags $libs -o "$dir/$source$suffix" \
            >> "$dir/compile.log" 2>&1; then
            if "$dir/$source$suffix" > "$dir/$source.log" 2>&1; then
                echo "$source PASS" >> "$dir/status.log"
            else
                echo "$source EXECUTION_FAILED" >> "$dir/status.log"; status=1
            fi
        else
            echo "$source BUILD_FAILED" >> "$dir/status.log"; status=1
        fi
    done
    if ! "$python" "$root/docs/research/orb_r2_independent.py" "$dir/orb_r2_numerics.log" \
        > "$dir/independent.log" 2>&1; then status=1; fi
    if ! "$python" "$root/docs/research/orb_levels_certificate.py" "$dir/orb_levels_probe.log" \
        > "$dir/r1-certificate.log" 2>&1; then status=1; fi
    "$cxx" -std=c++17 "-O$opt" $flags -dM -E "$root/docs/research/orb_r2_numerics.cpp" \
        | grep -E 'FLT_|DBL_|SSE|ARM|FAST_MATH|FINITE_MATH|LIBCPP|GLIBCXX|FP_FAST' > "$dir/macros.log"
    case "$(uname -s)" in
        Darwin)
            otool -L "$dir/orb_r3_trace" > "$dir/linkage.log" 2>&1 || status=1
            otool -tvV "$dir/orb_r3_trace" > "$dir/disassembly.log" 2>&1 || status=1 ;;
        MINGW*|MSYS*)
            "$(dirname "$cxx")/objdump.exe" -p "$dir/orb_r3_trace.exe" > "$dir/linkage.log" 2>&1 || status=1
            "$(dirname "$cxx")/objdump.exe" -d "$dir/orb_r3_trace.exe" > "$dir/disassembly.log" 2>&1 || status=1 ;;
        Linux) ldd "$dir/orb_r3_trace" > "$dir/linkage.log" 2>&1 || status=1 ;;
    esac
done
"$python" "$root/docs/research/orb_r3_manifest.py" "$output" "$status"
exit "$status"