# OpenCV Features for Ada

Handwritten, thick Ada binding to feature detection and description, using
`OpenCV.Core.Mat` from `opencv_core`. Repository: `opencv_features_ada`;
Alire crate: `opencv_features`; public packages: `OpenCV.Features` and
`OpenCV.Features.ORB`.

**Version: 0.1.0-dev. This is a bootstrap, not a qualified release.**
Initial ORB implementation, 20 registered AUnit cases, build scripts, and CI
workflows are included. Ada/native OpenCV compilation and the AUnit suite
have **not** been executed in the artifact-creation environment. See
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
Do not start BF matching until the initial native build/test gate is real.

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
WTA_K 2 records `Hamming`; WTA_K 3/4 record `Hamming_2` for the future matcher.
Blank/masked-out images return an empty result, not an error. A default
`Feature_Set` is also empty. No arbitrary fixed feature count is assumed.

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
contains 20 cases covering extraction, masks, descriptors, ownership,
noncontiguous Regions, configuration, and invalid inputs. Use `alr test`
for the native suite; the script propagates failures.

Cross-platform CI is configured for Linux and macOS on PRs and main.
Windows/MSYS2 runs only on main pushes or manual dispatch. A separate manual
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

Next: BF Hamming/Hamming_2 matching, then KNN result handling and explicit
application filtering. No matcher, homography, PnP, DTED reader, camera
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
