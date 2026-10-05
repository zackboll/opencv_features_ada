with OpenCV.Core;

--  Test-only child: deliberately constructed paired data, never installed as
--  a production descriptor generator or public construction API.
package OpenCV.Features.Radius_Fixtures is
   --  Optional exact keypoint values for structural conversion tests; the
   --  supplied nonempty array must contain one keypoint per descriptor row.
   function Paired (Data : OpenCV.Core.Mat; Norm : Binary_Descriptor_Norm;
                    Points : Keypoint_Array := [1 .. 0 => <>])
      return Feature_Set;
end OpenCV.Features.Radius_Fixtures;