# Shared GNATdoc enhancer integration (DOC-004 through DOC-010)

## DOC-010 qualification

The integration now adopts merged shared-enhancer PR #10 at immutable revision
`23cf51d3765e7b3f68411e25a57f52f4c0efc7e1`, still `0.1.0.dev0`. This includes
source-verified document metadata, fragment-aware navigation/history and the
reviewed generic-instance theme rules. Features has no public generic instance;
its declarations, anchors, guides, examples and offline type-link policy are
unchanged. [The fresh qualification record](evidence/features-doc-010/README.md)
supersedes current-pin/results statements below; DOC-001–009 evidence remains
historical and is not rewritten.

The complete site has 13 source-identified titles, language `en`, UTF-8 metadata,
18 files and 248 resolved relative references. The pristine native site remains
byte-identical (127/127 documented items, four packages, 38 declaration sections,
zero warnings). RCDATA/title validation and reconstruction by shared `verify`
remain enabled, with additional consumer mutation tests. The original 64 browser
assertions are unchanged; prefix-browser metadata checks are additive.

Only the exact reviewed navigation Git-blob SHA-256 is authorized by the Pages
checker. No general slash-literal or method-call exemption exists. Output-side
manifests and rewritten same-run hashes cannot authorize a different script.
The installer still uses an immutable Git archive, private documentation-only
environment and installed-module/asset Git-blob comparison. The Markdown
renderer pins and distribution hashes are unchanged.

Status: **Pages-qualified implementation, awaiting final evidence-head CI and
independent review**. The implementation run passed including actual uploaded
artifact verification; deployment was skipped. This is not a public deployment; see
[Pages publication](github-pages.md) and the qualification record for hosted status.

DOC-004 adopts the reviewed shared `ada-gnatdoc-enhancer` for a presentation
copy of the native Features API site. It was first qualified on the DOC-001
foundation and has been reconciled with `main` at
`6ab853a52fd2d72dd30924f7d7ec675134a86ade` (DOC-007), which carries the complete
DOC-002/DOC-003 comments and the DOC-006 strict checks. DOC-005 adds the
developer portal and guides to the same presentation copy and was reconciled
with `main` at `c4af75147586fe8cf6d9fab3588be632949769d6` (DOC-008). The native
site, its checks and its empty baselines are unchanged by this integration and
remain the authority; the enhancer is a documentation-only tool, never a
production or Alire dependency.

## Pinned tool and provenance

| Item | Value |
| --- | --- |
| Repository | `https://github.com/zackboll/ada-gnatdoc-enhancer` |
| Revision | `23cf51d3765e7b3f68411e25a57f52f4c0efc7e1` (reviewed merge of PR #10) |
| Version | `0.1.0.dev0` |
| Packaged `gnatdoc-navigation.js` | `b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd` |
| Packaged `gnatdoc-theme.css` | `cf06637732a8b047a7191bfb991a5c3da7cd31a52076876880d5f8a3f63929bc` |
| Packaged `gnatdoc-guides.css` (unchanged) | `79f3fc6d5f1e854eb42d225f9bec113b7a41fa833b12d3bd70ca089ba5df0a8c` |

`scripts/install_gnatdoc_enhancer.py` accepts only that revision (a constant in
`scripts/gnatdoc_enhancer_support.py`), builds it from `git archive` of the
commit, never from a branch or working tree, and proves that all 31 installed
modules and assets equal the commit's Git blobs. It records the installed
hashes; `scripts/enhance_docs.py` re-checks them, the revision and version, and
the packaged assets against `docs/gnatdoc-enhanced-assets.json` before every
run. DOC-010 supersedes the old PR #5 pin and adopts the intervening reviewed
shared changes through merged PR #10. Features has no public generic instance.
DOC-005 uses the Markdown guide mode of the pinned revision. The installer
rejects any other revision.

## Pipeline

```sh
sh scripts/generate_docs.sh                       # native _site + strict Features checks
git clone https://github.com/zackboll/ada-gnatdoc-enhancer.git /tmp/enhancer
python3 scripts/install_gnatdoc_enhancer.py --checkout /tmp/enhancer --venv /tmp/gnatdoc-enhancer --with-guides
python3 scripts/enhance_docs.py --venv /tmp/gnatdoc-enhancer   # writes _site-enhanced
FEATURES_DOCS_API="$PWD/_site/api" FEATURES_DOCS_LOG="$PWD/obj/docs/gnatdoc.log" \
FEATURES_ENHANCED_SITE="$PWD/_site-enhanced" FEATURES_ENHANCER_VENV=/tmp/gnatdoc-enhancer \
  python3 -m unittest discover -s tests/documentation -v
python3 -m http.server 8072 --bind 127.0.0.1 --directory _site-enhanced &
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright DOC_URL=http://127.0.0.1:8072/api/index.html \
  node tests/documentation/test_enhanced_browser.cjs
```

`docs/gnatdoc-enhance.toml` enables the theme, Ada highlighting, package
navigation with search and query bookmarks, and **local** type links. There are
no `external_types`, dependency manifests or allowed external hosts, so no
OpenCV Core URL can be produced; Core type names stay plain text. DOC-005
enables the enhancer's Markdown guide mode (see below).

The enhancer discovers sources recursively; with `directories = ["src"]` it
fails closed because `src/internal` holds non-private internal units
(`public package inventory mismatch: ['opencv.features.internal',
'opencv.features.internal.c_api']`). The driver therefore stages byte-identical
copies of the four `docs_api.gpr` specifications under
`obj/docs/enhancer-sources`, the pattern the enhancer's own real-site
qualification uses. This does not change the enhancer or any production file.

## Verification performed by `enhance_docs.py`

1. The pristine `_site` is copied; only the copy (`_site-enhanced`) is enhanced,
   and the pristine tree hashes are rechecked at the end.
2. Inventory reports exactly the four packages and 38 sections; a dry run leaves
   the copy unchanged; enhance and `verify` pass (47 local type links, 0
   external, on the fully documented sources).
3. Re-enhancing is byte-idempotent; a fresh enhancement of another pristine copy
   is byte-identical.
4. An independent HTML comparison requires unchanged native `h1`/`h4` text and
   ids, all native ids and hrefs, identical declaration code text (so visible
   declarations stay source-backed) and the unchanged native `gnatdoc.css`; all
   local links and fragments resolve; no external URL exists.
5. Within `api/`, the added files are exactly `gnatdoc-navigation.js`,
   `gnatdoc-theme.css` and `presentation.json`, and the two assets equal the
   packaged, inventoried bytes. Site-wide, with the DOC-005 guides, the added
   files and scripts must equal `docs/gnatdoc-enhanced-assets.json`: twelve
   files, and the only script is `gnatdoc-navigation.js` on `api/index.html`.

The Features-owned checks (declaration inventory, anchors, warnings, coverage)
still run on the native site. The enhancer's declaration inventory is not a
substitute for them.

## Tamper rejection

`tests/documentation/test_enhanced_site.py` runs the enhancer's `verify` on
mutated copies of the real enhanced site and staged sources. All are rejected:
native anchor id, native heading, native stylesheet, theme asset, navigation
asset, presentation manifest, injected script, injected external URL, altered
type-link target, changed staged source value, changed staged source comment,
an extra file and a missing asset. Unit tests cover the independent comparison,
staging and the offline profile.

## Chromium qualification

`tests/documentation/test_enhanced_browser.cjs` drives the real enhanced site
over HTTP. Locally, on the complete fully documented site (DOC-008): Chromium
156.0.8078.4, Playwright 1.64.1, Node v20.19.2, **64/64 assertions passed**
([evidence](gnatdoc-browser-qualification.json)). The DOC-005 portal checks are
described below; the other 39 assertions cover the API reference:

- light and dark color schemes at 1280x900: exact four-package index, default
  package frame, `?package=` bookmark via `replaceState`, `aria-current`,
  themed backgrounds (`#fff` / `#141b26`), no page or console errors;
- package navigation pushes a bookmark; Back and Forward restore package and URL;
  direct `?package=` bookmarks open that package, unknown names fall back;
- search filters to the matching package, announces `1 results`, Clear restores
  `5 results`;
- keyboard Tab focus on a link shows a 3px solid outline;
- declaration fragment bookmarks target and scroll to the `h4`; Ada keywords are
  highlighted in both schemes; a type link navigates to the right declaration
  anchor; declaration pages run no scripts;
- 390x844 mobile in both schemes: stacked layout, no horizontal page overflow,
  code snippets scroll internally;
- with JavaScript disabled the search controls stay hidden and native package
  and tagged-type links still work.

This is Chromium only. It is not a cross-browser or complete accessibility
certification (no screen-reader, contrast-audit or zoom testing).

## Continuous integration

The documentation workflow clones the enhancer, installs the pinned revision,
runs `enhance_docs.py`, the mutation tests and the Chromium script (Playwright
1.64.1 with its bundled Chromium), and uploads `_site-enhanced` with the reports.
That job still has `contents: read` only. DOC-009 adds a separate job that
publishes the same `_site-enhanced` to GitHub Pages, from `main` only and once
it meets the publication requirements; see
[GitHub Pages publication](github-pages.md).

## Evidence at this head

[gnatdoc-enhancement-evidence.json](gnatdoc-enhancement-evidence.json) is the
`scripts/enhance_docs.py` report for the complete site, the API reference with
the DOC-005 portal and guides, generated from the sources of `main` `c4af751`
(127/127 documented, 0 GNATdoc warnings). It records the enhancer operations,
the native comparison, the site-wide link check and the hashes of all 18
enhanced files. Enhanced page hashes change whenever documentation comments or
guides change; the checks, not these hashes, are the gate. The hashes can be
checked independently against the `features-api-enhanced-<sha>` artifact that
CI uploads.

## Reconciliation with the fully documented API (DOC-007)

PR #21 was first qualified at `349641978a56da22a3d0cd504a2c71dcb1d6368c`, on the
DOC-001 sources (11/127 documented, 110 warnings). DOC-007 merged `main`
`6ab853a` normally (no rebase). Only `docs/gnatdoc-foundation.md` conflicted:
its gate table keeps both the DOC-004 enhancer rows and the 127/127 row that is
enforced strictly since DOC-006. The workflow merged cleanly and keeps the
strict generation, the `FEATURES_DOCS_END_TO_END=1` test step and the enhancer
steps. No script, test, profile or asset inventory needed a change.

Everything was then remeasured from a fresh native generation; nothing was
carried over from the DOC-001 run:

| Measure | DOC-001 sources (`3496419`) | `main` `6ab853a` sources |
| --- | --- | --- |
| Native coverage / GNATdoc warnings | 11/127 / 110 (ceiling baselines) | 127/127 / 0 (empty baselines, strict) |
| Enhancer inventory | 4 packages, 38 sections | 4 packages, 38 sections |
| Type links (all local) / external | 47 / 0 | 47 / 0 |
| Links reported by the enhancer | 103 | 103 |
| Enhanced-site mutations rejected | 13/13 | 13/13 |
| Chromium assertions | 39/39 | 39/39 |

The link counts are unchanged because the enhancer links type names in the
native declaration code, which DOC-002/DOC-003 did not change; they were
measured again rather than assumed. An independent count over the enhanced
HTML (not the enhancer's report) found 47 `type-reference` links: 37 to a
heading on the same page and 10 to another Features package page (`Features`
11, `ORB` 12, `Matching` 20, `Correspondences` 4). Each one resolves to an `h4`
whose text equals the linked type name, and no link leaves the four Features
pages. Of the 103 references (`href`/`src`, including stylesheets and the
script), 88 carry fragments and all resolve.

Enhanced-site files whose bytes changed with the comments:

| File | DOC-001 sources | `main` `6ab853a` sources |
| --- | --- | --- |
| `api/8aee7d25….html` (`OpenCV.Features`) | `f51630dc3e8018bcc96ff7841e289d20e40440670cdf148774d6d4361606f6b6` | `80651b0ac77b5848aa56f53cfe6419fd75a32f89ed5499dffc5e297ff8e27844` |
| `api/71007168….html` (`OpenCV.Features.ORB`) | `0bbed1ee3d46b70c345365a15ee34e8e8978c54e7ef94f386562f9e1e693a80c` | `bce6ea7d3fdbfbbc8c3a74c09918b363eeef3f6f1b594e4cce183a8954b351e7` |
| `api/f8c4f9ff….html` (`OpenCV.Features.Matching`) | `52797715e3c7b757c82b1da0766b01eab54f9f4ecde21826d45dd216767188ee` | `1dcd90fd69b427fc4a2f0dad8394c3b6d04a33f01a6d88f306ab74d39389b30f` |
| `api/0276ad65….html` (`OpenCV.Features.Correspondences`) | `012aaa628d6b4129e052898498d25a0cab89a5e097e3e86310ae43b028009b4e` | `12d49d3c4eb2e0aed99619ee1e3ec5b2d1cb3065f7cd809af8176b53a549f4cd` |
| `api/presentation.json` | `4cd20816b68e07d6915146c784a40d894da6e3dba2d587efeb9ecdda486ef3c4` | `ba74d5839ef8a8be1167e9de3191eaaaecb7fc6e74cdeb5c2360e5ecf253efc9` |

Unchanged: `api/index.html` (`448e2955…`), the native `api/gnatdoc.css`
(`e86c483e…`) and both packaged assets. The pristine native pages equal the
fingerprints in [gnatdoc-strict-qualification.md](gnatdoc-strict-qualification.md).
The DOC-001 reports remain in Git history
(`3496419:docs/gnatdoc-enhancement-evidence.json` and
`3496419:docs/gnatdoc-browser-qualification.json`). In the browser report only
the `Create` fragment's scroll offset changed (19.25 to 18.875 px).

`scripts/preflight_gnatdoc_enhancer.py` was also rerun against the fully
documented site. It passed with 0 failures: the unstaged layout still fails
closed on `src/internal`; the conservative profile (56 links) and the local
type-link profile (103 links, 47 type links) both passed every check; and all
11 mutations were rejected. Its reviewed DOC-001 record,
[gnatdoc-enhancer-preflight.json](gnatdoc-enhancer-preflight.json), is kept
unchanged as historical evidence.

## Developer portal and guides (DOC-005)

DOC-005 enables `[guides] mode = "markdown"` with
`docs/site-map.json`. The enhancer renders `docs/index.html` (the portal home)
and seven guides from `docs/guides/*.md` into `index.html`, `guides/*.html` and
`assets/gnatdoc-guides.css` beside `api/`. Its supported contract is strict: one
leading H1, no raw HTML or images, fenced code only as `ada`, `sh`, `shell` or
`text`, `api:` links resolved to real native package pages and declaration
anchors (with `/N` for overloads), and an Ada fence only when it is
byte-identical to the guide's recorded example. The ORB and matching guides embed
`examples/src/orb_synthetic.adb` and `examples/src/orb_match_synthetic.adb`,
which production CI builds and runs; no other Ada code appears in the guides.

The renderer is installed with `--with-guides` from
`docs/gnatdoc-guides-requirements.txt`: `markdown-it-py==3.0.0` and
`mdurl==0.1.2`, as wheels with `--require-hashes --no-deps`, using PyPI's
published SHA-256 digests. The provenance record and asset inventory pin those
versions, the guide stylesheet's packaged hash
(`79f3fc6d5f1e854eb42d225f9bec113b7a41fa833b12d3bd70ca089ba5df0a8c`) and the
twelve added files. `enhance_docs.py` additionally resolves every local link and
fragment on all 13 HTML pages and requires that only `api/index.html` loads a
script.

Additional tamper tests reject a changed rendered guide, portal home, guide
stylesheet, guide Markdown source, embedded example source and guide API-link
target. The Chromium script adds portal checks (navigation, package directory,
themes, no scripts, API Reference hand-off, the embedded example, an `api:`
overload link landing on the masked `Detect_And_Compute`, a visible skip link)
and 390x844 layouts of the home page and three guides: **64/64 assertions**
with Chromium 156.0.8078.4 and Playwright 1.64.1. Guide pages generated by the
pinned enhancer have no `<title>` element (the portal home keeps the one in
`docs/index.html`, and the native GNATdoc API pages have none either). That is
an upstream presentation gap, not something Features patches in generated
output; it stays open and should be resolved before the site is published.
DOC-009 makes a `<title>` on every page a deployment requirement
([GitHub Pages publication](github-pages.md#page-titles-current-finding)).

## Reconciliation of the portal and guides with the fully documented API (DOC-008)

PR #22 was first qualified at `363b0d53aebfa15e2141d1f2c09152d04a4724fa`,
stacked on DOC-004 and the DOC-001 sources (11/127 documented, 110 warnings).
DOC-008 merged `main` `c4af751` (after #21) normally, without rebase. Two files
conflicted: this record, which keeps both the DOC-007 and the DOC-005 sections,
and the generated `gnatdoc-enhancement-evidence.json`, which was replaced by the
report of a fresh generation of the merged tree instead of either side. The
workflow merged cleanly: it keeps the strict generation, the
`FEATURES_DOCS_END_TO_END=1` step and the regeneration, and installs the
enhancer `--with-guides`. `main` had not changed any DOC-004 script, test,
profile or inventory since DOC-005 was written, so DOC-005's versions apply
unchanged. `src/`, the empty baselines, the strict generator and checker, the
manifests and the 14 strict-qualification tests are identical to `main`.

Everything was remeasured from a fresh native generation:

| Measure | DOC-005 on DOC-001 sources (`363b0d5`) | `main` `c4af751` sources |
| --- | --- | --- |
| Native coverage / GNATdoc warnings | 11/127 / 110 | 127/127 / 0 (strict, empty baselines) |
| HTML pages / enhanced files / added files | 13 / 18 / 12 | 13 / 18 / 12 |
| Links reported by the enhancer / local type links / external | 248 / 47 / 0 | 248 / 47 / 0 |
| Site link errors (`enhance_docs.py`) | 0 | 0 |
| Chromium assertions | 64/64 | 64/64 |

An independent census of the 13 pages, separate from the enhancer and the
Features scripts, found 248 references, 131 of them with fragments, all
resolving inside the site, and no URL of any scheme. The 47 `type-reference`
links (37 same-page, 10 cross-page) each land on an `h4` with the type's name.
Of 58 portal and guide links into `api/`, 35 target declaration anchors listed
in `gnatdoc-native-anchors.json` (each landing on the `h4` that names the
declaration), 14 target package pages and 9 the API index; together they reach
32 distinct packages and declarations. The portal links all seven guides, the
API index and all four package pages. `site-map.json`, `docs/guides/*.md` and
the rendered `guides/*.html` are the same seven guides, and there are no other
pages. The ORB guide's `masked overload` link targets anchor `07eb80b5…`, the
`Image, Mask` overload of `Detect_And_Compute`. The rendered Ada blocks of the
ORB and matching guides equal `examples/src/orb_synthetic.adb` and
`examples/src/orb_match_synthetic.adb`, and each guide's Markdown fence is
byte-identical to its source.

Only the four API pages and `api/presentation.json` changed. The API pages have
the `main` values in the DOC-007 table above. `presentation.json` is
`be824a6340d53ff9309955450c2c92444186c9bd957eb5b88e0d0db153fd67a8`
(`dd136e25…` on the DOC-001 sources; it differs from DOC-007's value because it
records the guides). The portal home, the seven guide pages, the guide
stylesheet and the packaged assets are byte-identical to DOC-005's. Guides
render from their Markdown and examples, and their `api:` links resolve to
native anchors, which the comments did not change.

Re-enhancement was byte-idempotent and a fresh run identical. Enhancing an
independently regenerated native site produced a byte-identical enhanced site
and report. The pristine `_site` was unchanged, and its pages equal the
fingerprints in [gnatdoc-strict-qualification.md](gnatdoc-strict-qualification.md).
The enhancer's `verify` rejected all 17 mutations of `test_enhanced_site.py`
and the extra-file and missing-file cases, each with a specific reason: for
example, `Ada code fence differs from its authoritative example source` for the
example source, and `published file differs from reconstructed output` for a
guide API-link target. The renderer wheels, downloaded again with
`--require-hashes`, have the pinned SHA-256 digests. Every installed module of
`markdown-it-py` 3.0.0 (68 files) and `mdurl` 0.1.2 (7 files) equals its wheel
member.

Against DOC-005's browser report, the assertions and their outcomes are the
same. Only the `Create` fragment's scroll offset changed (19.25 to 18.875 px in
both schemes), as in DOC-007. DOC-005's report had its top-level `url`
normalized to `PORT`; the committed report is now the script's unedited
output. The DOC-005 reports remain in Git history
(`363b0d5:docs/gnatdoc-enhancement-evidence.json` and
`363b0d5:docs/gnatdoc-browser-qualification.json`).
