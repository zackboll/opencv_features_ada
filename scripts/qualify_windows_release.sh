#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# New harness, independent original release checkout; never patch that checkout.
set -eu
case "$(uname -s)" in
    MINGW*|MSYS*) ;;
    *) echo 'error: Windows/MSYS2 release qualification only' >&2; exit 1 ;;
esac
[ "$#" -eq 1 ] || { echo 'usage: qualify_windows_release.sh OUTPUT' >&2; exit 1; }
harness=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output=$(cygpath -u "$1")
mkdir -p "$output"
output=$(CDPATH= cd -- "$output" && pwd)
rm -f "$output/qualification.json"
commit=e6d977f0bba02c526920834ef6e88905366ed1b9
tree=0265f6e39de174722cfe8ff59d7663dddbcf8cbd
temporary=$(cygpath -u "${RUNNER_TEMP:-${TMPDIR:-/tmp}}")
work=$(mktemp -d "$temporary/features-release-boundary.XXXXXXXX")
# Keep the checkout/diagnostics on failure for the runner's lifetime.
git clone --no-local --no-checkout "$harness" "$work/source"
git -C "$work/source" checkout --detach "$commit"
test "$(git -C "$work/source" rev-parse HEAD)" = "$commit"
test "$(git -C "$work/source" rev-parse 'HEAD^{tree}')" = "$tree"
test -z "$(git -C "$work/source" status --porcelain --untracked-files=all)"
cd "$work/source"
sh "$(cygpath -m "$harness/scripts/run_windows_native_boundary.sh")" \
    "$(cygpath -m "$work/source")" "$(cygpath -m "$output")" "$commit" "$tree"
git diff --exit-code HEAD --
test -z "$(git ls-files --others --exclude-standard)"
printf 'WINDOWS_RELEASE_SOURCE_QUALIFIED %s %s\n' "$commit" "$tree"