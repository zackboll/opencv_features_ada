# Candidate correspondences

After matching, a geometry stage usually needs *where* the matched features
are, not just their indices.
[OpenCV.Features.Correspondences](api:OpenCV.Features.Correspondences) turns
accepted matches into Ada-owned 2-D point pairs. The conversion is pure Ada: it
reads the sets through the public `Count` and `Point` accessors and makes no
native call.

## Converting matches

[From_Matches](api:OpenCV.Features.Correspondences.From_Matches) takes the query
set, the train set and an array of accepted
[Descriptor_Match](api:OpenCV.Features.Matching.Descriptor_Match) values. Each
result element is a
[Point_Correspondence](api:OpenCV.Features.Correspondences.Point_Correspondence)
with:

| Field | Value |
| --- | --- |
| `Query_Index`, `Train_Index` | The match's one-based keypoint indices, copied |
| `Query_Point` | `Point (Query, Query_Index).Position`, an exact Float32 copy |
| `Train_Point` | `Point (Train, Train_Index).Position`, an exact Float32 copy |
| `Distance` | The match's descriptor distance, copied |

The matches can come from `Nearest` or `Mutual_Nearest` matching, from KNN2
candidates selected with `Filter_By_Ratio`, from radius matching, or be supplied
by the application, as long as they refer to these two sets. Raw two-nearest
candidates cannot be passed directly; select matches first. The complete
`orb_match_synthetic` example in the Binary matching guide converts
ratio-accepted KNN2 matches this way.

## Guarantees

- Every query and train index is checked against its set's `Count` before any
  result is built. An index beyond its set raises `OpenCV_Error`, and nothing is
  returned.
- Results have bounds `1 .. Matches'Length` (for any bounds of `Matches`), keep
  the input order, and keep every duplicate. Nothing is sorted, deduplicated or
  filtered here. An empty `Matches` returns `1 .. 0` whatever the sets contain.
- Descriptor norms do not need to agree, and distances are not revalidated, so
  manually supplied matches are accepted as given.
- Positions are copied without arithmetic, rounding, normalization or offsets.
  Each point stays in the pixel frame of the image or Region its detector
  processed; relating the two frames is the application's responsibility.
- `Distance` is descriptor metadata. It is not a confidence, probability,
  geometric residual or reprojection error.
- Inputs are unchanged. The results are ordinary Ada values that hold no
  reference to the sets, detectors, Mats or native storage.

## Handing off to geometry

Correspondences are *candidates*, not verified inliers: no RANSAC, homography,
fundamental or essential matrix, epipolar check, pose recovery or other
geometric verification happens in Features. Both points are
`OpenCV.Float32_Point` values from the shared Core root package, so an
application can copy them into the inputs of its own Geometry or Calib3D stage
(for example a robust estimator that decides which pairs are inliers). Features
has no Ada dependency on those packages; the dependency direction is from the
application to both.

Next: the Ownership and lifecycle guide.
