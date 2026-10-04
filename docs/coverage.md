# Features binding coverage

This is a handwritten capability inventory, not a generated header census.
"Implemented draft" means source is present, not fully qualified. The initial
53-case AUnit suite now passes locally on Linux/OpenCV 4.10.0; see
`bootstrap-validation.md` for exact evidence and remaining platform/version,
source-review, sanitizer and ABI robustness gates.

| Native capability | Ada API | Status |
| --- | --- | --- |
| `cv::ORB::create` | `OpenCV.Features.ORB.Create` | Implemented draft, fixed structural profile |
| ORB object lifetime | limited-controlled `Detector`, `Close`, `Is_Ready` | Implemented draft |
| `detectAndCompute`, no supplied keypoints | two `Detect_And_Compute` overloads | Implemented draft, UInt8 C1 and optional mask |
| KeyPoint/descriptor conversion | private `Feature_Set`, getters and row mapping | Implemented draft |
| Native version/backend reporting | `Native_Version`, `Native_Backend` | Implemented draft |
| Separate detect/compute and supplied keypoints | none | Deferred |
| Arbitrary pyramid/patch parameters and setter APIs | none | Deferred |
| Binary one-best BF match | `Matching.Brute_Force_Match` | Hamming/Hamming2, nearest/mutual-nearest |
| Binary KNN, fixed K=2 | `Matching.Brute_Force_KNN_2` | Hamming/Hamming2, separate from cross-check |
| Strict ratio filtering | `Passes_Ratio_Test`, `Filter_By_Ratio` | Pure Ada, explicit threshold, nearest values only |
| Binary absolute radius | `Matching.Brute_Force_Radius_Match` | Inclusive CPU Hamming/Hamming2, flat owned values |
| Arbitrary K, match masks | none | Deferred |
| Other detectors, descriptors and FLANN | none | Deferred |
| UMat/OpenCL/CUDA wrappers | none | Deferred |
| Geometry, PnP, DTED, estimator logic | none | Outside Features |

No unimplemented native entry point is represented by a fake successful stub.

Task 002 adds four AUnit registrations: native nonbinary-mask semantics,
compiler-derived C/Ada keypoint representation/interchange, raw detector
creation, and raw extraction/result access with actual Core callback handles.
The latter covers null outputs/inputs, real wrong-type/shape Mats, initialized
failure outputs, invalid indices, first/last points, descriptor schema and
detector-independent result lifetime. Existing twenty semantic tests remain.

A separate Linux boundary driver additionally uses authoritative Core C
factories, rejects a legitimate external-view output, checks production
absence of fault controls, and exercises test-only exception categories and
publication-stage cleanup. Both production-source and fault-hook variants
run ordinarily and under ASan/UBSan. These assertions are **not additional
AUnit registrations**. C11 header and pure profile helper checks remain
separate static/helper evidence; Python configuration/topology inventory is 20.

Source review is limited to the fixed CPU profile in 4.1.0/4.10.0/5.0.0;
see `orb-source-review.md`. Real allocator exhaustion and installed/clean
consumer relocation are not covered.

Task 003 adds nine AUnit registrations: WTA2/WTA3/WTA4 self-match,
norm mismatch (including empty), compatible empties in both modes, related-scene
mutual nearest, descriptor/keypoint preservation, result lifetime, and compiler-
derived C/Ada match-record layout/interchange. Total: **33 registered**.
One-based indices, sorted query order, exact integer distances and automatic
norm selection are public contracts; ties do not promise a specific train index.
One-best/KNN2 Train rows are limited to 262143 by native packed indexing; Query is not.

Linux's two raw driver variants add manually controlled binary oracles:
Hamming 0/1/2/256; Hamming2 0/1/128; cross-check A/X retained and B/X rejected;
distinct train index; ROI; empty; schema/selector/null negatives; cleared result
access; oversized train rejection; 262144-row query acceptance in both modes;
input-independent result lifetime; and exception/publication cleanup. Both
variants also execute under ASan+UBSan, without suppressions. These are not
additional AUnit cases or instrumentation of all upstream libraries.
See `bfmatcher-source-review.md` and the validation record for exact evidence.

Task 004 adds **11 registrations**, total **44**: three pure-Ada ratio cases
(strict boundary oracles, invalid thresholds even on empty input, filtering
fields/order/empty/all-accepted/all-rejected), WTA2/3/4 KNN2 invariants and input
preservation, norm mismatch including empty sets, compatible empties, owned-value
lifetime, related-scene ratio acceptance, compiler-derived KNN2 layout/interchange.
Pure-policy cases do not call native code. Numeric invalid ranges are tested;
NaN is rejected by explicit positive validity, but no fabricated floating bit
representation is used in the tests.

Both Linux raw variants add exact KNN2 Hamming/Hamming2 0/1 and nonzero 1/2
pairs, distinguishing 0x03 cell, ties without exact tied ordering, schema/null/
selector negatives, one-row rejection, empties, cleared access, ROI/lifetime,
262143-row train with both best indices near its high end, and 262144-row Query
against two train rows for both norms. All run in ordinary and ASan+UBSan variants,
including the large-query case (no runtime-driven omission needed). Fault hooks
11/12/13/14 exercise all five exception categories, cleanup and atomic publication.
No production fault-control symbol, suppression, fake handle or double destroy.

Task 005 adds **9 registrations**, total **53**, preserving the existing 44:
WTA2/3/4 exact fixtures plus exhaustive independent ORB bit/cell distance oracles,
boundaries/ties/zero-one-many buckets and mapping, compatible empties, incompatible
norms including all empty combinations, invalid thresholds even for empties with
preserved inputs, one-row train/empty flattened/norm maximum, lifetime, and
returned Ada train index **262145** for both norms. The fixture child exists only
in the test crate, preserving pairing; it is not a production descriptor generator.

Raw actual-shim variants additionally exercise radius null outputs/inputs,
selectors/schema/N-D/threshold negatives, cleared getter outputs, owned empties,
ROI/lifetime, both maximum distances and direct high train indices. Checkpoints
15/16/17/18 cover five exception categories, private staging/atomic publication
and empty cleanup. Checked production count/layout helpers exercise overflow
without manufacturing invalid handles or allocating INT32_MAX matches: this is
helper evidence, **not** a billions-of-results native execution. Sanitizer
qualification remains separate from AUnit registrations; see validation record.
