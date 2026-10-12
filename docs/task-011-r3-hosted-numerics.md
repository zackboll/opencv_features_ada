# Task 011-R3 — hosted numerical qualification

## Campaign preparation

Disposition: **PLATFORM_EVIDENCE_PENDING** until actual hosted evidence and
native-build correspondence are reviewed. No configurable ORB implementation.

Main fetched at `495e385f91022735d5c52ba766f8d25164c7a900`; no open PRs at
reconciliation. Isolated branch `research/011-r3-hosted-numerics` starts at
R2 `8127c448a3bb2d811b9ffd1a43db6f18d97ea0eb`.

R1/R2 tools and mathematical tolerances are unchanged. R3 adds a focused runner,
intermediate-value/module trace and text-evidence checksum manifest. The two
new workflow jobs require workflow_dispatch and the exact R3 branch. Existing
production jobs and windows-post-merge.yml are unchanged. A narrow topology
validator extension accepts only the exact guarded R3 jobs; negative tests
reject absent/partial guards.

macOS uses macos-14, Homebrew native OpenCV and Apple clang. Windows uses
windows-latest, Alire-managed MSYS2 and the certified two-stage full upgrade,
then MinGW64 GCC/OpenCV. Both probe O0/O2/O3. These are research jobs, not
Windows production qualification. Existing production jobs also execute on
dispatch because their definitions are deliberately unchanged.

Evidence records exact installed versions, native build information, compiler
flags/macros, selected rounding header, runtime-loaded module paths and probe
disassembly. Only focused text evidence is uploaded, with 14-day retention.
Numerical failures retain original output; no tolerance is relaxed.

Local preparation: Linux probes passed all three optimization modes, including
unchanged R1 recurrence/native extraction and independent R2 rational checks.
Repository checks, 77 configuration tests, profile/layout tests, shell syntax,
YAML production-job equality, and actionlint 1.7.7 passed. Linux results are
not Apple/Windows evidence. The initial topology-check failure was reproduced
and resolved through the guarded validator extension, not hidden.

## Qualification limitations

The source-derived certificate is the all-target argument. Fixed-power checks
compare exact rational references at the unchanged 2^-20 absolute-error bound.
cvRound samples alone do not prove monotonicity for every input; selected header,
architecture and native compilation settings must support the contract.
Trace outputs distinguish Float64 powers from binary32 stores and recurrence.
The shim/probe's settings are not installed ORB's settings. Build correspondence
requires separate review of getBuildInformation and native provenance.

Installed releases other than 4.1.0, 4.10.0 or 5.0.0 are labeled by their exact
version and cannot substitute for those reviewed releases without further source
review. Missing native FP flags or math-provider correspondence leave the gate
pending even if all sample probes pass. A genuine numerical violation gives
SAFETY_GATE_NOT_ESTABLISHED, while unavailable builds/infrastructure remain
separately identified.

## Protected state and handoff

R1 worktree remains clean at `f29d988599d538a8edecafdc631b1c8f2d99a930`;
R2 remains clean at its starting commit. Its evidence index SHA-256 remains
`086cc557cde49f044417cd91ba15490ac553496ff6e436d14351a3aff4ded3d2`.
Both Task 008B worktrees remain clean at
`670643d36f6fdcb0e96fcc5ee9ee702dc7a2cad3`. Task 010's retained documentation
hashes verify; existing untracked research is preserved.

The campaign commit/run identities are recorded after the single authorized
dispatch. If it is still in progress, stop rather than poll or dispatch again.
No PR, production edits, Core pins, manifests, C ABI, merge, tag or release.
Any subsequent handoff commit must preserve the earlier tested SHA separately.