# Bootstrap validation record

## Task 007 — installation research and local qualification

Start/main and Task 006 merge: `7bac60fcc776918615985fa2cc89e5b8bfe426c7`;
Task 006 implementation `41c5d652e9471de7ec213dd2a67a221c02c31a90` is an
ancestor. Initial checkout was clean on that implementation branch. After
Gate 0, main fast-forwarded and `feature/007-clean-consumer-install` was created.

Gate 0 actual completed logs, exact merge SHA:

| Run | Job IDs | Result |
|---|---|---|
| 37252589376 Cross-platform | repository-checks 111583093614; linux 111583093693; macos 111583093431; linux-sanitizers 111583093604 | all success |
| 37252589409 Windows post-merge | windows 111583093151 | success |

SHA256 full downloaded logs:
cross-platform `290d9aa534c671defdbc6f9a8b94b83163bc10aeed3743584bbc8f28daaf2312`;
Windows `95250e5535a982edd7795be03759e999fbd93035f73babe2dc0b6a27ae9e37e9`.
JSON/job evidence hashes:
cross-platform `e68dd64c56755805d06c2baca0f5c23ae5c5b27c1dcf52d5421dafb8133b5ee7`;
Windows `f93a99046310de4457d325849e14378523435f4ca0fc7c832b89c496136574ca`.
Windows log has **67 OK lines**, **14 correspondence OK lines**, Successful
Tests 67, Failed Assertions 0, Unexpected Errors 0. Registration/ABI inventory
on the same SHA is recorded by the repository-check job: **67 and 17**.
Windows native output is OpenCV **5.0.0 / features**, external MSYS2
`mingw64/bin/g++.exe`, static Ada Features/Core archives and external Features
DLL/import-library checks. Actual PE checks print `libopencv_features-500.dll`
and `libopencv_core_shim.dll`; the step verifies Features/Core/Core-shim imports
exist. Existing extraction/matching/KNN2/ratio/radius and all correspondence
regressions execute successfully, not merely an overall green badge.

Local evidence retained outside Git under
`/tmp/features-task007-evidence.P4HK8vyM`. Baseline install workspace:
`/tmp/features-task007-baseline.2UyyMKhs`; prefix A moved to
`relocated-longer-prefix-b`. Both fresh public fixture builds/runs pass against
unchanged production/package files on Linux/OpenCV **4.10.0 / features2d**.
Commands: `alr -n build`; resolved-environment recursive
`gprinstall -f -p -r --prefix=<A> -P <resolved Core>/opencv_core.gpr`, then
the same command for Features; sanitized `gprbuild -p -v -vP2 -P consumer.gpr`;
fresh compilation after `mv <A> <B>`. Baseline inventory/generated config and
both full traces are preserved. First fixture compile exposed a missing Ada
enum operator visibility clause; corrected in the new fixture, not packaging.

First reusable validator run passed all three modes at
`/tmp/features-consumer.Mwq3oigx`. Core resolved normally from the new source
consumer's `alire/cache/pins/opencv_core_7956981a`, verified exact pinned SHA.
Original snapshot/source-consumer paths and prefix A are unavailable during
relocated compilation. Both projects and all four static archives resolve
under the intended prefix. Unused Common_Cxx_Switches retains bridge build
provenance but no Compiler package/use; no load-bearing source lookup found.
Linux ldd/readelf records system OpenCV linkage; runtime lookup is prefix-only.
See [installation contract and artifact inventory](installed-consumer-validation.md).

Final local validator evidence: `/tmp/features-consumer.4XUlDyB0` (all three
modes PASS). Core source was
`/tmp/features-consumer.4XUlDyB0/features_clean_consumer/alire/cache/pins/opencv_core_7956981a`;
it is retained under `unavailable-source-consumer` after installation. Prefix A
`/tmp/features-consumer.4XUlDyB0/prefix-a` was removed by relocation to
`/tmp/features-consumer.4XUlDyB0/relocated-longer-prefix-b`.
Both installed GPR paths and all four library paths are the inventory paths
in the installation document under A/B respectively. Source workspace is
retained as `unavailable-source-consumer`; fresh application workspaces are
`installed-consumer` and `relocated-consumer`. All three run logs contain
`opencv_features clean consumer ok` and OpenCV 4.10.0/features2d. Local native
compiler g++ Debian 14.2.0-19; GNAT 16.1.0; GPRbuild package 26.0.1.

Serial local regression: production/test builds, direct native AUnit,
`alr -n test`, **30** Python tests (previous **22**), repository checker,
C/C++ profile/header helpers, all shell syntax checks, raw production/fault
actual-shim tests, both ASan/UBSan variants, examples build/run and diff check
completed. Direct native counts **67 executed / 67 passed**, zero assertions
or unexpected errors; AUnit registrations **67 -> 67**, native ABI **17 -> 17**.
Alire test repeats the configured native suite and Linux raw tests; those
repeated results are not additional registered cases. No production API/configuration/version
changes or Core modifications were needed for the Linux baseline.

Ordinary PR exact-head evidence is recorded at review handoff after completed
logs are retrieved; it is not implied by local success. Task 007 Windows
execution remains post-merge only. Manual native-version matrix not dispatched:
no version-dependent linking/algorithm change. Release/index/pin removal/tag/
tarball qualification remains deferred.

First PR run `37254467678` on `11690347d2ca27355f75d91d52b4d5dca582edb2`:
repository-checks/Linux/Linux-sanitizers passed; macOS native AUnit and libc++
boundary/source consumer/install passed, but validator shell parsing failed at
line 73 before installed-consumer compilation. Reproduced exactly with GNU
Bash 3.2.0: case patterns inside a command substitution report unexpected `;;`
(modern Bash/dash accept it). Fix separates PATH-filter loop from command
substitution; no native/package/Core change. Completed log SHA256
`bbe99271ee102ca15bfb8d1d24bce7b8dae0fa6a98533243c10bd03b8a13c442`;
macOS job log `4349deba390a2804f70b1dbdaf407977e06a850d8b149c906f5ee5dc5f2530e6`.
Failure is validator implementation/old-shell portability, not Core contract.
Corrected validator passes all three modes under actual Bash 3.2 at
`/home/zboll/features-task007-local.L7988mcE/features-consumer.4kNNQUuI`.
An earlier reproduction attempt hit `/tmp` tmpfs exhaustion (actual compiler
"No space left on device" diagnostics preserved); retry used an isolated disk
TMPDIR, not a weakened test. All 30 Python tests/checker and sh/Bash-3.2 syntax
checks pass after correction. No production/package change.

Second PR run `37255117048` on `e827a93c141c94c23bccf25b659e5c452c577597`
passed repository-checks/Linux (all three consumers)/Linux-sanitizers. macOS
passed native/source/install and compiled/linked consumer A, but the strict
otool audit rejected executable libstdc++ automatically injected by GPR's
GNAT g++ driver. Native Features/Core dylibs use libc++ correctly. The generated
macOS Ada consumer now explicitly selects GNAT gcc as linker: already-built
Apple dylibs own their C++ runtime linkage. Linux remains g++; no production
or Core correction. Log SHA256
`df1c4517fcd619e1152566dce5c81e33492114cae2f11e938f70492716972b14`;
macOS job `111590419073` log
`768c5b1d40db7d6529c6c2f400f2981b59fe02b9c19617985b8588af70cb8d3c`.

## Status

**Build/CI tranche qualified locally; not a fully qualified binding or release.**
Historical ZIP checks below are distinct from actual build/test evidence.
No native result is implied by the existence of a test or workflow.

## Task 006 — owned candidate 2-D point correspondences

Starting fetched `origin/main`: **`009c911da04586340d3354c2723480267f193e3d`**,
the actual normal PR #5 merge (2026-10-05 01:11:35 UTC). Verified unchanged Task
005 head **`06c4c224065a503e29c4af3fa37bca3a7cd3d607`** is an ancestor of main.
Initial worktree was clean on `feature/005-radius-binary-matching` at that head;
fetched, checked out main, pulled `--ff-only`. After both gates passed, created
**`feature/006-point-correspondences`** from exact clean current `origin/main`.
Core pin remains `7956981a7881ce9121115f8cb65909aeb9edc439`; version **0.1.0-dev**.
No native source, interop, dependency, version or workflow change is included.

### Gate 1 — actual Task 005 Windows post-merge log

[Windows post-merge Features run 37250457092](https://github.com/zackboll/opencv_features_ada/actions/runs/37250457092),
[job 111576833776](https://github.com/zackboll/opencv_features_ada/actions/runs/37250457092/job/111576833776),
workflow and job completed **success**, job completion 2026-10-05 01:15:52 UTC.
Metadata and actual checkout log identify exact merge/main head
**`009c911da04586340d3354c2723480267f193e3d`**. Waited for completion before
creating the Task 006 branch or editing source. Retrieved actual job log via
`gh api repos/zackboll/opencv_features_ada/actions/jobs/111576833776/logs`:
**130525 bytes**, SHA-256
**`8ff01b2ea42f42ef3dc198297072732d8adc9cd47af7cc7ecc7c70bd7ebb9584`**.
Evidence is from that log, not a green badge.

OpenCV **5.0.0 / features (opencv5)**, MSYS2 OpenCV package **5.0.0-5**;
external **msys64/mingw64/bin/g++.exe**, GCC package **16.2.0-4**, Ada
GNAT native **16.1.0** / GPRbuild **26.0.1**. Independently matched all **53**
registered case names to actual log OK lines: **53 registered / 53 executed /
53 passed / 0 failed assertions / 0 unexpected errors**. All **nine** Task 005
radius cases executed; one-best/KNN2/ratio regressions remain green. Keypoint,
match and KNN2 ABI/layout tests pass; match size/alignment/offsets **12/4/0,4,8**,
KNN2 **20/4/0,4,8,12,16**, C-written interchange PASS.

Successful external-DLL inspection checks Features `.dll` and `.dll.a` exist,
static `.a` absent, driver external MinGW64 and not GNAT's C++ driver, configured
Features/Core/Core-shim import libraries present. Actual PE imports
**libopencv_features-500.dll** and **libopencv_core_shim.dll**. Native build/link
and AUnit execution with Core linkage succeed. No baseline correction needed.
This is Task 005 Windows coverage, not Task 006 post-merge Windows coverage.

### Public contract, architecture and inventory

New package **`OpenCV.Features.Correspondences`** declares
`Point_Correspondence` (Query_Index/Train_Index Positive; Query_Point/Train_Point
shared OpenCV.Float32_Point; Distance Matching.Binary_Descriptor_Distance),
`Point_Correspondence_Array (Positive range <>)`, and
`From_Matches (Query, Train : Feature_Set; Matches : Descriptor_Match_Array)`.
Pure Ada implementation uses only public `Count`/`Point`; no private fields,
descriptor copies, handles, Core bridges or native calls. Explicit complete
index preflight precedes exact-length result construction. Positive indices
beyond the respective count raise **OpenCV_Error**; no partial result escapes.
Positive-indexed input length fits Natural; offset arithmetic parenthesizes
`I - 1` to handle valid input bounds ending at Positive'Last without overflow.
Source inspection establishes preflight-before-construction; tests observe clean
late-invalid rejection, not instrumentation of allocation/construction internals.

Copy positions exactly, with no rounding/Float64/integer conversion, clamping,
normalization, coordinate offsets/transforms or Region-frame reinterpretation.
Preserve indices, descriptor distance, exact input order and every duplicate.
Empty matches return **1..0** for any empty/full Query/Train combination; nonempty
matches with either empty set reject. No norm compatibility or norm-specific
distance check; manually supplied matches may have differing norms. Distance
remains descriptor metadata, not confidence/probability/geometric residual/error.
Returned ordinary Ada records contain no references and outlive all inputs,
detectors, descriptor Mats and native storage. Inputs unchanged. Normal Ada
allocation errors remain possible. Raw KNN2 requires caller selection first;
Nearest/Mutual/KNN2-ratio/Radius outputs interoperate without new matcher policy.
Candidate points are **not geometric inliers**. No Calib3D dependency is added.

**This task adds no native C/C++ ABI and no new OpenCV algorithm dependency.**
ABI **17 -> 17** declarations/imports: zero new exports/imports, C++ production
functions, native handles or native allocator paths. Existing native source and
ABI files unchanged. Checker explicitly enforces 17 and pure-Ada public accessors.

AUnit **53 -> 67**, **14** actual new registrations, all executed/passed locally.
Exact case names (each prefixed `Correspondences ` in the suite/log):

1. `exact indices Float32 coordinates and distance`
2. `preserve reordered shifted and highest input bounds`
3. `preserve identical repeated-query and repeated-train duplicates`
4. `reject out-of-range query indices with OpenCV_Error`
5. `reject out-of-range train indices with OpenCV_Error`
6. `preflight late invalid query and train items`
7. `canonical empty bounds for all feature-set combinations`
8. `reject nonempty matches with empty query`
9. `reject nonempty matches with empty train`
10. `owned values survive sets and detector finalization`
11. `accept Nearest Mutual KNN2-ratio and Radius outputs`
12. `preserve input counts keypoints norms and descriptors`
13. `ignore norm mismatch and preserve full distance metadata`
14. `copy noncontiguous Region-local coordinates unchanged`

Reused/extended existing test-only pairing fixture with optional exact keypoints;
not installed in production. Signed fractional coordinates distinguish frames
and axes. No tolerance is used for value copies. Two checker regressions increase
Python **20 -> 22**, including rejection of private/native access.

### Local qualification

Linux x86_64, OpenCV **4.10.0 / features2d (opencv4)**, Alire **2.1.1**, GNAT
**16.1.0**, GPRbuild crate **26.0.1**. Host g++ **14.2.0**; inside Alire the
resolved g++ banner is **GNAT-FSF-builds 16.1.0**, using Linux libstdc++.
Python **3.13.5**. Warnings-as-errors unchanged. Shared build operations serial;
actual logs retained outside tracked source. Unchanged merged baseline also
executed/passed **53/53**, raw and sanitizer variants, and both examples before
Task 006 edits. First implementation build/suite passed without corrections.

| Command | Actual result |
| --- | --- |
| `alr -n build` | PASS production build |
| `alr -n -C tests build` | PASS test build |
| `alr -n -C tests exec -- sh ../scripts/run_native.sh bin/run_tests` | **67 registered / 67 executed / 67 passed**, **14/14 Task 006**, 0 failed assertions / 0 unexpected errors |
| `alr -n test` | PASS same **67/67/67**, not 134 distinct cases |
| `python3 -m unittest discover -s tests/configuration -v` | **22/22**, no failures/errors |
| `python3 scripts/check_repository.py` | PASS **17 ABI / 67 registrations**, public-accessor boundary/pins/manifests/ownership/topology |
| `sh scripts/run_profile_tests.sh` | **2/2** C/C++ helper executables PASS, not native algorithm coverage |
| `for script in scripts/*.sh; do sh -n "$script"; done` | **6/6** PASS |
| `alr -n exec -- sh scripts/run_sanitizers.sh native` | **2/2** production and fault-injection actual-shim variants PASS |
| `alr -n exec -- sh scripts/run_sanitizers.sh` | **2/2** existing ASan+UBSan variants PASS, leak detection/halt-on-error, no diagnostics/suppressions |
| `alr -n -C examples build` | PASS |
| `alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic` | PASS, 393 features locally |
| `alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_match_synthetic` | PASS, 121 ratio-accepted owned candidate point pairs locally; 89 radius32 matches |
| `git diff --check` | PASS |

Native regression/sanitizer suites remain green; **no Task 006-specific pure-Ada
memory sanitizer coverage** is claimed. Existing upstream/Core libraries are not
all instrumented. Example counts are observations, not portable API guarantees.

### Ordinary PR gate and explicit matrix omission

Final tested commit, remote/PR SHA equality and completed ordinary job log
evidence are recorded in the Task 006 PR body/qualification comment, avoiding
an evidence-only source commit that would invalidate the tested final head.
Require repository-checks/Linux/macOS/linux-sanitizers on that exact final PR
head, actual Task 006 OK case names and full suite counts, unchanged 17 ABI,
existing raw/fault/sanitizer regression green. Keep PR OPEN, non-draft, unmerged,
auto-merge disabled. No amend, force push, merge, tag, release or version bump.

**No manual 4.1/4.10/5.0 matrix dispatched for Task 006**: pure Ada conversion
adds no native API/call or version-dependent algorithm semantics. Existing
Windows Gate 1 plus full local regressions and ordinary PR CI are the intended
evidence; pinned-matrix dispatch would add no meaningful Task 006 evidence.

All geometry/estimator policy remains deferred: homography, RANSAC/LMEDS/RHO/
USAC, fundamental/essential matrices, epipolar filtering/recoverPose, PnP,
triangulation, camera/stereo calibration, undistortion/rectification, inlier
flags/reprojection error, coordinate transforms/pixel normalization/intrinsics,
3-D points, DTED/terrain/geospatial/navigation logic. Persistent databases,
arbitrary K, masks, FLANN, SIFT/SURF/GFTT, GPU/UMat and optical flow also remain
deferred. Calib3D/application may consume Features output, never the reverse.
Installed/clean-consumer qualification, allocator exhaustion and broader
platform/version/source-review limitations remain as documented historically;
no release readiness, formal proof, timing or navigation accuracy is claimed.

## Task 005 — absolute binary distance radius matching

Starting fetched `origin/main`: **`c545f00d3aaff18af1a5385fccb800800deb23dc`**,
exactly the expected PR #4 merge. Clean tracked worktree, previously on
`feature/004-knn2-ratio-filter` at `ad529998c8d5b5f2a64e19df355c30f88a6be5db`.
Created **`feature/005-radius-binary-matching`** directly from fetched main.
Core pin remains `7956981a7881ce9121115f8cb65909aeb9edc439`; version remains
**0.1.0-dev**. No unrelated changes discarded; no dependency/version bump,
amend, force push, merge, auto-merge, tag or release.

### Gate 0 — exact Task 004 Windows post-merge execution

[Run 37206302598](https://github.com/zackboll/opencv_features_ada/actions/runs/37206302598),
job **111448089162**, workflow **Windows post-merge Features**, completed
**success**, 2026-10-04 13:44:09 UTC, exact head
**`c545f00d3aaff18af1a5385fccb800800deb23dc`**. Retrieved workflow/job metadata,
the **actual job log** via `gh api .../actions/jobs/111448089162/logs`, and the
run's log ZIP. `gh run view --log` unexpectedly returned empty output; direct
job API retrieval supplied **129232 bytes**, SHA-256
**`beba315b4a3424e137f43b54e04f5536b37e68c6ef00e240e0c8dfb31b917a80`**.
No inference from the badge or empty CLI output was used.

Exact checkout SHA appears in log. Native **OpenCV 5.0.0 / features (opencv5)**,
MSYS2 **mingw-w64-x86_64-opencv 5.0.0-5**, external
**msys64/mingw64/bin/g++.exe**, GCC **16.2.0-4** package (Alire external 16.2.0).
All **44 named AUnit registrations** appear as OK: **44 executed / 44 passed**,
**0 failed assertions / 0 unexpected errors**. Includes three pure-Ada ratio
tests, WTA2/3/4 KNN2, mismatch/empties/lifetime/translated ratio, and compiler-
derived KNN2 layout/interchange. Existing keypoint and match layout tests pass;
match size/alignment/offsets **12/4/0,4,8**, KNN2 **20/4/0,4,8,12,16**, with
C-written interchange PASS. This independently establishes the expected
**44 registered / 44 executed / 44 passed** baseline before source edits.

Successful inspection step checks Features `.dll` and `.dll.a` exist, `.a`
does not; configured Features, Core and Core-shim import libraries exist, and
compiler is external MinGW64 (not GNAT's C++ driver). Actual PE output imports
**libopencv_features-500.dll** and **libopencv_core_shim.dll**. Build/link and
native execution succeed with the configured Core link. Topology remains valid;
no corrective baseline commit/rerun needed. Task 005 Windows execution remains
post-merge only and is **not** claimed by this Task 004 log.

### Source, contract and test evidence

Before implementation, re-retrieved/hash-verified the official peeled commits
for **4.1.0 / 4.10.0 / 5.0.0**, including actual 5.0 `modules/features` paths.
`radius-matcher-source-review.md` records immutable commits, source paths,
hashes, anchors and the exact radius chain conclusions. Supporting file hashes
remain in `source-provenance.json`; no vendored upstream files.

`Brute_Force_Radius_Match` returns flat owned Descriptor_Match values. Automatic
Hamming/Hamming2, **inclusive distance <= Maximum_Distance**, explicit threshold
**1..256 / 1..128** respectively; zero and above-128 Hamming2 reject even on
empty inputs. Norm mismatch checked before empty success. Compatible query/train/
both empty returns **1..0**; one-row train valid. Query ascending, distances
nondecreasing per query, ties with unspecified train order. No per-query duplicate
train rows; no global train uniqueness. No cross-check, ratio semantics, masks,
persistent matcher, arbitrary descriptors, GPU or geometry/Calib3D dependency.

All three CPU radius implementations use direct train k in DMatch, not KNN's
IMGIDX_SHIFT=18. **No radius 262143-row cap**; signed-32-bit native dimensions/
indices and checked flattened INT32_MAX/vector/Ada/allocation representation
remain. High-index tests actually return native row **262144**, Ada index
**262145**, with Train.Count=262145 for both norms. Existing one-best/KNN packed
overflow rejection is unchanged. Distance matrices use native full Cartesian
storage; byte arithmetic is preflighted without promising practical memory
availability. Staging reserves only actual match count and publishes atomically.

**9 new registrations**, **44 -> 53**, no weakened/deleted existing tests.
Exact hand-constructed bit/cell oracles test 0/1/2/3, inclusive boundary,
all ties, four matches for one query, missing query gap, one match, zero matches,
exact field mapping. WTA2/3/4 additionally compare every ORB query/train pair to
an independent pure-Ada bit/cell oracle, without hard-coded scene counts.
Separate empties/mismatch/threshold/preservation/one-row/max/lifetime/high-index
cases execute. Test-only fixture child preserves pairing and exists only in
the test crate, not the production installed library/API.

Both actual-shim raw variants execute radius exact fixtures, negative null/
selector/schema/depth/channel/column/N-D/threshold cases, cleared publication/get
outputs, null destroy, compatible empties, norm maximum, truly noncontiguous ROI,
shared train rows across queries (not cross-check), input lifetime and high index.
Existing fault framework stages **15/16/17/18**, all **five exception categories**,
plus empty cleanup cover preallocation, post-match, staging and prepublication.
Overflow is tested through the **same production arithmetic helpers**, without
forged handles or billions of native matches. Actual INT32_MAX result allocation/
native count overflow is not executed; real allocator exhaustion is not claimed.

### Local qualification environment and commands

Linux x86_64, OpenCV **4.10.0 / features2d (opencv4)**, GNU g++ **14.2.0**
(Debian 14.2.0-19), Alire **2.1.1**, GNAT **16.1.0**, GPRbuild crate **26.0.1**
(banner **GPRBUILD 26.0.0**). Core pin above, warnings-as-errors unchanged.
Alire/GPR commands run **serially** against shared artifacts. Log evidence is
retained outside tracked source. Final tested commit and remote run evidence
are recorded in the Task 005 PR qualification body/comment, avoiding a corrective
documentation-only commit after the final pinned-matrix dispatch.

| Exact command | Executed result |
| --- | --- |
| `alr -n build` | PASS production build |
| `alr -n -C tests build` | PASS test build |
| `alr -n -C tests exec -- sh ../scripts/run_native.sh bin/run_tests` | **53 registered / 53 executed / 53 passed**, 0 failed assertions / 0 unexpected errors |
| `alr test` | PASS, same **53/53/53**, not 106 distinct tests |
| `python3 -m unittest discover -s tests/configuration -v` | **20 executed / 20 passed**, 0 failures/errors |
| `python3 scripts/check_repository.py` | PASS **17 ABI declarations/imports / 53 registrations**, manifests/pin/ownership/CI topology |
| `sh scripts/run_profile_tests.sh` | **2 helper executables / 2 passed**, including checked radius count/layout compile-time boundaries; not native algorithm coverage |
| `for script in scripts/*.sh; do sh -n "$script"; done` | **6 scripts / 6 passed** |
| `alr -n exec -- sh scripts/run_sanitizers.sh native` | **2/2** actual-shim variants PASS (production, fault injection) |
| `alr -n exec -- sh scripts/run_sanitizers.sh` | **2/2** actual-shim ASan+UBSan variants PASS, ASan leak detection and halt-on-error / UBSan halt-on-error, no diagnostics/suppressions |
| `alr -n -C examples build` | PASS |
| `alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic` | PASS |
| `alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_match_synthetic` | PASS, explicit absolute radius **32** example policy, **89** radius matches locally |
| `git diff --check` | PASS |

Observed matching example counts remain Query=406 / Train=418 / nearest=406 /
mutual=218 / KNN2=406 / ratio-accepted=121; radius32=89 is not a portable API
guarantee or confidence/geometric/navigation evidence. ASan and UBSan instrument
the actual Features shim, not all upstream/Core libraries. Only test-driver
policy disables OpenCL; production leaves global state unchanged.

Validation correction: first test compile diagnosed tautological Positive>0
assertions under warnings-as-errors. Replaced with meaningful result-index bounds,
without weakening compiler checks. Serial rebuild/direct suite passed. No native
algorithm correction, sanitizer suppression or baseline failure concealed.

### Remote qualification gate policy

Normal non-draft PR stays OPEN, unmerged, auto-merge disabled. Require actual
repository/Linux/macOS/Linux-sanitizer job logs on unchanged final PR head before
one manual pinned-matrix dispatch. Each 4.1/4.10/5.0 target must execute the same
53 registered tests and radius/raw/fault/sanitizer cases, not 159 distinct tests.
Actual run IDs/job logs/counts and local=remote=PR SHA equality belong in the PR
qualification record. Windows is deferred to post-merge; do not merge for evidence.
No release, complete cross-version safety, installed-consumer qualification,
formal proof, timing or navigation accuracy follows from these tests.

## Task 004 — fixed two-nearest binary matching and pure-Ada ratio filtering

Starting fetched `origin/main`: **`966df5acd603f3e6ffddde3f13ff78dd54e9e97b`**
(PR #3 merge), clean worktree. Previously checked out
`feature/003-binary-bfmatcher`, HEAD `d95797dfe8417e1d971bd02ced066f09c9a421e1`.
Created `feature/004-knn2-ratio-filter` from fetched main; no intervening work.
Core pin `7956981a7881ce9121115f8cb65909aeb9edc439` and version `0.1.0-dev`
unchanged. No amend, force push, merge, tag, release or Windows PR job.

### Gate 0 — PR #3 Windows post-merge

[Run 37176893574](https://github.com/zackboll/opencv_features_ada/actions/runs/37176893574),
job **111361276654**, completed **success**, 2026-10-04 04:28:35 UTC, on starting
main SHA above. First Windows execution including binary matcher and 33-case
suite: **33 registered / 33 executed / 33 passed**, **0 failed assertions / 0
unexpected errors**. OpenCV **5.0.0 / features**, MSYS2 OpenCV package **5.0.0-5**;
external MSYS2 MinGW64 `mingw64/bin/g++.exe`, GCC package **16.2.0-4**, not GNAT's
C++ compiler. Features `.dll` / `.dll.a` existence and static archive absence
checks PASS; configured Features, Core and Core-shim import libraries present.
PE imports explicitly **libopencv_features-500.dll** and **libopencv_core_shim.dll**.
Exact job log retrieved; no baseline correction or rerun required. This is
Task 003 execution, not Windows coverage of Task 004. Windows stays post-merge only.

### Contract/source/ABI evidence

`Brute_Force_KNN_2` fixes K=2 and automatically uses matching Required_Norm
semantics: Hamming 0..256 or Hamming2 0..128. Norm mismatch precedes empties.
Compatible empties return 1..0 without native matching; nonempty query + one-row
train raises OpenCV_Error in Ada and C. Train<=262143, no corresponding 18-bit
Query cap. Otherwise result length=Query.Count; ascending one-based query indices,
distinct one-based train indices, exact integer nearest<=second distances, ties
permitted with unspecified tied train order. Owned values outlive inputs/detectors/
matcher/staging. Inputs unchanged. Separate from Mutual_Nearest K=1 cross-check.

Pure Ada `Passes_Ratio_Test` / `Filter_By_Ratio`: explicit threshold, no default;
OpenCV_Error unless 0<r<1. Negated positive validity rejects NaN/infinities.
Strict nearest < r*second, including equality and 0/0 rejection. Filter returns
nearest Descriptor_Match values only, preserving candidate order. Ratio is not
confidence/probability or geometric verification; .80 in the example is policy,
not a recommended navigation constant. Numeric invalid thresholds are tested;
no nonportable NaN representation manufactured.

Official sources re-retrieved/hash-verified at **371bba8f54560b374fbcd47e7e02f015ac4969ad**
(4.1), **71d3237a093b60a27601c20e9ee6c3e52154e8b1** (4.10), and
**40738fb16ceddb5fb3fea747585f7ce6abb0605b** (5.0). KNN overload forwarding,
CPU Mat path, K=min(K,Train.rows), distinct sorted insertion, CV_32S binary
distances, DMatch construction, empty handling, packed train fields and
crossCheck K==1 are derived in `bfmatcher-source-review.md`.

C compiler sizeof/_Alignof/offsetof and Ada Size/Alignment/Position plus C-written
field-by-field interchange PASS: **20 bytes / alignment 4 / offsets 0,4,8,12,16**.
These are observations, not handwritten layout proof.

### Local qualification

Linux x86_64, OpenCV **4.10.0 / features2d**, GNU g++ **14.2.0** (Debian
14.2.0-19), Alire **2.1.1**, GNAT **16.1.0**, GPRbuild crate **26.0.1** (banner
GPRBUILD 26.0.0). Warnings remain errors. Qualified Task 004 implementation
before its normal commit; immutable final commit/remote/CI SHA evidence is
recorded in the Task 004 PR qualification body after remote jobs complete.

| Validation | Executed result/count |
| --- | --- |
| Repository checker | PASS: **16 ABI exports/imports**, **44 registrations**, manifests/pin/ownership/CI topology |
| Python discovery | **20 executed / 20 passed**, 0 failures/errors |
| C/C++ profile/header helpers | **2 executables executed / 2 passed**, not native algorithm coverage |
| Shell syntax | **6 scripts checked / 6 passed** |
| Root production build | PASS |
| Tests build / direct native suite | PASS; **44 registered / 44 executed / 44 passed**, 0 failed assertions, 0 unexpected errors |
| `alr test` | PASS; separate execution of the same **44** cases, not 88 distinct registrations |
| Ordinary raw production actual-shim | **1 executed / 1 passed** |
| Ordinary raw fault-injection actual-shim | **1 executed / 1 passed** |
| ASan production actual-shim | **1 executed / 1 passed**, leak detection on, no diagnostics |
| ASan fault-injection actual-shim | **1 executed / 1 passed**, leak detection on, no diagnostics |
| UBSan | Both variants PASS, halt-on-error enabled, no diagnostics/suppressions |
| Examples build / orb_synthetic / orb_match_synthetic | PASS / PASS / PASS |
| `git diff --check` | PASS |

New **11** AUnit registrations separately cover pure ratio mechanics, WTA2/3/4
KNN2/preservation, mismatch including empties, compatible empties, lifetime,
translated-scene ratio filtering, KNN2 layout. No hard-coded scene acceptance count.
Observed example only: Query=406, Train=418, nearest=406, mutual=218, KNN2=406,
ratio=.80, accepted=121, nearest distances=0..99, accepted distances=0..74.
These synthetic counts are not portable API guarantees or localization evidence.

Both raw variants and both sanitizer variants execute exact Hamming/Hamming2
0/1 pair (third row=2), nonzero 1/2 pair, 0x03 Hamming=2/Hamming2=1, equal-distance
ties with distinct valid indices, all schema/null/selector negatives, one-row
rejection, compatible owned empties, cleared get outputs, null destroy, ROI and
input-independent lifetime. Train=262143 has unique best row 262142 and second
row 262141, both packed indices preserved; Train=262144 rejects. Query=262144,
Train=2 executes for both norms even in both sanitizer variants (runtime remained
reasonable). Fault stages 11/12/13/14 cover invalid_argument, cv::Exception,
bad_alloc, std::exception and unknown exception, atomic null/zero publication,
empty publication cleanup and getter clearing. Production has no control symbol.
Driver alone disables OpenCL; production leaves process-wide policy unchanged.
Core/upstream native libraries are not all sanitizer-instrumented. Injection is
not evidence of real allocator exhaustion.

Validation corrections: first tests compile exposed missing operator visibility
clauses, fixed normally. Initial `alr test` and example build were incorrectly
run concurrently against shared ignored Features object storage; dependency file
corruption and missing object during archive creation reproduced the scheduling
conflict, not an algorithm defect. Serial reruns both PASS, without suppressions
or source/build-policy weakening. Diagnostics were retained during qualification.

### Remote qualification and remaining scope

The final-head PR record supplies actual repository-checks/Linux/macOS/Linux-
sanitizers conclusions, registered/executed/passed counts and the single stable
final-head manual 4.1/features2d, 4.10/features2d, 5.0/features matrix run. Matrix
retains WITH_ADE=OFF. This committed local record does **not** label remote jobs
passed before execution. Windows Task 004 is deliberately deferred until merge.
Installed/clean-consumer relocation/linkage Task 001 work remains outstanding.
No arbitrary K, masks, radius, FLANN, float/SIFT/SURF, persistent matchers, drawing,
GPU/UMat public API, generators, geometric verification, homography, PnP, DTED,
optical flow or estimator policy added. No release readiness/formal proof claimed.

## Task 003 — binary one-best descriptor matching

Starting fetched `origin/main`: **`086e655b4a5d0d02960a3c9eda2452eba0ef6854`**
(PR #2 merge), clean worktree. Previously checked out
`feature/002-orb-native-qualification`, HEAD
`e273ae3ea9fc83aae6660bb8d05cff2792684492`. Requested branch:
`feature/003-binary-bfmatcher`, created from actual fetched main. Core pin
`7956981a7881ce9121115f8cb65909aeb9edc439` and version `0.1.0-dev` unchanged.

### Gate 0: PR #2 post-merge Windows

[Run 37174688163](https://github.com/zackboll/opencv_features_ada/actions/runs/37174688163),
job 111354758918, completed **success** on starting main at 2026-10-04 03:45 UTC.
OpenCV **5.0.0 / features**, MSYS2 `mingw-w64-x86_64-opencv 5.0.0-5`;
selected MSYS2 MinGW64 `mingw64/bin/g++.exe`, GCC package **16.2.0-4**, not
GNAT's C++ compiler. **24 registered / 24 executed / 24 successful**, **0
failed assertions / 0 unexpected errors**. Features DLL and `.dll.a` checks
passed, static archive absence check passed, all three configured native
Features/Core/Core-shim import-library checks passed. PE imports explicitly
include `libopencv_features-500.dll` and `libopencv_core_shim.dll`.
No rerun or baseline correction needed. This is Task 002 Windows evidence,
not execution of Task 003 matching. Windows remains post-merge only.

### Public/native contract and source review

`OpenCV.Features.Matching.Brute_Force_Match` consumes two immutable owned
Feature_Sets, borrowing private descriptor Mats via Core callbacks without
deep copies. Ada-owned results have ascending one-based query/train indices,
exact integer distances, automatic Required_Norm selection, nearest or native
mutual-nearest modes, and compatible empty success. Norm mismatch is rejected
even when empty. Hamming is 0..256; Hamming2 is 0..128. Ties do not promise a
particular exact train index. There are no masks or ratio filtering.

Source review covers official peeled 4.1.0/4.10.0/5.0.0 revisions and paths
recorded in `bfmatcher-source-review.md` and `source-provenance.json`.
Train <=262143 derives from CPU BFMatcher's 18-bit packed index assertion;
reverse cross-check batchDistance uses plain indices, so Query has no such cap.
Native checks cover schema, selectors, imgIdx=0, count/index/order/uniqueness,
finite integral distances and norm-specific bounds before result publication.

### Local execution evidence

Linux x86_64, OpenCV **4.10.0 / features2d**, external GNU g++ **14.2.0**,
Alire **2.1.1**, GNAT **16.1.0**, GPRbuild **26.0.1**. Warnings remain errors.
Executed against the implementation in this Task 003 branch before commit:

| Validation | Actual result/count |
| --- | --- |
| `python3 scripts/check_repository.py` | PASS; 13 matched ABI exports/imports, 33 AUnit registrations, manifest/pin/ownership/CI checks |
| Python unittest discovery | **20 executed / 20 passed**, 0 failures/errors |
| Profile/header helper script | **2 C/C++ helper executables executed/passed**, not native algorithm tests |
| Shell syntax | **6 scripts checked/passed** |
| Root build and tests build | PASS |
| Direct native AUnit | **33 registered / 33 executed / 33 passed**, 0 failed assertions, 0 unexpected errors |
| `alr test` | PASS; separate invocation of the same **33** cases, not 66 distinct tests |
| Raw actual-shim boundary | **2 variants executed/passed**: production and fault-injection |
| ASan + UBSan actual-shim | **2 jointly instrumented variants executed/passed**, no diagnostics/suppressions, leak detection enabled |
| C/Ada match layout | PASS: compiler-derived size **12**, alignment **4**, offsets **0/4/8**, C-written record read by Ada |
| Exact Hamming oracle | PASS: 0/1/2/256, valid zero-based query/train indices |
| Exact Hamming2 oracle | PASS: 0/1/128; 0x03 changed cell gives 1 versus Hamming's 2 |
| Cross-check oracle | PASS for both norms: A/X retained at 0, B/X rejected (B nearest X at 1) |
| Native bound oracles | PASS: Train=262144 rejected; Train=262143 accepted with unique last index 262142; Query=262144 accepted in both modes |
| Raw negatives/ownership | PASS: null outputs/inputs, selectors, depth/channels/31/33 columns/N-D, cleared get(-1/count), null destruction, empty/ROI/lifetime, publication cleanup |
| ORB synthetic example | PASS: 393 keypoints/descriptors |
| Matching synthetic example | PASS: Query 406 / Train 418; nearest 406 (86 zero, min/max 0/99); mutual 218 (86 zero, min/max 0/92) |
| `git diff --check` | PASS |

Local supplemental **4.1.0 / features2d** qualification also passed: build,
**33/33/33 AUnit**, raw production/fault, compiler layout, Hamming/Hamming2,
cross-check and both ASan+UBSan variants. Source-built 4.1 uses WITH_ADE=OFF.
An attempted extra local 5.0 run selected an existing **Core/Geometry-only**
installation with no `opencv2/features.hpp`; configuration correctly rejected
it. This is an incomplete local native installation, not matching execution or
a code defect. Default 4.10 configuration was restored and qualification rerun.
Final remote 5.0 qualification is required, not inferred from source review.

During development, concurrent test/example Alire builds contended for the
shared generated `opencv_features_install.gpr.tmp`. Serial rerun resolved it;
subsequent Alire builds were serialized. Compiler diagnostics for Ada aggregate
syntax, equality visibility/unused use clause, and the synthetic checker modulus
were corrected normally, retaining all warning-as-error checks. No production
fallback, sanitizer suppression, Core change or unrelated build refactor added.

### Remote evidence and review gate

The final-head ordinary PR jobs and once-dispatched corrected pinned matrix
must be recorded with immutable SHA/run/job IDs in the Task 003 PR body before
the review gate. They are **not claimed as run or passed by this pre-dispatch
local record**. [Task 003 Actions](https://github.com/zackboll/opencv_features_ada/actions?query=branch%3Afeature%2F003-binary-bfmatcher)
and [Task 003 PR](https://github.com/zackboll/opencv_features_ada/pulls?q=is%3Apr+head%3Afeature%2F003-binary-bfmatcher)
provide the live evidence. Do not equate written workflows with passing jobs.
The matrix must qualify 4.1/features2d, 4.10/features2d and 5.0/features,
including all 33 AUnit, layout/raw oracles and actual-shim ASan+UBSan variants.
It supplies previously missing corrected remote Task 002 4.1 evidence too.

Remaining Task 001 installed/clean-consumer relocation/linkage qualification
is outstanding. Upstream libraries are not fully sanitizer-instrumented; real
allocator exhaustion, optional vendor HAL/GPU paths and future native versions
are not comprehensively qualified. KNN/ratio/radius/masks/float descriptors,
FLANN, geometry and navigation accuracy remain outside this slice. No version,
release, merge or auto-merge work is authorized or performed.

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

### First pinned matrix conclusion and deterministic correction

The manual matrix was dispatched **once**,
[run 37173672098](https://github.com/zackboll/opencv_features_ada/actions/runs/37173672098),
at implementation head `9968fdbcfcfc204cf9517bc2b6f140abb5e7d5b8`.

| Target | Module | Build / native AUnit | Mask / raw ABI / C-Ada layout | ASan / UBSan |
| --- | --- | --- | --- | --- |
| 4.1.0 | features2d | FAIL in unrelated upstream ADE before Features; 24 registered in source, 0 executed / 0 passed | NOT EXECUTED | NOT EXECUTED |
| 4.10.0 | features2d | PASS; 24 registered / 24 executed / 24 successful; 0 failed assertions / 0 unexpected errors | PASS | PASS both actual-source variants |
| 5.0.0 | features | PASS; 24 registered / 24 executed / 24 successful; 0 failed assertions / 0 unexpected errors | PASS | PASS both actual-source variants |

Failed job `111351710612` log: `ade-0.1.1d/.../typed_graph.hpp:101:10:
error: 'uintptr_t' in namespace 'std' does not name a type`, compiling unused
`topological_sort.cpp`. Native GCC 13.3.0. OpenCV 4.1.0
`modules/gapi/cmake/init.cmake` defaults WITH_ADE=ON, downloading/adding the
ADE target before G-API's whitelist disablement. Thus even BUILD_LIST limited
to core/imgproc/features2d still builds this unrelated target. Local GCC 14.2.0
reproduces the exact failure by configuring the same tag with WITH_ADE=ON and
building target `ade`; not transient and not an ORB/test defect.
Correction: set **WITH_ADE=OFF** in the manual workflow, using upstream's
supported option. No upstream source patch, ORB module change, compiler-warning
suppression or weakened test. No unchanged rerun or second full-matrix dispatch.
Local corrected oldest-target validation is reported separately below; it does
not convert the original failed remote matrix cell into success.

Ordinary PR run
[37173674726](https://github.com/zackboll/opencv_features_ada/actions/runs/37173674726)
at that implementation head passed all four jobs. Linux/OpenCV 4.6.0 and
macOS/OpenCV 5.0.0 each executed/passed 24 AUnit cases, with zero assertions/errors;
Linux raw boundary and linux-sanitizers passed both variants; macOS verified actual
Features/Core-shim/libc++ linkage. Repository checks passed 20 Python tests.

Corrected **local** OpenCV 4.1.0 source build (official tag above, host GCC 14.2.0,
WITH_ADE=OFF, only core/imgproc/features2d) completed successfully. With its
pkg-config and loader prefix selected explicitly, `sh scripts/test.sh` and
`alr -n exec -- sh scripts/run_sanitizers.sh` passed: **24 registered / 24 executed /
24 successful / 0 failed assertions / 0 unexpected errors**, mask/raw ABI/layout
PASS, ordinary and ASan/UBSan production-source/fault variants all PASS.
The actual binding implementation is identical to the matrix's implementation
head; the correction changes only manual native-build configuration and evidence.
The failed remote 4.1 cell remains an explicit limitation of that single matrix
run, not a claimed passing corrected CI run. No second full matrix was dispatched.
All three reviewed native tags now have functional local/remote evidence, but
the **remote corrected 4.1 matrix cell at the final branch SHA remains outstanding**.

Task 001's source, masks, raw ABI/layout, CPU production-shim sanitizer and first
corrected Windows gates are covered. Installed/clean-consumer relocation/linkage
and corrected remote oldest-target matrix qualification remain outstanding;
Task 001 is not declared entirely complete. Real allocator exhaustion and full
dependency/GPU sanitizer qualification remain separately documented limitations.

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
