"""Opt-in real Alire environment regression; runnable on Windows and Linux.

FEATURES_REAL_ALIRE_TEST=1 python -m unittest discover -s tests/configuration
Requires alr 2.1.1 and gnat on the outer PATH. No native qualification claim:
the local source/index fixtures only exercise Alire hashing/environment export.
The settings-representation tests below always run and need no Alire.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import tomllib


def alire_settings(cache, msys2=None):
    """Return settings.toml text with Alire paths in native representation.

    Alire 2.1.1 appends native components to cache.dir. On Windows a
    forward-slash value yields C:/.../cache\\releases\\..., which Den rejects
    (Path_Parts predicate) when the build sync copies into an existing
    directory: "Could not sync build dir". Never use as_posix() here.
    """
    text = ('[index]\nauto_community=false\nauto_update=0\n'
            '[cache]\ndir=' + json.dumps(str(cache)) + '\n'
            '[toolchain]\nassistant=false\n')
    if msys2 is not None:
        text += '\n[msys2]\ninstall_dir=' + json.dumps(str(msys2)) + '\n'
    return text


class AlireSettingsRepresentationTests(unittest.TestCase):
    WINDOWS = PureWindowsPath(
        r'C:\Users\RUNNER~1\AppData\Local\Temp\real alire environment 0rg7qs68')

    def test_windows_paths_stay_native_with_spaces(self):
        settings = tomllib.loads(alire_settings(self.WINDOWS / 'cache',
                                                self.WINDOWS / 'msys64'))
        for value, expected in ((settings['cache']['dir'], self.WINDOWS / 'cache'),
                                (settings['msys2']['install_dir'], self.WINDOWS / 'msys64')):
            with self.subTest(value=value):
                self.assertEqual(value, str(expected))
                self.assertNotIn('/', value)
                self.assertIn(' ', value)

    def test_rejected_forward_slash_form_is_not_emitted(self):
        # The CI-019 fixture wrote this form; Alire then built a mixed path.
        text = alire_settings(self.WINDOWS / 'cache')
        self.assertNotIn((self.WINDOWS / 'cache').as_posix(), text)
        self.assertEqual(tomllib.loads(text)['cache']['dir'] + '\\releases',
                         str(self.WINDOWS / 'cache' / 'releases'))

    def test_posix_paths_and_optional_msys2(self):
        cache = PurePosixPath('/tmp/real alire environment x/cache')
        settings = tomllib.loads(alire_settings(cache))
        self.assertEqual(settings['cache']['dir'], str(cache))
        self.assertNotIn('msys2', settings)
        self.assertEqual(settings['index'], {'auto_community': False, 'auto_update': 0})
        self.assertEqual(settings['toolchain'], {'assistant': False})


@unittest.skipUnless(os.environ.get('FEATURES_REAL_ALIRE_TEST') == '1',
                     'opt-in real Alire 2.1.1 regression')
class RealAlireEnvironmentTests(unittest.TestCase):
    def test_path_hash_collision_and_single_execution_environment(self):
        self.assertIsNotNone(shutil.which('alr'), 'real alr required')
        self.assertIsNotNone(shutil.which('gnat'), 'gnat required on outer PATH')
        self.assertEqual(subprocess.check_output(['alr', '--version'], text=True).strip(),
                         'alr 2.1.1')
        with tempfile.TemporaryDirectory(prefix='real alire environment ') as temporary:
            root = Path(temporary)
            settings, index, core, workspace = [root / n for n in
                                                ('settings', 'index', 'core', 'workspace')]
            for path in (settings, index, core, workspace):
                path.mkdir()
            # Windows callers use the setup-alire MSYS2 already on PATH. Do
            # not create/install another MSYS2 in this disposable cache.
            msys = None
            if sys.platform == 'win32':
                pacman = shutil.which('pacman')
                self.assertIsNotNone(pacman, 'existing MSYS2 pacman required on outer PATH')
                msys = Path(pacman).resolve().parents[2]
            (settings / 'settings.toml').write_text(alire_settings(root / 'cache', msys))
            (index / 'index.toml').write_text('version="1.4.0"\n')
            metadata = ('description="Alire environment regression fixture"\n'
                        'licenses="Apache-2.0"\nmaintainers=["fixture@example.invalid"]\n'
                        'maintainers-logins=["fixture"]\n')
            core_manifest = ('name="boundary_core"\nversion="0.5.0"\n' + metadata +
                             '[environment]\nPATH.prepend="${CRATE_ROOT}/lib"\n')
            (core / 'alire.toml').write_text(core_manifest)
            (core / 'boundary_core.gpr').write_text('project Boundary_Core is\nend Boundary_Core;\n')
            release = index / 'bo/boundary_core/boundary_core-0.5.0.toml'
            release.parent.mkdir(parents=True)
            release.write_text(core_manifest + '\n[origin]\nurl=' +
                               json.dumps('file:' + core.as_posix()) + '\n')
            compiler = index / 'gn/gnat_external/gnat_external-external.toml'
            compiler.parent.mkdir(parents=True)
            compiler.write_text('name="gnat_external"\n' + metadata +
                                '[[external]]\nkind="version-output"\n'
                                'version-command=["gnat","--version"]\n'
                                'version-regexp="^GNAT\\\\D*([\\\\d\\\\.]+).*"\n'
                                'provides="gnat"\n')
            (workspace / 'alire.toml').write_text(
                'name="boundary_features"\nversion="0.1.0"\n' + metadata +
                '[[depends-on]]\nboundary_core="~0.5.0"\n'
                '[environment]\nPATH.prepend="${CRATE_ROOT}/lib"\n')
            (workspace / 'boundary_features.gpr').write_text(
                'with "boundary_core.gpr";\nproject Boundary_Features is\nend Boundary_Features;\n')
            alr = ['alr', '-s', str(settings), '-n']
            def run(*args):
                # -d makes Alire print the underlying exception (bounded: only
                # on failure) instead of only a generic sync/build error.
                result = subprocess.run([*alr, '-d', *args], cwd=workspace,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            run('index', '--add', str(index), '--name', 'fixture')
            run('build', '--stop-after=pre-build')
            # File probe avoids shell quoting/path conversion on both platforms.
            probe = workspace / 'probe.py'
            probe.write_text('''import hashlib, json, os, subprocess, sys
from pathlib import Path, PurePosixPath, PureWindowsPath
core=Path(os.environ['BOUNDARY_CORE_ALIRE_PREFIX'])
lines=(core/'alire/build_hash_inputs').read_text().splitlines()
digest=hashlib.sha256(b''.join(s.encode()+b'\\0' for s in lines)).hexdigest()
dependency=[s for s in Path('alire/build_hash_inputs').read_text().splitlines()
            if s.startswith('dependency:boundary_core=')]
nested=subprocess.run(json.loads(sys.argv[1])+['exec','--',sys.executable,'-c',
                      'print("NESTED_CHILD_RAN")'],capture_output=True,text=True)
Path('result.json').write_text(json.dumps(dict(core=core.name,core_prefix=str(core),digest=digest,
 dependency=dependency,features=os.environ['BOUNDARY_FEATURES_ALIRE_PREFIX'],
 nested_code=nested.returncode,nested_text=nested.stdout+nested.stderr)))
''')
            run('exec', '--', sys.executable, str(probe), json.dumps(alr))
            result = json.loads((workspace / 'result.json').read_text())
            self.assertEqual(result['core'], result['digest'])
            # The selected build is the disposable cache's hashed build.
            self.assertTrue(Path(result['core_prefix']).resolve().is_relative_to(
                (root / 'cache' / 'builds').resolve()), result['core_prefix'])
            self.assertEqual(result['dependency'], ['dependency:boundary_core=0.5.0=' + result['digest']])
            self.assertEqual(Path(result['features']).resolve(), workspace.resolve())
            self.assertNotEqual(result['nested_code'], 0)
            self.assertIn('Trying to set an already defined environment variable', result['nested_text'])
            self.assertIn('BOUNDARY_CORE_ALIRE_PREFIX', result['nested_text'])
            self.assertNotIn('NESTED_CHILD_RAN', result['nested_text'])


if __name__ == '__main__':
    unittest.main()
