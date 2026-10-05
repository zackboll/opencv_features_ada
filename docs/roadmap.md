# Navigation-oriented roadmap

## 001 — qualify the bootstrap

Build the current source against the real pinned Core dependency. Fix any
Ada/GPR/native integration defects with focused tests. Run the 20 AUnit cases
and the raw-ABI coverage added during review; validate OpenCV 4 and 5 and the
three intended platform runtimes. Record commands, versions and actual counts.
Do not label unrun tests PASS. See the complete first task.

## 002 — ORB native qualification

Source/ABI/layout/mask/raw-boundary and actual-shim sanitizer evidence is
recorded in `bootstrap-validation.md`. Installed/consumer Task 001 work remains.

## 003 — brute-force binary descriptor matching

Implemented: a small vertical API consuming two `Feature_Set` values. Borrow their
private Core Mats through scoped handles. Return Ada-owned match values with
validated one-based query/train indices, explicit distances, and well-defined
empty-input behavior. Support Hamming and Hamming_2 based on the stored
metadata and reject incompatible descriptor profiles. Keep native zero-based
indices below the public boundary. Do not silently reuse an L2 default.

Start with direct pairwise input, not a stateful database of reference images.
Add optional mutual one-nearest-neighbor checking as a separately clear policy.
Synthetic translated/rotated imagery should test identity/index mapping,
not pretend to establish terrain-navigation accuracy.

See `bfmatcher-source-review.md` for the exact one-best matching contract and
the native train-index bound. No geometric accuracy follows from this slice.

## 004 — KNN matching and explicit filtering

Implemented fixed **K=2** for binary ORB descriptors, automatic Hamming/Hamming2,
owned nearest/second records and pure-Ada strict ratio filtering. Nonempty query
requires two actual train candidates: one-row train rejects, compatible empties
return 1..0. Train <=262143; no corresponding Query cap. One-based ordered query
pairs have distinct train rows and nearest <= second; tied index order unspecified.
Threshold has no default and must satisfy 0 < r < 1. Strict nearest < r*second
rejects 0/0 duplicates; filtering returns nearest matches only, in candidate order.
Ratio is not confidence/probability, geometric verification or localization.
K=1 mutual cross-check remains a separate alternative, never combined with K=2.
Arbitrary K, masks, float descriptors and persistent matchers remain deferred.

## 005 — bounded radius-based binary matching

Implemented `Matching.Brute_Force_Radius_Match`: explicit absolute integer radius,
inclusive boundary, automatic Hamming/Hamming2 for ORB, no cross-check or masks.
Threshold validity is 1..256 / 1..128 respectively; zero is explicitly rejected,
including empties. Norm compatibility precedes empty results (1..0); one train
row is valid. Flat Ada-owned values sort by query then nondecreasing distance;
tied train order is unspecified. Zero/one/many matches per query, never K=2 or
ratio filtering. All values survive input/detector/native staging destruction.

Source-derived direct radius train indices do not inherit KNN's 18-bit bound;
signed 32-bit native rows/indices and checked flat count/allocation arithmetic
remain. Exact high-index regression returns Ada Train_Index=262145 for both
norms. Exact Hamming/Hamming2 boundaries, missing-query gaps and ties are tested
in native raw/sanitizer and public AUnit paths. See `radius-matcher-source-review.md`
and the validation record for actual executed qualification, not release readiness.
No Calib3D dependency or geometric verification was added. Exact-zero radius,
arbitrary K, matcher databases, persistent matchers, masks, float descriptors,
FLANN, GPU and broader feature/geometry policy remain deferred.

## 006 — owned candidate 2-D point correspondences

Implemented `OpenCV.Features.Correspondences`: one record and one unconstrained
array type, with `From_Matches (Query, Train, Matches)`. Pure Ada, public
`Count`/`Point` only; zero native ABI additions (17 declarations/imports remain).
All one-based query/train indices are preflighted before result construction;
out-of-range positive indices raise `OpenCV_Error`. Exact stored Float32 points,
indices and descriptor distance are copied without arithmetic or coordinate
transforms. Input order and all duplicates survive. Output bounds are
1..Matches'Length, with 1..0 empty success for any empty/full set combination;
nonempty matches against an empty set reject. No norm agreement or norm-specific
distance validation is required. Inputs unchanged; returned Ada values outlive
sets, detectors, descriptor Mats and native staging.

Features **detects descriptors, matches descriptors, and turns accepted matches
into spatial point correspondences**. Calib3D/application geometry **performs
geometric estimation using those points**, with no reverse Features-to-Calib3D
Ada dependency. Nearest, mutual-nearest, ratio-selected KNN2 and radius outputs
all feed the same conversion. Raw KNN2 needs caller selection first.
Descriptor distance remains metadata, not confidence or geometric error; no
geometric inlier status or reference-frame interpretation follows from conversion.

No homography, RANSAC/LMEDS/RHO/USAC, fundamental/essential matrix, epipolar
filtering, pose recovery, PnP, triangulation, calibration, undistortion,
rectification, intrinsics, 3-D points, coordinate/pixel normalization, geospatial
or navigation policy is added. Broader detectors, match masks, arbitrary K,
persistent/FLANN matchers, GPU and optical flow remain deferred.

## Later — expand only after evidence

Measure whether broader ORB pyramid tuning, bulk keypoint transfer, alternative
descriptors, or reference-database indexing is the next real bottleneck.
Potential later features include GFTT (respecting OpenCV 5 module ownership),
SIFT/other descriptors when appropriate, and additional matchers. Do not
create a universal detector class hierarchy before a second concrete use case.

## System integration outside this crate

Reference imagery registration, robust geometric verification, calibration,
projection and PnP need their own module-ownership decisions. DTED loading,
vertical/horizontal datums, map-to-local-metric transforms and terrain
sampling belong in a geospatial/terrain layer, not Features. Temporal
tracking and estimator/fusion logic are separate again.

The first end-to-end milestone is one recorded camera frame with reference
imagery and terrain data producing a checked pose or a defensible rejection.
For a strictly elevation-only reference, correspondence is a different problem
such as terrain-shape/skyline matching. For IR-to-visible references, test
cross-modal correspondence on representative data rather than assuming ORB
will bridge the modality difference.
