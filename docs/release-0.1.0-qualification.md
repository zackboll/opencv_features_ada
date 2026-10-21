# FEATURES-REL-014 — 0.1.0 source-candidate reconciliation

## Milestones and scope

This is preparation of a source candidate on the existing PR
[#15](https://github.com/zackboll/opencv_features_ada/pull/15), not a merged
source release, tagged GitHub release, or accepted Alire community-index release.
Those are four separate milestones. No tag, GitHub release, index submission,
replacement PR or auto-merge is authorized by this qualification.

## Authoritative baseline

- Initial release HEAD: `5302257323effb19678f6b1bb2c270a2b5cb2b89`;
  tree `37a312368546490ad5860ddd6cc202790f72d911`.
- Integrated main: `71eb93f45b3ee833d4cb2b96a10095aaf0541acd`;
  tree `5ad7cef0eb808bc57828509f66aeabeb712c8bc3`.
- Fresh fetch matched both expected identities. PR #15 was open, non-draft,
  unmerged, with auto-merge disabled; no other open PR or open issue overlapped.
- All documentation PR #18–#25 merge commits are ancestors of integrated main.
- Main Cross-platform Features
  [39196259242](https://github.com/zackboll/opencv_features_ada/actions/runs/39196259242),
  Windows [39196259295](https://github.com/zackboll/opencv_features_ada/actions/runs/39196259295),
  and documentation [39196259148](https://github.com/zackboll/opencv_features_ada/actions/runs/39196259148)
  completed successfully on that exact main SHA.
- Documentation deployed successfully as GitHub deployment `7165250076`;
  the public portal and API route were independently retrieved successfully.
  This is publication of development documentation, not a source release.

## Merge resolution

A normal merge of `origin/main` into `release/0.1.0-source` preserves release
versions and all merged documentation, strict checks, inventories, guides,
enhancer pin, immutable-source/security checks and workflows. Five conflicts:

- `docs/bootstrap-validation.md`: preserve Task 013 candidate evidence and
  main's independent Task 013-W1/W3 corrections, without duplicating the same
  historical Windows failure paragraph.
- `docs/build-and-platforms.md`: retain main's Pages workflow distinction and
  release qualification requirements.
- `docs/coverage.md`: retain release inventory and historical correction records.
- `scripts/check_repository.py`: retain both manifest identity/version assertions
  and main's script-file/Alire-environment assertions.
- `tests/configuration/test_consumer_validation.py`: retain main's stronger
  wrong-version/missing-manifest/workspace-pin and per-install failure tests,
  plus the release branch's explicit unescaped-version assertion.

README merged automatically; stale Pages and Windows status is corrected from
the main run/deployment evidence above. Historical DOC-010 evidence is retained.
Production Ada/C++ source semantics, 17-entry ABI, fixed eight-level ORB and
all matching/ownership contracts must remain unchanged.

## Qualification status

Local native and documentation qualification passed on the reconciled tree.
The exact committed/tested/pushed identities and hosted run results are recorded
in PR #15 to avoid a self-referential commit identity in this source file.

### Reproducible dependencies and tools

Fresh `alr -n update --online` used upstream community index `stable-1.4.0`
at `4635347cb4460e87ea70d6599aeff1eb615bd472`. It selected **opencv_core=0.5.0**,
not a version inferred from the constraint. Its indexed origin is
`git+https://github.com/zackboll/opencv_core_ada.git`, commit
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`. No Core pin or sibling dependency
was used. All three Features manifests remain 0.1.0; production constraint
remains `opencv_core = "~0.5.0"`.

Host resolution: `opencv=4.10.0`, `pkg_config=1.8.1`; test-only `aunit=26.0.0`.
Host Debian 13, Alire 2.1.1, GNAT native 16.1.0, GPRbuild crate 26.0.1
(binary 26.0.0, 2026-04-15), g++ 14.2.0, native OpenCV 4.10.0/features2d.
GNATdoc is exactly 26.0.0 (20260415), using the existing strict generator.
The enhancer is unchanged at `23cf51d3765e7b3f68411e25a57f52f4c0efc7e1`;
installed modules/assets were compared against immutable Git blobs and guide
renderer hashes were checked by the existing installer.

### Local execution

| Gate | Result |
| --- | --- |
| Repository/manifests and fixed ORB profile | PASS; 17 ABI declarations/imports, 67 registered AUnit cases |
| Complete configuration suite | PASS; 83 tests |
| Native Alire build | PASS; warnings-as-errors unchanged |
| AUnit | PASS; 67 executed, 67 successful, zero failed assertions/errors |
| Production/fault-injection native boundaries | PASS through `alr test` |
| Production/fault ASan and UBSan | PASS; no reported sanitizer errors |
| Both synthetic examples | PASS; 393 keypoints; nearest 406, mutual 218, ratio 121, radius 89 (fixture results, not API guarantees) |
| GPRinstall and shim-link metadata regressions | PASS; eight toolchain-backed tests through Alire |
| Fresh source, installed and relocated consumers | PASS; all three public-only applications built and ran |
| Source-path/link metadata audits | PASS; original source/prefix hidden; installed project/library resolution verified independently |
| Clean exported-source Alire build | PASS; no checkout build/config/cache artifacts exported |
| Debian 12 native compatibility | PASS; GNAT/g++ 12.2.0, native OpenCV 4.6.0, build, AUnit 67/67, both raw variants and both examples |
| Strict GNATdoc | PASS; 127/127 documented/rendered elements, four packages, 38 declarations, zero warnings; inventory unchanged |
| Deterministic native regeneration | PASS; site and diagnostic log byte-identical |
| Complete documentation suite | PASS; 94 tests, no skips, including real generation/mutations, guide/example and security checks |
| Enhancer compatibility preflight | PASS; zero failures; source/native identities preserved |
| Enhancement verification | PASS; immutable sources, native links/anchors/code, idempotence, deterministic fresh copy, all guides preserved |
| Chromium enhanced-site tests | PASS; 64/64 |
| Chromium project-prefix tests | PASS; 199/199 plus original 64/64 API assertions |
| Pages site and local archive | PASS; 18 files, 13 pages, 248 references; archive byte-identical |
| Independent public Pages browser test | PASS; 199/199 against the already deployed main site |

The existing installed metadata auditor reports one **unused**
`Common_Cxx_Switches` build variable containing the historical Core source include
path. It is non-load-bearing in externally built installed projects; active
source, ALI, linker and runtime resolution use the installed prefix/system native
libraries. This is not described as an absence of all textual source paths.
No audit exception or acceptance rule was changed.

The documentation-only whole-repository integrity checker correctly rejects
release manifest and release-check changes: this is not a docs-only PR. A separate
comparison using its real Ada lexer verifies that **all production Ada/GPR token
streams and C++ bytes equal integrated main**. The original integrity checker
and its regression tests remain unchanged and enabled for documentation PRs.
No public semantic validation is duplicated in the C++ shim by this task;
the shim is byte-identical to main.

Command-invocation issues were corrected without weakening checks: install
regressions require `alr exec`, GNATdoc requires the exact pinned installation,
and container commands require an existing explicit working directory. The
configured IDE command directory disappeared twice during execution; only an
empty recovery directory/note was recreated, not any Core source or Git state.

### Remaining identity-dependent gates

The non-submitting Alire publication validation against the final pushed commit,
final-head Linux/macOS/documentation CI (including immutable uploaded Pages
artifact verification), and manually dispatched OpenCV 4.1.0/4.10.0/5.0.0 matrix
must pass before independent-review readiness is claimed. PR #15 retains the
historical release evidence and supplies final results and run URLs. Local
evidence is retained outside committed source; no environment-specific paths
or tool dependencies are added to the production crate.

Windows execution of the final candidate is intentionally a post-merge gate;
the successful main baseline cannot qualify it. Release publication remains
blocked until review, merge, post-merge Windows and separate publication approval.