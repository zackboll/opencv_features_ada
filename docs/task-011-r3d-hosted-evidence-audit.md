# Task 011-R3D — hosted numerical and native-correspondence audit

## Disposition

**SAFETY_GATE_NOT_ESTABLISHED.**

| Platform | Numerical evidence | Native correspondence |
| --- | --- | --- |
| macOS arm64, hosted runner | `NUMERICAL_EVIDENCE_ESTABLISHED` | `NATIVE_CORRESPONDENCE_PENDING` |
| Windows x86-64, hosted MSYS2 | `NUMERICAL_EVIDENCE_ESTABLISHED` | `NATIVE_CORRESPONDENCE_PENDING` |

No required power, conversion, or integer-bound check failed, so neither
platform is `NUMERICAL_VIOLATION`. A successful Actions conclusion is not
treated as native correspondence. Production Task 011 must not implement
configurable ORB levels from this review.

The R1/R2 all-target argument remains conditionally supported for a probe
environment that meets its stated premises. It is not yet supported as a
statement about the ORB code actually loaded from the installed libraries.
The smallest remaining gap is attribution of the installed ORB translation
unit: its exact source bytes, the flags used to compile that unit, and the
math/rounding implementation reached by that unit.

## Baseline identities

Fetched `origin/main` is
`495e385f91022735d5c52ba766f8d25164c7a900`.
## Artifact integrity

Raw archives and the extracted trees are outside the repository:

| Platform | Artifact | Local archive | Bytes | SHA-256 |
| --- | ---: | --- | ---: | --- |
| macOS | `11781299622` | `/home/zboll/evidence/opencv-features-011-r3d/macos-11781299622.zip` | 1,928,456 | `22542f833b5281e86546ce4633646a53e7a9ba4393bd276f62f2d5a1f4db96ff` |
| Windows | `11782845831` | `/home/zboll/evidence/opencv-features-011-r3d/windows-11782845831.zip` | 10,719,736 | `ba40bd20c41915e400b5272b5f6ffd4a15f875b09ac2046a9e383997e552f9bf` |

Both SHA-256 values equal the GitHub artifact `digest` fields. Both
archives belong to run `38330152641`, commit `0c0db1f2...ba1a`, and were
unexpired on retrieval. `unzip -t` and Python `ZipFile.testzip()` reported
no CRC error. Extraction recomputed each member CRC before writing bytes.
Windows separators were normalized only in destination paths; file bytes
were not rewritten.

| Platform | Manifest entries | Missing | SHA-256 mismatches | Undeclared files | Manifest SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| macOS | 315 | 0 | 0 | 0 | `9444e6e4e21a1b9e069d084040d3211b7f391ddad49411cbef3ad5fd2fc11902` |
| Windows | 237 | 0 | 0 | 0 | `c827e615647126a59e8d0be3da14f76c2f8152cc4f134eb712fd662296da9d9e` |

Both manifests record `tested_sha`
`0c0db1f2fdc55b459f0a4db6ab451b2deccfba1a`, `run_id` `38330152641`,
`probe_exit_status` 0, `first_failure` null, and optimization modes
`0`, `2`, and `3` as `EXECUTED`. Their own disposition remains
`PLATFORM_EVIDENCE_PENDING`.

Required O0/O2/O3 compilations, launches, R2 independent checks, and R1
certificate checks all exited 0 on both platforms. The only non-zero
statuses are the intended optional negative controls:
macOS `preflight/apple-warning-before` exit 1, and Windows
`preflight/include-environment-before` exit 1. No step was skipped after a
required failure.

## Observed platform identities

These are the installed hosted packages, not the separately reviewed Linux
4.1.0, 4.10.0, and 5.0.0 source trees.

| Item | macOS | Windows |
| --- | --- | --- |
| Probe compiler | Apple clang++ `Apple LLVM 16.0.0 (clang-1600.0.26.4)` | MSYS2 MinGW64 `g++.exe (Rev5, Built by MSYS2 project) 16.2.0` |
| Compiler path | Xcode 16.1 default toolchain | `...\alire\cache\msys64\mingw64\bin\g++.exe` |
| SDK / target | `MacOSX15.1.sdk`, arm64 | `x86_64-w64-mingw32` |
| C++ runtime | libc++ `_LIBCPP_VERSION 180100`; probe links `libc++.1.dylib` current `1800.101.0` | libstdc++ macro `20260807`; loaded `libstdc++-6.dll` and `libgcc_s_seh-1.dll` |
| Math runtime visible to probe | `libSystem.B.dylib` current `1351.0.0` | probe imports `msvcrt.dll`; process also loads `ucrtbase.dll` |
| OpenCV package | Homebrew `opencv` 5.0.0, Cellar `5.0.0_5` | `mingw-w64-x86_64-opencv 5.0.0-5`, plus GCC `16.2.0-5` and CRT `14.0.0.r426.g4564ee4b5-1` |
| OpenCV compiler recorded by the library | `clang++ (ver 16.0.0.16000026)` | `D:/M/msys64/mingw64/bin/g++.exe (ver 16.2.0)` |
| Native version-control string | `unknown` | `eb52293-dirty` |
| Native CPU baseline | `NEON FP16 NEON_DOTPROD NEON_FP16`; host `Darwin 23.6.0 arm64` | package C++ flags include `-march=nocona -msahf -mtune=generic -O2` |
| Native optimization | Release `-O3 -DNDEBUG`; no fast-math flag in the recorded C++ flags | Release; recorded flags include `-O2` and `-D_FORTIFY_SOURCE=2`; no fast-math flag in that line |
| OpenCL | configured `YES`, linked `-framework OpenCL` | configured `YES (NVD3D11)`, dynamic load |
| Custom HAL | not named as custom | `Custom HAL: NO` |
| Algorithm hint | `ALGO_HINT_ACCURATE` | not separately quoted by this audit |

The macOS bottle formula currently on Homebrew master is revision 11 and is
not evidence for bottle `5.0.0_5`. The current MSYS2 PKGBUILD is
`pkgver=5.0.0`, `pkgrel=7`, while the runner installed `pkgrel` 5. Current
recipes therefore cannot be substituted for the installed binaries.

Research HEAD under audit is
`0c0db1f2fdc55b459f0a4db6ab451b2deccfba1a`
on `research/011-r3-hosted-numerics`.

GitHub Actions run `38330152641`, attempt `1`, conclusion `success`:
<https://github.com/zackboll/opencv_features_ada/actions/runs/38330152641>.
Event `workflow_dispatch`, branch `research/011-r3-hosted-numerics`, head
SHA equal to the research HEAD above. Six jobs completed successfully:
## Numerical evidence

### Contract observed in the probes

For every macOS and Windows O0/O2/O3 run, `orb_r2_numerics` reported:

- `FLT_RADIX == 2`, `FLT_MANT_DIG == 24`, `DBL_MANT_DIG == 53`;
- `sizeof(int) == 4` and `sizeof(size_t) == 8`;
- `numeric_limits<float>::is_iec559`;
- `FLT_EVAL_METHOD == 0` at execution;
- `fesetround(FE_TONEAREST) == 0` and `fegetround() == FE_TONEAREST`;
- no `__FAST_MATH__` definition, and the probe aborts if that macro exists;
- stored scale exactly `0x1.333334p+0` (`5033165/4194304`);
- stored reciprocal exactly `0x1.aaaaaap-1` (`13981013/16777216`).

Windows preprocessor output additionally defines `__FLT_EVAL_METHOD__ 0`,
`__SSE2__`, and `CV_SSE2 1`. macOS defines `__aarch64__` and `__ARM_NEON`,
and `CV_SSE2 0`. The macOS `-dM` line leaves `FLT_EVAL_METHOD` as the
implementation macro, but the executed probe prints the value 0. No
fast-math or contraction-changing flag appears in the probe compilation
commands. `FP_FAST_FMA*` availability macros on macOS are not fast-math
flags and are not used as a reassociation finding.

`selected-fast-math.txt` is byte-identical on both platforms, 15,016 bytes,
SHA-256 `cb39ce1134293ced080295dcac642bd863ef3b2421f38d8019e0b345524c1bde`.
That is the reviewed OpenCV 5.0.0 `fast_math.hpp` hash. It does not prove
that the installed ORB object included this header without a later
`CV_INLINE_ROUND_FLT` override. The float `cvRound` overload still selects,
in source order, an inline override, ARM64 MSVC, SSE2 `cvtss2si`, x87, a
builtin, or `lrintf`.

### Fixed powers against exact rationals

The oracle is `Fraction`, not the observed floating value and not the
probe's long-double product. The absolute allowance remains `2^-20`.
All 16 factor/scale inputs passed on every optimization mode. O0, O2, and
O3 produced identical `POWER`, `ROUND`, and `CONVERT` lines within each
platform (55 numeric lines).

macOS and Windows outputs are identical except one input. For factor level
7, macOS returned `0x1.1dc7912ef251bp-2` and Windows returned
`0x1.1dc7912ef251cp-2`. Those doubles differ by one binary64 spacing,
`2^-54`. Both absolute errors are far below `2^-20`; the macOS result is
the closer one. This is a real libm difference, not a manifest or parsing
discrepancy, and it is not a tolerance relaxation.

Largest absolute errors, same on both platforms except that level-7 factor
row:

| Input | Worst level | Magnitude |
| --- | ---: | --- |
| Factor `f^L`, L=1..8 | 3 | about `5.346e-17` |
| Scale `s^L`, L=0..7 | 4 | about `1.059e-16` |

Levels 0–2 for the scale and levels 1–2 for the factor were exact on both
platforms. No result was discarded.

### Rounding and conversion samples

Each R2 log contains 29 nonnegative `cvRound` samples and 8 integer
conversions. Sample checks confirm `|R(x)-x| <= 1`, `R(0)=0`, and
nondecreasing behavior across the logged neighborhood. Conversions at
1, 2, 3, 4096, the binary32 boundary `16777215/16777216/16777217`, and
`N = 1_073_741_823` stay within one binary32 spacing. These samples do not
themselves prove `cvRound` for every real input. On Windows the probe path
is the SSE2 overload because `CV_SSE2` is 1. On macOS the header's generic
fallback is `lrintf` unless an inline ARM override was defined while
compiling; the probe does not print that override state. Probe disassembly
shows `frintx`/`fcvtzs` on macOS and `cvtss2si` on Windows for the probe,
which is nearest-style rounding for the sampled path only.

### All-target integer argument

The sampled 151,547 targets times 8 levels are probe checks. They are not a
substitute for the rational argument. Replaying the unchanged R1 checker
logic and the independent R2 majorants on the hosted logs gives, for every
mode:

- uniform sum at `Nmax` no greater than `1_986_422_379`;
- uniform Harris reserve no greater than `1_986_422_380` by the R2 floor,
## Native correspondence

### What is established

1. **Matching source-level shape for reviewed 5.0.0, not for the installed
   binary.** The immutable 5.0.0 file
   `40738fb16ceddb5fb3fea747585f7ce6abb0605b:modules/features/src/orb.cpp`,
   SHA-256 `ac48243150ab9f011f3f122632df10f094597fe728aefcb711659c3f4833c7f9`,
   still has `getScale`, `float(1/scaleFactor)`, `std::pow((double)factor,
   (double)nlevels)`, the `cvRound` recurrence, signed accumulation, and
   signed residual. Both hosted packages report version string 5.0.0, but
   neither records that commit.

2. **Probe compiler family is close to the recorded native compiler, not
   proof of equal flags.** macOS native build information says clang++
   `16.0.0.16000026`, and the probe is Apple clang `1600.0.26.4` with SDK
   15.1. Windows native build information says MinGW64 g++ 16.2.0, matching
   the probe's `g++ --version`. Native flags are Release and do not display
   `-ffast-math`, but the macOS native unit was built `-O3` while the
   certificate also depends on O0/O2 probe runs. Windows native flags are
   the package `-O2 -pipe` line, not the probe's explicit `-O0/-O2/-O3`
   matrix. Flag strings in `getBuildInformation` are global configuration
   text, not a per-file command for `orb.cpp`.

3. **macOS loaded the features dylib and one distribution-shaped `pow`.**
   `O3/orb_r3_trace` loaded
   `/opt/homebrew/Cellar/opencv/5.0.0_5/lib/libopencv_features.5.0.0.dylib`.
   `otool -L` records its install name and links to libc++ current
   `1700.255.5` and libSystem current `1345.120.2`. The probe itself links
   libc++ `1800.101.0` and libSystem `1351.0.0`. Those are different
   recorded runtime versions, so probe libm behavior cannot be copied onto
   the dylib by version coincidence.

   Inside `ORB_Impl::detectAndCompute`, disassembly at `0x47908` computes
   `1/scale`, converts to binary32, multiplies by the integer feature count,
   calls `_pow`, converts back to binary32, subtracts from 1, divides, then
   loops with `frintx`, `fcvtzs`, a binary32 multiply by the factor, and a
   saturating residual via `bic`. That is structural correspondence with
   the reviewed distribution expression and with round-to-nearest plus a
   truncating conversion. `getScale` has no separate symbol; its body was
   not reliably separated from other conversions in this text disassembly.
   Another `_pow` in the same function feeds image-scale setup. A third
   `_pow` belongs to `SIFT_Impl::buildGaussianPyramid` and is not ORB
   evidence. Four `_pow` sites exist in the captured text; only the
   distribution site is attributed.

4. **Native extraction in the R1 probe did run ORB.** Each
   `orb_levels_probe` log ends `PASS targets=151547 levels=8 native
   extractions=8` after `cv::ORB::create` and `detectAndCompute` for levels
   1..8, with OpenCL explicitly disabled in that probe. The R3 trace does
   **not** call ORB. It calls only `getBuildInformation` before enumerating
   modules, so its module list is not an ORB call stack.

### What is not established

- macOS `getScale` was not isolated as a callable symbol, so its native
  `pow` input and binary32 store are not separately attributed.
- The features dylib's `_pow` is an undefined libSystem symbol. The audit
  has not identified which `pow` implementation that older linked libSystem
  uses, nor the rounding mode in force when ORB runs inside a larger process.
- The macOS version-control field is `unknown`. Bottle `5.0.0_5` predates
  the current formula revision and its later patches. No installed
  `orb.cpp` hash was captured.
- Windows `O3` module enumeration never loaded `libopencv_features-500.dll`.
  The harness therefore had no features path to pass to `objdump`.
  `native/features-linkage` and `native/features-disassembly` do not exist.
  The trace links only core. Its imports are `libgcc_s_seh-1.dll`,
  `KERNEL32.dll`, `msvcrt.dll`, `libopencv_core-500.dll`, and
  `libstdc++-6.dll`, with no `pow` import in that core-linked probe image.
  The O0 probe image contains a local `pow` thunk, which shows the probe's
  math call, not ORB's.
- Windows native provenance says `eb52293-dirty`. No public OpenCV commit
  with that prefix was found. The dirty marker means the packaged tree was
  not the unmodified commit. Package release 5 is also older than the
  current MSYS2 `pkgrel` 7. The installed `orb.cpp` bytes are unresolved.
- Both libraries configure OpenCL. The R1 probe disables it for its own
  process; the installed default for a consumer is not certified here.
  Forced OpenCL, custom HAL, another architecture, or a changed rounding
  mode remains outside this evidence.
- Header hash equality shows the include selected while preprocessing the
  probe. It does not show the macros defined while the installed ORB
  translation unit was compiled.
## Discrepancies from R1/R2 assumptions

- R1/R2 left Apple and Windows execution pending. Those probe executions now
  exist and pass. The pending item moves from "no logs" to "logs do not
  identify the installed ORB object."
- Hosted OpenCV is 5.0.0 packaging, not a rerun of the Linux 4.1.0/4.10.0
  source-pinned qualification. Linux source review remains separate.
- macOS is arm64 NEON. The R1 local cvRound discussion used an x86-64 SSE
  path. The macOS probe instead exercises Apple clang/libSystem. The
  certificate's monotone `|R(x)-x|<=1` contract is still the assumption;
  arm64 `frintx` in the observed distribution loop is consistent with it
  but is not a universal ARM override proof.
- Windows probe `cvRound` takes the SSE2 branch. The native package was
  configured with `-march=nocona`, which is also SSE2-class, but the ORB
  object was not disassembled to confirm `cvtss2si` rather than a later
  builtin or library call.
- Factor level 7 differs by one ULP between Apple libSystem and the MinGW
  math runtime. R1's finite-input check allows that. It also shows why a
  single platform's `pow` result cannot be copied to the other.
- macOS native libc++ / libSystem versions differ from the probe's loaded
  versions. Equal compiler marketing versions do not reconcile that.
- No numerical tolerance, feature cap, or level range was changed to obtain
  these results.

## Unresolved questions

1. What are the exact bytes of `modules/features/src/orb.cpp` inside Homebrew
   `opencv` bottle `5.0.0_5` and MSYS2 `mingw-w64-x86_64-opencv 5.0.0-5`?
2. What was the full compiler command for that translation unit, including
   architecture, fast-math, contraction, and rounding-related macros?
3. Which `pow` and rounding implementation does each installed ORB call
   reach, given the macOS libSystem version skew and the absent Windows
   features image?
4. Can `getScale` be attributed in the macOS binary, or is it only inlined
   into `detectAndCompute`?
5. Does a consumer that does not call `setUseOpenCL(false)` stay on the CPU
   path exercised by the probe?

## Smallest R3E follow-up, not dispatched

Do not rerun the 151,547-target matrix. One hosted evidence job per
platform is enough if it does all of the following and then stops:

1. Print the installed package identity and the full
   `getBuildInformation` compiler block.
2. Hash the installed `orb.cpp` if the package ships it, or otherwise
   extract debug/source mapping sufficient to bind the binary to bytes.
   If the package has no source, record that absence and stop with
   correspondence still pending rather than guessing.
3. Load `libopencv_features` explicitly. On Windows, `objdump -p` and a
   symbol-filtered disassembly of `libopencv_features-500.dll` must include
   its `pow`/rounding call sites. On macOS, record `otool -L` for both the
   probe and the dylib, and isolate `getScale` or state that the symbol is
   absent.
4. Keep the existing eight factor and eight scale inputs as a control, with
   the same `2^-20` rational check. Do not change tolerances.

Until that attribution exists, the safety gate stays not established.

## Evidence map

- Archives and manifests: paths and hashes above.
- Numerical logs: `<platform>/O{0,2,3}/orb_r2_numerics.stdout.log`,
  `independent.stdout.log`, `orb_levels_probe.stdout.log`,
  `r1-certificate.stdout.log`, and `orb_r3_trace.stdout.log`.
- macOS native binary: `macos/native/features-linkage.stdout.log`,
  `features-symbols.stdout.log`, `features-disassembly.stdout.log`, and
  `features-arithmetic.log`. The distribution site is disassembly line
  71090 of the captured text (`bl _pow`), with the rounding loop continuing
  at line 71097.
- Windows gap: `windows/O3/orb_r3_trace.stdout.log` loaded-module list and
  `windows/O3/linkage.stdout.log` import table. No features disassembly was
  present to omit.
- Headers: both `selected-fast-math.txt` files, hash above.
- Package identity: `macos/homebrew-opencv.log`,
  `macos/package/modversion.stdout.log`,
  `windows/preflight/packages.stdout.log`, and
  `windows/package/modversion.stdout.log`.


| Layer | macOS | Windows |
| --- | --- | --- |
| Source-level expression | Reviewed tag only; installed bytes unresolved | Reviewed tag only; dirty package unresolved |
| Compiler and FP semantics | Probe established; native unit pending | Probe established; native unit pending |
| Loaded math/rounding implementation | Distribution calls `_pow` and `frintx`; provider pending | Installed features image not captured |
| Tested numerical inputs | Established for the probe | Established for the probe |
| Independent all-target bound | Established conditionally for the probe contract | Established conditionally for the probe contract |

  and the coarser R1 ceiling `1_986_422_381`;
- doubled target exactly 2147483646, one below the signed 32-bit maximum;
- residual subtraction strictly above `-2^31`.

The R1 log tail is identical across modes:
`uniform reserve <= ceil(1.85*Nmax+8) = 1986422381` and
`residual subtraction >= -912680557`. The R2 checker also passed its
independent `.58` and per-level majorants. `E=8` is unchanged. `N=1` is
inside the probed prefix `1..4096` and remains covered by the integer
`A0 <= N` argument, not by a new sampled claim.

Thus the arithmetic premises remain supported **for these probe processes**:
IEEE binary32/binary64, 32-bit signed `int`, the named stored constants,
evaluation method 0, nearest rounding at the start of the probe, no
fast-math in the probe build, and `pow` errors inside `2^-20` on the finite
input set. That does not move the installed ORB binary into the same
category.

`repository-checks`, `linux`, `linux-sanitizers`, `macos`,
`orb-r3-macos-numerics`, and `orb-r3-windows-numerics`. The two production
Linux jobs and the production macOS job are not used as ORB numerical
evidence.

This audit adds documentation only. It does not reset, clean, rebase, or
overwrite the protected Task 008B, Task 010, R1, or R2 worktrees. R1/R2
certificates, probes, the `2^-20` tolerance, admission limits, production
sources, and workflows are unchanged.
