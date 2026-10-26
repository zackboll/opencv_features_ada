"""Opt-in real Alire environment regression; runnable on Windows and Linux.

FEATURES_REAL_ALIRE_TEST=1 python -m unittest discover -s tests/configuration
Requires alr 2.1.1 and gnat on the outer PATH. No native qualification claim:
the local source/index fixtures only exercise Alire hashing/environment export.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


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
            msys = ''
            if sys.platform == 'win32':
                pacman = shutil.which('pacman')
                self.assertIsNotNone(pacman, 'existing MSYS2 pacman required on outer PATH')
                msys = '\n[msys2]\ninstall_dir=' + json.dumps(
                    Path(pacman).resolve().parents[2].as_posix()) + '\n'
            (settings / 'settings.toml').write_text(
                '[index]\nauto_community=false\nauto_update=0\n'
                '[cache]\ndir=' + json.dumps((root / 'cache').as_posix()) + '\n'
                '[toolchain]\nassistant=false\n' + msys)
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
                result = subprocess.run([*alr, *args], cwd=workspace,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            run('index', '--add', str(index), '--name', 'fixture')
            run('build', '--stop-after=pre-build')
            # File probe avoids shell quoting/path conversion on both platforms.
            probe = workspace / 'probe.py'
            probe.write_text('''import hashlib, json, os, subprocess, sys
from pathlib import Path
core=Path(os.environ['BOUNDARY_CORE_ALIRE_PREFIX'])
lines=(core/'alire/build_hash_inputs').read_text().splitlines()
digest=hashlib.sha256(b''.join(s.encode()+b'\\0' for s in lines)).hexdigest()
dependency=[s for s in Path('alire/build_hash_inputs').read_text().splitlines()
            if s.startswith('dependency:boundary_core=')]
nested=subprocess.run(json.loads(sys.argv[1])+['exec','--',sys.executable,'-c',
                      'print("NESTED_CHILD_RAN")'],capture_output=True,text=True)
Path('result.json').write_text(json.dumps(dict(core=core.name,digest=digest,
 dependency=dependency,features=os.environ['BOUNDARY_FEATURES_ALIRE_PREFIX'],
 nested_code=nested.returncode,nested_text=nested.stdout+nested.stderr)))
''')
            run('exec', '--', sys.executable, str(probe), json.dumps(alr))
            result = json.loads((workspace / 'result.json').read_text())
            self.assertEqual(result['core'], result['digest'])
            self.assertEqual(result['dependency'], ['dependency:boundary_core=0.5.0=' + result['digest']])
            self.assertEqual(Path(result['features']).resolve(), workspace.resolve())
            self.assertNotEqual(result['nested_code'], 0)
            self.assertIn('Trying to set an already defined environment variable', result['nested_text'])
            self.assertIn('BOUNDARY_CORE_ALIRE_PREFIX', result['nested_text'])
            self.assertNotIn('NESTED_CHILD_RAN', result['nested_text'])


if __name__ == '__main__':
    unittest.main()
