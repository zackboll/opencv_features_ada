# Architecture decisions

## Module ownership

`opencv_features` is a separate Ada crate. The public package name does not
change when native OpenCV calls the module `features2d` (4.x) or `features`
(5.0). Source references are recorded in `source-provenance.json`.

The module owns feature detection, descriptions, and future descriptor
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

Future matching code, as a child of Features, may borrow the private stored
Mat through Core's scoped module bridge. It must not bypass ownership by
exposing a writable raw descriptor view to applications.

## Boundary and lifecycle

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
