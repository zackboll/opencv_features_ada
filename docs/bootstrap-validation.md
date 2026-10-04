# Bootstrap validation record

## Status

**Source bootstrap; not a qualified native binding or release.** This record
separates checks actually executed while creating the ZIP from checks that
require the user's Ada/OpenCV environment. No native test result is implied
by the existence of a test or workflow.

## Checks executed

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

## Not executed

The artifact environment has no `alr`, `gnat`, `gnatmake`, or `gprbuild` on
PATH, and no pkg-config metadata for `opencv5`, `opencv4`, or `opencv`.
Consequently, none of the following has been claimed as passing:

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
