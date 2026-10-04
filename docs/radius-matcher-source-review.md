# CPU binary radius matcher — immutable source review

Task 005 re-retrieved the official sources before implementation. Tags were
peeled using `git ls-remote`; each downloaded file's SHA-256 was checked against
`source-provenance.json`'s `binary_bfmatcher_source_review` inventory. No upstream
headers/source are copied into this repository. That inventory contains immutable
URLs, paths, Git blob IDs and SHA-256 for the entire reviewed call chain.

| Tag | Peeled commit | Actual matcher path | matchers.cpp SHA-256 |
| --- | --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | `modules/features2d/src/matchers.cpp` | `944e476ed3fe071dca0b586e4cd730949d63f557d6e04a6be0015d21aab6ee8e` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | `modules/features2d/src/matchers.cpp` | `9021d5e2a675e3febfa6d32771873e8e22c5a86b8358134dbc3fccaf969bbee3` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | `modules/features/src/matchers.cpp` | `52b219afc5d71d7b1750bf55726caa47323e582bf3306e28c5c92c636527cbb3` |

The 5.0 path/module was verified from the retrieved tree/file and declaration,
not assumed to be features2d. Reviewed supporting files:

* `modules/{features2d,features}/include/opencv2/{features2d,features}.hpp`:
  direct overload, `compactResult=false` default, norm selectors.
* `modules/core/src/batch_distance.cpp`: SHA-256
  `f3ab7ff2684c24d8a0ef91e87dda017d188c1eb58db66f6ba3f97adcb85fe298`
  (4.1), `0ab18fadec5e83a7bedc69c674f46ca8db889619198afffe56872d47a41d491d`
  (4.10 and 5.0; identical retrieved content).
* `modules/core/include/opencv2/core/types.hpp`: DMatch four-field construction
  and distance-only `operator<`. Hashes respectively
  `8798da3931c223a0068ed64270e9382267fc9d493b9c800adf5e77ada3c3b566`,
  `36492d4be823d05803afa52aa0645adecb28a1bead2e63d6957bf14dee1ec872`,
  `56d6a25199c7fa166aa20e8102c3f3c78e7c53f462184b2f22005810af405db2`.
* 4.x `modules/core/src/norm.cpp` and `stat.simd.hpp`; 5.0
  `norm.dispatch.cpp` and `norm.simd.hpp`: XOR-bit popcounts versus nonzero
  XOR two-bit cells, scalar tables and SIMD reduction (hashes in inventory).

## Conclusions supported by all three pinned CPU implementations

1. Direct query/train `DescriptorMatcher::radiusMatch` clones an empty matcher,
   adds the single train Mat, and calls the collection overload with a vector
   containing the supplied mask Mat. These are shallow native headers held by
   local reference counts, not deep descriptor copies or persistent storage.
   The binding supplies `cv::noArray()` and explicitly `compactResult=false`.
2. Collection overload clears matches, returns early if the matcher or query
   is empty, otherwise asserts `maxDistance > float epsilon`, checks masks,
   trains and calls `radiusMatchImpl`. Thus zero rejects on nonempty execution,
   but native validation can disappear on an empty query. Binding validation
   deliberately precedes **all** empty shortcuts. It rejects zero rather than
   mapping it to epsilon/one, and rejects >128 for Hamming2. Exact-zero radius
   support is deferred. Positive integer thresholds convert exactly to float.
3. An empty train Mat in a one-element collection is not an absent collection;
   it can reach type/schema assertions. Binding handles valid empties itself,
   after norm/threshold/schema checks. Ada returns `(1 .. 0)`; C publishes an
   owned empty result. Nonempty query with one train row is valid.
4. BF CPU path is selected for Mat input. OpenCL branch requires UMat query
   (and CV_32FC1), so it cannot execute for these UInt8 Mat descriptors even
   with OpenCL globally enabled. Production does not change OpenCL state.
   UMat/OpenCL, optional vendor HALs and future releases are not qualified here.
5. BF radius selects CV_32S for Hamming/Hamming2 and calls `batchDistance` with
   **K=0, no index output, update=0, crosscheck=false**. Full Query.rows by
   Train.rows integer distance storage is allocated, then converted to CV_32F.
   `batchDistHamming` writes integer `hal::normHamming` results;
   `batchDistHamming2` uses cellSize=2. For 32 bytes bounds are exactly 0..256
   and 0..128. 0x00 XOR 0x03 contributes 2 bits but 1 two-bit cell. All possible
   distances are exactly representable in binary32 and integer ABI records.
6. CPU loops ascending qIdx and train k, including **`distptr[k] <= maxDistance`**,
   then constructing **`DMatch(qIdx, k, iIdx, distptr[k])`**. One train image
   implies imgIdx=0. Every qualifying row is visited once per query: zero,
   one, or arbitrarily many qualifying matches, not KNN2, ratio, or cross-check.
7. Each bucket is `std::sort`ed by DMatch's distance-only comparison. With
   compactResult=false outer size equals query rows, including empty buckets;
   flattening retains qIdx gaps. Equal distances have no promised train ordering.
   The shim checks outer count, every index/imgIdx, finite/integral/ranged
   distance, inclusive threshold, nondecreasing ordering and within-query train
   uniqueness before publishing. No uniqueness across queries is promised.
8. Unlike BF `knnMatchImpl`, radius has **no IMGIDX_SHIFT/IMGIDX_ONE packing or
   train.rows<2^18 assertion**. Train index is directly k, with signed-int rows
   and indices. Do not apply KNN's Train<=262143 bound to radius. The regression
   uses Train=262145 with the **returned** native index=262144, Ada index=262145,
   for both norms. KNN's overflow rejection remains unchanged.
9. Native dimensions/loops are signed 32-bit. Distance Mat byte products must
   fit size_t; the shim checks Query*Train*4 using division before execution.
   It does not reserve the Cartesian product for staging: it sums actual bucket
   counts with checked addition, bounded by INT32_MAX and vector max_size, then
   reserves the actual count. Ada checks count representability before result
   allocation. These are representation/overflow checks, not a practical memory
   guarantee. Ordinary allocation failures remain errors. No speculative row cap.
10. `batchDistance` asserts matching types/columns and supported depth/output
    combinations, uses row pointers/strides, and dispatches independent query
    ranges. For masks, zero cells get INT_MAX (float conversion far beyond any
    binary radius), nonzero cells compute distance. `checkMasks` requires
    query-by-train UInt8 C1 when supplied. Its empty-mask guard was tightened
    after 4.1; the binding supplies only an empty mask and exposes no mask API.
11. Native assertions/errors throw cv::Exception; vector/Mat allocations can
    fail; none is allowed through the C ABI. The existing guard catches invalid
    arguments, cv::Exception, bad_alloc, std::exception and unknown exceptions.
    Existing fault hooks are extended at pre-allocation, post-match, staging,
    and pre-publication checkpoints. RAII owns all temporary data and result
    outputs remain null/zero until complete validation. Borrowed Core headers
    never escape the call; outputs own plain values independent of all inputs.

Reference anchors in immutable matchers.cpp (direct overload / collection
overload / BF radius impl / inclusive comparison / bucket sort):
**600 / 658 / 903 / 992 / 1007** (4.1),
**600 / 663 / 908 / 997 / 1012** (4.10),
**604 / 667 / 1046 / 1135 / 1150** (5.0).
Supporting batchDistance Hamming kernels are lines 103/125, schema/allocation
274..286, K>0-only insertion 226..246, cross-check assertion 303, dispatch
364..367. DMatch constructors/comparison are readily identifiable by name.

This is source-derived evidence for this small CPU binary/single-train profile,
not formal proof, real-time behavior, geometric inlier status or navigation
accuracy. Runtime/version qualification is recorded separately.