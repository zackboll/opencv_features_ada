# Task 011-R3E — installed ORB correspondence campaign

## Disposition

**HOSTED_EVIDENCE_PENDING.**

Both platforms remain `NATIVE_CORRESPONDENCE_PENDING`.
`SAFETY_GATE_NOT_ESTABLISHED`. No configurable ORB implementation.

R3D already established the standalone numerical probes. This campaign only
asks whether the installed ORB library can be tied to that arithmetic. A
Linux smoke test is not macOS or Windows evidence.

## Baseline

- Production `origin/main`: `495e385f91022735d5c52ba766f8d25164c7a900`
- R3D research start: `11577b9cffabfa88642acdba8aa8ad75f9c91957`
- Branch: `research/011-r3e-native-correspondence`
- No open pull requests at reconciliation.
- Existing R1, R2, R3D, Task 008B, and Task 010 worktrees were not reset.
- External R3D evidence at `/home/zboll/evidence/opencv-features-011-r3d/`
  was preserved.

## What this campaign runs

`docs/research/orb_r3e_native_probe.cpp` links the installed OpenCV package
and has three modes:

- `cpu`: disables OpenCL, builds one textured 96×128 UInt8 C1 matrix, creates
  eight-level Harris ORB, and calls `detectAndCompute`.
- `opencl-observe`: a separate process that records `haveOpenCL` and
  `useOpenCL` without changing them, then performs the same extraction.
- `powers`: the existing sixteen factor/scale inputs, with binary32 stores,
  `FLT_EVAL_METHOD`, nearest rounding, and no fast-math.

Module enumeration happens after the ORB call. The harness hashes only the
loaded Features or Features2D library. It does not infer linkage from a
Core-only program.

If `modules/features/src/orb.cpp` or `modules/features2d/src/orb.cpp` is not
installed under the package prefix, the harness writes
`SOURCE_BYTES_UNAVAILABLE`. That result cannot establish correspondence.
No local OpenCV rebuild is performed.

Disassembly is filtered to `pow`, rounding, and conversion neighborhoods and
capped at 2,500 lines. The report defaults to
`GETSCALE_ATTRIBUTION_PENDING` until a later review attributes control flow.
The R1 151,547-target probe is not compiled or executed.

## Workflow guards

The existing `cross-platform.yml` gains exactly two jobs:

- `orb-r3e-macos-native` on `macos-14`
- `orb-r3e-windows-native` on `windows-latest`

Both require `workflow_dispatch` and
`refs/heads/research/011-r3e-native-correspondence`.
The original R3 numerical jobs retain
`refs/heads/research/011-r3-hosted-numerics`, so they do not run on this
branch. Production jobs and `windows-post-merge.yml` are unchanged.
Artifacts are text logs and `manifest.json`, retained 14 days, uploaded with
`if: always()`.

Windows uses the existing Alire-managed MSYS2 two-stage `pacman -Syu`
sequence and the managed MinGW64 compiler. It is not a pull-request Windows
qualification job.

## Local validation

Repository checks passed. Configuration tests passed: 107 tests.
Profile and C ABI layout checks passed. `git diff --check` passed.
Shell syntax passed for `scripts/*.sh` and `docs/research/*.sh`.
`actionlint` is not installed here, so it was not run.

A local Debian smoke test linked OpenCV 4.10.0, extracted 156 keypoints with
156 descriptor rows, passed the sixteen-power rational check, and hashed
`/usr/lib/x86_64-linux-gnu/libopencv_features2d.so.4.10.0`.
Its package prefix did not contain `orb.cpp`, so the smoke correctly recorded
`SOURCE_BYTES_UNAVAILABLE`. The separate OpenCL observation reported
`have=1 use=1`; the CPU control reported `use=0` only after explicitly
disabling OpenCL. This demonstrates the harness. It does not qualify the
Homebrew `5.0.0_5` bottle or MSYS2 `mingw-w64-x86_64-opencv 5.0.0-5`.

## Required hosted review

When the artifacts exist, review them before changing either disposition.
Correspondence requires all five layers:

1. installed `orb.cpp` bytes, or an explicit source absence;
2. compiler flags for that translation unit;
3. ORB-attributed arithmetic instructions;
4. the math/rounding runtime actually reached by that call;
5. CPU-path evidence rather than an ambiguous OpenCL default.

Missing source bytes, an unattributed `getScale`, or an ambiguous OpenCL path
keeps `NATIVE_CORRESPONDENCE_PENDING`. A contradictory power or arithmetic
result is `NATIVE_CORRESPONDENCE_FAILED`.

The sixteen-power control remains regression evidence. It does not by itself
prove that the installed ORB binary uses the same `pow`.
