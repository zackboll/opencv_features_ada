"""Path-audit negative tests; native consumer qualification runs separately."""
from pathlib import Path
import sys
import tempfile
import unittest

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