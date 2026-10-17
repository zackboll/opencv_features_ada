"""Committed-tree fixtures for the documentation source-integrity boundary."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_doc_source_integrity as integrity  # noqa: E402

SPEC = """package Demo is
   --  Original comment.
   Text : constant String := "keep -- this";
   procedure P (X : Integer := 1);
end Demo;
"""


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        self.write("src/demo.ads", SPEC)
        self.write("cpp/shim.cpp", "int x;\n")
        self.write("docs/readme.md", "Docs\n")
        self.base = self.commit("base")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def compare(self):
        return integrity.compare(self.root, self.base, self.commit("change"))

    def test_comment_only_ada_change_and_documentation_pass(self):
        self.write("src/demo.ads", SPEC.replace("--  Original comment.",
                                                "--  Rewritten.\n   --  @param X Value."))
        self.write("docs/readme.md", "Better docs\n")
        self.write("docs/new.md", "New\n")
        result = self.compare()
        self.assertEqual(result["comment-only"], ["src/demo.ads"])
        self.assertEqual(result["documentation"], ["docs/readme.md"])
        self.assertEqual(result["added-documentation"], ["docs/new.md"])

    def test_string_literal_containing_comment_marker_is_protected(self):
        self.write("src/demo.ads", SPEC.replace('"keep -- this"', '"keep -- that"'))
        with self.assertRaisesRegex(integrity.IntegrityError, "tokens changed"):
            self.compare()

    def test_default_argument_change_is_rejected(self):
        self.write("src/demo.ads", SPEC.replace(":= 1", ":= 2"))
        with self.assertRaisesRegex(integrity.IntegrityError, "tokens changed"):
            self.compare()

    def test_production_bytes_additions_and_deletions_are_rejected(self):
        for mutate, message in (
                (lambda: self.write("cpp/shim.cpp", "int y;\n"), "production file changed"),
                (lambda: self.write("src/extra.ads", "package Extra is end Extra;\n"),
                 "added outside"),
                (lambda: (self.root / "cpp/shim.cpp").unlink(), "deleted")):
            with self.subTest(message=message):
                mutate()
                with self.assertRaisesRegex(integrity.IntegrityError, message):
                    self.compare()
                self.git("reset", "-q", "--hard", self.base)

    def test_uncommitted_changes_do_not_influence_the_committed_comparison(self):
        head = self.commit("no change")
        self.write("cpp/shim.cpp", "int changed_but_not_committed;\n")
        self.git("add", "cpp/shim.cpp")
        self.assertEqual(sum(map(len, integrity.compare(self.root, self.base, head).values())), 0)


if __name__ == "__main__":
    unittest.main()
