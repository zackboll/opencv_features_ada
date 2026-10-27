# Limitations and roadmap

`opencv_features` deliberately starts small. This guide lists what is fixed,
what is not implemented, and what belongs to other components.

## ORB scale-space limits

The original four-field configuration contains feature target, WTA_K,
Harris/FAST score and FAST threshold. Development after approved 0.1.0 adds
separate immutable scale-space settings: finite scale 1.1..2.0 and 2..16 levels,
default 1.2/eight. Edge threshold 31, first level 0 and patch size 31 remain
fixed. There are no setters. Nondefault targets are conservatively bounded
by INT32_MAX/(2*Levels); image admission checks all upper-level dimensions.
`Maximum_Features` is a requested target, not a strict cap. Very large images
can be rejected by the binding's conservative native size envelope even when
OpenCV itself might accept them (see `docs/orb-contract.md`).

Only ORB is provided. There is no generic detector hierarchy, and no SIFT,
AKAZE, GFTT or float-descriptor support.

## Matching

Provided: brute-force CPU matching of binary ORB descriptors with automatic
Hamming or Hamming_2, nearest and mutual-nearest one-best matching, fixed-K=2
neighbors with explicit ratio filtering, and inclusive radius matching.

Not provided: arbitrary K, matching masks, FLANN or other approximate matchers,
persistent or trained matcher objects and multi-image matcher databases,
GPU/UMat execution, float descriptors, and exact-zero radius matching. One-best
and KNN2 matching accept at most 262143 train keypoints.

## No geometric verification

Features detects and describes features, matches descriptors and converts
accepted matches into candidate 2-D point correspondences. It performs no
RANSAC or other robust estimation, homography, fundamental or essential matrix
estimation, epipolar filtering, pose recovery, PnP, triangulation, calibration,
undistortion or rectification. Descriptor distances and ratio tests are not
confidence measures, and candidates are not inliers. Those decisions belong to
a geometry stage such as an application's Calib3D usage, with no reverse
dependency from Features.

## Separate navigation components

Features does not provide a position fix. Image loading, camera access,
reference-imagery registration, terrain data such as DTED, datums and
geographic transforms, temporal tracking and estimator or fusion logic are
outside this crate and belong to separate layers with their own ownership and
qualification. Synthetic examples demonstrate index and ownership behavior;
they do not establish matching accuracy for real imagery or navigation.

## Roadmap

Further work is driven by evidence rather than scheduled here. Candidate
directions recorded in `docs/roadmap.md` include broader but still reviewed ORB
pyramid configuration, bulk keypoint transfer, additional detectors and
descriptors, additional matchers, and reference-database indexing. Each would
arrive as a separately reviewed, tested slice; none is implied by this release.

Back to the home page for the API reference and the other guides.
