# ORB feature extraction

[OpenCV.Features.ORB](api:OpenCV.Features.ORB) detects ORB (Oriented FAST and
Rotated BRIEF) keypoints in an 8-bit grayscale `OpenCV.Core.Mat` and computes a
32-byte binary descriptor for each one. The result is an
[OpenCV.Features.Feature_Set](api:OpenCV.Features.Feature_Set) that pairs Ada
keypoint values with a Core-owned descriptor matrix.

## Construct a detector

[Create](api:OpenCV.Features.ORB.Create) returns a ready
[Detector](api:OpenCV.Features.ORB.Detector). With no argument it uses the
defaults of [Configuration](api:OpenCV.Features.ORB.Configuration):

| Field | Default | Accepted values | Meaning |
| --- | --- | --- | --- |
| `Maximum_Features` | 500 | 1 .. 1_073_741_823 | Requested target (OpenCV `nfeatures`), not a cap |
| `Tuple` | `Two_Samples` | `Two_Samples`, `Three_Samples`, `Four_Samples` | OpenCV `WTA_K` 2, 3 or 4 |
| `Score` | `Harris_Score` | `Harris_Score`, `FAST_Score` | Candidate ranking measure |
| `FAST_Threshold` | 20 | 0 .. 255 | FAST intensity-difference threshold |

Out-of-range values raise `OpenCV.OpenCV_Error` from `Create`; a zero
`Maximum_Features` is already rejected by its `Positive` subtype. The
structural profile is fixed in this release: scale factor 1.2, eight pyramid
levels, edge threshold 31, first level 0 and patch size 31.
[Parameters](api:OpenCV.Features.ORB.Parameters) returns the configuration a
ready detector was created with.

## Extract features

[Detect_And_Compute](api:OpenCV.Features.ORB.Detect_And_Compute/1) takes the
detector and an image; the [masked overload](api:OpenCV.Features.ORB.Detect_And_Compute/2)
also takes a detection mask. Requirements and behavior:

- The image must be a nonempty, two-dimensional `UInt8` single-channel Mat of at
  least 2x2, within a conservative native size envelope
  (see `docs/orb-contract.md`). Anything else raises `OpenCV_Error`.
- The image (and mask) are copied before native detection and are never
  modified. A Region is treated as an isolated image: keypoint coordinates are
  local to it, and a noncontiguous Region gives the same result as its packed
  clone.
- A mask must have the image's rows, columns and type. Keypoints are detected
  only where it is nonzero; descriptor patches may still sample outside it. An
  all-zero mask gives an empty result. Use only 0 and 255 for portable results:
  OpenCV 4.x and 5.0 treat other nonzero values differently in the pyramid.
- A valid image without detectable features returns an empty set, not an
  error.
- [Count](api:OpenCV.Features.Count) is the number actually produced. It can be
  smaller than `Maximum_Features`, or larger when native responses tie.

## Read keypoints and descriptors

- [Point](api:OpenCV.Features.Point) returns one keypoint by one-based index,
  and [Keypoints](api:OpenCV.Features.Keypoints) returns all of them with bounds
  `1 .. Count`. An index beyond `Count` raises `OpenCV_Error`.
- A [Keypoint](api:OpenCV.Features.Keypoint) holds `Position` (X column, Y row,
  in the input's pixel frame), `Size`, `Angle_Degrees`, `Response`, `Octave`
  (0 .. 7) and `Class_Id`, copied unchanged from OpenCV.
- Keypoint `I` is paired with descriptor row `I - 1`;
  [Descriptor_Row](api:OpenCV.Features.Descriptor_Row) performs that mapping
  with bounds checking.
- [Descriptor_Copy](api:OpenCV.Features.Descriptor_Copy) returns a deep,
  caller-owned copy: `Count` rows by 32 columns of `UInt8` for a nonempty
  result, or an empty Mat. Changing the copy never affects the set. Matching
  operations read a set's descriptors directly, so no copy is needed for them.
- [Required_Norm](api:OpenCV.Features.Required_Norm) is `Hamming` for
  `Two_Samples` and `Hamming_2` for `Three_Samples` or `Four_Samples`, also for
  empty results. Matching requires both sets to agree.

## Lifetime

A `Feature_Set` owns its keypoints and descriptors. It remains valid after the
detector is closed or finalized and after the input image or mask is changed.
[Close](api:OpenCV.Features.ORB.Close) releases the native detector early and
is idempotent; finalization does the same automatically. Do not share one
detector between concurrent extractions, and do not close it or modify the
input while an extraction is running.

## Complete example

This is `examples/src/orb_synthetic.adb`, built and run by the repository's CI.
It synthesizes a textured 256x256 image, extracts features with the default
configuration, and copies the descriptors.

```ada
with Ada.Text_IO;
with OpenCV.Core.UInt8_Access;
with OpenCV.Features.ORB;

procedure ORB_Synthetic is
   package Features renames OpenCV.Features;
   package ORB renames OpenCV.Features.ORB;
   Image : OpenCV.Core.Mat := OpenCV.Core.Create
     (256, 256, (Depth => OpenCV.Core.UInt8, Channels => 1));
   Detector : ORB.Detector := ORB.Create;
begin
   for Row in 0 .. 255 loop
      for Column in 0 .. 255 loop
         OpenCV.Core.UInt8_Access.Set
           (Image, Row, Column,
            OpenCV.UInt8_Value
              ((Row * 37 + Column * 17 + (Row * Column mod 251)) mod 256));
      end loop;
   end loop;
   declare
      Result : constant Features.Feature_Set := ORB.Detect_And_Compute (Detector, Image);
      Descriptors : constant OpenCV.Core.Mat := Features.Descriptor_Copy (Result);
   begin
      Ada.Text_IO.Put_Line
        ("OpenCV " & Features.Native_Version & " / " & Features.Native_Backend);
      Ada.Text_IO.Put_Line ("Keypoints:" & Natural'Image (Features.Count (Result)));
      Ada.Text_IO.Put_Line
        ("Descriptor rows:" & Natural'Image (Descriptors.Rows));
      Ada.Text_IO.Put_Line
        ("Required matcher norm: " & Features.Binary_Descriptor_Norm'Image
           (Features.Required_Norm (Result)));
      ORB.Close (Detector);
      --  Result remains valid after Close. Do not use these features as a
      --  navigation measurement until matching and geometric verification
      --  have been implemented in subsequent modules/slices.
   end;
end ORB_Synthetic;
```

Run it with:

```sh
alr -n -C examples build
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic
```

Output observed on Linux with OpenCV 4.10.0 (counts depend on the native
OpenCV version):

```text
OpenCV 4.10.0 / features2d
Keypoints: 393
Descriptor rows: 393
Required matcher norm: HAMMING
```

Next: the Binary matching guide.
