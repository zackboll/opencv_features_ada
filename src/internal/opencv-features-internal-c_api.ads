with Interfaces;
with Interfaces.C;
with Interfaces.C.Strings;
with OpenCV.Core.Module_Interop;
with System;

package OpenCV.Features.Internal.C_API is
   subtype Status is Interfaces.Integer_32;
   Success : constant Status := 0;

   type C_Keypoint is record
      X, Y, Size, Angle, Response : Interfaces.C.C_float;
      Octave, Class_Id            : Interfaces.Integer_32;
   end record with Convention => C;

   type C_Descriptor_Match is record
      Query_Index, Train_Index, Distance : Interfaces.Integer_32;
   end record with Convention => C;

   type C_KNN2_Match is record
      Query_Index, Nearest_Train_Index, Nearest_Distance,
      Second_Train_Index, Second_Distance : Interfaces.Integer_32;
   end record with Convention => C;

   function BF_KNN2
     (Query, Train : OpenCV.Core.Module_Interop.Input_Mat_Handle;
      Norm : Interfaces.Integer_32; Result : access System.Address;
      Count : access Interfaces.Integer_32) return Status
     with Import, Convention => C, External_Name => "opencv_features_bf_knn2";
   function KNN2_Result_Get
     (Handle : System.Address; Index : Interfaces.Integer_32;
      Item : access C_KNN2_Match) return Status
     with Import, Convention => C, External_Name => "opencv_features_knn2_result_get";
   procedure KNN2_Result_Destroy (Handle : System.Address)
     with Import, Convention => C, External_Name => "opencv_features_knn2_result_destroy";

   Hamming_Selector : constant Interfaces.Integer_32 := 0;
   Hamming_2_Selector : constant Interfaces.Integer_32 := 1;
   Nearest_Selector : constant Interfaces.Integer_32 := 0;
   Mutual_Nearest_Selector : constant Interfaces.Integer_32 := 1;

   function BF_Match
     (Query, Train : OpenCV.Core.Module_Interop.Input_Mat_Handle;
      Norm, Mode : Interfaces.Integer_32;
      Result : access System.Address;
      Count : access Interfaces.Integer_32) return Status
     with Import, Convention => C, External_Name => "opencv_features_bf_match";
   function Match_Result_Get
     (Handle : System.Address; Index : Interfaces.Integer_32;
      Item : access C_Descriptor_Match) return Status
     with Import, Convention => C, External_Name => "opencv_features_match_result_get";

   function BF_Radius_Match
     (Query, Train : OpenCV.Core.Module_Interop.Input_Mat_Handle;
      Norm, Maximum_Distance : Interfaces.Integer_32;
      Result : access System.Address;
      Count : access Interfaces.Integer_32) return Status
     with Import, Convention => C, External_Name => "opencv_features_bf_radius_match";
   procedure Match_Result_Destroy (Handle : System.Address)
     with Import, Convention => C, External_Name => "opencv_features_match_result_destroy";

   function Native_Version return Interfaces.C.Strings.chars_ptr
     with Import, Convention => C,
          External_Name => "opencv_features_native_version";
   function Native_Backend return Interfaces.C.Strings.chars_ptr
     with Import, Convention => C,
          External_Name => "opencv_features_native_backend";
   function Last_Error return Interfaces.C.Strings.chars_ptr
     with Import, Convention => C,
          External_Name => "opencv_features_last_error";

   function ORB_Create
     (Maximum_Features, Tuple, Score, FAST_Threshold : Interfaces.Integer_32;
      Handle : access System.Address) return Status
     with Import, Convention => C,
          External_Name => "opencv_features_orb_create";
   procedure ORB_Destroy (Handle : System.Address)
     with Import, Convention => C,
          External_Name => "opencv_features_orb_destroy";

   function ORB_Extract
     (Handle : System.Address;
      Image : OpenCV.Core.Module_Interop.Input_Mat_Handle;
      Result : access System.Address;
      Count : access Interfaces.Integer_32) return Status
     with Import, Convention => C,
          External_Name => "opencv_features_orb_extract";

   function ORB_Extract_Masked
     (Handle : System.Address;
      Image, Mask : OpenCV.Core.Module_Interop.Input_Mat_Handle;
      Result : access System.Address;
      Count : access Interfaces.Integer_32) return Status
     with Import, Convention => C,
          External_Name => "opencv_features_orb_extract_masked";

   function Result_Point
     (Handle : System.Address; Index : Interfaces.Integer_32;
      Point : access C_Keypoint) return Status
     with Import, Convention => C,
          External_Name => "opencv_features_result_point";

   function Result_Descriptors
     (Handle : System.Address;
      Destination : OpenCV.Core.Module_Interop.Output_Mat_Handle) return Status
     with Import, Convention => C,
          External_Name => "opencv_features_result_descriptors";

   procedure Result_Destroy (Handle : System.Address)
     with Import, Convention => C,
          External_Name => "opencv_features_result_destroy";

   procedure Check (Code : Status; Operation : String);
end OpenCV.Features.Internal.C_API;
