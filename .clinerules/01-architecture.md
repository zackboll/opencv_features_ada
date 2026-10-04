# Architecture

Handwritten thick Ada -> private Ada interop -> stable C ABI -> C++17 shim.
Public packages stay version-independent: OpenCV.Features and its children.
Core owns Mat wrappers, shared scalar/point types and the scoped module bridge.
Only the Core Ada crate is a production Ada dependency. Do not copy its bridge,
redeclare its root types, or add an Ada Imgproc/Geometry dependency.
Native library dependencies are not Ada crate dependencies.

OpenCV 4 maps to native features2d; OpenCV 5.0 maps to features. Native version
handling stays below the public Ada API. Later native versions require review.
No image ingestion, DTED, geographic transforms, calibration, PnP or estimator
policy belongs here. No production generators or mechanical C++ API mirroring.
