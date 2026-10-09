# Task 008A-W1 — Windows installed-consumer qualification correction

## Reconciliation and scope

Fetched Features main: `87058d4a87e0bf9412b7f877017a1bc1e11c9c27`.
No open Features PRs existed at reconciliation. Work is isolated on
`corrective/008a-windows-consumer-validation`; existing worktrees and the
independent Task 008B candidate were not altered.

Core remains source-pinned to
`386c5360ac51f2b62e522853d94290aec4ee14a0` in all three manifests and in the
consumer's actual resolved-HEAD assertion. No Core/index dependency change,
production Ada/C++, GPR shim project, native ABI, version, release or tag change.

## Observed failures and correction

Windows run [37873824129](https://github.com/zackboll/opencv_features_ada/actions/runs/37873824129),
job `113637670880`, passed 67/67 AUnit, native DLL inspection, six GPRinstall
regressions, source-pinned consumer and recursive installation. Its normal
production PE inspection reports `libopencv_features-500.dll` and
`libopencv_core_shim.dll`. Installed PE inspection reports the native Features
DLL, then exits at the incorrect direct `opencv_core[0-9]` requirement.
Core functionality may be shim-mediated/transitive, so a direct native Core
DLL dependency is not an installation contract. The corrected check requires
whole actual backend and Core-shim names, case-insensitively, rejecting shim-only
or unrelated names. No artificial production dependency was added.

The same job records two `find: Failed to save initial working directory`
diagnostics after renaming the directory containing the shell's CWD. The helper
now changes to the preserved evidence directory before either rename. All piped
inventory/runtime/test-source collections now run `find` separately, retaining
raw output and failing before `sort`, `paste` or `grep` can mask a failure.
Sorted evidence remains available. Optional `bin` is included only when present;
required `lib` collection errors are no longer suppressed.

Existing MinGW64 compiler selection, configured native Core import library
under the pkg-config-selected installation, DLL/import pairs, stale static-shim
rejection, runtime execution, symbol resolution and project/source/linker audits
are preserved. Workflow routing is unchanged: no Windows PR job.

## Executed local Linux validation

Environment: Linux x86_64, OpenCV 4.10.0, g++ 14.2.0, Alire 2.1.1,
GNAT 16.1.0 and GPRbuild crate 26.0.1. Evidence retained separately from source
in a task-specific temporary log directory; consumer evidence basename
`features-consumer.tJ83Z2IY`.

- Repository checker PASS: 17 declarations/imports, 67 registrations.
- Configuration tests: 42 executed / 42 passed, including 9 new regressions.
- Profile/C11 helpers, all shell syntax and `git diff --check`: PASS.
- GPRinstall fixtures: 6 executed / 6 passed (synthetic artifacts).
- AUnit: 67 executed / 67 successful, zero assertions/errors.
- Actual production archive: 17 exported `opencv_features_*` symbols, unchanged.
- Actual-shim production and fault-injection native boundaries: PASS.
- ASan/UBSan production and fault variants: PASS with leak detection, no suppressions.
- Both synthetic examples: build/run PASS.
- Fresh source-pinned, installed prefix-A and relocated prefix-B consumers: PASS.
  Actual Core HEAD verified; prefix A physically absent, no symlink; separate
  fresh consumer builds; Core/Features project, source and linker paths audited.

The initial new static regression overmatched the existing standalone macOS
`find` (which is not a pipeline). It was corrected to reject piped collection;
no native or installation oracle was weakened.

## Hosted/review gate

Exact final-head Linux/macOS hosted PR results and head equality are recorded
in the PR handoff after CI completes, not inferred from local tests.
Windows installed/relocated certification remains pending the existing
post-merge workflow on new main after review/merge. Required evidence includes
67/67 AUnit, 6/6 fixtures, installed DLL/import pairs, all three consumers,
physical removal of prefix A and actual prefix-B project/source/linker paths.
Synthetic PE/CWD fixtures are not Windows native relocation evidence.
No automatic merge, release, tag or publication.