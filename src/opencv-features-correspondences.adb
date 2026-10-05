package body OpenCV.Features.Correspondences is
   function From_Matches
     (Query   : Feature_Set;
      Train   : Feature_Set;
      Matches : Matching.Descriptor_Match_Array)
      return Point_Correspondence_Array
   is
      --  Positive-indexed arrays have at most Natural'Last elements, so their
      --  length and the canonical 1-based result bounds are representable.
      Number      : constant Natural := Matches'Length;
      Query_Count : constant Natural := Count (Query);
      Train_Count : constant Natural := Count (Train);
   begin
      for Item of Matches loop
         if Item.Query_Index > Query_Count then
            raise OpenCV.OpenCV_Error with "Correspondence query index is outside the result";
         end if;
         if Item.Train_Index > Train_Count then
            raise OpenCV.OpenCV_Error with "Correspondence train index is outside the result";
         end if;
      end loop;

      --  No result-sized scratch array; allocation/construction follows the
      --  complete preflight, and no partial function result can be published.
      return Result : Point_Correspondence_Array (1 .. Number) do
         for I in Result'Range loop
            declare
               Item : constant Matching.Descriptor_Match :=
                 Matches (Matches'First + (I - 1));
            begin
               Result (I) :=
                 (Query_Index => Item.Query_Index,
                  Train_Index => Item.Train_Index,
                  Query_Point => Point (Query, Item.Query_Index).Position,
                  Train_Point => Point (Train, Item.Train_Index).Position,
                  Distance    => Item.Distance);
            end;
         end loop;
      end return;
   end From_Matches;
end OpenCV.Features.Correspondences;