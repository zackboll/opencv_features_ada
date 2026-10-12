# Task 008A-W3 — Windows resolution-trace evidence gate

## Disposition

`DIAGNOSTICS_REQUIRED / WINDOWS_POST_MERGE_PENDING`

This is a diagnostic-only correction, not a claim that Windows relocation is
fixed. Starting main is `1c8860d7b491e17782ea260dab078f3f555e41d4`.
Core remains pinned to `386c5360ac51f2b62e522853d94290aec4ee14a0`.
Main was fetched; there were no overlapping open PRs. Work is isolated on
`corrective/008a-windows-resolution-trace`. Existing worktrees, Task 010
untracked research, and Task 008B work are not changed. The previously absent
Task 008B temporary directory is not asserted to exist or recreated.

## Retained Windows evidence

Run: <https://github.com/zackboll/opencv_features_ada/actions/runs/37879014320>
Job: `113654123663`; head matches starting main.

The job-log API returns the retained raw **Actions job log**, but the artifact
API returns zero artifacts. That job log does not contain the raw installed or
relocated GPRls/GPRbuild output: those commands redirect output to temporary
files, which are not printed on success. The final auditor prints only its
normalized matching path. The retained job log confirms the installed and
fresh relocated consumers executed and prefix A was removed, but cannot
identify the offending resolution record. Application success is not evidence
that a source/include/project/library lookup is harmless.

The reported match is `features-consumer.24rqmvwd/candidate` in the **installed**
combined resolution trace. It is not yet known whether its source is GPRls,
GPRbuild compiler/binder/linker output, project metadata evaluation, an unused
diagnostic, or inherited configuration. No non-load-bearing exception is
established or added.

## Source inspection

The validator concatenates projects then build logs. It clears project/include/
library lookup environment variables, hides candidate and source consumer
directories, constructs installed-only `GPR_PROJECT_PATH`, then builds fresh
consumer directories. On Windows it uses GCC to link the Ada main, static Ada
runtime switches, and external MSYS2 DLL/import-library pairs. The original
absolute source `Linker_Options` defect remains removed; imported shim projects
still own their relocatable library directories.

Normalization replaces backslashes and case-folds on Windows. Matching uses the
unique `features-consumer.*` suffix to tolerate drive/MSYS and short **parent**
directory spellings (the retained Windows job uses `RUNNER~1`). This is not a
general 8.3 canonicalizer: shortened components within the unique work suffix
or an unrelated checkout are not resolved by it. No normalization/acceptance
change is made here; native raw records remain essential. Simulated drive,
MSYS, separator, case and short-parent fixtures are not Windows certification.

GPRinstall's pre-existing narrowly reviewed unused `Common_Cxx_Switches`
metadata handling is unchanged. It does not exempt resolution-log records.
Any candidate occurrence, even on a textual diagnostic line, still fails.

## Diagnostic implementation

On a forbidden trace occurrence the auditor now writes and reports:

- Combined resolution log and normalized matching path.
- Raw source log (GPRls versus GPRbuild), one-based line number and exact line.
- Two lines of context on either side where available.
- Command-shaped compiler/linker or binder/linker hints, or an explicitly
  unclassified/project diagnostic. These hints never change acceptance and
  are not a determination of active lookup.

Missing source logs are reported, with combined-trace fallback. All matching
raw records in both source logs are retained; raw files are not rewritten.
The validator exposes only the evidence directory as a step output. Windows
adds a failure-only, 14-day artifact for the six raw/combined installed and
relocated logs, failure report, and installed GPR metadata. It excludes full
environment output, PATH inventories, caches and binaries. Windows triggering
remains push-to-main only; the audit is neither bypassed nor downgraded.

## Regression and qualification record

- Repository consistency and helper profile/layout checks passed.
- Configuration suite: **54/54**, retaining all prior 44 cases; ten added
  diagnostic/fixture checks. Active compiler `-I`, active linker `-L`, removed
  prefix A, GPRls source diagnostics and unknown textual records remain rejected
  even when valid installed paths occur elsewhere in the same trace.
- Native Linux AUnit: **67 run / 67 passed**, zero assertions/errors.
- Real GPRinstall fixtures: **6/6**; installed-link metadata regressions: **2/2**.
- Production and fault-injection native boundaries passed on OpenCV 4.10.0.
- ASan/UBSan production and fault-injection runs passed with
  `detect_leaks=1:halt_on_error=1`, with no reported sanitizer errors.
- Both examples built and executed (86 zero-distance matches reported).
- Source-pinned, installed prefix-A, and fresh relocated prefix-B consumers
  passed. Prefix A was physically absent before the B build. Final installed
  metadata and both resolution audits passed. Raw Linux evidence is retained
  in the local consumer evidence directory (not committed).
- Shell syntax and whitespace checks passed. The initial foreground aggregate
  exceeded the command timeout after native/fixture tests; the remaining
  sanitizer/example/consumer aggregate completed with recorded exit status 0.
- Local compiler: GCC 14.2.0; GNAT 16.1.0; GPRbuild/GPRinstall 26.0.0;
  Alire 2.1.1. Native qualification uses the unchanged Core pin.

Exact-head CI is recorded in the PR validation update before the review gate.
No local macOS or
Windows execution is claimed. The eventual reviewed merge commit must pass the
Windows final source-path audit. If it still fails, review the published raw
record before making any corrective path-propagation or filtering change.