--  SPDX-License-Identifier: Apache-2.0

with OpenCV.Core;
private with Ada.Containers.Vectors;

--  Version-independent feature values shared by the Features packages:
--  keypoints, binary descriptor norms and the paired Feature_Set result.
--  Public values are Ada values, not C++ or C ABI records. A Feature_Set is
--  produced by a detector such as OpenCV.Features.ORB and pairs each Ada
--  keypoint with one row of a Core-owned descriptor Mat. Keypoint indices are
--  one-based; native descriptor rows are zero-based (see Descriptor_Row).
--  Binding and native failures raise OpenCV.OpenCV_Error. Language-defined
--  checks, such as passing zero as a Positive index, raise their normal Ada
--  exceptions, and array function results can raise Storage_Error.
package OpenCV.Features is

   --  One detected keypoint, copied from the native result without
   --  normalization. Coordinates are local to the image or Region passed to
   --  the detector: X is the column and Y the row, in pixels from its first
   --  element. Before publication the native layer requires finite values,
   --  0 <= X < columns, 0 <= Y < rows, Size > 0 and a valid pyramid octave.
   --  Keypoints from a higher octave are rescaled to input pixels and need
   --  not have integral coordinates.
   --  @field Position Keypoint location (X column, Y row) in input pixels.
   --  @field Size Diameter of the keypoint neighborhood in input pixels, as
   --  reported by OpenCV; always finite and positive.
   --  @field Angle_Degrees Keypoint orientation in degrees, as computed by
   --  the native detector; finite, with no range normalization by Ada.
   --  @field Response Native detector response used to rank keypoints (the
   --  configured Harris or FAST score). It is preserved unchanged and is not
   --  a probability or match confidence.
   --  @field Octave Zero-based pyramid level that produced the keypoint; for
   --  the fixed ORB profile it is in 0 .. 7.
   --  @field Class_Id Native class identifier, preserved unchanged. The
   --  Features operations neither assign nor interpret it.
   type Keypoint is record
      Position      : OpenCV.Float32_Point;
      Size          : OpenCV.Float32_Value;
      Angle_Degrees : OpenCV.Float32_Value;
      Response      : OpenCV.Float32_Value;
      Octave        : OpenCV.Int32_Value;
      Class_Id      : OpenCV.Int32_Value;
   end record;

   --  Ordinary Ada array of keypoint values. Keypoints returns bounds
   --  1 .. Count, so element I corresponds to descriptor row I - 1.
   type Keypoint_Array is array (Positive range <>) of Keypoint;

   --  Distance norm required to compare a set's binary descriptors. ORB
   --  WTA_K = 2 (Two_Samples) produces Hamming descriptors; WTA_K = 3 or 4
   --  produces Hamming_2 descriptors. Matching requires both sets to carry
   --  the same norm.
   --  @enum Hamming Number of differing bits across the 32-byte descriptor,
   --  0 .. 256 (OpenCV NORM_HAMMING).
   --  @enum Hamming_2 Number of differing 2-bit cells across the descriptor,
   --  0 .. 128 (OpenCV NORM_HAMMING2).
   type Binary_Descriptor_Norm is (Hamming, Hamming_2);

   --  An immutable, paired collection. Construction is through a detector.
   --  A default-declared set is empty. Results own their keypoint values and
   --  Core-owned descriptor storage, independently of the source/detector.
   --  Limited ownership avoids accidental copying of large feature sets.
   --  Keypoints are stored as Ada values in native detector order; keypoint
   --  I is paired with descriptor row I - 1. A set stays valid after its
   --  detector is closed or finalized and after the source image or mask is
   --  modified. No public operation changes a set after construction. A
   --  default-declared set reports the Hamming norm.
   type Feature_Set is limited private;

   --  Number of keypoints, equal to the number of descriptor rows. This is
   --  the actual produced count: it can be zero and is not bounded by a
   --  detector's requested feature target.
   --  @param Features Feature set to inspect.
   --  @return Number of stored keypoints.
   function Count (Features : Feature_Set) return Natural;

   --  True exactly when Count (Features) = 0, for example for a blank or
   --  fully masked image, or for a default-declared set.
   --  @param Features Feature set to inspect.
   --  @return Whether the set contains no keypoints.
   function Is_Empty (Features : Feature_Set) return Boolean;

   --  Copy of one stored keypoint, selected by its one-based index.
   --  @param Features Feature set to read.
   --  @param Index One-based keypoint index in 1 .. Count (Features).
   --  @return The keypoint value stored at Index.
   --  @exception OpenCV_Error Index is greater than Count (Features).
   function Point (Features : Feature_Set; Index : Positive) return Keypoint;

   --  Copy of every stored keypoint, in stored order.
   --  @param Features Feature set to read.
   --  @return An array with bounds 1 .. Count (Features); 1 .. 0 when empty.
   function Keypoints (Features : Feature_Set) return Keypoint_Array;

   --  Norm that must be used to compare these descriptors. It is recorded
   --  from the detector configuration, also for empty results.
   --  @param Features Feature set to inspect.
   --  @return Hamming for ORB Two_Samples results; Hamming_2 for
   --  Three_Samples and Four_Samples results.
   function Required_Norm
     (Features : Feature_Set) return Binary_Descriptor_Norm;

   --  Ada keypoint Index = 1 maps to OpenCV descriptor row 0. An invalid
   --  positive index raises OpenCV_Error (not a native unchecked access).
   --  @param Features Feature set whose pairing is queried.
   --  @param Index One-based keypoint index in 1 .. Count (Features).
   --  @return The zero-based descriptor row, Index - 1.
   --  @exception OpenCV_Error Index is greater than Count (Features).
   function Descriptor_Row
     (Features : Feature_Set; Index : Positive) return Natural;

   --  Explicit deep copy: caller mutation cannot break the stored pairing.
   --  For a nonempty ORB result: Count rows, 32 columns, UInt8 C1.
   --  For an empty result: an empty Mat; no 0x32 shape is promised.
   --  The returned Mat is a new Core-owned matrix owned by the caller. It
   --  shares no storage with the set, so writing to it never changes the set,
   --  and it stays valid after the set is finalized. Matching operations
   --  read a set's descriptors directly; no copy is needed for matching.
   --  @param Features Feature set whose descriptors are copied.
   --  @return A caller-owned copy of the descriptor matrix.
   function Descriptor_Copy (Features : Feature_Set) return OpenCV.Core.Mat;

   --  OpenCV version string (CV_VERSION) of the headers that the native
   --  Features shim was compiled against, for example "4.10.0".
   --  @return The native OpenCV version identifier.
   function Native_Version return String;

   --  Native OpenCV module behind this binding: "features2d" for OpenCV 4
   --  and "features" for OpenCV 5.0. The public Ada API is the same for both.
   --  @return The native backend module name.
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
