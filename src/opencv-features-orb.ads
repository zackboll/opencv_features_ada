--  SPDX-License-Identifier: Apache-2.0

private with Ada.Finalization;
private with System;

--  ORB (Oriented FAST and Rotated BRIEF) keypoint detection and binary
--  descriptor extraction for 8-bit grayscale Core Mats. The public profile
--  exposes the requested feature target, WTA_K, the Harris/FAST score and
--  the FAST threshold. The structural profile is fixed: scale factor 1.2,
--  eight pyramid levels, edge threshold 31, first level 0, patch size 31.
--  OpenCV 4 runs through the native features2d module and OpenCV 5.0
--  through features; the Ada API is the same for both. Results are
--  OpenCV.Features.Feature_Set values that own their keypoints and
--  descriptors. See docs/orb-contract.md for the reviewed native contract.
package OpenCV.Features.ORB is

   --  Number of points compared to build each descriptor element (OpenCV
   --  WTA_K). It also selects the norm recorded in the result.
   --  @enum Two_Samples WTA_K = 2, the default; descriptors use Hamming.
   --  @enum Three_Samples WTA_K = 3; descriptors use Hamming_2.
   --  @enum Four_Samples WTA_K = 4; descriptors use Hamming_2.
   type Tuple_Size is (Two_Samples, Three_Samples, Four_Samples);

   --  Measure used to rank FAST keypoint candidates before the strongest
   --  are retained. It also determines the meaning of Keypoint.Response.
   --  @enum Harris_Score Rank by the Harris corner response (OpenCV
   --  HARRIS_SCORE); the default.
   --  @enum FAST_Score Rank by the FAST score (OpenCV FAST_SCORE).
   type Score_Kind is (Harris_Score, FAST_Score);

   --  Public ORB parameters. Create validates the ranges that the Ada
   --  subtypes do not express and rejects others with OpenCV_Error.
   --  @field Maximum_Features Requested feature target (OpenCV nfeatures),
   --  1 .. 1_073_741_823 (2_147_483_647 / 2), default 500. It is a target
   --  distributed over the pyramid levels, not a strict cap: a result can
   --  hold fewer keypoints, or more when native responses tie.
   --  @field Tuple WTA_K selection, default Two_Samples.
   --  @field Score Candidate ranking measure, default Harris_Score.
   --  @field FAST_Threshold FAST intensity-difference threshold (OpenCV
   --  fastThreshold), 0 .. 255, default 20; larger values make corner
   --  detection stricter.
   type Configuration is record
      Maximum_Features : Positive := 500;
      Tuple            : Tuple_Size := Two_Samples;
      Score            : Score_Kind := Harris_Score;
      FAST_Threshold   : Natural := 20;
   end record;

   --  Owner of one native ORB detector, configured with a Configuration and
   --  a deliberately small initial profile. Native structural parameters are
   --  fixed at scaleFactor=1.2f, nlevels=8, edgeThreshold=31, firstLevel=0,
   --  patchSize=31. Expanding that surface is a later reviewed slice.
   --  A default-declared Detector is not ready; Create returns a ready one.
   --  Close and finalization release the native detector; both are
   --  idempotent and never raise. Detectors are limited and cannot be
   --  copied. Feature sets produced by a detector remain valid after it is
   --  closed or finalized.
   type Detector is tagged limited private;

   --  Create a ready detector with the given parameters and the fixed
   --  structural profile.
   --  @param Parameters Requested configuration; all defaults when omitted.
   --  @return A ready detector owning its native ORB instance.
   --  @exception OpenCV_Error Maximum_Features exceeds 1_073_741_823,
   --  FAST_Threshold exceeds 255, or the native detector cannot be created.
   function Create (Parameters : Configuration := (others => <>))
      return Detector;

   --  Release the native detector early. Closing a default-declared or
   --  already closed detector has no effect. Afterwards Is_Ready is False,
   --  and Parameters and Detect_And_Compute raise OpenCV_Error. Existing
   --  feature sets are unaffected. Do not close a detector while another
   --  task is extracting with it.
   --  @param Self Detector to close.
   procedure Close (Self : in out Detector);

   --  Whether the detector owns a native ORB instance, that is, it was
   --  returned by Create and has not been closed or finalized.
   --  @param Self Detector to inspect.
   --  @return True when extraction can be attempted.
   function Is_Ready (Self : Detector) return Boolean;

   --  Configuration that was supplied to Create, unchanged.
   --  @param Self A ready detector.
   --  @return The detector's public parameters.
   --  @exception OpenCV_Error The detector is not ready.
   function Parameters (Self : Detector) return Configuration;

   --  Detect ORB keypoints anywhere in the image and compute their binary
   --  descriptors. Image: nonempty UInt8 C1, two dimensions, at least 2x2.
   --  The fixed-profile native arithmetic envelope is checked in the shim;
   --  see docs/orb-contract.md. The image is snapshotted before native
   --  detection: a Region is an isolated logical image, returned coordinates
   --  are local to it, and a noncontiguous Region gives the same result as
   --  its packed clone. Inputs are unchanged on success and failure. A valid
   --  image without detectable features returns an empty set, not an error.
   --  Count of the result is the actual number produced, which can differ
   --  from Maximum_Features. Use distinct detectors for concurrent calls.
   --  Concurrent mutation of source storage, or Close during extraction, is
   --  not supported.
   --  @param Self A ready detector.
   --  @param Image Two-dimensional UInt8 single-channel image, at least 2x2
   --  and within the conservative native size envelope.
   --  @return A new feature set that owns its keypoints and descriptors and
   --  records the norm implied by the detector's Tuple.
   --  @exception OpenCV_Error The detector is not ready, the image is
   --  empty, has the wrong type, rank or size, exceeds the native envelope,
   --  or the native extraction fails.
   function Detect_And_Compute
     (Self : Detector; Image : OpenCV.Core.Mat) return Feature_Set;

   --  Detect only where Mask is nonzero, then describe the detected
   --  keypoints. The mask controls where keypoints may be detected; it does
   --  not restrict which pixels a descriptor patch samples. Mask must match
   --  the image geometry and type: a two-dimensional UInt8 single-channel
   --  Mat with the image's rows and columns. Image and mask are
   --  independently snapshotted; neither is modified.
   --  An all-zero mask yields an empty set. For portable results use only
   --  0 and 255. Other nonzero values are passed through unchanged. In the
   --  reviewed OpenCV 4.1.0 and 4.10.0 sources they count at pyramid level 0,
   --  but only 255 survives into later levels; OpenCV 5.0.0 first maps every
   --  nonzero value to 255. Thus an all-1 mask allows only octave-0 keypoints
   --  on those 4.x releases but behaves like an all-255 mask on 5.0. All
   --  other rules match the unmasked overload.
   --  @param Self A ready detector.
   --  @param Image Two-dimensional UInt8 single-channel image, at least 2x2
   --  and within the conservative native size envelope.
   --  @param Mask Detection mask with the same rows, columns and type as
   --  Image.
   --  @return A new feature set restricted to keypoints detected inside the
   --  mask.
   --  @exception OpenCV_Error The detector is not ready, the image or
   --  mask is invalid, their geometries differ, the native envelope is
   --  exceeded, or the native extraction fails.
   function Detect_And_Compute
     (Self : Detector; Image, Mask : OpenCV.Core.Mat) return Feature_Set;

private
   type Detector is new Ada.Finalization.Limited_Controlled with record
      Handle : aliased System.Address := System.Null_Address;
      Config : Configuration := (others => <>);
   end record;

   --  Finalization closes the detector exactly as Close does.
   --  @param Self Detector being finalized.
   overriding procedure Finalize (Self : in out Detector);
end OpenCV.Features.ORB;
