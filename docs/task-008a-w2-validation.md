# Task 008A-W2 — installed Features linker-path ownership

## Baseline and failure

Starting main: `641a1a262db63570ecca76b076f0407c9787e7ae`, including PR #9.
No overlapping open PR was present. Changes use an isolated corrective worktree;
the Task 008B candidate is not modified or applied.

Windows run 37876542933, job 113646349826, executed all three consumer modes
but failed at the final installed metadata audit. Its relocated Features GPR
contained `Linker_Options` with an absolute original `candidate/lib` path.
The audit is correct: execution success is not safe metadata or full relocation
certification. The logs do not establish Windows library search precedence.

## Research and correction

Features imports `opencv_features_shim.gpr`, a library project whose source
`Library_Dir` is `lib`. GPRbuild resolves that library dependency and supplies
its directory at link time. GPRinstall emits a library project with relative
`Library_Dir` (`../../lib/opencv_features_shim`) and Features retains its shim
project import. Those attributes, not an evaluated original-source `-L`, own
the installed search directory.

The predecessor `Linker.Linker_Options` explicitly concatenated
`Project'Project_Dir` and `lib`. Actual GPRinstall 26.0.0 reproduces its absolute
value in installed metadata. The correction removes only that `-L`, retaining
`-lopencv_features_shim`. The corresponding external-shim relocatable
`Library_Options` receives the same correction. Core 0.4.1 provides the useful
comparison: its consumer linker options retain the shim `-l` without source
`-L`. Core is not changed.

No installed-project substitutions, hardcoded destination, audit relaxation,
public Ada/C++ changes, pin removal, version bump or workflow routing changes
are included. External MSYS2 compilation, required DLL/import archive, Linux
static-PIC and Apple-clang shim behavior remain unchanged.

## Tests and local results

Alire 2.1.1; GNAT 16.1.0; GPRbuild crate 26.0.1 / binary 26.0.0;
GNU g++ 14.2.0; Linux x86_64; OpenCV 4.10.0 / features2d.

- Repository, profile, shell syntax and whitespace checks: PASS.
- Configuration: **44/44**, including two new source/removed-prefix linker
  metadata negatives and all nine unchanged W1 regressions.
- Existing GPRinstall regressions: **6/6**.
- New actual installed-link GPR regressions: **2/2**, with corrected static-PIC
  and relocatable Ada-library subcases. The predecessor emits absolute source
  `-L`; corrected source builds and installation pass, retain shim dependency,
  and emit library projects. After moving A to B and hiding original libraries,
  fresh consumers link/run. Actual link traces use B's shim directory, not A
  or original libraries. This external Unix shim fixture is not Windows native
  DLL/import-library certification. Existing six tests enforce archive handling.
- AUnit: **67 executed / 67 passed**, zero assertions/errors.
- Actual native exports: **17**, unchanged declarations/imports.
- Production/fault native boundary and actual-shim ASan/UBSan with leak
  detection: PASS.
- Both examples: built and ran successfully.
- Real Linux source-pinned, installed-A and fresh relocated-B consumers: PASS.
  A physically absent; original build/source locations hidden. Core/Features
  project/source/link-trace and metadata audits: PASS without weakening checks.
  Only the existing unused C++ provenance-variable exception is exercised.

The new regressions run through `scripts/test.sh` on Linux/macOS; Windows
continues using the full post-merge native qualifier. Actual Apple-clang/native
macOS qualification is supplied by exact-head PR CI, not Linux fixtures.
Core remains pinned to `386c5360ac51f2b62e522853d94290aec4ee14a0` in all three
roots, with production constraint `~0.4.0`. Features remains `0.1.0-dev`.
No official indexed dependency resolution is claimed.

## Review gate

Commit/push and a non-draft corrective PR are authorized; no merge, release,
tag, automatic merge or Windows PR job is authorized. Exact-head hosted
results and commit identity are reported in the task handoff. After review and
merge, the new Windows main run must pass the full final installed metadata
audit, not merely execute the consumer applications.