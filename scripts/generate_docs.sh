#!/bin/sh
# Generate the native GNATdoc 26.0.0 API site from the four public Features
# specifications, then run the Features-owned qualification checks.
#
# Usage: sh scripts/generate_docs.sh [OUTPUT]
#   OUTPUT defaults to _site (rebuilt). Any other OUTPUT must not exist yet,
#   so that repeated generations are written to separate clean directories.
# Requires: an Alire workspace configured by `alr -n build --stop-after=pre-build`
# (resolves indexed opencv_core ~0.5.0 and generates crate configuration),
# GNAT 16.1.0 / GPRbuild 26.0.0 selected through Alire, and GNATDOC_PREFIX
# naming a gnatdoc_bin=26.0.0 installation. No library is compiled or linked.
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
output=${1:-_site}
case $output in
    /*) ;;
    *) output="$root/$output" ;;
esac
: "${GNATDOC_PREFIX:?Set GNATDOC_PREFIX to a gnatdoc_bin=26.0.0 installation}"
gnatdoc="$GNATDOC_PREFIX/bin/gnatdoc"
version=$("$gnatdoc" --version 2>&1 || true)
test "$version" = 'GNATdoc 26.0.0 (20260415)' || {
    echo "error: unqualified GNATdoc: $version" >&2; exit 1;
}
alr -n exec -- gnat --version | grep -qx 'GNAT 16.1.0' || {
    echo 'error: select gnat_native=16.1.0 through Alire' >&2; exit 1;
}
alr -n exec -- gprbuild --version | grep -q '^GPRBUILD 26\.0\.0 (2026-04-15)' || {
    echo 'error: select gprbuild=26.0.1 (GPRBUILD 26.0.0) through Alire' >&2; exit 1;
}
if [ "$output" = "$root/_site" ]; then
    rm -rf -- "$root/_site"
elif [ -e "$output" ]; then
    echo "error: $output exists; use a new directory for each generation" >&2; exit 1
fi
mkdir -p obj/docs
# Semantic analysis only (-gnatc): proves the specifications are legal Ada 2022
# with the crate's configured switches; no object code or library is produced.
alr -n exec -- gprbuild -q -p -P docs_api.gpr -c -u -gnatc
log=obj/docs/gnatdoc.log
alr -n exec -- "$gnatdoc" -P docs_api.gpr --backend html --generate public \
    --style leading --warnings -O "$output/api" > "$log" 2>&1 || {
    cat "$log" >&2; echo 'error: GNATdoc failed' >&2; exit 1;
}
if grep -Ei '(^|[[:space:]])(error:|fatal:|ignore file due to)' "$log"; then
    echo 'error: incomplete GNATdoc generation' >&2; exit 1
fi
python3 scripts/check_gnatdoc.py all --api "$output/api" --log "$log"
