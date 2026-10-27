# FEATURES-API-020 validation

## Identity and scope

Started 2026-10-26 from freshly fetched `origin/main`:
`ef1e26e6557bf089cbd9c82e7a6879964f96ad0e`, tree
`1402655f104b5620e3ba39610eca6e0969389f99`. Clean worktree initially on
`ci/019-windows-alire-environment`; created
`feature/020-orb-scale-space-compatibility` from verified main, not that branch.
The approved release commit `e6d977f0bba02c526920834ef6e88905366ed1b9`
still has tree `0265f6e39de174722cfe8ff59d7663dddbcf8cbd`.
No Alire manifest or Windows workflow changes; no release/tag/index action.
Final head/tree and hosted execution URLs are recorded in the PR/handoff
rather than making a self-referential commit identity claim here.

## API and bounds

Adds `ORB.Pyramid_Configuration`, `Create (Configuration, Pyramid_Configuration)`
and `Pyramid_Parameters`. Existing four-field aggregates/default Create remain
unchanged. Both configuration accessors reject unready/closed detectors;
no setters. Limited detector/result ownership and finalization remain unchanged.
Only native addition:

```c
opencv_features_status opencv_features_orb_create_profiled(
    int32_t maximum_features, int32_t tuple, int32_t score, int32_t fast_threshold,
    float scale_factor, int32_t levels, opencv_features_orb_handle **out_handle);
```

All 17 legacy header signatures were compared byte-for-byte by operation name
against fetched main and preserved. The C header, C++ implementation and Ada
imports inventory now has 18 operations. Both factories share guarded creation.
Finite scale 1.1f..2.0f, levels 2..16. Nonlegacy target cap M/(2L); legacy
(1.2f,8) retains M/2. W=align_up(cols+64,16), H=L*(rows+64), WH<=M;
every level must be strictly above 0.5 before rounding in both reviewed native
dimension calculations. See the separate [source derivation](orb-source-review.md)
and provenance hashes. These are conservative acceptance limits, not native
maxima or available-memory guarantees. Some extreme scale/level combinations
have no admitted square geometry under the envelope.

## Local executed evidence

Linux x86_64, Debian g++ **14.2.0-19**, GNAT **16.1.0**, GPRbuild
**26.0.0 (2026-04-15)**, Alire **2.1.1**, indexed Core **0.5.0**,
pkg-config OpenCV **4.10.0** / features2d. System native libraries are not
fully sanitizer-instrumented. No OpenCV build is substituted by a mock.

Before edits: repository checks, configuration discovery (137 tests, 136 passed /
one opt-in skip), shell syntax, fixed-profile compiler tests, native build,
**67 registered/executed/passed AUnit**, two installed-link tests and both real
production/fault raw boundary variants passed. Baseline is not evidence for
the changed implementation on other native versions.

After implementation:

| Command/campaign | Observed result |
| --- | --- |
| `python3 scripts/check_repository.py` | Pass: 18 declarations/imports, 75 AUnit registrations, dependency/ownership/CI topology |
| `python3 -m unittest discover -s tests/configuration -v` | 137 discovered/executed, 136 pass, one real-Alire opt-in skipped in ordinary invocation |
| Separate `FEATURES_REAL_ALIRE_TEST=1` discovery of `test_alire_environment_real.py` inside Alire toolchain environment | 1/1 pass; combined configuration inventory has all 137 cases exercised successfully |
| `sh -n` on every script | Pass |
| `sh scripts/run_profile_tests.sh` | C11 ABI layout + C++17 fixed/configured target/distribution/layout boundary checks pass |
| `alr -n build` / `sh scripts/test.sh` | Build pass with warnings as errors; **75 registered, 75 executed, 75 passed AUnit**, zero assertions/errors |
| installed-link metadata regressions | 2/2 pass |
| `alr -n exec -- python3 tests/test_external_shim_install.py -v` | 6/6 GPRinstall regressions pass |
| `alr -n exec -- sh scripts/run_sanitizers.sh native` | Real Features/Core-backed production and fault variants pass |
| `alr -n exec -- sh scripts/run_sanitizers.sh` | Actual Features shim ASan+UBSan, production and fault variants pass, leak detection enabled, no suppressions |
| `alr -n -C examples build`, run all three examples | Both existing examples and `orb_pyramid_synthetic` pass |
| `sh scripts/validate_clean_consumer.sh` | Source, GPRinstalled and moved-prefix consumers pass, source lookup sanitized, new pyramid API invoked |
| GNATdoc generation + independent regeneration | Strict pass, byte-identical sites and logs |
| Official enhancer v0.1.0 fresh verified installation/integration | Pass; idempotent/fresh enhancement identical, native identities retained |
| Documentation discovery with native/enhanced/end-to-end environment | **104/104 pass**, including mutation and regeneration checks |
| Chromium 156.0.8078.4 / Playwright 1.64.1 | **64/64** enhanced-browser and **199/199** project-prefix Pages assertions pass |
| `git diff --check` | Pass |

Eight new AUnit cases preserve all prior 67 and cover levels 2/4/8/12/16,
scales 1.1/1.2/1.5/2, defaults/round trips, differing octave distributions,
descriptor pairing, WTA2/3/4, matching/correspondences, masks/empties/ROI,
preserved input, result lifetime, invalid profiles/upper-level size and closed
access. Raw drivers cover nonfinite/out-of-range scales, raw level extrema,
null/initialized outputs, exact target cap/cap+1, and same-build native ORB
reference values/order/descriptors. Fault injection covers all five exception
categories at creation and extraction stages 2/3/4. This is not allocator
exhaustion or exhaustive vendor path qualification.

Documentation: **41 public declarations**, **137/137 meaningful documented
elements**, **zero warnings**. Original 38 declarations and anchors preserved;
three additions captured only from source and successful real generation.
Official enhancer guide links use explicit overload selection for Create.
Updated site census is 18 files / 13 HTML pages / 258 resolved references;
the release-comparison regression's exact census changed accordingly, without
weakening its byte-identity or version-only assertions. Historical documentation
records remain historical, not current qualification evidence.

## Diagnostics corrected during development

Warnings-as-errors caught an Ada iterator syntax mistake/obsolete aggregate and
a synthetic parity literal warning; corrected using repository conventions.
Strict documentation caught the three intentionally added declarations/anchors
and overloaded Create guide links; inventories and explicit overload links were
updated, not bypassed. A reused enhancer environment failed launcher-integrity
verification, so a fresh official hash-verified installation was used. A stale
248-reference release-comparison fixture was reproduced on the new 258-reference
site and updated. Missing end-to-end environment variables in an early test
invocation were corrected; final full documentation discovery passes.

## Six-version qualification and review gate

The manual-only matrix now selects authentic fixed tags 4.1.0, 4.4.0, 4.6.0,
4.8.0, 4.10.0 and 5.0.0, verifies each independently recorded upstream commit,
and builds real core/imgproc/features2d (4.x) or features (5.0). Every entry
runs the full AUnit suite including configured tests, production/fault native
boundaries, actual-shim sanitizers and compiler-backed profile checks.
At this local checkpoint **all six pinned source-build outcomes remain pending**;
the system 4.10.0 run is not a replacement for the pinned hosted build.
The PR/handoff records actual dispatch head and run outcomes. No claim about
every intermediate minor, full cross-version safety or navigation accuracy.

Existing main Windows acceptance remains blocked: run
[40433424002](https://github.com/zackboll/opencv_features_ada/actions/runs/40433424002)
on starting main failed at **Regress real Alire environment hashing (not native
qualification)** and diagnostic preservation. This feature task does not
correct, weaken or bypass that separate workflow. Do not merge while mandatory
Windows acceptance is unresolved. Leave the feature PR open with auto-merge off.