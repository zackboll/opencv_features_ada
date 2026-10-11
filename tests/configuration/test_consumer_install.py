"""Path-audit negative tests; native consumer qualification runs separately."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from check_consumer_install import audit


class InstallAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="features-consumer.")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        (self.work / "core-source.txt").write_text(str(self.work / "candidate/core"))
        self.project = self.work / "relocated-longer-prefix-b/share/gpr/shim.gpr"
        self.project.parent.mkdir(parents=True)
        for mode, prefix in (("installed", "prefix-a"), ("relocated", "relocated-longer-prefix-b")):
            trace = "\n".join(str(self.work / prefix / sub) for sub in (
                "share/gpr/opencv_core.gpr", "share/gpr/opencv_features.gpr",
                "include/opencv_core/opencv-core.ads", "include/opencv_features/opencv-features.ads",
                "lib/opencv_core/libopencv_core_ada.a", "lib/opencv_features/libopencv_features_ada.a"))
            (self.work / f"{mode}-resolution.log").write_text(trace)

    def test_unused_build_provenance_is_not_a_lookup(self):
        self.project.write_text(f'Common_Cxx_Switches := ("-I{self.work}/candidate/core");\n')
        audit(self.work)

    def test_original_prefix_lookup_is_rejected(self):
        self.project.write_text(f'for Library_Dir use "{self.work}/prefix-a/lib";\n')
        with self.assertRaises(ValueError):
            audit(self.work)

    def test_source_library_linker_option_is_rejected(self):
        self.project.write_text(
            f'package Linker is\nfor Linker_Options use ("-L{self.work}/candidate/lib", '
            '"-lopencv_features_shim");\nend Linker;\n')
        with self.assertRaisesRegex(ValueError, "unreviewed source/original-prefix metadata"):
            audit(self.work)

    def test_removed_prefix_library_option_is_rejected(self):
        self.project.write_text(
            f'for Library_Options use ("-L{self.work}/prefix-a/lib", '
            '"-lopencv_features_shim");\n')
        with self.assertRaisesRegex(ValueError, "unreviewed source/original-prefix metadata"):
            audit(self.work)

    def test_source_include_used_by_compiler_is_rejected(self):
        self.project.write_text(f'Common_Cxx_Switches := ("-I{self.work}/candidate/core");\npackage Compiler is\n')
        with self.assertRaises(ValueError):
            audit(self.work)

    def test_trace_must_resolve_both_projects_and_libraries(self):
        path = self.work / "relocated-resolution.log"
        path.write_text(path.read_text().replace("lib/opencv_core/", "lib/other/"))
        with self.assertRaisesRegex(ValueError, "linked opencv_core"):
            audit(self.work)

    def test_source_in_actual_resolution_trace_is_rejected(self):
        path = self.work / "relocated-resolution.log"
        path.write_text(path.read_text() + f"\n{self.work}/candidate/lib\n")
        with self.assertRaisesRegex(ValueError, "resolution trace"):
            audit(self.work)

    def test_windows_separators_are_audited(self):
        for mode in ("installed", "relocated"):
            path = self.work / f"{mode}-resolution.log"
            path.write_text(path.read_text().replace("/", "\\"))
        audit(self.work)

    def test_windows_source_path_is_rejected(self):
        path = self.work / "relocated-resolution.log"
        path.write_text(path.read_text() + "\n" + str(self.work / "candidate/lib").replace("/", "\\"))
        with self.assertRaisesRegex(ValueError, "resolution trace"):
            audit(self.work)

    def test_removed_prefix_in_actual_trace_is_rejected(self):
        path = self.work / "relocated-resolution.log"
        path.write_text(path.read_text() + f"\n{self.work}/prefix-a/lib\n")
        with self.assertRaisesRegex(ValueError, "resolution trace"):
            audit(self.work)

    def rejected_record(self, record, source="build", mode="installed"):
        raw = self.work / f"{mode}-{source}.log"
        raw.write_text("before\n" + record + "\nafter\n")
        other = "projects" if source == "build" else "build"
        (self.work / f"{mode}-{other}.log").write_text("unrelated valid diagnostic\n")
        trace = self.work / f"{mode}-resolution.log"
        trace.write_text(trace.read_text() + "\n" + raw.read_text())
        with self.assertRaisesRegex(ValueError, "resolution trace") as caught:
            audit(self.work)
        evidence = (self.work / "path-audit-failure.log").read_text()
        self.assertIn(str(raw), evidence)
        self.assertIn("line 2", evidence)
        self.assertIn("Exact offending line: " + record, evidence)
        self.assertIn("1: before", evidence)
        self.assertIn("3: after", evidence)
        self.assertIn(evidence.strip(), str(caught.exception))
        self.assertEqual(raw.read_text(), "before\n" + record + "\nafter\n")
        return evidence

    def test_active_compiler_include_trace_rejected_with_provenance(self):
        evidence = self.rejected_record(f'gcc -c -I{self.work}/candidate/include main.adb')
        self.assertIn("GPRbuild", evidence)
        self.assertIn("compiler/linker command-shaped", evidence)

    def test_active_linker_source_trace_rejected_despite_valid_installed_paths(self):
        self.rejected_record(f'gcc main.o -L{self.work}/candidate/lib -lopencv_features_shim')

    def test_removed_prefix_linker_trace_rejected_with_provenance(self):
        self.rejected_record(f'gcc main.o -L{self.work}/prefix-a/lib', mode="relocated")

    def test_gprls_source_diagnostic_is_not_exempted(self):
        evidence = self.rejected_record(f'Processing project {self.work}/candidate/opencv_features.gpr',
                                        source="projects")
        self.assertIn("GPRls", evidence)
        self.assertIn("activity not yet established", evidence)

    def test_unknown_textual_diagnostic_is_not_exempted(self):
        self.rejected_record(f'Variable value: {self.work}/candidate')

    def test_valid_prefix_a_and_b_traces_pass(self):
        audit(self.work)
        self.assertFalse((self.work / "path-audit-failure.log").exists())

    def test_windows_drive_case_separator_and_short_parent_rejected(self):
        # Native Windows normalization, simulated here, is NOT certification.
        for parent in ('C:/Users/Runner/AppData/Local/Temp',
                       'c:/Users/RUNNER~1/AppData/Local/Temp', '/c/Users/RUNNER~1/Temp'):
            with self.subTest(parent=parent), patch('check_consumer_install.sys.platform', 'win32'):
                record = ('g++.exe -L' + parent + '/' + self.work.name.upper()
                          + '/CANDIDATE/lib').replace('/', '\\')
                self.rejected_record(record)
                # Reset combined fixture for the next spelling.
                path = self.work / "installed-resolution.log"
                path.write_text(path.read_text().split("\nbefore\n")[0])

    def test_windows_valid_drive_and_short_parent_lookups_pass(self):
        with patch('check_consumer_install.sys.platform', 'win32'):
            for mode in ("installed", "relocated"):
                path = self.work / f"{mode}-resolution.log"
                path.write_text(path.read_text().replace(str(self.work),
                    'C:/Users/RUNNER~1/Temp/' + self.work.name).upper().replace('/', '\\'))
            audit(self.work)