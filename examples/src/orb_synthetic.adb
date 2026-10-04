with Ada.Text_IO;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features.ORB;

procedure ORB_Synthetic is
   package Features renames OpenCV.Features;
   package ORB renames OpenCV.Features.ORB;
   Image : OpenCV.Core.Mat := OpenCV.Core.Create
     (256, 256, (Depth => OpenCV.Core.UInt8, Channels => 1));
   Detector : ORB.Detector := ORB.Create;
begin
   for Row in 0 .. 255 loop
      for Column in 0 .. 255 loop
         OpenCV.Core.UInt8_Access.Set
           (Image, Row, Column,
            OpenCV.UInt8_Value
              ((Row * 37 + Column * 17 + (Row * Column mod 251)) mod 256));
      end loop;
   end loop;
   declare
      Result : Features.Feature_Set := ORB.Detect_And_Compute (Detector, Image);
      Descriptors : constant OpenCV.Core.Mat := Features.Descriptor_Copy (Result);
   begin
      Ada.Text_IO.Put_Line
        ("OpenCV " & Features.Native_Version & " / " & Features.Native_Backend);
      Ada.Text_IO.Put_Line ("Keypoints:" & Natural'Image (Features.Count (Result)));
      Ada.Text_IO.Put_Line
        ("Descriptor rows:" & Natural'Image (Descriptors.Rows));
      Ada.Text_IO.Put_Line
        ("Required matcher norm: " & Features.Binary_Descriptor_Norm'Image
           (Features.Required_Norm (Result)));
      ORB.Close (Detector);
      --  Result remains valid after Close. Do not use these features as a
      --  navigation measurement until matching and geometric verification
      --  have been implemented in subsequent modules/slices.
   end;
end ORB_Synthetic;
