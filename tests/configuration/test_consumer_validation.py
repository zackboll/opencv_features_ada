"""Deterministic qualifier regressions, not native Windows certification."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPERS = ROOT / "scripts/consumer_validation_helpers.sh"


class ConsumerValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def shell(self, command, *args, env=None):
        return subprocess.run(
            ["sh", "-eu", "-c", '. "$1"; shift; ' + command,
             "fixture", str(HELPERS), *map(str, args)],
            capture_output=True, text=True, env=env)

    def pe(self, names):
        log = self.work / "pe.log"
        log.write_text("\n".join("\tDLL Name: " + name for name in names))
        return self.shell('check_features_pe_imports "$1"', log)

    def test_native_features_and_core_shim_without_direct_core(self):
        for backend in ("libopencv_features-500.dll", "libopencv_features2d410.dll"):
            with self.subTest(backend=backend):
                result = self.pe([backend, "libopencv_core_shim.dll"])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_core_shim_rejected(self):
        self.assertNotEqual(self.pe(["libopencv_features-500.dll", "libopencv_core500.dll"]).returncode, 0)

    def test_missing_native_features_rejected(self):
        self.assertNotEqual(self.pe(["libopencv_core_shim.dll"]).returncode, 0)

    def test_windows_case_variation(self):
        result = self.pe(["LiBoPeNcV_FeAtUrEs-500.DLL", "LIBOPENCV_CORE_SHIM.DLL"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_names_rejected(self):
        for names in (
            ["libopencv_features_shim.dll", "libopencv_core_shim.dll"],
            ["other_libopencv_features-500.dll", "libopencv_core_shim.dll"],
            ["libopencv_features-500.dll.extra", "libopencv_core_shim.dll"],
            ["libopencv_features-500.dll", "other_libopencv_core_shim.dll"],
            ["libopencv_features-500.dll", "libopencv_core_shim.dll.extra"],
        ):
            with self.subTest(names=names):
                self.assertNotEqual(self.pe(names).returncode, 0)

    def test_source_rename_leaves_valid_cwd_and_sorted_inventory(self):
        for name in ("candidate", "features_clean_consumer", "prefix-a"):
            (self.work / name).mkdir()
        for name in ("z.dll", "a.dll"):
            (self.work / "prefix-a" / name).touch()
        result = self.shell(
            'cd "$1/features_clean_consumer"; hide_consumer_sources "$1"; '
            'test "$(pwd -P)" = "$(cd "$1" && pwd -P)"; '
            'collect_consumer_inventory "$1/inventory" "$1/prefix-a" -type f', self.work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.work / "features_clean_consumer").exists())
        lines = (self.work / "inventory").read_text().splitlines()
        self.assertEqual(lines, sorted(str(self.work / "prefix-a" / n) for n in ("z.dll", "a.dll")))

    def test_failed_find_cannot_be_masked_by_sort(self):
        tools = self.work / "tools"
        tools.mkdir()
        find = tools / "find"
        find.write_text('#!/bin/sh\nprintf "partial evidence\\n"\necho "find fixture failure" >&2\nexit 1\n')
        find.chmod(0o755)
        env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"])
        result = self.shell(
            'collect_consumer_inventory "$1/inventory" "$1"; echo FALSE_SUCCESS', self.work, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("find fixture failure", result.stderr)
        self.assertNotIn("FALSE_SUCCESS", result.stdout)
        self.assertEqual((self.work / "inventory.raw").read_text(), "partial evidence\n")
        self.assertFalse((self.work / "inventory").exists())

    def test_installer_rejects_bad_core_before_writing_prefix_evidence(self):
        script = (ROOT / "scripts/validate_clean_consumer.sh").read_text()
        installer = (ROOT / "scripts/install_resolved_consumer.sh").read_text()
        self.assertIn('sh "$work/candidate/scripts/install_resolved_consumer.sh"', script)
        self.assertNotIn("sh -c", script)
        self.assertNotIn("\\\\", installer)
        self.assertIn('grep -E \'^version *= *"0\\.5\\.0"\'', installer)
        cases = (
            ("wrong-version", 'name = "opencv_core"\nversion = "0.4.1"\n', False),
            ("missing-manifest", None, False),
            ("workspace-pin", 'name = "opencv_core"\nversion = "0.5.0"\n', True),
        )
        for name, manifest, pin in cases:
            with self.subTest(name=name):
                case = self.work / name
                case.mkdir()
                core = case / ("candidate" if pin else "core with space")
                core.mkdir()
                if manifest is not None:
                    (core / "alire.toml").write_text(manifest)
                (core / "opencv_core.gpr").write_text("project OpenCV_Core is\nend OpenCV_Core;\n")
                (case / "candidate/opencv_features.gpr").parent.mkdir(exist_ok=True)
                (case / "candidate/opencv_features.gpr").write_text(
                    "project OpenCV_Features is\nend OpenCV_Features;\n")
                before = set(case.iterdir())
                result = subprocess.run(
                    ["sh", str(ROOT / "scripts/install_resolved_consumer.sh"), str(case)],
                    capture_output=True, text=True,
                    env={**os.environ, "OPENCV_CORE_ALIRE_PREFIX": str(core)})
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("unexpected EOF", result.stdout + result.stderr)
                self.assertFalse((case / "core-source.txt").exists())
                self.assertEqual(set(case.iterdir()), before)

    def test_installer_preserves_each_gprinstall_failure(self):
        for failing in ("opencv_core.gpr", "opencv_features.gpr"):
            with self.subTest(failing=failing):
                case = self.work / failing
                tools = case / "tools"
                tools.mkdir(parents=True)
                (tools / "gprinstall").write_text(
                    "#!/bin/sh\n"
                    "printf '%s\\n' \"$*\" >&2\n"
                    "for argument; do\n"
                    "    case \"$argument\" in\n"
                    f"*{failing}) exit 7 ;;\n"
                    "    esac\n"
                    "done\n"
                    "exit 0\n")
                (tools / "gprinstall").chmod(0o755)
                core = case / "core with space"
                core.mkdir()
                (core / "alire.toml").write_text(
                    "name = \"opencv_core\"\nversion = \"0.5.0\"\n")
                (core / "opencv_core.gpr").write_text(
                    "project OpenCV_Core is\nend OpenCV_Core;\n")
                (case / "candidate").mkdir()
                (case / "candidate/opencv_features.gpr").write_text(
                    "project OpenCV_Features is\nend OpenCV_Features;\n")
                env = os.environ.copy()
                env["OPENCV_CORE_ALIRE_PREFIX"] = str(core)
                env["PATH"] = str(tools) + os.pathsep + env["PATH"]
                result = subprocess.run(
                    ["sh", str(ROOT / "scripts/install_resolved_consumer.sh"), str(case)],
                    capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                self.assertIn(failing, result.stderr)
                self.assertIn("version = \"0.5.0\"", result.stdout)
                self.assertTrue((case / "core-source.txt").is_file())

    def test_windows_style_evidence_path_is_not_a_quote_failure(self):
        tools = self.work / "windows-tools"
        tools.mkdir()
        (tools / "gprinstall").write_text("#!/bin/sh\nexit 0\n")
        (tools / "gprinstall").chmod(0o755)
        core = self.work / "windows core"
        core.mkdir()
        (core / "alire.toml").write_text(
            "name = \"opencv_core\"\nversion = \"0.5.0\"\n")
        (core / "opencv_core.gpr").write_text(
            "project OpenCV_Core is\nend OpenCV_Core;\n")
        (self.work / "candidate").mkdir()
        (self.work / "candidate/opencv_features.gpr").write_text(
            "project OpenCV_Features is\nend OpenCV_Features;\n")
        env = os.environ.copy()
        env["OPENCV_CORE_ALIRE_PREFIX"] = str(core)
        env["PATH"] = str(tools) + os.pathsep + env["PATH"]
        result = subprocess.run(
            ["sh", str(ROOT / "scripts/install_resolved_consumer.sh"),
             "C:\\Program Files\\features-consumer"],
            capture_output=True, text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("version = \"0.5.0\"", result.stdout)
        self.assertNotIn("unexpected EOF", result.stdout + result.stderr)

    def test_qualifier_uses_checked_helpers(self):
        script = (ROOT / "scripts/validate_clean_consumer.sh").read_text()
        self.assertIn('hide_consumer_sources "$work"', script)
        self.assertIn('check_features_pe_imports "$work/installed-features-pe.log"', script)
        self.assertNotRegex(script, r'find "\$prefix[^\n]*\|')
        self.assertNotIn("opencv_core[0-9]", script)

    def test_failure_artifact_is_narrow_and_post_merge_only(self):
        workflow = (ROOT / ".github/workflows/windows-post-merge.yml").read_text()
        self.assertIn("branches:\n      - main", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("failure() && steps.consumer.outcome == 'failure'", workflow)
        artifact = workflow.split("uses: actions/upload-artifact@v4", 1)[1]
        self.assertIn("/installed-projects.log", artifact)
        self.assertIn("/installed-build.log", artifact)
        self.assertIn("/install.log", artifact)
        self.assertIn("/relocated-resolution.log", artifact)
        self.assertIn("/path-audit-failure.log", artifact)
        for excluded in ("resolved-environment.log", "toolchain-path.txt", "/**\n", "continue-on-error"):
            self.assertNotIn(excluded, artifact)

    def test_ci_evidence_output_does_not_change_local_directory_selection(self):
        script = (ROOT / "scripts/validate_clean_consumer.sh").read_text()
        self.assertIn('if [ -n "${GITHUB_OUTPUT:-}" ]; then', script)
        self.assertIn('"$FEATURES_CONSUMER_WORK" >> "$GITHUB_OUTPUT"', script)
        self.assertIn('work=$(mktemp -d', script)

    def test_removed_cwd_recovers_before_artifact_checks(self):
        for name in ("candidate", "features_clean_consumer", "removed-cwd", "prefix-a"):
            (self.work / name).mkdir()
        (self.work / "prefix-a" / "shim.dll").touch()
        result = self.shell(
            'cd "$1/removed-cwd"; rmdir "$1/removed-cwd"; '
            'hide_consumer_sources "$1"; '
            'collect_consumer_inventory "$1/inventory" "$1/prefix-a" -type f; '
            'test -s "$1/inventory"', self.work)
        self.assertEqual(result.returncode, 0, result.stderr)