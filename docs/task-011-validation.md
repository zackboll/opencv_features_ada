# Task 011 — research-stage validation

## Task 011-R1 update

The [R1 certificate](orb-pyramid-levels-arithmetic-r1.md) now proves every
admitted N conditionally on stated FP/pow/cvRound premises. The exact rational
checker passes. Its derived allowance is E=8, uniform Harris reserve bound
1,986,422,381, partial sum bound 1,986,422,380, and doubled target bound
2,147,483,646. Apple/Windows numerical qualification remains missing, so the
final full-profile disposition remains SAFETY_GATE_NOT_ESTABLISHED.

R1 final checks also passed: reproducible runner, shell syntax, repository
static checks (17 ABI exports), 76/76 configuration tests, and profile/header/
layout checks. No new AUnit execution is claimed. Both Task 008B worktrees
remain clean at the protected SHA; all retained Task 010 documentation hashes
verify. The local research commit contains only the seven research files;
raw run logs are indexed by `docs/research/orb_levels_evidence.json`.

Eighteen Linux probe configurations passed: native OpenCV 4.1/4.10/5.0,
g++ 14.2/clang++ 19.1.7, each at O0/O2/O3. Each checks 151,547 distinct targets
at all eight levels and runs eight actual upstream extractions. Exact rational
comparison of all reported pow outputs passed. This is not a production
Features configurable-level suite or a macOS/Windows qualification claim.

Added research sources: `docs/research/orb_levels_certificate.py`,
`docs/research/orb_levels_probe.cpp`, `docs/research/run_orb_levels_probe.sh`.
Native headers, original documents and diagnostics are preserved externally
under the existing evidence directory's r1 subdirectory. No production file,
manifest, dependency pin, ABI or workflow was edited. R1 authorizes a local
research-only commit; the pre-R1 untracked/no-commit state below is historical.

Disposition: **SAFETY_GATE_NOT_ESTABLISHED**. Stop before production changes
or an implementation PR. See [source review](orb-pyramid-levels-source-review.md)
for the missing all-target floating-error/rounding qualification for levels 2–8.
This is an evidence gap, not a reproduced native defect.

## Repository reconciliation

- Fetched origin/main: `495e385f91022735d5c52ba766f8d25164c7a900`, matching
  the requested starting SHA.
- Isolated worktree: `features-011`; branch: `feature/011-orb-pyramid-levels`.
- No open Features PRs were returned at reconciliation.
- HEAD remains the starting SHA. No commit, push, PR, workflow dispatch,
  merge, tag, release, or version/dependency change.
- Only the two Task 011 research/validation documents were added. They remain
  untracked for handoff; the worktree is therefore deliberately **not clean**.

## Actual local baseline checks

Environment: Linux, g++ 14.2.0 (Debian 14.2.0-19), pkg-config OpenCV 4.10.0.
These results exercise the **unchanged eight-level implementation**, not a
configurable-level implementation:

| Command | Result |
| --- | --- |
| `alr -n build` | Passed |
| `python3 scripts/check_repository.py` | Passed: 17 ABI declarations/imports, 67 AUnit registrations |
| `python3 -m unittest discover -s tests/configuration -v` | 76 executed, 76 passed |
| `sh scripts/run_profile_tests.sh` | Passed C11 header, C++17 profile/header and layout checks |
| `sh scripts/test.sh` | Passed build, 67 AUnit executed/67 passed, zero failed assertions/unexpected errors |
| Installed-link metadata regressions within test script | 2 executed, 2 passed |
| Native production/fault-injection boundaries within test script | Passed, real Features shim and Core bridge |
| `alr -n exec -- sh scripts/run_sanitizers.sh` | Passed production/fault-injection ASan/UBSan runs |
| `sh -n` for every script | Passed |
| `git diff --check` | Passed for tracked changes; added documents also manually reviewed |

Sanitizers instrument the actual Features shim, **not** Core or native OpenCV.
The standalone distribution probe is arithmetic/compiler evidence only.

All three required immutable ORB source files were reviewed and hashed.
Native 4.1/5.0 execution, six GPRinstall regressions, examples, three-mode
consumer qualification, and hosted Linux/macOS exact-head CI were **not run
for Task 011**. No Windows qualification is claimed. Earlier Task 008B evidence
is not reused as configurable-level certification.

## Compatibility and handoff

The public Configuration and existing Create remain unchanged; the production
detector still uses eight levels. No new constructor/getter, dynamic octave
validation, matching change, or additive C export exists. C ABI remains 17
exports rather than the planned 18; no public C layout or Core ABI changed.
The supported configurable range has **not** been admitted.

The Task 008B candidate branch and both protected worktree HEADs remain
`670643d36f6fdcb0e96fcc5ee9ee702dc7a2cad3`; both protected worktrees are clean.
Task 010 HEAD remains `1c8860d7b491e17782ea260dab078f3f555e41d4`. Its original
untracked research inventory is unchanged; SHA-256 verification of every file
under its docs directory passed after this work.

Raw source files, provenance JSON, distribution probe, build/configuration/
native/sanitizer logs and Task 010 preservation hashes are retained in a
separate sibling `features-011-evidence` directory, outside committed source.
There is no final implementation commit, remote/PR-head equality, PR URL,
or REVIEW_GATE_READY claim. Resume with the unresolved safety argument before
implementing Gates 2–11.
