# GitHub Pages publication (DOC-009 / DOC-010 / DOC-011)

## DOC-011 active enhancer dependency

The active documentation dependency is the official **ada-gnatdoc-enhancer
v0.1.0 GitHub release wheel**, source commit
`4ee95e8c95b8c7f54397a07e3e1c507783c115aa`, verified against Features-owned
SHA-256 `b0949aba6736515bf2ebe14fc7cc30c816a176257fc4524564285397b8aaf97d`.
See [installation identities and procedure](gnatdoc-enhancer-integration.md#active-dependency-official-v010-doc-011)
and [DOC-011 qualification](evidence/features-doc-011/README.md).
This supersedes only the active development-tool pin below; DOC-009/010 evidence
remains historical. It does not change the Features source-release status.

The two-job architecture and deployment policy are unchanged. `native-gnatdoc`
has read-only repository permissions and qualifies the actual uploaded Pages
artifact downloaded by immutable ID, including byte comparison with the local
archive and all 18 qualified site files. Only `deploy-pages` has Pages/id-token
write permissions, and only a successful publication-ready **push to main** can
deploy through the main-only `github-pages` environment. Pull requests and manual
dispatches never deploy. No environment restrictions were changed.

Local v0.1.0 qualification preserves all 13 source-owned page titles and metadata,
248 relative references/fragments, all three Chromium campaigns (64, 199 and 64
assertions), the project prefix and the independent JavaScript authority. The
only output byte change is the release version in the rebuilt presentation
manifest. Exact-final-head hosted status is recorded on the DOC-011 review PR;
local archive synthesis is not evidence of an actual GitHub upload or deployment.

The documentation workflow publishes the qualified enhanced site, the API
reference with the developer portal and the seven guides, as the project site
`https://zackboll.github.io/opencv_features_ada/`. It publishes exactly the
`_site-enhanced` directory that the existing pipeline generates and qualifies;
there is no second documentation build and no source file is published.

**Status: publicly deployed from main.** Documentation run
[39196259148](https://github.com/zackboll/opencv_features_ada/actions/runs/39196259148)
qualified and deployed main `71eb93f45b3ee833d4cb2b96a10095aaf0541acd`.
GitHub deployment `7165250076` completed successfully on 2026-10-19; the portal
and API route were independently fetched successfully during FEATURES-REL-014.
DOC-010 removed the title blocker and narrowly corrected the navigation slash
false positive. The [DOC-010 evidence](evidence/features-doc-010/README.md)
remains historical pre-merge evidence; its skipped deployment does not describe
the later main run. Candidate documentation qualification is separate from
publication of the existing main site.

The site describes the development sources on `main` (version 0.1.0-dev). It is
not a release, and Features 0.1.0 is not accepted into the Alire index.

## What is published

The pipeline is unchanged: GNATdoc 26.0.0 output from the four public
specifications with indexed `opencv_core` 0.5.0 (`scripts/generate_docs.sh`,
127/127 elements documented, zero warnings), presented by the pinned
`ada-gnatdoc-enhancer` `23cf51d3765e7b3f68411e25a57f52f4c0efc7e1` with the
hash-pinned Markdown renderer (`scripts/enhance_docs.py`). See the
[GNATdoc foundation](gnatdoc-foundation.md) and the
[enhancer integration](gnatdoc-enhancer-integration.md).

The Pages artifact is the root of `_site-enhanced`, 18 files:

| Path | Content |
| --- | --- |
| `index.html` | developer portal (from `docs/index.html`) |
| `assets/gnatdoc-guides.css` | portal and guide stylesheet (packaged enhancer asset) |
| `guides/*.html` | the seven guides of `docs/site-map.json`, rendered from `docs/guides/*.md` |
| `api/index.html` | native package index with the enhancer's navigation |
| `api/<hash>.html` | the four native package pages (`docs/gnatdoc-native-anchors.json`) |
| `api/gnatdoc.css` | native GNATdoc stylesheet |
| `api/gnatdoc-theme.css`, `api/gnatdoc-navigation.js` | packaged enhancer theme and navigation |
| `api/presentation.json` | enhancer presentation manifest |

The repository root, `obj/`, Alire caches, Python and Node environments, source
archives, Markdown or Ada sources and credentials are never part of it: the
upload step archives `_site-enhanced/` only, and the checker below rejects any
file outside this inventory. The file hashes are in
[gnatdoc-enhancement-evidence.json](gnatdoc-enhancement-evidence.json).

## Workflow

`.github/workflows/documentation.yml` has two jobs.

| Job | Permissions | Runs |
| --- | --- | --- |
| `native-gnatdoc` | `contents: read` (workflow default) | every event: the existing generation, strict checks, mutation tests, regeneration, enhancement, Chromium qualification and source integrity, then the Pages steps |
| `deploy-pages` | `pages: write`, `id-token: write` only | after `native-gnatdoc` succeeds, only for a `push` to `refs/heads/main` whose artifact is publication-ready |

Pages steps of `native-gnatdoc`, after every existing qualification step:

1. `python3 scripts/check_pages_site.py` checks `_site-enhanced` (see below) and
   writes `publication_ready` for the deployment job.
2. A copy is served below `/opencv_features_ada/` on `127.0.0.1`; Chromium runs
   `tests/documentation/test_pages_browser.cjs` and the existing
   `test_enhanced_browser.cjs` against it.
3. When the site is not publication-ready, a warning annotation names the
   blockers.
4. `actions/upload-pages-artifact@v4` uploads `_site-enhanced/` as the
   `github-pages` artifact.
5. `check_pages_site.py --archive "$RUNNER_TEMP/artifact.tar"` proves the
   action-created tar is byte-identical to the qualified directory. The reviewed
   Linux action creates that exact path and uploads it. The workflow additionally
   downloads the actual uploaded artifact by the action's immutable artifact ID,
   compares the downloaded tar with the original tar and reruns the consumer
   checker on it. Missing or mismatched uploaded bytes fail the build; a locally
   synthesized substitute cannot qualify the upload.

`deploy-pages` has one step, `actions/deploy-pages@v4`, targets the
`github-pages` environment, checks out and runs no repository code, and is in a
`github-pages` concurrency group that never cancels a deployment in progress.
Pull requests and manual dispatches build, qualify and upload the artifact but
never deploy: the job is skipped. Superseded pull-request runs are cancelled;
runs on `main` queue. Independently of the workflow file, the repository's
`github-pages` environment accepts deployments from `main` only.

## Publication requirements

`check_pages_site.py` fails the build when:

- the files differ from the reviewed inventory (native pages and stylesheet,
  the enhancer's inventoried added files, the site-map guides) or from the
  files and hashes `enhance_docs.py` verified in the same build;
- a symbolic link, hidden name, special file or a type other than HTML, CSS,
  JavaScript or JSON is present;
- a reference in HTML (attributes, inline styles) or CSS is absolute,
  scheme-relative or root-relative, a page uses `<base>` or a meta refresh, or
  a reference does not resolve under `https://zackboll.github.io/opencv_features_ada/`
  to a published file and, for HTML targets, an existing fragment;
- JavaScript contains an absolute or root-relative URL literal (navigation
  behaviour is qualified in Chromium), or the approved navigation asset differs
  in any byte from its independently reviewed Git-blob hash. Only those exact
  bytes are authorized: `lastIndexOf('/')` at line 103 locates a separator, not
  a URL. No filename-only, slash-literal or method-call exemption is applied;
- a file contains a build path (repository, home, runner or workspace
  directory) or credential-like text;
- with `--archive`, the uploaded tar differs from the site.

Publication additionally requires a non-empty `<title>` on every HTML page.
This does not fail pull requests; it keeps `publication_ready` false, so the
deployment job is skipped and the run shows the blockers.

### Page titles (DOC-010)

| Page | Produced by | `<title>` | `lang` |
| --- | --- | --- | --- |
| `index.html` | `docs/index.html` through the enhancer | `OpenCV Features for Ada documentation` | `en` |
| seven `guides/*.html` | enhancer Markdown guide mode | authored label + ` — OpenCV Features Ada` | `en` |
| `api/index.html` | source-verified shared enhancement | `API Reference — OpenCV Features Ada` | `en` |
| four `api/<hash>.html` | source/native verified package identity | package name + ` — OpenCV Features Ada` | `en` |

The reproduced old pin had 12/13 missing titles and five missing languages.
The old pinned navigation did not contain the slash expression; it first
appears in the adopted navigation, where the original Pages regex rejects it.
All 13 new pages have exactly one valid title, language and UTF-8 metadata.
Shared `verify` reconstructs source-owned output and rejects RCDATA/title
substitution, duplication and unapproved metadata. Features never patches
generated HTML. Metadata is also checked independently and in loaded Chromium
documents, including iframe navigation, reload, history and JavaScript-disabled
pages. The 248-reference census is unchanged; no destinations were waived.

## Project-site prefix

A project site is served below `/opencv_features_ada/`, not at the domain root,
so a root-relative link such as `/api/index.html` would leave the project.
Every generated reference is relative. The checker resolves each one as a
browser would from its page's public URL, and the Chromium test serves the
artifact below the same prefix and checks:

- every route (portal, `api/index.html`, the seven guides and four package
  pages) loads with the expected heading in light and dark schemes, its
  stylesheets load from the prefix and the theme applies, and every request
  stays under the prefix without a failed request or console error;
- a crawl of all 248 references on the 13 pages (targets and fragments);
- `/opencv_features_ada` without a slash redirects to the portal, from which
  relative navigation still works;
- portal navigation to every guide and back, package navigation with
  `?package=` bookmarks and Back on the prefixed path, a prefixed `?package=`
  bookmark, the guide's `api:` link to the masked `Detect_And_Compute` overload
  and a prefixed declaration bookmark.

The existing 64-assertion script also passes unchanged under the prefix.
DOC-010 retains all original 109 prefix assertions and adds 90 metadata checks
(199/199 locally); the reports are in the fresh evidence directory. The
following DOC-009 report remains historical.
Local results (Chromium 156.0.8078.4, Playwright 1.64.1, Node v20.19.2):
[github-pages-browser-qualification.json](github-pages-browser-qualification.json),
109/109 prefix assertions. This is Chromium only, not cross-browser or
accessibility certification.

## Reproducing locally

After the enhancer pipeline (see the
[enhancer integration](gnatdoc-enhancer-integration.md#pipeline)):

```sh
python3 scripts/check_pages_site.py            # writes obj/docs/pages.json
mkdir /tmp/pages-root && cp -R _site-enhanced /tmp/pages-root/opencv_features_ada
python3 -m http.server 8076 --bind 127.0.0.1 --directory /tmp/pages-root &
export PLAYWRIGHT_MODULE=/path/to/node_modules/playwright
PAGES_URL=http://127.0.0.1:8076/opencv_features_ada/ node tests/documentation/test_pages_browser.cjs
DOC_URL=http://127.0.0.1:8076/opencv_features_ada/api/index.html node tests/documentation/test_enhanced_browser.cjs
FEATURES_ENHANCED_SITE="$PWD/_site-enhanced" python3 -m unittest tests.documentation.test_pages_site -v
```

## Owner procedure

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.** On
   2026-10-17 this was already set (`build_type: workflow`; check with
   `gh api repos/zackboll/opencv_features_ada/pages`), and the `github-pages`
   environment allowed deployments from `main` only (Settings → Environments →
   `github-pages` → Deployment branches and tags). No deployment had been made.
2. After independent review and a human merge, the `push` run on `main` must
   pass `native-gnatdoc`. A site failing the publication requirements must not
   deploy. DOC-010 satisfied the former title blocker; main has now deployed.
3. For every subsequent deployment, confirm `deploy-pages` and the
   `github-pages` deployment succeeded, then check the public site:

   ```sh
   curl --fail --silent --show-error --location https://zackboll.github.io/opencv_features_ada/ | grep '<h1>OpenCV Features for Ada</h1>'
   curl --fail --silent --show-error --output /dev/null https://zackboll.github.io/opencv_features_ada/api/index.html
   PAGES_URL=https://zackboll.github.io/opencv_features_ada/ node tests/documentation/test_pages_browser.cjs
   DOC_URL=https://zackboll.github.io/opencv_features_ada/api/index.html node tests/documentation/test_enhanced_browser.cjs
   ```

4. Keep the README publication status evidence-based. The confirmed link now
   records the successful main deployment, not a release-publication claim.

To stop further deployments, disable the workflow (Actions → Ada API
Documentation → Disable workflow) or remove `main` from the environment's
deployment branches; Settings → Pages can unpublish a published site.
