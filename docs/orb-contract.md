# Initial ORB contract and native review boundary

## Public profile

The initial configuration exposes only maximum/requested feature target,
WTA_K (two/three/four samples), HARRIS/FAST score selection, and a FAST
threshold of 0 through 255. Feature target must be positive and no greater
than INT32_MAX/2. This last restriction covers native doubling of per-level
retained feature targets; it is not an assertion that the actual output
never exceeds the requested target when responses tie.

Structural settings are fixed: scaleFactor=1.2f, nlevels=8,
edgeThreshold=31, firstLevel=0, patchSize=31. Broader structural configuration
is intentionally deferred, not silently accepted. Fixed defaults reduce the
first review/test surface; they are not claimed optimal for navigation.

Source and optional mask must be nonempty 2-D UInt8 C1. Geometry must match.
The source is at least 2x2 so eight default pyramid levels do not round a
source dimension to zero at the last level. Empty images are errors;
featureless valid images are empty successful results.

Inputs and masks are cloned separately. Use **0/255 binary masks** for the
portable baseline. Other UInt8 mask values are accepted and forwarded
unchanged, not silently normalized by the binding. In reviewed OpenCV
4.1.0 and 4.10.0, level zero preserves nonbinary values, while later resized
masks are thresholded at 254 with THRESH_TOZERO: only 255 survives. OpenCV
5.0.0 first thresholds the incoming mask to 0/255 **inside the called
ORB_Impl::detectAndCompute override**, then uses the same pyramid policy.
Thus an all-1 mask permits only octave-zero detections on these 4.x tags;
on 5.0 it is equivalent to all-255. Native regression fixtures cover all-1
and spatial 0/1/254/255 stripes alongside existing zero/full masks. They
assert eligibility, octave behavior and preservation, not cross-release counts.

A mask governs detection eligibility, not whether every sample in a
feature's descriptor patch came from inside the mask. Region coordinates
are local. Source/mask mutation during extraction is not supported.

## Native arithmetic envelope

`cpp/orb_profile.hpp` admits a conservative subset, not OpenCV's exact
acceptance set. With the fixed profile, the native border is 32. Every
pyramid level is no larger than the input. Define

```
W = align_up(columns + 64, 16)
H = 8 * (rows + 64)
```

Both bounds and their product must fit a signed 32-bit integer. The helper
uses signed 64-bit arithmetic and a division-based product check. Stacking
all padded levels vertically is an upper bound on the packed pyramid's
height; no assumption that an allocation actually reaches H is made. The
product bound also contains the fixed-radius row-offset products. Large
images that OpenCV might accept can be rejected by this bootstrap envelope.

The pure C++ tests exercise negative/zero input, INT32 extrema, normal HD
and UHD shapes, and an exact admission boundary. ASan/UBSan results for
this helper do **not** establish sanitizer coverage of native ORB.

## Result contract

Native output is checked before publication: representable count, finite
keypoint coordinates/size/angle/response, coordinates inside the input,
positive keypoint size, valid fixed-profile octave, and N-by-32 UInt8 C1
descriptors for N nonzero keypoints. Empty output must have no descriptors.
Native class IDs and response values are preserved, not normalized.

WTA_K=2 implies Hamming. WTA_K=3/4 implies Hamming_2. This norm metadata is
carried with the result even when it is empty. It is not a match-quality
probability and does not perform descriptor matching.

## Source-review status

The fixed profile has now been reviewed against official tags **4.1.0,
4.10.0 and 5.0.0**. See [the expression/type/range derivation](orb-source-review.md)
and `source-provenance.json` for immutable revisions, paths, and hashes.
The conservative acceptance bounds are unchanged. The feature cap also
covers the reachable `firstLevelTarget*8` Harris reserve, not just doubling.
Image-derived candidate bounds account for retainBest response ties before
native size-to-int conversions and descriptor row allocation.
This is not exhaustive OpenCV/vendor-HAL review or a guarantee for other tags.

## Boundary qualification

The native AUnit inventory is 33 cases, including direct C exports driven
through scoped Core callbacks and compiler-derived C/Ada size/alignment/all
field offsets plus C-written record interchange. Linux additionally runs
Core's actual C factories through the production shim and a dedicated
test-hook build. No wrapper layout is duplicated or fake pointer dereferenced.
ASan/UBSan compile the actual Features source with warnings as errors;
CPU-only policy is confined to the test driver. System OpenCV/Core libraries
are not thereby fully instrumented or declared sanitizer-clean.
Test hooks inject exception categories and publication-stage failures but
do not exhaust a real allocator or every upstream allocation. See the
validation record for empirical runs and the isolated host AMD ICD finding.

No timing bound, real-time behavior, crash-proof guarantee, image-matching
accuracy, or geographic position accuracy is established by this starter.
