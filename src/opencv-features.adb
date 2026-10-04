with Interfaces.C.Strings;
with OpenCV.Features.Internal.C_API;

package body OpenCV.Features is
   package C renames OpenCV.Features.Internal.C_API;

   function Count (Features : Feature_Set) return Natural is
     (Natural (Features.Points.Length));

   function Is_Empty (Features : Feature_Set) return Boolean is
     (Features.Points.Is_Empty);

   function Descriptor_Row
     (Features : Feature_Set; Index : Positive) return Natural is
   begin
      if Index > Count (Features) then
         raise OpenCV.OpenCV_Error with "Keypoint index is outside the result";
      end if;
      return Index - 1;
   end Descriptor_Row;

   function Point (Features : Feature_Set; Index : Positive) return Keypoint is
   begin
      if Index > Count (Features) then
         raise OpenCV.OpenCV_Error with "Keypoint index is outside the result";
      end if;
      return Features.Points.Element (Index);
   end Point;

   function Keypoints (Features : Feature_Set) return Keypoint_Array is
   begin
      return Result : Keypoint_Array (1 .. Count (Features)) do
         for I in Result'Range loop
            Result (I) := Features.Points.Element (I);
         end loop;
      end return;
   end Keypoints;

   function Required_Norm
     (Features : Feature_Set) return Binary_Descriptor_Norm is
     (Features.Norm);

   function Descriptor_Copy (Features : Feature_Set) return OpenCV.Core.Mat is
     (Features.Data.Clone);

   function Native_Version return String is
     (Interfaces.C.Strings.Value (C.Native_Version));

   function Native_Backend return String is
     (Interfaces.C.Strings.Value (C.Native_Backend));
end OpenCV.Features;
