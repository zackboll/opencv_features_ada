"""Strict zero-gap, zero-warning GNATdoc qualification (DOC-006).

Unit tests always run. Real-site tests need FEATURES_DOCS_API and
FEATURES_DOCS_LOG from scripts/generate_docs.sh; when they are set, missing
inputs fail instead of skipping. End-to-end tests additionally need
FEATURES_DOCS_END_TO_END=1 and GNATDOC_PREFIX: they copy the tracked files into
a temporary directory, remove documentation there and run the real generator.

Every mutation happens in an isolated copy; the tests verify that the
repository sources, baselines and the generated site and log are unchanged.
"""
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
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
END_TO_END = os.environ.get("FEATURES_DOCS_END_TO_END") == "1"

PACKAGES = ["OpenCV.Features", "OpenCV.Features.Correspondences",
            "OpenCV.Features.Matching", "OpenCV.Features.ORB"]
COUNT = "OpenCV.Features.Count|function|function Count (Features : Feature_Set) return Natural"
COUNT_WARNING = ("opencv-features.ads: OpenCV.Features.Count: function Count "
                 "(Features : Feature_Set) return Natural: ")
POINT = ("OpenCV.Features.Point|function|function Point (Features : Feature_Set; "
         "Index : Positive) return Keypoint")
POINT_WARNING = ("opencv-features.ads: OpenCV.Features.Point: function Point "
                 "(Features : Feature_Set; Index : Positive) return Keypoint: ")
# Entries of the DOC-001 baselines that DOC-002 resolved; DOC-006 removed them.
OBSOLETE_GAP = f"{COUNT}|description"
OBSOLETE_WARNING = COUNT_WARNING + "entity `Count` is not documented"


def digest(path: Path) -> str:
    if path.is_dir():
        return hashlib.sha256(b"".join(
            p.relative_to(path).as_posix().encode() + b"\0" + p.read_bytes()
            for p in sorted(path.rglob("*")) if p.is_file())).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checker(*arguments: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = check.main(list(arguments))
    return code, out.getvalue(), err.getvalue()


def results(stdout: str) -> dict:
    return {m[1]: json.loads(m[2]) for m in re.finditer(r"^PASS (\w+): (\{.*\})$", stdout, re.M)}


class StrictConfigurationTests(unittest.TestCase):
    def test_allowed_gap_and_warning_baselines_are_tracked_and_empty(self):
        for name in (check.COVERAGE, check.WARNINGS):
            with self.subTest(baseline=name):
                path = ROOT / name
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), b"")
                subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", name],
                               check=True, capture_output=True)

    def test_standard_generation_invokes_the_strict_checker(self):
        text = (ROOT / "scripts/generate_docs.sh").read_text()
        code = re.sub(r"\\\n\s*", " ", "\n".join(line for line in text.splitlines()
                                                 if not line.lstrip().startswith("#")))
        calls = [line.split() for line in code.splitlines() if "check_gnatdoc.py" in line]
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(calls[0], ["python3", "scripts/check_gnatdoc.py", "all", "--strict",
                                    "--api", '"$output/api"', "--log", '"$log"'])

    def test_documentation_workflow_runs_the_standard_generator(self):
        workflow = (ROOT / ".github/workflows/documentation.yml").read_text()
        steps = re.findall(r"- name: (.*)\n((?:        .*\n)+)", workflow)
        generate = [body for name, body in steps
                    if name == "Generate native site and run Features-owned checks"]
        self.assertEqual(len(generate), 1)
        self.assertIn("run: sh scripts/generate_docs.sh\n", generate[0])
        regenerate = [body for name, body in steps if name.startswith("Qualify deterministic")]
        self.assertIn('sh scripts/generate_docs.sh "$RUNNER_TEMP/docs-second"', regenerate[0])
        self.assertNotIn("check_gnatdoc.py all", workflow)

    def test_capture_cannot_regenerate_existing_empty_baselines(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.txt"
            baseline.write_bytes(b"")
            with self.assertRaisesRegex(check.CheckError, "only captured when absent"):
                check._write_absent(baseline, "anything\n")
            self.assertEqual(baseline.read_bytes(), b"")


@unittest.skipUnless(API and LOG, "set FEATURES_DOCS_API and FEATURES_DOCS_LOG")
class StrictRealSiteTests(unittest.TestCase):
    """Strict checker runs against isolated copies of the real generated output."""

    def setUp(self):
        self.api, self.log = Path(API), Path(LOG)
        self.assertTrue((self.api / "index.html").is_file(), "generated site is required")
        self.assertTrue(self.log.is_file(), "GNATdoc log is required")
        protected = [self.api, self.log, ROOT / "src", ROOT / check.COVERAGE,
                     ROOT / check.WARNINGS, ROOT / check.DECLARATIONS, ROOT / check.ANCHORS]
        before = {path: digest(path) for path in protected}
        self.addCleanup(lambda: self.assertEqual(
            {path: digest(path) for path in protected}, before, "original files changed"))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        work = Path(temporary.name)
        self.root = work / "root"
        shutil.copytree(ROOT / "src", self.root / "src")
        (self.root / "docs").mkdir()
        for name in (check.DECLARATIONS, check.ANCHORS, check.COVERAGE, check.WARNINGS):
            shutil.copy(ROOT / name, self.root / name)
        self.copy = work / "api"
        shutil.copytree(self.api, self.copy)
        self.copy_log = work / "gnatdoc.log"
        shutil.copy(self.log, self.copy_log)
        self.reports = work / "reports"
        pages = native.read_site(self.api)[1]
        self.page = self.copy / pages["OpenCV.Features"].file

    def strict(self, strict=True):
        return run_checker("all", *(["--strict"] if strict else []), "--root", str(self.root),
                           "--api", str(self.copy), "--log", str(self.copy_log),
                           "--reports", str(self.reports))

    def edit(self, path, old, new):
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1))

    def test_real_site_is_strictly_zero_gap_and_zero_warning(self):
        code, out, err = self.strict()
        self.assertEqual(code, 0, err)
        report = results(out)
        self.assertEqual(report["inventory"], {"declarations": 41, "internal_units": 2,
                                               "packages": 4})
        self.assertEqual(report["site"]["sections"], 41)
        self.assertEqual(report["site"]["packages"], 4)
        self.assertEqual((report["warnings"]["raw"], report["warnings"]["baseline"],
                          report["warnings"]["new"], report["warnings"]["stale"]), (0, 0, [], []))
        self.assertEqual(report["coverage"]["total"], {"documented": 137, "elements": 137,
                                                       "percent": 100.0, "rendered": 137})
        self.assertEqual((report["coverage"]["baseline"], report["coverage"]["new_gaps"],
                          report["coverage"]["stale_baseline"]), (0, [], []))

    def test_exactly_four_packages_and_41_preserved_declarations(self):
        specs = source.specifications(ROOT)
        index, pages = native.read_site(self.api)
        self.assertEqual(sorted(name for name, _ in index.units), PACKAGES)
        self.assertEqual(sorted(check.public(specs)), PACKAGES)
        matched = check.match_sections(specs, pages)
        self.assertEqual(len(matched), 41)
        recorded = json.loads((ROOT / check.DECLARATIONS).read_text())
        self.assertEqual(sum(len(p["declarations"]) for p in
                             recorded["public_packages"].values()), 41)
        elements = check.coverage_elements(specs, pages, matched)
        self.assertEqual(len(elements), 137)
        self.assertEqual([e["identity"] for e in elements if not e["documented"]], [])
        self.assertEqual(check.warning_identities(self.log.read_text(), specs), [])

    def test_removed_declaration_documentation_fails(self):
        self.edit(self.page, "<p>Number of keypoints, equal to the number of descriptor rows.",
                  "<p>")
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn("new documentation gaps", err)
        self.assertIn(f"{COUNT}|description", err)

    def test_new_recognized_warning_fails(self):
        spec = source.specifications(ROOT)["OpenCV.Features"]
        declaration = next(d for d in spec.declarations if d.name == "Count")
        name = next(t for t in source.code(spec.tokens)
                    if t.line >= declaration.line and t.text == "Count")
        with self.copy_log.open("a") as log:
            log.write(f"opencv-features.ads:{name.line}:{name.column}: "
                      "warning: entity `Count` is not documented\n")
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn("new GNATdoc warnings", err)
        self.assertIn(OBSOLETE_WARNING, err)

    def test_restored_obsolete_gap_entry_fails_only_under_strict(self):
        (self.root / check.COVERAGE).write_text(OBSOLETE_GAP + "\n")
        self.assertEqual(self.strict(strict=False)[0], 0)
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn("stale coverage baseline entries", err)
        self.assertIn(OBSOLETE_GAP, err)

    def test_restored_obsolete_warning_entry_fails_only_under_strict(self):
        (self.root / check.WARNINGS).write_text(OBSOLETE_WARNING + "\n")
        self.assertEqual(self.strict(strict=False)[0], 0)
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn("stale warning baseline entries", err)
        self.assertIn(OBSOLETE_WARNING, err)

    def test_missing_public_native_declaration_fails(self):
        text = self.page.read_text()
        section = re.search(r"<h4 id=([0-9a-f]+)>Count</h4>.*?(?=<h4 )", text, re.S)
        text = text.replace(section[0], "").replace(f"<li><a href=#{section[1]}>Count</a>", "")
        self.page.write_text(text)
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn(f"{COUNT}: expected one native section, found 0", err)

    def test_changed_native_anchor_fails(self):
        text = self.page.read_text()
        anchor = re.search(r"<h4 id=([0-9a-f]+)>Count</h4>", text)[1]
        self.page.write_text(text.replace(anchor, "f" * 64))
        code, _, err = self.strict()
        self.assertEqual(code, 1)
        self.assertIn("native anchors/identities changed", err)
        self.assertIn(COUNT, err)


@unittest.skipUnless(END_TO_END, "set FEATURES_DOCS_END_TO_END=1 to regenerate in a copy")
class StrictEndToEndTests(unittest.TestCase):
    """Remove documentation in an isolated copy and run the real generator."""

    @classmethod
    def setUpClass(cls):
        if not os.environ.get("GNATDOC_PREFIX"):
            raise AssertionError("GNATDOC_PREFIX is required for end-to-end tests")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.temporary.name) / "repo"
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], check=True,
                                 capture_output=True).stdout.split(b"\0")
        for name in filter(None, (t.decode() for t in tracked)):
            target = cls.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        subprocess.run(["alr", "-n", "build", "--stop-after=pre-build"], cwd=cls.repo,
                       check=True, capture_output=True)
        cls.output = 0

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        protected = [ROOT / "src", ROOT / check.COVERAGE, ROOT / check.WARNINGS]
        before = {path: digest(path) for path in protected}
        self.addCleanup(lambda: self.assertEqual(
            {path: digest(path) for path in protected}, before, "original files changed"))

    def generate(self, old: str, new: str = "") -> tuple[subprocess.CompletedProcess, Path]:
        """Replace one unique documentation block in the copy and regenerate."""
        spec = self.repo / "src/opencv-features.ads"
        original = spec.read_text()
        self.assertEqual(original.count(old), 1, "documentation block is not unique")
        spec.write_text(original.replace(old, new))
        type(self).output += 1
        output = self.repo.parent / f"site-{self.output}"
        try:
            result = subprocess.run(["sh", "scripts/generate_docs.sh", str(output)],
                                    cwd=self.repo, capture_output=True, text=True)
            return result, output
        finally:
            spec.write_text(original)

    def coverage_gaps(self, output: Path) -> str:
        with self.assertRaises(check.CheckError) as failure:
            check.check_coverage(self.repo, output / "api", self.repo / check.COVERAGE,
                                 capture=False, strict=True, report=None)
        return str(failure.exception)

    def test_removed_declaration_comment_fails_real_generation(self):
        result, output = self.generate(
            "   --  Number of keypoints, equal to the number of descriptor rows. This is\n"
            "   --  the actual produced count: it can be zero and is not bounded by a\n"
            "   --  detector's requested feature target.\n"
            "   --  @param Features Feature set to inspect.\n"
            "   --  @return Number of stored keypoints.\n"
            "   function Count", "   function Count")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL warnings: new GNATdoc warnings", result.stderr)
        for message in ("entity `Count` is not documented",
                        "parameter `Features` is not documented",
                        "return value is not documented"):
            self.assertIn(COUNT_WARNING + message, result.stderr)
        gaps = self.coverage_gaps(output)
        for suffix in ("description", "parameter:Features", "return"):
            self.assertIn(f"{COUNT}|{suffix}", gaps)

    def test_removed_parameter_tag_fails_real_generation(self):
        result, output = self.generate(
            "   --  @param Index One-based keypoint index in 1 .. Count (Features).\n"
            "   --  @return The keypoint value stored at Index.\n",
            "   --  @return The keypoint value stored at Index.\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(POINT_WARNING + "parameter `Index` is not documented", result.stderr)
        self.assertIn(f"{POINT}|parameter:Index", self.coverage_gaps(output))

if __name__ == "__main__":
    unittest.main()
