# FEATURES-DOC-010 qualification

## Identities and disposition

- Starting Features main: `78a07df8bfd4884a9546cee78904fb5ff93aae21` (unchanged
  when rechecked before opening this PR).
- Old enhancer: `478d0bbff0be1b9141b5ad39f07a71f0386d86e9`.
- New enhancer: `23cf51d3765e7b3f68411e25a57f52f4c0efc7e1`, the actual two-parent
  merge of shared PR #10, equal to independently fetched enhancer `origin/main`.
- Package version: `0.1.0.dev0`, independently read from that Git tree.
- Final tested Features identity: the exact PR HEAD recorded in the hosted
  `gnatdoc-diagnostics-<sha>/qualification-head.json` artifact, together with the
  run URL and event. It is deliberately recorded at runtime: embedding a commit's
  own SHA in that same commit is not possible. The PR qualification comment binds
  the exact final HEAD to its completed hosted run and downloaded reports.
- Disposition when this record was written: **HOSTED_CI_PENDING**. Local site qualification passed;
  actual uploaded-artifact identity and exact-head hosted success remain required.
  Live exact-head status and completed run links are recorded on
  [Features PR #25](https://github.com/zackboll/opencv_features_ada/pull/25).
- Hosted implementation qualification **passed** at
  `fde853b5447a740b41f6c8eb22b9b9680ba65ef6` in
  [run 39191682802](https://github.com/zackboll/opencv_features_ada/actions/runs/39191682802).
  `hosted-fde853b/` preserves the actual downloaded metadata, Pages and browser
  reports, artifact IDs/digests and job/step outcomes. `native-gnatdoc` succeeded;
  `deploy-pages` was skipped. Both archive checks passed, including the actual
  upload downloaded by immutable ID. A separate agent-side download confirmed
  all 18 hashes equal both hosted and local qualified sites; tar SHA-256 is
  `11d45b53b734a9d06fc3b22f7aa7362f810d05901329cb8fa94d9a5a0ac14b6f`.
  This evidence-only follow-up requires a **new exact-final-head run**; the PR
  records that result without pretending the earlier commit is the final HEAD.
- No merge, deployment, release, tag, auto-merge, production/dependency changes,
  shared-enhancer modifications or PR #15 modifications are authorized or made.

Local work used a separate clean clone/branch and a detached baseline worktree.
Only the separate source-release PR #15 was open; no overlapping documentation
PR or active documentation generation process was found. Existing worktrees and
servers were not altered. Historical DOC-001–009 evidence is untouched.

## Baseline and false-positive reproduction

`baseline.txt`, `baseline-pages.json`, `baseline-enhancement.json`,
`baseline-provenance.json` and baseline Chromium reports are fresh measurements
from the exact starting commit, before the pin/checker changed.

The actual old pin has **no** `lastIndexOf('/')` expression and **no** JavaScript
checker error. It has 12 untitled pages and five pages without language, and is
not publication-ready. This differs from the task's historical JS expectation.

The adopted script, independently extracted from its immutable Git blob, has:

```javascript
// src/ada_gnatdoc_enhancer/assets/gnatdoc-navigation.js, line 103
if (!state || link.getAttribute('href')!==state.url.href.slice(state.url.href.lastIndexOf('/')+1)) {
```

The original regex (colon/slashes or a quote/backtick followed by a slash) matches the quote/slash inside that
expression. `original-checker-new-site.json` runs the actual unmodified baseline
checker against the new complete site: this is its sole error; all titles and
languages are now present. The negative-first run `security-red.txt` shows the
exact approved-script acceptance test failing before the checker correction
(`security-red.txt`).

The test fixture is byte-identical to the new Git blob, SHA-256
`b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd`.
The correction compares the entire asset hash against independent source-owned
policy, not an output manifest. It does not rewrite, remove or lexically exempt
expressions. Every changed byte fails, including escaped URLs, delimiter changes,
malformed calls, appended redirects and rewritten output-side manifests/hashes.

## Local qualification

| Gate | Measured result |
| --- | --- |
| Toolchain | Alire 2.1.1; GNAT 16.1.0; Alire GPRbuild 26.0.1 (reports GPRBUILD 26.0.0); GNATdoc 26.0.0 (20260415) |
| Core | indexed 0.5.0; no constraint or pin change |
| Native | 4 exact public packages; 38 declaration sections; 127/127 documented; zero warnings/gaps, original empty baselines |
| Regeneration | baseline, new native and independent second native trees byte-identical; logs identical |
| Shared enhancement | installed Git blobs verified; public source staging; inventory; immutable dry-run; independent verify; native preservation; two-copy determinism; byte-idempotence |
| Site | 13 HTML pages; 18 files; 248 references, 131 with fragments; 13 routes; zero unresolved/external references; 47 local type links, zero external type links |
| Metadata | 13/13 exact source-owned titles, `en`, UTF-8, one head/title, approved metadata only; title RCDATA/duplicate/unapproved mutations rejected |
| Documentation tests | 94/94 passed with all real-site and end-to-end environment gates enabled; no skips |
| Chromium enhanced | original suite unchanged: 64/64 |
| Chromium project prefix | original 109 assertions retained, 90 additive metadata checks: 199/199 |
| Chromium enhanced under prefix | unchanged suite: 64/64 |
| Native AUnit | 67 run, 67 successful, zero failed assertions/unexpected errors |
| Compiled guide examples | `orb_synthetic` and `orb_match_synthetic` built and executed |
| Repository/configuration/profile | repository check; 83 configuration tests; fixed-profile/layout tests and shell syntax passed |
| Consumer Pages checker | `errors=[]`, `pages_without_title=[]`, `pages_without_lang=[]`, `publication_ready=true` |
| Local Pages tar | action-equivalent command: 18 files byte-identical; **not** claimed as uploaded-artifact proof |

`documentation-tests.txt` records the complete enabled run. Additional adversarial
cases include wrong enhancer revision, modified installed assets, existing-but-wrong
type destination, staged source/comment changes, missing/extra files, presentation
manifest, native declaration/anchor changes, authored content, broken fragments,
metadata, nonidempotent/nondeterministic driver output and mismatched tar.
Every added mutation asserts that the changed bytes differ from the original.
The optional independent preflight also passed with zero failures, preserving
the pristine site and checking conservative and local-type-link profiles:
`preflight.json`. `source-integrity.txt` records the committed-tree check from
the actual main merge base; the unchanged production token/byte invariant is
also enforced on the final hosted HEAD.

Two local test setup failures were corrected without weakening gates: the first
full test invocation omitted `GNATDOC_PREFIX`; it was rerun with the required
qualified prefix. An additive iframe metadata test initially raced document
creation; it now waits for document completion. The unchanged 64 assertions were
never edited. Chromium qualification is not cross-browser/accessibility certification.

## Asset and output review

`asset-git-hashes.json` hashes both immutable Git trees independently. Navigation
and theme changed; guide CSS did not. `enhancer-provenance.json` records all 31
installed module/asset hashes proven equal to Git blobs.
`renderer-verification.json` independently confirms unchanged wheel digests and
all installed renderer modules (68 Markdown, seven mdurl) equal wheel members.
Renderer constraints and hashes were not edited.

`output-comparison.json` classifies **every** file, with old/new SHA-256:

- Five API pages: metadata insertion only; removing the exact new head/title/lang
  additions restores the old bytes. All 38 declaration identities, original
  anchors, code, documentation and links remain unchanged.
- Seven guides: only the source-owned title is added; removing it restores old
  bytes. Markdown, examples, guide bodies and API links are unchanged.
- Navigation: exact reviewed upstream blob; native-link-only destination map,
  declaration query bookmarks and outer-owned history, stale-load protection,
  iframe native-click handling, and mutation rejection. The slash is a separator.
- Theme: exactly four generic-instance presentation rules; no Features instance
  is introduced or documented.
- Presentation manifest: only `output_sha256` changes; all other fields identical.
- Portal home, native stylesheet and guide stylesheet: byte-identical.

No file is authorized merely because an enhancer produced it. The approved file
inventory and same-run enhanced-site hashes remain independent checks.

## Actual upload and deployment controls

Reviewed `actions/upload-pages-artifact@v4` action source at
`7b1f4a764d45c48632c6b24a0339c27f5614fb0b`: on Linux its tar command writes
`$RUNNER_TEMP/artifact.tar` and its upload step uploads that exact file. Thus the
existing local archive path is valid and available after the action. No existing
archive-path defect was reproduced.

The workflow now additionally downloads the **actual** uploaded artifact using
`steps.pages-upload.outputs.artifact_id`, with `merge-multiple: true` (required
for ID-based download into the exact target directory). It requires `cmp` equality
to the action-created tar and reruns the checker on the downloaded tar. Missing,
substituted or changed uploaded bytes block the build. Hosted evidence must confirm
this step; local tar synthesis is not a substitute.

Ordinary build permissions remain `contents: read`. Pages/id-token write remain
only in `deploy-pages`; the main-only push, readiness, successful dependency job,
`github-pages` environment and deployment concurrency conditions are unchanged.
The environment's deployment branch policy was independently inspected: `main`
only. Pull requests/manual dispatch never deploy. Production readiness requires
the exact final PR HEAD's full documentation run and successful downloaded-upload
qualification, with deployment skipped on the PR. Stop at independent review.

After independent approval and human merge, only the main workflow may deploy.
The actual public site and routes still need post-deployment verification before
any claim that Features documentation publication is complete.