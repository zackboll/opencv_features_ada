--  SPDX-License-Identifier: Apache-2.0

with OpenCV.Features.Matching;

--  Conversion of accepted descriptor matches into candidate 2-D point
--  correspondences between two feature sets. This is pure Ada: it uses only
--  the public Count and Point accessors, makes no native call and adds no
--  C ABI. A correspondence pairs the stored query and train keypoint
--  positions with the match's indices and descriptor distance; it is a
--  candidate for downstream geometry, not a verified inlier. Both points are
--  OpenCV.Float32_Point values from the shared Core root package, so an
--  application can hand them to its Geometry or Calib3D stage (for example
--  a robust estimator that decides inliers) without Features depending on
--  those packages. Coordinates keep each detector input's Region-local
--  pixel frame; relating the two frames is the caller's responsibility.
package OpenCV.Features.Correspondences is

   --  One candidate correspondence, copied exactly from a match and the
   --  stored keypoints of both feature sets.
   --  @field Query_Index One-based keypoint index in the Query set, copied
   --  from the match.
   --  @field Train_Index One-based keypoint index in the Train set, copied
   --  from the match.
   --  @field Query_Point Stored Position of the query keypoint, an exact
   --  Float32 copy in the query image's Region-local coordinates.
   --  @field Train_Point Stored Position of the train keypoint, an exact
   --  Float32 copy in the train image's Region-local coordinates.
   --  @field Distance Binary descriptor distance copied from the match. It
   --  is descriptor metadata, not a confidence, probability, geometric
   --  residual or reprojection error.
   type Point_Correspondence is record
      Query_Index : Positive;
      Train_Index : Positive;
      Query_Point : OpenCV.Float32_Point;
      Train_Point : OpenCV.Float32_Point;
      Distance    : Matching.Binary_Descriptor_Distance;
   end record;

   --  Ordinary Ada array of candidate correspondences. From_Matches returns
   --  bounds 1 .. Matches'Length, in input order.
   type Point_Correspondence_Array is
     array (Positive range <>) of Point_Correspondence;

   --  Pure Ada value copy using only public Count/Point accessors. Validate
   --  every one-based query/train index before constructing the result;
   --  an index beyond its feature count raises OpenCV_Error.
   --  Return bounds are 1 .. Matches'Length, including 1 .. 0 for any empty
   --  Matches (even with empty feature sets or different descriptor norms).
   --  Preserve input order and all duplicates, indices and descriptor distances
   --  exactly. Norm compatibility and norm-specific distance validation are
   --  deliberately not required for manually supplied matches.
   --  Copy stored Float32 positions without arithmetic, rounding, normalization,
   --  offsets or coordinate-frame/Region reinterpretation. Distance is metadata,
   --  not confidence, probability, geometric residual or reprojection error.
   --  Inputs are unchanged; returned ordinary Ada values retain no references
   --  to features, detectors, Mats or native storage. No matching/filtering or
   --  geometric verification occurs: these are candidates, not geometric inliers.
   --  Normal Ada allocation exceptions remain possible for array results.
   --  Matches can come from Nearest, Mutual_Nearest, ratio-filtered KNN2 or
   --  radius matching, or be supplied manually, provided they refer to these
   --  same Query and Train sets. Raw two-nearest candidates are not accepted;
   --  select matches first, for example with Filter_By_Ratio.
   --  @param Query Feature set that the matches' Query_Index values refer to.
   --  @param Train Feature set that the matches' Train_Index values refer to.
   --  @param Matches Accepted matches, with any index bounds; each
   --  Query_Index must be at most Count (Query) and each Train_Index at most
   --  Count (Train).
   --  @return One correspondence per match, in the same order, with bounds
   --  1 .. Matches'Length.
   --  @exception OpenCV_Error A Query_Index exceeds Count (Query) or a
   --  Train_Index exceeds Count (Train); nothing is returned in that case.
   function From_Matches
     (Query   : Feature_Set;
      Train   : Feature_Set;
      Matches : Matching.Descriptor_Match_Array)
      return Point_Correspondence_Array;
end OpenCV.Features.Correspondences;
