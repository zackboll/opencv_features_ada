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
unchanged, not silently normalized by the binding. In the reviewed OpenCV
4.10.0 source, resized masks are thresholded at 254 on later pyramid levels;
in OpenCV 5.0.0, the incoming mask is first thresholded to 0/255. Consequently,
a mask filled with 1 is not promised to produce equivalent results across
these versions. This behavior still needs a native regression fixture in
Task 001. The oldest 4.1 target has not been source-qualified here.

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

The following official upstream files informed the draft boundary:

- OpenCV 4.10.0 `modules/features2d/include/opencv2/features2d.hpp`
- OpenCV 4.10.0 `modules/features2d/src/orb.cpp`
- OpenCV 5.0.0 `modules/features/include/opencv2/features.hpp`
- OpenCV 5.0.0 `modules/features/src/orb.cpp`

Canonical URLs are recorded in `source-provenance.json`. This is **not** an
exhaustive review of all reachable native code or all supported 4.x tags.
The 4.1.0 source was not successfully retrieved during preparation. Task 001
must review the oldest target, confirm the structural assumptions across
versions, and execute native tests before claiming compatibility. The
manual CI matrix makes that missing qualification visible.

No timing bound, real-time behavior, crash-proof guarantee, image-matching
accuracy, or geographic position accuracy is established by this starter.
