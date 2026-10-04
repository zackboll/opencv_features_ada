package OpenCV.Features.Matching is
   --  SPDX-License-Identifier: Apache-2.0
   type Matching_Mode is (Nearest, Mutual_Nearest);
   type Binary_Descriptor_Distance is range 0 .. 256;
   type Descriptor_Match is record
      Query_Index : Positive;
      Train_Index : Positive;
      Distance    : Binary_Descriptor_Distance;
   end record;
   type Descriptor_Match_Array is
     array (Positive range <>) of Descriptor_Match;

   --  One-based indices map to descriptor rows/keypoints (1 -> native row 0).
   --  Results are ordinary owned Ada values, in ascending Query_Index order.
   --  Norms must agree, even for empty sets: WTA2 uses Hamming (0..256),
   --  WTA3/4 uses Hamming2 (0..128), with exact integer distances.
   --  Nearest returns Count(Query) entries if both sets are nonempty; ties
   --  do not promise a particular Train_Index. Mutual_Nearest uses native
   --  cross-check, with unique query/train indices; it is NOT a ratio test.
   --  Compatible empty inputs return (1 .. 0). Train.Count > 262143 raises
   --  OpenCV_Error (native BFMatcher packs train indices into 18 bits).
   --  No masks, KNN, ratio filtering, confidence score or geometric verification.
   --  Inputs are borrowed, not copied or modified. Concurrent mutation through
   --  implementation interfaces is not supported. Large results allocate an
   --  array function result; normal Ada allocation exceptions remain possible.
   function Brute_Force_Match
     (Query : Feature_Set; Train : Feature_Set;
      Mode : Matching_Mode := Nearest) return Descriptor_Match_Array;
end OpenCV.Features.Matching;