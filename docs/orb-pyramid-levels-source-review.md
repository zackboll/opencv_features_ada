# ORB pyramid levels — Task 011 safety review

## Disposition

Task 011-R1 supplies an [all-target conditional certificate](orb-pyramid-levels-arithmetic-r1.md)
and reproducible probes. The original missing mathematical derivation below
is preserved as research history; it is now resolved under explicit numerical
preconditions. The full gate remains unresolved pending Apple/Windows pow and
rounding-path qualification. See the supplemental certificate for current bounds.

`SAFETY_GATE_NOT_ESTABLISHED`: research only. No configurable-level binding
has been added. This is an incomplete qualification, **not** a finding that
OpenCV is unsafe for these level counts. The fixed-eight production profile
and its existing admission behavior remain unchanged.

## Immutable source evidence

The actual `orb.cpp` files were downloaded from the following immutable
revisions, not inferred from API documentation:

| OpenCV | Commit | Path | SHA-256 of downloaded file |
| --- | --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | `modules/features2d/src/orb.cpp` | `dee6e3b4ea60d8176914456722a9a24ae1314113f22f49330ed30f304e1626f6` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | `modules/features2d/src/orb.cpp` | `3874450ed3f9a779f2cf1a20daf544332898d5bcabed30a38071741a6ae5d203` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | `modules/features/src/orb.cpp` | `ac48243150ab9f011f3f122632df10f094597fe728aefcb711659c3f4833c7f9` |

The URL for each file is
`https://raw.githubusercontent.com/opencv/opencv/<commit>/<path>`.
The existing [fixed-profile review](orb-source-review.md) remains historical
evidence; it is not rewritten as configurable-level qualification.

## Reviewed call and parameter storage

All three factories construct `ORB_Impl` with the supplied integer `nlevels`.
The constructor stores it directly and stores the supplied `1.2f` scale factor
as a double. `detectAndCompute` starts from `this->nlevels`. With the binding's
empty keypoint vector and `useProvidedKeypoints=false`, the supplied-keypoint
octave inference branch is not reached. The native setters are not exposed by
the binding. Relevant locations:

| Operation | 4.1.0 | 4.10.0 | 5.0.0 |
| --- | --- | --- | --- |
| `getScale` | 648–651 | 653–656 | 653–656 |
| Distribution | 798–808 | 845–855 | 845–855 |
| First-level reserve | 834 | 881 | 881 |
| Harris doubled target | 852 | 899 | 899 |
| Harris reserve | 900 | 947 | 947 |
| Pyramid layout | 1024–1045 | 1075–1101 | 1079–1105 |
| Descriptor allocation | 1145 | 1201 | 1205 |
| Factory | 1206–1211 | 1262–1267 | 1266–1271 |

## Image-plane envelope: preliminary conclusion

Let `M = 2_147_483_647`, `W = align_up(columns + 64, 16)` and
`H = 8 * (rows + 64)`. Keep the existing dimensions-at-least-two and
`W * H <= M` admission rule, evaluated with checked wider arithmetic/division.
Do **not** replace 8 with the selected level count in this admission rule.

For level counts 1 through 8, the visited octave indices are a subset of 0
through 7. `getScale` returns `float(pow(double(1.2f), level))`; firstLevel
remains zero. These scales are positive and at least one. The old source
rounds `columns / scale`; the newer sources round `columns * inv_scale`.
No new scale or exponent is introduced. The existing dimension/rounding
argument therefore applies to each visited level. At the minimum geometry,
even octave 7 rounds to a positive dimension.

Every padded rectangle is at most `(columns + 64)` by `(rows + 64)`.
Packing fewer rectangles does not require a taller plane than stacking eight
of them. The aligned width remains W. Trial horizontal additions are bounded
by 2W, vertical additions by H, and signed plane offsets by WH. The existing
W/H restrictions also retain the fixed Harris, orientation, FAST and rotated
descriptor row-offset bounds recorded in the fixed-profile review. Independent
ROI snapshots are still necessary; this argument does not authorize retaining
borrowed Core headers.

This establishes why the unchanged **image** envelope is a suitable candidate
for all eight level counts. It is not a feature-target arithmetic proof.

## Feature-target arithmetic: separate evidence and unresolved gate

The current target range is `1 .. 1_073_741_823` (`M / 2`). In all three files:

```cpp
float factor = (float)(1.0 / scaleFactor);
float desired = nfeatures*(1-factor)
              / (1-(float)std::pow((double)factor, (double)nlevels));
int sumFeatures = 0;
for (level = 0; level < nlevels-1; ++level) {
    nfeaturesPerLevel[level] = cvRound(desired);
    sumFeatures += nfeaturesPerLevel[level];
    desired *= factor;
}
nfeaturesPerLevel[nlevels-1] = std::max(nfeatures - sumFeatures, 0);
```

**One level:** the loop is skipped. The sole target is exactly the original
integer N, not `cvRound(desired)`. The initial floating calculation is still
executed, with a nonzero denominator, but is not converted to a feature count.
The unconditional reserve and Harris retain target double N in signed int.
At the existing maximum this is `2_147_483_646`, safely below M. The Harris
reserve is N times 1. Reducing the feature limit solely because binary32
converts the maximum N to `1_073_741_824` would misread this reachable path.

**Levels 2–8:** ideal real-arithmetic first-level shares are
`N / (1 + f + ... + f^(L-1))`, where f is the stored reciprocal factor.
They decrease with L, but `L * first_share` increases. Safety must bound the
actual floating expressions, cvRound, repeated multiplication, signed partial
sums, and the final integer residual. In particular both `2 * target` and
`L * first_target` are evaluated as signed int **before** vector reserve's
size_t conversion. A successful allocation or small-image extraction cannot
substitute for that argument.

A standalone g++ binary32/`std::lrint` probe mirrored the distribution at
N = M/2. It observed:

| L | first target | sum before residual | residual | 2 × first | L × first |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1073741823 | 0 | 1073741823 | 2147483646 | 1073741823 |
| 2 | 585677376 | 585677376 | 488064447 | 1171354752 | 1171354752 |
| 3 | 424776960 | 778757760 | 294984063 | 849553920 | 1274330880 |
| 4 | 345645696 | 873715504 | 200026319 | 691291392 | 1382582784 |
| 5 | 299197920 | 929452800 | 144289023 | 598395840 | 1495989600 |
| 6 | 269066976 | 965609936 | 108131887 | 538133952 | 1614401856 |
| 7 | 248234736 | 990608456 | 83133367 | 496469472 | 1737643152 |
| 8 | 233189392 | 1008663008 | 65078815 | 466378784 | 1865515136 |

These are **observations at one target on one compiler**, not certified
per-level admission bounds. The probe is not linked to OpenCV and does not
establish every supported cvRound implementation or rounding environment.
The missing qualification is a conservative floating-error/rounding bound
for every admitted N for each L=2..8, covering all partial sums and residuals,
with its supported compiler/math assumptions stated and verified. Until that
is recorded, the requested all-level native arithmetic safety gate is not
established. No smaller arbitrary target cap is proposed to conceal this gap.

## Candidate/result counts and descriptors

Native FAST and retainBest can return response ties; the requested N is not
a guaranteed output bound. With L <= 8, the sum of level pixel counts is
bounded by `8 * rows * columns < WH <= M`. This is the separate image-derived
argument for counters, the casts of vector sizes to signed int, and Harris'
nonnegative offset accumulation. Descriptor rows use the final keypoint count;
columns are 32, type UInt8 C1. Descriptor byte allocation uses size_t, not a
signed `32 * count` guarantee, and memory exhaustion remains possible.

Native extraction assigns octave from the visited level loop. Descriptor
computation indexes layerInfo/layerScale with that octave. Any later binding
implementation must validate `0 <= octave < configured_levels` before
publishing results, as well as finite/in-geometry coordinates and paired
descriptor rows. No such production change was made in this research stage.
WTA2 continues to imply Hamming; WTA3/4 imply Hamming2.

## Masks and limitations

4.1/4.10 consume `_mask.getMat()` unchanged. 5.0 performs an initial binary
threshold inside the called ORB override (1039–1044), converting every nonzero
byte to 255. Later resized masks in all three revisions use INTER_LINEAR_EXACT
and THRESH_TOZERO at 254. Only 255 survives those later thresholds. With one
level there is no later mask resize, but the 5.0 initial normalization remains
reachable. Keep portable 0/255 masks and preserve input/mask storage.

This focused review is of the CPU Mat operation, not arbitrary HALs, forced
OpenCL, future native versions, all toolchains, or all upstream allocation
implementations. No feature-count equality across versions, available-memory,
navigation-accuracy, real-time, or formal-proof guarantee is made. Scale-factor,
edge-threshold, first-level and patch-size expansion remain separate work.
