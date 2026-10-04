# Binary one-best and fixed KNN2 BFMatcher source review

## Immutable source scope

Official `opencv/opencv` tags, peeled commits:

| Tag | Commit | Native module |
| --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | features2d |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | features2d |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | features |

`source-provenance.json` records immutable URLs, Git blob IDs and SHA-256
content hashes for each reviewed file. Paths are
`modules/{features2d,features}/include/opencv2/{features2d,features}.hpp`,
`modules/{features2d,features}/src/matchers.cpp`,
`modules/core/src/batch_distance.cpp`, and `modules/core/include/opencv2/core/types.hpp`.
The 4.x Hamming implementations are in `modules/core/src/norm.cpp` and
`modules/core/src/stat.simd.hpp`; 5.0 uses `norm.dispatch.cpp` and `norm.simd.hpp`.
This is a CPU Mat/single-train/32-byte binary descriptor review, not exhaustive
optional vendor HAL, OpenCL, GPU or future-version qualification.

## Call path and ownership

The BFMatcher declaration documents Hamming for ORB WTA_K=2 and Hamming2 for
WTA_K=3/4. `BFMatcher::create` constructs a matcher with the supplied norm and
crossCheck. `DescriptorMatcher::match(query, train, ...)` clones an empty
matcher, adds the one train Mat, and calls the collection overload. This is
native shallow Mat-header/reference-count ownership, not a descriptor deep copy.
The collection `match` invokes `knnMatch` with **k=1**, `compactResult=true`,
then `convertMatches`. No persistent train collection survives our local call.

`knnMatch` returns early for an empty query or empty matcher (no train
collection). BFMatcher's implementation also clears/returns for empty query
or absent collections. An **empty train Mat in a one-element collection is
not an absent collection**: it can reach type/column assertions in
`batchDistance`. Native empty-train success must not be assumed from that
early return. The binding deliberately handles valid empties itself: public Ada returns
`Descriptor_Match_Array (1 .. 0)` without calling C; raw C publishes a valid
empty owned result without running BFMatcher. Selectors/schema/norm compatibility
are still validated, and the train count preflight precedes the empty shortcut.

The OpenCL branch in `BFMatcher::knnMatchImpl` requires
`_queryDescriptors.isUMat()`. The supplied query is `cv::Mat`, so this path is
not selected even if process-wide OpenCL is enabled. Production matching never
changes global OpenCL settings. Native input headers are borrowed only inside
nested Core bridge callbacks and are never retained or deleted by Features.

## Integer distance derivation

`BFMatcher::knnMatchImpl` selects **CV_32S** for both binary norms and calls
`batchDistance`. `batchDistHamming` writes `int` distances using
`hal::normHamming(a,b,len)`; `batchDistHamming2` calls the overload with
`cellSize=2`. The former popcounts XOR bits; the latter counts nonzero XOR
2-bit cells. Scalar tables and SIMD paths implement the same reduction.

For 32 bytes:

* Hamming has 32*8 bits: exact integer **0..256**.
* Hamming2 has 32*4 cells: exact integer **0..128**.
* A changed byte 0x00 -> 0x03 contributes Hamming=2, Hamming2=1.
* 0x00... -> 0xFF... contributes Hamming=256, Hamming2=128.

BFMatcher converts `dist` to **CV_32F**, then constructs
`DMatch(qIdx, packedIndex & mask, packedIndex >> shift, distptr[k])`.
The four-argument constructor preserves all four values. IEEE binary32
represents every integer in these small ranges exactly (24-bit precision).
The shim therefore validates finite/integral/ranged float values before
converting them to int32. Public Ada never exposes a floating distance.
Distance is neither probability nor confidence.

## Packed train limit and reverse cross-check

All reviewed BFMatcher implementations define `IMGIDX_SHIFT=18` and
`IMGIDX_ONE=1 << 18`. Before each `batchDistance` call they assert
`trainDescCollection[iIdx].rows < IMGIDX_ONE`. The single train collection
has imgCount=1; the additional `imgCount*IMGIDX_ONE < INT_MAX` check is trivially
satisfied. Thus **Train.Count <= 262143**, with no silent truncation. Both Ada
and C preflight this native limit before execution. It is a native indexing
restriction, not a feature target or heuristic resource budget.

`batchDistance(crosscheck=true)` requires K=1, update=0, no mask and a nonempty
index result. It runs reverse `batchDistance(src2,src1,...,false)` and forward
`batchDistance(src1,src2,...,false)`, then rejects non-mutual candidates.
These inner searches use plain `int` indices and update=0, **not 18-bit packing**.
The reverse path has no `IMGIDX_ONE` assertion. Query rows therefore keep the
native signed-int/count bound, not the train bound. Raw qualification exercises
a real 262144-row Query against a one-row Train in **both modes**.

## Count, order, ties and result checks

With nonempty train, no mask, K=1, `batchDistance` initializes distances to
INT_MAX and indices to -1. Every actual binary distance is at most 256, hence
strictly less than INT_MAX, so every query receives a candidate. Ordinary
matching must emit exactly Query.rows matches. Cross-check may leave -1 indices,
so its count is 0..Query.rows. `convertMatches` copies the one candidate from
each nonempty query bucket.

The current implementation traverses queries in ascending qIdx. The binding
independently sorts by query index and validates strict increase, count, imgIdx=0,
query/train bounds, and distance before publication. Strict increase plus count
equality proves ordinary mode covers each query exactly once. Cross-check also
validates train uniqueness using a private heap-owned bitmap. No distance sort
is performed. Ada repeats count/index/distance/order checks before conversion.

`BatchDistInvoker` visits train rows in ascending order and inserts only when
`d < currentDistance`; this currently favors the first equal-distance candidate.
We deliberately **do not** freeze this implementation detail into the stable
Ada contract. Exact-index oracles avoid ties; self-match tests permit duplicate
descriptors. Mutual nearest is not Lowe's ratio test.

## Boundary qualification and limits

The C record contains three int32 fields, with compiler-derived C sizeof,
alignment and offsetof compared against the actual Ada Size/Alignment/Position.
A C-written record is read field-by-field in Ada. Observed Linux layout is
12 bytes, alignment 4, offsets 0/4/8; those handwritten values are not the proof.

Real Core factory descriptors cover exact distances, one-best/cross-check,
noncontiguous ROI, empty inputs, lifetime, null arguments, invalid selectors,
Float32, multichannel, 31/33-column, N-D, and 262144-row train rejection.
Production and test-hook actual-shim variants run normally and with ASan+UBSan.
Hooks cover all existing exception categories at allocation/native-result/
publication checkpoints, including empty publication cleanup and get clearing.
This is exception injection, not real allocator exhaustion. No invented pointer,
double-destruction, suppression or production fault-control symbol is used.
System Core/OpenCV libraries are not fully sanitizer-instrumented by this probe.

No masks, arbitrary K, radius, float matching, FLANN, persistent matcher,
geometric verification or navigation estimator is implemented in this slice.

## Task 004: K=2 derivation

Re-retrieved all files at the same peeled revisions above and verified every
SHA-256 against the provenance inventory. The reviewed CPU Mat paths in all
three revisions establish the following (not a future-version/vendor-HAL proof):

* Pairwise `DescriptorMatcher::knnMatch(query,train,...,knn)` clones an empty
  matcher, adds the one train Mat and forwards the same knn to its collection
  overload. No supplied mask yields an empty Mat entry; compactResult defaults
  false. The collection overload checks masks, trains and calls `knnMatchImpl`.
* `BFMatcher::knnMatchImpl` requires `_queryDescriptors.isUMat()` for its OpenCL
  branch (also CV_32FC1 in these revisions). Our UInt8 **Mat** inputs do not
  select it. K=2 proceeds through CPU `getMat`, one collection, update=0 and
  `batchDistance(...,knn,...,crossCheck=false)`. Production OpenCL state unchanged.
* `modules/core/src/batch_distance.cpp`: `K = std::min(K,src2.rows)`. Distance
  and index outputs have src1.rows rows and K columns. Requiring Train.rows>=2
  leaves **two columns**. Both norms use CV_32S, initialized INT_MAX, with -1
  indices. Empty mask means every row is eligible; every exact binary distance
  <=256 is below the sentinel. At least two eligible rows fill both columns.
* `BatchDistInvoker::operator()`: each query visits each train row j exactly
  once. It inserts if `d < distptr[K-1]`, shifts entries while `distptr[k] > d`,
  and writes `nidxptr[k+1] = j+update`. Insertion preserves nondecreasing distance
  order. A new train row is inserted once, so retained indices are distinct.
  Equal distances can occupy both columns; current visit order is not a stable
  exact-index public guarantee. No particular tied train ordering is promised.
* Same `IMGIDX_SHIFT=18`, `IMGIDX_ONE=1<<18`, and Train.rows<IMGIDX_ONE assertion
  applies **before** this K=2 `batchDistance` call. Thus Train<=262143. Query is
  the output row/qIdx, not masked/shifted: no K=2-specific 18-bit Query restriction.
  The ordinary native signed-int/count and allocation constraints still apply.
* Hamming uses `batchDistHamming` / `hal::normHamming`; Hamming2 uses
  `batchDistHamming2` with cellSize=2. Norm/stat files and DMatch four-argument
  constructor reviewed again: CV_32S distances convert exactly to CV_32F over
  0..256/0..128. DMatch receives qIdx, packed train low bits, image high bits,
  and rank distance. One collection means imgIdx=0. qIdx loop appends one bucket
  per ascending query row, with two entries from nidx.cols for valid inputs.
* `batchDistance` crosscheck branch asserts **K==1**, update==0, mask.empty().
  KNN2 deliberately constructs BFMatcher(norm,**false**), with no cross-check
  selector. Mutual_Nearest is the distinct K=1 alternative, not ratio filtering.
* Collection empty/query early returns do not imply empty-train-schema safety.
  Binding schema/selector/train checks precede legitimate empty publication;
  public compatible empties bypass C entirely. Norm mismatch precedes empties.
  Nonempty Query + one-row Train rejects before BFMatcher rather than accepting
  native K=min(2,1)=1. Valid raw empties own an empty staging result.

Reference anchors in `matchers.cpp` (line numbers in immutable files): pairwise /
collection knnMatch / BF knnMatchImpl are 589/642/752 (4.1), 589/647/757 (4.10),
593/651/901 (5.0). In all three `batch_distance.cpp`, insertion is around 235-246,
K clamp at 284, crosscheck assertion at 303, norm dispatch around 364-367.
Paths, hashes and revisions remain in `source-provenance.json`; no copied sources.

Shim independently validates outer count=Query.rows, two elements per bucket,
imgIdx=0, expected qIdx, both train bounds, finite/integral/norm-bounded distances,
distinct train rows and nearest<=second before publishing integer records. Ada
rechecks count and ascending qIdx=position before one-based conversion. Staging
owns values and no input headers, so results survive descriptors and matchers.

Compiler-derived C sizeof/_Alignof/offsetof compared to Ada Size/Alignment/Position
and a C-written five-field record establish layout/interchange. Local observation:
size 20, alignment 4, offsets 0/4/8/12/16; handwritten constants are not the proof.

Raw oracles: Hamming and Hamming2 unique 0/1 pairs with a third distance-2 row;
nonzero 1/2 pairs; explicit 0x03 Hamming=2 versus Hamming2=1; equal-distance ties
with distinct valid indices, no exact tie order. Both norms test Train=262143,
unique best row 262142 and second row 262141, and rejection at 262144. Query=262144
against Train=2 executes in ordinary and both sanitizer variants for both norms.

Ratio helpers are pure Ada: explicit threshold 0<r<1 (negated positive validity
rejects NaN/infinities); strict nearest < r*second. Numeric 0, negative, 1 and >1
invalid thresholds tested; no undefined NaN representation fabricated. Exact
1/2 at .50 rejects and .51 passes; ties and 0/0 reject. Filter preserves candidate
order and returns only nearest Descriptor_Match values. No default policy,
confidence/probability, or geometric verification; .80 is example policy only.