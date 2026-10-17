# GNATdoc initial public inventory (DOC-001)

Measured at production main `c2b6c6e9763d505d1624b0ce9d1034326897002c` with
GNATdoc 26.0.0 (20260415), `--generate public --style leading`, against the
indexed `opencv_core` 0.5.0 release (origin `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`).
These are the **initial** measurements; later documentation changes update the
Features-owned baselines, not this historical record.

Every public declaration is rendered by GNATdoc. Rendering is not documentation:
an element is *documented* only when its rendered prose equals the source
comment that GNATdoc attached to that exact declaration, is not shared with the
package description, and passes a minimal word floor (see
[the foundation record](gnatdoc-foundation.md#coverage-model)).

## Summary

| Package | Elements | Rendered | Documented |
| --- | ---: | ---: | ---: |
| `OpenCV.Features` | 40 | 40 | 3 |
| `OpenCV.Features.Correspondences` | 13 | 13 | 1 |
| `OpenCV.Features.Matching` | 40 | 40 | 5 |
| `OpenCV.Features.ORB` | 34 | 34 | 2 |

Total: 127 elements; 127 rendered; 11 documented (8.6614%); 116 gaps.

| Element category | Elements | Rendered | Documented |
| --- | ---: | ---: | ---: |
| field | 23 | 23 | 0 |
| function | 20 | 20 | 9 |
| literal | 9 | 9 | 0 |
| package | 4 | 4 | 0 |
| parameter | 33 | 33 | 0 |
| procedure | 1 | 1 | 0 |
| return | 20 | 20 | 0 |
| type | 17 | 17 | 2 |

| Gap reason | Count |
| --- | ---: |
| no rendered prose | 108 |
| source block is shared by the package description and a declaration | 8 |

Warnings: 110 raw (2 private-part, 108 public); new: 0; stale baseline entries: 0.
Coverage baseline: 116 gaps; new: 0; stale: 0.

Four package descriptions and four first declarations share one source block:
the comment directly after `package ... is` is both the package description
and the leading comment of the first declaration (`Keypoint`, `Tuple_Size`,
`Matching_Mode`, `Point_Correspondence`). In three packages that block is only
the SPDX identifier; in `OpenCV.Features` it also contains one sentence. Neither
side of a shared block is credited.

The eleven credited elements are the existing leading comments of two types
(`Feature_Set`, `Detector`) and nine functions (`Descriptor_Row`,
`Descriptor_Copy`, the first `Detect_And_Compute` overload, the five matching
operations and `From_Matches`). The second
`Detect_And_Compute` overload (with `Mask`) has no attached comment. No
parameter, return value, record component or enumeration literal is documented.
Crediting is mechanical: for example, the existing `Detector` comment mostly
describes the fixed structural profile; DOC-002 reviews its content.

## Public units and exclusions

| Unit | Source | Published |
| --- | --- | --- |
| `OpenCV.Features` | `src/opencv-features.ads` | yes |
| `OpenCV.Features.ORB` | `src/opencv-features-orb.ads` | yes |
| `OpenCV.Features.Matching` | `src/opencv-features-matching.ads` | yes |
| `OpenCV.Features.Correspondences` | `src/opencv-features-correspondences.ads` | yes |
| `OpenCV.Features.Internal` | `src/internal/opencv-features-internal.ads` | no (internal) |
| `OpenCV.Features.Internal.C_API` | `src/internal/opencv-features-internal-c_api.ads` | no (17-entry C ABI imports) |

The public specifications reference only Ada runtime units and the indexed
Core release, so `docs_api.gpr` exposes no internal unit to GNATdoc at all.
Core's and the crate configuration's project files are excluded from
publication. The site validator rejects any `.Internal` or `OpenCV.Core` unit.

## Warnings

110 raw GNATdoc warnings: 108 on public declarations and 2 in the private part
of `OpenCV.Features.ORB` (the overriding `Finalize` and its parameter). There
are no project, error or unclassified diagnostics. The stable, line-independent
identities are in [gnatdoc-warning-baseline.txt](gnatdoc-warning-baseline.txt).

## Declarations, members and observed anchors

Members list parameters (with mode, subtype and default), function results,
record components (with defaults) and enumeration literals, exactly as parsed
from the source. Anchors are the first 12 hexadecimal digits of the observed
native `h4` ids; the complete values are in
[gnatdoc-native-anchors.json](gnatdoc-native-anchors.json). "Ownership-sensitive"
is mechanical: the profile uses a public limited type or `OpenCV.Core.Mat`.

### `OpenCV.Features`

Source `src/opencv-features.ads`; native page `8aee7d25112f028c5446a96519872c18ad78baa4beac4c4e2a13798d7521472c.html`. Package description: gap (source block is shared by the package description and a declaration).

| Declaration | Kind | Members | Existing comment | Description credit | Native anchor | Ownership-sensitive |
| --- | --- | --- | --- | --- | --- | --- |
| `Keypoint` | type record | Position : OpenCV.Float32_Point<br>Size : OpenCV.Float32_Value<br>Angle_Degrees : OpenCV.Float32_Value<br>Response : OpenCV.Float32_Value<br>Octave : OpenCV.Int32_Value<br>Class_Id : OpenCV.Int32_Value | 2 line(s), shared with package description | gap | `cfdc5b6aecc0…` | — |
| `Keypoint_Array` | type array | — | none | gap | `56ef4787cce1…` | — |
| `Binary_Descriptor_Norm` | type enumeration | Hamming<br>Hamming_2 | none | gap | `38f4246b8c08…` | — |
| `Feature_Set` | type private | — | 4 line(s) | yes | `c1e8394f0eb7…` | — |
| `Count` | function subprogram | Features : in Feature_Set<br>return Natural | none | gap | `d6e2bf5390c2…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Is_Empty` | function subprogram | Features : in Feature_Set<br>return Boolean | none | gap | `d72b56b53993…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Point` | function subprogram | Features : in Feature_Set<br>Index : in Positive<br>return Keypoint | none | gap | `07ba432d694e…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Keypoints` | function subprogram | Features : in Feature_Set<br>return Keypoint_Array | none | gap | `0a6468df1181…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Required_Norm` | function subprogram | Features : in Feature_Set<br>return Binary_Descriptor_Norm | none | gap | `905a58159996…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Descriptor_Row` | function subprogram | Features : in Feature_Set<br>Index : in Positive<br>return Natural | 2 line(s) | yes | `72a8798c1b7a…` | in Features: limited private type OpenCV.Features.Feature_Set |
| `Descriptor_Copy` | function subprogram | Features : in Feature_Set<br>return OpenCV.Core.Mat | 3 line(s) | yes | `0a0d51397b8b…` | in Features: limited private type OpenCV.Features.Feature_Set; result: Core-owned native matrix wrapper |
| `Native_Version` | function subprogram | return String | none | gap | `0e21b0e249b4…` | — |
| `Native_Backend` | function subprogram | return String | none | gap | `4728c6587561…` | — |

### `OpenCV.Features.Correspondences`

Source `src/opencv-features-correspondences.ads`; native page `0276ad652f884946c096f409451e99a54a424134b0183a333688d154e443c58b.html`. Package description: gap (source block is shared by the package description and a declaration).

| Declaration | Kind | Members | Existing comment | Description credit | Native anchor | Ownership-sensitive |
| --- | --- | --- | --- | --- | --- | --- |
| `Point_Correspondence` | type record | Query_Index : Positive<br>Train_Index : Positive<br>Query_Point : OpenCV.Float32_Point<br>Train_Point : OpenCV.Float32_Point<br>Distance : Matching.Binary_Descriptor_Distance | 1 line(s), shared with package description | gap | `93782fcd4935…` | — |
| `Point_Correspondence_Array` | type array | — | none | gap | `5de82a187d2c…` | — |
| `From_Matches` | function subprogram | Query : in Feature_Set<br>Train : in Feature_Set<br>Matches : in Matching.Descriptor_Match_Array<br>return Point_Correspondence_Array | 15 line(s) | yes | `03ccdc4f988b…` | in Query: limited private type OpenCV.Features.Feature_Set; in Train: limited private type OpenCV.Features.Feature_Set |

### `OpenCV.Features.Matching`

Source `src/opencv-features-matching.ads`; native page `f8c4f9ff8d48083e265efee6caac04d35ec5fd66029c3db2332e801220bed0dd.html`. Package description: gap (source block is shared by the package description and a declaration).

| Declaration | Kind | Members | Existing comment | Description credit | Native anchor | Ownership-sensitive |
| --- | --- | --- | --- | --- | --- | --- |
| `Matching_Mode` | type enumeration | Nearest<br>Mutual_Nearest | 1 line(s), shared with package description | gap | `6f12d3795802…` | — |
| `Binary_Descriptor_Distance` | type range | — | none | gap | `72d1532e7792…` | — |
| `Descriptor_Match` | type record | Query_Index : Positive<br>Train_Index : Positive<br>Distance : Binary_Descriptor_Distance | none | gap | `346ae6a7608b…` | — |
| `Descriptor_Match_Array` | type array | — | none | gap | `9b31f45c5c8f…` | — |
| `Brute_Force_Match` | function subprogram | Query : in Feature_Set<br>Train : in Feature_Set<br>Mode : in Matching_Mode := Nearest<br>return Descriptor_Match_Array | 13 line(s) | yes | `8713ca64d6b3…` | in Query: limited private type OpenCV.Features.Feature_Set; in Train: limited private type OpenCV.Features.Feature_Set |
| `Binary_Neighbor` | type record | Train_Index : Positive<br>Distance : Binary_Descriptor_Distance | none | gap | `4d1b33d4e4d9…` | — |
| `Brute_Force_Radius_Match` | function subprogram | Query : in Feature_Set<br>Train : in Feature_Set<br>Maximum_Distance : in Binary_Descriptor_Distance<br>return Descriptor_Match_Array | 17 line(s) | yes | `c362b300693c…` | in Query: limited private type OpenCV.Features.Feature_Set; in Train: limited private type OpenCV.Features.Feature_Set |
| `Two_Nearest_Match` | type record | Query_Index : Positive<br>Nearest : Binary_Neighbor<br>Second_Nearest : Binary_Neighbor | none | gap | `154f2fd90623…` | — |
| `Two_Nearest_Match_Array` | type array | — | none | gap | `028960085fab…` | — |
| `Brute_Force_KNN_2` | function subprogram | Query : in Feature_Set<br>Train : in Feature_Set<br>return Two_Nearest_Match_Array | 7 line(s) | yes | `8e0182c12a07…` | in Query: limited private type OpenCV.Features.Feature_Set; in Train: limited private type OpenCV.Features.Feature_Set |
| `Passes_Ratio_Test` | function subprogram | Candidate : in Two_Nearest_Match<br>Maximum_Ratio : in OpenCV.Float64_Value<br>return Boolean | 4 line(s) | yes | `3158e9d41767…` | — |
| `Filter_By_Ratio` | function subprogram | Candidates : in Two_Nearest_Match_Array<br>Maximum_Ratio : in OpenCV.Float64_Value<br>return Descriptor_Match_Array | 4 line(s) | yes | `982e840270c5…` | — |

### `OpenCV.Features.ORB`

Source `src/opencv-features-orb.ads`; native page `71007168ac326a7bdd4e866a08abe473df533f97af629fa8d55c6ab3677485c7.html`. Package description: gap (source block is shared by the package description and a declaration).

| Declaration | Kind | Members | Existing comment | Description credit | Native anchor | Ownership-sensitive |
| --- | --- | --- | --- | --- | --- | --- |
| `Tuple_Size` | type enumeration | Two_Samples<br>Three_Samples<br>Four_Samples | 1 line(s), shared with package description | gap | `231f8948b27b…` | — |
| `Score_Kind` | type enumeration | Harris_Score<br>FAST_Score | none | gap | `71f2a9ce16f2…` | — |
| `Configuration` | type record | Maximum_Features : Positive := 500<br>Tuple : Tuple_Size := Two_Samples<br>Score : Score_Kind := Harris_Score<br>FAST_Threshold : Natural := 20 | none | gap | `02e4cf0e0223…` | — |
| `Detector` | type private | — | 5 line(s) | yes | `f4314b0abccf…` | — |
| `Create` | function subprogram | Parameters : in Configuration := (others => <>)<br>return Detector | none | gap | `f62e99d5b086…` | result: limited private type OpenCV.Features.ORB.Detector |
| `Close` | procedure subprogram | Self : in out Detector | none | gap | `c38ce55b4e51…` | in out Self: limited private type OpenCV.Features.ORB.Detector |
| `Is_Ready` | function subprogram | Self : in Detector<br>return Boolean | none | gap | `0d7240e2d312…` | in Self: limited private type OpenCV.Features.ORB.Detector |
| `Parameters` | function subprogram | Self : in Detector<br>return Configuration | none | gap | `213f1936fac8…` | in Self: limited private type OpenCV.Features.ORB.Detector |
| `Detect_And_Compute` | function subprogram | Self : in Detector<br>Image : in OpenCV.Core.Mat<br>return Feature_Set | 10 line(s) | yes | `22f828a1a3f4…` | in Self: limited private type OpenCV.Features.ORB.Detector; in Image: Core-owned native matrix wrapper; result: limited private type OpenCV.Features.Feature_Set |
| `Detect_And_Compute` | function subprogram | Self : in Detector<br>Image : in OpenCV.Core.Mat<br>Mask : in OpenCV.Core.Mat<br>return Feature_Set | none | gap | `07eb80b590b7…` | in Self: limited private type OpenCV.Features.ORB.Detector; in Image: Core-owned native matrix wrapper; in Mask: Core-owned native matrix wrapper; result: limited private type OpenCV.Features.Feature_Set |

