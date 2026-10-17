"""R3E evidence must stay bounded and fail closed without installed ORB bytes."""
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'docs/research'))
from orb_r3e_harness import Harness


class NativeEvidence(unittest.TestCase):
    def test_probe_modes_and_no_large_matrix(self):
        source = (ROOT / 'docs/research/orb_r3e_native_probe.cpp').read_text()
        for required in ('detectAndCompute', 'setUseOpenCL(false)', 'haveOpenCL',
                         'LOADED ', 'PASS R3E fixed powers', 'for (int level = 1; level <= 8'):
            self.assertIn(required, source)
        self.assertNotIn('151547', source)
        self.assertNotIn('orb_levels_probe', source)

    def test_loaded_features_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = Harness(directory)
            self.assertIsNone(harness.features_library('LOADED /tmp/libopencv_core.dylib\n'))
            selected = harness.features_library(
                'LOADED /opt/opencv/lib/libopencv_features.5.0.0.dylib\n')
            self.assertTrue(selected.endswith('libopencv_features.5.0.0.dylib'))

    def test_missing_orb_source_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = Harness(directory)
            harness.source_search([directory])
            text = (Path(directory) / 'source/orb-cpp.txt').read_text()
            self.assertIn('SOURCE_BYTES_UNAVAILABLE', text)

    def test_manifest_records_probe_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            harness = Harness(directory)
            harness.note('probe/example.txt', 'PASS native ORB extraction\n')
            harness.first_failure = dict(label='probe/cpu', exit_status=1)
            self.assertEqual(harness.manifest(1), 1)
            manifest = (Path(directory) / 'manifest.json').read_text()
            self.assertIn('NATIVE_CORRESPONDENCE_PENDING', manifest)
            self.assertIn('probe/example.txt', manifest)

    def test_runner_syntax(self):
        script = ROOT / 'docs/research/run_orb_r3e.sh'
        subprocess.run(['sh', '-n', script], check=True)
        probe = ROOT / 'docs/research/orb_r3e_native_probe.cpp'
        self.assertNotIn('orb_levels_probe', textwrap.dedent(probe.read_text()))


if __name__ == '__main__':
    unittest.main()
