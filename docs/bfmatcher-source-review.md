# Binary one-best BFMatcher source review

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

No masks, KNN, ratio, radius, float matching, FLANN, persistent matcher,
geometric verification or navigation estimator is implemented in this slice.