"""Regression checks for source ownership and workflow routing policy."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_repository import check_bridge_ownership, check_correspondences, check_clean_consumer
from workflow_topology import check_topology


class RepositoryTests(unittest.TestCase):
    def test_clean_consumer_contract(self):
        check_clean_consumer(ROOT)

    def test_clean_consumer_rejects_private_packages_or_lookup(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / ".github", root / ".github")
            fixture = root / "scripts/features_clean_consumer.adb"
            original = fixture.read_text()
            for package in ("OpenCV.Features.Internal.C_API", "OpenCV.Features.Radius_Fixtures",
                            "OpenCV.Core.Module_Interop"):
                fixture.write_text(original + f"\nwith {package};\n")
                with self.subTest(package=package), self.assertRaises(ValueError):
                    check_clean_consumer(root)
            fixture.write_text(original)
            validator = root / "scripts/validate_clean_consumer.sh"
            validator.write_text(validator.read_text().replace("unset GPR_PROJECT_PATH", "unset OMITTED"))
            with self.assertRaisesRegex(ValueError, "unset inherited GPR_PROJECT_PATH"):
                check_clean_consumer(root)

    def test_each_consumer_workflow_stage_is_required(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / ".github", root / ".github")
            for name in ("cross-platform.yml", "windows-post-merge.yml"):
                path = root / ".github/workflows" / name
                original = path.read_text()
                count = original.count("run: sh scripts/validate_clean_consumer.sh")
                for index in range(count):
                    parts = original.split("run: sh scripts/validate_clean_consumer.sh")
                    path.write_text("run: sh scripts/validate_clean_consumer.sh".join(parts[:index + 1])
                                    + "run: echo omitted"
                                    + "run: sh scripts/validate_clean_consumer.sh".join(parts[index + 1:]))
                    with self.subTest(workflow=name, stage=index), self.assertRaises(ValueError):
                        check_clean_consumer(root)
                path.write_text(original)

    def test_correspondences_public_ada_boundary(self):
        check_correspondences(ROOT)

    def test_correspondences_reject_private_or_native_access(self):
        original = (ROOT / "src/opencv-features-correspondences.adb").read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src/opencv-features-correspondences.ads").write_text(
                (ROOT / "src/opencv-features-correspondences.ads").read_text())
            body = root / "src/opencv-features-correspondences.adb"
            for forbidden in ("Query.Points", "Train.Data", "Descriptor_Copy (Query)",
                              "Required_Norm (Train)", "pragma Import (C, X)",
                              "with OpenCV.Core.Module_Interop;", "with Interfaces;"):
                with self.subTest(forbidden=forbidden):
                    body.write_text(original + "\n" + forbidden)
                    with self.assertRaises(ValueError):
                        check_correspondences(root)

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

    def test_sanitizer_runner_must_be_linux(self):
        with self.assertRaises(ValueError):
            self.check(cross=self.cross.replace(
                "  linux-sanitizers:\n    runs-on: ubuntu-24.04",
                "  linux-sanitizers:\n    runs-on: windows-latest"))

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
        self.assertIn("-DWITH_ADE=OFF", self.compatibility)
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