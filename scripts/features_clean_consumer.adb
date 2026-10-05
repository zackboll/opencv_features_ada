with Ada.Text_IO;
with OpenCV;
with OpenCV.Core;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features;
with OpenCV.Features.ORB;
with OpenCV.Features.Matching;
with OpenCV.Features.Correspondences;

procedure Features_Clean_Consumer is
   package Features renames OpenCV.Features;
   package ORB renames Features.ORB;
   package Matching renames Features.Matching;
   package Correspondences renames Features.Correspondences;
   package Bytes renames OpenCV.Core.UInt8_Access;
   use type Matching.Binary_Descriptor_Distance;
   use type Matching.Matching_Mode;
   use type OpenCV.Float32_Point;

   procedure Require (Condition : Boolean; Message : String) is
   begin
      if not Condition then
         raise Program_Error with Message;
      end if;
   end Require;

   --  The already-qualified orb_match_synthetic texture/translation, not an
   --  exact feature-count oracle. Thresholds below are fixture policy only.
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
           ((R * 37 + C * 17
             + ((R / 16 + C / 16) mod Checker_Parity_Modulus) * 83
             + R * C mod 251) mod 256));
      end loop;
   end loop;
   for R in 0 .. 247 loop
      for C in 0 .. 250 loop
         Bytes.Set (Train_Image, R + 8, C + 5, Bytes.Get (Query_Image, R, C));
      end loop;
   end loop;
   declare
      Query : constant Features.Feature_Set :=
        ORB.Detect_And_Compute (Detector, Query_Image);
      Train : constant Features.Feature_Set :=
        ORB.Detect_And_Compute (Detector, Train_Image);

      procedure Check_Conversion (Matches : Matching.Descriptor_Match_Array) is
         Points : constant Correspondences.Point_Correspondence_Array :=
           Correspondences.From_Matches (Query, Train, Matches);
      begin
         Require (Points'Length = Matches'Length, "conversion count");
         for Offset in 0 .. Matches'Length - 1 loop
            declare
               M : constant Matching.Descriptor_Match := Matches (Matches'First + Offset);
               P : constant Correspondences.Point_Correspondence := Points (Points'First + Offset);
            begin
               Require (P.Query_Index = M.Query_Index, "query index");
               Require (P.Train_Index = M.Train_Index, "train index");
               Require (P.Distance = M.Distance, "descriptor distance");
               Require (P.Query_Point = Features.Point (Query, M.Query_Index).Position,
                        "query position");
               Require (P.Train_Point = Features.Point (Train, M.Train_Index).Position,
                        "train position");
            end;
         end loop;
      end Check_Conversion;
   begin
      Require (Features.Count (Query) >= 2, "query needs two features");
      Require (Features.Count (Train) >= 2, "train needs two features");
      Ada.Text_IO.Put_Line ("OpenCV " & Features.Native_Version & " / " & Features.Native_Backend);
      for Mode in Matching.Matching_Mode loop
         declare
            Matches : constant Matching.Descriptor_Match_Array :=
              Matching.Brute_Force_Match (Query, Train, Mode);
         begin
            if Mode = Matching.Nearest then
               Require (Matches'Length > 0, "nearest matches empty");
            end if;
            Check_Conversion (Matches);
         end;
      end loop;
      declare
         Pairs : constant Matching.Two_Nearest_Match_Array :=
           Matching.Brute_Force_KNN_2 (Query, Train);
         Accepted : constant Matching.Descriptor_Match_Array :=
           Matching.Filter_By_Ratio (Pairs, 0.80);
         Radius : constant Matching.Descriptor_Match_Array :=
           Matching.Brute_Force_Radius_Match (Query, Train, Maximum_Distance => 32);
      begin
         Require (Pairs'Length = Features.Count (Query), "KNN2 pair count");
         Check_Conversion (Accepted); --  Empty ratio output is legitimate.
         Check_Conversion (Radius);
      end;
   end;
   Ada.Text_IO.Put_Line ("opencv_features clean consumer ok");
end Features_Clean_Consumer;