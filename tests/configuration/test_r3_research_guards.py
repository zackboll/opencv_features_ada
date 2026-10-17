"""Branch-only research additions must not become production/PR jobs."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_topology import check_topology


R3 = "${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/research/011-r3-hosted-numerics' }}"
R3E = "${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/research/011-r3e-native-correspondence' }}"


class ResearchGuards(unittest.TestCase):
    def setUp(self):
        self.cross = (ROOT / '.github/workflows/cross-platform.yml').read_text()
        self.windows = (ROOT / '.github/workflows/windows-post-merge.yml').read_text()
        self.compatibility = (ROOT / '.github/workflows/opencv-compatibility.yml').read_text()

    def check(self, cross=None):
        check_topology(self.cross if cross is None else cross, self.windows, self.compatibility)

    def test_current_jobs_are_exact(self):
        self.check()
        self.assertEqual(self.cross.count(R3), 2)
        self.assertEqual(self.cross.count(R3E), 2)
        self.assertNotIn('pull_request:', self.windows)

    def test_guard_required(self):
        for wrong in ("${{ true }}", "${{ github.event_name == 'workflow_dispatch' }}"):
            for guard in (R3, R3E):
                with self.subTest(guard=guard, wrong=wrong):
                    altered = self.cross.replace(guard, wrong, 1)
                    with self.assertRaisesRegex(ValueError, 'exact dispatch and branch guards'):
                        self.check(altered)

    def test_r3_jobs_do_not_follow_r3e(self):
        altered = self.cross.replace(R3, R3E, 1)
        with self.assertRaisesRegex(ValueError, 'exact dispatch and branch guards'):
            self.check(altered)

    def test_production_windows_job_still_rejected(self):
        with self.assertRaises(ValueError):
            self.check(self.cross + "  windows:\n    runs-on: windows-latest\n")


if __name__ == '__main__':
    unittest.main()
