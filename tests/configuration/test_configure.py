"""Exercise build configuration with fixture metadata, not native OpenCV."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2]

class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="features configure ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        for name in ("configure_opencv.sh", "build_opencv_shim.sh"):
            shutil.copy(SOURCE / "scripts" / name, self.root / "scripts" / name)
        self.include = self.root / "native include"
        (self.include / "opencv2").mkdir(parents=True)
        for name in ("features.hpp", "features2d.hpp"):
            (self.include / "opencv2" / name).write_text("// test fixture only\n")
        self.lib = self.root / "native lib"
        self.lib.mkdir()
        self.core = self.root / "core crate"
        (self.core / "cpp").mkdir(parents=True)
        (self.core / "cpp/opencv_core_module_bridge.hpp").write_text("// fixture\n")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (bin_dir / "uname").write_text("#!/bin/sh\nprintf 'Linux\\n'\n")
        pkg = bin_dir / "pkg-config"
        pkg.write_text("""#!/bin/sh
case "$1" in
  --exists) test "$2" = "$FIXTURE_PACKAGE" ;;
  --modversion) printf '%s\\n' "$FIXTURE_VERSION" ;;
  --variable=includedir) test "${FIXTURE_LEGACY:-0}" = 1 || printf '%s\\n' "$FIXTURE_INCLUDE" ;;
  --variable=includedir_new) printf '%s\\n' "$FIXTURE_INCLUDE" ;;
  --variable=libdir) printf '%s\\n' "$FIXTURE_LIB" ;;
  *) exit 1 ;;
esac
""")
        for p in bin_dir.iterdir(): p.chmod(0o755)
        self.env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                        PKG_CONFIG=str(pkg), OPENCV_CORE_ALIRE_PREFIX=str(self.core),
                        FIXTURE_PACKAGE="opencv4", FIXTURE_VERSION="4.10.0",
                        FIXTURE_INCLUDE=str(self.include), FIXTURE_LIB=str(self.lib))
    def run_configure(self):
        return subprocess.run(["sh", "scripts/configure_opencv.sh"], cwd=self.root,
                              env=self.env, capture_output=True, text=True, check=False)
    def config(self):
        return (self.root / "config/opencv_features_install.gpr").read_text()
    def test_opencv4_source_bridge_and_space_paths(self):
        run = self.run_configure()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Native_Backend := "features2d";', self.config())
        self.assertIn(str(self.core / "cpp"), self.config())
    def test_opencv5(self):
        self.env.update(FIXTURE_PACKAGE="opencv5", FIXTURE_VERSION="5.0.0")
        run = self.run_configure()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('OpenCV_Features_Link_Option := "-lopencv_features";', self.config())
    def test_installed_bridge_preferred(self):
        (self.core / "include").mkdir()
        (self.core / "include/opencv_core_module_bridge.hpp").write_text("// installed fixture\n")
        self.assertEqual(self.run_configure().returncode, 0)
        self.assertIn(str(self.core / "include"), self.config())
    def test_legacy_include_metadata(self):
        self.env["FIXTURE_LEGACY"] = "1"
        self.assertEqual(self.run_configure().returncode, 0)
    def test_unsupported_versions(self):
        for version in ("4.0.0", "5.1.0", "6.0.0", "garbage"):
            with self.subTest(version=version):
                self.env["FIXTURE_VERSION"] = version
                self.assertNotEqual(self.run_configure().returncode, 0)
    def test_missing_core_prefix(self):
        del self.env["OPENCV_CORE_ALIRE_PREFIX"]
        self.assertNotEqual(self.run_configure().returncode, 0)
    def test_missing_header(self):
        (self.include / "opencv2/features2d.hpp").unlink()
        self.assertNotEqual(self.run_configure().returncode, 0)
    def test_missing_metadata(self):
        self.env["FIXTURE_PACKAGE"] = "unavailable"
        self.assertNotEqual(self.run_configure().returncode, 0)
    def test_missing_bridge(self):
        (self.core / "cpp/opencv_core_module_bridge.hpp").unlink()
        self.assertNotEqual(self.run_configure().returncode, 0)

if __name__ == "__main__": unittest.main()
