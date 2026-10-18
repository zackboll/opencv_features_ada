--  SPDX-License-Identifier: Apache-2.0

--  Brute-force matching of binary ORB descriptors between two feature sets,
--  through OpenCV's CPU BFMatcher, plus pure Ada ratio filtering. The norm
--  is selected automatically from the sets: Hamming for WTA_K = 2 results,
--  Hamming_2 for WTA_K = 3 or 4 results; both sets must agree. Available
--  operations are one-best matching (Nearest or native cross-check
--  Mutual_Nearest), exactly two nearest neighbors (KNN2), explicit ratio
--  filtering of KNN2 candidates and absolute inclusive radius matching.
--  Input descriptor Mats are borrowed for the duration of a call through
--  Core's scoped bridge; they are neither copied nor modified. Results are
--  ordinary Ada values with one-based keypoint indices and exact integer
--  distances; they own no native storage and stay valid after the inputs,
--  detectors and native staging are finalized. A distance is not a
--  confidence or probability. Arbitrary K, matching masks, FLANN or other
--  approximate matchers, GPU/UMat execution, persistent trained matchers
--  and geometric verification are not provided.
package OpenCV.Features.Matching is

   --  Selection rule for one-best matching (Brute_Force_Match).
   --  @enum Nearest For every query descriptor, the train descriptor at
   --  minimum distance (OpenCV BFMatcher without cross-check). Every query
   --  gets one match when both sets are nonempty; train indices may repeat.
   --  @enum Mutual_Nearest OpenCV BFMatcher cross-check: a query's nearest
   --  train descriptor is kept only when that query is also the train
   --  descriptor's nearest query. Queries without a mutual partner are
   --  omitted; query and train indices are each unique. This symmetric
   --  consistency check is not a ratio test.
   type Matching_Mode is (Nearest, Mutual_Nearest);

   --  Exact integer binary descriptor distance: smaller means more similar.
   --  Hamming distances are in 0 .. 256 and Hamming_2 distances in 0 .. 128;
   --  the type range covers both. It is not a confidence or probability.
   type Binary_Descriptor_Distance is range 0 .. 256;

   --  One accepted query/train descriptor pair.
   --  @field Query_Index One-based keypoint index in the Query feature set;
   --  native descriptor row Query_Index - 1.
   --  @field Train_Index One-based keypoint index in the Train feature set;
   --  native descriptor row Train_Index - 1.
   --  @field Distance Exact distance between the two descriptors under the
   --  sets' shared norm.
   type Descriptor_Match is record
      Query_Index : Positive;
      Train_Index : Positive;
      Distance    : Binary_Descriptor_Distance;
   end record;

   --  Ordinary Ada array of matches. Matching operations return bounds
   --  1 .. N, including 1 .. 0 for an empty result.
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
   --  @param Query Feature set whose descriptors are matched; in Nearest
   --  mode every query keypoint receives exactly one match.
   --  @param Train Feature set searched for the nearest descriptors; at most
   --  262143 keypoints. There is no corresponding 18-bit limit on Query.
   --  @param Mode Nearest (the default) or Mutual_Nearest.
   --  @return Matches with strictly ascending Query_Index and bounds 1 .. N:
   --  N = Count (Query) for Nearest with two nonempty sets, N <=
   --  Count (Query) for Mutual_Nearest, and N = 0 when either set is empty.
   --  @exception OpenCV_Error The two norms differ (also for empty sets),
   --  Train has more than 262143 keypoints, or native matching fails.
   function Brute_Force_Match
     (Query : Feature_Set; Train : Feature_Set;
      Mode : Matching_Mode := Nearest) return Descriptor_Match_Array;

   --  One train neighbor of a query descriptor in a two-nearest result.
   --  @field Train_Index One-based keypoint index in the Train feature set.
   --  @field Distance Exact distance from the query descriptor to this train
   --  descriptor.
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
   --  OpenCV itself rejects radii that are not above floating-point epsilon
   --  for nonempty inputs, so the binding rejects zero for every input
   --  instead of silently substituting a different radius.
   --  @param Query Feature set whose descriptors are matched.
   --  @param Train Feature set searched within the radius; no 18-bit row
   --  limit applies.
   --  @param Maximum_Distance Inclusive absolute distance limit chosen by
   --  the caller: 1 .. 256 for Hamming sets, 1 .. 128 for Hamming_2 sets.
   --  There is no default.
   --  @return Every pair with distance <= Maximum_Distance, grouped by
   --  ascending Query_Index, with bounds 1 .. N; 1 .. 0 when nothing
   --  qualifies or either set is empty.
   --  @exception OpenCV_Error The norms differ, Maximum_Distance is zero or
   --  above the norm's maximum (checked also for empty inputs), or native
   --  matching or allocation fails.
   function Brute_Force_Radius_Match
     (Query : Feature_Set; Train : Feature_Set;
      Maximum_Distance : Binary_Descriptor_Distance)
      return Descriptor_Match_Array;

   --  The two nearest train descriptors of one query descriptor.
   --  @field Query_Index One-based keypoint index in the Query feature set.
   --  @field Nearest Closest train neighbor.
   --  @field Second_Nearest Next closest train neighbor: its Train_Index
   --  differs from Nearest's and its Distance is at least Nearest.Distance.
   type Two_Nearest_Match is record
      Query_Index    : Positive;
      Nearest        : Binary_Neighbor;
      Second_Nearest : Binary_Neighbor;
   end record;

   --  Ordinary Ada array of two-nearest candidates. Brute_Force_KNN_2
   --  returns one per query keypoint, with bounds 1 .. N.
   type Two_Nearest_Match_Array is
     array (Positive range <>) of Two_Nearest_Match;

   --  Exactly K=2, without cross-check. Norm compatibility is checked before
   --  empties. Compatible empties return (1 .. 0); a nonempty query with one
   --  train row raises OpenCV_Error. Train.Count <= 262143; no corresponding
   --  18-bit Query limit. Otherwise Length = Query.Count, in ascending query
   --  order. One-based train indices are distinct, nearest distance <= second,
   --  exact Hamming 0..256 / Hamming2 0..128. Ties have no fixed train ordering.
   --  Owned Ada values survive all inputs and native staging. Inputs unchanged.
   --  The result carries candidates only; apply an explicit caller policy,
   --  such as Filter_By_Ratio, before using pairs as matches.
   --  @param Query Feature set whose descriptors are matched.
   --  @param Train Feature set searched for two neighbors; it needs at least
   --  two keypoints when Query is nonempty, and at most 262143.
   --  @return One candidate per query keypoint, with Query_Index I at
   --  position I and bounds 1 .. Count (Query); 1 .. 0 when either set is
   --  empty.
   --  @exception OpenCV_Error The norms differ (also for empty sets), Train
   --  has more than 262143 keypoints, a nonempty Query meets a one-keypoint
   --  Train, or native matching fails.
   function Brute_Force_KNN_2
     (Query : Feature_Set; Train : Feature_Set)
      return Two_Nearest_Match_Array;

   --  Pure Ada mechanics, no default application policy. OpenCV_Error unless
   --  0 < Maximum_Ratio < 1 (also rejects NaN/nonfinite). Strict acceptance:
   --  nearest < Maximum_Ratio * second, using floating integer conversion.
   --  Thus 0/0 duplicate descriptors reject. Ratio is not confidence/probability.
   --  The test only compares the two distances of one query as a
   --  distinctiveness heuristic; its outcome depends on the caller's
   --  threshold and is not a calibrated likelihood. A zero nearest distance
   --  passes whenever the second distance is nonzero.
   --  @param Candidate Two-nearest candidate to test.
   --  @param Maximum_Ratio Caller-chosen threshold, strictly between 0 and 1.
   --  @return True when Nearest.Distance < Maximum_Ratio *
   --  Second_Nearest.Distance.
   --  @exception OpenCV_Error Maximum_Ratio is not in the open interval
   --  0 .. 1, including NaN and infinities.
   function Passes_Ratio_Test
     (Candidate : Two_Nearest_Match; Maximum_Ratio : OpenCV.Float64_Value)
      return Boolean;

   --  Returns nearest matches only, preserving candidate order. Validates the
   --  threshold even for empty input; empty/all-rejected returns (1 .. 0).
   --  No native calls or geometric verification. Normal Ada allocation errors
   --  remain possible for array results, as for Brute_Force_Match.
   --  @param Candidates Two-nearest candidates, normally from
   --  Brute_Force_KNN_2.
   --  @param Maximum_Ratio Caller-chosen threshold, strictly between 0 and 1;
   --  applied to every candidate exactly as Passes_Ratio_Test.
   --  @return The Query_Index, Nearest.Train_Index and Nearest.Distance of
   --  each accepted candidate, in candidate order, with bounds 1 .. N.
   --  @exception OpenCV_Error Maximum_Ratio is not in the open interval
   --  0 .. 1, including NaN and infinities, even for empty Candidates.
   function Filter_By_Ratio
     (Candidates : Two_Nearest_Match_Array;
      Maximum_Ratio : OpenCV.Float64_Value) return Descriptor_Match_Array;
end OpenCV.Features.Matching;
