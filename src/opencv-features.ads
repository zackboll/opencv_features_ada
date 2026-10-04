with OpenCV.Core;
private with Ada.Containers.Vectors;

package OpenCV.Features is
   --  SPDX-License-Identifier: Apache-2.0
   --  Public values are Ada values, not C++ or C ABI records.
   type Keypoint is record
      Position      : OpenCV.Float32_Point;
      Size          : OpenCV.Float32_Value;
      Angle_Degrees : OpenCV.Float32_Value;
      Response      : OpenCV.Float32_Value;
      Octave        : OpenCV.Int32_Value;
      Class_Id      : OpenCV.Int32_Value;
   end record;

   type Keypoint_Array is array (Positive range <>) of Keypoint;
   type Binary_Descriptor_Norm is (Hamming, Hamming_2);

   --  An immutable, paired collection. Construction is through a detector.
   --  A default-declared set is empty. Results own their keypoint values and
   --  Core-owned descriptor storage, independently of the source/detector.
   --  Limited ownership avoids accidental copying of large feature sets.
   type Feature_Set is limited private;

   function Count (Features : Feature_Set) return Natural;
   function Is_Empty (Features : Feature_Set) return Boolean;
   function Point (Features : Feature_Set; Index : Positive) return Keypoint;
   function Keypoints (Features : Feature_Set) return Keypoint_Array;
   function Required_Norm
     (Features : Feature_Set) return Binary_Descriptor_Norm;

   --  Ada keypoint Index = 1 maps to OpenCV descriptor row 0. An invalid
   --  positive index raises OpenCV_Error (not a native unchecked access).
   function Descriptor_Row
     (Features : Feature_Set; Index : Positive) return Natural;

   --  Explicit deep copy: caller mutation cannot break the stored pairing.
   --  For a nonempty ORB result: Count rows, 32 columns, UInt8 C1.
   --  For an empty result: an empty Mat; no 0x32 shape is promised.
   function Descriptor_Copy (Features : Feature_Set) return OpenCV.Core.Mat;

   function Native_Version return String;
   function Native_Backend return String;

private
   package Keypoint_Vectors is new Ada.Containers.Vectors
     (Index_Type => Positive, Element_Type => Keypoint);

   type Feature_Set is limited record
      Points : Keypoint_Vectors.Vector;
      Data   : OpenCV.Core.Mat;
      Norm   : Binary_Descriptor_Norm := Hamming;
   end record;
end OpenCV.Features;
