# Build and platform notes

## Dependencies and source pins

Production Ada dependency: `opencv_core ~0.4.0`. The native/system crates
are `opencv` and `pkg_config`; the Windows selector adds `mingw_w64_gcc`.
The native OpenCV Alire external-package model uses `*`; configuration
performs the actual native semantic-version check.

Core is pinned to commit `7956981a7881ce9121115f8cb65909aeb9edc439` in all
three manifests. This is a development pin to the observed Core 0.4.0
source, not a claim that 0.4.0 is already published in the community index.
The pin is not transitive configuration: tests and examples are separate
roots, so their pins are explicit too.

To use an existing sibling checkout for local development, replace the Core
pin in each manifest with a path appropriate to that manifest. From the
Features root, a sibling Core is `../opencv_core_ada`; from `tests/` and
`examples/`, it is `../../opencv_core_ada`. Do not mix different Core
revisions or OpenCV installations in one process. Update the consistency
check intentionally when moving off the bootstrap SHA pin.

AUnit 26 is used only by the test crate. GNATprove/GNATcov are not introduced
merely to populate a template; add them in a separate justified test-only
slice when a concrete proof/coverage target exists. No SPARK proof is claimed.

## Generated configuration

Alire generates the `*_config.gpr` files. The pre-build script generates
`config/opencv_features_install.gpr`. Neither belongs in source control.
The script is normally invoked by `alr build`, which defines
`OPENCV_CORE_ALIRE_PREFIX` for the resolved dependency. A manual configure
must run inside the same Alire environment.

pkg-config search order is `opencv5`, `opencv4`, `opencv`. The legacy
`includedir_new` fallback and MacPorts metadata fallback are retained.
Configuration rejects unsupported versions instead of guessing a new module
mapping. It checks the selected `features2d.hpp`/`features.hpp` header exists.

The Core bridge include is discovered at `$OPENCV_CORE_ALIRE_PREFIX/include`
for an installed layout or `.../cpp` for a source dependency. The installed
header takes precedence. The header is never vendored. Installed-consumer
linkage still needs qualification; header discovery alone does not prove
that `gprinstall` relocates every generated path correctly.

## Linux

GPRbuild compiles C++17 with g++ and links libstdc++. The default library
kind is static-pic. The Features shim links its selected native module and
native Core; the GPR closure contains the Core shim providing Mat resolution.
Use one native OpenCV installation for all bindings. A custom installation
must be visible to pkg-config and to the runtime loader.

## macOS

The compiler and SDK are located with xcrun. C++ uses Apple clang++ and
libc++, not GNAT's bundled g++. The relocatable Features shim follows
Imgproc's existing GPR closure into Core. CI checks direct native Features,
Core shim, and libc++ linkage, and rejects libstdc++ linkage. macOS runtime
search paths and installed-consumer behavior remain native validation gates.

## Windows/MSYS2

The script prefers target-prefixed pkg-config and selects g++ from the
OpenCV installation's own prefix. It builds an independent DLL and import
library outside GPRbuild. It explicitly links the OpenCV Features/Core
import libraries and the Core shim import library. CPATH and related compiler
environment injection are removed for this C++ subprocess.

Build Ada with its selected GNAT compiler. Do not put MSYS2's compiler at
the front of the Ada build PATH. The test launcher changes runtime DLL lookup
only in the child that runs the test executable. `alr test` uses that launcher.
For examples, use the documented `alr exec -- sh ../scripts/run_native.sh ...`
form, not an unqualified executable launched from a random shell.

Windows CI is post-merge only: `windows-post-merge.yml` triggers exclusively
on pushes to `main`, with neither PR nor manual dispatch triggers. Corrected
code Windows qualification is deliberately deferred until it lands on main.
MSYS2 provider updates may require reviewed maintenance rather than weakening
compiler/runtime checks. Installation uses `pacman -Sy --noconfirm --needed`,
not an unnecessary full system upgrade.

## CI routing

PR CI (`cross-platform.yml`):
- repository checks;
- Linux production build, native AUnit suite, and synthetic example;
- macOS production build, native AUnit suite, and Apple-clang/libc++ linkage check.

The same cross-platform workflow runs on main pushes and manual dispatch.
Post-merge main CI (`windows-post-merge.yml`): **Windows only**. No Windows job
or runner matrix is present in the PR workflow, including a skipped job.
The repository checker validates trigger/job structure without a PyYAML
dependency; unsupported routing syntax fails closed and needs checker review.
Regression fixtures cover quoted keys, comments, flow/block formatting, forbidden
events, missing main routing, Windows runners/jobs/matrices, and dependency caches.

## Qualification targets

The PR workflow exercises runner-installed Linux/macOS OpenCV; the separate
post-merge workflow exercises MSYS2 Windows OpenCV.
The manual workflow source-builds 4.1.0, 4.10.0 and 5.0.0 on Linux with CPU
paths and explicit pkg-config/runtime prefixes. The distro development package
is also installed to satisfy Alire's external-package discovery; its native
library must not shadow the requested source build. The workflow verifies
the configured native version after the test run.

Before release, test `alr build`, `alr test`, examples, all target backends,
compiler/runtime dependencies, `gprinstall`/clean consumer linkage, and source
package contents. No release automation or automatically publishing workflow
is included.
