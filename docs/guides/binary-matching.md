# Binary matching

[OpenCV.Features.Matching](api:OpenCV.Features.Matching) compares the binary
descriptors of two feature sets, a *query* set and a *train* set, with OpenCV's
CPU brute-force matcher. Results are ordinary Ada arrays that own their values.

## Norms and indices

The norm comes from the sets: `Hamming` (0 .. 256 differing bits) for ORB
`Two_Samples` results and `Hamming_2` (0 .. 128 differing 2-bit cells) for
`Three_Samples` and `Four_Samples`. Both sets must carry the same
[Required_Norm](api:OpenCV.Features.Required_Norm); otherwise every operation
raises `OpenCV_Error`, even for empty sets. Distances are exact integers of type
[Binary_Descriptor_Distance](api:OpenCV.Features.Matching.Binary_Descriptor_Distance):
smaller means more similar, and a distance is not a confidence or probability.

Every index in a result is a one-based keypoint index: `Query_Index` refers to
`Point (Query, Query_Index)` and native descriptor row `Query_Index - 1`, and
likewise for `Train_Index`. Compatible empty inputs return an empty array with
bounds `1 .. 0`.

## Nearest and mutual-nearest matching

[Brute_Force_Match](api:OpenCV.Features.Matching.Brute_Force_Match) returns at
most one [Descriptor_Match](api:OpenCV.Features.Matching.Descriptor_Match) per
query keypoint, in ascending `Query_Index` order:

- `Nearest` (the default) gives every query keypoint its closest train
  descriptor, so the result length equals `Count (Query)` when both sets are
  nonempty. Train indices may repeat.
- `Mutual_Nearest` uses OpenCV's cross-check: a pair is kept only when each
  descriptor is the other's nearest neighbor. Queries without a mutual partner
  are omitted, and both query and train indices are unique. This is a symmetric
  consistency check, not a ratio test.

Equal distances do not promise a particular train index. The train set may hold
at most 262143 keypoints, because native one-best and KNN matching pack train
indices into 18 bits; there is no corresponding limit on the query set.

## Two nearest neighbors with an explicit ratio policy

[Brute_Force_KNN_2](api:OpenCV.Features.Matching.Brute_Force_KNN_2) returns,
for every query keypoint, its two nearest train descriptors as a
[Two_Nearest_Match](api:OpenCV.Features.Matching.Two_Nearest_Match). K is fixed
at 2: the train set needs at least two keypoints when the query set is
nonempty, the two train indices are distinct, and the nearest distance never
exceeds the second. These are candidates, not accepted matches.

The application chooses an acceptance policy.
[Filter_By_Ratio](api:OpenCV.Features.Matching.Filter_By_Ratio) keeps a
candidate when `Nearest.Distance < Maximum_Ratio * Second_Nearest.Distance`
and returns its nearest match, in candidate order;
[Passes_Ratio_Test](api:OpenCV.Features.Matching.Passes_Ratio_Test) applies the
same test to one candidate. There is no default ratio: the threshold must
satisfy `0 < Maximum_Ratio < 1`, and NaN or infinite values raise
`OpenCV_Error`, even for empty input. Acceptance is strict, so two zero
distances (duplicate descriptors) are rejected, while a zero nearest distance
with a nonzero second distance is accepted. The ratio is a distinctiveness
heuristic, not a probability or confidence. The example below uses 0.80 as
example application policy only.

## Radius matching

[Brute_Force_Radius_Match](api:OpenCV.Features.Matching.Brute_Force_Radius_Match)
returns every pair whose distance is at most `Maximum_Distance` (inclusive).
The caller must choose the radius: 1 .. 256 for `Hamming` sets or 1 .. 128 for
`Hamming_2` sets. Zero is rejected for every input, including empty ones,
because OpenCV itself rejects a radius that is not above floating-point
epsilon; it is not silently replaced. The flat result is grouped by ascending
`Query_Index` with nondecreasing distance within each query; a query may
contribute zero, one or many matches, and each train row appears at most once
per query. Radius matching has no 18-bit train limit, but native distance
matrices for large inputs can be large and allocation can fail.

## Ownership

Matching borrows each set's descriptor Mat only for the duration of the call
through Core's scoped bridge: nothing is copied or modified, and no
`Descriptor_Copy` is needed. Results own all their values and remain valid after
the sets, the detector and all native staging are finalized. Matching masks,
arbitrary K, FLANN, persistent trained matchers, GPU execution and geometric
verification are not provided.

## Complete example

This is `examples/src/orb_match_synthetic.adb`, built and run by the
repository's CI. It extracts features from a synthetic image and from a
translated copy, then runs both one-best modes, KNN2 with a 0.80 example ratio
policy, the conversion to candidate correspondences, and radius matching with an
example radius of 32.

```ada
with Ada.Text_IO;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features.ORB;
with OpenCV.Features.Matching;
with OpenCV.Features.Correspondences;

procedure ORB_Match_Synthetic is
   package Features renames OpenCV.Features;
   package ORB renames Features.ORB;
   package Matching renames Features.Matching;
   package Bytes renames OpenCV.Core.UInt8_Access;
   use type Matching.Binary_Descriptor_Distance;
   Checker_Parity_Modulus : constant Positive := 2;
   Query_Image : OpenCV.Core.Mat := OpenCV.Core.Create
     (256, 256, (Depth => OpenCV.Core.UInt8, Channels => 1));
   Train_Image : OpenCV.Core.Mat := OpenCV.Core.Create
     (256, 256, (Depth => OpenCV.Core.UInt8, Channels => 1));
   Detector : constant ORB.Detector := ORB.Create;
begin
   Train_Image.Set_To (OpenCV.Make_Scalar (0.0));
   for R in 0 .. 255 loop
      for C in 0 .. 255 loop
         Bytes.Set (Query_Image, R, C, OpenCV.UInt8_Value
                    ((R * 37 + C * 17 + ((R / 16 + C / 16) mod Checker_Parity_Modulus) * 83
                      + R * C mod 251) mod 256));
      end loop;
   end loop;
   for R in 0 .. 247 loop
      for C in 0 .. 250 loop
         Bytes.Set (Train_Image, R + 8, C + 5, Bytes.Get (Query_Image, R, C));
      end loop;
   end loop;
   declare
      Query : constant Features.Feature_Set := ORB.Detect_And_Compute (Detector, Query_Image);
      Train : constant Features.Feature_Set := ORB.Detect_And_Compute (Detector, Train_Image);
   begin
      Ada.Text_IO.Put_Line ("OpenCV " & Features.Native_Version & " / " & Features.Native_Backend);
       Ada.Text_IO.Put_Line ("Query features:" & Natural'Image (Features.Count (Query)));
       Ada.Text_IO.Put_Line ("Train features:" & Natural'Image (Features.Count (Train)));
      for Mode in Matching.Matching_Mode loop
         declare
            Matches : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (Query, Train, Mode);
            Minimum : Matching.Binary_Descriptor_Distance := 256;
            Maximum : Matching.Binary_Descriptor_Distance := 0;
            Zero_Count : Natural := 0;
         begin
            Ada.Text_IO.Put_Line ("Matching mode: " & Matching.Matching_Mode'Image (Mode));
             Ada.Text_IO.Put_Line (Matching.Matching_Mode'Image (Mode) & " match count:" & Natural'Image (Matches'Length));
            for Item of Matches loop
               Minimum := Matching.Binary_Descriptor_Distance'Min (Minimum, Item.Distance);
               Maximum := Matching.Binary_Descriptor_Distance'Max (Maximum, Item.Distance);
               if Item.Distance = 0 then
                  Zero_Count := Zero_Count + 1;
               end if;
            end loop;
            if Matches'Length > 0 then
               Ada.Text_IO.Put_Line ("Zero-distance matches:" & Natural'Image (Zero_Count));
                Ada.Text_IO.Put_Line (Matching.Matching_Mode'Image (Mode) & " distance min/max:" & Matching.Binary_Descriptor_Distance'Image (Minimum)
                                     & " /" & Matching.Binary_Descriptor_Distance'Image (Maximum));
            end if;
         end;
      end loop;
      declare
         --  Example application policy only, not a library default or
         --  recommended navigation constant.
         Ratio : constant OpenCV.Float64_Value := 0.80;
         Pairs : constant Matching.Two_Nearest_Match_Array := Matching.Brute_Force_KNN_2 (Query, Train);
         Accepted : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Pairs, Ratio);
          Points : constant Features.Correspondences.Point_Correspondence_Array :=
            Features.Correspondences.From_Matches (Query, Train, Accepted);
         Minimum : Matching.Binary_Descriptor_Distance := 256;
         Maximum : Matching.Binary_Descriptor_Distance := 0;
      begin
         Ada.Text_IO.Put_Line ("KNN2 candidate count:" & Natural'Image (Pairs'Length));
         Ada.Text_IO.Put_Line ("Ratio threshold (example policy, no library default):" & OpenCV.Float64_Value'Image (Ratio));
         Ada.Text_IO.Put_Line ("Ratio-accepted count:" & Natural'Image (Accepted'Length));
          Ada.Text_IO.Put_Line ("Owned candidate 2-D correspondences:" & Natural'Image (Points'Length));
          Ada.Text_IO.Put_Line ("Candidates only: not geometric inliers; downstream Calib3D/application policy required.");
         for Item of Accepted loop
            Minimum := Matching.Binary_Descriptor_Distance'Min (Minimum, Item.Distance);
            Maximum := Matching.Binary_Descriptor_Distance'Max (Maximum, Item.Distance);
         end loop;
         if Accepted'Length > 0 then
            Ada.Text_IO.Put_Line ("Accepted-distance min/max:" & Matching.Binary_Descriptor_Distance'Image (Minimum)
                                  & " /" & Matching.Binary_Descriptor_Distance'Image (Maximum));
         end if;
      end;
      declare
         --  Explicit absolute distance: example application policy only, not
         --  a library default or recommended navigation threshold.
         Radius_Matches : constant Matching.Descriptor_Match_Array :=
           Matching.Brute_Force_Radius_Match (Query, Train, Maximum_Distance => 32);
      begin
         Ada.Text_IO.Put_Line ("Absolute inclusive radius 32 (example policy), match count:"
                               & Natural'Image (Radius_Matches'Length));
      end;
      Ada.Text_IO.Put_Line ("Descriptor correspondence only: no geometric registration or navigation accuracy claim.");
   end;
end ORB_Match_Synthetic;
```

Run it with:

```sh
alr -n -C examples build
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_match_synthetic
```

Output observed on Linux with OpenCV 4.10.0 (counts depend on the native
OpenCV version):

```text
OpenCV 4.10.0 / features2d
Query features: 406
Train features: 418
Matching mode: NEAREST
NEAREST match count: 406
Zero-distance matches: 86
NEAREST distance min/max: 0 / 99
Matching mode: MUTUAL_NEAREST
MUTUAL_NEAREST match count: 218
Zero-distance matches: 86
MUTUAL_NEAREST distance min/max: 0 / 92
KNN2 candidate count: 406
Ratio threshold (example policy, no library default): 8.00000000000000E-01
Ratio-accepted count: 121
Owned candidate 2-D correspondences: 121
Candidates only: not geometric inliers; downstream Calib3D/application policy required.
Accepted-distance min/max: 0 / 74
Absolute inclusive radius 32 (example policy), match count: 89
Descriptor correspondence only: no geometric registration or navigation accuracy claim.
```

Next: the Candidate correspondences guide.
