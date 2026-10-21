"""Linux-runnable harness/control-flow fixtures. NOT Windows native execution."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import windows_native_boundary as boundary
from check_windows_boundary import check_windows_boundary


class BoundaryFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="boundary fixture ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.output = self.root / "output"
        self.core = self.root / "indexed core"
        self.native = self.root / "native/mingw64"
        for directory in (self.source / "cpp", self.source / "tests/cpp",
                          self.source / "scripts", self.source / "config", self.core / "cpp",
                          self.core / "lib", self.native / "bin", self.native / "lib",
                          self.native / "include/opencv2"):
            directory.mkdir(parents=True)
        for name in ("opencv_core_module_bridge.hpp", "opencv_core_shim.h"):
            (self.core / "cpp" / name).write_text("// fixture, never native evidence\n")
        (self.core / "alire.toml").write_text(
            'name="opencv_core"\nversion="0.5.0"\n[origin]\n'
            'url="git+https://github.com/zackboll/opencv_core_ada.git"\n'
            'commit="f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f"\n')
        for name in ("libopencv_core_shim.dll.a", "libopencv_core_shim.dll"):
            (self.core / "lib" / name).touch()
        for name in ("libopencv_features2d.dll.a", "libopencv_core.dll.a"):
            (self.native / "lib" / name).touch()
        (self.native / "include/opencv2/features2d.hpp").touch()
        (self.source / "cpp/opencv_features_shim.cpp").write_text("// fixture source\n")
        (self.source / "tests/cpp/native_boundary.cpp").write_text("// fixture driver\n")
        (self.source / "alire.toml").write_text('name="opencv_features"\nversion="0.1.0"\n')
        (self.source / ".gitignore").write_text("/config/\n")
        shutil.copy(ROOT / "scripts/run_native.sh", self.source / "scripts/run_native.sh")
        self.driver = self.native / "bin/g++.exe"
        self.driver.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
a=sys.argv[1:]
if a==['-dumpmachine']: print(os.environ.get('FIXTURE_TARGET','x86_64-w64-mingw32'));sys.exit(0)
if a==['--version']: print('FIXTURE compiler, not Windows');sys.exit(0)
out=pathlib.Path(a[a.index('-o')+1]);stage='compile' if '-c' in a else 'link'
variant=out.parent.name
if os.environ.get('FIXTURE_FAIL') in (stage,stage+':'+variant):sys.exit(23)
if stage=='compile':
 out.write_text('hooks' if '-DOPENCV_FEATURES_TEST_HOOKS' in a else 'ordinary')
else:
 hooks='hooks' in pathlib.Path(a[0]).read_text()
 markers=['PASS: matcher Hamming','PASS: KNN2 Hamming/Hamming2','PASS: radius raw negatives',
          'PASS: actual Features shim / Core bridge / ORB boundary on 4.10.0']
 if hooks and not os.environ.get('FIXTURE_NO_FAULT'):
  markers.append('PASS: radius fault stages 15/16/17/18 x five exception categories, empty cleanup')
 if os.environ.get('FIXTURE_NO_MARKERS'):markers=[]
 out.write_text('#!/bin/sh\\n'+'# '+('hooks' if hooks else 'ordinary')+'\\n'+
                '\\n'.join("echo '"+s+"'" for s in markers)+'\\nexit '+
                ('17' if os.environ.get('FIXTURE_FAIL') in ('execute','execute:'+variant) else '0')+'\\n')
 out.chmod(0o755)
""")
        self.driver.chmod(0o755)
        nm = self.native / "bin/nm.exe"
        nm.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
hooks='# hooks' in pathlib.Path(sys.argv[-1]).read_text()
if os.environ.get('FIXTURE_SYMBOL')=='leak':hooks=True
if os.environ.get('FIXTURE_SYMBOL')=='missing':hooks=False
print('000 T opencv_features_test_fail' if hooks else '000 T opencv_features_orb_create')
""")
        nm.chmod(0o755)
        self.config = self.source / "config/opencv_features_install.gpr"
        fields = {"Shim_Build": "External_Relocatable", "Cxx_Toolchain": "GNU",
                  "Cxx_Driver": str(self.driver), "Native_Backend": "features2d",
                  "Native_Version": "4.10.0", "Include_Switch": f"-I{self.native}/include",
                  "Core_Bridge_Include_Switch": f"-I{self.core}/cpp",
                  "OpenCV_Features_Link_Option": f"{self.native}/lib/libopencv_features2d.dll.a",
                  "OpenCV_Core_Link_Option": f"{self.native}/lib/libopencv_core.dll.a",
                  "Core_Shim_Link_Option": f"{self.core}/lib/libopencv_core_shim.dll.a"}
        self.config.write_text("\n".join(f'   {k} := "{v}";' for k, v in fields.items()))
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "Fixture, not release evidence")
        self.identity = boundary.source_identity(self.source)
        self.environment = patch.dict(os.environ, OPENCV_CORE_ALIRE_PREFIX=str(self.core))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], text=True).strip()

    def qualify(self):
        real_identity = boundary.source_identity
        def identity(path, expected=None):
            return real_identity(path, expected) if path == self.source else self.identity
        with patch.object(boundary, "source_identity", side_effect=identity):
            boundary.qualify(self.source, self.output)

    def test_both_variants_compile_actual_selected_files_and_complete(self):
        calls = []
        real_run = boundary.run
        def capture(args, *a, **kw):
            calls.append([str(arg) for arg in args])
            return real_run(args, *a, **kw)
        with patch.object(boundary, "run", side_effect=capture):
            self.qualify()
        self.assertTrue((self.output / "qualification.json").is_file())
        for variant in boundary.VARIANTS:
            compiles = [a for a in calls if '-c' in a and f'/{variant}/' in ' '.join(a)]
            self.assertEqual(len(compiles), 2)
            self.assertEqual({a[a.index('-c')+1] for a in compiles}, {
                str(self.source / "cpp/opencv_features_shim.cpp"),
                str(self.source / "tests/cpp/native_boundary.cpp")})
            for args in compiles:
                self.assertIn('-DOPENCV_FEATURES_BUILDING', args)
                self.assertEqual('-DOPENCV_FEATURES_TEST_HOOKS' in args, variant == 'fault-injection')
            links = [a for a in calls if '-o' in a and '-c' not in a and f'/{variant}/' in ' '.join(a)]
            self.assertEqual(len(links), 1)
            self.assertNotIn('libopencv_features_shim.dll.a', ' '.join(links[0]))
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_compile_link_and_execution_failures_propagate_each_variant(self):
        for stage in ('compile', 'link', 'execute'):
            for variant in boundary.VARIANTS:
                with self.subTest(stage=stage, variant=variant), patch.dict(
                        os.environ, FIXTURE_FAIL=f'{stage}:{variant}'):
                    with self.assertRaisesRegex(ValueError, 'command failed'):
                        self.qualify()
                    self.assertFalse((self.output / 'qualification.json').exists())

    def test_missing_markers_and_missing_injected_execution_fail(self):
        for key in ('FIXTURE_NO_MARKERS', 'FIXTURE_NO_FAULT'):
            with self.subTest(key=key), patch.dict(os.environ, {key: '1'}):
                with self.assertRaisesRegex(ValueError, 'marker|exception paths'):
                    self.qualify()
                self.assertFalse((self.output / 'qualification.json').exists())

    def test_production_leak_and_fault_missing_controls_fail(self):
        for value in ('leak', 'missing'):
            with self.subTest(value=value), patch.dict(os.environ, FIXTURE_SYMBOL=value):
                with self.assertRaisesRegex(ValueError, 'fault-control symbol'):
                    self.qualify()

    def test_omitting_either_variant_fails(self):
        for variant in boundary.VARIANTS:
            with self.subTest(variant=variant), patch.object(boundary, 'VARIANTS', (variant,)):
                with self.assertRaisesRegex(ValueError, 'both successful'):
                    self.qualify()
        for results in ({}, {'production': ''}, {'fault-injection': ''},
                        {**boundary.MARKERS, 'production': ''}):
            with self.assertRaises(ValueError):
                boundary.require_complete(results)

    def test_wrong_compiler_target(self):
        with patch.dict(os.environ, FIXTURE_TARGET='x86_64-pc-linux-gnu'):
            with self.assertRaisesRegex(ValueError, 'MinGW64 target'):
                self.qualify()

    def test_early_failure_removes_stale_success_report(self):
        self.output.mkdir()
        (self.output / 'qualification.json').write_text('stale success')
        self.config.unlink()
        with self.assertRaises(OSError):
            self.qualify()
        self.assertFalse((self.output / 'qualification.json').exists())

    def test_wrong_compiler_and_import_selection_rejected(self):
        original = self.config.read_text()
        for old, new in ((str(self.driver), str(self.driver).replace('mingw64', 'gnat_native')),
                         ('libopencv_features2d.dll.a', 'libopencv_features_shim.dll.a'),
                         ('External_Relocatable', 'Static_PIC'),
                         (f'-I{self.core}/cpp', '-I/other/core/cpp')):
            with self.subTest(new=new):
                self.config.write_text(original.replace(old, new))
                with self.assertRaises(ValueError):
                    boundary.configuration(self.source, self.core)
        self.config.write_text(original)
        for library in (self.native / 'lib/libopencv_core.dll.a',
                        self.native / 'lib/libopencv_features2d.dll.a',
                        self.core / 'lib/libopencv_core_shim.dll.a'):
            library.unlink()
            with self.assertRaisesRegex(ValueError, 'missing Windows boundary input'):
                boundary.configuration(self.source, self.core)
            library.touch()

    def test_release_identity_and_dirty_source_rejected(self):
        expected = [self.identity['commit'], self.identity['tree']]
        self.assertEqual(boundary.source_identity(self.source, expected), self.identity)
        for index in (0, 1):
            wrong = expected.copy(); wrong[index] = '0' * 40
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                boundary.source_identity(self.source, wrong)
        (self.source / 'cpp/opencv_features_shim.cpp').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'no tracked edits'):
            boundary.source_identity(self.source, expected)

    def test_release_shell_failures_propagate_before_success_marker(self):
        tools = self.root / 'tools'
        tools.mkdir()
        trace = self.root / 'trace'
        scripts = {
            'uname': '#!/bin/sh\necho MINGW64_NT\n',
            'cygpath': '#!/bin/sh\nprintf "%s\\n" "$2"\n',
            'git': '''#!/bin/sh
echo "git $*" >> "$TRACE"
if [ "$1" = clone ]; then
    for last do :; done
    mkdir -p "$last"
fi
case "$*" in
    *rev-parse*tree*) echo "${FIXTURE_TREE:-0265f6e39de174722cfe8ff59d7663dddbcf8cbd}" ;;
    *rev-parse*) echo e6d977f0bba02c526920834ef6e88905366ed1b9 ;;
esac
''',
            'alr': '''#!/bin/sh
echo "alr $*" >> "$TRACE"
case "$*" in
    *build*) [ "${FIXTURE_STAGE:-}" != build ] ;;
    *exec*) [ "${FIXTURE_STAGE:-}" != boundary ] ;;
    *) exit 1 ;;
esac
''',
        }
        for name, text in scripts.items():
            path = tools / name; path.write_text(text); path.chmod(0o755)
        env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ['PATH'],
                   TRACE=str(trace), RUNNER_TEMP=str(self.root))
        for change in ({'FIXTURE_TREE': 'wrong'}, {'FIXTURE_STAGE': 'build'},
                       {'FIXTURE_STAGE': 'boundary'}):
            with self.subTest(change=change):
                trace.write_text('')
                result = subprocess.run(['sh', str(ROOT / 'scripts/qualify_windows_release.sh'),
                                         str(self.output)], env={**env, **change},
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('WINDOWS_RELEASE_SOURCE_QUALIFIED', result.stdout)
                if 'FIXTURE_TREE' in change:
                    self.assertNotIn('alr ', trace.read_text())
                if change.get('FIXTURE_STAGE') == 'build':
                    self.assertNotIn('alr -n exec', trace.read_text())

    def test_shell_rejects_missing_completion_markers_and_python_failure(self):
        tools = self.root / 'tools'
        tools.mkdir()
        for name, text in {
            'uname': '#!/bin/sh\necho MINGW64_NT\n',
            'cygpath': '#!/bin/sh\nprintf "%s\\n" "$2"\n',
            'python': '''#!/bin/sh
[ "${FIXTURE_OMIT:-}" = production ] || echo WINDOWS_NATIVE_BOUNDARY_PRODUCTION_PASS
[ "${FIXTURE_OMIT:-}" = fault ] || echo WINDOWS_NATIVE_BOUNDARY_FAULT_PASS
exit "${FIXTURE_EXIT:-0}"
''',
        }.items():
            path = tools / name; path.write_text(text); path.chmod(0o755)
        env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ['PATH'])
        for change in ({}, {'FIXTURE_OMIT': 'production'}, {'FIXTURE_OMIT': 'fault'},
                       {'FIXTURE_EXIT': '21'}):
            with self.subTest(change=change):
                result = subprocess.run(['sh', str(ROOT / 'scripts/run_windows_native_boundary.sh'),
                                         str(self.source), str(self.output)],
                                        env={**env, **change}, capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, not change, result.stdout + result.stderr)


class BoundaryPolicyTests(unittest.TestCase):
    def test_unconditional_steps_and_history_required(self):
        text = (ROOT / '.github/workflows/windows-post-merge.yml').read_text()
        check_windows_boundary(text)
        for token in ('run_windows_native_boundary.sh', 'qualify_windows_release.sh',
                      'fetch-depth: 0'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                check_windows_boundary(text.replace(token, 'omitted'))
        for bypass in ('        if: false\n', '        continue-on-error: true\n',
                       '        shell: echo\n'):
            with self.subTest(bypass=bypass), self.assertRaises(ValueError):
                check_windows_boundary(text.replace(
                    '        run: alr -n exec -- sh scripts/run_windows_native_boundary.sh',
                    bypass + '        run: alr -n exec -- sh scripts/run_windows_native_boundary.sh'))
        for bypass in (' || true', ' # disabled', ' && echo ignored'):
            with self.assertRaises(ValueError):
                check_windows_boundary(text.replace('obj/windows-native-boundary\n',
                                                    'obj/windows-native-boundary' + bypass + '\n'))
        for option in ('if: false', 'continue-on-error: true'):
            with self.assertRaises(ValueError):
                check_windows_boundary(text.replace('    runs-on:', f'    {option}\n    runs-on:'))

    def test_release_checkout_is_independent_and_pinned(self):
        script = (ROOT / 'scripts/qualify_windows_release.sh').read_text()
        for token in ('git clone --no-local --no-checkout',
                      'commit=e6d977f0bba02c526920834ef6e88905366ed1b9',
                      'tree=0265f6e39de174722cfe8ff59d7663dddbcf8cbd',
                      'rev-parse HEAD', "rev-parse 'HEAD^{tree}'", 'git diff --exit-code HEAD --',
                      'alr -n build', '$harness/scripts/run_windows_native_boundary.sh'):
            self.assertIn(token, script)
        self.assertLess(script.index("rev-parse 'HEAD^{tree}'"), script.index('alr -n build'))
        self.assertNotIn('cp ', script)

    def test_linux_campaign_bytes_remain_approved(self):
        # Digests are of the approved release scripts, not fixture output.
        approved = {
            'scripts/run_sanitizers.sh': '1cbfd2d8e32024389efb3ac5fa63cd61fa2ca00fc5f6ec7430fbe76f8cf081f6',
            'scripts/test.sh': '7d66f61710d542ecd2396a88aecdb11b9f7eb95fa6a3cc8bed4c1ec685f185b6',
        }
        for name, digest in approved.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_real_windows_required_at_entry(self):
        with patch.object(boundary.sys, 'platform', 'linux'):
            with self.assertRaisesRegex(ValueError, 'real Windows'):
                boundary.main()


if __name__ == '__main__':
    unittest.main()