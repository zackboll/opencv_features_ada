# Task 008A — external shim installation / Core 0.4.1

## Provenance and contract

Starting Features main: `4a12eca349df6d53abd54b4711aabfcd884f8667`.
Gate 0 fetched main and found no open Features PRs. Implementation uses an
isolated worktree on `feature/008a-windows-shim-install`; unrelated checkout
changes are preserved.

Core annotated tag `0.4.1`, object
`ee6c92eefd4543845a17f42b174335c13dcbcfe2`, peels to
`386c5360ac51f2b62e522853d94290aec4ee14a0`. All three source pins and the
consumer's resolved-Core assertion use this commit. The dependency constraint
remains `opencv_core = "~0.4.0"`; version remains `0.1.0-dev`. This qualification
does not depend on Alire-index PR #2208 or modify Core/index repositories.

Before production edits, a fresh temporary candidate changing only the three
pins passed production build, 67/67 AUnit tests (zero failed assertions/errors),
actual-shim native boundary checks, both examples, 30 existing configuration
tests, repository checks and profile helpers. The compiled root dependency's
actual clean Git HEAD was checked, not just the manifest. Core 0.4.1 supplies
all APIs required by Features; no API substitution or newer Core main was used.

The defect was the external branch overriding C++ and `cpp/` with empty lists.
GPRinstall rejected no-language projects or emitted abstract projects for a
language without sources. The correction retains the real sources/language,
keeps external MSYS2 compilation ownership, and requires the `.dll.a` via
`Install.Required_Artifacts`, alongside the automatically installed DLL.
Linux Static_PIC and Apple Relocatable production settings are unchanged.
No Ada specs, C++ exports, bridge ownership or public API changed.

## Executed Linux evidence

Environment: Linux x86_64, Alire 2.1.1, GNAT 16.1.0, selected GPRbuild crate
26.0.1 (binary identifies as 26.0.0, 2026-04-15), system g++ 14.2.0.

- Repository checker: PASS, 17 ABI declarations/imports, 67 registrations.
- Configuration discovery: 33/33 PASS; profile/C11 helpers: PASS.
- `sh scripts/test.sh`: 67 executed / 67 successful / zero assertions/errors;
  both production and fault-injection raw native boundary variants PASS on
  system OpenCV 4.10.0.
- Both examples build/run on 4.10.0, including descriptor matching and owned
  correspondence conversion.
- Six GPRinstall regressions PASS with actual GPR tools and tiny isolated
  fixture projects. Both shared library and nonempty synthetic import bytes
  copy exactly; stale static bytes are not installed. A missing required import
  archive fails. External GPRbuild produces no duplicate object. Nonexternal
  mode parsing checks are not cross-platform native linkage claims.
- ASan/UBSan production and fault variants PASS, leak detection enabled, no
  suppressions; pinned source-built OpenCV 4.1.0 also passes 67/67 AUnit,
  raw production/fault boundaries and sanitizer variants.
- Separately built OpenCV 5.0.0 (core/imgproc/features, shared, OpenCL/IPP/TBB
  disabled) passes 67/67 AUnit, raw production/fault boundaries and ASan/UBSan.
  Configuration asserts native 5.0.0/features rather than system 4.10.0.
  The cached upstream 5.0.0 source tarball SHA-256 is
  `b0528f5a1d379d59d4701cb28c36e22214cc51cf64594e5b56f2d3e6c0233095`;
  the unpacked source has no Git metadata, so no starting SHA is invented.
- Modified shell syntax and `git diff --check`: PASS.

The fixture initially incorrectly expected GPRls to list uncompiled C++ files.
Captured output instead reports the actual source search directory. The
assertion was corrected to require that directory; installation assertions
were not relaxed.

The actual resolved Core Git HEAD in production, tests AND examples is the
certified commit. `nm` also confirms **17 defined production C exports**.

## Installed and relocated consumers

Final Linux OpenCV 4.10.0 evidence directory printed by the validator:
`features-consumer.P7ZrWxsW` (under the local temporary directory).

1. Fresh source-pinned consumer: PASS; actual resolved Core HEAD verified.
2. Core then Features recursively installed to prefix A: PASS; four installed
   GPR projects, Core bridge, Ada libraries and both native static-PIC archives.
   Fresh installed consumer build/run: PASS.
3. Prefix A moved to longer prefix B; A physically absent with no symlink:
   VERIFIED. Separate fresh relocated consumer build/run: PASS.

Every mode emits `opencv_features clean consumer ok`. Raw source/install,
build, GPRls/project resolution, linkage, inventory, run and audit logs are
retained. GPRbuild uses portable `-v`; GPRls supports parser `-vP2` and records
both installed GPR project paths. Audits require Core AND Features project,
source and linker paths under the intended installed prefix and reject source
and removed-prefix lookup. The sole retained source reference is an evaluated,
unused Common_Cxx_Switches variable with no Compiler package/use; reported as
provenance, not usable lookup. The old prefix is not silently available.

## Platform and review gates

macOS qualification is hosted PR CI, retaining Apple clang++/libc++ and rejecting
libstdc++. No local macOS execution is claimed. Windows DLL/import installation,
actual native PE imports, installed execution and relocated execution remain
an explicit post-merge main gate; Linux synthetic fixtures are not Windows
native evidence. Windows PR jobs were not added. Pinned compatibility workflow
remains manual and was not dispatched. No merge, release or tag is authorized.

## PR #8 corrective fixture qualification

Starting PR head: `d698958c823e963ca6ea5d19941f649158f7383c`.
Hosted run 37717575918 / macOS job 113117507317 passed production build,
67/67 AUnit and Apple libc++ linkage, then failed the synthetic regression step
with three compiler errors and two path assertions. The original fixture hid
compiler stdout/stderr; the captured command used Apple clang++ with generic
`-shared -fPIC` and no configured SDK. GPRls reported the identical unique
fixture source directory with lowercase `/t/` rather than `/T/`.

The corrective fixture uses `-dynamiclib -isysroot <configured SDK>` and
`-arch <native host architecture>`, retaining the selected Apple compiler.
Linux/Windows compile arguments are unchanged. Captured compiler command,
stdout and stderr appear in failure assertions, and Darwin commands are logged
even on success. One non-oracle predecessor probe records the exact old command
and diagnostics on Darwin; the corrected build must still succeed.

Source-directory comparison normalizes separators and Darwin/Windows case,
retaining the complete unique fixture path and terminal `cpp/`. Negative
subtests reject another fixture directory and a `cpp-other` sibling; a
lowercased Darwin positive checks the observed behavior. All six original
regressions still run, without macOS skips.

Corrective local Linux execution: six regressions PASS; 67/67 AUnit with zero
assertions/errors; 17 actual exports and certified resolved Core SHA verified;
33 configuration tests, repository/profile checks, production/fault native
boundaries and ASan/UBSan PASS. All shell syntax and diff checks PASS.
Fresh three-stage consumer qualification PASS, evidence directory
`features-consumer.1p19gP9l`; original prefix A physically removed and complete
Core/Features installed project/source/library resolution audits PASS.
Exact corrective-head hosted macOS and installed/relocated results must be
checked before declaring the review gate ready; original failed CI is not
substituted for corrected-head evidence.