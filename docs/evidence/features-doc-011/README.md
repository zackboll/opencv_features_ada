# FEATURES-DOC-011 — released enhancer adoption

## Identity and disposition

- Starting/freshly fetched main: `71eb93f45b3ee833d4cb2b96a10095aaf0541acd`;
  tree `5ad7cef0eb808bc57828509f66aeabeb712c8bc3`.
- Review branch: `docs/011-adopt-enhancer-v0.1.0`, separate clean worktree.
- Official release: [v0.1.0](https://github.com/zackboll/ada-gnatdoc-enhancer/releases/tag/v0.1.0).
- Annotated unsigned tag object: `14463739818eb4c78b93ad42ecc4a4077cbec2bc`.
- Peeled source: `4ee95e8c95b8c7f54397a07e3e1c507783c115aa`;
  tree `c5cff2cff52e595f71202bf97c513b7e0f46c918`; version `0.1.0`.
- Wheel SHA-256: `b0949aba6736515bf2ebe14fc7cc30c816a176257fc4524564285397b8aaf97d`.
- Sdist SHA-256: `b5114c9d186dc6d230f1d48c139739b32e83a037d7fe7e7516c46755916e854a`.
- Release provenance SHA-256: `7d08f56d7566416009bcd0595ecaa186cc7701e1aa1c5e9d8349d6e601c1a269`.
- Disposition at evidence creation: **HOSTED_CI_PENDING**. Local gates pass;
  exact-final-head hosted documentation qualification and actual uploaded artifact
  verification are still required. Final commit/tree, run URL, downloaded artifact
  identities and disposition are bound in the review PR's qualification comment.
  Embedding a commit's own SHA in itself is not possible; the hosted runtime
  `qualification-head.json` records that exact identity independently.

No Ada source, GPR/ABI, library behavior, Alire manifest, consumer repository,
upstream enhancer, deployment permission or Pages environment changes are made.
No rebase, force-push, amend, auto-merge, merge or feature-branch publication.

## Fresh qualification and reused inputs

Freshly reproduced: all three official HTTPS downloads with redirect host policy;
all archive digests; GitHub API tag/commit/tree inspection and separate Git fetch;
41 wheel-member hashes against the approved provenance; all 35 package member
hashes against immutable tagged Git blobs; new isolated old-development and
release installations; two independent native generations; both full enhanced
outputs; strict checks; security mutations; three Chromium campaigns; local Pages
tar identity and environment policy readback. `acquisition.json` retains the exact
tag annotation, archive and member identities. Sdist was verified but not installed.

Reused inputs, not reused passing results: unchanged Features-owned native anchor,
source declaration, warning and coverage oracles and DOC-004–010 historical records;
the old enhancer Git object was read from an existing object database but exported
by exact `23cf51d3765e7b3f68411e25a57f52f4c0efc7e1` and freshly installed;
existing GNATdoc 26.0.0 installation and selected Alire toolchain were version-checked;
indexed Core 0.5.0 was freshly resolved without pins; existing Playwright 1.64.1 /
Chromium 156.0.8078.4 executables were version-checked and all campaigns freshly run.
No historical enhanced site or old development presentation manifest was reused.

## Native source authority and compatibility

`native-qualification.json`, `native-first.txt`, `native-second.txt`, `inventory.json`,
`coverage.json` and `warnings.json` record:

| Gate | Result |
| --- | --- |
| Explicit public specs / packages | 4 / 4; internal units excluded |
| Source/native declarations | 38 / 38 |
| Documented API elements | 127 / 127 |
| GNATdoc warnings | 0; both exception baselines empty |
| Native generations | Two separate clean outputs and logs byte-identical |
| Staged source | Exact four pristine source-file byte hashes |
| Native CSS / original anchors / type identities | Unchanged |
| Toolchain | GNAT 16.1.0, GPRBUILD 26.0.0 (Alire 26.0.1), GNATdoc 26.0.0 |
| Dependency | Indexed Core 0.5.0; no local pin |

The normal semantic-only GPRbuild gate passes before GNATdoc. No library compile
or algorithm testing is claimed for this documentation-only upgrade. Features-owned
strict coverage/warning ratchets remain authoritative; enhancer coverage is not a
replacement.

`output-comparison.json` classifies every file by both SHA-256 values. **17 files
are byte-identical**, including every HTML page, guide, stylesheet and JavaScript.
Only `api/presentation.json` changes, and its only change is the exact string
`enhancer_version: 0.1.0.dev0` → `0.1.0`. The fail-closed comparison script requires
this transition and rejects HTML, manifest or inventory drift. Both independent
censuses have 13 pages, 18 files and **248 resolved references**. Seven guides,
four packages, original anchors, local type links and zero external URLs/type links
are preserved. No semantic difference was found; no oracle was replaced or relaxed.
`enhancement.json` records fresh-run determinism, byte-idempotence and unchanged
pristine input. `preflight.json` also passes all retained conservative compatibility
and mutation checks using a separately downloaded dependency-free release install.

## Installation and security

The approved member inventory is source-owned in `docs/gnatdoc-enhancer-release.json`.
All three default asset digests equal the actual official wheel bytes. The installer
downloads only HTTPS from exact approved hosts, bounds download size, checks full
digests, rejects unexpected/duplicate/nonregular wheel members, checks package
metadata, approved provenance and a fresh annotated tag fetch (Git HTTP redirects
disabled), then installs the wheel `--no-index --no-deps` non-editably. No Git
checkout or source archive is installed. Core installation has no runtime dependency.

`installed-enhancer.json` records source/tag/tree, archive digest, all installed
package/distribution files, launcher and optional renderer files. Every subsequent
invocation rechecks against the source-owned approval inventory, not the mutable
receipt. Distribution and module versions and CLI output must all be `0.1.0`.
Unverified bytecode caches are discarded before package imports; the isolated
launcher disables writing bytecode. Optional renderer requirements and hashes are
unchanged (`markdown-it-py` 3.0.0, `mdurl` 0.1.2).

Negative-first evidence is explicit: `security-red.txt` shows new release assertions
fail against the old implementation's absent gates (not a passing exploit test).
`renderer-negative-first.txt` independently demonstrates the real old weakness:
modified `markdown_it/main.py` was accepted because the old receipt checked versions
only. The new real-install mutation test rejects that same modification, modified
mdurl, Python module, CSS, JavaScript, launcher, installed release provenance,
development module/metadata versions and incorrect receipts. Rewritten same-run
file hashes cannot authorize altered files. Wrong archive digest fails before venv
creation; wrong source/tag/tree/version, redirect hosts, partial/oversized downloads
and unexpected wheel members are tested.

`full-tests.txt`: **104 tests executed, all pass, no skips**, including real native
regeneration mutations. `configuration-tests.txt`: **83 pass**. Existing native
anchors/source-stage/declarations, rendered guides/examples, title/metadata,
navigation, stylesheet, presentation manifest, relative link/fragment, external
URL/script, extra/missing file, non-idempotence, nondeterminism and changed uploaded
archive controls remain. JavaScript authority in `check_pages_site.py` is unchanged.
`security-red.txt` is expected failing preimplementation evidence, not the final run.

## Chromium and Pages

- `browser.json`: 64/64 root-site assertions.
- `pages-browser.json`: 199/199 project-prefix assertions.
- `prefix-browser.json`: 64/64 enhanced-browser assertions under the project prefix.
- Chromium 156.0.8078.4, Playwright 1.64.1, Node v20.19.2; Chromium only, not
  cross-browser or formal accessibility certification.

All existing desktop/mobile 390px, light/dark, search/clear, package bookmarks,
direct URLs, history, fragments/type navigation, JavaScript-disabled links,
keyboard/focus, portal/guide/API, 13 page metadata and prefix/network/error controls
pass unchanged. `pages.json` and `pages-archive.json` pass; local tar has exactly
the qualified 18 files. A synthetic local tar is **not** claimed as hosted upload
evidence. The unchanged hosted upload/download-by-immutable-ID/cmp/checker steps
must succeed on the final head. `pages-environment.json` confirms main-only policy;
no policy was changed. Read-only `native-gnatdoc` and main-push-only `deploy-pages`
remain the only jobs. PR/manual runs must show deployment skipped.

## Coordination and limitations

PR #15 was freshly checked and remains **OPEN**, source-release head
`9c2b4e0377e10e2712c77a9b7cfb62a8fc1a2a2c` (`pr15.json`). Overlap is limited to
`docs/github-pages.md` and `docs/gnatdoc-enhancer-integration.md`; DOC-011 prepends
clearly scoped current guidance and preserves historical evidence. No source-release
changes are duplicated. Both PRs must remain unmerged for coordinated review while
#15 is open; if it merges first, refresh main, reconcile by normal merge, preserve
release intent and rerun affected gates. Main was unchanged at the final local fetch.

Local scratch storage hit the shared `/tmp` inode quota during initial evidence
writes. Only this task's scratch directory was relocated to the home filesystem
and its path preserved by symlink; interrupted steps and the full tests were rerun.
No unrelated task files were removed. One preliminary probe lacked source staging;
it failed before enhancement and was rerun after staging. An initial provenance
comparison omitted its `name` field; this failed closed before environment creation
and was corrected to require the exact published schema. No gate was relaxed.