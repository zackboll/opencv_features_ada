# Task 008A-W4B — inherited consumer PATH sanitization

## Reconciliation and original evidence

Starting `origin/main`: `92d415fe8d8c0bff509fe74baaf2b6f1cf157a57`,
including merged PR #12. No overlapping open PRs were present. Work was
isolated on `corrective/008a-windows-consumer-path-sanitization`; other
worktrees, Task 010 research and surviving Task 008B evidence were untouched.

Retrieved Windows run `38189442183`, job `114618823252`, artifact
`11721391939`, named
`windows-consumer-resolution-92d415fe8d8c0bff509fe74baaf2b6f1cf157a57`.
Archive SHA-256 verified:
`90483440bfef59a998ef03ff5ea13cbd2e6ddcc45898711a5618d9fc871d16f5`.
The unmodified archive, extracted raw records and job log were retained
locally outside the repository.

Both `installed-projects.log` and `relocated-projects.log` have the same
offending entries at lines **228 and 2562**, immediately following `PATH =`.
The exact first two entries of each offending record are:

```text
C:\Users\RUNNER~1\AppData\Local\Temp\features-consumer.gBsRjJm7\candidate\lib
C:\Users\runneradmin\AppData\Local\Temp\features-consumer.gBsRjJm7\features_clean_consumer\alire\cache\pins\opencv_core_386c5360\lib
```

These are entries in one semicolon-delimited native Windows PATH record,
not separate log lines. The remaining entries include selected Alire
GPRbuild/GNAT and system tools; the entire runner PATH is not reproduced here.
Neither captured GPRbuild command log nor the four installed GPR metadata
files contains the original `candidate/lib` reference (slash-normalized).
The finding is inherited GPRls environment diagnostics, not observed active
source inputs or linker options. PATH participates in executable and possibly
DLL lookup; this does **not** establish that all possible effects are harmless.

## Representation and correction

The source-stage capture is `alr exec -- sh` writing `$PATH` to
`toolchain-path.txt`. That file is **not** included in the old diagnostic
artifact: its exact capture-time spelling cannot be asserted from that run.
At the later native GPRls boundary the raw artifact conclusively shows
semicolon-delimited Windows drive-letter/backslash paths, including both
short and long parent names. Git Bash uses a colon-delimited shell PATH and
converts it for native programs; Alire/native shells can expose native lists.
The previous `tr ':'` and POSIX case patterns cannot safely handle a native
list, drive letters, backslashes, case differences or 8.3 parent aliases.

The new handwritten, validation-only Python helper:

- Accepts native semicolon lists and shell colon lists; preserves drive-letter
  colons during parsing, including mixed shell/native entries.
- Uses `cygpath -aml` on Windows to obtain absolute, mixed-separator long
  names **before** candidate and source-consumer directories are hidden.
  Case-folded normalized comparisons enforce directory-component boundaries.
- Removes candidate, source-consumer dependency cache, repository source and
  prefix-A entries, including exact roots. Drops implicit cwd/empty entries.
- Retains inherited independent toolchain/system entries in order and emits
  absolute shell paths through `cygpath -u`, without a hardcoded toolchain list.
- Reports only capture/output format classifications, not the runner PATH.

Supported cygpath conversion options are documented at
<https://cygwin.com/cygwin-ug-net/cygpath.html> (`-a`, `-m`, `-l`, `-u`).
No guessed expansion of `RUNNER~1` exists in production code; the deterministic
test adapter models one explicit alias, while native qualification must verify
the actual conversion. Conversion errors fail qualification.

The sanitized base PATH excludes prefix A in both modes. Existing execution
logic explicitly adds each current prefix's runtime directories plus the
selected independent MSYS2 native runtime on Windows. The original sources
remain physically hidden and A is physically removed before the fresh B build.
No auditor, captured diagnostic line, workflow trigger or failure-only upload
was changed. No Core/pin/version, production Ada/C++, ABI or algorithm changed.

## Local qualification

Linux: OpenCV 4.10.0, g++ 14.2.0, Alire 2.1.1, GNAT 16.1.0,
GPRbuild 26.0.0 (Alire package selection retained).

- Repository checks; **76/76 configuration tests**, retaining all existing 61
  and adding 15 value-based parsing/filtering/CLI/audit regressions.
- Fixed-profile/layout helpers, every shell script's syntax, whitespace checks.
- Native AUnit **67 executed / 67 passed**, zero failed assertions.
- Six external-shim GPRinstall and two installed-link metadata regressions.
- Production and fault-injection boundaries with real Core handles; full
  ASan/UBSan run passed, including radius fault-stage exception categories.
- Both examples built and executed successfully.
- Source-pinned, installed-A and fresh relocated-B consumers passed.
  A removal and source hiding verified physically; strict installed project,
  source, linker and final metadata/resolution audits passed unchanged.
- Final helper/script version was rerun through all repository/configuration
  checks and a fresh three-mode consumer qualification. Retained Linux PATH
  includes selected GNAT (two entries) and GPRbuild (one); zero original
  candidate/source-consumer entries. Actual installed builds and GPRls passed.

Local logs and native evidence remain outside committed source. Windows
fixtures are **not** native Windows certification. Actual Windows retained
GNAT/GPRbuild/MSYS2 behavior and capture-format classification remain pending
the reviewed merge's post-merge run, which must pass the **full final audit**.
Exact-head hosted CI and final commit/PR identity are recorded in the review
handoff rather than inferred from these local results.

Disposition: `REVIEW_GATE_READY / WINDOWS_POST_MERGE_PENDING` after required
exact-head hosted checks pass. No merge, auto-merge, Windows dispatch, release
or Core unpinning is authorized by this record.