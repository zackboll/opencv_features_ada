with AUnit.Assertions;
with AUnit.Test_Caller;
with AUnit.Test_Fixtures;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features.ORB;

package body Features_Tests is
   use AUnit.Assertions;
   use OpenCV.Features;
   package ORB renames OpenCV.Features.ORB;
   package Bytes renames OpenCV.Core.UInt8_Access;
   use type OpenCV.Core.Depth_Type;
   use type OpenCV.Core.Channel_Count;
   use type OpenCV.UInt8_Value;
   use type OpenCV.Float32_Value;

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
      return Result;
   end Suite;
end Features_Tests;
