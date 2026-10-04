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
   --  No masks, confidence score or geometric verification.
   --  Inputs are borrowed, not copied or modified. Concurrent mutation through
   --  implementation interfaces is not supported. Large results allocate an
   --  array function result; normal Ada allocation exceptions remain possible.
   function Brute_Force_Match
     (Query : Feature_Set; Train : Feature_Set;
      Mode : Matching_Mode := Nearest) return Descriptor_Match_Array;

   type Binary_Neighbor is record
      Train_Index : Positive;
      Distance    : Binary_Descriptor_Distance;
   end record;

   --  Absolute inclusive radius, not KNN/ratio filtering or cross-check.
   --  Norms must agree, even for empty inputs; automatic Hamming for WTA2,
   --  Hamming2 for WTA3/4. OpenCV_Error unless Maximum_Distance is 1..256
   --  (Hamming) or 1..128 (Hamming2), including empty inputs. Zero is rejected;
   --  exact-zero radius matching is deferred, not mapped to another radius.
   --  Compatible empties return (1 .. 0); one-row Train is valid.
   --  All qualifying matches, flat and Ada-owned: ascending Query_Index,
   --  nondecreasing Distance within each query, unspecified tied train order.
   --  Query/train indices are one-based and bounded by the input counts;
   --  each train row occurs at most once per query, not once globally.
   --  Queries can contribute zero, one, or many matches; length need not equal
   --  Query.Count. Distances are exact integers, <= Maximum_Distance.
   --  No KNN 18-bit train bound: native rows/indices are signed 32-bit; flat
   --  count must fit signed 32-bit and Ada Natural/allocation representation.
   --  Inputs unchanged; owned values survive inputs, detector and native staging.
   --  CPU Mats only; no masks, persistent matcher or geometric policy. Native
   --  full distance matrices/results may be large; allocation can fail.
   function Brute_Force_Radius_Match
     (Query : Feature_Set; Train : Feature_Set;
      Maximum_Distance : Binary_Descriptor_Distance)
      return Descriptor_Match_Array;

   type Two_Nearest_Match is record
      Query_Index    : Positive;
      Nearest        : Binary_Neighbor;
      Second_Nearest : Binary_Neighbor;
   end record;
   type Two_Nearest_Match_Array is
     array (Positive range <>) of Two_Nearest_Match;

   --  Exactly K=2, without cross-check. Norm compatibility is checked before
   --  empties. Compatible empties return (1 .. 0); a nonempty query with one
   --  train row raises OpenCV_Error. Train.Count <= 262143; no corresponding
   --  18-bit Query limit. Otherwise Length = Query.Count, in ascending query
   --  order. One-based train indices are distinct, nearest distance <= second,
   --  exact Hamming 0..256 / Hamming2 0..128. Ties have no fixed train ordering.
   --  Owned Ada values survive all inputs and native staging. Inputs unchanged.
   function Brute_Force_KNN_2
     (Query : Feature_Set; Train : Feature_Set)
      return Two_Nearest_Match_Array;

   --  Pure Ada mechanics, no default application policy. OpenCV_Error unless
   --  0 < Maximum_Ratio < 1 (also rejects NaN/nonfinite). Strict acceptance:
   --  nearest < Maximum_Ratio * second, using floating integer conversion.
   --  Thus 0/0 duplicate descriptors reject. Ratio is not confidence/probability.
   function Passes_Ratio_Test
     (Candidate : Two_Nearest_Match; Maximum_Ratio : OpenCV.Float64_Value)
      return Boolean;

   --  Returns nearest matches only, preserving candidate order. Validates the
   --  threshold even for empty input; empty/all-rejected returns (1 .. 0).
   --  No native calls or geometric verification. Normal Ada allocation errors
   --  remain possible for array function results, as for Brute_Force_Match.
   function Filter_By_Ratio
     (Candidates : Two_Nearest_Match_Array;
      Maximum_Ratio : OpenCV.Float64_Value) return Descriptor_Match_Array;
end OpenCV.Features.Matching;