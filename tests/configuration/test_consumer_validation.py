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

    def test_qualifier_uses_checked_helpers(self):
        script = (ROOT / "scripts/validate_clean_consumer.sh").read_text()
        self.assertIn('hide_consumer_sources "$work"', script)
        self.assertIn('check_features_pe_imports "$work/installed-features-pe.log"', script)
        self.assertNotRegex(script, r'find "\$prefix[^\n]*\|')
        self.assertNotIn("opencv_core[0-9]", script)

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