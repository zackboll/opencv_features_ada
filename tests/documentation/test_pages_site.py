"""GitHub Pages artifact and deployment workflow tests.

Unit tests always run. The real-site test runs when FEATURES_ENHANCED_SITE (the
enhanced site directory) is set, as in the documentation workflow.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_pages_site as pages  # noqa: E402

SITE = os.environ.get("FEATURES_ENHANCED_SITE")
WORKFLOW = ROOT / ".github/workflows/documentation.yml"

FIXTURE = {
    "index.html": '<!doctype html><html lang="en"><head><title>Home</title>'
                  '<link rel="stylesheet" href="assets/site.css"></head><body><h1>Home</h1>'
                  '<a href="api/index.html">API</a> <a href="guides/a.html#intro">Guide</a></body></html>',
    "api/index.html": '<html lang="en"><title>API</title><a href="p.html#x">P</a>'
                      '<script src="nav.js"></script>',
    "api/p.html": '<html lang="en"><title>P</title><h4 id="x">X</h4><a href="../index.html">Home</a>',
    "api/nav.js": "const u = new URL('p.html', location.href);\n",
    "assets/site.css": "body { color: black; }\n",
    "guides/a.html": '<html lang="en"><title>A</title><h1 id="intro">A</h1>'
                     '<a href="../api/p.html#x">P</a> <a href="../">Home</a>',
}
ROUTES = ["", "api/index.html", "guides/a.html", "api/p.html"]


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)


def pages_archive(site: Path, archive: Path) -> None:
    """The archive command of actions/upload-pages-artifact@v4 on Linux."""
    subprocess.run(["tar", "--dereference", "--hard-dereference", "--directory", str(site),
                    "-cf", str(archive), "--exclude=.git", "--exclude=.github",
                    "--exclude=.[^/]*", "."], check=True)


class CheckerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.temp = Path(directory.name)
        self.site = self.temp / "site"
        write(self.site, FIXTURE)

    def check(self, **options):
        return pages.check(self.site, set(FIXTURE), ROUTES, **options)

    def test_relative_site_passes_and_is_ready(self):
        report = self.check()
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["publication_ready"])
        self.assertEqual(report["html_pages"], 4)
        self.assertEqual(report["routes"][pages.PAGES_URL + "guides/a.html"], "guides/a.html")

    def test_missing_title_blocks_publication_without_an_error(self):
        write(self.site, {"guides/a.html": FIXTURE["guides/a.html"].replace("<title>A</title>", "")})
        report = self.check()
        self.assertEqual(report["errors"], [])
        self.assertFalse(report["publication_ready"])
        self.assertEqual(report["pages_without_title"], ["guides/a.html"])
        self.assertIn("1 of 4 HTML pages have no <title>: guides/a.html", report["blockers"][0])

    def test_reference_mutations_are_errors(self):
        for page, old, new, message in (
                ("guides/a.html", '"../api/p.html#x"', '"/api/p.html#x"', "root-relative"),
                ("guides/a.html", '"../api/p.html#x"', '"/opencv_features_ada/api/p.html"',
                 "root-relative"),
                ("guides/a.html", '"../api/p.html#x"', '"//example.invalid/p.html"', "absolute"),
                ("guides/a.html", '"../api/p.html#x"',
                 f'"{pages.PAGES_URL}api/p.html"', "absolute"),
                ("guides/a.html", '"../api/p.html#x"', '"../../p.html"', "resolves outside"),
                ("guides/a.html", '"../api/p.html#x"', '"../api/p.html#missing"', "no fragment"),
                ("guides/a.html", '"../api/p.html#x"', '"../api/q.html"', "no published file"),
                ("guides/a.html", '"../api/p.html#x"', '"../api"', "no published file"),
                ("index.html", '<h1>Home</h1>', '<base href="api/"><h1>Home</h1>', "<base>"),
                ("index.html", '<h1>Home</h1>',
                 '<meta http-equiv="refresh" content="0; url=api/"><h1>Home</h1>', "meta refresh"),
                ("index.html", '<h1>Home</h1>', '<h1 style="background: url(/x.png)">Home</h1>',
                 "root-relative"),
                ("assets/site.css", "color: black;", "background: url('/x.png');", "root-relative"),
                ("assets/site.css", "color: black;", '@import "../../x.css";', "resolves outside"),
                ("api/nav.js", "'p.html'", "'/p.html'", "URL literal"),
                ("api/nav.js", "'p.html'", "'https://example.invalid/'", "URL literal")):
            with self.subTest(message=message, new=new):
                write(self.site, FIXTURE)
                write(self.site, {page: FIXTURE[page].replace(old, new)})
                self.assertNotEqual(FIXTURE[page], (self.site / page).read_text())
                report = self.check()
                self.assertTrue(any(message in e for e in report["errors"]), report["errors"])
                self.assertFalse(report["publication_ready"])

    def test_inventory_file_type_link_and_hidden_mutations_are_errors(self):
        for mutate, message in (
                (lambda: write(self.site, {"guides/a.md": "# A\n"}), "unexpected ['guides/a.md']"),
                (lambda: write(self.site, {"src/x.ads": "package X is end X;\n"}),
                 "unpublishable file type src/x.ads"),
                (lambda: (self.site / "api/p.html").unlink(), "missing ['api/p.html']"),
                (lambda: write(self.site, {".nojekyll": ""}), "hidden name .nojekyll"),
                (lambda: write(self.site, {"api/.cache/x.json": "{}"}), "hidden name api/.cache"),
                (lambda: (self.site / "assets/link.css").symlink_to(self.site / "assets/site.css"),
                 "symbolic link assets/link.css"),
                (lambda: (self.site / "outside").symlink_to(self.temp, target_is_directory=True),
                 "symbolic link outside")):
            with self.subTest(message=message):
                shutil.rmtree(self.site)
                write(self.site, FIXTURE)
                mutate()
                report = self.check()
                self.assertTrue(any(message in e for e in report["errors"]), report["errors"])

    def test_build_paths_and_credentials_are_errors(self):
        token = "gh" + "p_" + "A" * 36
        key = "-----BEGIN " + "RSA PRIVATE KEY-----"
        for text, message in ((str(pages.ROOT), "build path"), (token, "credential-like"),
                              (key, "credential-like")):
            with self.subTest(message=message):
                write(self.site, FIXTURE)
                write(self.site, {"assets/site.css": f"/* {text} */\n"})
                report = self.check()
                self.assertTrue(any(message in e for e in report["errors"]), report["errors"])

    def test_site_must_equal_the_verified_enhancement(self):
        hashes = {name: pages.sha256(text.encode()) for name, text in FIXTURE.items()}
        self.assertEqual(self.check(enhancement={"enhanced_site": hashes})["errors"], [])
        changed = dict(hashes, **{"api/p.html": "0" * 64})
        self.assertIn("the site differs from the files and hashes verified by enhance_docs.py",
                      self.check(enhancement={"enhanced_site": changed})["errors"])

    def test_uploaded_archive_must_be_byte_identical(self):
        archive = self.temp / "artifact.tar"
        pages_archive(self.site, archive)
        report = self.check(archive=archive)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["archive"], {"files": len(FIXTURE), "identical": True})
        write(self.site, {"api/p.html": FIXTURE["api/p.html"] + " "})
        report = self.check(archive=archive)
        self.assertTrue(any("changed ['api/p.html']" in e for e in report["errors"]))

    def test_archive_links_and_escapes_are_rejected(self):
        for name, kind in (("../x.html", tarfile.REGTYPE), ("/x.html", tarfile.REGTYPE),
                           ("./link.html", tarfile.SYMTYPE)):
            with self.subTest(name=name):
                archive = self.temp / "bad.tar"
                with tarfile.open(archive, "w") as tar:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.linkname = "/etc/passwd" if kind == tarfile.SYMTYPE else ""
                    tar.addfile(member, None if kind == tarfile.SYMTYPE else io.BytesIO(b""))
                with self.assertRaises(pages.PagesError):
                    pages.read_archive(archive)


class ReviewedInventoryTests(unittest.TestCase):
    def test_inventory_has_the_portal_api_assets_and_seven_guides(self):
        expected = pages.expected_files()
        anchors = json.loads((ROOT / "docs/gnatdoc-native-anchors.json").read_text())
        packages = {"api/" + p["page"] for p in anchors["packages"].values()}
        self.assertEqual(len(packages), 4)
        self.assertLessEqual({"index.html", "api/index.html", "api/gnatdoc.css",
                              "api/gnatdoc-theme.css", "api/gnatdoc-navigation.js",
                              "assets/gnatdoc-guides.css"} | packages, expected)
        self.assertEqual(len([n for n in expected if n.startswith("guides/")]), 7)
        self.assertEqual(len(expected), 18)
        routes = pages.routes()
        for route in ("", "api/index.html", "guides/getting-started.html",
                      "guides/orb-extraction.html", "guides/binary-matching.html"):
            self.assertIn(route, routes)
        self.assertEqual(len(routes), 13)
        self.assertLessEqual({r or "index.html" for r in routes}, expected)


class NavigationSecurityTests(unittest.TestCase):
    """Immutable input fixture, independently copied from the reviewed Git blob.

    Output-side manifests and same-run hashes must never confer JS authority.
    """
    NAVIGATION = "api/gnatdoc-navigation.js"
    EXPRESSION = "state.url.href.lastIndexOf('/')"

    def setUp(self):
        CheckerTests.setUp(self)
        self.script = (ROOT / "tests/documentation/fixtures/gnatdoc-navigation.js").read_text()
        self.assertEqual(pages.sha256(self.script.encode()),
                         "b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd")
        write(self.site, {self.NAVIGATION: self.script})

    def check(self, **options):
        return pages.check(self.site, set(FIXTURE) | {self.NAVIGATION}, ROUTES, **options)

    def test_original_regex_rejects_the_approved_separator(self):
        self.assertEqual(self.script.count(self.EXPRESSION), 1)
        matches = list(re.finditer(r"://|[\"'`]/", self.script))
        self.assertEqual(len(matches), 1)
        self.assertEqual(self.script[:matches[0].start()].count("\n") + 1, 103)
        self.assertIn(self.EXPRESSION, self.script.splitlines()[102])

    def test_exact_reviewed_navigation_passes(self):
        self.assertEqual(self.check()["errors"], [])

    def test_unsafe_literals_cannot_hide_beside_the_approved_expression(self):
        for literal in ("'/api/index.html'", "'//example.com/path'", "'https://example.com/'",
                        '"http://example.com/"', '`/${path}`', "'/x' + suffix", "'/'",
                        r"'\x2fapi/index.html'", r"'\u002fapi/index.html'", r"'\/api/index.html'",
                        r'"\u{2f}api/index.html"', r'`\x2f${path}`', r"'\057api/index.html'",
                        '"//example.com"', '`https://example.com/`'):
            with self.subTest(literal=literal):
                altered = self.script + "\nconst destination = " + literal + ";\n"
                self.assertNotEqual(altered, self.script)
                self.assertIn(self.EXPRESSION, altered)
                write(self.site, {self.NAVIGATION: altered})
                report = self.check()
                self.assertTrue(any("JavaScript" in e for e in report["errors"]), report)
                self.assertFalse(report["publication_ready"])

    def test_rewrites_and_malformed_expressions_are_rejected(self):
        for expression in ("state.url.href.lastIndexOf('/x')", 'state.url.href.lastIndexOf("/")',
                           "state.url.href.indexOf('/')", "state.url.href.split('/')",
                           "0 /* substituted separator expression */",
                           "state.url.href.lastIndexOf('/'", "window.location.href = '//example.com'",
                           "state.url.href.lastIndexOf(`/${path}`)"):
            with self.subTest(expression=expression):
                altered = self.script.replace(self.EXPRESSION, expression)
                self.assertNotEqual(altered, self.script)
                write(self.site, {self.NAVIGATION: altered})
                self.assertFalse(self.check()["publication_ready"])

    def test_rewritten_output_manifests_cannot_authorize_modified_javascript(self):
        altered = self.script + "\n// unexpected modification\n"
        self.assertNotEqual(altered, self.script)
        write(self.site, {self.NAVIGATION: altered})
        manifest = "api/presentation.json"
        forged = {"assets": {self.NAVIGATION: pages.sha256(altered.encode())}}
        write(self.site, {manifest: json.dumps(forged)})
        self.assertEqual(json.loads((self.site / manifest).read_text()), forged)
        hashes = {p.relative_to(self.site).as_posix(): pages.sha256(p.read_bytes())
                  for p in self.site.rglob("*") if p.is_file()}
        report = pages.check(self.site, set(hashes), ROUTES, {"enhanced_site": hashes})
        self.assertNotIn("the site differs from the files and hashes verified by enhance_docs.py",
                         report["errors"])
        self.assertTrue(any("JavaScript" in e for e in report["errors"]), report)
        self.assertFalse(report["publication_ready"])

    def test_filename_alone_does_not_authorize_the_expression(self):
        write(self.site, {self.NAVIGATION: self.EXPRESSION + ";\n"})
        self.assertNotEqual((self.site / self.NAVIGATION).read_text(), self.script)
        self.assertFalse(self.check()["publication_ready"])


def jobs(text: str) -> dict[str, str]:
    body = text.split("\njobs:\n", 1)[1]
    return {m[1]: m[2] for m in re.finditer(r"^  ([\w-]+):\n((?:(?:    .*)?\n)+)", body, re.M)}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.jobs = jobs(self.text)

    def test_least_privilege_permissions(self):
        self.assertIn("\npermissions:\n  contents: read\nconcurrency:\n", self.text)
        self.assertEqual(set(self.jobs), {"native-gnatdoc", "deploy-pages"})
        self.assertNotIn("permissions:", self.jobs["native-gnatdoc"])
        self.assertIn("    permissions:\n      pages: write\n      id-token: write\n",
                      self.jobs["deploy-pages"])
        self.assertEqual(self.text.count("pages: write"), 1)
        self.assertEqual(self.text.count("id-token: write"), 1)

    def test_deployment_only_from_a_ready_push_to_main(self):
        deploy = self.jobs["deploy-pages"]
        self.assertIn("    needs: native-gnatdoc\n", deploy)
        condition = re.search(r"    if: >-\n((?:      .*\n)+)", deploy)[1].split()
        self.assertEqual(" ".join(condition),
                         "github.event_name == 'push' && github.ref == 'refs/heads/main' && "
                         "needs.native-gnatdoc.outputs.publication_ready == 'true'")
        self.assertIn("    environment:\n      name: github-pages\n", deploy)
        self.assertIn("    concurrency:\n      group: github-pages\n      cancel-in-progress: false\n",
                      deploy)
        steps = re.findall(r"^      - ", deploy, re.M)
        self.assertEqual(len(steps), 1)
        self.assertIn("uses: actions/deploy-pages@v4\n", deploy)
        self.assertNotIn("run:", deploy)
        self.assertNotIn("checkout", deploy)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", self.text)

    def test_artifact_is_uploaded_after_qualification_and_verified(self):
        build = self.jobs["native-gnatdoc"]
        names = re.findall(r"^      - name: (.*)$", build, re.M)
        order = [names.index(n) for n in (
            "Enhance an isolated copy of the native site with guides and verify it",
            "Chromium qualification of the enhanced site",
            "Coverage and warning summary",
            "Qualify the Pages artifact under the project-site prefix",
            "Upload the qualified enhanced site as the GitHub Pages artifact",
            "Verify the uploaded Pages archive is byte-identical to the qualified site")]
        self.assertEqual(order, sorted(order))
        self.assertEqual(build.count("actions/upload-pages-artifact@v4"), 1)
        upload = build.split("actions/upload-pages-artifact@v4", 1)[1]
        self.assertTrue(upload.startswith("\n        with:\n          path: _site-enhanced/\n"))
        self.assertIn("publication_ready: ${{ steps.pages.outputs.publication_ready }}", build)
        self.assertIn('python3 scripts/check_pages_site.py --github-output "$GITHUB_OUTPUT"', build)
        self.assertIn('check_pages_site.py --archive "$RUNNER_TEMP/artifact.tar"', build)
        self.assertIn("artifact-ids: ${{ steps.pages-upload.outputs.artifact_id }}", build)
        self.assertIn("          merge-multiple: true\n", build)
        self.assertIn('cmp "$RUNNER_TEMP/artifact.tar" "$RUNNER_TEMP/uploaded-pages/artifact.tar"',
                      build)
        self.assertIn('--archive "$RUNNER_TEMP/uploaded-pages/artifact.tar"', build)
        self.assertIn("node tests/documentation/test_pages_browser.cjs", build)
        self.assertIn('DOC_URL="${PAGES_URL}api/index.html"', build)


@unittest.skipUnless(SITE, "set FEATURES_ENHANCED_SITE")
class RealSiteTests(unittest.TestCase):
    def test_all_metadata_matches_source_owned_identities(self):
        import html
        import tomllib
        project = tomllib.loads((ROOT / "docs/gnatdoc-enhance.toml").read_text())["project"]
        anchors = json.loads((ROOT / "docs/gnatdoc-native-anchors.json").read_text())
        site_map = json.loads((ROOT / "docs/site-map.json").read_text())
        expected = {"index.html": "OpenCV Features for Ada documentation",
                    "api/index.html": "API Reference — " + project}
        expected.update({"api/" + data["page"]: name + " — " + project
                         for name, data in anchors["packages"].items()})
        expected.update({g["path"]: g["label"] + " — " + project for g in site_map["guides"]})
        self.assertEqual(len(expected), 13)
        for name, title in expected.items():
            with self.subTest(page=name):
                text = (Path(SITE) / name).read_text(encoding="utf-8")
                self.assertEqual(len(re.findall(r"<title(?:\s[^>]*)?>", text, re.I)), 1)
                raw = re.search(r"<title>(.*?)</title>", text, re.S)[1]
                self.assertEqual(html.unescape(raw), title)
                self.assertNotIn("<", raw)
                self.assertRegex(text, r'<html\b[^>]*\blang="en"')
                self.assertEqual(len(re.findall(r"<head>", text)), 1)
                self.assertEqual(len(re.findall(r"</head>", text)), 1)
                self.assertEqual(len(re.findall(r'<meta charset="utf-8">', text)), 1)
                metas = re.findall(r"<meta\b[^>]*>", text)
                self.assertTrue(all(m == '<meta charset="utf-8">' or
                                    m == '<meta name="viewport" content="width=device-width, initial-scale=1">'
                                    for m in metas), metas)

    def test_real_site_is_a_qualified_pages_artifact(self):
        report = pages.check(Path(SITE).resolve(), pages.expected_files(), pages.routes())
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["files"]), 18)
        self.assertEqual(report["html_pages"], 13)
        self.assertEqual(report["publication_ready"], not report["pages_without_title"])
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "artifact.tar"
            pages_archive(Path(SITE), archive)
            report = pages.check(Path(SITE).resolve(), pages.expected_files(), pages.routes(),
                                 archive=archive)
            self.assertEqual(report["archive"], {"files": 18, "identical": True})


if __name__ == "__main__":
    unittest.main()
