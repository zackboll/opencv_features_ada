#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Sourced by the qualifier and deterministic regression fixtures.
check_features_pe_imports() {
    # Match whole import names, not the Features shim or unrelated DLLs.
    grep -Ei '^[[:space:]]*DLL Name:[[:space:]]+libopencv_features(2d)?-?[0-9]+\.dll[[:space:]]*$' "$1" &&
    grep -Ei '^[[:space:]]*DLL Name:[[:space:]]+libopencv_core_shim\.dll[[:space:]]*$' "$1"
}

collect_consumer_inventory() {
    inventory=$1
    shift
    # Portable sh has no mandatory pipefail. Retain raw evidence even on failure.
    find "$@" > "$inventory.raw" || return 1
    sort "$inventory.raw" > "$inventory"
}

hide_consumer_sources() {
    # Never rename the shell's current directory (MSYS find cannot recover it).
    cd "$1" || return 1
    mv "$1/candidate" "$1/unavailable-candidate" || return 1
    mv "$1/features_clean_consumer" "$1/unavailable-source-consumer"
}