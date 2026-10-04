# Navigation-oriented roadmap

## 001 — qualify the bootstrap

Build the current source against the real pinned Core dependency. Fix any
Ada/GPR/native integration defects with focused tests. Run the 20 AUnit cases
and the raw-ABI coverage added during review; validate OpenCV 4 and 5 and the
three intended platform runtimes. Record commands, versions and actual counts.
Do not label unrun tests PASS. See the complete first task.

## 002 — brute-force binary descriptor matching

Add a small vertical API consuming two `Feature_Set` values. Borrow their
private Core Mats through scoped handles. Return Ada-owned match values with
validated one-based query/train indices, explicit distances, and well-defined
empty-input behavior. Support Hamming and Hamming_2 based on the stored
metadata and reject incompatible descriptor profiles. Keep native zero-based
indices below the public boundary. Do not silently reuse an L2 default.

Start with direct pairwise input, not a stateful database of reference images.
Add optional mutual one-nearest-neighbor checking as a separately clear policy.
Synthetic translated/rotated imagery should test identity/index mapping,
not pretend to establish terrain-navigation accuracy.

## 003 — KNN matching and explicit filtering

Represent per-query results without assuming every query has exactly K
neighbors. Define missing/empty neighbor semantics and grouping. Preserve
query indexing. Keep a ratio threshold and other application filters explicit;
never bake an unexplained ratio constant into the binding. Do not combine
native k=1 cross-check semantics blindly with k=2 matching.

## 004 — expand only after evidence

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
