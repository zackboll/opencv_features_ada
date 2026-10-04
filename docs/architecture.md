# Architecture decisions

## Module ownership

`opencv_features` is a separate Ada crate. The public package name does not
change when native OpenCV calls the module `features2d` (4.x) or `features`
(5.0). Source references are recorded in `source-provenance.json`.

The module owns feature detection, descriptions, and binary descriptor
matching. It does not own image preprocessing, capture, serialization,
geographic coordinates, DTED interpolation, calibration, robust pose
estimation, or estimator/fusion policy. Do not introduce dependencies on
Ada Imgproc or Geometry merely because native Features includes other native
headers or links transitively to other OpenCV libraries.

The three reference repositories are guides, not templates to copy blindly.
Core defines shared numeric/point types and the Mat bridge; Imgproc shows how
a module actually consumes that bridge. Geometry demonstrates Ada-owned
variable-length results and version-normalized module ownership, but its
no-Mat/no-Core-shim restriction is specific to Geometry and does not apply
to image-based Features.

## Public API and invariants

`OpenCV.Features` owns `Keypoint`, `Binary_Descriptor_Norm`, and a limited,
private `Feature_Set`. `OpenCV.Features.ORB` owns a limited-controlled
`Detector`. The detector is created explicitly; its default state is
unready. `Close` is idempotent and finalization calls it.

Every returned feature set has exactly one descriptor row per keypoint,
unless empty, in which case its descriptor Mat is empty. The Ada index is
one-based and the native row is zero-based. The explicit conversion method
checks bounds. No native indices are silently exposed as Ada indices.

Applications cannot separately replace keypoints or the stored descriptor
matrix. `Keypoints` copies the values; `Descriptor_Copy` deep-clones pixels.
The private vector avoids an unbounded stack scratch array during extraction.
The public array-copy getter can allocate a large function result; callers
with large collections should use `Count`/`Point` to avoid that copy.

`OpenCV.Features.Matching` borrows the private stored Mat through nested Core
scoped callbacks without copying descriptors. A local native BFMatcher and
RAII staging result never escape. The result guard destroys native storage
after copying validated plain values into an Ada array, including on failure.
The public API exposes no matcher identity or writable descriptor view.
Semantic selectors stay private; Required_Norm supplies automatic selection.
Ascending query order is independently enforced below the Ada API. Native
schema/count/index/integer-distance checks precede publication and allocation.
The public array return can require a large function result; it does not use
an additional unbounded stack scratch array. See `bfmatcher-source-review.md`.

## Boundary and lifecycle

Radius matching reuses the one-best flat C record and result get/destroy ABI,
not KNN2 pairs or nested vectors. CPU BF radiusMatch executes locally with no
masks/cross-check and compactResult=false. Outer buckets retain query gaps;
the shim validates all indices/imgIdx, exact norm-bounded/inclusive distances,
distance order, per-query train uniqueness and checked flat count before atomic
publication. Actual-count staging reserves no unbounded Cartesian product.
Integer thresholds 1..256 (Hamming) / 1..128 (Hamming2) are checked before empties;
zero rejects. Radius direct indices have no KNN 18-bit train cap. Native full
distance storage has checked size_t arithmetic but ordinary memory failures
remain possible. Scoped Core borrowing, RAII staging and owned Ada conversion
remain unchanged. See `radius-matcher-source-review.md` for immutable evidence.

KNN2 has its own five-int32 C record, opaque staging handle, getter and destructor,
not an overloaded one-best result or persistent matcher. Both languages use RAII
to release staging on conversion/publication failure. The shim verifies outer
count = Query rows, each bucket length = 2, imgIdx=0, expected ascending query row,
distinct bounded train indices, finite integral norm-bounded distances and nearest
<= second. Ada repeats pair/count/order checks before one-based conversion.
For KNN2, Train <=262143 derives from packed train indexing; Query has no 18-bit cap.
Compatible empties bypass native matching, after norm compatibility validation;
one-row Train with nonempty Query rejects. K=2 never combines with cross-check,
whose native implementation requires K=1.

Ratio policy stays entirely in Ada value operations. There is no default threshold:
0 < r < 1 is validated positively (NaN/nonfinite cannot establish validity), even
for empty input. Strict nearest < r*second rejects ties and 0/0 duplicates. The
filter copies nearest matches only, preserving input order, with empty bounds
1..0. Ratio is not confidence/probability; no geometric verification is implied.

`OpenCV.Features.Internal` and `.Internal.C_API` are ordinary child packages
under `src/internal`, matching Imgproc's implementation organization. Ada
private-child visibility would prevent the Features and ORB bodies from
with-ing the nested C API. Implementation use remains in bodies; no C ABI
types or raw pointers are added to the normal public Features API.

1. Ada validates image semantics and the public configuration.
2. The private interop calls a fixed-width C ABI. No C++ ABI types cross it.
3. The shim independently validates ABI selectors, Core handles, image/mask
   shape and type, and the fixed structural profile's arithmetic envelope.
4. The shim clones the source and optional mask before native extraction.
5. A private result owns native descriptors and plain packed keypoint records.
   No borrowed input header is retained.
6. Ada validates the returned count before reserving its private vector.
   Keypoints are copied by explicit field conversion, not by reinterpreting
   public Ada records. For this first slice the copy is one C call per point;
   bulk transfer is a future measured optimization, not a guessed capacity.
7. Through `With_Output_Handle`, the shim assigns descriptor storage to the
   actual Core-owned Mat header. No application Mat wrapper is allocated here.
8. A local limited-controlled guard destroys the staging result even when
   Ada allocation or conversion fails. Incomplete results never escape.

The native descriptor buffer becomes reference-counted storage held by Core
when its header is assigned. Destruction of the temporary native result does
not invalidate that storage. Core bridge pointers exist only in their
callbacks. Input/output header resolution uses the installed authoritative
header, never a copied local version.

## Validation and exceptions

Use `OpenCV.OpenCV_Error` for binding/native errors. Language-defined subtype
checks still raise their normal Ada exceptions; for example, passing zero to
a `Positive` formal can fail before entering an operation. Do not pretend
all possible Ada failures are OpenCV errors.

C++ functions contain OpenCV, allocation, standard, and unknown exceptions.
Error text is a bounded thread-local buffer. Destructors never throw or
replace the diagnostic from the failed operation. Opaque pointers from C
callers must be live and valid; null checks are not arbitrary-pointer
validation, and no binding can infer the lifetime of an invented pointer.

The bootstrap's guards are not a formal proof of native OpenCV. Do normal
source review, sanitizers, boundary fixtures, and practical regression work.
Do not declare an entire native implementation safe because one guard or
one synthetic test passes.

## Platform boundary

Linux follows GNU g++/libstdc++ with a static-PIC C++ shim. macOS follows
Imgproc's GPR-driven Apple clang++/libc++ relocatable shim and Core closure.
Windows follows the external MSYS2/MinGW DLL and explicit import library
path, with the native compiler from the same prefix as OpenCV. The native
runtime is prepended only for running a test/program, not for compiling Ada.

No global OpenCV thread count, OpenCL setting, random seed, or process-wide
configuration is changed by library calls. Sharing one detector for
concurrent extraction/Close is not supported. Test policy must not silently
turn a global setting change into a public runtime side effect.
