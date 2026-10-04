with Ada.Finalization;
with Interfaces;
with OpenCV.Core.Module_Interop;
with OpenCV.Features.Internal.C_API;
with System;

package body OpenCV.Features.Matching is
   package C renames OpenCV.Features.Internal.C_API;
   package Bridge renames OpenCV.Core.Module_Interop;
   use type System.Address;
   use type Interfaces.Integer_32;

   type Result_Guard is new Ada.Finalization.Limited_Controlled with record
      Handle : aliased System.Address := System.Null_Address;
   end record;
   overriding procedure Finalize (Self : in out Result_Guard);
   overriding procedure Finalize (Self : in out Result_Guard) is
   begin
      C.Match_Result_Destroy (Self.Handle);
      Self.Handle := System.Null_Address;
   end Finalize;

   function Brute_Force_Match
     (Query : Feature_Set; Train : Feature_Set;
      Mode : Matching_Mode := Nearest) return Descriptor_Match_Array
   is
      Guard : Result_Guard;
      Number : aliased Interfaces.Integer_32 := 0;
      Code : C.Status := C.Success;
      Norm : constant Interfaces.Integer_32 :=
        (if Required_Norm (Query) = Hamming then C.Hamming_Selector
         else C.Hamming_2_Selector);
      Selector : constant Interfaces.Integer_32 :=
        (if Mode = Nearest then C.Nearest_Selector else C.Mutual_Nearest_Selector);
      Maximum : constant Interfaces.Integer_32 :=
        (if Required_Norm (Query) = Hamming then 256 else 128);
      procedure Query_Input (Q : Bridge.Input_Mat_Handle) is
         procedure Train_Input (T : Bridge.Input_Mat_Handle) is
         begin
            Code := C.BF_Match (Q, T, Norm, Selector, Guard.Handle'Access, Number'Access);
         end Train_Input;
      begin
         Bridge.With_Input_Handle (Train.Data, Train_Input'Access);
      end Query_Input;
   begin
      if Required_Norm (Query) /= Required_Norm (Train) then
         raise OpenCV.OpenCV_Error with "Binary descriptor norms do not agree";
      end if;
      if Count (Train) > 262_143 then
         raise OpenCV.OpenCV_Error with "BFMatcher train descriptor limit is 262143";
      end if;
      if Is_Empty (Query) or else Is_Empty (Train) then
         return [1 .. 0 => <>];
      end if;
      Bridge.With_Input_Handle (Query.Data, Query_Input'Access);
      C.Check (Code, "Matching.Brute_Force_Match");
      if Guard.Handle = System.Null_Address or else Number < 0
        or else Number > Interfaces.Integer_32 (Count (Query))
        or else (Mode = Nearest and then Number /= Interfaces.Integer_32 (Count (Query)))
      then
         raise OpenCV.OpenCV_Error with "Invalid native match count";
      end if;
      --  Count is checked before allocating the public function result. No
      --  result-sized scratch array is placed on the primary stack.
      return Result : Descriptor_Match_Array (1 .. Natural (Number)) do
         for I in Result'Range loop
            declare
               Item : aliased C.C_Descriptor_Match;
            begin
               C.Check (C.Match_Result_Get (Guard.Handle, Interfaces.Integer_32 (I - 1),
                                           Item'Access), "Matching.Copy_Match");
               if Item.Query_Index < 0 or else Item.Query_Index >= Interfaces.Integer_32 (Count (Query))
                 or else Item.Train_Index < 0 or else Item.Train_Index >= Interfaces.Integer_32 (Count (Train))
                 or else Item.Distance < 0 or else Item.Distance > Maximum
                 or else (I > Result'First and then
                          Item.Query_Index < Interfaces.Integer_32 (Result (I - 1).Query_Index))
               then
                  raise OpenCV.OpenCV_Error with "Invalid native binary match";
               end if;
               Result (I) := (Positive (Item.Query_Index + 1),
                              Positive (Item.Train_Index + 1),
                              Binary_Descriptor_Distance (Item.Distance));
            end;
         end loop;
      end return;
   end Brute_Force_Match;
end OpenCV.Features.Matching;