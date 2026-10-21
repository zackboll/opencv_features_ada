# FEATURES-CI-016 — Windows native-boundary qualification

## Release identity and original gap

The approved **0.1.0** source remains merge commit
`e6d977f0bba02c526920834ef6e88905366ed1b9`, tree
`0265f6e39de174722cfe8ff59d7663dddbcf8cbd`. Fresh main equalled that commit
when this correction began. No release tag exists. PR #26 is unrelated and
is not incorporated into this branch. During local qualification a fresh fetch
observed that it was merged externally into main at
`782e33ef6822887c45e607c5934032d9d856b3ad` (tree
`a505c57ef1eb2f385bd40d6198801bdbaf2d810e`). This task did not merge or modify
that PR; the correction remains based on the main verified at branch creation.
No newer main commit substitutes for the pinned release source.

[Windows run 39540052561](https://github.com/zackboll/opencv_features_ada/actions/runs/39540052561),
[job 119025486968](https://github.com/zackboll/opencv_features_ada/actions/runs/39540052561/job/119025486968),
passed AUnit 67/67, native setup, DLL checks, GPRinstall, all three consumer
modes and audits. Step 8 called `scripts/test.sh`, whose raw-boundary driver
is Linux-only. No production/fault-injection raw-boundary execution appears
in that Windows log. Overall workflow success did not close this coverage gap.

## Compilation and execution contract

After `alr -n build`, from an Alire environment on Windows/MSYS2:

```sh
alr -n exec -- sh scripts/run_windows_native_boundary.sh . obj/windows-native-boundary
```

The shell entry requires Windows/MSYS2 and native Windows Python 3.11+ (the
existing Windows manifest-validation prerequisite). The Python orchestrator:

- Reads the generated `config/opencv_features_install.gpr`, not a second
  pkg-config selection. Requires external MinGW64 GNU g++, target
  `x86_64-w64-mingw32`, the configured OpenCV headers/import libraries and the
  resolved indexed Core bridge, C factory header, DLL and import library.
- Validates stable Core ~0.5.0 and records its parsed version/public Git origin.
  No mock bridge, sibling Core pin, copied header or new production dependency.
- Compiles the selected source checkout's **actual**
  `cpp/opencv_features_shim.cpp` and `tests/cpp/native_boundary.cpp` separately
  for each variant, then links each independent executable against the native
  OpenCV Features/Core and Core-shim import libraries. It does not link the
  prebuilt Features shim DLL.
- Defines `OPENCV_FEATURES_BUILDING` in both translation units so standalone
  Features definitions/declarations agree on Windows export conventions, rather
  than importing themselves. Only the fault variant defines
  `OPENCV_FEATURES_TEST_HOOKS`. No production header or ABI changes are needed.
- Removes inherited C/C++ include/compiler/library injection variables in child
  processes. Runs through the selected source's unchanged `run_native.sh`,
  preserving existing child-only Core/MinGW DLL lookup without altering Ada's
  compiler PATH.
- Checks defined symbols: production must lack `opencv_features_test_fail`;
  fault must contain it. Both executions must return zero and print the existing
  ORB, matcher, KNN2 and radius coverage markers. Fault execution must also print
  the existing radius checkpoint 15/16/17/18 × five exception-category marker.
  A symbol alone or an empty successful executable is not accepted.
- Requires both successful variants. Compile, link, symbol-inspection and
  execution failures propagate with command diagnostics. Old success reports
  and executables are removed before reuse. Completion markers are issued only
  after the corresponding execution and marker checks, and the shell rejects
  a zero exit missing either marker:
  `WINDOWS_NATIVE_BOUNDARY_PRODUCTION_PASS` and
  `WINDOWS_NATIVE_BOUNDARY_FAULT_PASS`.

Each variant has separate object/executable/log paths. `qualification.json`
records tested source commit/tree, harness commit/tree, Core version/origin,
compiler path/version/target, configured OpenCV version, import selections and
both results. It is written only after both variants and final source-integrity
checks pass. CI uploads only logs/JSON, not unqualified binaries or environment
dumps, with 14-day diagnostic retention.

## Independent immutable release campaign

The second mandatory Windows step runs:

```sh
sh scripts/qualify_windows_release.sh obj/windows-release-boundary
```

It independently clones the fully fetched harness repository without local
hard-link optimization, checks out the original approved commit detached, and
verifies both exact commit and tree **before** Alire builds that original
source. The new runner stays outside that checkout and is invoked through the
original crate's `alr exec` environment with explicit source/output paths and
expected commit/tree. The compiled C++ implementation **and boundary driver**
come from the original checkout. Tracked edits and unignored additions fail
qualification before and after execution. Generated ignored Alire/build files
are permitted; no tracked file is patched or copied into the source.

The final marker is `WINDOWS_RELEASE_SOURCE_QUALIFIED` followed by the approved
commit and tree. The report separately identifies the newer harness: that
harness is qualification infrastructure, not content of the release archive.
Repeated main pushes repeat both campaigns; no Windows PR/manual triggers are
added. Main and pinned-release results are separate, neither substitutes for
the other. Linux's ordinary and ASan/UBSan runners remain byte-identical.

## Coverage and regressions

The existing raw driver covers real Core factories/borrowed bridge headers,
ORB extraction/masks/schema, invalid/null inputs and clearing, descriptor
export, result lifetime, nearest/mutual-nearest, exact Hamming/Hamming2 oracles,
KNN2 and high indices, inclusive radius/ties/empty results, noncontiguous ROIs,
input preservation, publication atomicity and injected exception translation
and cleanup. This is CPU qualification, not arbitrary image/platform safety.

Fifteen added configuration tests exercise both required variants, individual
compile/link/execution failures, missing execution/completion markers, missing
fault execution, production symbol leaks, absent fault controls, wrong compiler
target/path, missing/wrong import libraries, source commit/tree and dirty-source
rejection, independent release setup/build/run failure propagation, stale
report rejection, mandatory unconditional CI steps/full history, and unchanged
Linux runner digests. These Linux-runnable fixtures **do not execute Windows
algorithms**. Existing 67 AUnit registrations and 17 native exports are unchanged.

## Local qualification and review gate

Local Linux: Alire 2.1.1, selected GNAT 16.1.0 / GPRbuild crate 26.0.1,
g++ 14.2.0, native OpenCV 4.10.0/features2d, indexed Core 0.5.0 origin
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`.

- Repository check, shell syntax, fixed-profile/layout helpers: PASS.
- Configuration suite: **101 tests passed**, including 15 new harness/policy tests.
- Native build and AUnit: **67 registered / 67 executed / 67 passed**, zero
  assertions/errors. Ordinary production/fault raw drivers: PASS.
- Actual-shim ASan/UBSan, production and fault: PASS, no reported diagnostics.
- Both examples, six external-shim GPRinstall regressions and two installed-link
  metadata regressions: PASS.
- Fresh source/installed/relocated consumers and active audits: PASS. The
  pre-existing unused `Common_Cxx_Switches` source include is reported as
  non-load-bearing; no auditor acceptance rule changed.
- Production Ada/C++/GPR, all three manifests, boundary driver, `test.sh` and
  `run_sanitizers.sh` are unchanged from the approved release.

An initial local retry failed because the host `/tmp` inode quota was exhausted
(`Errno 28`); consumer installation also failed to create an ALI file there.
Diagnostics were preserved, then complete configuration/native/consumer checks
passed using disk-backed temporary storage. No source/test weakening was used.

The original merged-main documentation run
[39540052584](https://github.com/zackboll/opencv_features_ada/actions/runs/39540052584)
has now completed successfully, deployment `7217229632`. An independent HTTP
retrieval verified all **18 public site files** against the qualified uploaded
artifact SHA-256 values at <https://zackboll.github.io/opencv_features_ada/>.
This is public-byte/deployment verification, not a new browser campaign.

Final committed/pushed identities and PR-hosted results belong in the corrective
PR to avoid a self-referential source commit. No actual Windows execution of
this correction has occurred locally. Independent review, eventual merge, and
successful main-branch Windows execution of **both corrected-main and immutable
release campaigns** are mandatory outstanding gates. Leave the PR non-draft,
unmerged, auto-merge disabled. No release tag, GitHub Release or Alire index
submission is authorized by this correction.