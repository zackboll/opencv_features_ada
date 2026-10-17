# Shared GNATdoc enhancer integration (DOC-004)

DOC-004 adopts the reviewed shared `ada-gnatdoc-enhancer` for a presentation
copy of the native Features API site. It is stacked on the DOC-001 foundation
(`docs/001-gnatdoc-foundation`). The native site, its checks and baselines are
unchanged and remain the authority; the enhancer is a documentation-only tool,
never a production or Alire dependency.

## Pinned tool and provenance

| Item | Value |
| --- | --- |
| Repository | `https://github.com/zackboll/ada-gnatdoc-enhancer` |
| Revision | `478d0bbff0be1b9141b5ad39f07a71f0386d86e9` (reviewed merge of PR #5) |
| Version | `0.1.0.dev0` |
| Packaged `gnatdoc-navigation.js` | `61eac070e65b38ac63242a54ed0546a8f4a27b25d8958c2824557860623f40b2` |
| Packaged `gnatdoc-theme.css` | `63c1e9c9a6f2e17cbf64287592dcad5d68f2de9064408bd9963b81ae99d17371` |

`scripts/install_gnatdoc_enhancer.py` accepts only that revision (a constant in
`scripts/gnatdoc_enhancer_support.py`), builds it from `git archive` of the
commit, never from a branch or working tree, and proves that all 26 installed
modules and assets equal the commit's Git blobs. It records the installed
hashes; `scripts/enhance_docs.py` re-checks them, the revision and version, and
the packaged assets against `docs/gnatdoc-enhanced-assets.json` before every
run. Enhancer `main` later merged PR #6 (`4c75e86`, generic-instance
summaries); it is not adopted because it has not been authorized for this
campaign, and Features has no public generic instance.

## Pipeline

```sh
sh scripts/generate_docs.sh                       # native _site + Features checks
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
   external).
3. Re-enhancing is byte-idempotent; a fresh enhancement of another pristine copy
   is byte-identical.
4. An independent HTML comparison requires unchanged native `h1`/`h4` text and
   ids, all native ids and hrefs, identical declaration code text (so visible
   declarations stay source-backed) and the unchanged native `gnatdoc.css`; all
   local links and fragments resolve; no external URL exists.
5. Added files are exactly `gnatdoc-navigation.js`, `gnatdoc-theme.css` and
   `presentation.json`; the two assets equal the packaged, inventoried bytes; the
   only script is `gnatdoc-navigation.js` on `index.html`.

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
over HTTP. Locally: Chromium 156.0.8078.4, Playwright 1.64.1, Node v20.19.2,
**39/39 assertions passed** ([evidence](gnatdoc-browser-qualification.json)):

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
It still has `contents: read` only and does not deploy GitHub Pages.

## Evidence at this head

[gnatdoc-enhancement-evidence.json](gnatdoc-enhancement-evidence.json) records
the enhancer operations, comparison and enhanced file hashes for the DOC-001
sources. Enhanced page hashes change whenever documentation comments change;
the checks, not these hashes, are the gate.

## Developer portal and guides (DOC-005)

DOC-005, stacked on this integration, enables `[guides] mode = "markdown"` with
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
enhancer have no `<title>` element; that is an upstream presentation gap, not
something Features patches in generated output.
