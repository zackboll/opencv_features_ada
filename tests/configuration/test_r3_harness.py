"""Synthetic failures validate reporting, not hosted numerical premises."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('r3_harness', ROOT / 'docs/research/orb_r3_harness.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HarnessFailures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.h = MODULE.Harness(self.root)

    def fake_compiler(self, body):
        script = self.root / 'fake_compiler.py'
        script.write_text(body)
        return [sys.executable, str(script)]

    def assert_manifest(self, status):
        self.assertEqual(self.h.manifest(), status)
        data = json.loads((self.root / 'manifest.json').read_text())
        self.assertEqual(data['probe_exit_status'], status)
        self.assertEqual(set(data['optimization_modes']), {'0', '2', '3'})
        return data

    def test_compilation_stderr(self):
        command = self.fake_compiler('import sys\nprint("compile error", file=sys.stderr)\nsys.exit(3)\n')
        self.assertEqual(self.h.run('compile', command)[0], 3)
        self.assertIn('compile error', (self.root / 'compile.stderr.log').read_text())
        self.assertEqual(self.assert_manifest(1)['first_failure']['exit_status'], 3)

    def test_silent_exit(self):
        command = self.fake_compiler('import sys\nsys.exit(42)\n')
        self.assertEqual(self.h.run('compile', command)[0], 42)
        self.assertEqual((self.root / 'compile.stderr.log').read_bytes(), b'')
        self.assert_manifest(1)

    def test_missing_executable(self):
        self.assertFalse(self.h.executable('launch', self.root / 'missing'))
        self.assertEqual(self.assert_manifest(1)['first_failure']['exit_status'], 127)

    def test_preprocessing_failure(self):
        command = self.fake_compiler('import sys\nprint("missing limits", file=sys.stderr)\nsys.exit(1)\n')
        self.h.run('macros', command + ['-E'])
        # Later mode reporting and optional failures cannot overwrite the primary.
        self.h.run('diagnostic', [self.root / 'absent'], required=False)
        self.assertEqual(self.assert_manifest(1)['first_failure']['label'], 'macros')

    def test_numerical_execution_failure(self):
        command = self.fake_compiler('import sys\nprint("premise failed")\nsys.exit(9)\n')
        self.h.run('numerical', command)
        self.h.skip('independent', 'numerical execution failed')
        self.assertEqual(self.assert_manifest(1)['first_failure']['exit_status'], 9)

    def test_missing_numerical_output(self):
        self.assertFalse(self.h.check('independent', self.root / 'checker', self.root / 'missing'))
        data = self.assert_manifest(1)
        self.assertEqual(data['first_failure']['classification'], 'PREREQUISITE_FAILED')
        self.assertEqual(data['invocations'][0]['classification'], 'PREREQUISITE_FAILED')

    def test_success_and_optional_diagnostic(self):
        command = self.fake_compiler('print("PASS")\n')
        self.assertEqual(self.h.run('compile', command)[0], 0)
        self.h.run('optional', [self.root / 'absent'], required=False)
        self.assertIsNone(self.assert_manifest(0)['first_failure'])

    def test_unexpected_failure_finalizes_nonzero(self):
        with patch.object(MODULE.Harness, 'execute', side_effect=RuntimeError('setup failed')):
            self.assertEqual(MODULE.main(self.root), 1)
        data = json.loads((self.root / 'manifest.json').read_text())
        self.assertIn('setup failed', data['first_failure']['message'])

    def test_success_main(self):
        with patch.object(MODULE.Harness, 'execute'):
            self.assertEqual(MODULE.main(self.root), 0)
        self.assertTrue((self.root / 'manifest.json').is_file())

    def test_compile_success_without_executable(self):
        command = self.fake_compiler('import sys\nsys.exit(0)\n')
        self.assertEqual(self.h.run('compile', command)[0], 0)
        self.assertFalse(self.h.executable('launch', self.root / 'not-produced'))
        self.assert_manifest(1)

    def test_missing_output_checker_not_executed(self):
        command = self.fake_compiler('raise RuntimeError("must not run")\n')
        self.assertFalse(self.h.check('independent', command[-1], self.root / 'absent'))
        self.assertFalse((self.root / 'independent.stderr.log').exists())
        self.assert_manifest(1)