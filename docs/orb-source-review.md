# Fixed-profile ORB source review — Task 002

## Scope and immutable upstream revisions

Official `opencv/opencv` tags, fetched directly rather than inferred from current
documentation:

| Tag | Peeled commit | Native module |
| --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | features2d |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | features2d |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | features |

For each tag, reviewed paths are `modules/<module>/include/opencv2/<module>.hpp`,
`modules/<module>/src/{orb,fast,fast_score,keypoint,feature2d}.cpp`,
`modules/imgproc/src/{resize,thresh,smooth.dispatch}.cpp`, and
`modules/core/src/copy.cpp`. The provenance JSON records URLs and content hashes.
This is a focused review of the reachable CPU Mat fixed profile, not all OpenCV,
optional vendor HALs, all SIMD variants, GPU paths, or arbitrary build options.

Public ORB declarations occur at lines 309/423/444 in the respective headers;
`create` at 346/460/481; `kBytes=32` at 313/427/448. Factories at the ends of
`orb.cpp` construct ORB_Impl with the requested parameters. Its scale factor is
stored as **double**, initialized from the factory's float `1.2f`.
The binding calls the virtual `detectAndCompute` directly, with Mat inputs,
Mat descriptors, an initially empty keypoint vector, and `useProvidedKeypoints=false`.
Supplied-keypoint level inference, non-31 random patches, and color conversion
are not reached. Feature2D's `detect` forwarding is not an extra preprocessing
step on this call. FAST's own override gets the pyramid Mat and mask directly.

## Arithmetic derivation

Let `M=INT32_MAX=2147483647`, requested target `N` in `1..1073741823`,
`W=align_up(columns+64,16)`, `H=8*(rows+64)`. Admission requires both dimensions
at least two and `W*H<=M`, calculated by int64 division in the binding.
In particular `W>=80`, `H>=528`, so `W<=4067203` and
`rows<=3355379`; these dimension bounds are below binary32's exact integer range.
The actual aligned W is a multiple of 16 and no greater than that upper bound.
All listed integer bounds apply to the three tags unless explicitly distinguished.

| Native expression / operation | Native type and intermediate bound | Exclusion argument |
| --- | --- | --- |
| `getScale(level,0,scaleFactor)` uses `pow(scaleFactor,level)` | double power returned as float; levels 0..7, scale 1..less than 3.584 | finite, positive, monotone; no enlargement with firstLevel zero |
| `cvRound(cols/scale)` (4.1), `cvRound(cols*inv_scale)` (4.10/5.0), similarly rows | float division/multiplication then signed int rounding | sizes no larger than source; at 2 pixels and scale 1.2^7, result rounds to 1, not zero; dimensions below 2^24 |
| `patchSize/2`, `cvCeil(halfPatchSize*sqrt(2.0))`, `max(edgeThreshold,descPatchSize,HARRIS_BLOCK_SIZE/2)+1` | int 15, int 22, int 32; border calculation uses Harris constant 9 although responses use block 7 | fixed positive structural constants; borders contain rotated pattern and response/orientation radii |
| `(cvRound(cols/getScale(0,...))+border*2+15)&-16` (4.1); `(int)alignSize(level0_width+border*2,16)` (4.10/5.0) | 4.1 signed int; later size_t width/height before signed casts | W bounds alignment addition/cast; level0 scale exactly 1 |
| `level_ofs.x+wholeSize.width`, `level_ofs.y+level_dy`, `level_ofs.x+=wholeSize.width` | signed int; trial x sum at most 2W; y/height at most H | 2W<M because H>=528; stacking all eight padded levels bounds height, even when native packs several into one row |
| `linfo.y*bufSize.width+linfo.x` | signed int plane offset, less than W*H | rectangle origins and their interiors lie in the allocated padded plane; product guard covers 4.1's signed expression and later tags' identical layerOfs expression |
| Harris `step=(int)img.step`, `i*step+j`, `step+1`, `-step-1`, old `(y0-r+layer.y)*step+x0-r+layer.x` | signed int; step W; block 7, offsets through 6W+6; absolute center offset <WH | H>=528 bounds local row products; 4.10/5.0 additionally check `size_t_step*blockSize+blockSize+1<=INT_MAX` and use size_t for global pointer offset |
| Harris `Ix`, `Iy`, `a+=Ix*Ix`, `b+=Iy*Iy`, `c+=Ix*Iy` | int gradients <=1020 absolute; 49 terms <=50,979,600 absolute | UInt8 pixels and fixed 7x7 response block; products fit int; final Harris polynomial casts to float before multiplying sums |
| orientation `umax(halfPatchSize+2)`, `v*v`, circular symmetry loop | 17 ints; radius 15, v extrema 11; square <=225 | bounded fixed geometry; no user patch/radius values; `sqrt` argument nonnegative in constructed range |
| orientation `u +/- v*step`, `m_10`, `m_01` | signed int row offsets <=15W+15; conservative absolute moment bound 2*31*31*15*255=7,351,650 | border/WH guard covers offsets; UInt8 and fixed radius bound accumulation |
| FAST `makeOffsets`: `dx+dy*rowStride`, 25 entries; `img.cols*3`, `(img.cols+16)*3` scratch terms | int offsets <=3W+3; int scratch factor <=3*(W+16), byte multiplication promoted by sizeof to size_t | stride/dimension bound excludes overflow; score differences -255..255, threshold-table index 0..510; TYPE_9_16 nonmax emits at most one point per pixel |
| `factor=(float)(1.0/scaleFactor)`; `N*(1-factor)/(1-(float)pow((double)factor,8))` | binary32 factor near 0.8333333, initial desired share near 0.2171745N; rounded int | conservative first share <0.22N+1, shrinking subsequent shares; rounding margin far below spare range |
| `sumFeatures+=nfeaturesPerLevel[level]` for seven levels; `max(N-sumFeatures,0)` | signed int; ideal seven-level sum about 0.9394N; conservative <0.95N+1024 at maximum, individually <=N including small N rounding | floating rounding cannot approach M under cap; small N rounds to zero/one, sums at most seven; last subtraction may be negative but never underflows |
| `keypoints.reserve(nfeaturesPerLevel[0]*2)`; Harris `retainBest(...2*featuresNum...)` | multiplication occurs in signed int **before** vector's size_t conversion; each per-level target <=N | retained N cap gives 2N<=M; reserve doubling is reached even with FAST scoring |
| Harris `newAllKeypoints.reserve(nfeaturesPerLevel[0]*nlevels)` | signed int product with 8; <8*(0.22N+1), at cap <1.89 billion | this additional reachable expression also fits M; cap must not be justified only from doubling |
| `(int)keypoints.size()`, counters, `offset+=nkeypoints`, descriptor `_descriptors.create(nkeypoints,32,CV_8U)` | signed int counts; total candidates <=sum(level rows*cols)<=8*rows*cols<WH<=M | image-derived count bound, **not** requested target; response ties in retainBest can exceed target; each loop uses only detected points |
| `pattern.resize(ntuples*tupleSize)` and `pattern[tupleSize*i+k]` | signed int: ntuples=32*4=128; tuple 3/4; size 384/512; WTA2 copies 512 points | selectors restricted to 2/3/4; descriptor loops 32 rows of byte operations, fixed bounded pattern indexes |
| descriptor `iy*step+ix`, rounded rotated pattern | signed int, conservative absolute <=22W+22 | patch radius bound, padded border 32 and edge exclusion 31; point/octave order retained through descriptor construction |
| mask/image resize exact-linear: `interp_y_len*dst_width*cn`, `dx*interp_x.len`, `dy*interp_y.len`, `dst_width*dst_height` | signed int with len=2, cn=1; coefficient buffer sizeof products use size_t | 2W and 2*rows fit; pixel product <WH; source/destination steps are size_t; dimensions positive |
| `copyMakeBorder`: `src.rows+top+bottom`, `src.cols+left+right` | signed int additions, border 32 each side | padded dimensions bounded by H and W; independently cloned ROI headers cannot import outside-source pixels |
| GaussianBlur Size(7,7), sigma 2, fixed kernel dispatch | fixed int kernel dimensions, allocated pixel plane indexed with Mat strides | no tunable kernel arithmetic; image plane envelope remains unchanged; not exhaustive vendor-dispatch review |

The profile helper also evaluates malformed int32 input safely: alignment numerator
is at most M+79, H at most 8*(M+64), both well inside int64; reject before multiplying
large dimensions. No acceptance bound changed. Maximum-target helper tests mirror
the compiled float distribution and include the exact first rejected feature target;
they are supporting empirical evidence, not a formal proof or exhaustive allocation
test. Huge accepted targets can still fail allocations and return an error.

`retainBest` partitions at the boundary response and resizes through **all ties**
(`keypoint.cpp`, 69..89 in 5.0). Native allocations use size_t capacities; preflight
does not guarantee available memory. Shim count/schema checks occur after native
execution and before result publication/Ada result-sized allocation. Descriptor
byte allocation is size_t (32*count), not a promise to fit a signed byte count.

OpenCL is not selected by ordinary Mat input/output in the standard dispatch;
the dedicated qualification driver explicitly disables it. Forced debug OCL,
custom HAL implementations and unrelated native versions require separate review.

## Masks: actual called path

At `ORB_Impl::detectAndCompute`, 4.1/4.10 use `_mask.getMat()` unchanged.
5.0 `orb.cpp` 1039..1044 instead executes
`threshold(_mask,mask,0,255,THRESH_BINARY)` **inside that override**; therefore
normalization is reached by our direct call, not merely by a wrapper we do not call.
This confirms, rather than corrects, the earlier 5.0 normalization statement.

All tags build level zero with `copyMakeBorder(mask,...,BORDER_CONSTANT)`.
Later levels use `resize(prevMask,currMask,...,INTER_LINEAR_EXACT)` followed by
`threshold(currMask,currMask,254,0,THRESH_TOZERO)`. Interior pixels stay unchanged
at level zero; outer border is zero. Later padded copies use BORDER_ISOLATED.
The threshold helper keeps a value only when strictly greater than 254, hence
only 255 survives later levels. Constant exact-linear inputs remain constant.
FAST detects first, then KeyPointsFilter::runByPixelsMask removes points whose
rounded pixel byte is **zero**, not those whose byte is different from 255.

Consequently all-1 gives eligible level-zero points and zero later masks on 4.1
and 4.10; 5.0 normalizes it to all-255 first, equivalent to a full mask throughout.
All-zero excludes detection on every level in all tags. An all-255 interior remains
255 in every resized interior. Mixed stripes 0/1/254/255 have source nonzero
eligibility at level zero in all tags, but later masks legitimately differ.
Tests assert those properties and input preservation, not numerical count equality
across releases. Descriptors may sample outside the eligible detection mask.

## Schema, ownership, failure publication

All tags return descriptorSize=kBytes=32, descriptorType=CV_8U, and defaultNorm
NORM_HAMMING for WTA2 / NORM_HAMMING2 for WTA3/4. Empty points release descriptors.
The binding independently checks N-by-32 UInt8 C1 for nonempty results.

Creation holds the wrapper in unique_ptr until ORB creation succeeds. Extraction
owns clones, descriptor Mat and staging points with RAII; all checks/reserve/copies
precede the final count and result assignments. Point access initializes all fields
before validating, then copies a trivial C record. Export resolves a real Core
output before shallow Mat assignment: invalid argument/bridge rejection leaves the
destination unchanged; no result-owned wrapper or borrowed input is retained.
Mat assignment retains descriptor storage independently of result/detector lifetime.
No broader strong exception guarantee for arbitrary failing upstream Mat assignment
is claimed. Each fallible export is guarded for invalid_argument, cv::Exception,
bad_alloc, std::exception, and unknown exceptions; destruction catches all and does
not replace the last diagnostic. Arbitrary/dangling C pointers are not test inputs.

Test-only checkpoints exercise all five exception categories and selected publication
stages, with bad_alloc at staging/result reserve cleanup, point-copy, and pre-export
checkpoints. This is deterministic exception injection, **not real allocator exhaustion**
or exhaustive failure of every allocation inside OpenCV. Hooks and control symbols
are absent from the production build. No safe ordinary fixed-profile input was found
that deterministically causes cv::Exception after preflight; that mapping is tested
synthetically. Both limits remain explicit.