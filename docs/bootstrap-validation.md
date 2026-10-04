# Bootstrap validation record

## Status

**Build/CI tranche qualified locally; not a fully qualified binding or release.**
Historical ZIP checks below are distinct from actual build/test evidence.
No native result is implied by the existence of a test or workflow.

## Task 002 — ORB native qualification

Starting fetched `origin/main`: `1feceff04f8323f8d9ec5f01f8875529d4265c45`
(PR #1 merge), clean worktree. The previously checked-out branch was
`feature/001-build-and-ci`, HEAD `28412deccaaf09fd80495d000963b41cd2fe51cd`.
New branch `feature/002-orb-native-qualification` starts at the actual main.
Core pin and package version are unchanged; no API expansion or matching work.

### Gate 0: corrected-code post-merge Windows

[Run 37172139283](https://github.com/zackboll/opencv_features_ada/actions/runs/37172139283)
completed **success** at the starting merge SHA (job 111347089731).
Native OpenCV **5.0.0 / features**, MSYS2 package `mingw-w64-x86_64-opencv 5.0.0-5`.
Selected driver was MSYS2's `mingw64/bin/g++.exe` under Alire's MSYS2 cache,
package `mingw-w64-x86_64-gcc 16.2.0-4`, not GNAT's C++ driver.
Historical suite: **20 registered, 20 executed, 20 successful, 0 failed
assertions, 0 unexpected errors**. Features DLL and `.dll.a` existence checks
passed, all three configured native Features/Core/Core-shim import-library
existence checks passed, and PE imports show `libopencv_features-500.dll`
and `libopencv_core_shim.dll`. Thus actual Core shim import linkage was verified.
No rerun/correction was needed; Windows remains exclusively main-push-only.
This is a PR #1 baseline, not Windows execution of Task 002's new tests.

### Source-derived guarantees versus binding validation

Reviewed official 4.1.0/4.10.0/5.0.0 paths and peeled commits are recorded in
`orb-source-review.md` and `source-provenance.json`, including content hashes.
Acceptance bounds remain conservative and unchanged. The review covers both
doubling expressions, the Harris first-level-target-times-eight reserve,
image-derived candidate/count bounds despite response ties, and local/global
pyramid offsets. Existing nonbinary-mask documentation is **confirmed**:
4.1/4.10 all-1 permits level zero only; 5.0 normalizes inside the called override.
The expanded mask case checks these version-aware properties and mixed stripes.

Four new AUnit registrations bring the inventory to **24**. Raw tests use real
Core callback handles for wrong schema/geometry and successful extraction/export.
Compiler-derived C sizeof/alignment/all offsets are compared with the actual
Ada C_Keypoint attributes; C writes a record which Ada checks field-by-field.
The compiled result agrees: size 28, alignment 4, offsets 0/4/8/12/16/20/24.
No public C types, copied bridge, or fabricated wrapper is introduced.

Linux's additional C++ boundary driver calls Core's authoritative C factories,
including a real external view to test invalid output rejection. Native result
lifetime after detector destruction and descriptor lifetime after result destruction
are exercised. Dedicated test-only macro builds inject invalid_argument,
cv::Exception, bad_alloc, std::exception and unknown exceptions; publication-stage
checks verify initialized outputs and cleanup. Production symbol inspection rejects
fault controls. This is **exception fault injection, not real allocator exhaustion**;
upstream allocator exhaustion and exhaustive allocation points remain unqualified.
No deterministic safe ordinary input native-exception trigger was found after preflight.

### Local empirical results

Linux x86_64; native OpenCV **4.10.0 / features2d**; Alire 2.1.1;
GNAT/GCC selected by Alire **16.1.0**, GPRbuild 26.0.1; host Debian g++ 14.2.0.

| Check | Observed result |
| --- | --- |
| repository checker | PASS: 10 ABI declarations/imports, 24 registrations, source ownership/topology |
| configuration/static Python suite | PASS: 20 executed/successful, 0 failures/errors |
| C11 header and C++17 profile helper | PASS: two executables; complete offsets, exact feature rejection boundary, compiled maximum-target float distribution |
| shell syntax / diff whitespace | PASS |
| `alr -n build`; `alr -n -C tests build` | PASS |
| explicit native AUnit run; `alr test` | PASS each: 24 registered / 24 executed / 24 successful / 0 failed assertions / 0 unexpected errors |
| ordinary raw C++ boundary / dedicated fault variant | PASS both, real Core factory/resolver path |
| example build/run | PASS: 393 points / 393 descriptor rows, HAMMING |
| `alr -n exec -- sh scripts/run_sanitizers.sh` | PASS production-source and dedicated fault variants; ASan incl. leak detection and UBSan; CPU-only |

ASan/UBSan command uses `-g -O1 -fsanitize=address,undefined
-fno-omit-frame-pointer -std=c++17 -Wall -Wextra -Wpedantic -Werror` on actual
`cpp/opencv_features_shim.cpp` plus `tests/cpp/native_boundary.cpp`, linked to
the resolved Core shim and pkg-config's OpenCV. Run with
`ASAN_OPTIONS=detect_leaks=1:halt_on_error=1` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. Neither OpenCV nor the
entire Core/dependency graph is rebuilt with these flags; no such claim is made.

### Preserved host-runtime finding and minimization

Initial default-OpenCL instrumented production-source run exited 1 with
LeakSanitizer **9724 bytes / 173 allocations** in AMD HSA/COMGR/LLVM/OpenCL
initialization. A direct upstream-only reproducer, `tests/cpp/upstream_orb_probe.cpp`,
compiled inside the same Alire GCC 16.1 environment with the flags above and
`$(pkg-config --cflags --libs opencv4)`, reproduces exactly the same summary
without Features or Core bindings. Its textured fixture is required: a blank
result does not reach the same native runtime initialization. The equivalent
upstream CPU-only run (`probe cpu`) exits 0; Features CPU-only runs also exit 0.
Host g++14's initial blank probe did not reproduce; it is not contrary binding evidence.
Stacks identify `libhsa-runtime64.so.1`, `libamdocl64.so`, `libamd_comgr.so.2`,
`libLLVM-17.so.1`; the issue is classified as an optional host ICD/runtime finding,
not a demonstrated binding leak.
Original full diagnostics were preserved during
the task; a durable minimized stack/command record is in
`host-opencl-sanitizer-finding.md`. The sanitizer driver explicitly disables OpenCL **in test main only**,
with leak detection still enabled. No suppression or production global change.
GPU/default-ICD cleanliness remains outside this CPU-only qualification.

### Remote qualification gate

Remote conclusions are not implied by the local results above. The Task 002
PR validation record reports the exact reviewed/pushed SHA, once-dispatched manual
matrix run ID, per-target registered/executed/successful counts, and PR job results.
See the [Task 002 branch's Actions runs](https://github.com/zackboll/opencv_features_ada/actions?query=branch%3Afeature%2F002-orb-native-qualification)
for the immutable logs; this source record deliberately does not predict CI success.
Manual workflow remains manual-only, now executing
native AUnit/mask/layout/raw boundary and actual-shim sanitizers for each target.
Installed/clean-consumer relocation/linkage remains Task 001 work; real allocator
exhaustion and full dependency/GPU sanitizer coverage are explicit limitations.
No formal proof, timing bound, navigation/matching accuracy, complete OpenCV safety
or release readiness is claimed.

## Task 001 build/CI tranche

Starting repository: `zackboll/opencv_features_ada`, clean `main` and fetched
`origin/main` at `43a92f040e496278c214db57e2a951638fafe79d`
(`bootstrap features repo`). Branch: `feature/001-build-and-ci`. Core remains
pinned to `7956981a7881ce9121115f8cb65909aeb9edc439` in all three roots.

Baseline Actions run #1, ID `37170492545`: repository-checks passed; Linux
and macOS failed because `.Internal.C_API` was declared a private child.
Its callers are Features and ORB bodies, not descendants of Internal. Both
Internal declarations now use ordinary packages under `src/internal`, as in
Imgproc; C imports remain confined to implementation packages.

The immediate production build passed. Subsequent test/example builds exposed
warning-as-error failures in fixture code: immutable detector/result declarations
needed `constant`; the checkerboard parity modulus now has a descriptive named
constant instead of a suspicious literal `mod 2`. Pixel arithmetic and all
assertions are unchanged. The repository checker also incorrectly treated
Alire's fetched Core bridge as vendoring; it now prunes dependency caches while
still rejecting repository-source copies, with a dedicated regression fixture.
No compiler warnings, validation checks, ownership rules or Core pins were removed.

Local environment: Linux x86_64, Alire 2.1.1, GNAT native 16.1.0,
GPRbuild crate 26.0.1 (banner 26.0.0), Python 3.13.5, native OpenCV
4.10.0 / features2d. The host G++ is Debian 14.2.0; inside `alr exec`, the
Linux `g++` driver resolves to GNAT-FSF-builds 16.1.0 and links libstdc++.
macOS/Windows retain their explicit non-GNAT native compiler selection.

| Exact local command | Observed result |
| --- | --- |
| `alr -n build` | PASS: production Ada/C++ compilation and libraries |
| `alr -n -C tests build` | PASS: native AUnit executable linked against pinned Core |
| `alr -n -C tests exec -- sh ../scripts/run_native.sh bin/run_tests` | PASS: 20 registered, 20 executed, 20 passed; 0 failed assertions, 0 unexpected errors |
| `alr test` | PASS: root test action repeats production/test build and native suite; 20 executed, 20 passed |
| `alr -n -C examples build` | PASS |
| `alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic` | PASS: OpenCV 4.10.0 / features2d, 393 keypoints, 393 descriptor rows, HAMMING; no files/GUI/camera/Imgproc Ada dependency |
| `python3 scripts/check_repository.py` | PASS, including CI topology and 20 registrations |
| `python3 -m unittest discover -s tests/configuration -v` | PASS: 19 tests (9 existing configuration + 10 source-ownership/topology regressions) |
| `sh scripts/run_profile_tests.sh` | PASS: preserved C11 ABI header/layout and C++17 profile tests |
| `for script in scripts/*.sh; do sh -n "$script"; done` | PASS: all five scripts |
| `git diff --check` | PASS |

PR CI: repository-checks, Linux, macOS. Post-merge Windows is in
`windows-post-merge.yml`, triggered only by pushes to main. The separate
OpenCV compatibility workflow remains manual-only and was not dispatched.
Corrected-code PR run [`37171617629`](https://github.com/zackboll/opencv_features_ada/actions/runs/37171617629)
on commit `1dedf5f16353dc65cdfa6bd6bdbff90f4fad6bd0` completed successfully:

| PR job | Actual result |
| --- | --- |
| repository-checks | PASS: checker, 19 Python tests, C/C++ profile tests, shell syntax, whitespace |
| linux (Ubuntu 24.04) | PASS: production build, AUnit 20 registered / 20 executed / 20 passed, synthetic example 393 paired rows; OpenCV 4.6.0 / features2d |
| macos (macOS 14 arm64) | PASS: production build, AUnit 20 registered / 20 executed / 20 passed; OpenCV 5.0.0 / features; Apple-clang/libc++ linkage validation passed, direct native Features and Core shim found, no libstdc++ |

Only those three jobs existed in the PR run; Windows did not run. No corrective
CI rerun or warning/test weakening was needed. This records the tested source
commit; subsequent evidence-documentation commits are checked again by PR CI.
The runner-installed 5.0.0 success is real evidence for that environment, not
qualification of the unrun pinned 4.1/4.10/5.0 compatibility matrix.
Windows is intentionally not a PR check; its corrected-code native qualification
must occur on main after merge, not by a development dispatch.

## Historical ZIP checks executed

Environment: Linux x86_64, GCC/G++ 14.2.0, Python 3.13.5.

| Check | Observed result | What it establishes |
| --- | --- | --- |
| `python3 scripts/check_repository.py` | PASS | Manifests, consistent Core source pin, ten C ABI declarations with matching Ada imports, ownership-layout checks, twenty AUnit registrations |
| `python3 -m unittest discover -s tests/configuration -v` | 9 tests, all PASS | Linux configure-script behavior under mocked pkg-config metadata: OpenCV 4/5 selection, bridge discovery, spaced paths, legacy include metadata, and missing/unsupported inputs |
| `sh -n scripts/*.sh` applied individually | All five scripts PASS | POSIX shell syntax only |
| `sh scripts/run_profile_tests.sh` | PASS | C11 header compilation/layout assertions and C++17 parameter/layout-boundary tests; warnings treated as errors |
| Same C++ profile test built with `-fsanitize=address,undefined -fno-omit-frame-pointer` | PASS, no diagnostics | Arithmetic-helper execution only; **not** the production shim or native ORB |
| All TOML, JSON, Python sources, and both workflow YAML files parsed | PASS | Syntax/parser acceptance, not Alire or GitHub Actions execution |
| Source whitespace and ZIP integrity/path checks | PASS | Text-only repository package, no unexpected binary/build artifacts, no unsafe archive paths |
| Checks repeated from extracted ZIP | PASS | Repository checker, nine configuration tests, shell syntax, C/C++ standalone tests |

The configuration tests use controlled fixtures rather than real native
OpenCV. The helper sanitizer run cannot reveal defects inside `cv::ORB`.
YAML parsing does not validate every GitHub Actions expression or permission.
The repository checker compares ABI names, not compiler-derived Ada/C
calling conventions or full binary ABI layout.

## Historical bootstrap checks not executed

The original artifact environment had no `alr`, `gnat`, `gnatmake`, or `gprbuild` on
PATH, and no pkg-config metadata for `opencv5`, `opencv4`, or `opencv`.
Consequently, at artifact creation none of the following was claimed as passing
(the build/CI tranche evidence above supersedes its local build/test entries):

- Ada compilation or binding/linking against the pinned Core checkout.
- Compilation of the production C++ shim against native OpenCV.
- Any of the **20 registered AUnit tests** or the synthetic Ada example.
- Real native ORB sanitizer tests, raw-ABI robustness tests, or performance tests.
- Linux/macOS/Windows Actions jobs or the OpenCV compatibility matrix.
- A clean installed-consumer test through Alire/GPRinstall.

The sources have been inspected and static consistency checks performed,
but native compile errors, warning-as-error failures, runtime integration
issues, and platform-specific link problems can still remain. Run Task 001
before adding matching features or treating this as a tested release.

## Historical bootstrap source-review limits (superseded by Task 002 above)

Selected live files from Core, Imgproc, and Geometry informed the design;
`source-provenance.json` records their paths and blob IDs. This is not an
assertion that every file in those repositories was reviewed.

Official OpenCV 4.10.0 and 5.0.0 feature declarations and ORB implementation
files informed the draft profile. Oldest-target 4.1.0 source retrieval was
unsuccessful, and that target remains unqualified. The nonbinary-mask
normalization difference is documented in `orb-contract.md` and requires
native regression coverage. No end-to-end navigation or DTED processing
was implemented or validated.

## First gate

Follow [`tasks/001-validate-bootstrap.md`](tasks/001-validate-bootstrap.md):
record the actual toolchain/Core/OpenCV provenance, build, fix any errors
without weakening warnings, execute the twenty AUnit cases and synthetic
example, add the missing native regression coverage, and verify clean
consumer/CI behavior. Stop at the review gate; do not automatically publish.

At the end of Task 001's build/CI tranche, Task 001 was **not complete**.
The then-remaining qualification included oldest-target
4.1 source review and cross-version ORB/arithmetic review; real-handle raw C ABI
negative/fault-injection and C/Ada layout probes; production/native ASan/UBSan;
nonbinary-mask regression; pinned OpenCV 4.1/4.10/5.0 native matrix; Windows
corrected-code post-merge execution; installed/clean-consumer relocation and
linkage qualification. No formal proof, timing/navigation accuracy, complete
cross-version safety or release readiness is claimed.
