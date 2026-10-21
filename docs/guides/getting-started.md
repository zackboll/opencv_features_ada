# Getting started

`opencv_features` is a thick Ada binding to OpenCV ORB detection and description
and to brute-force binary descriptor matching. It builds on the
`opencv_core` Ada crate, which owns the `OpenCV.Core.Mat` type used for images
and descriptors, and on a native OpenCV installation. This guide takes you from
a clean machine to running the bundled examples.

## Prerequisites

- **Alire** (the Ada package manager). The repository's CI uses Alire 2.1.1.
- **An Ada 2022 compiler and GPRbuild** selected through Alire. CI uses
  `gnat_native=16.1.0` and `gprbuild=26.0.1`.
- **A C++17 compiler and pkg-config.** A small C++ shim is compiled against
  native OpenCV during the build: g++ on Linux, Apple clang++ on macOS, and the
  MSYS2 g++ that matches the OpenCV installation on Windows.
- **Native OpenCV development files**, version 4 (module `features2d`) or 5.0
  (module `features`), discoverable through pkg-config as `opencv5`, `opencv4`
  or `opencv`.

On Debian or Ubuntu:

```sh
sudo apt-get update
sudo apt-get install -y build-essential pkg-config libopencv-dev
```

On macOS with Homebrew, `brew install opencv pkg-config` provides the same
prerequisites. Windows uses MSYS2 packages; see the Platform compatibility
guide.

Select the toolchain once:

```sh
alr -n toolchain --select gnat_native=16.1.0 gprbuild=26.0.1
```

## Dependency resolution

The only Ada library dependency is `opencv_core ~0.5.0`, resolved from the
Alire community index; no Git pin or sibling checkout is needed. `opencv` and
`pkg_config` are native system dependencies, and Windows additionally
requests the MSYS2 C++ toolchain. To see the resolution in a checkout:

```sh
alr -n show --solve
```

The solution lists `opencv_core=0.5.0` together with the detected native
`opencv` and `pkg_config` packages. Configuration fails clearly when native
OpenCV is missing or is a major version that has not been reviewed.

## Build, test and run the examples

```sh
git clone https://github.com/zackboll/opencv_features_ada.git
cd opencv_features_ada
alr -n build
alr test
alr -n -C examples build
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_synthetic
alr -n -C examples exec -- sh ../scripts/run_native.sh bin/orb_match_synthetic
```

`alr -n build` configures native OpenCV, compiles the C++ shim and builds the
Ada library with warnings as errors. `alr test` builds and runs the native AUnit
suite (67 registered cases). The examples need no image files, camera, GUI or
other Ada bindings: they synthesize their own images. Always start examples
through `alr exec` and `scripts/run_native.sh`, which set up the native runtime
search path for the child process only.

## Using the library from your own crate

Until `opencv_features` is available from the Alire community index, depend on
a local checkout:

```sh
alr -n init --bin my_app
cd my_app
alr -n with opencv_features --use=/path/to/opencv_features_ada
```

`opencv_core` is still resolved from the index. When a release of
`opencv_features` is available in the index (check with
`alr show opencv_features`), the usual `alr with opencv_features` applies
instead. In Ada code, `with` the packages you use:

- [OpenCV.Features](api:OpenCV.Features) for keypoints, feature sets and norms;
- [OpenCV.Features.ORB](api:OpenCV.Features.ORB) for detection;
- [OpenCV.Features.Matching](api:OpenCV.Features.Matching) for descriptor matching;
- [OpenCV.Features.Correspondences](api:OpenCV.Features.Correspondences) for 2-D point pairs.

Installed GPR consumers that are not Alire workspaces use
`with "opencv_features";` after a recursive `gprinstall` of Core and Features;
the Platform compatibility guide describes the qualified procedure.

## Checks that need no native OpenCV

```sh
python3 scripts/check_repository.py
python3 -m unittest discover -s tests/configuration -v
sh scripts/run_profile_tests.sh
```

These validate manifests, the C ABI inventory and helper code. They do not
exercise native ORB or matching; only `alr test` and the examples do.

## Building this documentation

The API reference is generated with GNATdoc 26.0.0 from the public
specifications, and these guides are rendered by the shared GNATdoc enhancer.
The exact commands and checks are recorded in `docs/gnatdoc-foundation.md` and
`docs/gnatdoc-enhancer-integration.md`; the documentation workflow uploads the
generated site as a review artifact.

Next: the ORB feature extraction guide.
