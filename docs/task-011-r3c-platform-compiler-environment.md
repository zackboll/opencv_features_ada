# Task 011-R3C — platform compiler child environment

Disposition: **PLATFORM_EVIDENCE_PENDING**. Production Task 011 remains gated.
Both native correspondence subgates remain pending. Research only.

## Reconciliation

Clean branch `research/011-r3-hosted-numerics` started at
`bce42c72be41e880a416bd1fab5286d25863ffa5`, equal to fetched remote HEAD;
ancestry verified. No amend, rebase, reset or force push.
R3B run 38328737960 tested that SHA. All four ordinary jobs passed;
the two research jobs failed:

| Platform | Job | Artifact | Verified manifest entries |
| --- | --- | --- | --- |
| macOS | 115073378840 | 11781352666 | 209 |
| Windows | 115073378663 | 11781414441 | 83 |

ZIP integrity and all internal hashes verified, normalizing Windows manifest
path separators only for verification. Downloaded archive SHA-256 values match
the supplied identities exactly:

- macOS `c3067b13302e2527f0e1cdc871ae62d9db9a5d2057b921b1cdf11cb83e5f7e82`
- Windows `a6c9f67cfacb341759185442ffd521498a2df9910a0f0eba3c4e52195408781b`

Raw archives, extracted evidence, run metadata and local validation logs are
retained in the external sibling `features-011-r3c-evidence` directory.

## Apple: warning policy, not arithmetic

Apple clang 16.0.0 from Xcode 16.1, its macOS 15.1 SDK and libc++ passed
compiler/OpenCV compile/link/launch preflights. OpenCV 5.0.0 headers then failed
the numerical build at O0/O2/O3: mat.inl.hpp lines 2330/2345 expand CV_XADD to
`_Atomic`, producing `-Werror,-Wc11-extensions`. The first required failure was
O0/orb_r2_numerics-compile. This is a research warning-policy prerequisite
failure; no failed arithmetic premise is established.

Only Darwin research warning flags gain `-Wno-error=c11-extensions`, after
`-Werror`. The warning remains enabled/visible; all other warning classes remain
errors. This flag necessarily applies to that warning class throughout the
research translation unit, not solely the header location. Sources, C++17,
optimization settings, pkg-config semantics and paired SDK/libc++ stay intact.
No -w or general warning downgrade.

The next hosted run compiles the same OpenCV core smoke source under the
original warning policy (optional negative evidence), then requires compilation
under the narrowly adjusted policy. Failure stops qualification without wider
suppression. No clang is installed locally; the actual Apple positive control
remains pending. Deterministic tests inspect actual subprocess argv and streams,
not just source text, but cannot establish Apple compiler behavior.

## Windows: scoped include-environment correction

Managed MinGW64 GCC 16.2.0 and OpenCV 5.0.0 were present. Ordinary C++ and limits
compile/launch preflights passed. OpenCV compilation failed in cstdlib's
`#include_next <stdlib.h>`. Both original -I and transformed -isystem failed.
Recorded C_INCLUDE_PATH and CPLUS_INCLUDE_PATH duplicated the selected
compiler's mingw64/include CRT directory; CPATH was unset. Verbose search
placed that directory before libstdc++, leaving no later CRT directory for
include_next. This strongly implicates inherited overrides, not package absence.

The compiler child environment is copied, never changing os.environ or runner
configuration. Windows ntpath normalization, case folding and full component
comparison identify the native include directory relative to the selected
compiler. Semicolon splitting preserves drive-letter colons and spaces.
Only matching entries in C_INCLUDE_PATH/CPLUS_INCLUDE_PATH are removed;
unrelated entries, empty components, CPATH and the managed runtime PATH remain.
Original values and corrected values are recorded. The same corrected child
environment is used for subsequent preflights, compilation, preprocessing,
checkers and relevant launches; initial inventory intentionally records the
inherited state. No reinstall, replacement header or packaging change.

Hosted controlled evidence preprocesses `<cstdlib>` with the original inherited
environment (optional negative) and then the corrected environment (required
positive), using the same compiler/source/arguments. The corrected OpenCV core
compile, link and launch remain required. If positive preprocessing or OpenCV
compilation fails, stop with the new diagnostic rather than speculate.

Real local Debian GCC 14.2.0 reproduced the mechanism: cstdlib preprocessing
with CPLUS_INCLUDE_PATH=/usr/include failed (status 1); removing that override
passed (status 0). Logs retain verbose search and diagnostics. This establishes
a local mechanism, **not actual MinGW64 before/after causality**. Windows root
cause resolution must await the controlled hosted results.

## Numerical integrity and native correspondence

All O0/O2/O3 modes still compile and launch R2 numerics, R3 trace and R1 target
probes, run unchanged rational comparisons, perform native extraction through
the existing probes, and record macros/compiler/library provenance. Compile
failures are prerequisites, not arithmetic failures. Manifest generation and
first required failure retention remain intact; negative diagnostics are not
required successes or numerical results.

R3B produced no successful numerical probes on either platform. Apple clang
16 selection alone does not establish native equivalence. Existing Apple
loaded-library linkage, symbols, disassembly and arithmetic-neighborhood capture
are retained. Windows adds loaded Features DLL PE imports/disassembly alongside
probe disassembly and actual module inventories. Review must attribute native
ORB pow/round/conversion paths and compare floating-point/build flags and math
runtime, rather than infer equivalence from compiler version or extraction.
Both **MACOS_NATIVE_CORRESPONDENCE_PENDING** and
**WINDOWS_NATIVE_CORRESPONDENCE_PENDING** apply until that review is complete.

## Local qualification and preservation

Repository checks, configuration regressions, profile/header/layout tests,
shell/Python syntax and actionlint passed. Linux GCC 14.2.0 research passed
O0/O2/O3 with unchanged R1/R2 rational checks; all 192 indexed hashes verified.
Final configuration result: **99/99 passed**, including **22 focused harness
tests**, recorded in the external final configuration log.
No new AUnit execution claimed: 67 registrations and 17 ABI exports are static
inventory, not executed-test counts.

Protected R1 f29d988599d538a8edecafdc631b1c8f2d99a930, R2
8127c448a3bb2d811b9ffd1a43db6f18d97ea0eb and both 008B worktrees at
670643d36f6fdcb0e96fcc5ee9ee702dc7a2cad3 remain clean. Task 010 HEAD 1c8860d
and its existing untracked GFTT research are preserved; retained checksums verify.
R2 evidence index remains
086cc557cde49f044417cd91ba15490ac553496ff6e436d14351a3aff4ded3d2.
Production worktree HEAD 4711c2b is unchanged and clean.

Only harness, configuration harness tests and this document change. Certificates,
R1/R2 probes, 2^-20 tolerance, feature/level bounds, source-review assumptions,
production Ada/C++, ABI, manifests, pins, versions and workflows remain unchanged.
One normal corrective commit, fast-forward push/parity verification and one
dispatch follow local validation. Exact SHA/run are retained in the external
receipt and final handoff. Stop if queued/running, without polling. No PR,
merge, tag, publication or release. A green probe does not establish universal
C++ portability or automatically complete production Task 011.