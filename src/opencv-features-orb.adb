with Ada.Containers;
with Interfaces;
with OpenCV.Core.Module_Interop;
with OpenCV.Features.Internal.C_API;

package body OpenCV.Features.ORB is
   package C renames OpenCV.Features.Internal.C_API;
   package Bridge renames OpenCV.Core.Module_Interop;
   use type System.Address;

   type Result_Guard is new Ada.Finalization.Limited_Controlled with record
      Handle : aliased System.Address := System.Null_Address;
   end record;
   overriding procedure Finalize (Self : in out Result_Guard);

   overriding procedure Finalize (Self : in out Result_Guard) is
   begin
      C.Result_Destroy (Self.Handle);
      Self.Handle := System.Null_Address;
   end Finalize;

   function Tuple_Value (Value : Tuple_Size) return Interfaces.Integer_32 is
   begin
      case Value is
         when Two_Samples   => return 2;
         when Three_Samples => return 3;
         when Four_Samples  => return 4;
      end case;
   end Tuple_Value;

   function Create (Parameters : Configuration := (others => <>))
      return Detector
   is
   begin
      if Parameters.Maximum_Features > 2_147_483_647 / 2
        or else Parameters.FAST_Threshold > 255
      then
         raise OpenCV.OpenCV_Error with "ORB configuration is outside the supported profile";
      end if;
      return Result : Detector do
         C.Check
           (C.ORB_Create
              (Interfaces.Integer_32 (Parameters.Maximum_Features),
               Tuple_Value (Parameters.Tuple),
               Interfaces.Integer_32 (Score_Kind'Pos (Parameters.Score)),
               Interfaces.Integer_32 (Parameters.FAST_Threshold),
               Result.Handle'Access), "ORB.Create");
         Result.Config := Parameters;
      end return;
   end Create;

   procedure Close (Self : in out Detector) is
   begin
      C.ORB_Destroy (Self.Handle);
      Self.Handle := System.Null_Address;
   end Close;

   overriding procedure Finalize (Self : in out Detector) is
   begin
      Close (Self);
   end Finalize;

   function Is_Ready (Self : Detector) return Boolean is
     (Self.Handle /= System.Null_Address);

   function Parameters (Self : Detector) return Configuration is
   begin
      if not Is_Ready (Self) then
         raise OpenCV.OpenCV_Error with "ORB detector is not ready";
      end if;
      return Self.Config;
   end Parameters;

   procedure Validate_Image (Image : OpenCV.Core.Mat) is
      use type OpenCV.Core.Depth_Type;
      use type OpenCV.Core.Channel_Count;
   begin
      if Image.Is_Empty or else Image.Dimension_Count /= 2
        or else Image.Depth /= OpenCV.Core.UInt8 or else Image.Channels /= 1
        or else Image.Rows < 2 or else Image.Columns < 2
      then
         raise OpenCV.OpenCV_Error with "ORB requires a two-dimensional UInt8 C1 image of at least 2x2";
      end if;
   end Validate_Image;

   function Extract
     (Self : Detector; Image, Mask : OpenCV.Core.Mat; Masked : Boolean)
      return Feature_Set
   is
      use type Interfaces.Integer_32;
      Guard : Result_Guard;
      Number : aliased Interfaces.Integer_32 := 0;
      Code : C.Status := C.Success;
      procedure Input (Source : Bridge.Input_Mat_Handle) is
         procedure Selection (Mask_Handle : Bridge.Input_Mat_Handle) is
         begin
            Code := C.ORB_Extract_Masked
              (Self.Handle, Source, Mask_Handle, Guard.Handle'Access,
               Number'Access);
         end Selection;
      begin
         if Masked then
            Bridge.With_Input_Handle (Mask, Selection'Access);
         else
            Code := C.ORB_Extract
              (Self.Handle, Source, Guard.Handle'Access, Number'Access);
         end if;
      end Input;
   begin
      if not Is_Ready (Self) then
         raise OpenCV.OpenCV_Error with "ORB detector is not ready";
      end if;
      Validate_Image (Image);
      if Masked then
         Validate_Image (Mask);
         if Image.Rows /= Mask.Rows or else Image.Columns /= Mask.Columns then
            raise OpenCV.OpenCV_Error with "ORB mask geometry must match the image";
         end if;
      end if;
      Bridge.With_Input_Handle (Image, Input'Access);
      C.Check (Code, "ORB.Detect_And_Compute");
      if Guard.Handle = System.Null_Address or else Number < 0 then
         raise OpenCV.OpenCV_Error with "Invalid native ORB result";
      end if;

      --  Number is validated before any result-sized allocation. The private
      --  vector grows on the heap, not in an unbounded stack/secondary-stack
      --  scratch array. Guard frees the native temporary on every path.
      return Result : Feature_Set do
         Result.Norm :=
           (if Self.Config.Tuple = Two_Samples then Hamming else Hamming_2);
         Result.Points.Reserve_Capacity (Ada.Containers.Count_Type (Number));
         for I in 1 .. Natural (Number) loop
            declare
               Native : aliased C.C_Keypoint;
            begin
               C.Check
                 (C.Result_Point
                    (Guard.Handle, Interfaces.Integer_32 (I - 1), Native'Access),
                  "ORB.Copy_Keypoint");
               Result.Points.Append
                 (Keypoint'
                    (Position => (X => OpenCV.Float32_Value (Native.X),
                                  Y => OpenCV.Float32_Value (Native.Y)),
                     Size => OpenCV.Float32_Value (Native.Size),
                     Angle_Degrees => OpenCV.Float32_Value (Native.Angle),
                     Response => OpenCV.Float32_Value (Native.Response),
                     Octave => Native.Octave, Class_Id => Native.Class_Id));
            end;
         end loop;
         declare
            procedure Output (Destination : Bridge.Output_Mat_Handle) is
            begin
               Code := C.Result_Descriptors (Guard.Handle, Destination);
            end Output;
         begin
            Bridge.With_Output_Handle (Result.Data, Output'Access);
            C.Check (Code, "ORB.Copy_Descriptors");
         end;
      end return;
   end Extract;

   function Detect_And_Compute
     (Self : Detector; Image : OpenCV.Core.Mat) return Feature_Set
   is
      Empty_Mask : OpenCV.Core.Mat;
   begin
      return Extract (Self, Image, Empty_Mask, False);
   end Detect_And_Compute;

   function Detect_And_Compute
     (Self : Detector; Image, Mask : OpenCV.Core.Mat) return Feature_Set is
   begin
      return Extract (Self, Image, Mask, True);
   end Detect_And_Compute;
end OpenCV.Features.ORB;
