# Installed and clean-consumer qualification (Task 007)

Version remains **0.1.0-dev**. This is packaging/integration qualification,
not a release, index submission, algorithm extension or compatibility promise.

## Three separate claims

1. **Source-pinned external consumer:** a fresh `alr init --bin` application
   adds `opencv_features --use=<candidate>`. Features' bootstrap Core pin
   resolves normally; no sibling Core checkout is selected manually.
2. **Installed-prefix consumer:** Core and Features are recursively installed
   with real projects and `gprinstall -f -p -r --prefix=... -P ...`.
   A separate non-Alire GPR application builds/runs against installed projects
   only, with no Features manifest or source pin.
3. **Relocated installed-prefix consumer:** move installation A to a longer
   absolute prefix B, verify A is absent (no symlink), then compile/link/run a
   new application with no reused consumer objects.

**Alire public-index consumption is not tested.** Bare `alr with opencv_features`
is not documented as resolving from the index. Core 0.4.0 remains pinned to
`7956981a7881ce9121115f8cb65909aeb9edc439`.

## Reproduce

From a Git candidate checkout with Alire 2.1.1, GNAT Ada 2022/GPRbuild,
Python 3, system OpenCV development libraries and pkg-config available:

```sh
sh scripts/validate_clean_consumer.sh
```

This exact command was executed locally. Run directly, not inside `alr exec`.
It prints its unique temporary evidence directory and keeps logs on failure:
source build/run, dependency environment/Core SHA, installation/inventory,
both fresh build/project-resolution traces, linkage, runs and textual audit.

It copies version-controlled/nonignored candidate files (including uncommitted
changes), excluding tests/examples and ignored build/cache artifacts. It clears
inherited project/header/library/compiler lookup. After installing, it renames
snapshot and source-consumer directories, making original lookup locations
unavailable. They remain under evidence names, not project/runtime lookup.
Installed consumers use only `<prefix>/share/gpr` for project lookup.
Toolchain PATH and normal system OpenCV/pkg-config remain intentional.

The public-only fixture uses the qualified deterministic 256x256 texture and
(8,5) translation. It exercises Core Mat/UInt8 access, ORB creation/extraction,
counts/native metadata, Nearest/Mutual, KNN2/ratio, radius and correspondence
conversion. Checks cover indices, exact copied Float32 positions/distances and
lengths, not portable exact feature counts or nonempty ratio acceptance.
Marker: `opencv_features clean consumer ok`.

## Baseline research and contract

Starting main: `7bac60fcc776918615985fa2cc89e5b8bfe426c7`.
Linux/OpenCV 4.10.0 baseline installation and fresh relocated build/run passed
before production/package changes. No Linux packaging defect was manufactured;
no production/package correction was needed for that result.

Generated configuration contained system Include_Switch/Library_Search_Switch,
Features/Core linker switches, Cxx_Driver=g++, empty Cxx_Sysroot and
Core_Shim_Link_Option, and absolute Core_Bridge_Include_Switch. These are valid
build inputs. GPRinstall drops config imports, emits externally built projects,
uses relative installed Source_Dirs/Library_Dir and freezes native system link
options. The bridge path survives only in unused Common_Cxx_Switches: its
Compiler package and all uses are absent. The audit reports that provenance
rather than declaring every absolute string a defect. Fresh compilation with
original lookup locations unavailable is the operational authority. Binary
debug paths/manifest hashes are not project/library lookup evidence.

Default Linux inventory, relative to prefix:

| Artifact | Installed path |
|---|---|
| Features/Core projects | `share/gpr/opencv_features.gpr`, `share/gpr/opencv_core.gpr` |
| Features Ada library/ALI | `lib/opencv_features/libopencv_features_ada.a`, `lib/opencv_features/*.ali` |
| Features shim | `lib/opencv_features_shim/libopencv_features_shim.a` |
| Core Ada library/ALI | `lib/opencv_core/libopencv_core_ada.a`, `lib/opencv_core/*.ali` |
| Core shim | `lib/opencv_core_shim/libopencv_core_shim.a` |
| Public Features specs | `include/opencv_features/opencv-features*.ads` |
| Correspondences spec | `include/opencv_features/opencv-features-correspondences.ads` |
| Core bridge export | `include/opencv_core_module_bridge.hpp` |

Recursive development installation includes implementation units/native shim
sources as GPRinstall requires, not test children. Public consumers do not
access private units. macOS uses dylibs; Windows DLLs/import libraries.
Actual inventories are recorded, not assumed to match Linux artifact types.

The installed application contains `with "opencv_features";` and executes
`gprbuild -p -v -vP2 -P consumer.gpr` with prefix-only project lookup. This is
not an ad-hoc copied-spec installation. After A moves to B the same command
runs in a new workspace with no objects.

## Runtime/platform scope

Linux inspects executables with ldd/readelf. Static archives are proven by the
link command, not expected in ldd. Runtime lookup includes installed directories
plus system loader paths. macOS uses otool -L on executables/installed dylibs,
requires libc++ and rejects libstdc++; DYLD_LIBRARY_PATH is prefix-only.
The macOS installed Ada main explicitly links with GNAT gcc, not GNAT g++:
already-built Apple shim dylibs own libc++ linkage. GPR's default C++ driver
would add an unused libstdc++ dependency to the main; the strict check caught it.
Windows uses external MSYS2 MinGW64 and objdump PE inspection. Installed lib/bin
and matching MSYS2 runtime are prepended only when executing, not compiling Ada.

Linux/macOS ordinary PR jobs execute all three modes. Windows Task 007 remains
**post-merge only**, after native/linkage checks; it cannot be claimed executed
before merge. No Windows PR CI or merge to obtain evidence is authorized.
The manual 4.1/4.10/5.0 matrix is not dispatched: these changes concern consumer
qualification, not version-dependent native algorithm/link changes.

Release/index submission, pin removal, version/tag/release changes, release
tarballs and semantic-version policy remain deferred. This does not establish
arbitrary cross-platform or future OpenCV safety.