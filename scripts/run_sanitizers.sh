#!/bin/sh
# Linux only; invoke inside the root Alire environment after alr build.
# Optional "native" runs the same boundary suite without sanitizer instrumentation.
set -eu
[ "$(uname -s)" = Linux ] || { echo 'error: Linux sanitizer driver only' >&2; exit 1; }
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
core=${OPENCV_CORE_ALIRE_PREFIX:?run using alr exec after building Core}
package=
for candidate in opencv5 opencv4 opencv; do
    if pkg-config --exists "$candidate"; then package=$candidate; break; fi
done
[ -n "$package" ] || { echo 'error: missing OpenCV metadata' >&2; exit 1; }
mkdir -p obj/sanitizers
flags='-g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer'
suffix=
case "${1:-sanitizers}" in
    sanitizers) ;;
    native) flags='-g -O1'; suffix=-native ;;
    *) echo 'error: expected native or sanitizers' >&2; exit 1 ;;
esac
core_shim="$core/lib/libopencv_core_shim.a"
[ -f "$core_shim" ] || { echo 'error: build the resolved static-PIC Core shim first' >&2; exit 1; }
for variant in production fault-injection; do
    define=
    [ "$variant" != fault-injection ] || define=-DOPENCV_FEATURES_TEST_HOOKS
    # pkg-config emits compiler/linker word lists, intentionally shell split.
    # Instrument the actual source, not a copied substitute or arithmetic helper.
    ${CXX:-g++} -std=c++17 -Wall -Wextra -Wpedantic -Werror \
        $flags \
        $define -Icpp "-I$core/cpp" $(pkg-config --cflags "$package") \
        cpp/opencv_features_shim.cpp tests/cpp/native_boundary.cpp \
        "$core_shim" $(pkg-config --libs "$package") \
        -o "obj/sanitizers/$variant$suffix"
    if [ "$variant" = production ]; then
        if nm "obj/sanitizers/$variant$suffix" | grep -q opencv_features_test_fail; then
            echo 'error: fault-injection API leaked into production build' >&2; exit 1
        fi
    fi
    ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 "obj/sanitizers/$variant$suffix"
done