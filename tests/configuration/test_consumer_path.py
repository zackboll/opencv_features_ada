"""Value-based PATH fixtures; not native Windows certification."""
from pathlib import Path
import os
import posixpath
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from sanitize_consumer_path import sanitize, split_path, windows_canonical
import test_consumer_install


WORK = "C:/Users/runneradmin/AppData/Local/Temp/features-consumer.gBsRjJm7"
ROOTS = [WORK + "/candidate", WORK + "/features_clean_consumer",
         "D:/a/opencv_features_ada", WORK + "/prefix-a"]
# Realistic indexed checkout, not a hardcoded release or runner identity.
CORE = ("C:/Users/runneradmin/AppData/Local/alire/cache/builds/"
        "opencv_core_0.5.0_f8aef00c/"
        "f0441d76a402296da21d8c1fdb7cdf8741f80dbc21a43c18aead6e61e003889c")
GNAT = "C:/alire/toolchains/gnat_native/bin"
GPR = "C:/alire/toolchains/gprbuild/bin"
MSYS = "C:/alire/cache/msys64/mingw64/bin"


def canonical_fixture(path):
    path = path.replace("\\", "/")
    if len(path) > 2 and path[0] == "/" and path[2] == "/":
        path = path[1] + ":" + path[2:]
    # Explicit fixture alias, not production substring heuristics.
    path = path.replace("RUNNER~1", "runneradmin")
    return posixpath.normpath(path)


def shell_fixture(path):
    path = canonical_fixture(path)
    return "/" + path[0].lower() + path[2:]


def clean(value):
    return sanitize(value, ROOTS, True, canonical_fixture, shell_fixture)


def clean_indexed_core(value):
    return sanitize(value, ROOTS + [CORE], True, canonical_fixture, shell_fixture)


class ConsumerPathTests(unittest.TestCase):
    def test_native_semicolon_and_drive_letters(self):
        self.assertEqual(split_path(GNAT + ";" + GPR, True), [GNAT, GPR])
        self.assertEqual(clean(GNAT + ";" + GPR), shell_fixture(GNAT) + ":" + shell_fixture(GPR))

    def test_colon_drive_and_mixed_shell_entries(self):
        self.assertEqual(split_path(GNAT + ":/usr/bin:" + GPR, True), [GNAT, "/usr/bin", GPR])
        self.assertEqual(clean(GNAT + ":" + shell_fixture(GPR)),
                         shell_fixture(GNAT) + ":" + shell_fixture(GPR))

    def test_shell_source_entries(self):
        self.assertEqual(clean(shell_fixture(WORK + "/candidate/lib") + ":" + GNAT),
                         shell_fixture(GNAT))

    def test_posix(self):
        self.assertEqual(sanitize("/tmp/work/candidate/lib:/opt/gnat/bin:/usr/bin",
                                  ["/tmp/work/candidate"]), "/opt/gnat/bin:/usr/bin")

    def test_windows_case_and_slashes(self):
        source = (WORK + "/candidate/lib").upper().replace("/", "\\")
        self.assertEqual(clean(source + ";" + GNAT), shell_fixture(GNAT))

    def test_actual_short_parent_candidate_record(self):
        record = r"C:\Users\RUNNER~1\AppData\Local\Temp\features-consumer.gBsRjJm7\candidate\lib"
        self.assertEqual(clean(record + ";" + GNAT), shell_fixture(GNAT))

    def test_actual_core_pin_record(self):
        record = r"C:\Users\runneradmin\AppData\Local\Temp\features-consumer.gBsRjJm7\features_clean_consumer\alire\cache\pins\opencv_core_386c5360\lib"
        self.assertEqual(clean(record + ";" + GPR), shell_fixture(GPR))

    def test_preserves_selected_tools_and_independent_runtime(self):
        self.assertEqual(clean(";".join([GNAT, GPR, MSYS])),
                         ":".join(map(shell_fixture, [GNAT, GPR, MSYS])))

    def test_removed_prefix_a(self):
        self.assertEqual(clean(WORK + "/prefix-a/lib;" + GNAT), shell_fixture(GNAT))

    def test_component_boundary_not_word_filter(self):
        unrelated = [WORK + "/candidate-other/lib", WORK + "/prefix-ab/lib",
                     "C:/independent/features/opencv/candidate/bin"]
        self.assertEqual(clean(";".join(unrelated)), ":".join(map(shell_fixture, unrelated)))

    def test_repository_source(self):
        self.assertEqual(clean("D:/a/opencv_features_ada/lib;" + GNAT), shell_fixture(GNAT))

    def test_empty_and_all_removed(self):
        self.assertEqual(clean(";" + GNAT + ";"), shell_fixture(GNAT))
        with self.assertRaises(ValueError):
            clean(WORK + "/candidate/lib")

    def test_cygpath_long_absolute_mixed_conversion(self):
        with patch("sanitize_consumer_path.subprocess.check_output", return_value="C:/long/path\n") as call:
            self.assertEqual(windows_canonical("C:/SHORT~1"), "C:/long/path")
            call.assert_called_once_with(["cygpath", "-aml", "--", "C:/SHORT~1"], text=True)

    def test_cli_outputs_shell_path(self):
        with tempfile.TemporaryDirectory() as directory:
            captured = Path(directory) / "captured.txt"
            captured.write_text("/tmp/candidate/lib:/opt/gnat/bin:/usr/bin\n")
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2]
                                    / "scripts/sanitize_consumer_path.py"), str(captured),
                                    "--remove", "/tmp/candidate"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "/opt/gnat/bin:/usr/bin\n")

    def test_indexed_core_root_and_lib_are_removed(self):
        sibling = CORE + "b/lib"
        similar = ("C:/Users/runneradmin/AppData/Local/alire/cache/builds/"
                   "opencv_core_0.5.0_f8aef00c_other/lib")
        unrelated = "C:/independent/opencv_core_0.5.0/lib"
        native = ";".join([CORE, CORE + "/lib", sibling, similar, unrelated, GNAT, GPR, MSYS])
        self.assertEqual(clean_indexed_core(native),
                         ":".join(map(shell_fixture, [sibling, similar, unrelated, GNAT, GPR, MSYS])))
        shell = ":".join([shell_fixture(CORE + "/lib"), shell_fixture(GNAT),
                          shell_fixture(sibling), shell_fixture(MSYS)])
        self.assertEqual(clean_indexed_core(shell),
                         ":".join(map(shell_fixture, [GNAT, sibling, MSYS])))

    def test_indexed_core_windows_case_slashes_and_short_parent(self):
        mixed = (CORE + "/lib").upper().replace("/", "\\")
        short = (CORE + "/lib").replace("runneradmin", "RUNNER~1").replace("/", "\\")
        retained = ":".join(map(shell_fixture, [GNAT, GPR, MSYS]))
        self.assertEqual(clean_indexed_core(mixed + ";" + GNAT + ";" + GPR + ";" + MSYS), retained)
        self.assertEqual(clean_indexed_core(short + ";" + GNAT + ";" + GPR + ";" + MSYS), retained)

    def test_validator_passes_recorded_core_source_to_sanitizer(self):
        root = Path(__file__).resolve().parents[2]
        script = (root / "scripts/validate_clean_consumer.sh").read_text()
        start = script.index('test -s "$work/core-source.txt"')
        finish = script.index('> "$work/installed-toolchain-path.txt"')
        fragment = script[start:script.index("\n", finish)]
        self.assertIn('IFS= read -r core_source < "$work/core-source.txt"', fragment)
        self.assertIn('--remove "$core_source"', fragment)
        self.assertLess(script.index("sanitize_consumer_path.py"), script.index("hide_consumer_sources"))
        self.assertIn('MINGW*|MSYS*) set -- "$@" --windows', script)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            core = work / "alire/builds/opencv_core_0.5.0_f8aef00c/indexed-checkout"
            (core / "lib").mkdir(parents=True)
            for name in ("candidate", "features_clean_consumer", "prefix-a"):
                (work / name).mkdir()
            (work / "core-source.txt").write_bytes(str(core).encode() + b"\n")
            (work / "toolchain-path.txt").write_text(":".join([
                str(core), str(core / "lib"), str(core) + "b/lib",
                "/opt/gnat/bin", "/opt/gprbuild/bin", "/mingw64/bin"]) + "\n")
            env = os.environ.copy()
            env.update(work=str(work), python=sys.executable, source_root=str(root))
            result = subprocess.run(
                ["sh", "-eu", "-c", fragment, "fixture"],
                capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            retained = (work / "installed-toolchain-path.txt").read_text().rstrip("\n").split(":")
            self.assertEqual(retained, [str(core) + "b/lib", "/opt/gnat/bin",
                                        "/opt/gprbuild/bin", "/mingw64/bin"])

    def test_core_source_read_preserves_windows_backslashes(self):
        recorded = (r"C:\Users\runneradmin\AppData\Local\alire\cache\builds"
                    r"\opencv_core_0.5.0_f8aef00c\indexed-checkout")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "core-source.txt"
            source.write_bytes(recorded.encode() + b"\n")
            fragment = 'test -s "$1"; IFS= read -r core_source < "$1"; test -n "$core_source"; printf "%s" "$core_source"'
            result = subprocess.run(["sh", "-eu", "-c", fragment, "fixture", str(source)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, recorded)


class PathAuditTests(unittest.TestCase):
    def test_surviving_path_report_is_rejected(self):
        fixture = test_consumer_install.InstallAuditTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        trace = fixture.work / "installed-resolution.log"
        trace.write_text(trace.read_text() + "\nPATH =\n" + str(fixture.work / "candidate/lib"))
        with self.assertRaisesRegex(ValueError, "source/original prefix"):
            from check_consumer_install import audit
            audit(fixture.work)