with Ada.Containers;

package body OpenCV.Features.Radius_Fixtures is
   function Paired (Data : OpenCV.Core.Mat; Norm : Binary_Descriptor_Norm)
      return Feature_Set
   is
   begin
      return Result : Feature_Set do
         Result.Norm := Norm;
         Result.Data := Data.Clone;
         Result.Points.Reserve_Capacity (Ada.Containers.Count_Type (Data.Rows));
         for I in 1 .. Data.Rows loop
            Result.Points.Append
              (Keypoint'(Position => (OpenCV.Float32_Value (I), 0.0),
                         Size => 1.0, Angle_Degrees => 0.0, Response => 0.0,
                         Octave => 0, Class_Id => OpenCV.Int32_Value (I)));
         end loop;
      end return;
   end Paired;
end OpenCV.Features.Radius_Fixtures;