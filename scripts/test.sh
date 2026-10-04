#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
alr -n build
alr -n -C tests build
# Resolve dependency runtime paths in the test crate's Alire environment.
alr -n -C tests exec -- sh ../scripts/run_native.sh bin/run_tests
