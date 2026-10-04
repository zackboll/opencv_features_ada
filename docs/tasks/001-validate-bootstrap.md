# Task 001 — qualify the Features bootstrap

Read `AGENTS.md`, the six `.clinerules` files, `README.md`, and the architecture,
ORB contract, build notes, source provenance, and bootstrap validation record.

## Goal

Turn the supplied initial ORB slice into an actually built and tested baseline.
This is not a task to add matching, calibration, DTED, GPU code, or a binding
generator. The supplied code is intentionally marked native-unvalidated.

## Provenance and scope

Record repository/worktree status and HEAD. Do not overwrite unrelated user
changes, create/modify a remote, force-push, merge, tag, or publish. A newly
unpacked directory may not yet have Git metadata; report that state and do
not invent a starting commit. Use a normal feature branch only when there is
a clean existing repository. No commit/push/PR is authorized by this task
unless the user separately requests one.

The default Core pin is `7956981a7881ce9121115f8cb65909aeb9edc439` (Core 0.4.0).
Read the resolved Core source and authoritative module bridge before changing
interop. Use the other OpenCV repositories as architectural evidence, but
keep Features' actual Mat-dependent ownership needs distinct from Geometry.

## Work

1. Run `python3 scripts/check_repository.py`, configuration unit tests, shell
   syntax checks and `sh scripts/run_profile_tests.sh`. Record actual output.
2. Run `alr -n build`. Correct compiler/GPR errors without changing the
   public architecture or suppressing broad classes of warnings. In
   particular, verify controlled finalization, limited result returns,
   private-child visibility, callbacks and C-compatible record layout.
3. Run `alr test` and the synthetic example. The intended baseline is 20
   registered AUnit cases; report registered/executed/passed independently.
   Fix a failed fixture or implementation from evidence rather than changing
   a numerical oracle simply to make a job green.
4. Review the native ORB path in 4.1.0, 4.10.0 and 5.0.0. Confirm the fixed
   structural profile, per-level rounding, mask behavior, packed-buffer and
   row-offset bounds, target-count doubling, and output schema. The oldest
   source review and native qualification are outstanding in the bootstrap.
5. Add native raw-C-ABI regression coverage: null outputs/detectors/masks,
   malformed selectors/thresholds, initialized failure outputs, invalid result
   indices, lifetime/finalization, and C/Ada keypoint layout. Use real Core
   handles for descriptor export. Never use fabricated pointers as if they
   were valid opaque objects. Exercise allocation/failure paths where a
   deterministic test hook is justified.
6. Run relevant ASan/UBSan probes against the actual native shim and tests.
   The existing sanitizer helper result is not native ORB coverage. Separate
   reproducible native defects, binding defects and environment failures.
7. Exercise OpenCV 4/5 builds and the platform matrix. Preserve Windows
   main/manual-only policy; do not repeatedly dispatch it for every review
   correction. Linux must not accidentally link a second OpenCV; macOS must
   use Apple clang++/libc++; Windows must use matching MSYS2 C++ imports/runtime.
8. Check a clean consumer and installed bridge/linkage path. Document any
   unresolved GPR install/relocation limitation honestly; do not substitute a
   copied bridge header or duplicate Mat wrapper as a shortcut.
9. Update source-reviewed contracts and validation evidence. Leave BF/KNN for
   later tasks after this baseline is real.

## Review gate

Report changed files, actual commands, compiler and native versions, test
counts, source revisions, failures and outstanding limitations. Distinguish
static checks from native tests and empirical tests from proved contracts.
Stop at review. No automatic commit, push, PR, merge, release or version bump.

## Version-sensitive mask regression

Task 002 supplies all-1 and 0/1/254/255 fixtures alongside 0/255 masks.
Source review confirms 4.1 and 4.10 preserve input level-zero values and
zero sub-255 resized levels, while 5.0 normalizes the incoming mask inside
the called ORB override. See `docs/orb-source-review.md`; no cross-version
count equality or binding-side normalization is introduced.
