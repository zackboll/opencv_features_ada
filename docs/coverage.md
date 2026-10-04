# Features binding coverage

This is a handwritten capability inventory, not a generated header census.
"Implemented draft" means source is present; native validation is outstanding.

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
