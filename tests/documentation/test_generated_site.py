"""Mutation tests against the actual generated native GNATdoc site.

Set FEATURES_DOCS_API (native api/ directory) and FEATURES_DOCS_LOG (GNATdoc
log) after running scripts/generate_docs.sh. The documentation workflow sets
both; when they are set, missing inputs fail instead of skipping.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_gnatdoc as check  # noqa: E402
import gnatdoc_native as native  # noqa: E402
import gnatdoc_source as source  # noqa: E402

API = os.environ.get("FEATURES_DOCS_API")
LOG = os.environ.get("FEATURES_DOCS_LOG")


@unittest.skipUnless(API and LOG, "set FEATURES_DOCS_API and FEATURES_DOCS_LOG")
class GeneratedSiteTests(unittest.TestCase):
    def setUp(self):
        self.api = Path(API)
        self.log = Path(LOG)
        self.assertTrue((self.api / "index.html").is_file(), "generated site is required")
        self.assertTrue(self.log.is_file(), "GNATdoc log is required")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.copy = Path(self.temporary.name) / "api"
        shutil.copytree(self.api, self.copy)
        self.pages = {p.package: p.file for p in native.read_site(self.api)[1].values()}

    def page(self, package="OpenCV.Features"):
        return self.copy / self.pages[package]

    def edit(self, path, old, new, count=1):
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, count))

    def site(self):
        return check.check_site(ROOT, self.copy, ROOT / check.ANCHORS, capture=False)

    def coverage(self, baseline=None, strict=False):
        return check.check_coverage(ROOT, self.copy, baseline or ROOT / check.COVERAGE,
                                    capture=False, strict=strict, report=None)

    def test_unmodified_site_passes_every_check(self):
        self.assertEqual(self.site()["sections"], 41)
        self.coverage()
        check.check_warnings(ROOT, self.log, ROOT / check.WARNINGS, capture=False,
                             strict=False, report=None)

    def test_changed_anchor_is_rejected(self):
        text = self.page().read_text()
        anchor = re.search(r"<h4 id=([0-9a-f]+)>", text)[1]
        self.page().write_text(text.replace(anchor, "0" * 64))
        with self.assertRaisesRegex(check.CheckError, "anchors"):
            self.site()

    def test_removed_declaration_section_is_rejected(self):
        text = self.page().read_text()
        match = re.search(r"<h4 id=([0-9a-f]+)>Count</h4>.*?(?=<h4 )", text, re.S)
        text = text.replace(match[0], "")
        text = re.sub(rf"<li><a href=#{match[1]}>Count</a>", "", text)
        self.page().write_text(text)
        with self.assertRaises(check.CheckError):
            self.site()

    def test_changed_rendered_signature_is_rejected(self):
        self.edit(self.page(), "function Count (Features : Feature_Set) return Natural",
                  "function Count (Features : Feature_Set) return Positive")
        with self.assertRaisesRegex(check.CheckError, "expected one native section"):
            self.site()

    def test_script_and_unknown_markup_are_rejected(self):
        self.edit(self.page(), "<h1>", "<script>alert(1)</script><h1>")
        with self.assertRaises(native.NativeError):
            self.site()

    def test_external_url_is_rejected(self):
        self.edit(self.page(), "<h2>Entities</h2>",
                  "<h2>Entities</h2><ul><li><a href=https://example.com/x>x</a></ul>")
        with self.assertRaises((check.CheckError, native.NativeError)):
            self.site()

    def test_extra_site_file_is_rejected(self):
        (self.copy / "extra.js").write_text("// unexpected")
        with self.assertRaisesRegex(check.CheckError, "file inventory"):
            self.site()

    def test_broken_fragment_is_rejected(self):
        text = self.page().read_text()
        anchor = re.search(r"<li><a href=#([0-9a-f]+)>", text)[1]
        self.page().write_text(text.replace(f"<li><a href=#{anchor}>",
                                            "<li><a href=#missing>", 1))
        with self.assertRaises(check.CheckError):
            self.site()

    def test_published_internal_package_is_rejected(self):
        index = self.copy / "index.html"
        shutil.copy(self.page(), self.copy / "internal.html")
        self.edit(self.copy / "internal.html", "<h1>OpenCV.Features</h1>",
                  "<h1>OpenCV.Features.Internal</h1>")
        self.edit(index, "</ul><h2 id=tagged-types>",
                  "<li><a href=internal.html target=document-content>OpenCV.Features.Internal"
                  "</a></ul><h2 id=tagged-types>")
        with self.assertRaises(check.CheckError):
            self.site()

    def test_modified_native_stylesheet_is_rejected(self):
        with (self.copy / "gnatdoc.css").open("a") as css:
            css.write("\nbody { color: red; }\n")
        with self.assertRaisesRegex(check.CheckError, "stylesheet_sha256"):
            self.site()

    def test_prose_without_attached_source_is_not_credited(self):
        self.edit(self.page(), "function Count (Features : Feature_Set) return Natural\n</code></pre>",
                  "function Count (Features : Feature_Set) return Natural\n</code></pre>"
                  "<p>Injected prose that has no source comment.")
        specs = source.specifications(ROOT)
        _, pages = native.read_site(self.copy)
        elements = check.coverage_elements(specs, pages, check.match_sections(specs, pages))
        count = next(e for e in elements if e["identity"].startswith("OpenCV.Features.Count|")
                     and e["identity"].endswith("|description"))
        declaration = next(d for d in specs["OpenCV.Features"].declarations
                           if d.name == "Count")
        expected = ("without an attached source block" if declaration.comment_start is None
                    else "differs from attached source")
        self.assertTrue(count["rendered"])
        self.assertFalse(count["documented"])
        self.assertIn(expected, count["reason"])

    def test_misrendered_prose_is_not_credited_and_is_a_new_gap(self):
        self.edit(self.page(), "<p>Explicit deep copy:", "<p>Altered deep copy:")
        with self.assertRaisesRegex(check.CheckError, "Descriptor_Copy"):
            self.coverage()

    def test_removed_native_member_is_rejected(self):
        self.edit(self.page(), "<dt>Hamming_2<dd>", "")
        with self.assertRaises(check.CheckError):
            self.coverage()

    def test_strict_mode_rejects_stale_baseline_entries(self):
        baseline = Path(self.temporary.name) / "baseline.txt"
        baseline.write_text((ROOT / check.COVERAGE).read_text() + "Fixed.Element|description\n")
        self.coverage(baseline)
        with self.assertRaisesRegex(check.CheckError, "stale"):
            self.coverage(baseline, strict=True)

    def test_new_and_unclassified_warnings_are_rejected(self):
        log = Path(self.temporary.name) / "gnatdoc.log"
        original = self.log.read_text()
        spec = source.specifications(ROOT)["OpenCV.Features"]
        declaration = next(d for d in spec.declarations if d.name == "Count")
        name = next(t for t in source.code(spec.tokens)
                    if t.line >= declaration.line and t.text == "Count")
        log.write_text(original + f"opencv-features.ads:{name.line}:{name.column}: "
                       "warning: invented warning\n")
        with self.assertRaisesRegex(check.CheckError, "new GNATdoc warnings"):
            check.check_warnings(ROOT, log, ROOT / check.WARNINGS, False, False, None)
        log.write_text(original + "gnatdoc: something unexpected\n")
        with self.assertRaisesRegex(check.CheckError, "unclassified"):
            check.check_warnings(ROOT, log, ROOT / check.WARNINGS, False, False, None)


class CreditTests(unittest.TestCase):
    def test_every_credit_reason(self):
        cases = (
            (("", "Attached prose here.", 3, False, True), "no rendered prose"),
            (("Rendered prose here.", "", 3, False, False),
             "rendered prose without an attached source block"),
            (("Shared prose here.", "Shared prose here.", 3, True, True),
             "source block is shared by the package description and a declaration"),
            (("Rendered prose here.", "Other prose here.", 3, False, True),
             "rendered prose differs from attached source"),
            (("Too short", "Too short", 3, False, True), "fewer than 3 words besides SPDX"),
        )
        for arguments, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(check._credit(*arguments),
                                 {"documented": False, "reason": reason})
        self.assertEqual(check._credit("Three words here.", "Three words here.", 3, False, True),
                         {"documented": True})


class SourceInventoryTests(unittest.TestCase):
    def copy_root(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        shutil.copytree(ROOT / "src", root / "src")
        (root / "docs").mkdir()
        shutil.copy(ROOT / check.DECLARATIONS, root / check.DECLARATIONS)
        return root

    def test_comment_only_change_keeps_the_declaration_inventory(self):
        root = self.copy_root()
        path = root / "src/opencv-features.ads"
        path.write_text(path.read_text().replace(
            "   function Count", "   --  Number of stored keypoints.\n   function Count"))
        check.check_inventory(root, root / check.DECLARATIONS, False, None)

    def test_declaration_change_is_rejected(self):
        root = self.copy_root()
        path = root / "src/opencv-features-orb.ads"
        path.write_text(path.read_text().replace(":= 500;", ":= 501;"))
        with self.assertRaisesRegex(check.CheckError, "removed: OpenCV.Features.ORB.Configuration"):
            check.check_inventory(root, root / check.DECLARATIONS, False, None)

    def test_new_public_unit_is_rejected(self):
        root = self.copy_root()
        (root / "src/opencv-features-extra.ads").write_text(
            "package OpenCV.Features.Extra is\n   procedure P;\nend OpenCV.Features.Extra;\n")
        with self.assertRaisesRegex(check.CheckError, "added: package OpenCV.Features.Extra"):
            check.check_inventory(root, root / check.DECLARATIONS, False, None)

    def test_capture_never_overwrites(self):
        root = self.copy_root()
        with self.assertRaisesRegex(check.CheckError, "only captured when absent"):
            check.check_inventory(root, root / check.DECLARATIONS, True, None)


if __name__ == "__main__":
    unittest.main()
