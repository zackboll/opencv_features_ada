"""Regression checks for source ownership and workflow routing policy."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_repository import check_bridge_ownership
from workflow_topology import check_topology


class RepositoryTests(unittest.TestCase):
    def test_bridge_dependency_caches_are_not_vendoring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for prefix in ("alire", "tests/alire", "examples/alire"):
                bridge = root / prefix / "cache/pins/core/cpp/opencv_core_module_bridge.hpp"
                bridge.parent.mkdir(parents=True)
                bridge.write_text("dependency fixture")
            check_bridge_ownership(root)
            bridge = root / "cpp/opencv_core_module_bridge.hpp"
            bridge.parent.mkdir()
            bridge.write_text("vendored fixture")
            with self.assertRaisesRegex(ValueError, "do not vendor"):
                check_bridge_ownership(root)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = ROOT / ".github/workflows"
        self.cross = (directory / "cross-platform.yml").read_text()
        self.windows = (directory / "windows-post-merge.yml").read_text()
        self.compatibility = (directory / "opencv-compatibility.yml").read_text()

    def check(self, cross=None, windows=None, compatibility=None):
        check_topology(cross or self.cross, windows or self.windows,
                       compatibility or self.compatibility)

    def test_current_topology(self):
        self.check()

    def test_equivalent_formatting(self):
        for trigger in (
            '"on": {"push": {"branches": ["main"]}} # comment\n',
            "'on':\n    'push':\n        branches: ['main'] # comment\n",
            "on:\n   push: {branches: [main]}\n",
        ):
            with self.subTest(trigger=trigger):
                self.check(windows=trigger + "jobs:\n  windows:\n    runs-on: windows-latest\n")
        self.check(cross=self.cross.replace("  ", "    "))

    def test_forbidden_windows_events(self):
        for event in ("pull_request", "workflow_dispatch", "pull_request_target"):
            for trigger in (f"on:\n  push:\n    branches: [main]\n  {event}:\n",
                            f"on: {{push: {{branches: [main]}}, '{event}': {{}}}}\n"):
                with self.subTest(trigger=trigger), self.assertRaises(ValueError):
                    self.check(windows=trigger)

    def test_main_push_required(self):
        for trigger in ("on: push\n", "on: [push]\n", "on: workflow_dispatch\n",
                        "on: {push: {branches: [develop]}}\n",
                        "on: {push: {branches: [main, develop]}}\n",
                        "on: {push: {branches: [main], paths: [src/**]}}\n"):
            with self.subTest(trigger=trigger), self.assertRaises(ValueError):
                self.check(windows=trigger)

    def test_windows_pr_job_rejected_even_if_conditional(self):
        with self.assertRaises(ValueError):
            self.check(cross=self.cross + "  windows:\n    if: github.event_name == 'push'\n    runs-on: windows-latest\n")

    def test_windows_runner_or_matrix_rejected(self):
        for replacement in ("runs-on: windows-latest", "runs-on: [self-hosted, Windows]",
                            "runs-on: ${{ matrix.os }}"):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.check(cross=self.cross.replace("runs-on: ubuntu-24.04", replacement))
        with self.assertRaises(ValueError):
            self.check(cross=self.cross.replace("  linux:\n", "  linux:\n    strategy:\n      matrix:\n        os: [ubuntu-24.04, windows-latest]\n"))

    def test_manual_compatibility_only(self):
        with self.assertRaises(ValueError):
            self.check(compatibility=self.compatibility.replace("  workflow_dispatch:", "  pull_request:"))

    def test_ambiguous_or_unsupported_routing_fails_closed(self):
        for trigger in ("on: &events {push: {branches: [main]}}\n",
                        "on: {push: {branches: [main]}, push: {}}\n",
                        "on:\n  push:\n    branches: [main]\non: push\n"):
            with self.subTest(trigger=trigger), self.assertRaises(ValueError):
                self.check(windows=trigger)

    def test_step_scripts_are_opaque(self):
        self.check(cross=self.cross + "          on: pull_request\n          runs-on: windows-latest\n")


if __name__ == "__main__":
    unittest.main()