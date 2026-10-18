# GNATdoc foundation (DOC-001)

This record establishes a reproducible, Features-owned GNATdoc pipeline for the
four public packages `OpenCV.Features`, `OpenCV.Features.ORB`,
`OpenCV.Features.Matching` and `OpenCV.Features.Correspondences`. It changes no
Ada source, build project, native shim, test, example or production workflow.
Initial measurements are in [gnatdoc-initial-inventory.md](gnatdoc-initial-inventory.md).

## Gates

| Gate | Status |
| --- | --- |
| Native GNATdoc 26.0.0 HTML for exactly the four public packages | established |
| Ada 2022 semantic analysis of the documented specifications (`-gnatc`) | established |
| Source-backed public declaration inventory (API freeze for doc changes) | established |
| Observed native anchor manifest, link/fragment and file-inventory validation | established |
| Line-independent warning baseline with region classification | established |
| Rendered-versus-documented coverage report with an exact gap baseline (empty, strict since DOC-006) | established |
| Deterministic regeneration in separate clean directories | established locally; CI job added |
| Documentation-only source-integrity check (`docs/*` branches) | established |
| Shared enhancer compatibility preflight (optional, offline) | passes with staged public specifications |
| Shared enhancer presentation copy, tamper and Chromium checks | established by DOC-004; see [integration](gnatdoc-enhancer-integration.md) |
| Complete public documentation | established by DOC-002/DOC-003: 127/127; enforced strictly since DOC-006 |
| Hosted CI for this workflow | pending until the PR runs; not claimed here |

## Toolchain and provenance

| Component | Identity |
| --- | --- |
| Alire | `alr 2.1.1` |
| Compiler | `gnat_native=16.1.0` (`GNAT 16.1.0`) |
| Project tools | `gprbuild=26.0.1` (`GPRBUILD 26.0.0 (2026-04-15)`) |
| Documentation generator | `gnatdoc_bin=26.0.0` (`GNATdoc 26.0.0 (20260415)`) |
| Native GNATdoc stylesheet | `gnatdoc.css` SHA-256 `e86c483e8a66f80bd653129c7ceeec99e63848ecfc308e98ea9de1693fd32e0e`, byte-identical to `share/gnatdoc/html/static/gnatdoc.css` in the release |
| Core dependency | indexed `opencv_core=0.5.0`, origin `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` (community index `stable-1.4.0`), resolved from `opencv_core ~0.5.0` with no pin |
| Native OpenCV for Core configuration | Debian `libopencv-dev` 4.10.0 locally; Ubuntu 24.04 package in CI |
| Python | 3.13.5 locally (standard library only) |

`generate_docs.sh` refuses any other GNATdoc, GNAT or GPRbuild version. GNATdoc's
`--version` exits with status 1, so its output is compared instead.

## Reproducible commands

```sh
# One-time: resolve the indexed Core release and generate crate configuration.
# Runs only Alire's generation and pre-build (configure) stages; nothing is compiled.
alr -n build --stop-after=pre-build
alr -n install --prefix="$HOME/.local/gnatdoc-26.0.0" gnatdoc_bin=26.0.0   # or an existing install
export GNATDOC_PREFIX="$HOME/.local/gnatdoc-26.0.0"

sh scripts/generate_docs.sh                    # writes _site/api and obj/docs/*.json
python3 -m unittest discover -s tests/documentation -v
FEATURES_DOCS_API="$PWD/_site/api" FEATURES_DOCS_LOG="$PWD/obj/docs/gnatdoc.log" \
  python3 -m unittest discover -s tests/documentation -v
cp obj/docs/gnatdoc.log /tmp/gnatdoc-first.log
sh scripts/generate_docs.sh /tmp/features-docs-second   # must not already exist
diff -r _site /tmp/features-docs-second && cmp /tmp/gnatdoc-first.log obj/docs/gnatdoc.log
python3 scripts/check_gnatdoc.py markdown      # coverage and warning tables
python3 scripts/check_doc_source_integrity.py "$(git merge-base origin/main HEAD)" HEAD
```

`generate_docs.sh` checks tool versions, compiles the four specifications with
`-gnatc` under the crate's own `Ada_Compiler_Switches` (which carry `-gnat2022`
from `alire.toml`), runs GNATdoc with `--backend html --generate public --style
leading --warnings`, rejects error/fatal/ignored-file diagnostics, and runs
`scripts/check_gnatdoc.py all`. It only deletes the task-owned `_site`; any other
output directory must be new.

## Documentation project

`docs_api.gpr` never imports `opencv_features.gpr`. It lists the four public
specifications explicitly, `with`s the indexed `opencv_core.gpr` and the
generated `config/opencv_features_config.gpr` for name resolution and switches,
and excludes those project files (and Core's shim, configuration and install
projects) from publication. The public specifications reference only Ada
runtime units and Core, so no internal unit is visible to GNATdoc: neither
`OpenCV.Features.Internal` nor the 17-entry `OpenCV.Features.Internal.C_API`
can be published. Core's pre-build configuration is required because
`opencv_core.gpr` imports its generated `config/opencv_core_install.gpr`.

## Observed GNATdoc 26.0.0 leading-style attachment

Isolated experiments (not committed) established the rules the source model
reproduces. They are also authoring rules for DOC-002 and DOC-003:

1. A declaration owns the contiguous comment-only lines directly above it.
   A blank line breaks attachment; comments after a declaration are ignored.
2. The first comment block after `package X is` is the package description
   when it starts on the next line (then it is **also** the leading comment of
   an adjacent first declaration) or when a blank line follows it, even if a
   block above `package` exists. Only when the first block after `is` is a
   declaration's own leading block is the nearest block above the `package`
   keyword used; that block may be separated from `package` by blank lines,
   but not by code such as a context clause. Recommended layout: SPDX line
   first in the file, then context clauses, the package description directly
   above `package`, and a blank line after `is` with no floating comment
   block before the first declaration. (Found while measuring DOC-002: a
   separated SPDX block after `is` became the package description.)
3. `@param`, `@return`, `@field`, `@enum` and `@exception` tags render into the
   Parameters, Return Value, Record fields, Enumeration Literal and Raised
   exceptions groups. Never put comments inside a declaration: the native
   snippet prints declaration text and the anchor manifest checks it.
4. Native page names and `h4` anchors are stable when comment lines are added
   or moved (verified by inserting lines before a declaration), and do not depend
   on the checkout path (verified by regenerating from another directory).

## Inventory, anchors and site validation

- `scripts/gnatdoc_source.py` is a real Ada lexer (comments, string and
  character literals, attributes, compound delimiters) and a fail-closed parser
  for the visible declaration forms used by this API. Objects, exceptions,
  aspects, renamings, generics, discriminants, derived types, pragmas and
  nested packages in a visible part are rejected rather than skipped.
- `docs/gnatdoc-declarations.json` is the source-backed public inventory: 4
  packages, 38 declarations, every parameter (mode, subtype, default), result,
  record component (default) and literal, and mechanical ownership sensitivity
  (profile uses `Feature_Set`, `Detector` or `OpenCV.Core.Mat`). It contains no
  line numbers or comments, so documentation edits keep it exact; any
  declaration change fails `check_gnatdoc.py inventory`.
- `docs/gnatdoc-native-anchors.json` records the observed page for each package
  and `(page, anchor)` for each declaration identity, the tagged-type index and
  the native stylesheet hash. Each source declaration must match exactly one
  native `h4` section by name and token-identical rendered signature, and every
  native section must match a declaration. No anchor is computed or guessed.
- `scripts/gnatdoc_native.py` accepts only the observed native tag set, so a
  script, iframe in a page, comment or unknown element fails. The validator
  also requires the exact file inventory, the four packages and no internal or
  Core unit, resolved local links and fragments, no external URL, consistent
  entity tables, unique ids and the unchanged native stylesheet.

## Coverage model

Elements are package descriptions (4), declaration descriptions (38),
parameters (33), function results (20), record components (23) and enumeration
literals (9): **127**. An element is *rendered* when GNATdoc emits its section,
member entry or description slot; all 127 are rendered. It is *documented* only
when all of these hold:

- the rendered prose equals (after whitespace normalization) the source block
  or `@tag` text that the attachment model assigns to that exact element;
- the block is not shared by the package description and a declaration;
- it has at least three words (descriptions) or two words (members) after
  removing an SPDX identifier.

This is a mechanical attachment and floor check, not a semantic-quality claim.
Rendered prose that does not match, prose without a source block, duplicate
tags and mismatched `@exception` groups are reported with reasons. Native member
groups must equal the source members exactly.

## Baseline policy

The warning and coverage baselines hold stable, line-free identities. A new
warning or gap always fails; a resolved entry is reported as *stale* and fails
with `--strict`. During DOC-002 and DOC-003 the baselines were ceilings, because
those independent comment-only PRs could not edit these files. Since DOC-006
both baselines are **empty** and `scripts/generate_docs.sh` runs the checker
with `--strict`, so any undocumented public element, any GNATdoc warning and
any baseline entry fail (see [strict qualification](gnatdoc-strict-qualification.md)).
`--capture` writes a baseline only when the file is absent; it never
overwrites. The declaration inventory and anchor manifest are exact.

Warnings at DOC-001: 110 raw, 108 public and 2 private-part (`ORB.Finalize`);
since DOC-002/DOC-003: 0. The log's diagnostics must all be
`file:line:column: warning:` lines in the four specifications; anything else
fails as unclassified.

## Determinism and fingerprints

Two generations into separate new directories, and the default `_site`, were
byte-identical, as were their GNATdoc logs. A generation from a second copy of
the repository at another absolute path was also identical.

| File | SHA-256 |
| --- | --- |
| `src/opencv-features.ads` | `3099d8b54449d6c9f221daf6cb09df6b7e0218c47d8c601a6c4a12b54c5daf35` |
| `src/opencv-features-orb.ads` | `2594efc86b73703ab2c918888eb12deb9ac640b04efaa9d3ba13cbd3c1c7b278` |
| `src/opencv-features-matching.ads` | `9c1d642de6f6a923bad1636dcb86f1b8a704767d88087d203f9dc6fda6f73a38` |
| `src/opencv-features-correspondences.ads` | `22bf36747bc06267d16136fb18e78353db720f7ada6f5713e3f976471ec4541f` |
| `docs_api.gpr` | `81939e31948827719f96c32a93af8c6046e87f808e5bd88feb373530a04af8a6` |
| `api/index.html` | `0d4a79efbedd84ceb9107baec943875d34557a2b07d546a3e460a70d1fd83986` |
| `api/8aee7d25….html` (`OpenCV.Features`) | `5f10ce396a7d5b022e35a640001c1d8df392402d18ceb3d6aff527d49049cd06` |
| `api/71007168….html` (`OpenCV.Features.ORB`) | `c5e67db83e845f3774c304fa58ad1e47ad661bf5247cbc25d37d107813fd8b82` |
| `api/f8c4f9ff….html` (`OpenCV.Features.Matching`) | `c205628fec06c1efe02b7804005de8bf57b92f42741da8e51da34e61fa50486c` |
| `api/0276ad65….html` (`OpenCV.Features.Correspondences`) | `41fd7be7ccbb7f7261b0d88893fc9f342ff9d414da6b5f8e8df3bef90378a2d7` |
| `api/gnatdoc.css` | `e86c483e8a66f80bd653129c7ceeec99e63848ecfc308e98ea9de1693fd32e0e` |
| `obj/docs/gnatdoc.log` | `f4885e7efc725aac339ad1c848ee51f593198fa953699794768df425b6bfb9bb` |

## Source integrity

`scripts/check_doc_source_integrity.py BASE HEAD` compares committed trees. Ada
and GPR files must have identical non-comment token streams (real lexer, so a
`--` inside a string literal is code); every other existing file must be
byte-identical; deletions and additions outside an allowlist written in the
checker are rejected. Fixtures use temporary Git repositories. The workflow
runs it from the merge base for pull requests from `docs/*` branches only,
because ordinary production PRs legitimately change code. Token equality is
necessary but not sufficient; specification edits must still build and pass the
native test suite in the production workflow.

## Continuous integration

`.github/workflows/documentation.yml` is separate from the production
workflows (whose topology checker is unchanged). On Ubuntu 24.04 it installs
native OpenCV for Core configuration, Alire 2.1.1, the qualified toolchain and
GNATdoc 26.0.0, runs the tooling unit tests, generates and checks the site, runs
the mutation tests against it, regenerates into a separate directory with
`diff -r` and log comparison, runs source integrity on `docs/*` PRs, writes the
coverage/warning tables to the step summary and uploads the site and reports as
artifacts. It has `contents: read` only and does **not** deploy GitHub Pages.

## Shared enhancer compatibility preflight

`scripts/preflight_gnatdoc_enhancer.py` is optional and offline with respect to
Features: it is not a build or generation dependency. Evidence:
[gnatdoc-enhancer-preflight.json](gnatdoc-enhancer-preflight.json), recorded on
the DOC-001 sources; its page hashes are those of that site. It was rerun with
the same outcome on the fully documented sources (see the
[enhancer integration](gnatdoc-enhancer-integration.md#reconciliation-with-the-fully-documented-api-doc-007)).

- Pinned revision `478d0bbff0be1b9141b5ad39f07a71f0386d86e9` (reviewed merge of
  enhancer PR #5) was exported with `git archive` and installed non-editably in
  a private virtual environment; all 26 installed modules and assets equal the
  reviewed Git blobs. `gnatdoc-enhancer --version` reports `0.1.0.dev0`.
- **Exact finding:** with the real repository layout (`directories = ["src"]`)
  the enhancer fails closed: `public package inventory mismatch:
  ['opencv.features.internal', 'opencv.features.internal.c_api']`. Its source
  discovery is recursive and treats the non-private internal units in
  `src/internal` as public. This is a layout incompatibility, not an unsupported
  Features declaration.
- As in the enhancer's own real-site qualification, byte-identical copies of the
  four specifications listed in `docs_api.gpr` were staged under
  `qualification-public/src`. With the conservative profile (theme, Ada
  highlighting, local package navigation; type links, external Core links,
  generic-instance augmentation and guides disabled): inventory found 4
  packages and 38 sections; dry-run left the site unchanged; enhance and verify
  passed; a second enhancement was byte-identical; two fresh enhancements were
  identical; all native `h1`/`h4` text and ids, native ids and hrefs,
  declaration code text and `gnatdoc.css` were preserved; all links resolve;
  there are no external URLs; the only script is `gnatdoc-navigation.js` on
  `index.html`. Added files: `gnatdoc-navigation.js`, `gnatdoc-theme.css`
  (byte-identical to the packaged assets) and `presentation.json`.
- `verify` rejected all eleven mutations: native anchor id, native heading,
  native stylesheet, theme asset, navigation asset, presentation manifest,
  injected script, injected external URL, changed staged default value,
  changed staged comment, and an unapproved extra file.
- A local-type-link variant (`type_links = true`, no external types) also passed
  all checks with 47 local type links.
- Enhancer `main` advanced to `4c75e86524648bd84fad17f112ea2f56f24ebffa`
  (generic-instance summaries, PR #6) during this work. It is **not** used:
  only `478d0bb` is the authorized baseline. Features has no public generic
  instance, so that feature is not needed here.

Browser behaviour, the portal and CI integration are DOC-004 scope.

## Limitations

- The coverage floor is mechanical; reviewers judge semantic accuracy.
- The parser supports only the visible forms in this API; a new form fails
  until the model is extended and reviewed.
- The hosted CI result for this workflow is not known until it runs; this
  record does not claim it. Windows is not involved in documentation builds.
