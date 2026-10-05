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