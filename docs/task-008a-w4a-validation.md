# Task 008A-W4A — consistent managed MSYS2 upgrades

## Evidence and scope

Starting main: `6fb666363767dee49d395fc8f77a2ea475fd4ea9` (PR #11).
Windows run `38187939229`, job `114614253384`, failed in
`Install MSYS2 native dependencies`, before Features compilation or consumer
qualification. The artifact API reports zero artifacts; this is expected,
not an artifact-upload defect. Raw job diagnostics were retained locally.

Alire's initial external dependency deployment installed GCC, `cc-libs`,
`libgcc`, `libstdc++`, `libquadmath`, and `libgfortran` at `16.2.0-4`.
The workflow then executed `pacman -Sy --noconfirm --needed` with the three
native targets. After refreshing databases, pacman proposed `libgcc` and
`libstdc++` at `16.2.0-5` and rejected the transaction:

```text
error: failed to prepare transaction (could not satisfy dependencies)
:: installing mingw-w64-x86_64-libgcc (16.2.0-5) breaks dependency 'mingw-w64-x86_64-libgcc=16.2.0-4' required by mingw-w64-x86_64-cc-libs
:: installing mingw-w64-x86_64-libstdc++ (16.2.0-5) breaks dependency 'mingw-w64-x86_64-libstdc++=16.2.0-4' required by mingw-w64-x86_64-cc-libs
:: installing mingw-w64-x86_64-libgcc (16.2.0-5) breaks dependency 'mingw-w64-x86_64-libgcc=16.2.0-4' required by mingw-w64-x86_64-libgfortran
:: installing mingw-w64-x86_64-libgcc (16.2.0-5) breaks dependency 'mingw-w64-x86_64-libgcc=16.2.0-4' required by mingw-w64-x86_64-libquadmath
```

This establishes a partial-upgrade transaction against older installed
exact-version dependents, not corruption of the installed package database.
The log does not prove that all repository/mirror versions were mutually
consistent. A supported full upgrade can still fail if upstream publication
or mirror synchronization is temporarily inconsistent; such failures remain
fatal and must be diagnosed from their actual next-run output.

## Official procedure and adaptation

- <https://www.msys2.org/docs/updating/>: MSYS2 supports full system upgrades
  only (`pacman -Suy`, equivalent to `-Syu`). Core updates can require closing
  MSYS2 processes and running the upgrade again in a fresh process.
- <https://www.msys2.org/docs/ci/>: automated installations use two separate
  upgrade invocations, for core and remaining packages.
- <https://alire.ada.dev/docs/#alr-on-windows>: Alire manages MSYS2 for external
  tools and libraries. The failed job identifies its managed pacman under
  the Alire cache, rather than the runner's independent MSYS2 installation.

The workflow retains `setup-alire` with `msys2: true`, the selected Ada
toolchain, and MinGW64 packages. Each package command uses `alr -n exec`:

1. `pacman -Syu --noconfirm` in a PowerShell step.
2. The same full upgrade in a fresh PowerShell step/process.
3. `pacman -S --noconfirm --needed` for OpenCV, pkg-config and GCC, without
   another database refresh.
4. `pacman -Dk` to check local package database/dependency consistency.

PowerShell is outside the managed MSYS2 runtime; no managed Bash parent is
kept alive during core replacement. Every native-command exit code is
explicitly checked and thrown on failure, including the first upgrade.
No ignored core-update failure, dependency bypass, downgrade, package removal,
signature override, alternate MSYS2 installation, or PATH/compiler injection
is introduced. `alr exec` may deploy external dependencies on its first use,
as observed in the original log; if that prerequisite itself fails, the
workflow fails rather than disguising it as a successful upgrade.

The Windows trigger, native/consumer qualification and failure-artifact
collection are unchanged. Production sources, GPR configuration, Core pin,
and source-path audit acceptance are unchanged. This is not a correction or
classification of the original Windows resolution-trace reference.

## Regression and qualification

Seven focused configuration tests retain all existing 54 cases (61 total).
They cover full upgrades (including equivalent option ordering/long forms),
rejection of partial upgrades and install-time refresh, required MinGW64
packages/managed environment, separate non-MSYS parent invocations,
mandatory failure propagation and dependency check, and failure artifacts.
These are policy/syntax regressions, not Windows package execution evidence.

Local Linux qualification passed on OpenCV 4.10.0, GNU g++ 14.2.0,
GNAT 16.1.0, GPRbuild/GPRinstall 26.0.0 (crate 26.0.1), Alire 2.1.1:

- Repository checks, 61/61 configuration cases, profile/layout helpers,
  shell syntax and whitespace checks passed.
- AUnit: 67 executed / 67 passed, zero assertions or unexpected errors.
- Six GPRinstall and two installed-link metadata regressions passed.
- Production/fault native boundaries and ASan/UBSan passed, including leak
  detection; no sanitizer error was reported.
- Both examples built and ran (86 zero-distance matches).
- Source-pinned, installed-A and fresh relocated-B consumers passed; A was
  physically removed before B. Strict final metadata and resolution audits
  passed unchanged. Raw Linux consumer evidence was retained locally.
- Actionlint 1.7.12 accepted the Windows workflow. PowerShell 7.6.6 parsed
  all three package steps without errors; this is syntax-only validation.

Exact-head hosted results are reported at the PR review handoff.
Windows certification remains pending the eventual reviewed merge commit's
post-merge workflow, including final installed and relocated resolution audits.