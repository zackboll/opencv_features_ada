# Ownership and lifecycle

This guide summarizes who owns what, how long values live, and how errors are
reported. The API reference states the same contracts on each declaration.

## Detectors

An [ORB.Detector](api:OpenCV.Features.ORB.Detector) owns one native ORB
detector. It is a limited, controlled type, so it cannot be copied.

- A default-declared detector is not ready.
  [Is_Ready](api:OpenCV.Features.ORB.Is_Ready) is `False`, and extraction or
  [Parameters](api:OpenCV.Features.ORB.Parameters) raises `OpenCV_Error`.
- [Create](api:OpenCV.Features.ORB.Create/1) returns a ready detector.
- [Close](api:OpenCV.Features.ORB.Close) releases the native detector early.
  Closing again, or closing a default-declared detector, has no effect.
  Finalization closes automatically; neither raises an exception.
- Closing a detector does not affect feature sets it produced.

## Feature sets

A [Feature_Set](api:OpenCV.Features.Feature_Set) is limited and private, so it
is never copied by accident. A default-declared set is empty (and reports the
`Hamming` norm). A set returned by a detector owns:

- its keypoints, stored as Ada values in native detector order, and
- one Core-owned descriptor Mat, whose row `I - 1` belongs to keypoint `I`.

No public operation changes a set after construction. It stays valid after its
detector is closed or finalized and after the source image or mask is modified,
and is released when it goes out of scope.

## Copied versus borrowed

| Operation | Inputs | Result |
| --- | --- | --- |
| `ORB.Detect_And_Compute` | Image and mask are copied (snapshotted) before native detection; never modified | New `Feature_Set` owning keypoints and descriptors |
| `Point`, `Keypoints` | Read only | Ada value copies |
| `Descriptor_Copy` | Read only | New caller-owned deep-copy Mat, independent of the set |
| `Matching` operations | Descriptor Mats borrowed for the call only; not copied or modified | Ada arrays owning all values |
| `Correspondences.From_Matches` | Read through `Count` and `Point` | Ada array owning all values |

Application Mats are always created and owned through `opencv_core`. Features
never exposes native pointers, C++ objects or STL containers; internal native
results are staged privately and released on every path, including errors.

## Errors

- Binding and native failures raise `OpenCV.OpenCV_Error` with a descriptive
  message: invalid images or masks, an unready detector, an index beyond
  `Count`, incompatible norms, invalid thresholds or ratios, native limits and
  native exceptions (including native allocation failure).
- Language-defined checks keep their normal Ada exceptions. For example,
  passing zero where a `Positive` index or count is expected raises
  `Constraint_Error` before the operation runs.
- Array results are ordinary function results, so very large results can raise
  `Storage_Error` from Ada allocation.

## Concurrency

Concurrent use is not qualified by the test suite, and no thread-safety
guarantee is made. The API documents these rules: use distinct detectors for
concurrent calls; never close a detector while it is extracting; and never
modify an image, mask or descriptor storage through other interfaces while an
operation is reading it. Library calls do not change OpenCV's global thread
count, OpenCL setting or other process-wide configuration.

Next: the Platform compatibility guide.
