# Task 011-R3A — hosted research harness repair

Disposition: **PLATFORM_EVIDENCE_PENDING**. This is research infrastructure,
not configurable ORB, production qualification or a relaxed numerical gate.

## Reconciliation and reproduced evidence

Starting branch `research/011-r3-hosted-numerics`, clean local HEAD
`45d9ff614033b8c6603ec13f2be75cd9352f0a5e`. Remote fetched; its campaign head
`b7eefa3b430d38fdf56e2c2bb2a154c5d15b7f95` is an ancestor. The documentation
commit is preserved without amend/rebase. A normal corrective commit follows it.

Failed run 38322895613 tested b7eefa3. Downloaded both research artifacts:
macOS 11779447483 (job 115054833798), Windows 11779049892 (job 115054833832).
The macOS manifest's 24 hashes verify. Windows produced no manifest and only O0.
The ordinary production jobs passed; research failures were infrastructure,
not observed mathematical violations.

macOS: artifact establishes Apple clang 15.0.0, Xcode_15.4, arm64 Darwin 23.6.0,
OpenCV 5.0.0, and missing `<limits>` during preprocessing. The deeper cause
(SDK selection versus unavailable toolchain headers) was not recorded by that
run. It is not honest to claim that distinction has already been established.

Windows: GCC package 16.2.0-5, OpenCV 5.0.0-5, managed MinGW64 compiler version
query succeeds, but compilation exits nonzero without diagnostics. Exact
compiler/frontend/runtime cause remains unresolved. One proven harness defect:
the unguarded preprocessing/grep pipeline under set -e can abort before later
modes and manifest creation. The silent compiler failure is not inferred to be
a DLL problem. Colon-separated Windows drive-path handling was also removed,
without claiming it was the observed compiler's root cause.

## Corrective design

The shell entry delegates to a standard-library Python subprocess harness.
Every invocation records argv, exit status, separate stdout/stderr and combined
checker input. Launch exceptions have status 127 with diagnostics. The first
required failure is retained; optional diagnostics cannot overwrite it.
Finally always writes a focused text checksum manifest for failures within the
Python harness. Python itself/output-directory creation remains an external
prerequisite; workflow logs retain failures before Python can initialize.

Apple candidates come from xcrun's selected developer directory and discovered
installed Xcode applications. For each, compiler and SDK come from the same
DEVELOPER_DIR; SDKROOT and explicit -isysroot are paired with -stdlib=libc++.
Verbose preprocessing inventories include searches and libc++ header presence.
Only a candidate passing the exact `<limits>` smoke compilation and launch is
selected; no borrowed headers, guessed include directory or global xcode-select
change. Otherwise fail with a clear diagnostic.

Windows compiler derives from managed OpenCV pkg-config libdir, restricted to
MinGW64, and uses a native child-process PATH with native separators. The same
compiler/environment executes version/target, verbose preprocessing, frontend
location/import diagnostics, plain main, limits, OpenCV compile-only, OpenCV link
and executable launches. Driver/frontend PE imports are optional evidence, not
proof of loaded DLL resolution; successful numerical trace records actual modules.
No MSVC substitution or additional package upgrade.

Preflight failures explicitly leave all modes PREREQUISITE_NOT_COMPLETED.
After preflight, every O0/O2/O3 runs even if a previous numerical build or macro
preprocessing fails. Checkers only run after successful numerical launch;
missing/empty output is a prerequisite failure, not failed arithmetic.
Required failures return nonzero. Existing always-upload steps retain logs and
manifest with 14-day retention. Workflow jobs/guards are unchanged.

R1/R2 sources, rational certificates and 2^-20 pow tolerance remain unchanged.
No production files, ABI, pins, Alire manifests or Windows certification changes.

## Validation and handoff

Synthetic tests cover stderr failures, silent exits, absent executables, success
without output, preprocessing failure, numerical execution failure, missing
numerical output without checker execution, finalization and successful runs.
These test reporting only; they do not qualify Apple/Windows numerics.

Linux research passed O0/O2/O3, including unchanged numerical, independent
rational and native extraction checks. Repository/configuration, shell syntax,
profile/layout and actionlint checks passed. Raw evidence stays in a sibling
features-011-r3a-evidence directory, outside committed source.
Final configuration result: **88/88 passed**, including 11 focused harness
tests; all 190 indexed Linux text-evidence hashes verified. ABI exports remain
17; 67 AUnit registrations are static inventory, not a new AUnit execution.

R1/R2 and both Task 008B worktrees remain clean at their protected SHAs; R2
evidence-index hash is unchanged. Task 010 research inventory remains present
and retained documentation hashes verify. No PR, merge, tag or release.

One corrected commit/push/dispatch is authorized. Record its exact tested SHA
and run ID in the final handoff. If queued/in progress, stop without polling.
After completion require all modes on both platforms and separately review
native build correspondence; compiler smoke success is not qualification.