"""Unit tests for the source-backed GNATdoc declaration and comment model."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import gnatdoc_source as source  # noqa: E402


def parse_text(text: str, name: str = "src/demo.ads") -> source.Specification:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / name
        path.parent.mkdir(parents=True)
        path.write_text(text)
        return source.parse(path, root)


class LexerTests(unittest.TestCase):
    def test_comment_markers_inside_literals_are_not_comments(self):
        tokens = source.lex('X : constant String := "a -- b"; -- real\nC : Character := \'-\';')
        self.assertIn(("string", '"a -- b"'), [(t.kind, t.text) for t in tokens])
        self.assertEqual([t.text for t in tokens if t.kind == "comment"], [" real"])
        self.assertIn(("character", "'-'"), [(t.kind, t.text) for t in tokens])

    def test_attribute_tick_is_not_a_character_literal(self):
        tokens = source.lex("A'First'Image (X)")
        self.assertNotIn("character", [t.kind for t in tokens])

    def test_doubled_quote_in_string(self):
        tokens = source.lex('S := "say ""hi"" -- not comment";')
        self.assertEqual(sum(t.kind == "string" for t in tokens), 1)
        self.assertFalse(any(t.kind == "comment" for t in tokens))

    def test_compound_delimiters_and_based_numbers(self):
        texts = [t.text for t in source.lex("X := 16#FF# ** 2 .. 1.5E+3 => <> /= >=")]
        self.assertEqual(texts, ["X", ":=", "16#FF#", "**", "2", "..", "1.5E+3",
                                 "=>", "<>", "/=", ">="])

    def test_layout_independent_signature(self):
        one = source.code(source.lex("function F\n  (A : T;\n   B : U := (others => <>))\n   return R;"))
        two = source.code(source.lex("function F (A : T; B : U := (others => <>)) return R;"))
        self.assertEqual(source.code_signature(one), source.code_signature(two))
        self.assertEqual(source.code_signature(two),
                         "function F (A : T; B : U := (others => <>)) return R")


class ParserTests(unittest.TestCase):
    def test_supported_visible_forms_and_members(self):
        spec = parse_text("""with OpenCV.Core;
package Demo is
   type E is (A, B);
   type R is record
      X, Y : Integer := 0;
   end record;
   type L is tagged limited private;
   type D is range 0 .. 9;
   type V is array (Positive range <>) of R;
   function F (Left, Right : in out R; Mode : E := A) return OpenCV.Core.Mat;
   procedure P;
private
   type L is tagged limited null record;
end Demo;
""")
        self.assertEqual(spec.package, "Demo")
        self.assertEqual([d.category for d in spec.declarations],
                         ["enumeration", "record", "private", "range", "array", "subprogram",
                          "subprogram"])
        record = spec.declarations[1]
        self.assertEqual([(m.name, m.default) for m in record.members], [("X", "0"), ("Y", "0")])
        function = spec.declarations[5]
        self.assertEqual([(m.kind, m.name, m.mode, m.default) for m in function.members],
                         [("parameter", "Left", "in out", None),
                          ("parameter", "Right", "in out", None),
                          ("parameter", "Mode", "in", "A"),
                          ("return", None, None, None)])
        self.assertEqual(spec.private_line, 12)

    def test_unsupported_visible_constructs_fail_closed(self):
        for body in ("X : constant Integer := 1;",
                     "Failure : exception;",
                     "type D (N : Natural) is null record;",
                     "function F return Integer with Inline;",
                     "function F return Integer is (1);",
                     "procedure Q renames P;",
                     "generic procedure G;",
                     "package Nested is end Nested;",
                     "type N is new Integer;",
                     "type C is (Low, 'x');",
                     "pragma Preelaborate;"):
            with self.subTest(body=body), self.assertRaises(source.SourceError):
                parse_text(f"package Demo is\n   {body}\nend Demo;\n")

    def test_private_library_unit_under_src_is_rejected(self):
        with self.assertRaises(source.SourceError):
            parse_text("private package Demo is\nend Demo;\n")

    def test_internal_directory_units_are_classified_internal(self):
        spec = parse_text("package Demo.Internal is\n   X : Integer;\nend Demo.Internal;\n",
                          "src/internal/demo-internal.ads")
        self.assertEqual(spec.visibility, "internal")
        self.assertEqual(spec.declarations, [])


class CommentModelTests(unittest.TestCase):
    def test_block_after_is_is_the_package_description_and_is_shared(self):
        spec = parse_text("package Demo is\n   --  SPDX-License-Identifier: Apache-2.0\n"
                          "   type E is (A, B);\nend Demo;\n")
        self.assertEqual(spec.description_start, 2)
        self.assertEqual(spec.declarations[0].comment_start, 2)

    def test_block_above_package_used_when_is_is_followed_by_blank_line(self):
        spec = parse_text("with Ada.Text_IO;\n\n--  Demo description.\n\npackage Demo is\n\n"
                          "   --  SPDX-License-Identifier: Apache-2.0\n\n"
                          "   --  Enumeration.\n   type E is (A, B);\nend Demo;\n")
        self.assertEqual(spec.description_lines, ["Demo description."])
        self.assertEqual(spec.declarations[0].comment_lines, ["Enumeration."])

    def test_blank_line_breaks_declaration_attachment(self):
        spec = parse_text("package Demo is\n\n   --  Detached.\n\n   type E is (A, B);\nend Demo;\n")
        self.assertIsNone(spec.declarations[0].comment_start)

    def test_tags_split_and_continue(self):
        docs = source.split_tags(["Adds values.", "@param A First", "operand.",
                                  "@return The sum.", "@exception OpenCV_Error When invalid."])
        self.assertEqual(docs.description, "Adds values.")
        self.assertEqual(docs.tags[("param", "a")], "First operand.")
        self.assertEqual(docs.tags[("return", None)], "The sum.")
        self.assertEqual(docs.tags[("exception", "opencv_error")], "When invalid.")

    def test_duplicate_tags_are_reported(self):
        docs = source.split_tags(["@param A One.", "@param a Two."])
        self.assertEqual(docs.duplicates, [("param", "a")])

    def test_meaningful_is_a_word_floor_excluding_spdx(self):
        self.assertFalse(source.meaningful("SPDX-License-Identifier: Apache-2.0", 1))
        self.assertFalse(source.meaningful("Too short", 3))
        self.assertTrue(source.meaningful("Returns the count.", 3))


class RepositoryModelTests(unittest.TestCase):
    def test_actual_public_and_internal_units(self):
        specs = source.specifications(ROOT)
        public = sorted(n for n, s in specs.items() if s.visibility == "public")
        internal = sorted(n for n, s in specs.items() if s.visibility == "internal")
        self.assertEqual(public, ["OpenCV.Features", "OpenCV.Features.Correspondences",
                                  "OpenCV.Features.Matching", "OpenCV.Features.ORB"])
        self.assertEqual(internal, ["OpenCV.Features.Internal",
                                    "OpenCV.Features.Internal.C_API"])

    def test_ownership_sensitive_operations_are_mechanical(self):
        specs = source.specifications(ROOT)
        owned = source.ownership_types(specs)
        self.assertEqual(sorted(owned), ["Detector", "Feature_Set", "OpenCV.Core.Mat"])
        orb = {d.signature: d for d in specs["OpenCV.Features.ORB"].declarations}
        close = orb["procedure Close (Self : in out Detector)"]
        self.assertEqual(source.ownership_sensitive(close, owned),
                         ["in out Self: limited private type OpenCV.Features.ORB.Detector"])


if __name__ == "__main__":
    unittest.main()
