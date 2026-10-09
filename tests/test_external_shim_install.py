"""Real GPRinstall fixtures; synthetic Linux archives are not Windows coverage.

Run after alr build: alr exec -- python3 tests/test_external_shim_install.py -v
Kept outside configuration discovery, which needs no Ada toolchain.
"""
from pathlib import Path
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source_directory_present(expected, trace, system):
    """Match the complete directory, including its trailing separator.

    Darwin GPRls lowercases paths on the hosted case-insensitive filesystem.
    Do not apply that equivalence to case-sensitive Linux paths.
    """
    expected = str(expected).replace("\\", "/").rstrip("/") + "/"
    trace = trace.replace("\\", "/")
    if system in ("Darwin", "Windows"):
        expected, trace = expected.casefold(), trace.casefold()
    return expected in trace


class ExternalInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="features-external-gprinstall.")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("config", "cpp", "lib"):
            (self.root / directory).mkdir()
        (self.root / "opencv_core.gpr").write_text(
            'abstract project OpenCV_Core is end OpenCV_Core;\n')
        (self.root / "config/opencv_features_config.gpr").write_text(
            'abstract project OpenCV_Features_Config is\n'
            'Build_Profile := "development"; end OpenCV_Features_Config;\n')
        self.config = (ROOT / "config/opencv_features_install.gpr").read_text()
        self.project = self.root / "opencv_features_shim.gpr"
        self.original = (ROOT / "opencv_features_shim.gpr").read_text()
        self.project.write_text(self.original)
        self.mode("External_Relocatable")
        self.source = self.root / "cpp/probe.cpp"
        self.source.write_text('extern "C" int features_install_probe() { return 37; }\n')
        self.library = self.root / "lib" / (
            "libopencv_features_shim.dll" if os.name == "nt" else
            "libopencv_features_shim.dylib" if os.uname().sysname == "Darwin" else
            "libopencv_features_shim.so")
        self.archive = self.root / "lib/libopencv_features_shim.dll.a"

    def mode(self, mode):
        config = re.sub(r'Shim_Build : Shim_Build_Kind := "[^"]+";',
                        f'Shim_Build : Shim_Build_Kind := "{mode}";', self.config)
        (self.root / "config/opencv_features_install.gpr").write_text(config)

    def run_tool(self, tool, *args):
        return subprocess.run([tool, *args, "-P", str(self.project)],
                              cwd=self.root, text=True, capture_output=True)

    def install(self):
        return self.run_tool("gprinstall", "-f", "-p", "-r",
                             f"--prefix={self.root / 'prefix'}")

    def prebuild(self):
        driver = re.search(r'Cxx_Driver := "([^"]+)";', self.config)[1]
        command = [driver, "-shared", "-fPIC", str(self.source), "-o", str(self.library)]
        if sys.platform == "darwin":
            if self._testMethodName == "test_actual_external_library_and_archive_install":
                # Preserve one exact predecessor probe for diagnosis. Its
                # status is not an oracle; the corrected build below must pass.
                predecessor = subprocess.run(command, text=True, capture_output=True)
                print(f"Predecessor compiler command: {shlex.join(command)}\n"
                      f"exit: {predecessor.returncode}\nstdout:\n{predecessor.stdout}\n"
                      f"stderr:\n{predecessor.stderr}", flush=True)
            sysroot = re.search(r'Cxx_Sysroot := "([^"]*)";', self.config)[1]
            self.assertTrue(sysroot and Path(sysroot).is_dir(),
                            "Darwin fixture requires the configured Apple SDK")
            command = [driver, "-dynamiclib", "-isysroot", sysroot,
                       "-arch", platform.machine(), str(self.source),
                       "-o", str(self.library)]
        if os.name == "nt":
            command.append(f"-Wl,--out-implib,{self.archive}")
        result = subprocess.run(command, text=True, capture_output=True)
        diagnostics = (f"Compiler command: {shlex.join(command)}\n"
                       f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        # Display captured diagnostics in unittest failures rather than hiding
        # CalledProcessError.output/stderr. Successful Darwin commands also
        # record the selected compiler, SDK and native architecture in CI.
        if sys.platform == "darwin":
            print(diagnostics, flush=True)
        self.assertEqual(result.returncode, 0, diagnostics)
        if os.name != "nt":
            # Nonempty deterministic fixture, not a valid Windows import archive.
            self.archive.write_bytes(b"synthetic import archive copy fixture\x00\xff\n")
        # A stale static archive must not be selected instead of the shared one.
        (self.root / "lib/libopencv_features_shim.a").write_bytes(b"stale static archive")

    def test_previous_empty_language_is_rejected(self):
        self.project.write_text(self.original.replace(
            'for Externally_Built use "True";',
            'for Externally_Built use "True";\n'
            'for Languages use ();\nfor Source_Dirs use ();', 1))
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no language found, aborting", result.stdout + result.stderr)

    def test_language_without_real_sources_is_not_library(self):
        self.project.write_text(self.original.replace(
            'for Externally_Built use "True";',
            'for Externally_Built use "True";\nfor Source_Dirs use ();', 1))
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = self.root / "prefix/share/gpr/opencv_features_shim.gpr"
        self.assertIn("abstract project", installed.read_text())
        self.assertFalse((self.root / "prefix/lib/opencv_features_shim").exists())

    def test_actual_external_library_and_archive_install(self):
        self.prebuild()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = self.root / "prefix/lib/opencv_features_shim"
        for artifact in (self.library, self.archive):
            self.assertEqual(artifact.read_bytes(), (installed / artifact.name).read_bytes())
        self.assertFalse((installed / "libopencv_features_shim.a").exists())
        project = (self.root / "prefix/share/gpr/opencv_features_shim.gpr").read_text()
        self.assertIn("library project", project)
        self.assertNotIn("abstract project", project)
        self.assertIn('for Externally_Built use "True"', project)

    def test_missing_required_archive_fails(self):
        self.prebuild()
        self.archive.unlink()
        result = self.install()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("libopencv_features_shim.dll.a", result.stdout + result.stderr)

    def test_external_build_does_not_compile_duplicate_object(self):
        self.prebuild()
        result = self.run_tool("gprbuild", "-p", "-v")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(list((self.root / "obj").rglob("*.o")))
        self.assertFalse(list((self.root / "obj").rglob("*.obj")))

    def test_nonexternal_modes_remain_valid(self):
        for mode in ("Static_PIC", "Relocatable"):
            with self.subTest(mode=mode):
                self.mode(mode)
                # Configuration-only parse: Apple linkage cannot run on Linux,
                # nor can GNU/MSYS2 certify Apple libc++ or Windows DLLs.
                result = self.run_tool("gprls", "-v", "-U")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                trace = result.stdout + result.stderr
                self.assertTrue(source_directory_present(
                    self.root / "cpp", trace, platform.system()), trace)
                # Negative full-path oracle: neither a different unique
                # fixture nor a cpp-prefixed sibling can satisfy this check.
                for unrelated in (self.root.with_name(self.root.name + "-other") / "cpp",
                                  self.root / "cpp-other"):
                    with self.subTest(unrelated=unrelated):
                        self.assertFalse(source_directory_present(
                            self.root / "cpp", str(unrelated) + "/", platform.system()))
                self.assertTrue(source_directory_present(
                    self.root / "cpp", str(self.root / "cpp").lower() + "/", "Darwin"))


if __name__ == "__main__":
    unittest.main()