with OpenCV.Features.Matching;

package OpenCV.Features.Correspondences is
   --  SPDX-License-Identifier: Apache-2.0
   type Point_Correspondence is record
      Query_Index : Positive;
      Train_Index : Positive;
      Query_Point : OpenCV.Float32_Point;
      Train_Point : OpenCV.Float32_Point;
      Distance    : Matching.Binary_Descriptor_Distance;
   end record;

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
   function From_Matches
     (Query   : Feature_Set;
      Train   : Feature_Set;
      Matches : Matching.Descriptor_Match_Array)
      return Point_Correspondence_Array;
end OpenCV.Features.Correspondences;