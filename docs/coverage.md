# Features binding coverage

This is a handwritten capability inventory, not a generated header census.
"Implemented draft" means source is present, not fully qualified. The initial
24-case AUnit suite now passes locally on Linux/OpenCV 4.10.0; see
`bootstrap-validation.md` for exact evidence and remaining platform/version,
source-review, sanitizer and ABI robustness gates.

| Native capability | Ada API | Status |
| --- | --- | --- |
| `cv::ORB::create` | `OpenCV.Features.ORB.Create` | Implemented draft, fixed structural profile |
| ORB object lifetime | limited-controlled `Detector`, `Close`, `Is_Ready` | Implemented draft |
| `detectAndCompute`, no supplied keypoints | two `Detect_And_Compute` overloads | Implemented draft, UInt8 C1 and optional mask |
| KeyPoint/descriptor conversion | private `Feature_Set`, getters and row mapping | Implemented draft |
| Native version/backend reporting | `Native_Version`, `Native_Backend` | Implemented draft |
| Separate detect/compute and supplied keypoints | none | Deferred |
| Arbitrary pyramid/patch parameters and setter APIs | none | Deferred |
| BF match and KNN match | none | Next after qualification |
| Other detectors, descriptors and FLANN | none | Deferred |
| UMat/OpenCL/CUDA wrappers | none | Deferred |
| Geometry, PnP, DTED, estimator logic | none | Outside Features |

No unimplemented native entry point is represented by a fake successful stub.

Task 002 adds four AUnit registrations: native nonbinary-mask semantics,
compiler-derived C/Ada keypoint representation/interchange, raw detector
creation, and raw extraction/result access with actual Core callback handles.
The latter covers null outputs/inputs, real wrong-type/shape Mats, initialized
failure outputs, invalid indices, first/last points, descriptor schema and
detector-independent result lifetime. Existing twenty semantic tests remain.

A separate Linux boundary driver additionally uses authoritative Core C
factories, rejects a legitimate external-view output, checks production
absence of fault controls, and exercises test-only exception categories and
publication-stage cleanup. Both production-source and fault-hook variants
run ordinarily and under ASan/UBSan. These assertions are **not additional
AUnit registrations**. C11 header and pure profile helper checks remain
separate static/helper evidence; Python configuration/topology inventory is 20.

Source review is limited to the fixed CPU profile in 4.1.0/4.10.0/5.0.0;
see `orb-source-review.md`. Real allocator exhaustion and installed/clean
consumer relocation are not covered. No matching API was added.
