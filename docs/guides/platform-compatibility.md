# Platform compatibility

The public Ada packages are the same on every platform and OpenCV version.
Version and platform handling lives below the public API, in the build
configuration and a small C++17 shim.

## Native OpenCV versions

| Native OpenCV | Module used | `Native_Backend` |
| --- | --- | --- |
| 4.x | `features2d` | `"features2d"` |
| 5.0 | `features` | `"features"` |

Configuration looks for pkg-config packages in the order `opencv5`, `opencv4`,
`opencv`, checks that the matching module header exists, and rejects other major
versions instead of guessing a module mapping.
[Native_Version](api:OpenCV.Features.Native_Version) and
[Native_Backend](api:OpenCV.Features.Native_Backend) report what the shim was
compiled against.

The fixed ORB profile and the matchers were reviewed against the OpenCV 4.1.0,
4.10.0 and 5.0.0 sources (`docs/orb-source-review.md`,
`docs/bfmatcher-source-review.md`, `docs/radius-matcher-source-review.md`).
One documented behavioral difference is visible through the API: nonbinary
detection-mask values. OpenCV 4.x keeps them at pyramid level 0 but only 255
survives into later levels, while OpenCV 5.0 first maps every nonzero value to
255, so use 0/255 masks for portable results. A manual workflow
(`opencv-compatibility.yml`) builds those three OpenCV versions from source on
Linux; it is a qualification target, not a result implied for every commit.
Other OpenCV releases are not reviewed.

## Compilers and runtimes

- Ada: Ada 2022, built through Alire with warnings as errors. CI uses GNAT
  16.1.0 (`gnat_native`) and GPRbuild 26.0.1.
- C++: C++17 for the shim, with a small fixed-width C ABI between Ada and C++.
  No C++ exceptions, STL types or OpenCV objects cross that boundary.
- Linux: g++ and libstdc++; the shim is built static-PIC by default.
- macOS: Apple clang++ and libc++ located with `xcrun` (not GNAT's bundled
  g++); the shim is a relocatable library and CI rejects libstdc++ linkage.
- Windows: MSYS2/MinGW. The shim is an external DLL with an import library,
  built by the g++ from the same MSYS2 prefix as OpenCV.

Use one native OpenCV installation for Core, Features and any other OpenCV Ada
bindings in an application.

## Windows MSYS2 runtime handling

On Windows the Ada build keeps its own GNAT compiler; MSYS2's compiler is never
put in front of the Ada build `PATH`. The OpenCV and shim DLL directories are
added to the runtime search path only for the child process that runs a test
or program. Run examples through
`alr exec -- sh ../scripts/run_native.sh <program>` rather than starting the
executable from an arbitrary shell; `alr test` uses the same launcher. Windows
CI runs after merges to `main` only (`windows-post-merge.yml`), never on pull
requests. For example, run 39047716214 on main commit `c2b6c6e` built and ran
the native suite, inspected the external shim DLL, and qualified source,
installed and relocated consumers. A later change is covered only by its own
post-merge run.

## Installed GPR consumers

Besides Alire workspaces, Core and Features can be installed with
`gprinstall` and consumed by a plain GPR project using `with "opencv_features";`.
`scripts/validate_clean_consumer.sh` qualifies this end to end: it builds a
fresh Alire application against a path-pinned Features checkout and the indexed
Core release, recursively installs both into an isolated prefix, builds and
runs installed consumers, then moves the prefix and repeats, so lookup cannot
depend on the source tree or the original prefix. See
`docs/installed-consumer-validation.md` for the contract.

## Continuous integration

| Workflow | Runs on | Covers |
| --- | --- | --- |
| `cross-platform.yml` | pull requests, `main`, manual | repository checks; Linux and macOS build, AUnit and consumer qualification; Linux examples and ASan/UBSan boundary driver; macOS libc++ linkage check |
| `windows-post-merge.yml` | pushes to `main` only | MSYS2 build, AUnit, DLL inspection and consumer qualification |
| `opencv-compatibility.yml` | manual | source-built OpenCV 4.1.0, 4.10.0 and 5.0.0 on Linux |
| `documentation.yml` | pull requests, `main`, manual | GNATdoc API reference, documentation checks, enhanced site and these guides; no publication |

Next: the Limitations and roadmap guide.
