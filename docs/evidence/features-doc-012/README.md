# FEATURES-DOC-012 — migrate to ada-gnatdoc-enhancer v0.1.5

## Identity

- Base: `main` `7909c62d4a4a08b972de1da4b7a59ff02f01f1e8`, tree
  `1dd3fa20ed7786720c9f0d22d933d46fc788dd68` (freshly fetched; equal to the
  last observed main).
- Branch: `docs/features-gnatdoc-enhancer-015`. The PR records the final head
  and tree, because a commit cannot contain its own SHA. The hosted
  `qualification-head.json` records the identity that CI actually ran.
- Release: [v0.1.5](https://github.com/zackboll/ada-gnatdoc-enhancer/releases/tag/v0.1.5).
  Tag object `c6ca2b445b089e7f50abc1779d76dd4ff3f0f1eb` (annotated, unsigned).
  It peels to commit `0120bee2f2455e4c832d1d5ddae0a4cb03cb9477` and tree
  `01900ddb099c801eeb92fba718f4c528f87d865f`.

## Release verification (`acquisition.json`, `release-install.txt`)

All four official downloads match the expected SHA-256 values:

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| Wheel | 117934 | `d712d330f213fc1909a66c47bc2c7e5e15d5ec687222bea3c4922f5243db4247` |
| Source distribution | 3521158 | `2bc2cc4160a182a2a9b1a4907f47198daabf88883888fa09d736913bd2931079` |
| Release provenance | 1157963 | `6c30b7a4ec987ab4f74a44d04586dcd57308dd592ac13f33c9444ef3acf0a8f3` |
| `SHA256SUMS` | 300 | `93e061866d52e13b6266c6fa0efb3b9c2e3a1bd1b4c818981a11a802ded74756` |

`SHA256SUMS` lists exactly the other three. The wheel has 48 members, and each
digest and size equals the release provenance. All 47 `RECORD` entries verify
(digest and size). All 42 package modules and assets equal the v0.1.5 tagged
Git blobs. The metadata reports `ada-gnatdoc-enhancer 0.1.5`, with only the two
optional `guides` requirements. After a non-editable `--no-index --no-deps`
install into a new virtual environment, the module `__version__`, distribution
metadata and `gnatdoc-enhancer --version` all report `0.1.5`. The renderers
(`markdown-it-py==3.0.0`, `mdurl==0.1.2`) are unchanged and hash-pinned.

The release provenance records `publication_authorized: false` and
`qualification.status: FINAL_ARTIFACTS_QUALIFIED`. Features does not treat that
document as an authority. Its approval is the Features-owned
`docs/gnatdoc-enhancer-release.json`, cross-checked as described above.

## Native baseline (before and after)

Both runs used GNAT 16.1.0, GPRbuild 26.0.0 (Alire `gprbuild=26.0.1`),
GNATdoc 26.0.0 (20260415), Alire 2.1.1, indexed `opencv_core=0.5.2` and
system OpenCV 4.6.0 for Core configuration only. Nothing was compiled or linked.

| Gate | Main (v0.1.0) | This branch (v0.1.5) |
| --- | --- | --- |
| Public packages / internal units excluded | 4 / 2 | 4 / 2 |
| Native declaration sections | 38 | 38 |
| Documented elements | 127 / 127 | 127 / 127 |
| GNATdoc warnings / coverage gaps | 0 / 0 | 0 / 0 |
| Native site bytes | `native-api.sha256` | identical (`diff -r`) |
| Second clean generation and log | identical | identical (`native-second.txt`) |

## Enhanced site (before and after)

The v0.1.0 baseline was regenerated freshly from main with the unmodified
v0.1.0 integration. It is byte-identical to the DOC-011 hosted evidence
(`../features-doc-011/enhancement.json`). The live Pages host was not reachable
from the qualification environment, so the published bytes were not compared
directly.

| Measure | v0.1.0 | v0.1.5 |
| --- | --- | --- |
| Files / HTML pages / added files | 18 / 13 / 12 | 18 / 13 / 12 |
| Links / local type links / external | 248 / 47 / 0 | 248 / 47 / 0 |
| Pages references / routes / titled pages | 248 / 13 / 13 | 248 / 13 / 13 |
| Byte-identical files | — | 15 of 18 |

`output-comparison.json` lists every file. Only `api/gnatdoc-navigation.js`,
`api/index.html` (filter label text) and `api/presentation.json` (version and
two output digests) changed. `enhancement.json` records the four enhancer
operations, dry-run immutability, byte-idempotent re-enhancement, an identical
fresh enhancement, the independent native comparison, site-wide link
resolution and an unchanged pristine site.

## Tests

- `full-tests.txt`: 106 documentation tests against the real enhanced site and
  v0.1.5 environment. OK, with 2 skipped (those two run in `end-to-end-tests.txt`).
  These include the installed-module, asset, launcher, renderer, receipt and
  version tampering cases, the 23 enhanced-site mutations, extra and missing
  files, the non-idempotent and non-deterministic driver cases, and the
  transition comparison with four drift mutations.
- `end-to-end-tests.txt`: `FEATURES_DOCS_END_TO_END=1` strict regeneration. OK.
- New unit cases: new-schema provenance tampering (13 cases), `SHA256SUMS`
  tampering (5), wheel `RECORD` tampering (5), rejection of the superseded
  v0.1.0 revision and of `0.1.0` and `0.1.6.dev0` installed versions.
- `preflight.json`: the optional preflight passes against v0.1.5 with 0 failures.

## Chromium (Chromium 153.0.8010.12, Playwright 1.63.0, Node 22)

The local runtime was the preinstalled Playwright, not CI's 1.64.1. The hosted
run uses 1.64.1.

| Campaign | v0.1.0 | v0.1.5 |
| --- | --- | --- |
| Enhanced site, root (`browser.json`) | 70/71 (fails only the new label assertion) | 71/71 |
| Pages project prefix (`pages-browser.json`) | — | 199/199 |
| Enhanced site under prefix (`prefix-browser.json`) | — | 71/71 |

Seven assertions were added for the new navigation behavior: the filter label,
a direct `?declaration=` bookmark, Back and Forward around a declaration, reload,
the tagged-type sidebar link and console errors. In each case the Detector
declaration is revealed inside the frame after a 4565px scroll. The original 64
assertions are unchanged.

`presentation-layout.json` compares body, main, navigation, iframe, heading,
label and search-box geometry, and page overflow, for the portal home, the ORB
guide and the API index (desktop and 390px, light and dark). All 12
combinations have identical layout. Screenshots are pixel-identical except for
the label text on the API index (`label-change.png`, top: v0.1.0, bottom:
v0.1.5).

## Pages

`pages.json`: 18 files, 13 pages, 248 references and 13 routes resolve under
`https://zackboll.github.io/opencv_features_ada/`; the site is publication-ready.
`pages-archive-local.json` covers a locally built tar only. The hosted workflow
verifies the actual upload, downloaded by immutable artifact ID.

## Not verified locally

- Hosted exact-head documentation run and the actual uploaded Pages artifact
  (bound in the PR).
- Linux, macOS, sanitizer and Windows jobs. This change touches no production
  file. `scripts/check_doc_source_integrity.py` records that.
