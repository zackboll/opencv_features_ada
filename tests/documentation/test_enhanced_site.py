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
    def test_configuration_is_offline_and_local(self):
        config = tomllib.loads((ROOT / enhance_docs.CONFIG).read_text())
        self.assertEqual(config["security"]["external_hosts"], [])
        self.assertNotIn("external_types", config)
        self.assertNotIn("external_dependencies", config)
        self.assertEqual(config["guides"]["mode"], "none")
        self.assertEqual(config["sources"]["directories"], [enhance_docs.STAGE])
        self.assertEqual(config["gnatdoc"]["version"], "26.0.0")

    def test_asset_inventory_names_the_pinned_revision(self):
        manifest = json.loads((ROOT / enhance_docs.ASSETS).read_text())
        self.assertEqual(manifest["enhancer_revision"], support.PINNED_REVISION)
        self.assertEqual(set(manifest["packaged_assets"]) | {"presentation.json"},
                         set(manifest["added_files"]))
        config = tomllib.loads((ROOT / enhance_docs.CONFIG).read_text())
        self.assertEqual(manifest["public_packages"], sorted(config["sources"]["packages"]))

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
        self.copy = Path(directory.name) / "site"
        shutil.copytree(self.site, self.copy)
        anchors = json.loads((ROOT / "docs/gnatdoc-native-anchors.json").read_text())
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
