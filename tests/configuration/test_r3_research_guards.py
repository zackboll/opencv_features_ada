"""Branch-only research additions must not become production/PR jobs."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_topology import check_topology


class ResearchGuards(unittest.TestCase):
    def test_guard_required(self):
        cross = (ROOT / '.github/workflows/cross-platform.yml').read_text()
        windows = (ROOT / '.github/workflows/windows-post-merge.yml').read_text()
        compatibility = (ROOT / '.github/workflows/opencv-compatibility.yml').read_text()
        check_topology(cross, windows, compatibility)
        for wrong in ("${{ true }}", "${{ github.event_name == 'workflow_dispatch' }}"):
            altered = cross.replace(
                "${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/research/011-r3-hosted-numerics' }}",
                wrong, 1)
            with self.assertRaisesRegex(ValueError, 'exact dispatch and branch guards'):
                check_topology(altered, windows, compatibility)