#!/usr/bin/env python3
"""Focused subprocess evidence; prerequisite failures are not arithmetic failures."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ('orb_r2_numerics', 'orb_r3_trace', 'orb_levels_probe')


class Harness:
    def __init__(self, output):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.env = os.environ.copy()
        self.records = []
        self.first_failure = None
        self.modes = {str(n): 'PREREQUISITE_NOT_COMPLETED' for n in (0, 2, 3)}

    def run(self, label, command, required=True):
        path = self.output / label
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run([str(x) for x in command], env=self.env,
                                    capture_output=True, check=False)
            code, out, err = result.returncode, result.stdout, result.stderr
        except OSError as exc:
            code, out, err = 127, b'', str(exc).encode()
        path.with_suffix('.stdout.log').write_bytes(out)
        path.with_suffix('.stderr.log').write_bytes(err)
        # Combined stream for unchanged checkers; not a time-ordered stream.
        path.with_suffix('.log').write_bytes(out + err)
        record = dict(label=label, command=[str(x) for x in command],
                      exit_status=code, required=required)
        self.records.append(record)
        path.with_suffix('.status.log').write_text(json.dumps(record) + '\n')
        if code and required and self.first_failure is None:
            self.first_failure = record
        return code, out.decode(errors='replace')

    def skip(self, label, reason):
        self.records.append(dict(label=label, classification='PREREQUISITE_FAILED', reason=reason))

    def executable(self, label, executable):
        return self.run(label, [executable])[0] == 0

    def check(self, label, checker, numerical):
        numerical = Path(numerical)
        if not numerical.is_file() or not numerical.stat().st_size:
            self.skip(label, 'missing numerical output; no arithmetic result')
            if self.first_failure is None:
                self.first_failure = dict(label=label, classification='PREREQUISITE_FAILED')
            return False
        return self.run(label, [sys.executable, checker, numerical])[0] == 0

    def manifest(self):
        records = [dict(path=str(p.relative_to(self.output)),
                        sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                   for p in sorted(self.output.rglob('*')) if p.suffix in ('.log', '.txt')]
        data = dict(tested_sha=self.env.get('GITHUB_SHA', 'local'),
                    run_id=self.env.get('GITHUB_RUN_ID', 'local'),
                    disposition='PLATFORM_EVIDENCE_PENDING',
                    probe_exit_status=int(self.first_failure is not None),
                    first_failure=self.first_failure, optimization_modes=self.modes,
                    invocations=self.records, files=records)
        (self.output / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n')
        return data['probe_exit_status']

    def select_apple(self, smoke):
        self.run('apple/xcode-select', ['xcode-select', '-p'], False)
        candidates = [self.env.get('DEVELOPER_DIR')]
        candidates += [str(p) for p in sorted(Path('/Applications').glob('Xcode*.app/Contents/Developer'))]
        for index, developer in enumerate(dict.fromkeys(candidates)):
            if developer:
                self.env['DEVELOPER_DIR'] = developer
            else:
                self.env.pop('DEVELOPER_DIR', None)
            prefix = f'apple/candidate-{index}'
            cc, compiler = self.run(prefix + '/compiler', ['xcrun', '--find', 'clang++'], False)
            sc, sdk = self.run(prefix + '/sdk', ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], False)
            if cc or sc:
                continue
            compiler, sdk = compiler.strip(), sdk.strip()
            self.env['SDKROOT'] = sdk
            flags = ['-isysroot', sdk, '-stdlib=libc++']
            self.run(prefix + '/search', [compiler, *flags, '-v', '-E', '-x', 'c++', smoke], False)
            headers = list(Path(compiler).parent.parent.glob('include/c++/v1/limits'))
            (self.output / prefix / 'headers.txt').write_text('\n'.join(str(p) for p in headers) + '\n')
            exe = self.output / prefix / 'smoke'
            code, _ = self.run(prefix + '/smoke', [compiler, *flags, smoke, '-o', exe], False)
            if code == 0 and exe.is_file() and self.run(prefix + '/launch', [exe], False)[0] == 0:
                return compiler, flags
        raise RuntimeError('No discovered Apple clang/SDK pair passed the libc++ limits smoke test')

    def execute(self):
        (self.output / 'runner.log').write_text(json.dumps(dict(
            os=platform.platform(), architecture=platform.machine(),
            runner_os=self.env.get('RUNNER_OS'), runner_arch=self.env.get('RUNNER_ARCH'),
            image_os=self.env.get('ImageOS'), image_version=self.env.get('ImageVersion')), indent=2) + '\n')
        smoke = self.output / 'limits.cpp'
        smoke.write_text('#include <limits>\nint main() { return std::numeric_limits<int>::max() == 0; }\n')
        windows = platform.system() == 'Windows'
        suffix = '.exe' if windows else ''
        pc = shutil.which('x86_64-w64-mingw32-pkg-config') if windows else None
        pc = pc or shutil.which('pkg-config')
        if not pc:
            raise RuntimeError('selected pkg-config not found')
        package = None
        for candidate in ('opencv5', 'opencv4', 'opencv'):
            if self.run('package/' + candidate, [pc, '--exists', candidate], False)[0] == 0:
                package = candidate
                break
        if not package:
            raise RuntimeError('native OpenCV package unavailable')
        def pkg(option):
            code, value = self.run('package/' + option.replace('-', ''), [pc, option, package])
            if code:
                raise RuntimeError('pkg-config failed: ' + option)
            return value.strip()
        flags = shlex.split(pkg('--cflags'))
        flags = [value for token in flags for value in
                 (['-isystem', token[2:]] if token.startswith('-I') else [token])]
        libs = shlex.split(pkg('--libs'))
        pkg('--modversion')
        if windows:
            libdir = Path(pkg('--variable=libdir')).resolve()
            compiler = str(libdir.parent / 'bin/g++.exe')
            if 'mingw64' not in compiler.lower() or 'gnat_native' in compiler.lower():
                raise RuntimeError('Expected managed MinGW64 compiler: ' + compiler)
            # Native subprocess PATH separators, not colon-separated drive paths.
            # This changes only the research child environment, not Ada's PATH.
            self.env['PATH'] = str(Path(compiler).parent) + os.pathsep + self.env.get('PATH', '')
            self.run('preflight/packages', ['pacman', '-Q', 'mingw-w64-x86_64-gcc',
                     'mingw-w64-x86_64-opencv', 'mingw-w64-x86_64-crt'], False)
            extra = []
        elif platform.system() == 'Darwin':
            compiler, extra = self.select_apple(smoke)
            self.run('preflight/os', ['sw_vers'], False)
        else:
            compiler, extra = self.env.get('CXX', 'g++'), []
        self.run('preflight/version', [compiler, '--version'])
        self.run('preflight/target', [compiler, '-dumpmachine'])
        self.run('preflight/frontend', [compiler, '-print-prog-name=cc1plus'], False)
        if windows:
            _, frontend = self.run('preflight/frontend-location', [compiler, '-print-prog-name=cc1plus'], False)
            front = Path(frontend.strip())
            tool = Path(compiler).parent / 'objdump.exe'
            if front.is_file():
                self.run('preflight/frontend-imports', [tool, '-p', front], False)
            self.run('preflight/driver-imports', [tool, '-p', compiler], False)
        self.run('preflight/search', [compiler, *extra, '-v', '-E', '-x', 'c++', smoke], False)
        plain = self.output / 'plain.cpp'
        plain.write_text('int main() { return 0; }\n')
        core = self.output / 'core.cpp'
        core.write_text('#include <opencv2/core.hpp>\nint main() { return cv::getBuildInformation().empty(); }\n')
        stages = [('plain', plain, [], [], False), ('limits', smoke, [], [], False),
                  ('opencv-compile', core, flags, [], True),
                  ('opencv-link', core, flags, libs, False)]
        for name, source, includes, links, compile_only in stages:
            exe = self.output / ('preflight-' + name + ('.o' if compile_only else suffix))
            command = [compiler, *extra, '-std=c++17', '-v', *includes]
            if compile_only:
                command += ['-c']
            code, _ = self.run('preflight/' + name, [*command, source, *links, '-o', exe])
            if code:
                raise RuntimeError('Preflight failed: ' + name + '; see driver output/status')
            if not exe.is_file():
                self.executable('preflight/' + name + '-missing-output', exe)
                raise RuntimeError('Compiler returned success without output: ' + name)
            if not compile_only and not self.executable('preflight/' + name + '-launch', exe):
                raise RuntimeError('Preflight executable launch failed: ' + name)
        include = Path(pkg('--variable=includedir'))
        for header in (include / 'opencv2/core/fast_math.hpp',
                       include / 'opencv4/opencv2/core/fast_math.hpp',
                       include / 'opencv5/opencv2/core/fast_math.hpp'):
            if header.is_file():
                shutil.copyfile(header, self.output / 'selected-fast-math.txt')
                break
        for opt in (0, 2, 3):
            directory = self.output / f'O{opt}'
            directory.mkdir(exist_ok=True)
            self.modes[str(opt)] = 'EXECUTED'
            successful = set()
            for name in SOURCES:
                exe = directory / (name + suffix)
                command = [compiler, *extra, '-std=c++17', f'-O{opt}', '-Wall', '-Wextra',
                           '-Wpedantic', '-Werror', ROOT / 'docs/research' / (name + '.cpp'),
                           *flags, *libs, '-o', exe]
                code, _ = self.run(f'O{opt}/{name}-compile', command)
                if code:
                    self.skip(f'O{opt}/{name}', 'compilation/link prerequisite failed')
                elif self.executable(f'O{opt}/{name}', exe):
                    successful.add(name)
            for name, checker, label in [('orb_r2_numerics', 'orb_r2_independent.py', 'independent'),
                                         ('orb_levels_probe', 'orb_levels_certificate.py', 'r1-certificate')]:
                if name in successful:
                    self.check(f'O{opt}/{label}', ROOT / 'docs/research' / checker,
                               directory / (name + '.log'))
                else:
                    self.skip(f'O{opt}/{label}', 'numerical executable unavailable or failed')
            self.run(f'O{opt}/macros', [compiler, *extra, '-std=c++17', f'-O{opt}', *flags,
                     '-dM', '-E', ROOT / 'docs/research/orb_r2_numerics.cpp'])
            trace = directory / ('orb_r3_trace' + suffix)
            if trace.is_file():
                if windows:
                    tool = Path(compiler).parent / 'objdump.exe'
                    self.run(f'O{opt}/linkage', [tool, '-p', trace], False)
                    self.run(f'O{opt}/disassembly', [tool, '-d', trace], False)
                elif platform.system() == 'Darwin':
                    self.run(f'O{opt}/linkage', ['otool', '-L', trace], False)
                    self.run(f'O{opt}/disassembly', ['otool', '-tvV', trace], False)
                else:
                    self.run(f'O{opt}/linkage', ['ldd', trace], False)


def main(output):
    harness = Harness(output)
    try:
        harness.execute()
    except Exception as exc:
        (harness.output / 'prerequisite-failure.log').write_text(str(exc) + '\n')
        if harness.first_failure is None:
            harness.first_failure = dict(classification='PREREQUISITE_FAILED', message=str(exc))
    finally:
        status = harness.manifest()
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))