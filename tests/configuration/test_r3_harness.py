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

    def test_pkg_include_semantics(self):
        self.assertEqual(MODULE.parse_pkg_flags('-I/opt/include -isystem /vendor/include'),
                         ['-I/opt/include', '-isystem', '/vendor/include'])

    def test_drive_paths_and_other_flags(self):
        self.assertEqual(MODULE.parse_pkg_flags(
            '-IC:/Program\\ Files/opencv -LD:/native/lib -lcore -pthread -DVALUE=2'),
            ['-IC:/Program Files/opencv', '-LD:/native/lib', '-lcore', '-pthread', '-DVALUE=2'])

    def exercise_pipeline(self, fail=False):
        reported = '-IC:/Users/runneradmin/AppData/Local/alire/cache/msys64/mingw64/bin/../include/opencv5'
        original = self.h.run

        def run(label, command, required=True, environment=None):
            command = [str(x) for x in command]
            if label == 'preflight/opencv-compile' and fail:
                return original(label, self.fake_compiler(
                    'import sys\nprint("cstdlib: fatal error: stdlib.h: No such file", file=sys.stderr)\nsys.exit(1)\n'))
            values = {'package/cflags': reported, 'package/libs': '-LD:/native/lib -lopencv_core',
                      'package/variable=libdir': str(self.root / 'mingw64/lib'),
                      'package/variable=includedir': str(self.root / 'include')}
            if '-o' in command:
                Path(command[command.index('-o') + 1]).touch()
            path = self.root / label
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_suffix('.log').write_text('synthetic output\n')
            self.h.records.append(dict(label=label, command=command, required=required, exit_status=0))
            self.h.records[-1]['environment'] = (self.h.env if environment is None else environment).copy()
            return 0, values.get(label, '')

        with patch.object(MODULE.platform, 'system', return_value='Windows'), \
                patch.object(MODULE.shutil, 'which', return_value='pkg-config'), \
                patch.object(self.h, 'run', side_effect=run):
            if fail:
                with self.assertRaisesRegex(RuntimeError, 'Preflight failed: opencv-compile'):
                    self.h.execute()
            else:
                self.h.execute()
        return reported

    def test_reported_windows_flags_reach_all_compiles(self):
        reported = self.exercise_pipeline()
        data = self.assert_manifest(0)
        for record in data['invocations']:
            if record['label'] == 'preflight/opencv-compile' or record['label'].endswith('-compile'):
                self.assertIn(reported, record['command'])
                self.assertNotIn('-isystem', record['command'])
        self.assertEqual(data['optimization_modes'], {key: 'EXECUTED' for key in ('0', '2', '3')})
        self.assertEqual(sum(r['label'].endswith('/independent') for r in data['invocations']), 3)

    def test_header_failure_is_prerequisite_and_finalizes(self):
        self.exercise_pipeline(fail=True)
        data = self.assert_manifest(1)
        self.assertEqual(data['first_failure']['label'], 'preflight/opencv-compile')
        self.assertEqual(data['first_failure']['classification'], 'PREREQUISITE_FAILED')
        self.assertEqual(data['optimization_modes'],
                         {key: 'PREREQUISITE_NOT_COMPLETED' for key in ('0', '2', '3')})
        self.assertFalse(any(r['label'].startswith('O') for r in data['invocations']))
        self.assertIn('stdlib.h', (self.root / 'preflight/opencv-compile.stderr.log').read_text())

    def test_scoped_apple_warnings(self):
        flags = MODULE.research_warnings('Darwin')
        self.assertEqual(flags, ['-Wall', '-Wextra', '-Wpedantic', '-Werror',
                                 '-Wno-error=c11-extensions'])
        self.assertNotIn('-Wno-error=c11-extensions', MODULE.research_warnings('Windows'))
        self.assertNotIn('-Wno-error=c11-extensions', MODULE.research_warnings('Linux'))

    def test_windows_include_components(self):
        env = {'C_INCLUDE_PATH': r'C:\MSYS\mingw64\include;D:\other\include',
               'CPLUS_INCLUDE_PATH': 'c:/msys/mingw64/bin/../include;E:/Program Files/headers',
               'CPATH': r'F:\keep', 'PATH': 'unchanged'}
        before = env.copy()
        child, native = MODULE.windows_include_environment(env, r'C:\MSYS\mingw64\bin\g++.exe')
        self.assertEqual(native, r'c:\msys\mingw64\include')
        self.assertEqual(child['C_INCLUDE_PATH'], r'D:\other\include')
        self.assertEqual(child['CPLUS_INCLUDE_PATH'], 'E:/Program Files/headers')
        self.assertEqual(child['CPATH'], env['CPATH'])
        self.assertEqual(child['PATH'], env['PATH'])
        self.assertEqual(env, before)

    def test_only_duplicate_entries_removed(self):
        env = {'C_INCLUDE_PATH': 'C:/msys/mingw64/include',
               'CPLUS_INCLUDE_PATH': 'C:/msys/mingw64/include-extra;;D:/headers'}
        child, _ = MODULE.windows_include_environment(env, 'C:/msys/mingw64/bin/g++.exe')
        self.assertNotIn('C_INCLUDE_PATH', child)
        self.assertEqual(child['CPLUS_INCLUDE_PATH'], env['CPLUS_INCLUDE_PATH'])

    def test_same_corrected_environment_across_pipeline(self):
        native = str(self.root / 'mingw64/include')
        self.h.env['C_INCLUDE_PATH'] = native
        self.h.env['CPLUS_INCLUDE_PATH'] = native + ';D:/keep'
        self.exercise_pipeline()
        records = self.assert_manifest(0)['invocations']
        negative = next(r for r in records if r['label'] == 'preflight/include-environment-before')
        self.assertEqual(negative['environment']['C_INCLUDE_PATH'], native)
        for r in records:
            if r['label'] == 'preflight/include-environment-after' or r['label'].startswith('O') or \
                    r['label'].startswith('preflight/opencv'):
                self.assertNotIn('C_INCLUDE_PATH', r['environment'])
                self.assertEqual(r['environment']['CPLUS_INCLUDE_PATH'], 'D:/keep')

    def test_subprocess_uses_explicit_child_without_parent_mutation(self):
        parent = self.h.env.copy()
        child = parent.copy()
        child['CPLUS_INCLUDE_PATH'] = 'D:/controlled'
        command = self.fake_compiler('import os\nprint(os.environ["CPLUS_INCLUDE_PATH"])\n')
        self.assertEqual(self.h.run('positive', command, environment=child)[1].strip(), 'D:/controlled')
        self.assertEqual(self.h.env, parent)
        self.assert_manifest(0)

    def test_apple_warning_commands_reach_subprocess(self):
        command = [sys.executable, '-c', 'pass', *MODULE.research_warnings('Darwin')]
        with patch.object(MODULE.subprocess, 'run', return_value=MODULE.subprocess.CompletedProcess(
                command, 0, b'', b'_Atomic is a C11 extension\n')) as run:
            self.h.run('apple-positive', command)
        actual = run.call_args.args[0]
        self.assertIn('-Werror', actual)
        self.assertGreater(actual.index('-Wno-error=c11-extensions'), actual.index('-Werror'))
        self.assertNotIn('-w', actual)
        self.assertIn('_Atomic', (self.root / 'apple-positive.stderr.log').read_text())

    def test_negative_positive_environment_streams(self):
        command = self.fake_compiler('import os, sys\n'
            'bad = "CPLUS_INCLUDE_PATH" in os.environ\n'
            'print("stdlib.h missing" if bad else "preprocessed", file=sys.stderr)\n'
            'sys.exit(1 if bad else 0)\n')
        before = self.h.env.copy()
        before['CPLUS_INCLUDE_PATH'] = 'C:/managed/include'
        after = before.copy()
        del after['CPLUS_INCLUDE_PATH']
        self.assertEqual(self.h.run('before', command, False, environment=before)[0], 1)
        self.assertEqual(self.h.run('after', command, environment=after)[0], 0)
        self.assertIn('stdlib.h missing', (self.root / 'before.stderr.log').read_text())
        self.assertIn('preprocessed', (self.root / 'after.stderr.log').read_text())
        self.assert_manifest(0)