"""Enhancer integration tests.

Unit tests always run. Real-site mutation tests run when FEATURES_ENHANCED_SITE
(the enhanced site directory containing api/) and FEATURES_ENHANCER_VENV (the
environment from scripts/install_gnatdoc_enhancer.py) are set, as in the
documentation workflow; then missing inputs fail rather than skip.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import enhance_docs  # noqa: E402
import gnatdoc_enhancer_support as support  # noqa: E402

SITE = os.environ.get("FEATURES_ENHANCED_SITE")
VENV = os.environ.get("FEATURES_ENHANCER_VENV")

PAGE = """<!DOCTYPE html>
<html class=main>
<link rel=stylesheet href=gnatdoc.css><body class=content><h1>Demo</h1>
<h4 id=a1>T</h4><pre class=ada-code-snippet><code>type T is (A, B);
</code></pre><p>Doc.<ul><li><a href=#a1>T</a></ul>
"""


class ProfileTests(unittest.TestCase):
    def test_installer_rejects_every_unapproved_revision_before_installation(self):
        import install_gnatdoc_enhancer as installer
        for revision in ("main", "latest", "0" * 40,
                         "478d0bbff0be1b9141b5ad39f07a71f0386d86e9"):
            with self.subTest(revision=revision), mock.patch.object(support, "install") as install:
                self.assertEqual(installer.main(["--checkout", str(ROOT), "--venv", "/unused",
                                                 "--revision", revision]), 1)
                install.assert_not_called()

    def test_modified_installed_asset_and_wrong_provenance_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = Path(directory)
            package = environment / "package"
            package.mkdir()
            asset = package / "navigation.js"
            asset.write_text("original\n")
            record = {"revision": support.PINNED_REVISION, "files": support.package_hashes(package)}
            (environment / support.PROVENANCE).write_text(json.dumps(record))
            with self.assertRaisesRegex(support.SupportError, "is not"):
                support.verified_tool(environment, "0" * 40)
            asset.write_text("modified\n")
            self.assertNotEqual(support.package_hashes(package), record["files"])
            with mock.patch.object(support, "installed_package", return_value=package):
                with self.assertRaisesRegex(support.SupportError, "files changed"):
                    support.verified_tool(environment)

    def test_configuration_is_offline_and_local(self):
        config = tomllib.loads((ROOT / enhance_docs.CONFIG).read_text())
        self.assertEqual(config["security"]["external_hosts"], [])
        self.assertNotIn("external_types", config)
        self.assertNotIn("external_dependencies", config)
        self.assertEqual(config["guides"], {"mode": "markdown", "manifest": "docs/site-map.json"})
        self.assertEqual(config["sources"]["directories"], [enhance_docs.STAGE])
        self.assertEqual(config["gnatdoc"]["version"], "26.0.0")

    def test_asset_inventory_names_the_pinned_revision(self):
        manifest = json.loads((ROOT / enhance_docs.ASSETS).read_text())
        self.assertEqual(manifest["enhancer_revision"], support.PINNED_REVISION)
        site_map = json.loads((ROOT / "docs/site-map.json").read_text())
        expected = {"api/presentation.json", "index.html"} | set(manifest["packaged_assets"]) \
            | {guide["path"] for guide in site_map["guides"]}
        self.assertEqual(set(manifest["added_files"]), expected)
        config = tomllib.loads((ROOT / enhance_docs.CONFIG).read_text())
        self.assertEqual(manifest["public_packages"], sorted(config["sources"]["packages"]))
        requirements = (ROOT / "docs/gnatdoc-guides-requirements.txt").read_text()
        for name, version in manifest["guide_renderer"].items():
            self.assertIn(f"{name}=={version} \\\n    --hash=sha256:", requirements)

    def test_guides_match_the_site_map_and_real_examples(self):
        site_map = json.loads((ROOT / "docs/site-map.json").read_text())
        identities = [guide["id"] for guide in site_map["guides"]]
        self.assertEqual(sorted(p.stem for p in (ROOT / "docs/guides").glob("*.md")),
                         sorted(identities))
        mains = (ROOT / "examples/opencv_features_examples.gpr").read_text()
        for guide in site_map["guides"]:
            if "example" in guide:
                example = ROOT / guide["example"]
                self.assertTrue(example.is_file(), guide)
                self.assertIn(f'"{example.name}"', mains, "example is not a built main")
                text = (ROOT / f"docs/guides/{guide['id']}.md").read_text()
                self.assertIn("```ada\n" + example.read_text().strip("\n") + "\n```", text)

    def test_staging_copies_only_the_documented_specifications(self):
        with tempfile.TemporaryDirectory() as directory:
            staged = Path(directory) / "stage"
            specs = support.stage_public_sources(staged)
            self.assertEqual(sorted(p.name for p in staged.iterdir()), sorted(specs))
            self.assertEqual(len(specs), 4)
            for spec in specs:
                self.assertEqual((staged / spec).read_bytes(), (ROOT / "src" / spec).read_bytes())
            with self.assertRaises(support.SupportError):
                support.stage_public_sources(staged)

    def test_install_requires_a_full_resolvable_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(support.SupportError, "full commit SHA"):
                support.install(Path(directory), "main", Path(directory) / "env")


class SiteLinkTests(unittest.TestCase):
    def test_relative_links_fragments_and_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "api").mkdir()
            (site / "guides").mkdir()
            (site / "api/page.html").write_text(PAGE)
            (site / "api/gnatdoc.css").write_text("body{}")
            (site / "index.html").write_text('<a href="api/page.html#a1">x</a>')
            (site / "guides/g.html").write_text('<a href="../api/page.html">x</a>'
                                                '<script src="x.js" defer></script>')
            (site / "guides/x.js").write_text("")
            result = support.check_site_links(site)
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["scripts"], {"guides/g.html": ["x.js"]})
            for bad in ('<a href="../../outside.html">x</a>', '<a href="api/page.html#no">x</a>',
                        '<a href="https://example.com/">x</a>', '<a href="missing.html">x</a>'):
                with self.subTest(bad=bad):
                    (site / "index.html").write_text(bad)
                    self.assertTrue(support.check_site_links(site)["errors"])


class CompareNativeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.native = Path(directory.name) / "native"
        self.native.mkdir()
        (self.native / "gnatdoc.css").write_text("body{}")
        (self.native / "page.html").write_text(PAGE)
        self.enhanced = Path(directory.name) / "enhanced"
        shutil.copytree(self.native, self.enhanced)

    def edit(self, old, new):
        path = self.enhanced / "page.html"
        path.write_text(path.read_text().replace(old, new))

    def test_identical_and_decorated_copies_pass(self):
        self.edit("<code>type", '<code><span class="ada-keyword">type</span')
        self.edit('ada-keyword">type</span T', 'ada-keyword">type</span> T')
        self.assertEqual(support.compare_native(self.native, self.enhanced)["errors"], [])

    def test_changes_are_rejected(self):
        for old, new, message in (
                ("<h4 id=a1>", "<h4 id=a2>", "ids"),
                (">T</h4>", ">U</h4>", "headings"),
                ("(A, B)", "(A, C)", "code text"),
                ("<h1>", '<a href="https://example.com">x</a><h1>', "external"),
                ("<h1>", '<a href="missing.html">x</a><h1>', "unresolved"),
                ("<h1>", '<a href="#nowhere">x</a><h1>', "unresolved")):
            with self.subTest(message=message):
                shutil.copy(self.native / "page.html", self.enhanced / "page.html")
                self.edit(old, new)
                errors = support.compare_native(self.native, self.enhanced)["errors"]
                self.assertTrue(any(message in e for e in errors), errors)

    def test_stylesheet_and_removed_files_are_rejected(self):
        (self.enhanced / "gnatdoc.css").write_text("body{color:red}")
        self.assertIn("native gnatdoc.css changed",
                      support.compare_native(self.native, self.enhanced)["errors"])
        (self.enhanced / "page.html").unlink()
        self.assertTrue(any("removed" in e for e in
                            support.compare_native(self.native, self.enhanced)["errors"]))


@unittest.skipUnless(SITE and VENV, "set FEATURES_ENHANCED_SITE and FEATURES_ENHANCER_VENV")
class EnhancedSiteMutationTests(unittest.TestCase):
    def setUp(self):
        self.site = Path(SITE)
        self.assertTrue((self.site / "api/presentation.json").is_file(), "enhanced site required")
        self.tool, _ = support.verified_tool(Path(VENV))
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "root"
        (self.root / "docs").mkdir(parents=True)
        shutil.copy(ROOT / enhance_docs.CONFIG, self.root / enhance_docs.CONFIG)
        shutil.copytree(ROOT / enhance_docs.STAGE, self.root / enhance_docs.STAGE)
        for portal in ("docs/site-map.json", "docs/index.html"):
            shutil.copy(ROOT / portal, self.root / portal)
        shutil.copytree(ROOT / "docs/guides", self.root / "docs/guides")
        shutil.copytree(ROOT / "examples/src", self.root / "examples/src")
        shutil.copy(ROOT / "docs_api.gpr", self.root / "docs_api.gpr")
        shutil.copy(ROOT / enhance_docs.ASSETS, self.root / enhance_docs.ASSETS)
        shutil.copytree(ROOT / "src", self.root / "src")
        self.copy = Path(directory.name) / "site"
        shutil.copytree(self.site, self.copy)
        anchors = json.loads((ROOT / "docs/gnatdoc-native-anchors.json").read_text())
        self.existing_anchor = next(v["anchor"] for k, v in anchors["declarations"].items()
                                    if k.startswith("OpenCV.Features.ORB.Create|"))
        self.page = self.copy / "api" / anchors["packages"]["OpenCV.Features.ORB"]["page"]

    def verify(self):
        return support.enhancer(self.tool, "verify", self.root, enhance_docs.CONFIG,
                                self.copy, check=False)

    def assert_rejected(self):
        outcome = self.verify()
        self.assertIsInstance(outcome, subprocess.CompletedProcess, "mutation accepted")
        self.assertNotEqual(outcome.returncode, 0)

    def test_unmodified_copy_verifies(self):
        self.assertEqual(self.verify()["mode"], "verified")

    def test_driver_rejects_nonidempotent_and_nondeterministic_output(self):
        real_enhancer = support.enhancer
        for fresh in (False, True):
            with self.subTest(fresh=fresh):
                output = self.root / ("fresh" if fresh else "idempotent")
                calls = 0

                def altered(tool, command, root, config, site, *extra, **kwargs):
                    nonlocal calls
                    result = real_enhancer(tool, command, root, config, site, *extra, **kwargs)
                    if command == "enhance" and "--dry-run" not in extra:
                        calls += 1
                        if (fresh and site != output) or (not fresh and calls == 2):
                            path = site / "index.html"
                            original = path.read_bytes()
                            path.write_bytes(original + b"\n")
                            self.assertNotEqual(path.read_bytes(), original)
                    return result

                with mock.patch.object(support, "enhancer", side_effect=altered):
                    with self.assertRaisesRegex(enhance_docs.EnhanceError,
                                                "fresh enhancement differs" if fresh else "not byte-idempotent"):
                        enhance_docs.enhance(Path(VENV), ROOT / "_site", output, self.root)

    def test_mutations_are_rejected(self):
        api = self.copy / "api"
        mutations = {
            "native anchor": (self.page, lambda t: re.sub(r"<h4 id=[0-9a-f]{8}",
                                                          "<h4 id=00000000", t, count=1)),
            "native heading": (self.page, lambda t: t.replace("</h4>", "X</h4>", 1)),
            "native stylesheet": (api / "gnatdoc.css", lambda t: t + "\n/* x */\n"),
            "theme asset": (api / "gnatdoc-theme.css", lambda t: t + "\n/* x */\n"),
            "navigation asset": (api / "gnatdoc-navigation.js", lambda t: t + "\n// x\n"),
            "presentation manifest": (api / "presentation.json",
                                      lambda t: t.replace('"26.0.0"', '"26.0.1"', 1)),
            "script": (self.page, lambda t: t.replace("<h1>", "<script>alert(1)</script><h1>", 1)),
            "external URL": (self.page, lambda t: t.replace(
                "<h1>", "<a href=https://example.com>x</a><h1>", 1)),
            "type link target": (self.page, lambda t: re.sub(
                r'(class="type-reference" href="[0-9a-f]{64}\.html#)[0-9a-f]{8}',
                r"\g<1>00000000", t, count=1)),
            "staged source value": (self.root / enhance_docs.STAGE / "opencv-features-orb.ads",
                                    lambda t: t.replace(":= 500;", ":= 501;", 1)),
            "staged source comment": (self.root / enhance_docs.STAGE / "opencv-features.ads",
                                      lambda t: t.replace("--", "-- altered", 1)),
            "rendered guide": (self.copy / "guides/binary-matching.html",
                               lambda t: t.replace("Mutual_Nearest", "Mutual_Furthest", 1)),
            "rendered portal home": (self.copy / "index.html",
                                     lambda t: t.replace("<h1>", "<h1>Altered ", 1)),
            "guide stylesheet": (self.copy / "assets/gnatdoc-guides.css",
                                 lambda t: t + "\n/* x */\n"),
            "guide source": (self.root / "docs/guides/ownership-lifecycle.md",
                             lambda t: t.replace("limited", "unlimited", 1)),
            "embedded example source": (self.root / "examples/src/orb_synthetic.adb",
                                        lambda t: t.replace("Keypoints:", "Points:", 1)),
            "guide API link": (self.copy / "guides/orb-extraction.html",
                               lambda t: re.sub(r'(href="\.\./api/[0-9a-f]{64}\.html#)[0-9a-f]{8}',
                                                r"\g<1>00000000", t, count=1)),
            "missing title": (self.page, lambda t: re.sub(r"<title>.*?</title>", "", t, count=1)),
            "duplicated title": (self.page, lambda t: t.replace("</title>", "</title><title>X</title>", 1)),
            "RCDATA title": (self.page, lambda t: t.replace("<title>", "<title><b>", 1)),
            "unapproved metadata": (self.page, lambda t: t.replace("</head>", '<meta name="x" content="y"></head>', 1)),
            "native declaration": (self.page, lambda t: t.replace("Feature_Set", "Feature_Bag", 1)),
            "wrong existing type link": (self.page, lambda t: re.sub(
                r'(class="type-reference" href="[0-9a-f]{64}\.html#)[0-9a-f]{64}',
                lambda m: m[1] + self.existing_anchor, t, count=1)),
        }
        for label, (path, change) in mutations.items():
            with self.subTest(mutation=label):
                original = path.read_text()
                altered = change(original)
                self.assertNotEqual(altered, original, "mutation did not apply")
                path.write_text(altered)
                try:
                    self.assert_rejected()
                finally:
                    path.write_text(original)

    def test_extra_and_missing_files_are_rejected(self):
        extra = self.copy / "api/extra.html"
        extra.write_text("<!DOCTYPE html>")
        self.assert_rejected()
        extra.unlink()
        (self.copy / "api/gnatdoc-theme.css").unlink()
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main()
