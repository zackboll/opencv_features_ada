# Task 011-R1 — all-target conditional arithmetic certificate

## Disposition and scope

**SAFETY_GATE_NOT_ESTABLISHED** for the complete supported-platform profile.
The missing all-N derivation is now supplied below. Its numerical preconditions
are checked on the available Linux configurations, but not yet on Apple
libSystem/libc++ or the matching MSYS2 Windows runtime. C++ itself supplies no
portable pow accuracy guarantee. Do not implement or publish the configurable
binding on the strength of this conditional certificate alone.

## Source and types

The three immutable ORB identities and SHA-256 hashes in
[the initial source review](orb-pyramid-levels-source-review.md) were retained.
Distribution lines are 798–808 (4.1), 845–855 (4.10/5.0). Factory storage is
float 1.2f promoted exactly to double in ORB_Impl. The integer N is converted
to float by usual arithmetic conversions in `N * (1 - factor)`. The literal
1 converts to float in both subtractions. The product and division have float
type. `pow` takes two explicitly converted doubles and returns double, then
casts to float. Every recurrence assignment stores float. L-1, array indices,
sumFeatures and the residual subtraction are native signed int. Matching
source text alone does not establish matching evaluation precision or libm.

The reviewed upstream `modules/core/include/opencv2/core/fast_math.hpp` files:

| Revision | SHA-256 |
| --- | --- |
| 4.1.0 | `c03db070cc0887290621b378607b6f008d7a19093ba46419b2870e2be24b8814` |
| 4.10.0 | `d7e869721c2e5d588b2bcf7dcc3a3b2a692a9a61af9f896498b6f4288dccff8d` |
| 5.0.0 | `cb39ce1134293ced080295dcac642bd863ef3b2421f38d8019e0b345524c1bde` |

4.1 cvRound(float), lines 182–207, selects SSE conversion, x87, ARM conversion,
lrintf, or a fallback float-add-and-cast. 4.10 lines 322–343 and 5.0 lines
330 onward select architecture overrides, SSE/x87 or builtin/library lrintf.
The certificate assumes a monotone integer rounding function R with
`abs(R(x)-x)<=1`, `R(0)=0`, for nonnegative in-range x. SSE nearest/directed
conversion and lrintf meet that contract in a fixed rounding mode. The 4.1
generic fallback and user-defined architecture overrides require separate
qualification; the float-add fallback is not silently covered by the <=1
assumption at large x. Local x86-64 probes use the SSE path.

## Explicit numerical preconditions

1. IEEE binary32/binary64, native 32-bit int; ordinary correctly rounded basic
   operations and conversions, no fast-math reassociation/approximate division.
   Evaluation uses binary32 stores and no reduced precision. Wider evaluation
   needs its own qualification if it changes the named rounding boundaries.
2. Fixed floating rounding mode during an extraction; nearest mode is qualified
   locally. The relative bound below allows a full spacing, not just half-ULP.
3. For the fixed reciprocal factor f and L=1..8,
   `abs(pow(double(f),double(L)) - f**L) <= 2^-20`, with finite result.
   This is a stated **precondition**, not a portable C++ guarantee.
4. R meets the cvRound contract above. Forced OpenCL/custom HAL paths are outside
   this CPU-Mat certificate, as in the existing source review.

The stored nearest binary32 literal is exactly
`s = 5033165/4194304 = 1.2000000476837158203125`. Promotion to double is exact.
The exact reciprocal is `4194304/5033165`; rounding it to nearest float gives
`f = 13981013/16777216 = 0.833333313465118408203125`.
Let `u = 2^-23`, a full binary32 relative spacing allowance. Rational checks
establish `0.83 < (1/s)(1-u) <= f <= (1/s)(1+u) < 0.84`.
The native literal/reciprocal observed in all local probes match those values.

## Outward rational interval derivation

Let `a=.83`, `b=.84`, `e=2^-20`. All decimal quantities here denote exact
rationals, not decimal floating constants. For L>=2:

```
double pow result in [a**L-e, b**L+e]
float power p in [(a**L-e)(1-u), (b**L+e)(1+u)]
d = float(1-p) >= (1-(b**L+e)(1+u))(1-u) = d_min > 0
float(N) in [N(1-u), N(1+u)]
1-f in (0.16,0.17)
q0 <= N * c_L
c_L = .17(1+u)**3 / d_min
```

The subtraction 1-f is exact by Sterbenz's lemma (both operands within a
factor two); hence no extra numerator-subtraction error is omitted. The three
numerator/quotient factors cover N conversion, product, and division. A lower
bound for q0 is `.16*N*(1-u)**3 / d_max`, with
`d_max=(1-(a**L-e)(1-u))(1+u)`. Every operation is positive, finite and normal
at N>=1; the smallest of the at-most-seven shares stays well above underflow.
All intermediates are far below binary32 overflow.

The exact fractions, rather than the displayed approximations below, are
checked by `docs/research/orb_levels_certificate.py`:

| L | c_L (display only) | L*c_L (display only) | ceil(c_L*Nmax+1) |
| --- | ---: | ---: | ---: |
| 2 | .577447963081 | 1.154895926163 | 620030030 |
| 3 | .417388112345 | 1.252164337035 | 448167074 |
| 4 | .338559505452 | 1.354238021808 | 363525502 |
| 5 | .292203272439 | 1.461016362197 | 313750876 |
| 6 | .262062318668 | 1.572373912007 | 281387273 |
| 7 | .241166110734 | 1.688162775141 | 258950141 |
| 8 | .226026929981 | 1.808215439846 | 242694569 |

All c_L < .578 and all L*c_L < 1.85. The first integer target A0 satisfies
`A0 <= c_L*N+1`. This +1 derives from the explicit rounding contract.

## Recurrence and every signed consumer

For stored q>=0, `q*f < q` since f<1. Correct rounding of q*f cannot exceed
the already representable q in any fixed IEEE rounding mode. It is monotone
as a function of q. Consequently stored shares and their rounded integer
targets are nonincreasing, nonnegative, finite, and at most A0. Explicit
intervals for q_i are
`q0_lower*(a*(1-u))**i <= q_i <= q0_upper*(b*(1+u))**i`.
R(q_i) lies between q_i-1 and q_i+1; monotonicity gives the tighter A_i<=A0.
The following bounds hold for **every** integer N, not only Nmax:

- For N>=3, `.578*N+1 <= N`. For N=1 or 2, `c_L*N+1 < N+1`, so the integer
  A0<=N. Every preceding target is therefore <=N and representable by cvRound.
- Every intermediate partial sum S contains at most L-1 nonnegative targets.
  `S <= (L-1)(c_L*N+1) <= 1.85*N+(L-1)`.
  At Nmax this is at most **1,986,422,380** after outward integer rounding.
  This bound does not assume S<=N; small requests can over-distribute.
- `N-S` lies between `-.85*N-7` and N, hence between **-912,680,557** and
  **1,073,741,823**. Signed subtraction cannot overflow.
- Residual B=max(N-S,0) is in [0,N]. It need not follow the decreasing-share
  sequence; it is independently bounded.
- Harris reserve `L*A0 <= 1.85*N+L <= 1.85*N+8`. The derived uniform additive
  allowance is **E=8**, one rounding unit per factor L, not an arbitrary margin.
  The outward maximum is **1,986,422,381**, below M=2,147,483,647.
- Unconditional `2*A0` reserve and Harris `2*featuresNum` for every earlier
  target and the residual are <=2N<=**2,147,483,646**. FAST reaches the reserve
  too; it cannot be excluded from this check.
- Harris' second retainBest uses the undoubled targets; all are nonnegative
  signed int. Vector lengths for layers, targets and counters are L<=8;
  indexing `nlevels-1` and level increments cannot overflow.
- Per-level counters, total vector-size-to-int conversions, and `offset +
  nkeypoints`/`offset += nkeypoints` consume actual candidates, not target
  counts. The unchanged image bound gives total candidates <=8*rows*columns
  < W*H<=M. Offsets are partial sums of those nonnegative counts. No target
  hard-cap assumption is made; response ties can exceed the target.
- Descriptor allocation takes the candidate count as signed rows, fixed 32
  columns and UInt8 C1 type. Byte capacities are size_t; vector/Mat allocation
  can fail. This certificate does not guarantee available RAM or size_t byte
  capacity on unqualified 32-bit platforms. Existing supported 64-bit targets
  can represent 32*M and the fixed-size keypoint storage products.

**L=1:** q0 is still computed, with positive denominator bounded away from zero
by the same f/pow premises, but is never passed to cvRound. S=0 and the sole
target is exactly integer N. Doubling is <=M-1, Harris reserve is N, residual
subtraction is N. Counters/descriptors retain the image-derived proof. Do not
replace this integer target with rounded q0.

## Math-library qualification and remaining limitations

Downloaded glibc 2.41 `sysdeps/ieee754/dbl-64/e_pow.c` advertises worst-case
0.54 ULP at its source header. URL:
`https://raw.githubusercontent.com/bminor/glibc/glibc-2.41/sysdeps/ieee754/dbl-64/e_pow.c`.
SHA-256: `1a1051692682d6fe790dc6cdf885fb7b79d60fcf9b3a61314439a2d9f5593ef7`.
That claim is much tighter than e, but is **not** treated as proof that every
installed/vendor implementation uses this code or as Apple/Windows evidence.

Local qualification uses a simpler finite-input check: only eight pow inputs
exist for the observed stored factor. Each hexadecimal double output was
converted back to an exact rational and compared to the exact rational f**L
by the Python certificate. Thus these particular observed libm results meet e
without assuming perfect rounding or relying on the probe's long-double
reference. The N-dependent integer proof then covers omitted target ranges.

Still missing for the full profile:

1. Apple clang++/libc++ with libSystem: finite-input pow interval verification,
   expression evaluation and selected cvRound-path qualification.
2. Matching MSYS2 g++/libstdc++/math DLLs: the same qualification. Linux clang
   with libstdc++ is not Apple or Windows certification.
3. Any supported nondefault FP environment or architecture override must satisfy
   the stated premises; no arbitrary mode-changing concurrent code, fast-math,
   x87 excess precision, custom round macro, or generic fallback is admitted.

## Compiled evidence and reproduction

Linux x86-64, g++ 14.2.0 (Debian 14.2.0-19), clang++ 19.1.7,
libstdc++ macro 20250315, glibc 2.41-12+deb13u4. FLT_EVAL_METHOD=0,
FE_TONEAREST, no fast-math. Eighteen successful configurations:
OpenCV 4.1.0/4.10.0/5.0.0, each compiler, each -O0/-O2/-O3.
Each executes 151,547 distinct target values times eight levels, plus eight
actual upstream ORB extractions. These are probe checks, not AUnit additions.
Targets include 1..4096, powers-of-two neighborhoods, binary32 transitions and
conversion midpoints, share-rounding candidates, the last 8193 targets,
Nmax, and deterministic seeded stress samples. Stress is not universal proof.

The old native 4.1/5.0 installations were read only; no protected worktree or
artifact was rebuilt. Initial clang 4.1 compilation with upstream headers as
ordinary includes failed -Werror on upstream `_Atomic` extensions; diagnostics
are preserved. Reruns classify pkg-config upstream includes as system headers,
retaining warnings-as-errors for the probe, and pass. This is research compiler
coverage, not a production build-option change.

Run `sh docs/research/run_orb_levels_probe.sh OUTPUT_DIR` in an environment
selecting the intended OpenCV via PKG_CONFIG_PATH and LD_LIBRARY_PATH. Select
CXX and OPT explicitly. Then pass its probe.log to the Python certificate.
Full raw local logs and downloaded sources stay outside the repository.

## Alternatives and recommendation

A smaller N cap alone cannot cure an unbounded/NaN pow implementation: a bad
denominator can invalidate conversion even for N=1. No arbitrary cap is
recommended. The source-derived alternative for separate review is a finite
startup/runtime profile preflight checking the eight power results against
exactly certified outward intervals, with rejection before native execution,
plus the qualified rounding/evaluation contract. This task implements no
preflight and does not weaken the existing eight-level admission range.

Next: independently review the rational certificate, then qualify the eight
power inputs and rounding paths on Apple and Windows, or explicitly approve
a guarded numerical-profile design. Only then decide whether the complete
supported-profile gate permits implementation.
