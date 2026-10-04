# Bootstrap validation record

## Status

**Build/CI tranche qualified locally; not a fully qualified binding or release.**
Historical ZIP checks below are distinct from actual build/test evidence.
No native result is implied by the existence of a test or workflow.

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
At this local-validation checkpoint, corrected-code PR CI has not yet run.
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

## Source-review limits

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

Task 001 is **not complete**. Remaining qualification includes oldest-target
4.1 source review and cross-version ORB/arithmetic review; real-handle raw C ABI
negative/fault-injection and C/Ada layout probes; production/native ASan/UBSan;
nonbinary-mask regression; pinned OpenCV 4.1/4.10/5.0 native matrix; Windows
corrected-code post-merge execution; installed/clean-consumer relocation and
linkage qualification. No formal proof, timing/navigation accuracy, complete
cross-version safety or release readiness is claimed.
