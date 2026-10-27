with Ada.Text_IO;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features.ORB;
with OpenCV.Features.Matching;
with OpenCV.Features.Correspondences;

procedure ORB_Pyramid_Synthetic is
   package Features renames OpenCV.Features;
   package ORB renames Features.ORB;
   package Matching renames Features.Matching;
   package Bytes renames OpenCV.Core.UInt8_Access;
   Checker_Parity_Modulus : constant Positive := 2;
   Source : OpenCV.Core.Mat := OpenCV.Core.Create
     (512, 512, (Depth => OpenCV.Core.UInt8, Channels => 1));
   Default : constant ORB.Detector := ORB.Create;
   Configured : constant ORB.Detector := ORB.Create
     ((others => <>), (Scale_Factor => 1.1, Levels => 12));
begin
   for R in 0 .. 511 loop
      for C in 0 .. 511 loop
         Bytes.Set (Source, R, C, OpenCV.UInt8_Value
           ((R * 37 + C * 17 + ((R / 16 + C / 16) mod Checker_Parity_Modulus) * 83
             + R * C mod 251) mod 256));
      end loop;
   end loop;
   declare
      Query : constant Features.Feature_Set := Default.Detect_And_Compute (Source);
      Train : constant Features.Feature_Set := Configured.Detect_And_Compute (Source);
      Matches : constant Matching.Descriptor_Match_Array :=
        Matching.Brute_Force_Match (Query, Train, Matching.Mutual_Nearest);
      Points : constant Features.Correspondences.Point_Correspondence_Array :=
        Features.Correspondences.From_Matches (Query, Train, Matches);
   begin
      Ada.Text_IO.Put_Line ("OpenCV " & Features.Native_Version);
      Ada.Text_IO.Put_Line ("Default levels:" & Positive'Image (Default.Pyramid_Parameters.Levels)
        & "; features:" & Natural'Image (Features.Count (Query)));
      Ada.Text_IO.Put_Line ("Configured levels:"
        & Positive'Image (Configured.Pyramid_Parameters.Levels)
        & "; scale:" & OpenCV.Float32_Value'Image (Configured.Pyramid_Parameters.Scale_Factor)
        & "; features:" & Natural'Image (Features.Count (Train)));
      Ada.Text_IO.Put_Line ("Mutual descriptor matches / owned candidate correspondences:"
        & Natural'Image (Points'Length));
      Ada.Text_IO.Put_Line
        ("Synthetic scale-space comparison only; no geometric inlier or localization claim.");
   end;
end ORB_Pyramid_Synthetic;