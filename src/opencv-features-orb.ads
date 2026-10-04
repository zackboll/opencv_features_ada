private with Ada.Finalization;
private with System;

package OpenCV.Features.ORB is
   --  SPDX-License-Identifier: Apache-2.0
   type Tuple_Size is (Two_Samples, Three_Samples, Four_Samples);
   type Score_Kind is (Harris_Score, FAST_Score);

   type Configuration is record
      Maximum_Features : Positive := 500;
      Tuple            : Tuple_Size := Two_Samples;
      Score            : Score_Kind := Harris_Score;
      FAST_Threshold   : Natural := 20;
   end record;

   --  Deliberately small initial profile. Native structural parameters are
   --  fixed at scaleFactor=1.2f, nlevels=8, edgeThreshold=31, firstLevel=0,
   --  patchSize=31. Expanding that surface is a later reviewed slice.
   --  Maximum_Features <= 2_147_483_647/2; FAST_Threshold <= 255.
   --  Maximum_Features is a native requested target, not a strict output cap.
   type Detector is tagged limited private;

   function Create (Parameters : Configuration := (others => <>))
      return Detector;
   procedure Close (Self : in out Detector);
   function Is_Ready (Self : Detector) return Boolean;
   function Parameters (Self : Detector) return Configuration;

   --  Nonempty UInt8 C1, two dimensions, at least 2x2. Image and optional
   --  mask are independently snapshotted. A Region is an isolated logical
   --  image; returned coordinates are local to it. Mask must match the image
   --  geometry and type. Use a 0/255 mask for the portable baseline. Other
   --  nonzero values are forwarded unchanged: native 4.x and 5.0 differ
   --  in normalization before constructing the mask pyramid.
   --  The fixed-profile native arithmetic envelope is checked in the shim;
   --  see docs/orb-contract.md. Inputs are unchanged on success and failure.
   --  Use distinct detectors for concurrent calls. Concurrent mutation of
   --  source storage, or Close during extraction, is not supported.
   function Detect_And_Compute
     (Self : Detector; Image : OpenCV.Core.Mat) return Feature_Set;
   function Detect_And_Compute
     (Self : Detector; Image, Mask : OpenCV.Core.Mat) return Feature_Set;

private
   type Detector is new Ada.Finalization.Limited_Controlled with record
      Handle : aliased System.Address := System.Null_Address;
      Config : Configuration := (others => <>);
   end record;

   overriding procedure Finalize (Self : in out Detector);
end OpenCV.Features.ORB;
