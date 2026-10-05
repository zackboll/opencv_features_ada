with OpenCV.Core;

--  Test-only child: deliberately constructed paired data, never installed as
--  a production descriptor generator or public construction API.
package OpenCV.Features.Radius_Fixtures is
   function Paired (Data : OpenCV.Core.Mat; Norm : Binary_Descriptor_Norm)
      return Feature_Set;
end OpenCV.Features.Radius_Fixtures;