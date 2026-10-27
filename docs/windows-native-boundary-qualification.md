# FEATURES-CI-016 — Windows native-boundary qualification

## FEATURES-CI-019 — one execution environment

### Investigation recorded before implementation

Initial worktree: clean, branch `ci/018-windows-core-provenance`, HEAD
`8db6b23de18976e89853e23f69e5735388be43de`. Freshly fetched main and the new
`ci/019-windows-alire-environment` branch start at
`915ea1229085c7ae1eec5887f430d8eab568e1db` (tree
`bd7eae9b989b690f47f106a89e328b9a5c30b9e8`). Approved release remains
`e6d977f0bba02c526920834ef6e88905366ed1b9`, tree
`0265f6e39de174722cfe8ff59d7663dddbcf8cbd`.

The complete [Windows job 121373932959](https://github.com/zackboll/opencv_features_ada/actions/runs/40261253660/job/121373932959)
and [artifact 12624238928](https://github.com/zackboll/opencv_features_ada/actions/runs/40261253660/artifacts/12624238928)
were downloaded and inspected. AUnit completed 67/67; boundary compilation
never began and immutable release qualification was skipped. The artifact has
only campaign/failure logs, not hash-input files, DLLs, link configuration or
qualification JSON. It cannot establish their historical byte identities.

The outer `alr exec` supplied Core build
`398c0561ce064e26c796348909430c1c8069ef811ca04123885f5316eaa20876`.
The resolver's nested `alr exec` tried to assign
`0dce2c62a74a892bcb1251df1da3b1fc6d723e71761b2f4b838398ba0f72e0ee`
to the already set `OPENCV_CORE_ALIRE_PREFIX`. Both paths select the same
`opencv_core_0.5.0_f8aef00c` deployment: a build hash is not a source revision.
The build log also records bridge/configuration build
`e3ffe32c14157e6d9acc22dc628d869ef54e2551711b7d7f090b372b15d9a53c`.
Simply removing the nested call must not make that different build acceptable.

Alire 2.1.1 source `fa9a1a9971d159f8cb2b8007dbb73e9e029fc109`
explains the mechanism. `Builds.Hashes.Compute` loads an environment with
`For_Hashing => True`: resource paths use relative deployment names, but
`Environment.Compile` starts with the process's existing environment.
`Add_Environment` hashes the effective values of manifest-modified variables.
Indexed Core 0.5.0 (public Git origin, immutable
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`) and Features both prepend
`${CRATE_ROOT}/lib` to PATH on MSYS2. The exported outer environment adds
absolute build/toolchain paths. Hashing again inside that environment therefore
has additional PATH inputs, producing a different digest without changing the
selected release. Windows startup also unconditionally prepends MSYS2's usr/bin;
shell/native transitions can change PATH representation. `Exec.Execute` exports
again and `Environment.Compile(Check_Conflicts => True)` rejects the different
resource prefix before starting the Python probe. This is not evidence of an
inconsistent dependency solution, nor a supported way to query inherited values.

A real Alire 2.1.1 local-index experiment, with both crates declaring precisely
the PATH prepend above, reproduced this conflict on Linux without mocked
subprocesses. The outer prefix matched the recorded dependency hash; nested
exec computed another hash and did not launch its child. Linux's ordinary Core
metadata omits the MSYS2 PATH action, explaining why CI-018's real Linux probe
missed the regression. Exact historical digests cannot be recomputed from the
Windows artifact because it does not retain the historical PATH/hash inputs.

### Correction and acceptance contract

The resolver reads both inherited absolute resource prefixes. Only metadata
queries (`show` for the exact selected version and `version`, both structured
JSON) invoke Alire; neither exports an execution environment. All CI-018
lock/index/origin/immutable commit, stable version, unpinned dependency, workspace,
cache layout, sorted NUL-terminated Core SHA-256 recomputation, Features dependency
hash, vault manifest and bridge-header checks remain. Generated configuration
still must reference this exact Core bridge/import library, with its actual DLL
present. A different valid-looking cache directory is not an acceptable substitute.

Removing only the nested query is insufficient: the failed build's bridge and
later outer prefix already differed. The shell launcher now calls
`prepare_windows_boundary.py` **outside** Alire. That native Python process
runs build and exec as siblings with an identical unmodified parent environment,
then exec invokes the native Python harness directly, not through an MSYS shell.
This avoids extra PATH transformations between selection and verification and
regenerates configuration for the same selected build. The launcher rejects
already inherited Core/Features prefixes instead of clearing them. It removes
old report/variant evidence before preparation; every subprocess failure remains
fatal. No provenance error is suppressed and no alternate build is selected.

The immutable campaign still clones independently, verifies the exact original
commit/tree before building, and uses the newer harness externally without any
overlay or source/manifest edit. Both native variants, symbol checks, report and
final commit/tree marker remain mandatory. Trigger routing is unchanged:
Windows remains main-only, not PR CI. A real-tool environment regression is added
to that same post-merge workflow, explicitly separate from native qualification.

### Local validation

- Repository/profile/layout checks, all shell syntax and whitespace checks: PASS.
- **137/137 configuration tests**, no skips with `FEATURES_REAL_ALIRE_TEST=1`:
  50 harness/policy fixtures plus one real-Alire environment regression. This
  includes all CI-018 negatives, inherited/selected mismatch and link-prefix
  substitution rejection, preparation failures and stale-report cleanup.
- Real resolver with actual indexed Core 0.5.0, full origin commit above, actual
  lock/vault/build/bridge: PASS without nested exec. Local build digest
  `59c9d1a9a87e5b0e5373d4b44fa3558506b5db4669aa1b218555afed90327689`.
- Linux native: **67 registered / 67 executed / 67 passed AUnit**, zero failures
  or errors; ordinary production/fault and both ASan/UBSan variants: PASS.
- Both examples, six external-shim installation and two installed-link metadata
  regressions, source/installed/relocated consumers and active path audits: PASS.
  The existing unused `Common_Cxx_Switches` include remains non-load-bearing;
  no auditor acceptance rule changed.
- GNATdoc 26.0.0: **127/127** documented/rendered, zero gaps/warnings, second
  independent generation/site/log identical. Official Enhancer v0.1.0 verified
  installation and deterministic/idempotent enhancement: PASS. **104/104**
  documentation tests, no skips, including real generation/security mutations.
  Pages: 18 files / 13 pages / 248 references: PASS.
- Official enhancer compatibility preflight: zero failures.
- Independent detached checkout of the exact approved release commit/tree:
  Linux build, both ordinary native variants and both ASan/UBSan variants PASS;
  strict Git cleanliness unchanged afterward. This supplemental Linux run is
  not either mandatory Windows campaign and emits no Windows release marker.
- Chromium 156.0.8078.4 / Playwright 1.64.1: **64/64** root API, **199/199**
  project-prefix and **64/64** prefix API assertions: PASS. Local Pages archive
  byte-identical; hosted uploaded-artifact verification remains a CI gate.

Local tools: Alire 2.1.1 (source SHA above), GNAT 16.1.0, GPRbuild crate 26.0.1
(binary 26.0.0), Alire-environment g++ 16.1.0, host g++ 14.2.0, OpenCV 4.10.0 /
features2d. GNAT version probing through the existing generation script emits
Alire's broken-pipe diagnostic after grep exits early; the generation exits zero,
both sites/logs compare identically and strict checks pass. No tool/script was
changed to hide that diagnostic.

Final tested/pushed/PR SHA equality and hosted run URLs belong in the PR record
to avoid self-reference. Exact-final-head repository, Linux, macOS, sanitizer and
documentation CI must pass before review readiness. No local result here is real
Windows qualification. Independent review/merge and the **first Windows main
run** remain outstanding: require actual compile/link/execution/symbol logs,
qualification JSON and both native markers for corrected main and independently
for the original immutable release, plus exactly
`WINDOWS_RELEASE_SOURCE_QUALIFIED e6d977f0bba02c526920834ef6e88905366ed1b9 0265f6e39de174722cfe8ff59d7663dddbcf8cbd`.
FEATURES-REL-015 remains blocked. No tag, release or Alire index submission.

## FEATURES-CI-018 — selected Core provenance, separate build and source roots

Starting worktree was clean on `ci/017-windows-cleanliness-correction`, HEAD
`f30ce8c08b7b5585d42b0b55ef342befad6e5b5f`. After a fresh fetch the requested
branch `ci/018-windows-core-provenance` starts from main
`c5a372d1ec802dcd91aaf92972921f122b92f57c`, tree
`37199d381a1ced2658892142d5b92fc1dd9928c4`. The immutable release commit/tree
in this document remains unchanged; no release source is patched.

### Observed failure and metadata authority

[Run 39900729214](https://github.com/zackboll/opencv_features_ada/actions/runs/39900729214),
[job 120241451642](https://github.com/zackboll/opencv_features_ada/actions/runs/39900729214/job/120241451642),
[artifact 12478838018](https://github.com/zackboll/opencv_features_ada/actions/runs/39900729214/artifacts/12478838018)
were retrieved through GitHub's API and the actual logs inspected. The artifact
contains only campaign/failure logs. The exact failing relative location is
`cache/builds/opencv_core_0.5.0_f8aef00c/398c0561ce064e26c796348909430c1c8069ef811ca04123885f5316eaa20876/alire.toml`
under the runner's Alire cache. It fails before raw boundary compilation;
the immutable-release step is skipped. AUnit passed separately, but neither
raw Windows campaign is qualified by that run.

Live local probes used Alire **2.1.1**, source commit
`fa9a1a9971d159f8cb2b8007dbb73e9e029fc109`. Built-in help and that exact
upstream implementation were inspected, particularly `alire-roots.adb`
(`Release_Base`), `alire-environment-loading.adb`, `alire-builds.adb`,
`alire-releases.adb` (`Deployment_Folder`) and `alire-builds-hashes.adb`.
Observed formats, also used by the reduced test fixtures:

```toml
[solution.context]
solved = true
[[solution.state]]
crate = "opencv_core"
fulfilment = "solved"
pinned = false
transitivity = "direct"
versions = "~0.5.0"
[solution.state.release]
name = "opencv_core"
version = "0.5.0"
[solution.state.release.origin]
commit = "f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f"
url = "git+https://github.com/zackboll/opencv_core_ada.git"
```

`alr -n --format=JSON show opencv_core=0.5.0` returns a release object with
`name`, `version` and `origin` (plus actions, dependencies and other fields).
`alr -n --format=JSON version` returns an array of `{"key": ..., "value": ...}`
rows including `alr version`, `root status`, `root folder`, `build folder` and
`vault folder`. In contrast, `with`, `printenv` and `show --solve` do **not**
support structured output in 2.1.1. Neither pretty solution text nor the build
directory name alone is a provenance authority.

### Resolver contract

1. Parse the selected workspace's lockfile. Require exactly one solved,
   unpinned, direct `opencv_core` under the existing `~0.5.0` constraint. Apply
   the shared stable SemVer validator; reject wrong identity, prereleases,
   incompatible versions, workspace/Git pins and incomplete metadata.
2. Require the exact public Git URL above and a full lowercase 40-hex commit.
   Independently query the index for that **exact selected version**, not latest
   Core. Require identity/version/origin agreement. Extra/unsupported origin
   selectors such as subdirectories fail closed.
3. Require reviewed Alire 2.1.1 structured location metadata for the selected
   workspace. **Corrected by CI-019:** validate the two inherited absolute resource
   prefixes against the selected Core and tested Features checkout without
   re-exporting an already established environment.
4. Use the documented/implementation-reviewed shared layout only:
   `builds/<deployment>/<build-hash>` and `releases/<deployment>`. The deployment
   uses selected version (without SemVer build metadata) and commit prefix;
   these names are consistency checks, not proof. Recompute the SHA-256 of
   Core's sorted, NUL-terminated `alire/build_hash_inputs` entries and require
   Features' recorded `dependency:opencv_core=<version>=<hash>` to match exactly.
   Missing or unrelated environment/cache/hash associations fail.
5. Read only that exact vault source manifest, retaining
   `validate_core_manifest.py`; verify identity/version/origin agreement. The
   build root may lack `alire.toml`; if present, contradictions are rejected.
   Build bridge/C factory headers (and optional include copies) must match the
   source deployment. Existing generated configuration still requires the real
   Core bridge, DLL and exact import library from this build, external MSYS2
   MinGW64 compiler and matching OpenCV imports. No cache recursion, copied
   production bridge or alternate algorithm is introduced.
6. Recheck provenance and strict Features source identity before writing the
   report or either completion marker. Record source/build prefixes, version,
   full origin and build hash in qualification JSON. Preflight failures clear
   stale reports and per-variant execution evidence and propagate nonzero.

The trust boundary is Alire's index/solution/deployment records and the local
build environment, as with the original harness, not adversarial cache
attestation or arbitrary pointer validation. This intentionally supports the
reviewed shared-cache layout; unknown Alire versions/layouts need review,
not a best-effort fallback. No production dependencies change.

### Local qualification and remaining gates

Local Linux: Alire 2.1.1, GNAT/g++ 16.1.0, GPRbuild crate 26.0.1 (binary
26.0.0), OpenCV 4.10.0/features2d, indexed Core 0.5.0 origin
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`. The real resolver was executed
successfully against the actual local lock/index/environment/cache, separately
from the synthetic Windows fixtures.

- Repository checks, **129/129 configuration tests** (43 Windows harness/policy),
  all shell syntax checks and profile/layout helpers: PASS.
- Native build, **67 registered / 67 executed / 67 passed AUnit**, zero assertion
  failures/errors; raw production/fault and both ASan/UBSan variants: PASS.
- Both examples, six external GPRinstall and two installed-link regressions,
  source/installed/relocated consumers and strict path audits: PASS. The existing
  unused `Common_Cxx_Switches` include remains reported as non-load-bearing.
- GNATdoc 26.0.0: **127/127 documented elements**, zero gaps/warnings; independent
  second site/log byte-identical. Official Enhancer v0.1.0 wheel installation,
  integrity verification, deterministic/idempotent enhancement: PASS.
  **104/104 documentation tests**, no skips (including real regeneration and
  installed mutations); Pages 18 files/13 pages/248 references: PASS. The first
  documentation invocation omitted optional site environment variables and
  skipped ten tests; the complete configured rerun passed all 104.
- Official enhancer compatibility preflight: zero failures. Chromium
  156.0.8078.4 / Playwright 1.64.1: 64/64 root API, 199/199 project-prefix and
  64/64 prefix API assertions passed; local Pages tar byte-identical. An initial
  browser attempt picked up an unrelated global alpha Playwright lacking its
  browser; isolated CI-matched 1.64.1 tooling corrected that tooling failure.
  Hosted uploaded-artifact validation is still independent of local-tar evidence.

Production Ada/C++, public API, 17 ABI entries, all Alire manifests, native
boundary driver, Linux sanitizer implementation and Windows trigger policy
remain unchanged. Final commit/tree and hosted URLs/results are recorded in
the PR to avoid a self-referential source commit. Final-head repository,
Linux, macOS, sanitizer and documentation hosted success is required before
`READY_FOR_INDEPENDENT_REVIEW`.

No local Linux fixture constitutes Windows qualification. Leave the PR unmerged,
auto-merge disabled. The first post-merge Windows run must compile/link/check
symbols/execute **both production and fault variants** on corrected main and,
independently, approved release `e6d977f0bba02c526920834ef6e88905366ed1b9`, tree
`0265f6e39de174722cfe8ff59d7663dddbcf8cbd`. Inspect both actual execution logs
and qualification JSON reports, both native PASS markers, and the exact
`WINDOWS_RELEASE_SOURCE_QUALIFIED` commit/tree marker. FEATURES-REL-015 remains
paused: no tag, GitHub Release or Alire index PR is authorized.

## FEATURES-CI-017 — strict Git cleanliness correction

Starting main is `d57a86e805f978840053b0a52a02beb04679233d`, tree
`67935bcc398c50c56c0a0b7cc780946ecb636091`. No overlapping open PR or existing
publication was found. The approved release commit/tree below is unchanged.

[Run 39699379940](https://github.com/zackboll/opencv_features_ada/actions/runs/39699379940),
job `119564604824`, passed step 8 (67/67 AUnit), then failed step 9 before any
boundary compilation: `qualification source must have no tracked edits or
unignored files`. Step 10, the immutable-release campaign, was skipped. Artifact
`12393125026` contains only campaign/failure logs, no qualification JSON, symbol
or execution logs. It cannot qualify either native campaign.

The runner invoked Alire from repository-local `alire_install/bin/alr.exe`.
The exact setup-alire action revision used was
`1ff7d9224297858cc9ecce29b08bc6109f93e49a`; its `src/main.ts` sets
`install_dir = "alire_install"` and extracts the archive there. In a real Git
fixture with the original ignore rules, creating that executable reproduces
`?? alire_install/bin/alr.exe`. Committing only `/alire_install/` restores clean
status. This establishes the false-rejection mechanism, not an exhaustive list
of dirty paths on the historical runner: the old harness discarded those paths.
Any further dirty path must be diagnosed independently, not silently exempted.

Only the corrected harness checkout gains the repository-root ignore rule.
Nested unexpected installations, tracked changes (even under ignored paths),
unexpected files/directories and wrong commit/tree identities remain rejected.
The original immutable release's `.gitignore` is not changed or overlaid. Its
checkout uses the externally installed Alire executable, not a new setup-alire
installation inside that checkout.

Failure diagnostics retain the two-column index/worktree status category and
at most 20 repository-relative path samples, each capped at 240 characters,
plus the omitted-entry count. JSON escaping prevents terminal control output;
no file contents, environment or filesystem inventory is printed. Diagnostics
remain in campaign/failure logs collected by the existing artifact glob.
Source status and identity are checked before and after execution. Both PASS
markers are now withheld until the final integrity check and JSON write succeed.
Stale success JSON is removed before shell setup and Python preflight; previous
variant objects, executables and logs are removed before Python preflight.

Eleven added tests (26 Windows harness/policy tests total) cover actual Git
status/ignore behavior, tracked Ada/C++ changes, unexpected files/directories,
staged/deleted files, bounded escaped diagnostics, CLI nonzero failure/artifact
writes, stale success removal and late source mutation. Original-rule strictness
is fixed by the approved ignore-file digest, so shallow CI checkouts work.
Existing tests continue to require both variants, symbol controls and pinned
independent release checks. These Linux fixtures are not Windows execution.

Local Linux qualification: Alire 2.1.1, GNAT 16.1.0, GPRbuild crate 26.0.1
(binary 26.0.0), Alire-environment g++ 16.1.0, OpenCV 4.10.0/features2d,
indexed Core 0.5.0 origin `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`.
Native build, 67/67 AUnit, both ordinary raw variants, both ASan/UBSan variants,
both examples, six external GPRinstall/two installed-link regressions and all
source/installed/relocated consumers passed. The pre-existing unused
`Common_Cxx_Switches` include is still reported as non-load-bearing; no audit
exception changed. Additional local results:
repository/profile/shell checks passed; **112 configuration tests passed**;
GNATdoc 26.0.0 documented/rendered **127/127**, zero warnings, independent second
generation/site/log byte-identical; official Enhancer v0.1.0 installation and
deterministic/idempotent enhancement passed; **104 documentation tests executed
and passed, no skips**, including native regeneration and installed mutations.
Exact pushed head and hosted results belong in the PR qualification record,
not a self-referential source commit. Local browser tests were not rerun by
CI-017; final-head hosted browser/artifact checks remain required.

Final-head hosted repository/Linux/macOS/sanitizer/documentation success is
required for review readiness. After independent review and eventual merge,
**both actual Windows campaigns and their JSON/symbol/execution evidence remain
mandatory**, including the exact original-source completion marker. Publication
remains blocked. This task does not authorize merging, tagging or publishing.

## Release identity and original gap

The approved **0.1.0** source remains merge commit
`e6d977f0bba02c526920834ef6e88905366ed1b9`, tree
`0265f6e39de174722cfe8ff59d7663dddbcf8cbd`. Fresh main equalled that commit
when this correction began. No release tag exists. During initial local qualification a fresh fetch
observed that it was merged externally into main at
`782e33ef6822887c45e607c5934032d9d856b3ad` (tree
`a505c57ef1eb2f385bd40d6198801bdbaf2d810e`). The initial correction did not
incorporate that PR. FEATURES-CI-016R1 subsequently integrates that fresh main
by normal merge into the existing branch, preserving its official released
GNATdoc Enhancer installation. This merges existing main, not PR #26 itself.
No newer main commit substitutes for the pinned release source.

[Windows run 39540052561](https://github.com/zackboll/opencv_features_ada/actions/runs/39540052561),
[job 119025486968](https://github.com/zackboll/opencv_features_ada/actions/runs/39540052561/job/119025486968),
passed AUnit 67/67, native setup, DLL checks, GPRinstall, all three consumer
modes and audits. Step 8 called `scripts/test.sh`, whose raw-boundary driver
is Linux-only. No production/fault-injection raw-boundary execution appears
in that Windows log. Overall workflow success did not close this coverage gap.

## Compilation and execution contract

From an outer Windows/MSYS2 shell (not inside `alr exec`); preparation builds
and then establishes the single execution environment:

```sh
sh scripts/run_windows_native_boundary.sh . obj/windows-native-boundary
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

### FEATURES-CI-016R1 — reconcile released documentation tooling

Starting PR #27 head `95b8fc83fda09228954e4e6a8fc88e38eb791eca` normally merges
main `782e33ef6822887c45e607c5934032d9d856b3ad`, with no conflicts and no rebase,
amend, reset or force-push. Documentation run
[39543589137](https://github.com/zackboll/opencv_features_ada/actions/runs/39543589137),
job `119036644757`, step 12 failed because the newer official-wheel workflow
invoked the old branch installer without its required `--checkout`. Steps 9–11
had already passed native generation, coverage/warnings, mutations and
deterministic regeneration. This was not a production Ada or Windows failure.

R1 preserves main's documentation files, wheel approval inventory/security
checks and workflow byte-for-byte. All Windows harness files, 15 added fixtures,
mandatory campaigns and pinned release identities remain unchanged from the
starting PR head. No production/manifests/Linux-runner changes occur.

Fresh integrated local qualification passed:

- 101 configuration tests; repository, shell and fixed-profile checks.
- Native build, AUnit 67/67, both ordinary raw variants and actual-shim
  production/fault ASan/UBSan; both examples; six GPRinstall/two link-metadata
  regressions; source/installed/relocated consumers and audits.
- Strict GNATdoc 26.0.0: 127/127 documented/rendered elements, zero warnings;
  independent generation and diagnostic log byte-identical.
- Official Enhancer v0.1.0 wheel installed through the exact workflow interface
  (`--venv ... --with-guides`, no `--checkout`). Source/tag/tree, wheel/provenance
  hashes, installed modules/assets/renderer/launcher verified against main's
  unchanged approval inventory. Compatibility preflight: zero failures.
- Complete documentation suite: 104 executed / 104 passed, no skips, including
  real regeneration and installed security mutations. Enhancement deterministic,
  byte-idempotent, pristine/native identities preserved.
- Chromium 156.0.8078.4 / Playwright 1.64.1: 64/64 root, 199/199 project-prefix,
  64/64 prefix API assertions. Local Pages archive: 18 files, 13 pages,
  248 references, byte-identical. Hosted uploaded-artifact verification remains
  a separate final-head CI requirement, not inferred from the local tar.

An agent-side optional-preflight invocation initially used the wrong interface;
it was corrected to the documented `--revision`/`--workspace` arguments and
passed without source changes. Main's historical security evidence has one
existing trailing space; it is preserved unchanged, and the PR diff against
main is whitespace-clean. Final commit/tree and final-head hosted results are
recorded in PR #27. Real Windows execution remains post-merge only.

### Initial FEATURES-CI-016 local evidence

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