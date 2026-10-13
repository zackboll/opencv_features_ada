# Task 011-R3B — preserve pkg-config include semantics

Disposition: **PLATFORM_EVIDENCE_PENDING**.
macOS subgate: **MACOS_NATIVE_CORRESPONDENCE_PENDING**.
Research only; no configurable ORB or production qualification.

## Reconciliation and retained evidence

Clean research branch `research/011-r3-hosted-numerics` started at
`3187737411329f241e673e8ab1b33063fea9ec2e`, equal to fetched origin.
Completed R3A run 38327410260 tested that SHA. Research jobs:

| Job | ID | Conclusion | Artifact | Manifest entries verified |
| --- | --- | --- | --- | --- |
| macOS numerics | 115069197275 | success | 11782040365 | 228 |
| Windows numerics | 115069197381 | failure | 11782295372 | 74 |

All five other workflow jobs succeeded. Both downloaded ZIP CRC inventories
and all internal text hashes verify (Windows manifest paths use backslashes).
Archive SHA-256 values:

- macOS: `a33a6bd461690fb674a28e3da240760d6312aa6e54c66c91c1bada77f807038a`
- Windows: `a7d9c0a04e59d7cc75687b86a6ba2b2ff9c1e5c70d32d572c802108bc2285b02`

These are locally computed archive identities, not a claim of comparison with
an independently published ZIP digest. Raw evidence is retained outside source
in the sibling `features-011-r3b-evidence` directory.

Protected HEADs recorded before work: R1 f29d988, R2 8127c44, both Task 008B
worktrees 670643d36f6fdcb0e96fcc5ee9ee702dc7a2cad3, Task 010 1c8860d.
R1/R2/008B were clean. Task 010's existing untracked research was preserved;
the retained Task 010 checksum inventory verified. R2 evidence-index SHA-256
remains `086cc557cde49f044417cd91ba15490ac553496ff6e436d14351a3aff4ded3d2`.

## GCC failure: established mechanism versus Windows causality

Windows GCC 16.2.0 and ordinary C++/limits compile-and-launch preflights passed.
The first required failure is `preflight/opencv-compile`, in libstdc++ cstdlib's
`#include_next <stdlib.h>`. No numerical optimization mode ran.
The pkg-config output was an `-I` argument pointing at the managed OpenCV5
include directory. R3A incorrectly changed its option class to `-isystem`.

GCC searches user `-I` directories and system directories in different groups;
`#include_next` resumes after the directory containing the current header.
Moving a CRT include directory before libstdc++ can therefore make stdlib.h
unreachable from cstdlib, even when the file exists. This is not a missing
compiler, absent OpenCV installation, or demonstrated numerical violation.

A real local Debian GCC 14.2.0 test with `<cstdlib>` passed normally and with
`-I/usr/include`; `-isystem /usr/include` failed with the same missing stdlib.h
diagnostic. Its verbose search listed /usr/include before libstdc++ and removed
the duplicate later occurrence. This demonstrates the mechanism, **not an
exact reproduction of the Windows OpenCV include directory**. Additional
nostdinc experiments failed and are retained, not counted as successful tests.

Important limitation: Windows R3A's limits preprocessing inventory already
lists the managed CRT include directory before libstdc++, even without the
OpenCV flag. Consequently, these artifacts do **not** establish that rewriting
the OpenCV flag alone caused that ordering. Targeted include environment and
original-versus-transformed preprocessing diagnostics are added for the next
campaign. Do not claim sole Windows root cause before those results.

## Narrow changes

- Parse pkg-config cflags and libs as shell-escaped argument lists without
  rewriting option classes, ordering, drive-letter colons, defines or libraries.
- Preserve explicitly supplied `-isystem`. No hardcoded OpenCV directory,
  replacement headers, global diagnostic suppression or tolerance change.
- Preserve checked subprocesses, separate streams and final failure manifest;
  mark failed preflight compilation explicitly `PREREQUISITE_FAILED`.
- Record only targeted include-path environment variables. Windows A/B
  preprocessing is optional diagnostic evidence; real compiles always use
  original flags, with the same compiler/environment as the probes.
- Inventory installed Apple clang candidates, preferring discovered Apple
  clang 16 only when its own SDK/libc++ pair passes compile and launch. No
  unmatched headers or global Xcode selection change.
- Record the actually loaded macOS Features dylib's linkage, undefined symbols
  and disassembly, plus arithmetic instruction neighborhoods. Diagnostic
  failures cannot become numerical-pass claims or overwrite required failures.

## macOS correspondence review

R3A macOS 14.8.9 ARM64 used Apple clang 15.0.0, Xcode 15.4's macOS 14.5 SDK,
libc++ headers reporting 170006, and OpenCV 5.0.0. All O0/O2/O3 executables and
unchanged R1/R2 rational checks passed. Fixed-input powers, scale stores, float
conversions, rounding and recurrence observations are preserved, as are native
ORB extraction observations. These remain empirical fixed-input evidence.

Installed OpenCV reports clang++ 16.0.0.16000026 and Release -O3 -DNDEBUG;
recorded flags do not contain fast-math. The probe O3 disassembly calls `_pow`,
then converts double to float (`fcvt`), and rounds via `frintx`/`fcvtzs`.
The installed fast_math.hpp uses the clang math builtin/lrint path on this
target rather than the x86 SSE path. Loaded modules include the Homebrew
OpenCV 5.0.0_5 Features/Core dylibs, libSystem, libsystem_m, libc++ and libc++abi.
This supports shared runtime provenance and ordinary rounding semantics.

It does not yet identify the compiled native ORB pow call sites or exclude
compiler transformations of those sites. R3A retained only probe disassembly
and stopped candidate discovery at the first passing clang 15 pair. Thus no
claim that clang 16 was unavailable, or that native arithmetic is equivalent,
is justified. The next campaign inventories candidates and captures native
symbols/disassembly; attribution of instruction neighborhoods to relevant ORB
paths remains a review obligation. Successful probe results are not discarded.

## Local qualification and handoff

Repository checker, 92 configuration regressions (15 focused harness tests),
profile/layout tests, shell/Python syntax and cross-platform actionlint passed.
Real Linux GCC 14.2.0 probes passed O0/O2/O3, including unchanged independent
R1/R2 checks; 191 manifest hashes verified. No new native AUnit execution is
claimed: 67 registrations and 17 ABI declarations are static inventory.

R1/R2 sources/certificates and the 2^-20 power tolerance are unchanged. No
production files, pins, manifests, ABI, workflow guards, production jobs or
windows-post-merge workflow changes. One normal corrective commit and one
dispatch are authorized. Record their exact SHA/run in the external campaign
receipt and final handoff; stop if queued/running without polling. Upon
completion verify artifact hashes and all modes, then assess native
correspondence independently. Neither smoke tests nor a green workflow alone
establish the safety gate.