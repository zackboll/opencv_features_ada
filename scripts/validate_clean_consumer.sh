#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Three distinct proofs, not public-index resolution. Keep evidence on failure.
# Run directly (not inside alr exec): sh scripts/validate_clean_consumer.sh [source]
set -eu
source_root=$(CDPATH= cd -- "${1:-$(dirname -- "$0")/..}" && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/features-consumer.XXXXXXXX")
echo "Consumer evidence: $work"
unset GPR_PROJECT_PATH ADA_PROJECT_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset LIBRARY_PATH GCC_EXEC_PREFIX COMPILER_PATH LD_LIBRARY_PATH DYLD_LIBRARY_PATH LD_RUN_PATH
export FEATURES_CONSUMER_SOURCE="$source_root" FEATURES_CONSUMER_WORK="$work"
python=python3
case "$(uname -s)" in
    MINGW*|MSYS*)
        python=python
        export FEATURES_CONSUMER_SOURCE="$(cygpath -m "$source_root")"
        export FEATURES_CONSUMER_WORK="$(cygpath -m "$work")" ;;
esac
printf '%s\n' "$FEATURES_CONSUMER_SOURCE" > "$work/original-source.txt"
# Copy only version-controlled/nonignored candidate files: no config, objects,
# dependency caches, tests or examples. This also includes uncommitted changes.
"$python" - <<'PY'
import os, pathlib, shutil, subprocess
root = pathlib.Path(os.environ['FEATURES_CONSUMER_SOURCE'])
work = pathlib.Path(os.environ['FEATURES_CONSUMER_WORK'])
files = subprocess.check_output(
    ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
for name in set(files.decode().split('\0')) - {''}:
    if pathlib.PurePosixPath(name).parts[0] in {'tests', 'examples'}:
        continue
    src, dst = root / name, work / 'candidate' / name
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
PY
cd "$work"
alr -n init --bin features_clean_consumer
cd features_clean_consumer
cp "$work/candidate/scripts/features_clean_consumer.adb" src/
alr -n with opencv_features --use="$work/candidate"
alr -n build > "$work/source-build.log" 2>&1 || {
    cat "$work/source-build.log"; exit 1;
}
alr -n exec -- sh "$work/candidate/scripts/run_native.sh" bin/features_clean_consumer \
    > "$work/source-run.log" 2>&1
cat "$work/source-run.log"
grep -Fx 'opencv_features clean consumer ok' "$work/source-run.log"
echo 'SOURCE-PINNED consumer PASS (not an Alire index test)'
alr -n printenv > "$work/resolved-environment.log"
alr -n exec -- sh -c '
    set -eu
    printf "Resolved Core source: %s\n" "$OPENCV_CORE_ALIRE_PREFIX"
    git -C "$OPENCV_CORE_ALIRE_PREFIX" rev-parse HEAD
    test "$(git -C "$OPENCV_CORE_ALIRE_PREFIX" rev-parse HEAD)" = 7956981a7881ce9121115f8cb65909aeb9edc439
    printf "%s\n" "$OPENCV_CORE_ALIRE_PREFIX" > "$1/core-source.txt"
    printf "%s\n" "$PATH" > "$1/toolchain-path.txt"
    gprinstall -f -p -r --prefix="$1/prefix-a" -P "$OPENCV_CORE_ALIRE_PREFIX/opencv_core.gpr"
    gprinstall -f -p -r --prefix="$1/prefix-a" -P "$1/candidate/opencv_features.gpr"
' sh "$work" > "$work/install.log" 2>&1 || { cat "$work/install.log"; exit 1; }
cat "$work/install.log"
cp "$work/candidate/config/opencv_features_install.gpr" "$work/build-time-install.gpr"
driver=$(sed -n 's/^[ ]*Cxx_Driver := "\(.*\)";/\1/p' "$work/build-time-install.gpr")
case "$(uname -s)" in
    MINGW*|MSYS*) native_bin=$(cygpath -u "$(dirname "$driver")") ;;
    *) native_bin= ;;
esac
cp "$work/candidate/scripts/features_clean_consumer.adb" "$work/fixture.adb"
# Preserve evidence, but make the precise build/source locations inaccessible.
mv "$work/candidate" "$work/unavailable-candidate"
mv "$work/features_clean_consumer" "$work/unavailable-source-consumer"
tr ':' '\n' < "$work/toolchain-path.txt" | while IFS= read -r directory; do
    case "$directory" in
        "$work"/*|"$source_root"/*) ;;
        *) printf '%s\n' "$directory" ;;
    esac
done > "$work/installed-toolchain-path.txt"
PATH=$(paste -sd ':' "$work/installed-toolchain-path.txt"); export PATH
unset OPENCV_CORE_ALIRE_PREFIX OPENCV_FEATURES_ALIRE_PREFIX ALIRE
prefix_a="$work/prefix-a"
test -f "$prefix_a/include/opencv_core_module_bridge.hpp"
find "$prefix_a" -type f | sort > "$work/installed-inventory.txt"
find "$prefix_a" -type f \( -name '*.gpr' -o -name '*opencv*ada.a' -o -name '*shim*.a' -o -name '*.dll' -o -name '*.dylib' -o -name '*.so' -o -name '*bridge.hpp' \) | sort
for project in opencv_features opencv_core opencv_features_shim opencv_core_shim; do
    test -f "$prefix_a/share/gpr/$project.gpr"
done
for spec in opencv-features.ads opencv-features-orb.ads opencv-features-matching.ads opencv-features-correspondences.ads; do
    test -f "$prefix_a/include/opencv_features/$spec"
done
if find "$prefix_a" -iname '*radius_fixtures*' -o -iname '*features_tests*' | grep .; then
    echo 'error: test-only sources installed' >&2; exit 1
fi
for mode in installed relocated; do
    if [ "$mode" = installed ]; then
        prefix="$prefix_a"
    else
        prefix="$work/relocated-longer-prefix-b"
        mv "$prefix_a" "$prefix"
        test ! -e "$prefix_a" && test ! -L "$prefix_a"
        echo 'Original prefix removed VERIFIED'
    fi
    consumer="$work/$mode-consumer"
    mkdir "$consumer"
    cp "$work/fixture.adb" "$consumer/features_clean_consumer.adb"
    cat > "$consumer/consumer.gpr" <<'GPR'
with "opencv_features";
project Consumer is
   for Source_Dirs use (".");
   for Object_Dir use "obj";
   for Exec_Dir use "bin";
   for Main use ("features_clean_consumer.adb");
   package Compiler is
      for Default_Switches ("Ada") use ("-gnat2022", "-gnatwa", "-gnatwe");
   end Compiler;
end Consumer;
GPR
    (
        unset GPR_PROJECT_PATH ADA_PROJECT_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
        unset LIBRARY_PATH GCC_EXEC_PREFIX COMPILER_PATH LD_LIBRARY_PATH DYLD_LIBRARY_PATH LD_RUN_PATH
        case "$(uname -s)" in
            MINGW*|MSYS*) GPR_PROJECT_PATH=$(cygpath -m "$prefix/share/gpr") ;;
            *) GPR_PROJECT_PATH="$prefix/share/gpr" ;;
        esac
        export GPR_PROJECT_PATH
        echo "Project lookup: $GPR_PROJECT_PATH"
        cd "$consumer"
        gprbuild -p -v -vP2 -P consumer.gpr > "$work/$mode-build.log" 2>&1 || {
            cat "$work/$mode-build.log"; exit 1;
        }
        # Project parser plus final link line prove the lookup, not just our
        # intended environment. Full traces are retained separately.
        grep -E 'opencv_(features|core)(\.gpr|/|_ada|_shim)' "$work/$mode-build.log" \
            > "$work/$mode-resolution.log"
        grep -E '\.gpr|features_clean_consumer.o|/lib/opencv_' "$work/$mode-resolution.log" | tail -12
        runtime_dirs=$(find "$prefix/lib" "$prefix/bin" -type d 2>/dev/null | paste -sd ':' -)
        binary=bin/features_clean_consumer
        case "$(uname -s)" in
            Linux)
                export LD_LIBRARY_PATH="$runtime_dirs"
                echo "Runtime LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
                ldd "$binary" > "$work/$mode-linkage.log"
                readelf -d "$binary" >> "$work/$mode-linkage.log" ;;
            Darwin)
                export DYLD_LIBRARY_PATH="$runtime_dirs"
                echo "Runtime DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH"
                otool -L "$binary" > "$work/$mode-linkage.log"
                find "$prefix" -name '*.dylib' -exec otool -L {} \; >> "$work/$mode-linkage.log"
                grep 'libc++' "$work/$mode-linkage.log"
                if grep 'libstdc++' "$work/$mode-linkage.log"; then exit 1; fi ;;
            MINGW*|MSYS*)
                binary="$binary.exe"
                "$native_bin/objdump.exe" -p "$binary" > "$work/$mode-linkage.log"
                export PATH="$runtime_dirs:$native_bin:$PATH"
                echo "Runtime installed dirs=$runtime_dirs; native MSYS2=$native_bin" ;;
            *) echo 'error: unsupported consumer platform' >&2; exit 1 ;;
        esac
        "$binary" > "$work/$mode-run.log" 2>&1 || { cat "$work/$mode-run.log"; exit 1; }
        cat "$work/$mode-run.log"
        grep -Fx 'opencv_features clean consumer ok' "$work/$mode-run.log"
    )
    echo "$mode consumer PASS"
done
# Report textual provenance separately from runtime/project/library lookups.
"$python" "$source_root/scripts/check_consumer_install.py" "$FEATURES_CONSUMER_WORK"
echo "Source lookup sanitized VERIFIED; three consumer modes PASS; evidence: $work"