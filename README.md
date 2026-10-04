# OpenCV Features for Ada

Handwritten, thick Ada binding to feature detection, description and binary matching, using
`OpenCV.Core.Mat` from `opencv_core`. Repository: `opencv_features_ada`;
Alire crate: `opencv_features`; public packages: `OpenCV.Features` and
`OpenCV.Features.ORB` and `OpenCV.Features.Matching`.

**Version: 0.1.0-dev. This is a bootstrap, not a qualified release.**
ORB, binary BF one-best/KNN2/radius matching and pure-Ada ratio filtering, 53 registered
AUnit cases, build scripts, and CI workflows are included. Local qualification passes all 53
native AUnit cases locally on Linux/OpenCV 4.10.0. Broader qualification is
still outstanding. See
[the validation record](docs/bootstrap-validation.md) before treating the
binding as operational. No CI badges imply success.

## Start here

With Alire, an Ada 2022 toolchain, a C++17 compiler, pkg-config, and native
OpenCV development packages available:

```sh
unzip opencv_features_ada_bootstrap.zip
cd opencv_features_ada
alr -n build
alr test
alr -n -C examples build
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_match_synthetic
```

On Debian/Ubuntu, native prerequisites can be installed with:

```sh
sudo apt-get update
sudo apt-get install -y build-essential pkg-config libopencv-dev
```

The bootstrap pins Core 0.4.0 to commit
`7956981a7881ce9121115f8cb65909aeb9edc439`. Alire fetches it; no sibling
checkout is required and Core is not bundled. The same source pin appears
in the production, tests, and examples manifests because they are separate
Alire roots. Review/remove the development pin when preparing an Alire
index release. [Dependency and platform notes](docs/build-and-platforms.md).

The first agent task is [Task 001: validate the bootstrap](docs/tasks/001-validate-bootstrap.md).
Its installed/clean-consumer qualification remains outstanding; the native
ORB build/test baseline has been established in Task 002.

## Included API

```ada
with OpenCV.Features.ORB;

-- Image is an existing nonempty UInt8 C1 OpenCV.Core.Mat.
declare
   Detector : OpenCV.Features.ORB.Detector :=
     OpenCV.Features.ORB.Create;
   Result : OpenCV.Features.Feature_Set :=
     OpenCV.Features.ORB.Detect_And_Compute (Detector, Image);
begin
   for I in 1 .. OpenCV.Features.Count (Result) loop
      declare
         P : constant OpenCV.Features.Keypoint :=
           OpenCV.Features.Point (Result, I);
         Row : constant Natural :=
           OpenCV.Features.Descriptor_Row (Result, I);
      begin
         -- P is an Ada value; Row selects the matching native descriptor.
         null;
      end;
   end loop;
end;
```

The complete standalone program is `examples/src/orb_synthetic.adb`.
It uses only Core and Features: no image files, GUI, camera, or Imgproc
binding is needed to exercise extraction.

The initial detector supports a requested feature target, HARRIS/FAST
scoring, WTA_K 2/3/4, and a FAST threshold. Its structural profile is fixed
at scale factor 1.2, eight pyramid levels, edge threshold 31, first level 0,
and patch size 31. These are deliberately not exposed as unchecked tuning
knobs yet. See [the ORB contract](docs/orb-contract.md).

A `Feature_Set` is limited and private. Keypoints are owned Ada values in a
private heap-backed vector; descriptors live in a Core-owned Mat. Keypoint
index 1 maps to descriptor row 0. `Descriptor_Copy` explicitly returns a
deep copy, so caller edits cannot corrupt the stored correspondence.
WTA_K 2 records `Hamming`; WTA_K 3/4 record `Hamming_2` for matching.
Blank/masked-out images return an empty result, not an error. A default
`Feature_Set` is also empty. No arbitrary fixed feature count is assumed.

### Binary one-best matching

```ada
with OpenCV.Features.Matching;

-- Query and Train are ORB Feature_Sets; no Descriptor_Copy is needed.
declare
   Matches : constant OpenCV.Features.Matching.Descriptor_Match_Array :=
     OpenCV.Features.Matching.Brute_Force_Match
       (Query, Train, OpenCV.Features.Matching.Mutual_Nearest);
begin
   for Item of Matches loop
      -- Item.Query_Index / Train_Index are one-based keypoint indices.
      -- Item.Distance is an exact integer, not probability/confidence.
      null;
   end loop;
end;
```

`Nearest` (default) returns one match per query when both sets are nonempty;
train indices may repeat. `Mutual_Nearest` retains native cross-check pairs,
with unique query and train indices; it is **not a ratio test**. Results are
ordinary Ada values in ascending Query_Index order, independent of input and
detector lifetime. Equal minimum-distance ties do not promise an exact train index.

Norm selection is automatic: Hamming for WTA2 (**0..256** differing bits),
Hamming2 for WTA3/4 (**0..128** differing 2-bit cells). Different required norms
raise `OpenCV_Error`, even with empty inputs. Compatible empty inputs succeed
with bounds **1..0**. For one-best/KNN2, Train.Count must be **<=262143**, because
native CPU knnMatchImpl packs train indices in 18 bits; no corresponding query cap is imposed.
Descriptors are borrowed immutably through Core's scoped bridge, not deep-copied.
See [the immutable source review](docs/bfmatcher-source-review.md).

### Two-nearest matching and explicit ratio filtering

```ada
declare
   Pairs : constant OpenCV.Features.Matching.Two_Nearest_Match_Array :=
     OpenCV.Features.Matching.Brute_Force_KNN_2 (Query, Train);
   Accepted : constant OpenCV.Features.Matching.Descriptor_Match_Array :=
     OpenCV.Features.Matching.Filter_By_Ratio (Pairs, 0.80);
begin
   null;
end;
```

K is fixed at **2**, with no masks or cross-check. `Mutual_Nearest` remains a
separate K=1 alternative: native cross-check requires K=1, not K=2. Norm selection,
one-based indices, exact integer distance ranges, train bound and owned-value
lifetime are as above. Each nonempty query has exactly one pair when Train has
at least two rows; the train indices are distinct and nearest distance **<=**
second-nearest distance. Ties are permitted, with no guaranteed tied index order.
Compatible empty Query/Train returns **1..0** without entering BFMatcher.
Nonempty Query with one Train row raises `OpenCV_Error`. Norm mismatch is checked
before empties. There is no corresponding 18-bit Query limit.

`Passes_Ratio_Test` and `Filter_By_Ratio` are **pure Ada** mechanics. The application
must supply a threshold; there is **no default**. `OpenCV_Error` is raised unless
**0 < r < 1**, including NaN/nonfinite values and on empty filter input. Acceptance
is strictly `nearest.distance < r * second.distance`; equality rejects. In
particular **0/0 duplicates reject**. The filter returns nearest `Descriptor_Match`
values only and preserves candidate order; empty/all-rejected results have bounds
1..0. Ratio is not probability or confidence.

The translated synthetic example retains nearest/mutual output and adds KNN2,
an explicit **0.80 example policy**, and accepted distance extrema. This is not a
library default or a recommended navigation constant. It demonstrates descriptor
correspondence only, with no geometric verification, registration or localization.

### Absolute binary distance radius matching

```ada
Radius_Matches := OpenCV.Features.Matching.Brute_Force_Radius_Match
  (Query, Train, Maximum_Distance => 32);
```

The application supplies an **absolute distance**, with no library default.
The value 32 above is example application policy, not a recommended navigation
threshold. This is OpenCV's CPU `BFMatcher::radiusMatch`, **not** Lowe ratio
filtering, KNN2 truncation, or cross-check. Automatic norm selection remains
Hamming for WTA2 and Hamming2 for WTA3/4; incompatible norms raise `OpenCV_Error`,
including empty inputs. Thresholds must be **1..256 for Hamming**, **1..128 for
Hamming2**, even for empty inputs. Zero and Hamming2 thresholds above 128 raise
`OpenCV_Error`; exact-zero radius matching is deferred, not silently remapped.

The boundary is **inclusive: distance <= Maximum_Distance** in all three pinned
sources. Results are flat Ada-owned `Descriptor_Match_Array` values, ascending
by one-based Query_Index and nondecreasing Distance within each query. Equal
distances have unspecified train ordering. Each train row appears at most once
per query, but may match different queries. A query may contribute zero, one,
or many results; the total need not equal Query.Count. Compatible empty Query,
empty Train, or both return **1..0**. A one-row Train is valid.

Unlike one-best/KNN2, radius uses direct train indices, **not the 18-bit packed
representation**: no 262143-row radius cap is imposed. Native dimensions and
indices are signed 32-bit; flattened count must fit int32/Ada representation
and allocation sizes. Native full distance matrices and potentially large
results may fail allocation. The shim checks arithmetic and actual result
counts, and never reserves the theoretical Cartesian product for flat staging.
Inputs are unchanged; results survive inputs, detectors and native staging.
No masks, persistent matcher, UMat/GPU, arbitrary descriptor types, probability,
confidence or geometric verification are exposed. See
[immutable radius source review](docs/radius-matcher-source-review.md).

Images and masks are independently snapshotted for ORB. A noncontiguous
Region is processed as an isolated image, and coordinates are Region-local.
Use 0/255 binary masks for the portable baseline; OpenCV 4.10 and 5.0
handle other nonzero mask values differently during pyramid construction.
The binding preserves the installed algorithm rather than normalizing masks.
Sources remain unchanged. Results remain valid after the detector is
closed or the source storage is modified. Do not mutate source storage or
share/close the same detector concurrently with extraction.

## Architecture

```text
Ada application
    OpenCV.Features / OpenCV.Features.ORB
        private Ada C interop
            fixed-width C ABI + opaque detector/temporary-result handles
                C++17 shim
                    OpenCV 4: features2d
                    OpenCV 5.0: features

Image/descriptor ownership and callback-scoped Mat access: opencv_core
```

Core remains the sole owner of application Mat wrappers. This crate never
copies Core's bridge header or exposes native pointers in the public API.
The C++ result handle is an internal, scoped staging object, not an
application object. It is destroyed on successful conversion and on every
Ada exception path. Public outputs contain no STL containers or C++ handles.

Only `opencv_core` is a production **Ada** dependency. `opencv` and
`pkg_config` are native/system dependencies; Windows additionally requests
its native C++ toolchain. No Ada Imgproc or Geometry dependency is added.
Native OpenCV may have its own transitive module dependencies.

This follows Core's ownership/bridge architecture, Imgproc's Mat integration
and compiler isolation, and Geometry's Ada-owned outputs and version-neutral
public package policy. Geometry's special prohibition on a Mat bridge is
not copied here: Features actually needs image/descriptor Mats.
[Architecture decisions and source provenance](docs/architecture.md).

## Validation and CI

Commands that do not need Ada or native OpenCV:

```sh
python3 scripts/check_repository.py       # Python 3.11+
python3 -m unittest discover -s tests/configuration -v
sh scripts/run_profile_tests.sh
```

These checks do not prove native ORB correctness. The configured AUnit suite
contains 53 cases covering extraction, masks, descriptors, ownership, matching, ratio, radius,
noncontiguous Regions, configuration, and invalid inputs. Use `alr test`
for the native suite; the script propagates failures. Linux also runs the
real-Core-handle raw-boundary driver. `alr -n exec -- sh scripts/run_sanitizers.sh`
instruments the actual Features shim for CPU-only ASan/UBSan qualification.
See `docs/orb-source-review.md` for pinned upstream source-derived bounds.

Cross-platform CI is configured for Linux and macOS on PRs and main.
Windows/MSYS2 runs only on main pushes in a separate post-merge workflow,
never on PRs or manual dispatch. A separate manual
workflow builds native OpenCV 4.1.0, 4.10.0, and 5.0.0. These are intended
qualification targets, not successful runs claimed by this bootstrap.
The setup-alire action currently follows its `latest` ref, matching the
reference setup; pin action commits as part of CI hardening.

## Navigation direction and exclusions

This crate provides correspondences' front-end building blocks. It does not
provide a position fix. The planned first pipeline is camera features plus
georeferenced reference imagery, followed by geometric verification and
terrain-aware pose estimation using a separate elevation/geospatial layer.
DTED is terrain data, not camera texture; direct visible/IR-to-elevation
matching is not promised. Test the actual camera/reference modalities early.

KNN2, explicit strict ratio filtering and absolute radius matching are included;
broader matching is deferred.
No homography, PnP, DTED reader, camera
calibration, image loading, optical flow, GPU path, or navigation estimator
is implemented here. [Roadmap](docs/roadmap.md).

## Repository initialization

The ZIP contains files only: no `.git`, remote, credentials, artifacts from
the other repositories, or compiled binaries. After reviewing the bootstrap:

```sh
git init -b main
git add .
git commit -m "Bootstrap thick OpenCV Features binding for Ada"
```

Create/configure a remote separately. Nothing in the bootstrap automatically
creates repositories, commits, pushes, opens PRs, merges, tags, or publishes.

## License

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
