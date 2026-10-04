# Ada design

Use shared OpenCV value types and OpenCV.Core.Mat. Keep C pointers, status
codes, STL and C++ handles out of the ordinary public API. Detectors own
native identity through limited-controlled objects. Feature_Set is limited
and private to preserve keypoint/descriptor pairing.

Use typed enums/records, explicit index conversions and documented errors.
Check counts before result-sized allocation; prefer heap-owned internal
collections to unbounded stack scratch arrays. Preserve row/keypoint order.
Do not assume a native requested feature target is a guaranteed output bound.
Expose mutation/copy semantics explicitly. Default-declared resources must
have a clear state; finalization must be safe, idempotent and exception-free.
