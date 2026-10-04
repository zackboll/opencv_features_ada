with AUnit.Assertions;
with AUnit.Test_Caller;
with AUnit.Test_Fixtures;
with Ada.Text_IO;
with OpenCV.Core.UInt8_Access;
with OpenCV.Core.Module_Interop;
with OpenCV.Features.Internal.C_API;
with OpenCV.Features.ORB;
with OpenCV.Features.Matching;
with Interfaces;
with Interfaces.C;
with System;

package body Features_Tests is
   use AUnit.Assertions;
   use OpenCV.Features;
   package ORB renames OpenCV.Features.ORB;
   package Matching renames OpenCV.Features.Matching;
   use type Matching.Binary_Descriptor_Distance;
   package Bytes renames OpenCV.Core.UInt8_Access;
   use type OpenCV.Core.Depth_Type;
   use type OpenCV.Core.Channel_Count;
   use type OpenCV.UInt8_Value;
   use type OpenCV.Float32_Value;
   use type OpenCV.Float64_Value;
   use type ORB.Tuple_Size;
   package ABI renames OpenCV.Features.Internal.C_API;
   package Bridge renames OpenCV.Core.Module_Interop;
   use type Interfaces.Integer_32;
   use type Interfaces.C.C_float;
   use type System.Address;
   use type ABI.C_Keypoint;

   type Fixture is new AUnit.Test_Fixtures.Test_Fixture with null record;

   function Image (Rows : Positive := 256; Columns : Positive := 256;
                   Textured : Boolean := True) return OpenCV.Core.Mat is
      Checker_Parity_Modulus : constant Positive := 2;
      Result : OpenCV.Core.Mat := OpenCV.Core.Create
        (Rows, Columns, (Depth => OpenCV.Core.UInt8, Channels => 1));
   begin
      Result.Set_To (OpenCV.Make_Scalar (0.0));
      if Textured then
         for R in 0 .. Rows - 1 loop
            for C in 0 .. Columns - 1 loop
               Bytes.Set
                 (Result, R, C,
                  OpenCV.UInt8_Value
                     ((R * 37 + C * 17
                       + ((R / 16 + C / 16) mod Checker_Parity_Modulus) * 83
                      + ((R * C) mod 251)) mod 256));
            end loop;
         end loop;
      end if;
      return Result;
   end Image;

   procedure Assert_Same (A, B : OpenCV.Core.Mat) is
   begin
      Assert (A.Rows = B.Rows and then A.Columns = B.Columns,
              "matrix geometry differs");
      if not A.Is_Empty then
         for R in 0 .. A.Rows - 1 loop
            for C in 0 .. A.Columns - 1 loop
               Assert (Bytes.Get (A, R, C) = Bytes.Get (B, R, C),
                       "matrix content differs");
            end loop;
         end loop;
      end if;
   end Assert_Same;

   procedure Expect_Invalid_Image (Source : OpenCV.Core.Mat) is
      Detector : constant ORB.Detector := ORB.Create;
   begin
      declare
         Result : Feature_Set := ORB.Detect_And_Compute (Detector, Source);
         pragma Unreferenced (Result);
      begin
         Assert (False, "invalid source accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Expect_Invalid_Image;

   procedure Metadata (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Assert (Native_Version'Length > 0, "empty native version");
      Assert (Native_Backend = "features2d" or else Native_Backend = "features",
              "unexpected native backend");
   end Metadata;

   procedure Lifecycle (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : ORB.Detector;
   begin
      Assert (not ORB.Is_Ready (Detector), "default detector should be closed");
      ORB.Close (Detector);
      declare
         Ready : ORB.Detector := ORB.Create;
      begin
         Assert (ORB.Is_Ready (Ready), "created detector is not ready");
         ORB.Close (Ready);
         ORB.Close (Ready);
         Assert (not ORB.Is_Ready (Ready), "closed detector still ready");
      end;
   end Lifecycle;

   procedure Config_Round_Trip (T : in out Fixture) is
      pragma Unreferenced (T);

      Config : constant ORB.Configuration :=
        (Maximum_Features => 300, Tuple => ORB.Four_Samples,
         Score => ORB.FAST_Score, FAST_Threshold => 7);
      Detector : constant ORB.Detector := ORB.Create (Config);
      use type ORB.Configuration;
   begin
      Assert (ORB.Parameters (Detector) = Config, "configuration changed");
   end Config_Round_Trip;

   procedure Blank_Image (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image (Textured => False);
      Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Descriptors : constant OpenCV.Core.Mat := Descriptor_Copy (Result);
      Points : constant Keypoint_Array := Keypoints (Result);
   begin
      Assert (Is_Empty (Result) and then Count (Result) = 0, "blank image has features");
      Assert (Points'Length = 0 and then Descriptors.Is_Empty, "empty pairing failed");
   end Blank_Image;

   procedure Paired_Result (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Before : constant OpenCV.Core.Mat := Source.Clone;
      Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Descriptors : constant OpenCV.Core.Mat := Descriptor_Copy (Result);
   begin
      Assert (Count (Result) > 0, "synthetic texture yielded no features");
      Assert (Descriptors.Rows = Count (Result) and then Descriptors.Columns = 32,
              "descriptor/keypoint shape mismatch");
      Assert (Descriptors.Depth = OpenCV.Core.UInt8 and then Descriptors.Channels = 1,
              "unexpected descriptor element type");
      Assert (Required_Norm (Result) = Hamming, "default ORB norm is not Hamming");
      for I in 1 .. Count (Result) loop
         declare
            P : constant Keypoint := Point (Result, I);
         begin
            Assert (Descriptor_Row (Result, I) = I - 1, "one/zero-based mapping failed");
            Assert (P.Position.X >= 0.0 and then P.Position.Y >= 0.0
                    and then P.Position.X < 256.0 and then P.Position.Y < 256.0,
                    "keypoint outside image");
         end;
      end loop;
      Assert_Same (Source, Before);
   end Paired_Result;

   procedure Zero_Mask (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Mask : constant OpenCV.Core.Mat := Image (Textured => False);
      Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
   begin
      Assert (Count (Result) = 0, "zero mask did not exclude keypoints");
   end Zero_Mask;

   procedure Full_Mask (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Mask : OpenCV.Core.Mat := Image (Textured => False);
   begin
      Mask.Set_To (OpenCV.Make_Scalar (255.0));
      declare
         Before : constant OpenCV.Core.Mat := Mask.Clone;
         Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
      begin
         Assert (Count (Result) > 0, "full mask unexpectedly excluded all features");
         Assert_Same (Mask, Before);
      end;
   end Full_Mask;

   procedure Wrong_Depth (T : in out Fixture) is
      pragma Unreferenced (T);

      Source : constant OpenCV.Core.Mat := OpenCV.Core.Create
        (256, 256, (Depth => OpenCV.Core.Float32, Channels => 1));
   begin
      Expect_Invalid_Image (Source);
   end Wrong_Depth;

   procedure Wrong_Channels (T : in out Fixture) is
      pragma Unreferenced (T);

      Source : constant OpenCV.Core.Mat := OpenCV.Core.Create
        (256, 256, (Depth => OpenCV.Core.UInt8, Channels => 3));
   begin
      Expect_Invalid_Image (Source);
   end Wrong_Channels;

   procedure Empty_Source (T : in out Fixture) is
      pragma Unreferenced (T);

      Source : OpenCV.Core.Mat;
   begin
      Expect_Invalid_Image (Source);
   end Empty_Source;

   procedure Tiny_Source (T : in out Fixture) is
      pragma Unreferenced (T);

      Source : constant OpenCV.Core.Mat := Image (Rows => 1, Columns => 1);
   begin
      Expect_Invalid_Image (Source);
   end Tiny_Source;

   procedure Mask_Shape (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Mask : constant OpenCV.Core.Mat := Image (Rows => 128);
   begin
      declare
         Result : Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
         pragma Unreferenced (Result);
      begin
         Assert (False, "mismatched mask accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Mask_Shape;

   procedure Mask_Depth (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Mask : constant OpenCV.Core.Mat := OpenCV.Core.Create
        (256, 256, (Depth => OpenCV.Core.Float32, Channels => 1));
   begin
      declare
         Result : Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
         pragma Unreferenced (Result);
      begin
         Assert (False, "wrong mask depth accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Mask_Depth;

   procedure Closed_Detector (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : ORB.Detector;
      Source : constant OpenCV.Core.Mat := Image;
   begin
      declare
         Result : Feature_Set := ORB.Detect_And_Compute (Detector, Source);
         pragma Unreferenced (Result);
      begin
         Assert (False, "unready detector accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Closed_Detector;

   procedure Result_Lifetime (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : ORB.Detector := ORB.Create;
      Source : OpenCV.Core.Mat := Image;
      Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Before : constant OpenCV.Core.Mat := Descriptor_Copy (Result);
   begin
      Assert (Count (Result) > 0, "no result to test");
      ORB.Close (Detector);
      Source.Set_To (OpenCV.Make_Scalar (0.0));
      declare
         After : constant OpenCV.Core.Mat := Descriptor_Copy (Result);
      begin
         Assert_Same (Before, After);
      end;
   end Result_Lifetime;

   procedure Descriptor_Isolation (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Copy : OpenCV.Core.Mat := Descriptor_Copy (Result);
      Original : constant OpenCV.UInt8_Value := Bytes.Get (Copy, 0, 0);
   begin
      Bytes.Set (Copy, 0, 0, Original + 1);
      declare
         Fresh : constant OpenCV.Core.Mat := Descriptor_Copy (Result);
      begin
         Assert (Bytes.Get (Fresh, 0, 0) = Original, "descriptor getter shared writable storage");
      end;
   end Descriptor_Isolation;

   procedure Region_Isolation (T : in out Fixture) is
      pragma Unreferenced (T);

      Detector : constant ORB.Detector := ORB.Create;
      Parent : constant OpenCV.Core.Mat := Image (Rows => 320, Columns => 320);
      Region : constant OpenCV.Core.Mat :=
        Parent.Region (OpenCV.Rect'(X => 32, Y => 32, Width => 256, Height => 256));
      Packed : constant OpenCV.Core.Mat := Region.Clone;
      First : constant Feature_Set := ORB.Detect_And_Compute (Detector, Region);
      Second : constant Feature_Set := ORB.Detect_And_Compute (Detector, Packed);
      A : constant OpenCV.Core.Mat := Descriptor_Copy (First);
      B : constant OpenCV.Core.Mat := Descriptor_Copy (Second);
   begin
      Assert (Count (First) > 0 and then Count (First) = Count (Second),
              "ROI and packed extraction differ");
      Assert_Same (A, B);
   end Region_Isolation;

   procedure Index_Rejection (T : in out Fixture) is
      pragma Unreferenced (T);

      Empty : Feature_Set;
   begin
      declare
         P : constant Keypoint := Point (Empty, 1);
         pragma Unreferenced (P);
      begin
         Assert (False, "out-of-range keypoint accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Index_Rejection;

   procedure Tuple_Norms (T : in out Fixture) is
      pragma Unreferenced (T);

      Source : constant OpenCV.Core.Mat := Image;
   begin
      for Tuple in ORB.Three_Samples .. ORB.Four_Samples loop
         declare
            Detector : constant ORB.Detector := ORB.Create
              ((Tuple => Tuple, others => <>));
            Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
         begin
            Assert (Count (Result) > 0, "no features for tuple test");
            Assert (Required_Norm (Result) = Hamming_2, "tuple norm mismatch");
         end;
      end loop;
   end Tuple_Norms;

   procedure Config_Rejection (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      declare
         Detector : ORB.Detector := ORB.Create
           ((FAST_Threshold => 256, others => <>));
         pragma Unreferenced (Detector);
      begin
         Assert (False, "invalid FAST threshold accepted");
      end;
   exception
      when OpenCV.OpenCV_Error => null;
   end Config_Rejection;

   procedure Nonbinary_Masks (T : in out Fixture) is
      pragma Unreferenced (T);
      Detector : constant ORB.Detector := ORB.Create;
      Source : constant OpenCV.Core.Mat := Image;
      Mask : OpenCV.Core.Mat := Image (Textured => False);
   begin
      Mask.Set_To (OpenCV.Make_Scalar (1.0));
      declare
         Before : constant OpenCV.Core.Mat := Mask.Clone;
         Ones : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
      begin
         Assert (Count (Ones) > 0, "all-1 mask lost level-zero features");
         Assert_Same (Mask, Before);
         Mask.Set_To (OpenCV.Make_Scalar (255.0));
         declare
            Full : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
         begin
            if Native_Version (Native_Version'First) = '5' then
               Assert (Count (Ones) = Count (Full), "5.0 incoming normalization differs");
               for I in 1 .. Count (Ones) loop
                  Assert (Point (Ones, I) = Point (Full, I), "5.0 normalized keypoint differs");
               end loop;
               Assert_Same (Descriptor_Copy (Ones), Descriptor_Copy (Full));
            else
               for I in 1 .. Count (Ones) loop
                  Assert (Point (Ones, I).Octave = 0, "4.x all-1 mask survives resized level");
               end loop;
            end if;
         end;
      end;
      -- Vertical stripes: 0 / 1 / 254 / 255. Level-zero FAST uses != 0.
      for R in 0 .. 255 loop
         for C in 0 .. 255 loop
            Bytes.Set (Mask, R, C,
                       (case C / 64 is when 0 => 0, when 1 => 1,
                        when 2 => 254, when others => 255));
         end loop;
      end loop;
      declare
         Before : constant OpenCV.Core.Mat := Mask.Clone;
         Result : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source, Mask);
      begin
         Assert (Count (Result) > 0, "mixed mask yielded no features");
         for I in 1 .. Count (Result) loop
            declare
               P : constant Keypoint := Point (Result, I);
            begin
               if P.Octave = 0 then
                  Assert (Bytes.Get (Mask, Natural (P.Position.Y), Natural (P.Position.X)) /= 0,
                          "level-zero point outside nonzero mask");
               end if;
            end;
         end loop;
         Assert_Same (Mask, Before);
      end;
   end Nonbinary_Masks;

   procedure ABI_Layout (T : in out Fixture) is
      pragma Unreferenced (T);
      function Layout (Field : Interfaces.Integer_32) return Interfaces.Integer_32
        with Import, Convention => C, External_Name => "features_test_layout";
      procedure Fill (Point : access ABI.C_Keypoint)
        with Import, Convention => C, External_Name => "features_test_keypoint";
      P : aliased ABI.C_Keypoint;
      type Positions is array (Natural range <>) of Natural;
      Offsets : constant Positions :=
        [P.X'Position, P.Y'Position, P.Size'Position, P.Angle'Position,
         P.Response'Position, P.Octave'Position, P.Class_Id'Position];
   begin
      Assert (ABI.C_Keypoint'Size = Natural (Layout (0)) * System.Storage_Unit,
              "C/Ada keypoint size mismatch");
      Assert (ABI.C_Keypoint'Alignment = Natural (Layout (1)), "C/Ada alignment mismatch");
      for I in Offsets'Range loop
         Assert (Offsets (I) = Natural (Layout (Interfaces.Integer_32 (I + 2))),
                 "C/Ada field offset mismatch");
      end loop;
      Assert (P.X'First_Bit = 0 and then P.Y'First_Bit = 0
              and then P.Size'First_Bit = 0 and then P.Angle'First_Bit = 0
              and then P.Response'First_Bit = 0 and then P.Octave'First_Bit = 0
              and then P.Class_Id'First_Bit = 0, "non-byte-aligned field");
      Fill (P'Access);
      Assert (P = (1.25, -2.5, 31.0, 90.0, 0.125, 7, -1), "C/Ada interchange mismatch");
   end ABI_Layout;

   procedure ABI_Creation (T : in out Fixture) is
      pragma Unreferenced (T);
      Detector : aliased System.Address := System.Null_Address;
      Live : aliased System.Address := System.Null_Address;
      procedure Invalid (Maximum, Tuple, Score, Threshold : Interfaces.Integer_32) is
      begin
         Detector := Live; -- a live sentinel, never dereferenced on failed creation
         Assert (ABI.ORB_Create (Maximum, Tuple, Score, Threshold, Detector'Access) = 1,
                 "malformed raw configuration accepted");
         Assert (Detector = System.Null_Address, "failed creation did not clear output");
      end Invalid;
   begin
      Assert (ABI.ORB_Create (500, 2, 0, 20, null) = 1, "null creation output accepted");
      Assert (ABI.ORB_Create (500, 2, 0, 20, Live'Access) = 0, "valid raw creation failed");
      Invalid (0, 2, 0, 20);
      Invalid (Interfaces.Integer_32'Last / 2 + 1, 2, 0, 20);
      Invalid (500, 1, 0, 20);
      Invalid (500, 5, 0, 20);
      Invalid (500, 2, -1, 20);
      Invalid (500, 2, 2, 20);
      Invalid (500, 2, 0, -1);
      Invalid (500, 2, 0, 256);
      ABI.ORB_Destroy (Live);
      ABI.ORB_Destroy (System.Null_Address);
   end ABI_Creation;

   procedure ABI_Extraction (T : in out Fixture) is
      pragma Unreferenced (T);
      Detector : aliased System.Address := System.Null_Address;
      Result : aliased System.Address := System.Null_Address;
      Count : aliased Interfaces.Integer_32 := -1;
      P : aliased ABI.C_Keypoint := (0.0, 0.0, 0.0, 0.0, 0.0, 0, 0);
      Zero : constant ABI.C_Keypoint := (0.0, 0.0, 0.0, 0.0, 0.0, 0, 0);
      Source : constant OpenCV.Core.Mat := Image;
      Wrong : constant OpenCV.Core.Mat := OpenCV.Core.Create
        (256, 256, (Depth => OpenCV.Core.Float32, Channels => 1));
      Small : constant OpenCV.Core.Mat := Image (Rows => 128, Columns => 128);
      Output : OpenCV.Core.Mat;
      -- Null is expressed at the raw test boundary; no invented non-null handles.
      function Null_Image
        (Handle, Image : System.Address; Result : access System.Address;
         Count : access Interfaces.Integer_32) return ABI.Status
        with Import, Convention => C, External_Name => "opencv_features_orb_extract";
      function Null_Mask
        (Handle : System.Address; Image : Bridge.Input_Mat_Handle; Mask : System.Address;
         Result : access System.Address; Count : access Interfaces.Integer_32) return ABI.Status
        with Import, Convention => C, External_Name => "opencv_features_orb_extract_masked";
      function Null_Destination (Handle, Destination : System.Address) return ABI.Status
        with Import, Convention => C, External_Name => "opencv_features_result_descriptors";
      procedure Failed (Code : ABI.Status) is
      begin
         Assert (Code = 1, "raw extraction error status differs");
         Assert (Result = System.Null_Address and then Count = 0, "failure outputs not cleared");
         Count := -1;
      end Failed;
      procedure Extract (H : Bridge.Input_Mat_Handle) is
         procedure Bad_Mask (M : Bridge.Input_Mat_Handle) is
         begin
            Failed (ABI.ORB_Extract_Masked (Detector, H, M, Result'Access, Count'Access));
         end Bad_Mask;
      begin
         Failed (ABI.ORB_Extract (System.Null_Address, H, Result'Access, Count'Access));
         Failed (Null_Mask (Detector, H, System.Null_Address, Result'Access, Count'Access));
         Assert (ABI.ORB_Extract (Detector, H, null, Count'Access) = 1 and then Count = 0,
                 "null result output not handled");
         Assert (ABI.ORB_Extract (Detector, H, Result'Access, null) = 1
                 and then Result = System.Null_Address, "null count output not handled");
         Bridge.With_Input_Handle (Wrong, Bad_Mask'Access);
         Bridge.With_Input_Handle (Small, Bad_Mask'Access);
         Assert (ABI.ORB_Extract (Detector, H, Result'Access, Count'Access) = 0 and then Count > 0,
                 "raw extraction failed");
      end Extract;
      procedure Bad_Image (H : Bridge.Input_Mat_Handle) is
      begin
         Failed (ABI.ORB_Extract (Detector, H, Result'Access, Count'Access));
      end Bad_Image;
      procedure Export (H : Bridge.Output_Mat_Handle) is
      begin
         Assert (ABI.Result_Descriptors (Result, H) = 0, "real Core descriptor export failed");
      end Export;
   begin
      Assert (ABI.ORB_Create (500, 2, 0, 20, Detector'Access) = 0, "creation failed");
      Failed (Null_Image (Detector, System.Null_Address, Result'Access, Count'Access));
      Bridge.With_Input_Handle (Wrong, Bad_Image'Access);
      Bridge.With_Input_Handle (Source, Extract'Access);
      ABI.ORB_Destroy (Detector);
      Detector := System.Null_Address;
      -- Native result owns its data independently of the destroyed detector.
      for Index in 0 .. Count - 1 loop
         if Index = 0 or else Index = Count - 1 then
            Assert (ABI.Result_Point (Result, Index, P'Access) = 0 and then P.Size > 0.0,
                    "first/last point or result lifetime failed");
         end if;
      end loop;
      Assert (ABI.Result_Point (Result, -1, P'Access) = 1 and then P = Zero,
              "negative index/output clearing failed");
      P := (1.0, 1.0, 1.0, 1.0, 1.0, 1, 1);
      Assert (ABI.Result_Point (Result, Count, P'Access) = 1 and then P = Zero,
              "end index/output clearing failed");
      Assert (ABI.Result_Point (Result, 0, null) = 1, "null point output accepted");
      Assert (ABI.Result_Point (System.Null_Address, 0, P'Access) = 1 and then P = Zero,
              "null result point accepted");
      Assert (Null_Destination (System.Null_Address, System.Null_Address) = 1,
              "null descriptor result accepted");
      Assert (Null_Destination (Result, System.Null_Address) = 1, "null destination accepted");
      Bridge.With_Output_Handle (Output, Export'Access);
      Assert (Output.Rows = Natural (Count) and then Output.Columns = 32
              and then Output.Depth = OpenCV.Core.UInt8 and then Output.Channels = 1,
              "raw descriptor schema differs");
      ABI.Result_Destroy (Result);
      Assert (Output.Rows = Natural (Count), "Core output lost result storage");
   end ABI_Extraction;

   procedure Check_Self_Match (Tuple : ORB.Tuple_Size) is
      Source : constant OpenCV.Core.Mat := Image;
      Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
      Features : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Matches : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (Features, Features);
   begin
      Assert (Count (Features) > 0, "self-match fixture has no features");
      Assert (Matches'Length = Count (Features), "nearest count differs from query count");
      for I in Matches'Range loop
         Assert (Matches (I).Query_Index = I, "query coverage/order is not complete");
         Assert (Matches (I).Train_Index <= Count (Features), "train index outside feature set");
         Assert (Matches (I).Distance = 0, "self-match distance is not zero");
      end loop;
   end Check_Self_Match;

   procedure Match_WTA2 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_Self_Match (ORB.Two_Samples);
   end Match_WTA2;

   procedure Match_WTA3 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_Self_Match (ORB.Three_Samples);
   end Match_WTA3;

   procedure Match_WTA4 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_Self_Match (ORB.Four_Samples);
   end Match_WTA4;

   procedure Match_Norm_Mismatch (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Blank : constant OpenCV.Core.Mat := Image (Textured => False);
      Detector : constant ORB.Detector := ORB.Create;
      WTA2 : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Empty_WTA2 : constant Feature_Set := ORB.Detect_And_Compute (Detector, Blank);
      procedure Reject (A, B : Feature_Set) is
      begin
         declare
            Matches : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (A, B);
            pragma Unreferenced (Matches);
         begin
            Assert (False, "norm mismatch accepted");
         end;
      exception
         when OpenCV.OpenCV_Error => null;
      end Reject;
   begin
      for Tuple in ORB.Three_Samples .. ORB.Four_Samples loop
         declare
            Other : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            WTA : constant Feature_Set := ORB.Detect_And_Compute (Other, Source);
            Empty_WTA : constant Feature_Set := ORB.Detect_And_Compute (Other, Blank);
         begin
            Reject (WTA2, WTA);
            Reject (WTA, WTA2);
            Reject (Empty_WTA2, WTA);
            Reject (WTA2, Empty_WTA);
            Reject (Empty_WTA2, Empty_WTA);
         end;
      end loop;
   end Match_Norm_Mismatch;

   procedure Match_Empty (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Blank : constant OpenCV.Core.Mat := Image (Textured => False);
      Default_Set : Feature_Set;
      procedure Check (A, B : Feature_Set) is
      begin
         for Mode in Matching.Matching_Mode loop
            declare
               Matches : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (A, B, Mode);
            begin
               Assert (Matches'Length = 0 and then Matches'First = 1 and then Matches'Last = 0,
                       "empty result bounds are not 1..0");
            end;
         end loop;
      end Check;
   begin
      Check (Default_Set, Default_Set);
      for Tuple in ORB.Tuple_Size loop
         declare
            Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            Full : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
            Empty_Set : constant Feature_Set := ORB.Detect_And_Compute (Detector, Blank);
         begin
            Assert (Count (Full) > 0 and then Is_Empty (Empty_Set), "empty matching fixture");
            Check (Empty_Set, Full);
            Check (Full, Empty_Set);
            Check (Empty_Set, Empty_Set);
         end;
      end loop;
   end Match_Empty;

   function Translated_Image (Source : OpenCV.Core.Mat) return OpenCV.Core.Mat is
      Result : OpenCV.Core.Mat := Image (Textured => False);
   begin
      for R in 0 .. 247 loop
         for C in 0 .. 250 loop
            Bytes.Set (Result, R + 8, C + 5, Bytes.Get (Source, R, C));
         end loop;
      end loop;
      return Result;
   end Translated_Image;

   procedure Match_Mutual (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Related : constant OpenCV.Core.Mat := Translated_Image (Source);
   begin
      for Tuple in ORB.Tuple_Size loop
         declare
            Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            Query : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
            Train : constant Feature_Set := ORB.Detect_And_Compute (Detector, Related);
            Nearest : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (Query, Train);
            Mutual : constant Matching.Descriptor_Match_Array :=
              Matching.Brute_Force_Match (Query, Train, Matching.Mutual_Nearest);
            Maximum : constant Matching.Binary_Descriptor_Distance :=
              (if Required_Norm (Query) = Hamming then 256 else 128);
            Previous : Natural := 0;
         begin
            Assert (Count (Query) > 0 and then Count (Train) > 0, "related scene fixture is empty");
            Assert (Nearest'Length = Count (Query), "related nearest count");
            Assert (Mutual'Length > 0 and then Mutual'Length <= Nearest'Length, "mutual count contract");
            for Item of Mutual loop
               Assert (Item.Query_Index > Previous and then Item.Query_Index <= Count (Query),
                       "mutual query order/bounds");
               Assert (Item.Train_Index <= Count (Train) and then Item.Distance <= Maximum,
                       "mutual train/distance bounds");
               Assert (Nearest (Item.Query_Index).Distance = Item.Distance,
                       "mutual pair does not have forward-nearest distance");
               Previous := Item.Query_Index;
            end loop;
            for I in Mutual'Range loop
               for J in Mutual'First .. I - 1 loop
                  Assert (Mutual (I).Train_Index /= Mutual (J).Train_Index, "mutual train index reused");
               end loop;
            end loop;
         end;
      end loop;
   end Match_Mutual;

   procedure Match_Preservation (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Related : constant OpenCV.Core.Mat := Translated_Image (Source);
   begin
      for Tuple in ORB.Tuple_Size loop
         declare
            Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            Query : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
            Train : constant Feature_Set := ORB.Detect_And_Compute (Detector, Related);
            Query_Data : constant OpenCV.Core.Mat := Descriptor_Copy (Query);
            Train_Data : constant OpenCV.Core.Mat := Descriptor_Copy (Train);
            Query_Points : constant Keypoint_Array := Keypoints (Query);
            Train_Points : constant Keypoint_Array := Keypoints (Train);
         begin
            for Mode in Matching.Matching_Mode loop
               declare
                  Matches : constant Matching.Descriptor_Match_Array := Matching.Brute_Force_Match (Query, Train, Mode);
               begin
                  Assert (Matches'Length > 0, "preservation fixture empty");
                  Assert_Same (Query_Data, Descriptor_Copy (Query));
                  Assert_Same (Train_Data, Descriptor_Copy (Train));
                  Assert (Query_Points = Keypoints (Query) and then Train_Points = Keypoints (Train),
                          "matching modified keypoints");
               end;
            end loop;
         end;
      end loop;
   end Match_Preservation;

   procedure Match_Lifetime (T : in out Fixture) is
      pragma Unreferenced (T);
      function Local_Matches return Matching.Descriptor_Match_Array is
         Source : constant OpenCV.Core.Mat := Image;
         Detector : ORB.Detector := ORB.Create;
         Features : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      begin
         ORB.Close (Detector);
         return Matching.Brute_Force_Match (Features, Features);
      end Local_Matches;
      Matches : constant Matching.Descriptor_Match_Array := Local_Matches;
   begin
      Assert (Matches'Length > 0, "lifetime fixture empty");
      for I in Matches'Range loop
         Assert (Matches (I).Query_Index = I and then Matches (I).Train_Index <= Matches'Length
                 and then Matches (I).Distance = 0, "match values lost with inputs/detector");
      end loop;
   end Match_Lifetime;

   procedure Match_Layout (T : in out Fixture) is
      pragma Unreferenced (T);
      function Layout (Field : Interfaces.Integer_32) return Interfaces.Integer_32
        with Import, Convention => C, External_Name => "features_test_match_layout";
      procedure Fill (Item : access ABI.C_Descriptor_Match)
        with Import, Convention => C, External_Name => "features_test_match";
      Item : aliased ABI.C_Descriptor_Match;
      type Positions is array (Natural range <>) of Natural;
      Offsets : constant Positions := [Item.Query_Index'Position, Item.Train_Index'Position, Item.Distance'Position];
      use type ABI.C_Descriptor_Match;
   begin
      Assert (ABI.C_Descriptor_Match'Size = Natural (Layout (0)) * System.Storage_Unit, "match size mismatch");
      Assert (ABI.C_Descriptor_Match'Alignment = Natural (Layout (1)), "match alignment mismatch");
      for I in Offsets'Range loop
         Assert (Offsets (I) = Natural (Layout (Interfaces.Integer_32 (I + 2))), "match field offset mismatch");
      end loop;
      Assert (Item.Query_Index'First_Bit = 0 and then Item.Train_Index'First_Bit = 0
              and then Item.Distance'First_Bit = 0, "match field is not byte-aligned");
      Fill (Item'Access);
      Assert (Item = (17, 23, 256), "C-written match interchange mismatch");
      Ada.Text_IO.Put_Line
        ("Match C/Ada layout: size" & Interfaces.Integer_32'Image (Layout (0)) &
         ", alignment" & Interfaces.Integer_32'Image (Layout (1)) &
         ", offsets" & Interfaces.Integer_32'Image (Layout (2)) &
         "/" & Interfaces.Integer_32'Image (Layout (3)) &
         "/" & Interfaces.Integer_32'Image (Layout (4)) & "; C-written interchange PASS");
   end Match_Layout;

   procedure Ratio_Oracles (T : in out Fixture) is
      pragma Unreferenced (T);
      function Pass (First, Second : Matching.Binary_Descriptor_Distance;
                     Ratio : OpenCV.Float64_Value) return Boolean is
        (Matching.Passes_Ratio_Test ((1, (1, First), (2, Second)), Ratio));
   begin
      Assert (Pass (1, 2, 0.80), "1/2 at .80 must pass");
      Assert (not Pass (2, 2, 0.80), "tie must reject");
      Assert (Pass (0, 1, 0.80), "0/1 must pass");
      Assert (not Pass (0, 0, 0.80), "duplicate exact pair must reject");
      Assert (not Pass (1, 2, 0.50), "strict equality must reject");
      Assert (Pass (1, 2, 0.51), "above strict boundary must pass");
   end Ratio_Oracles;

   procedure Ratio_Invalid (T : in out Fixture) is
      pragma Unreferenced (T);
      type Ratios is array (Positive range <>) of OpenCV.Float64_Value;
      Invalid : constant Ratios := [0.0, -0.1, 1.0, 1.1];
      Empty : constant Matching.Two_Nearest_Match_Array (1 .. 0) := [others => <>];
   begin
      for Ratio of Invalid loop
         begin
            Assert (not Matching.Passes_Ratio_Test ((1, (1, 1), (2, 2)), Ratio),
                    "invalid predicate ratio accepted");
            Assert (False, "invalid predicate ratio did not raise");
         exception
            when OpenCV.OpenCV_Error => null;
         end;
         begin
            declare
               Result : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Empty, Ratio);
               pragma Unreferenced (Result);
            begin
               Assert (False, "invalid filter ratio accepted on empty input");
            end;
         exception
            when OpenCV.OpenCV_Error => null;
         end;
      end loop;
   end Ratio_Invalid;

   procedure Ratio_Filter (T : in out Fixture) is
      pragma Unreferenced (T);
      use type Matching.Descriptor_Match_Array;
      Candidates : constant Matching.Two_Nearest_Match_Array :=
        [7 => (11, (5, 1), (6, 2)), 8 => (13, (7, 2), (8, 2)),
         9 => (17, (9, 0), (10, 1)), 10 => (19, (11, 0), (12, 0))];
      Empty : constant Matching.Two_Nearest_Match_Array (1 .. 0) := [others => <>];
      Accepted : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Candidates, 0.80);
      No_Input : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Empty, 0.80);
      Rejected : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Candidates (10 .. 10), 0.80);
      Passing : constant Matching.Two_Nearest_Match_Array := [Candidates (7), Candidates (9)];
      All_Pass : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Passing, 0.80);
   begin
      Assert (Accepted = [1 => (11, 5, 1), 2 => (17, 9, 0)], "filter fields/order differ");
      Assert (No_Input'First = 1 and then No_Input'Last = 0, "empty filter bounds");
      Assert (Rejected'First = 1 and then Rejected'Last = 0, "all-rejected bounds");
      Assert (All_Pass = Accepted, "all-accepted nearest fields/order differ");
   end Ratio_Filter;

   procedure Check_KNN2 (Tuple : ORB.Tuple_Size) is
      Source : constant OpenCV.Core.Mat := Image;
      Related : constant OpenCV.Core.Mat := Translated_Image (Source);
      Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
      Query : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Train : constant Feature_Set := ORB.Detect_And_Compute (Detector, Related);
      Query_Data : constant OpenCV.Core.Mat := Descriptor_Copy (Query);
      Train_Data : constant OpenCV.Core.Mat := Descriptor_Copy (Train);
      Query_Points : constant Keypoint_Array := Keypoints (Query);
      Train_Points : constant Keypoint_Array := Keypoints (Train);
      Pairs : constant Matching.Two_Nearest_Match_Array := Matching.Brute_Force_KNN_2 (Query, Train);
      Maximum : constant Matching.Binary_Descriptor_Distance :=
        (if Tuple = ORB.Two_Samples then 256 else 128);
   begin
      Assert (Count (Query) > 0 and then Count (Train) >= 2, "KNN2 fixture undersized");
      Assert (Pairs'Length = Count (Query), "KNN2 count differs from query");
      for I in Pairs'Range loop
         Assert (Pairs (I).Query_Index = I and then Pairs (I).Nearest.Train_Index <= Count (Train)
                 and then Pairs (I).Second_Nearest.Train_Index <= Count (Train)
                 and then Pairs (I).Nearest.Train_Index /= Pairs (I).Second_Nearest.Train_Index
                 and then Pairs (I).Nearest.Distance <= Pairs (I).Second_Nearest.Distance
                 and then Pairs (I).Second_Nearest.Distance <= Maximum, "KNN2 pair invariant");
      end loop;
      Assert_Same (Query_Data, Descriptor_Copy (Query));
      Assert_Same (Train_Data, Descriptor_Copy (Train));
      Assert (Query_Points = Keypoints (Query) and then Train_Points = Keypoints (Train),
              "KNN2 modified keypoints");
   end Check_KNN2;

   procedure KNN2_WTA2 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_KNN2 (ORB.Two_Samples);
   end KNN2_WTA2;
   procedure KNN2_WTA3 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_KNN2 (ORB.Three_Samples);
   end KNN2_WTA3;
   procedure KNN2_WTA4 (T : in out Fixture) is
      pragma Unreferenced (T);
   begin
      Check_KNN2 (ORB.Four_Samples);
   end KNN2_WTA4;

   procedure KNN2_Norm_Mismatch (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Blank : constant OpenCV.Core.Mat := Image (Textured => False);
      Detector : constant ORB.Detector := ORB.Create;
      WTA2 : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Empty_WTA2 : constant Feature_Set := ORB.Detect_And_Compute (Detector, Blank);
      procedure Reject (A, B : Feature_Set) is
      begin
         declare
            Pairs : constant Matching.Two_Nearest_Match_Array := Matching.Brute_Force_KNN_2 (A, B);
            pragma Unreferenced (Pairs);
         begin
            Assert (False, "KNN2 norm mismatch accepted");
         end;
      exception
         when OpenCV.OpenCV_Error => null;
      end Reject;
   begin
      for Tuple in ORB.Three_Samples .. ORB.Four_Samples loop
         declare
            Other : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            WTA : constant Feature_Set := ORB.Detect_And_Compute (Other, Source);
            Empty_WTA : constant Feature_Set := ORB.Detect_And_Compute (Other, Blank);
         begin
            Reject (WTA2, WTA); Reject (WTA, WTA2);
            Reject (Empty_WTA2, WTA); Reject (WTA, Empty_WTA2);
            Reject (WTA2, Empty_WTA); Reject (Empty_WTA, WTA2);
            Reject (Empty_WTA2, Empty_WTA); Reject (Empty_WTA, Empty_WTA2);
         end;
      end loop;
   end KNN2_Norm_Mismatch;

   procedure KNN2_Empty (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Blank : constant OpenCV.Core.Mat := Image (Textured => False);
      Default_Set : Feature_Set;
      procedure Check (A, B : Feature_Set) is
         Pairs : constant Matching.Two_Nearest_Match_Array := Matching.Brute_Force_KNN_2 (A, B);
      begin
         Assert (Pairs'First = 1 and then Pairs'Last = 0, "KNN2 empty bounds differ");
      end Check;
   begin
      Check (Default_Set, Default_Set);
      for Tuple in ORB.Tuple_Size loop
         declare
            Detector : constant ORB.Detector := ORB.Create ((Tuple => Tuple, others => <>));
            Full : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
            Empty_Set : constant Feature_Set := ORB.Detect_And_Compute (Detector, Blank);
         begin
            Check (Empty_Set, Full); Check (Full, Empty_Set); Check (Empty_Set, Empty_Set);
         end;
      end loop;
   end KNN2_Empty;

   procedure KNN2_Lifetime (T : in out Fixture) is
      pragma Unreferenced (T);
      function Local_Pairs return Matching.Two_Nearest_Match_Array is
         Source : constant OpenCV.Core.Mat := Image;
         Detector : ORB.Detector := ORB.Create;
         Features : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      begin
         ORB.Close (Detector);
         return Matching.Brute_Force_KNN_2 (Features, Features);
      end Local_Pairs;
      Pairs : constant Matching.Two_Nearest_Match_Array := Local_Pairs;
   begin
      Assert (Pairs'Length >= 2, "KNN2 lifetime fixture empty");
      for I in Pairs'Range loop
         Assert (Pairs (I).Query_Index = I and then Pairs (I).Nearest.Distance = 0
                 and then Pairs (I).Nearest.Train_Index <= Pairs'Length
                 and then Pairs (I).Second_Nearest.Train_Index <= Pairs'Length
                 and then Pairs (I).Nearest.Train_Index /= Pairs (I).Second_Nearest.Train_Index,
                 "KNN2 lost owned values after finalization");
      end loop;
   end KNN2_Lifetime;

   procedure KNN2_Related_Ratio (T : in out Fixture) is
      pragma Unreferenced (T);
      Source : constant OpenCV.Core.Mat := Image;
      Related : constant OpenCV.Core.Mat := Translated_Image (Source);
      Detector : constant ORB.Detector := ORB.Create;
      Query : constant Feature_Set := ORB.Detect_And_Compute (Detector, Source);
      Train : constant Feature_Set := ORB.Detect_And_Compute (Detector, Related);
      Pairs : constant Matching.Two_Nearest_Match_Array := Matching.Brute_Force_KNN_2 (Query, Train);
      Accepted : constant Matching.Descriptor_Match_Array := Matching.Filter_By_Ratio (Pairs, 0.80);
      Previous : Natural := 0;
   begin
      Assert (Pairs'Length = Count (Query) and then Accepted'Length <= Pairs'Length
              and then Accepted'Length > 0, "related scene ratio count invariant");
      for Item of Accepted loop
         declare
            Pair : constant Matching.Two_Nearest_Match := Pairs (Item.Query_Index);
         begin
            Assert (Item.Query_Index > Previous and then Item.Train_Index = Pair.Nearest.Train_Index
                    and then Item.Distance = Pair.Nearest.Distance
                    and then Matching.Passes_Ratio_Test (Pair, 0.80)
                    and then OpenCV.Float64_Value (Pair.Nearest.Distance) <
                      0.80 * OpenCV.Float64_Value (Pair.Second_Nearest.Distance),
                    "accepted item differs from strictly passing nearest");
            Previous := Item.Query_Index;
         end;
      end loop;
   end KNN2_Related_Ratio;

   procedure KNN2_Layout (T : in out Fixture) is
      pragma Unreferenced (T);
      function Layout (Field : Interfaces.Integer_32) return Interfaces.Integer_32
        with Import, Convention => C, External_Name => "features_test_knn2_layout";
      procedure Fill (Item : access ABI.C_KNN2_Match)
        with Import, Convention => C, External_Name => "features_test_knn2";
      Item : aliased ABI.C_KNN2_Match;
      type Positions is array (Natural range <>) of Natural;
      Offsets : constant Positions :=
        [Item.Query_Index'Position, Item.Nearest_Train_Index'Position, Item.Nearest_Distance'Position,
         Item.Second_Train_Index'Position, Item.Second_Distance'Position];
   begin
      Assert (ABI.C_KNN2_Match'Size = Natural (Layout (0)) * System.Storage_Unit, "KNN2 size mismatch");
      Assert (ABI.C_KNN2_Match'Alignment = Natural (Layout (1)), "KNN2 alignment mismatch");
      for I in Offsets'Range loop
         Assert (Offsets (I) = Natural (Layout (Interfaces.Integer_32 (I + 2))), "KNN2 field offset mismatch");
      end loop;
      Assert (Item.Query_Index'First_Bit = 0 and then Item.Nearest_Train_Index'First_Bit = 0
              and then Item.Nearest_Distance'First_Bit = 0 and then Item.Second_Train_Index'First_Bit = 0
              and then Item.Second_Distance'First_Bit = 0, "KNN2 field byte alignment");
      Fill (Item'Access);
      Assert (Item.Query_Index = 17 and then Item.Nearest_Train_Index = 23 and then Item.Nearest_Distance = 128
              and then Item.Second_Train_Index = 29 and then Item.Second_Distance = 256, "KNN2 C-written interchange");
      Ada.Text_IO.Put ("KNN2 C/Ada layout: size" & Interfaces.Integer_32'Image (Layout (0)) &
                       ", alignment" & Interfaces.Integer_32'Image (Layout (1)) & ", offsets");
      for I in 2 .. 6 loop
         Ada.Text_IO.Put (Interfaces.Integer_32'Image (Layout (Interfaces.Integer_32 (I))));
      end loop;
      Ada.Text_IO.Put_Line ("; C-written interchange PASS");
   end KNN2_Layout;

   package Caller is new AUnit.Test_Caller (Fixture);
   function Suite return AUnit.Test_Suites.Access_Test_Suite is
      Result : constant AUnit.Test_Suites.Access_Test_Suite :=
        new AUnit.Test_Suites.Test_Suite;
   begin
      Result.Add_Test
        (Caller.Create ("Native backend/version metadata",
                        Metadata'Access));
      Result.Add_Test
        (Caller.Create ("Owned detector lifecycle and idempotent Close",
                        Lifecycle'Access));
      Result.Add_Test
        (Caller.Create ("Typed ORB configuration round trip",
                        Config_Round_Trip'Access));
      Result.Add_Test
        (Caller.Create ("Blank image returns a paired empty result",
                        Blank_Image'Access));
      Result.Add_Test
        (Caller.Create ("Textured image: keypoints and UInt8 descriptor rows",
                        Paired_Result'Access));
      Result.Add_Test
        (Caller.Create ("Zero mask excludes all keypoints",
                        Zero_Mask'Access));
      Result.Add_Test
        (Caller.Create ("Full mask produces results without mutation",
                        Full_Mask'Access));
      Result.Add_Test
        (Caller.Create ("Reject non-UInt8 source",
                        Wrong_Depth'Access));
      Result.Add_Test
        (Caller.Create ("Reject multichannel source",
                        Wrong_Channels'Access));
      Result.Add_Test
        (Caller.Create ("Reject empty source",
                        Empty_Source'Access));
      Result.Add_Test
        (Caller.Create ("Reject collapsed fixed-profile pyramid",
                        Tiny_Source'Access));
      Result.Add_Test
        (Caller.Create ("Reject mismatched mask geometry",
                        Mask_Shape'Access));
      Result.Add_Test
        (Caller.Create ("Reject non-UInt8 mask",
                        Mask_Depth'Access));
      Result.Add_Test
        (Caller.Create ("Reject extraction from an unready detector",
                        Closed_Detector'Access));
      Result.Add_Test
        (Caller.Create ("Result survives detector close and source mutation",
                        Result_Lifetime'Access));
      Result.Add_Test
        (Caller.Create ("Descriptor_Copy cannot mutate stored pairing",
                        Descriptor_Isolation'Access));
      Result.Add_Test
        (Caller.Create ("Noncontiguous ROI agrees with its isolated clone",
                        Region_Isolation'Access));
      Result.Add_Test
        (Caller.Create ("Reject a positive keypoint index beyond the result",
                        Index_Rejection'Access));
      Result.Add_Test
        (Caller.Create ("WTA_K 3 and 4 carry Hamming_2 metadata",
                        Tuple_Norms'Access));
      Result.Add_Test
        (Caller.Create ("Reject a FAST threshold outside the public profile",
                        Config_Rejection'Access));
      Result.Add_Test (Caller.Create ("Nonbinary mask native semantics", Nonbinary_Masks'Access));
      Result.Add_Test (Caller.Create ("Compiler-derived C/Ada keypoint layout", ABI_Layout'Access));
      Result.Add_Test (Caller.Create ("Raw C ABI detector creation", ABI_Creation'Access));
      Result.Add_Test (Caller.Create ("Raw C ABI extraction/results with real Core handles", ABI_Extraction'Access));
      Result.Add_Test (Caller.Create ("Matching WTA2 Hamming self-match", Match_WTA2'Access));
      Result.Add_Test (Caller.Create ("Matching WTA3 Hamming2 self-match", Match_WTA3'Access));
      Result.Add_Test (Caller.Create ("Matching WTA4 Hamming2 self-match", Match_WTA4'Access));
      Result.Add_Test (Caller.Create ("Matching rejects different norms including empty sets", Match_Norm_Mismatch'Access));
      Result.Add_Test (Caller.Create ("Matching compatible empty sets in both modes", Match_Empty'Access));
      Result.Add_Test (Caller.Create ("Matching mutual-nearest translated scene", Match_Mutual'Access));
      Result.Add_Test (Caller.Create ("Matching preserves descriptors and keypoints", Match_Preservation'Access));
      Result.Add_Test (Caller.Create ("Matching values survive input/detector finalization", Match_Lifetime'Access));
      Result.Add_Test (Caller.Create ("Compiler-derived C/Ada match layout and interchange", Match_Layout'Access));
      Result.Add_Test (Caller.Create ("Pure Ada strict ratio boundary oracles", Ratio_Oracles'Access));
      Result.Add_Test (Caller.Create ("Pure Ada ratio invalid thresholds including empty filter", Ratio_Invalid'Access));
      Result.Add_Test (Caller.Create ("Pure Ada ratio filter fields/order/empty/all accepted/rejected", Ratio_Filter'Access));
      Result.Add_Test (Caller.Create ("KNN2 WTA2 Hamming invariants and preservation", KNN2_WTA2'Access));
      Result.Add_Test (Caller.Create ("KNN2 WTA3 Hamming2 invariants and preservation", KNN2_WTA3'Access));
      Result.Add_Test (Caller.Create ("KNN2 WTA4 Hamming2 invariants and preservation", KNN2_WTA4'Access));
      Result.Add_Test (Caller.Create ("KNN2 norm mismatch before empties", KNN2_Norm_Mismatch'Access));
      Result.Add_Test (Caller.Create ("KNN2 compatible empty inputs", KNN2_Empty'Access));
      Result.Add_Test (Caller.Create ("KNN2 owned values survive inputs/detector", KNN2_Lifetime'Access));
      Result.Add_Test (Caller.Create ("KNN2 translated scene strict ratio filter", KNN2_Related_Ratio'Access));
      Result.Add_Test (Caller.Create ("Compiler-derived C/Ada KNN2 layout/interchange", KNN2_Layout'Access));
      return Result;
   end Suite;
end Features_Tests;
