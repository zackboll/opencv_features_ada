"""Actual GPRinstall/link fixtures, not Windows DLL certification.

Run inside the built root's Alire environment. Uses the real Features GPR
with minimal Ada/C++ fixture sources and an externally prebuilt native shim.
"""
from pathlib import Path
import os
import shutil
import subprocess
import unittest

import test_external_shim_install as fixtures

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == "nt", "native Unix fixture; Windows uses the full post-merge qualifier")
class InstalledLinkMetadataTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalInstallTests(
            methodName="test_external_build_does_not_compile_duplicate_object")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.prebuild()
        config = self.root / "config/opencv_features_config.gpr"
        config.write_text(config.read_text().replace(
            'Build_Profile :=', 'Ada_Compiler_Switches := ();\nBuild_Profile :='))
        (self.root / "src/internal").mkdir(parents=True)
        (self.root / "src/install_probe.ads").write_text(
            'package Install_Probe is\nfunction Value return Integer;\nend Install_Probe;\n')
        (self.root / "src/install_probe.adb").write_text(
            'package body Install_Probe is\n'
            'function Native_Value return Integer\n'
            'with Import, Convention => C, External_Name => "features_install_probe";\n'
            'function Value return Integer is (Native_Value);\nend Install_Probe;\n')
        self.project = self.root / "opencv_features.gpr"
        self.corrected = (ROOT / "opencv_features.gpr").read_text()
        self.project.write_text(self.corrected)
        self.prefix = self.root / "prefix-a"

    def tool(self, name, *args, cwd=None, env=None):
        result = subprocess.run([name, *args], cwd=cwd or self.root,
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def install(self, kind):
        env = dict(os.environ, OPENCV_FEATURES_LIBRARY_TYPE=kind)
        self.tool("gprbuild", "-p", "-v", "-P", str(self.project), env=env)
        self.tool("gprinstall", "-f", "-p", "-r", f"--prefix={self.prefix}",
                  "-P", str(self.project), env=env)
        return self.prefix / "share/gpr/opencv_features.gpr"

    def test_predecessor_installs_absolute_source_linker_path(self):
        predecessor = self.corrected.replace(
            '("-lopencv_features_shim");',
            '("-L" & Project\'Project_Dir & "lib", "-lopencv_features_shim");')
        self.assertEqual(predecessor.count('Project\'Project_Dir & "lib"'), 2)
        self.project.write_text(predecessor)
        installed = self.install("static-pic").read_text()
        self.assertIn('-L' + str(self.root / "lib"), installed)
        self.assertIn("for Linker_Options", installed)
        print("Predecessor installed linker metadata:", installed)

    def test_corrected_install_and_relocation_link_both_library_kinds(self):
        for kind in ("static-pic", "relocatable"):
            with self.subTest(kind=kind):
                if self.prefix.exists():
                    shutil.rmtree(self.prefix)
                installed = self.install(kind).read_text()
                self.assertIn("library project", installed)
                self.assertIn('with "opencv_features_shim"', installed)
                self.assertIn('"-lopencv_features_shim"', installed)
                self.assertNotIn(str(self.root / "lib"), installed)
                self.assertNotIn('Project\'Project_Dir & "lib"', self.corrected)
                print(f"Corrected {kind} installed linker metadata:", installed)
                relocated = self.root / ("prefix-b-" + kind)
                self.prefix.rename(relocated)
                self.assertFalse(self.prefix.exists())
                # Remove all original library files: a stale -L cannot help.
                hidden = self.root / ("unavailable-lib-" + kind)
                (self.root / "lib").rename(hidden)
                try:
                    consumer = self.root / ("consumer-" + kind)
                    consumer.mkdir()
                    (consumer / "main.adb").write_text(
                        'with Install_Probe;\nprocedure Main is\nbegin\n'
                        'if Install_Probe.Value /= 37 then raise Program_Error; end if;\n'
                        'end Main;\n')
                    (consumer / "consumer.gpr").write_text(
                        'with "opencv_features";\nproject Consumer is\n'
                        'for Main use ("main.adb");\nfor Object_Dir use "obj";\n'
                        'package Linker is\nfor Driver use "gcc";\nend Linker;\n'
                        'end Consumer;\n')
                    env = dict(os.environ, GPR_PROJECT_PATH=str(relocated / "share/gpr"))
                    trace = self.tool("gprbuild", "-p", "-v", "-P", "consumer.gpr",
                                      cwd=consumer, env=env)
                    self.assertIn(str(relocated / "lib/opencv_features_shim"), trace)
                    self.assertNotIn(str(self.prefix), trace)
                    self.assertNotIn(str(self.root / "lib"), trace)
                    print(f"Relocated {kind} actual link trace:", trace)
                    runtime = ":".join(str(p) for p in (relocated / "lib").iterdir() if p.is_dir())
                    env.update(LD_LIBRARY_PATH=runtime, DYLD_LIBRARY_PATH=runtime)
                    self.tool(str(consumer / "obj/main"), cwd=consumer, env=env)
                    projects = self.tool("gprls", "-v", "-vP2", "-U", "-P", "consumer.gpr",
                                         cwd=consumer, env=env)
                    self.assertTrue(fixtures.source_directory_present(
                        relocated / "share/gpr", projects, fixtures.platform.system()), projects)
                finally:
                    hidden.rename(self.root / "lib")


if __name__ == "__main__":
    unittest.main()