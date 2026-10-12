# Task 011-R2: independent derivation and platform qualification handoff

## Disposition

**PLATFORM_EVIDENCE_PENDING**. The R1 arithmetic certificate remains
conditionally valid. No required inequality failed. Actual Apple and Windows
execution environments were not available in this Linux session:
**MACOS_EVIDENCE_PENDING**, **WINDOWS_EVIDENCE_PENDING**.

This is a second derivation by the coding agent, not a claim of review by a
separate human, formal prover, or independent organization. Neither the R1
Python checker nor its sampled target results were used as the mathematical
oracle for the independent inequalities below.

Starting main: `495e385f91022735d5c52ba766f8d25164c7a900`.
R2 starting HEAD: `f29d988599d538a8edecafdc631b1c8f2d99a930`.
Separate branch: `research/011-r2-platform-numerics`.
All R1 files remain unchanged; R2 adds research files only.

## Independent rational derivation

Use binary32 relative spacing allowance u=2^-23 and assumed absolute double
pow error e=2^-20. For positive normal correctly rounded basic operations,
relative error is at most u, including directed rounding. Local qualification
is narrower: round-to-nearest, FLT_EVAL_METHOD=0, no fast-math.

Native nearest binary32 1.2 is s=5033165/4194304. Its exact double promotion
has no error. Double division followed by float conversion yields
f=13981013/16777216. The independent checker verifies that the exact reciprocal
plus/minus half a binary64 spacing (2^-54 at this exponent) remains strictly
inside the nearest binary32 cell centered at f with half-width 2^-25.
Thus this two-stage calculation is not assumed equivalent to single rounding.
For this cell, .83<f<.84. `1-f` is exact by Sterbenz and less than .17.

For L=2..8, let b=.84. The double power is at most b^L+e; it is less than one.
Its conversion to float adds at most u in absolute error. The denominator
subtraction adds at most u; since 2u<2e, a deliberately coarser lower bound is

```
d >= 1 - b^L - 3e > 0.
(1+u)^3 < 1+e.
q0 <= .17*N*(1+e)/(1-b^L-3e).
```

The three relative factors cover integer-to-float conversion, numerator
multiplication, and division. No numerator-subtraction rounding was omitted.
This absolute denominator-error construction differs from R1's relative
denominator formula. Exact rational cross-products establish the following
simple upper majorants, without importing or executing the R1 certificate:

| L | q0/N upper majorant | L times majorant |
| --- | ---: | ---: |
| 2 | .580 | 1.160 |
| 3 | .420 | 1.260 |
| 4 | .340 | 1.360 |
| 5 | .295 | 1.475 |
| 6 | .265 | 1.590 |
| 7 | .245 | 1.715 |
| 8 | .230 | 1.840 |

All displayed decimals are exact rational choices, verified by cross
multiplication in `docs/research/orb_r2_independent.py`. They are research
majorants, not authorized production limits/constants. This independent proof
actually obtains L*q0 <1.84N, which implies the requested looser 1.85N bound.

Under the explicit monotone cvRound contract |R(q)-q|<=1, A0<=q0+1.
For N>=3, .58N+1<=N; for N=1,2, .58N+1<N+1 and integer A0<=N.
Since f<1, rounding the product of a stored nonnegative q and f cannot exceed
the already representable q. Correct rounding is monotone. Hence each stored
share and each integer target is nonincreasing and no greater than A0<=N.
The independent lower bound `.16*(1-u)^3*(.83*(1-u))^7 > .04` excludes share
underflow even at N=1; positivity of the denominator and modest upper bounds
exclude NaN, infinity and division by zero under the stated pow premise.

Every partial S is a sum of at most L-1 nonnegative targets:
S<=(L-1)(q0+1)<=1.85N+7. Every intermediate is bounded, not merely the final
sum. Thus N-S>=-.85N-7 and <=N; it cannot underflow or overflow. Residual
B=max(N-S,0) lies in [0,N] independently of monotonicity. Both earlier targets
and B admit doubling <=2N<=2147483646. Harris reserve L*A0<=1.85N+8. All these
are signed products before vector size_t conversion; allocation success is
not promised.

### Integer floor versus conservative ceiling

At Nmax=1073741823:

| Bound | Exact rational real value | Integer floor | R1 outward ceiling |
| --- | ---: | ---: | ---: |
| (37/20)Nmax+8 | 39728447611/20 = 1986422380.55 | **1986422380** | 1986422381 |
| (37/20)Nmax+7 | 39728447591/20 = 1986422379.55 | **1986422379** | 1986422380 |

R1's ceilings are safe, not mathematical errors. They are not the tight integer
maxima implied by those real inequalities. No production change is necessary.
The +8 allowance is one integer rounding unit multiplied by L<=8.

### Candidate counts and the one-level path

For CPU FAST with nonmaximum suppression, at most one candidate originates
per level pixel. Filtering/retainBest only removes points; all response ties
may remain. Thus no requested-feature hard cap is assumed. With positive
native stored pyramid scales >=1 and qualified monotone dimension rounding,
level dimensions do not exceed source dimensions. Therefore total candidates
<=L*rows*columns<=8*rows*columns<W*H<=INT32_MAX. Vector-size casts, counters,
offsets and offset partial sums fit. Descriptor rows fit int; byte capacities
use size_t. Supported 64-bit allocation arithmetic is distinct from RAM
availability. Small native dimensions remain >=1 since stored scales <4 and
nearest rounding maps 2/scale to at least one for this fixed scale profile.

**Additional explicit dependency:** getScale uses pow(double(s),level),
level=0..7, followed by float conversion. R1 distribution-factor power outputs
alone do not qualify the image-envelope premise. R2 inventories these eight
scale-power inputs too. For level zero it requires exact one; remaining stored
scales are >1 and <4. At level zero division/inverse and dimension conversion
must preserve dimensions (the existing image envelope bounds dimensions well
below 2^24). At higher levels the gap from one exceeds floating error by many
orders, so correctly rounded division or inverse/multiplication cannot enlarge
an integer source dimension. The prior structural/Harris/descriptor index
review remains applicable, not replaced by a target-count bound.

L=1 still computes an unused float share. f and the qualified power error leave
its denominator positive. No float share conversion occurs in the distribution
loop; S=0 and the sole integer target is N. Harris reserve=N and doubling=2N.
Candidate count and getScale(0) requirements remain separate.

No circular target assumption was found: monotonicity follows from correctly
rounded multiplication, sums from the first-share majorant, and candidate
counts from the image profile. Pow accuracy remains a named external premise;
stress sampling does not justify it. A fixed-input exact-output check can
establish it for a particular implementation and environment, not all builds.

## Native build correspondence and local execution

Available host: Linux x86-64 only. No native Apple tools, PowerShell/Windows
runtime or assigned remote platform execution facility was available. No SSH
host was guessed, no workflow dispatched, and no remote write attempted.

Inspected native configurations:

- Debian OpenCV 4.10.0+dfsg-5, compiler g++ 14.2.0, Release -O2, C++11,
  SSE/SSE2 baseline, reported native flags do not enable fast-math.
- Retained OpenCV 4.1.0 build: g++ /usr/bin/c++, Release -O3, C++11,
  SSE2/SSE3, ENABLE_FAST_MATH=OFF; actual orb.cpp flags in build.ninja inspected.
- Retained OpenCV 5.0.0 build: g++ /usr/bin/c++, Release -O3, C++17,
  SSE3, ENABLE_FAST_MATH=OFF; actual orb.cpp flags inspected.
- Installed libstdc++ 14.2.0-19; glibc/libm 2.41-12+deb13u4. Probes report
  FLT_EVAL_METHOD=0 and FE_TONEAREST. All use real installed native libraries.

R2 successfully executed g++ O0/O3 on each native version, g++ O2 on 4.10,
and clang++ 19.1.7 O2 on 4.10: eight configurations. Each runs the new boundary/
conversion/scale-power probe and the preserved R1 all-level recurrence/actual
ORB driver (151547 targets x eight levels, eight extractions). All exact
rational power-output checks passed, including actual errors and rational
references recorded externally. The Linux clang build is supplemental probe
compiler evidence, not the compiler that built the native ORB library.

Native C++11 versus probe C++17 does not change these fundamental arithmetic
conversion rules or the explicitly double pow overload, but headers, compiler,
FP flags and emitted instructions still require review. NDEBUG affects only
assertions; it does not alter ORB's numerical expressions. Probes retain checks.
Non-FP warning/visibility/section flags do not alter the expressions. Native
SSE flags and no fast-math corroborate the local evaluation model; actual
Apple/Windows builds must establish their own correspondence. getBuildInformation
and probe linkage are preserved in every run. These results are bounded local
evidence, not certification of arbitrary future packages or architecture overrides.

## Reproducible actual-platform qualification

The runner records compiler, pkg-config metadata, complete native build info,
power and boundary outputs, exact rational errors, and linkage. It preserves
R1 sources unmodified. Use output directories outside Git. No workflow edits
or dispatches are needed or authorized.

### macOS — MACOS_EVIDENCE_PENDING

Existing workflow uses macos-14, Homebrew OpenCV, Apple clang, libc++, libSystem.
Actual versions, architecture and build flags: **not observed here**. On an
already provisioned real supported host, select the matching pkg-config native
package (opencv4 or opencv5), then execute:

```sh
xcrun clang++ --version
sw_vers
uname -m
brew info --json=v2 opencv > "$EVIDENCE/homebrew-opencv.json"
for opt in 0 2 3; do
  CXX="$(xcrun --find clang++)" OPT="$opt" OPENCV_PACKAGE=opencv4 \
    sh docs/research/run_orb_r2.sh "$EVIDENCE/apple-O$opt"
done
```

Set OPENCV_PACKAGE to the actual installed package; isolate metadata if two
versions coexist. Confirm libc++ and libSystem with otool, not libstdc++.
Inspect the selected fast_math.hpp branch, preprocessed macros, and the native
build's ORB FP flags. For arm64, do not label the rounding path SSE2. Native
build optimization must be matched or separately explained. If build info
cannot establish absence of unsafe FP flags, retain a build-correspondence
blocker rather than inferring it from successful extraction.

### Windows — WINDOWS_EVIDENCE_PENDING

Existing policy is main-only Windows post-merge workflow, Alire-managed MSYS2,
MinGW64 g++/libstdc++, mingw-w64-x86_64-opencv. Do not substitute MSVC or a
separate MSYS2 installation. Actual compiler/runtime/DLL versions and flags:
**not observed here**. On an already provisioned real host, use the driver
selected by the certified Features configuration, run within that managed
MSYS2 environment, and preserve `pacman -Q` package versions. From that shell:

```sh
driver=$(sed -n 's/^[ ]*Cxx_Driver := "\(.*\)";/\1/p' config/opencv_features_install.gpr)
case "$driver" in *gnat_native*) exit 1;; *mingw64*/bin/g++*) ;; *) exit 1;; esac
pacman -Q mingw-w64-x86_64-gcc mingw-w64-x86_64-opencv > "$EVIDENCE/packages.log"
for opt in 0 2 3; do
  CXX="$driver" OPT="$opt" PYTHON=python OPENCV_PACKAGE=opencv4 \
    sh docs/research/run_orb_r2.sh "$EVIDENCE/mingw64-O$opt"
done
```

The configured native DLL directory must precede competing runtimes, while the
external compiler is invoked by its explicit path, not injected into Ada PATH.
Also record loaded module paths and versions using the native Windows tooling;
PE import names alone do not establish which DLLs the loader selected. Verify
the actual math provider (MinGW helper, CRT or compiler-folded call) from imports
and disassembly, rather than assuming MSVCRT/UCRT or Linux libm. Preserve selected
fast_math.hpp and native build flags, and inspect cvRound lowering. The diagnostic
O0 run does not replace the installed ORB Release configuration.

## Fallback research — no implementation

A proposed native numerical-profile preflight could avoid relying on a libm
accuracy specification by enumerating the fixed reciprocal/power results,
checking finite positive stored denominators/shares and checked int64 shadow
arithmetic before native execution. Rationally generated outward dyadic bounds
could be checked using exact representable comparisons, not another pow call.
Include getScale inputs, FP mode, architecture and rounding path; distribution
inputs alone are insufficient. Reject on a profile mismatch before native ORB.

The independent .58 and per-level majorants above justify keeping the full N
range **if** this profile and the remaining basic-operation/cvRound contract
are established. A smaller target cannot repair a NaN or unbounded denominator;
no narrower arbitrary target is proposed. The existing eight-level constructor
must retain its admission range.

This preflight's libm assumptions are easier to check (finite fixed inputs),
but it does not automatically solve correspondence: a shim may use different
compiler flags or math entry points from OpenCV. A credible design must match
or attest the native build and protect the FP environment through the call,
or reject the unqualified configuration. It cannot claim arbitrary vendor ORB
behavior based on shim-only observations. This is separate-review research,
not an implemented fallback or a passed gate.

## Evidence and protected state

Raw R2 evidence is retained in the sibling `features-011-r2-evidence` directory.
`docs/research/orb_r2_evidence.json` indexes relative log names and SHA-256 hashes;
no build artifacts or environment-specific paths are committed.
All three retained immutable ORB source hashes and 18 R1 successful log hashes
verified. The original R1 worktree remains clean at its starting commit.
Both Task 008B protected worktrees remain clean at
`670643d36f6fdcb0e96fcc5ee9ee702dc7a2cad3`. Task 010's existing untracked research
inventory remains present and its retained documentation hash list verifies.
No protected source, build artifact, pin or workflow was changed.

Final static/configuration validation passed: repository checks (17 ABI exports,
67 AUnit registrations, not executions), 76/76 configuration tests, profile/C
header/layout checks, shell syntax, and all 58 indexed raw-log hashes. No new
AUnit execution or Apple/Windows test execution is claimed. Retained 4.1 and
5.0 native-build source files match the immutable reviewed ORB hashes.

Next gate: obtain real Apple/Windows numerical logs and native-build provenance,
then independently check them against this conditional proof. No production
implementation may advance from this pending disposition.