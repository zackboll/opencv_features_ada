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
   use type Interfaces.Unsigned_64;
   use type OpenCV.Float64_Value;

   type KNN2_Guard is new Ada.Finalization.Limited_Controlled with record
      Handle : aliased System.Address := System.Null_Address;
   end record;
   overriding procedure Finalize (Self : in out KNN2_Guard);
   overriding procedure Finalize (Self : in out KNN2_Guard) is
   begin
      C.KNN2_Result_Destroy (Self.Handle);
      Self.Handle := System.Null_Address;
   end Finalize;

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
   function Brute_Force_KNN_2
     (Query : Feature_Set; Train : Feature_Set) return Two_Nearest_Match_Array
   is
      Guard : KNN2_Guard;
      Number : aliased Interfaces.Integer_32 := 0;
      Code : C.Status := C.Success;
      Norm : constant Interfaces.Integer_32 :=
        (if Required_Norm (Query) = Hamming then C.Hamming_Selector else C.Hamming_2_Selector);
      Maximum : constant Interfaces.Integer_32 :=
        (if Required_Norm (Query) = Hamming then 256 else 128);
      procedure Query_Input (Q : Bridge.Input_Mat_Handle) is
         procedure Train_Input (T : Bridge.Input_Mat_Handle) is
         begin
            Code := C.BF_KNN2 (Q, T, Norm, Guard.Handle'Access, Number'Access);
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
      if Count (Train) < 2 then
         raise OpenCV.OpenCV_Error with "KNN2 requires two train rows";
      end if;
      Bridge.With_Input_Handle (Query.Data, Query_Input'Access);
      C.Check (Code, "Matching.Brute_Force_KNN_2");
      if Guard.Handle = System.Null_Address or else Number < 0
        or else Number /= Interfaces.Integer_32 (Count (Query))
      then
         raise OpenCV.OpenCV_Error with "Invalid native KNN2 count";
      end if;
      return Result : Two_Nearest_Match_Array (1 .. Natural (Number)) do
         for I in Result'Range loop
            declare
               Item : aliased C.C_KNN2_Match;
            begin
               C.Check (C.KNN2_Result_Get (Guard.Handle, Interfaces.Integer_32 (I - 1),
                                          Item'Access), "Matching.Copy_KNN2");
               if Item.Query_Index /= Interfaces.Integer_32 (I - 1)
                 or else Item.Nearest_Train_Index < 0
                 or else Item.Nearest_Train_Index >= Interfaces.Integer_32 (Count (Train))
                 or else Item.Second_Train_Index < 0
                 or else Item.Second_Train_Index >= Interfaces.Integer_32 (Count (Train))
                 or else Item.Nearest_Train_Index = Item.Second_Train_Index
                 or else Item.Nearest_Distance < 0 or else Item.Second_Distance > Maximum
                 or else Item.Nearest_Distance > Item.Second_Distance
               then
                  raise OpenCV.OpenCV_Error with "Invalid native KNN2 pair";
               end if;
               Result (I) :=
                 (Positive (Item.Query_Index + 1),
                  (Positive (Item.Nearest_Train_Index + 1), Binary_Descriptor_Distance (Item.Nearest_Distance)),
                  (Positive (Item.Second_Train_Index + 1), Binary_Descriptor_Distance (Item.Second_Distance)));
            end;
         end loop;
      end return;
   end Brute_Force_KNN_2;

   function Brute_Force_Radius_Match
     (Query : Feature_Set; Train : Feature_Set;
      Maximum_Distance : Binary_Descriptor_Distance)
      return Descriptor_Match_Array
   is
      Guard : Result_Guard;
      Number : aliased Interfaces.Integer_32 := 0;
      Code : C.Status := C.Success;
      Norm : constant Interfaces.Integer_32 :=
        (if Required_Norm (Query) = Hamming then C.Hamming_Selector
         else C.Hamming_2_Selector);
      Maximum : constant Binary_Descriptor_Distance :=
        (if Required_Norm (Query) = Hamming then 256 else 128);
      Previous_Query : Interfaces.Integer_32 := -1;
      Previous_Distance : Interfaces.Integer_32 := -1;
      procedure Query_Input (Q : Bridge.Input_Mat_Handle) is
         procedure Train_Input (T : Bridge.Input_Mat_Handle) is
         begin
            Code := C.BF_Radius_Match (Q, T, Norm, Interfaces.Integer_32 (Maximum_Distance),
                                      Guard.Handle'Access, Number'Access);
         end Train_Input;
      begin
         Bridge.With_Input_Handle (Train.Data, Train_Input'Access);
      end Query_Input;
   begin
      if Required_Norm (Query) /= Required_Norm (Train) then
         raise OpenCV.OpenCV_Error with "Binary descriptor norms do not agree";
      end if;
      if Maximum_Distance = 0 or else Maximum_Distance > Maximum then
         raise OpenCV.OpenCV_Error with "Invalid binary radius threshold";
      end if;
      if Is_Empty (Query) or else Is_Empty (Train) then
         return [1 .. 0 => <>];
      end if;
      Bridge.With_Input_Handle (Query.Data, Query_Input'Access);
      C.Check (Code, "Matching.Brute_Force_Radius_Match");
      if Guard.Handle = System.Null_Address or else Number < 0
        or else Interfaces.Unsigned_64 (Number) > Interfaces.Unsigned_64 (Natural'Last)
      then
         raise OpenCV.OpenCV_Error with "Invalid native radius count";
      end if;
      return Result : Descriptor_Match_Array (1 .. Natural (Number)) do
         for I in Result'Range loop
            declare
               Item : aliased C.C_Descriptor_Match;
            begin
               C.Check (C.Match_Result_Get (Guard.Handle, Interfaces.Integer_32 (I - 1),
                                           Item'Access), "Matching.Copy_Radius");
               if Item.Query_Index < 0
                 or else Item.Query_Index >= Interfaces.Integer_32 (Count (Query))
                 or else Item.Train_Index < 0
                 or else Item.Train_Index >= Interfaces.Integer_32 (Count (Train))
                 or else Item.Distance < 0
                 or else Item.Distance > Interfaces.Integer_32 (Maximum_Distance)
                 or else Item.Query_Index < Previous_Query
                 or else (Item.Query_Index = Previous_Query and then Item.Distance < Previous_Distance)
               then
                  raise OpenCV.OpenCV_Error with "Invalid native radius match";
               end if;
               Previous_Query := Item.Query_Index;
               Previous_Distance := Item.Distance;
               Result (I) := (Positive (Item.Query_Index + 1), Positive (Item.Train_Index + 1),
                              Binary_Descriptor_Distance (Item.Distance));
            end;
         end loop;
      end return;
   end Brute_Force_Radius_Match;

   procedure Validate_Ratio (Maximum_Ratio : OpenCV.Float64_Value) is
   begin
      --  Negated positive validity rejects NaN as well as infinities/range
      --  errors: neither unordered comparison can establish validity.
      if not (Maximum_Ratio > 0.0 and then Maximum_Ratio < 1.0) then
         raise OpenCV.OpenCV_Error with "Ratio threshold must satisfy 0 < ratio < 1";
      end if;
   end Validate_Ratio;

   function Passes_Ratio_Test
     (Candidate : Two_Nearest_Match; Maximum_Ratio : OpenCV.Float64_Value)
      return Boolean
   is
   begin
      Validate_Ratio (Maximum_Ratio);
      return OpenCV.Float64_Value (Candidate.Nearest.Distance) <
        Maximum_Ratio * OpenCV.Float64_Value (Candidate.Second_Nearest.Distance);
   end Passes_Ratio_Test;

   function Filter_By_Ratio
     (Candidates : Two_Nearest_Match_Array; Maximum_Ratio : OpenCV.Float64_Value)
      return Descriptor_Match_Array
   is
      Number : Natural := 0;
   begin
      Validate_Ratio (Maximum_Ratio);
      for Candidate of Candidates loop
         if Passes_Ratio_Test (Candidate, Maximum_Ratio) then
            Number := Number + 1;
         end if;
      end loop;
      return Result : Descriptor_Match_Array (1 .. Number) do
         declare
            Position : Natural := 0;
         begin
            for Candidate of Candidates loop
               if Passes_Ratio_Test (Candidate, Maximum_Ratio) then
                  Position := Position + 1;
                  Result (Position) := (Candidate.Query_Index, Candidate.Nearest.Train_Index,
                                        Candidate.Nearest.Distance);
               end if;
            end loop;
         end;
      end return;
   end Filter_By_Ratio;
end OpenCV.Features.Matching;