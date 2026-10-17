# Strict zero-gap GNATdoc qualification (DOC-006)

DOC-006 makes the completed documentation state mandatory: both allowed-gap
baselines are empty and `scripts/generate_docs.sh` runs the Features-owned
checker with `--strict`. The checker, source model, warning identities and
anchor matching are unchanged. The DOC-001 measurements in
[gnatdoc-initial-inventory.md](gnatdoc-initial-inventory.md) stay as historical
evidence.

## Identities

| Item | Value |
| --- | --- |
| Starting SHA (`main`) | `7be0f44da70e54a4b2336b3e56b239324f8e781e` (merge of #20 after #18 and #19) |
| Tested SHA | recorded in the follow-up commit below |
| Alire | `alr 2.1.1` |
| Compiler / project tools | `gnat_native=16.1.0` (`GNAT 16.1.0`), `gprbuild=26.0.1` (`GPRBUILD 26.0.0 (2026-04-15)`) |
| Generator | `gnatdoc_bin=26.0.0` (`GNATdoc 26.0.0 (20260415)`) |
| Core | indexed `opencv_core=0.5.0`, origin `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`, from `opencv_core ~0.5.0` (no pin) |
| Native OpenCV for Core configuration | 4.10.0 locally; the Ubuntu 24.04 package (4.6.0) in hosted CI |

## Starting state, verified before any change

Hosted run [39056009636](https://github.com/zackboll/opencv_features_ada/actions/runs/39056009636)
(`Ada API Documentation`, push to `main`, checkout `7be0f44`) succeeded. Its
uploaded reports, not PR descriptions, were checked:

- 4 public packages, 38 source declarations, 38 matched native sections, 2
  internal units excluded; no missing declaration or native anchor;
- 127/127 elements rendered and meaningfully documented; 0 new gaps;
- an empty GNATdoc log: 0 warnings;
- every one of the 116 coverage-baseline identities is present in the report
  and documented, and none of the 110 warning-baseline identities occurs.

A local generation of `7be0f44` with the toolchain above produced a site and
log byte-identical to the run's `features-api-7be0f44…` and
`gnatdoc-diagnostics-7be0f44…` artifacts. Before DOC-006, `--strict` failed on
exactly those stale entries (`FAIL warnings: stale warning baseline entries`).

## Coverage history

| Package | DOC-001 initial | DOC-002 alone | DOC-003 alone | `main` since #20 |
| --- | ---: | ---: | ---: | ---: |
| `OpenCV.Features` | 3/40 | 40/40 | 3/40 | **40/40** |
| `OpenCV.Features.ORB` | 2/34 | 34/34 | 2/34 | **34/34** |
| `OpenCV.Features.Matching` | 5/40 | 5/40 | 40/40 | **40/40** |
| `OpenCV.Features.Correspondences` | 1/13 | 1/13 | 13/13 | **13/13** |
| Total | 11/127 (8.66%) | 80/127 | 58/127 | **127/127 (100%)** |
| GNATdoc warnings | 110 | 43 | 67 | **0** |

## Removed allowances

| File | Entries removed | SHA-256 of removed content |
| --- | ---: | --- |
| `docs/gnatdoc-coverage-baseline.txt` | 116 | `4263138f4a041cfdd28e6739a3c9a186d1286e6f6fde05a58a7393a4b04bb1e3` |
| `docs/gnatdoc-warning-baseline.txt` | 110 | `3d4e5f0697109efecced9e95ab14c5dce162f7ffa452a035614dd304cec83219` |

Both hashes equal the DOC-001 captures recorded in
[gnatdoc-foundation.md](gnatdoc-foundation.md). The coverage entries were 23
record components, 33 parameters, 20 function results, 9 enumeration literals,
4 package descriptions, 15 type, 11 function and 1 procedure descriptions
(`OpenCV.Features` 37, `ORB` 32, `Matching` 35, `Correspondences` 12). The
warnings were 108 public and 2 private-part (`ORB.Finalize`) diagnostics. Both
files remain tracked and are now empty; `--capture` refuses to overwrite them.

## Strict enforcement

`scripts/generate_docs.sh` ends with

```sh
python3 scripts/check_gnatdoc.py all --strict \
    --api "$output/api" \
    --log "$log"
```

and the documentation workflow runs that script for the published site and
for the independent regeneration. With empty baselines, the strict path fails
on any undocumented public element, any GNATdoc warning, any (stale) baseline
entry, an added, removed or changed public declaration, a missing or extra
native section, and any changed native page or anchor.

## Regression tests

`tests/documentation/test_strict_qualification.py` (14 tests; the workflow sets
`FEATURES_DOCS_API`, `FEATURES_DOCS_LOG` and `FEATURES_DOCS_END_TO_END=1`).
Every mutation uses an isolated copy, and each test asserts that the repository
sources, baselines and the generated site and log are unchanged afterwards.

Positive checks: the strict CLI passes on the real output with 4 packages, 38
declarations and sections, 127/127 documented and 0 warnings; the baselines are
tracked and empty; the generator's only checker call is exactly the strict
invocation above; the workflow's generation and regeneration steps run it.

Negative checks:

| Mutation | Strict result |
| --- | --- |
| Rendered `Count` description removed | `new documentation gaps` with `…Count…\|description` |
| Recognized warning added at `Count`'s name position | `new GNATdoc warnings` |
| Obsolete gap `…Count…\|description` restored to the baseline | passes without `--strict`; fails with `stale coverage baseline entries` |
| Obsolete warning ``…: entity `Count` is not documented`` restored | passes without `--strict`; fails with `stale warning baseline entries` |
| `Count` native section removed | `expected one native section, found 0` |
| `Count` native anchor changed | `native anchors/identities changed` |
| End to end: `Count`'s source comment removed, real GNATdoc rerun | generator exits 1 |
| End to end: `Point`'s `@param Index` removed, real GNATdoc rerun | generator exits 1 |

The end-to-end cases reproduce exact DOC-001 identities. Removing `Count`'s
comment yields:

```text
FAIL warnings: new GNATdoc warnings:
  opencv-features.ads: OpenCV.Features.Count: function Count (Features : Feature_Set) return Natural: entity `Count` is not documented
  opencv-features.ads: OpenCV.Features.Count: function Count (Features : Feature_Set) return Natural: parameter `Features` is not documented
  opencv-features.ads: OpenCV.Features.Count: function Count (Features : Feature_Set) return Natural: return value is not documented
```

and the strict coverage check on that output reports
`…Count…|description`, `…|parameter:Features` and `…|return` as new gaps.
Removing `Point`'s `@param Index` yields ``parameter `Index` is not documented``
and the gap `…Point…|parameter:Index`.

## Deterministic regeneration

Under strict mode, `_site` and a generation into a new directory were
byte-identical, as were their (empty) GNATdoc logs, and both equal the hosted
`7be0f44` artifact. Page fingerprints:

| File | SHA-256 |
| --- | --- |
| `api/index.html` | `0d4a79efbedd84ceb9107baec943875d34557a2b07d546a3e460a70d1fd83986` |
| `api/8aee7d25….html` (`OpenCV.Features`) | `bc42228b09c8825211d86149725af11c1857be071cded08a49a79625f526b7ae` |
| `api/71007168….html` (`OpenCV.Features.ORB`) | `bcb5d237fcbcbf0ba493e353015c87b809e5543fde43c606c8dd1969d9ed1cfd` |
| `api/f8c4f9ff….html` (`OpenCV.Features.Matching`) | `b213b4ded5f7a4fb2c5effd458651838a0b074843ec762fc914f05924f0fd81c` |
| `api/0276ad65….html` (`OpenCV.Features.Correspondences`) | `8528f405aa2c9fb936d426a026781ff1b720172f3715258edab904c7e68f448b` |
| `api/gnatdoc.css` | `e86c483e8a66f80bd653129c7ceeec99e63848ecfc308e98ea9de1693fd32e0e` |

## Reproduction

```sh
alr -n build --stop-after=pre-build
export GNATDOC_PREFIX=/path/to/gnatdoc_bin-26.0.0
python3 scripts/check_repository.py
python3 -m unittest discover -s tests/configuration -v
python3 -m unittest discover -s tests/documentation -v
sh scripts/generate_docs.sh
FEATURES_DOCS_API="$PWD/_site/api" FEATURES_DOCS_LOG="$PWD/obj/docs/gnatdoc.log" \
FEATURES_DOCS_END_TO_END=1 python3 -m unittest discover -s tests/documentation -v
cp obj/docs/gnatdoc.log /tmp/gnatdoc-first.log
sh scripts/generate_docs.sh /tmp/features-docs-second
diff -r _site /tmp/features-docs-second && cmp /tmp/gnatdoc-first.log obj/docs/gnatdoc.log
git diff --check origin/main...HEAD
python3 scripts/check_doc_source_integrity.py "$(git merge-base origin/main HEAD)" HEAD
```
