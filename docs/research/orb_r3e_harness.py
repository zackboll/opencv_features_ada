#!/usr/bin/env python3
"""R3E installed-ORB evidence. Text only; no large target matrix."""
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/research/orb_r3e_native_probe.cpp'
CHECKER = ROOT / 'docs/research/orb_r2_independent.py'


def parse_pkg_flags(value):
    return shlex.split(value)


def windows_include_environment(environment, compiler):
    native = ntpath.normcase(ntpath.normpath(ntpath.join(
        ntpath.dirname(compiler), '..', 'include')))
    child = environment.copy()
    for key in ('C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH'):
        if key not in child:
            continue
        kept = [entry for entry in child[key].split(';')
                if ntpath.normcase(ntpath.normpath(entry)) != native]
        if kept:
            child[key] = ';'.join(kept)
        else:
            del child[key]
    return child


def research_warnings(system):
    flags = ['-Wall', '-Wextra', '-Wpedantic', '-Werror']
    if system == 'Darwin':
        flags.append('-Wno-error=c11-extensions')
    return flags


class Harness:
    def __init__(self, output):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.env = os.environ.copy()
        self.records = []
        self.first_failure = None

    def run(self, label, command, required=True):
        path = self.output / label
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run([str(item) for item in command], env=self.env,
                                    capture_output=True, check=False)
            code, out, err = result.returncode, result.stdout, result.stderr
        except OSError as exc:
            code, out, err = 127, b'', str(exc).encode()
        path.with_suffix('.stdout.log').write_bytes(out)
        path.with_suffix('.stderr.log').write_bytes(err)
        path.with_suffix('.log').write_bytes(out + err)
        record = dict(label=label, command=[str(item) for item in command],
                      exit_status=code, required=required)
        self.records.append(record)
        path.with_suffix('.status.log').write_text(json.dumps(record) + '\n')
        if code and required and self.first_failure is None:
            self.first_failure = record
        return code, out.decode(errors='replace'), err.decode(errors='replace')

    def note(self, name, text):
        path = self.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if text.endswith('\n') else text + '\n')

    def select_apple(self):
        smoke = self.output / 'limits.cpp'
        smoke.write_text('#include <limits>\nint main() { return std::numeric_limits<int>::max() == 0; }\n')
        code, developers, _ = self.run('apple/xcode-select', ['xcode-select', '-p'], False)
        candidates = [None]
        if code == 0:
            candidates.append(developers.strip())
        for index in range(8, 17):
            candidates.append(f'/Applications/Xcode_{index}.app/Contents/Developer')
        for index, developer in enumerate(candidates):
            if developer:
                self.env['DEVELOPER_DIR'] = developer
            else:
                self.env.pop('DEVELOPER_DIR', None)
            prefix = f'apple/candidate-{index}'
            cc, compiler, _ = self.run(prefix + '/compiler', ['xcrun', '--find', 'clang++'], False)
            sc, sdk, _ = self.run(prefix + '/sdk', ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], False)
            if cc or sc:
                continue
            compiler, sdk = compiler.strip(), sdk.strip()
            self.env['SDKROOT'] = sdk
            flags = ['-isysroot', sdk, '-stdlib=libc++']
            exe = self.output / prefix / 'smoke'
            built, _, _ = self.run(prefix + '/smoke', [compiler, *flags, smoke, '-o', exe], False)
            if built == 0 and self.run(prefix + '/launch', [exe], False)[0] == 0:
                return compiler, flags
        raise RuntimeError('No Apple clang/SDK pair passed the libc++ smoke test')

    def features_library(self, text):
        for line in text.splitlines():
            if not line.startswith('LOADED '):
                continue
            path = line[len('LOADED '):].strip()
            name = Path(path).name.lower()
            if name.startswith(('libopencv_features.', 'libopencv_features-', 'libopencv_features2d.')):
                return path
        return None

    def hash_file(self, label, path):
        digest = hashlib.sha256()
        with open(path, 'rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        self.note(label, f'path={path}\nsha256={digest.hexdigest()}\nbytes={Path(path).stat().st_size}\n')

    def source_search(self, roots):
        found = []
        for root in roots:
            if not root or not Path(root).exists():
                continue
            base = Path(root)
            for relative in ('modules/features/src/orb.cpp', 'modules/features2d/src/orb.cpp'):
                candidate = base / relative
                if candidate.is_file():
                    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                    found.append(f'{digest} {candidate}')
        if found:
            self.note('source/orb-cpp.txt', 'SOURCE_BYTES_PRESENT\n' + '\n'.join(found) + '\n')
        else:
            searched = '\n'.join(str(root) for root in roots if root)
            self.note('source/orb-cpp.txt', 'SOURCE_BYTES_UNAVAILABLE\nsearched:\n' + searched + '\n')

    def focused_disassembly(self, text):
        lines = text.splitlines()
        index_lines = []
        for number, line in enumerate(lines, 1):
            if 'ORB' in line or 'getScale' in line or 'pow' in line.lower():
                index_lines.append(f'{number}:{line[:240]}')
        self.note('native/symbol-index.txt', '\n'.join(index_lines[:400]))
        selected = set()
        for index, line in enumerate(lines):
            lowered = line.lower()
            if any(word in lowered for word in ('pow', 'lrint', 'frint', 'fcvt', 'cvtss', 'cvtsd')):
                selected.update(range(max(0, index - 12), min(len(lines), index + 13)))
        chosen = [lines[index][:240] for index in sorted(selected)[:2500]]
        self.note('native/arithmetic-neighborhood.txt', '\n'.join(chosen))
        self.note('native/attribution.txt',
                  'GETSCALE_ATTRIBUTION_PENDING\n'
                  'A pow or rounding instruction is ORB evidence only when its\n'
                  'enclosing symbol or reviewed control flow identifies that path.\n')

    def manifest(self, status):
        files = []
        for path in sorted(self.output.rglob('*')):
            if path.is_file() and path.suffix in {'.log', '.txt', '.json'} and path.name != 'manifest.json':
                files.append(dict(path=path.relative_to(self.output).as_posix(),
                                   sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                   size=path.stat().st_size))
        payload = dict(tested_sha=self.env.get('GITHUB_SHA', 'local'),
                       run_id=self.env.get('GITHUB_RUN_ID', 'local'),
                       probe_exit_status=status,
                       first_failure=self.first_failure,
                       disposition='NATIVE_CORRESPONDENCE_PENDING',
                       files=files)
        (self.output / 'manifest.json').write_text(json.dumps(payload, indent=2) + '\n')
        return 0 if status == 0 and self.first_failure is None else 1

    def execute(self):
        system = platform.system()
        windows = system == 'Windows'
        suffix = '.exe' if windows else ''
        self.note('runner.txt', json.dumps(dict(
            os=platform.platform(), architecture=platform.machine(),
            runner_os=self.env.get('RUNNER_OS'),
            runner_arch=self.env.get('RUNNER_ARCH')), indent=2))
        pc = shutil.which('x86_64-w64-mingw32-pkg-config') if windows else None
        pc = pc or shutil.which('pkg-config')
        if not pc:
            raise RuntimeError('pkg-config not found')
        package = None
        for candidate in ('opencv5', 'opencv4', 'opencv'):
            if self.run('package/' + candidate, [pc, '--exists', candidate], False)[0] == 0:
                package = candidate
                break
        if not package:
            raise RuntimeError('installed OpenCV pkg-config package unavailable')

        def pkg(option):
            label = 'package/' + option.strip('-').replace('-', '')
            code, value, _ = self.run(label, [pc, option, package])
            if code:
                raise RuntimeError('pkg-config failed: ' + option)
            return value.strip()

        flags = parse_pkg_flags(pkg('--cflags'))
        libs = parse_pkg_flags(pkg('--libs'))
        pkg('--modversion')
        includedir = pkg('--variable=includedir')
        libdir = pkg('--variable=libdir')
        if windows:
            compiler = str(Path(libdir).resolve().parent / 'bin/g++.exe')
            if 'mingw64' not in compiler.lower() or 'gnat_native' in compiler.lower():
                raise RuntimeError('managed MinGW64 compiler was not selected: ' + compiler)
            self.env['PATH'] = str(Path(compiler).parent) + os.pathsep + self.env.get('PATH', '')
            self.env = windows_include_environment(self.env, compiler)
            extra = []
            self.run('package/inventory', ['pacman', '-Q', 'mingw-w64-x86_64-gcc',
                     'mingw-w64-x86_64-opencv', 'mingw-w64-x86_64-crt'])
        elif system == 'Darwin':
            compiler, extra = self.select_apple()
            self.run('package/brew', ['brew', 'info', '--json=v2', 'opencv'], False)
            self.run('package/versions', ['brew', 'list', '--versions', 'opencv'], False)
        else:
            compiler, extra = self.env.get('CXX', 'g++'), []
        self.run('compiler/version', [compiler, '--version'])
        self.run('compiler/target', [compiler, '-dumpmachine'])
        exe = self.output / ('orb_r3e_native_probe' + suffix)
        command = [compiler, *extra, '-std=c++17', '-O2', *research_warnings(system),
                   SOURCE, *flags, *libs, '-o', exe]
        if self.run('probe/compile', command)[0]:
            raise RuntimeError('native probe compilation failed')
        for mode in ('cpu', 'opencl-observe', 'powers'):
            if self.run('probe/' + mode, [exe, mode])[0]:
                raise RuntimeError('native probe failed: ' + mode)
        powers = (self.output / 'probe/powers.log').read_text(errors='replace')
        adapted = powers.replace('PASS R3E fixed powers', 'PASS R2 numerical boundaries')
        adapted_path = self.output / 'probe/powers-adapted.log'
        adapted_path.write_text(adapted)
        if self.run('probe/power-check', [sys.executable, CHECKER, adapted_path])[0]:
            raise RuntimeError('fixed-power rational check failed')
        cpu = (self.output / 'probe/cpu.log').read_text(errors='replace')
        native = self.features_library(cpu)
        if not native:
            raise RuntimeError('ORB execution did not load a Features library')
        self.hash_file('native/library-sha256.txt', native)
        self.source_search([includedir, libdir, str(Path(libdir).parent),
                            '/opt/homebrew/Cellar/opencv', '/usr/local/Cellar/opencv'])
        header = Path(includedir) / 'opencv2/core/fast_math.hpp'
        if header.is_file():
            self.hash_file('native/fast-math-sha256.txt', header)
        else:
            self.note('native/fast-math-sha256.txt', 'FAST_MATH_HEADER_UNAVAILABLE')
        if windows:
            tool = str(Path(compiler).parent / 'objdump.exe')
            self.run('native/linkage', [tool, '-p', native], False)
            self.run('native/symbols', [tool, '-T', native], False)
            code, assembly, _ = self.run('native/disassembly', [tool, '-d', '--demangle', native], False)
        elif system == 'Darwin':
            self.run('native/linkage', ['otool', '-L', native], False)
            self.run('native/symbols', ['nm', '-u', native], False)
            self.run('native/uuid', ['dwarfdump', '--uuid', native], False)
            code, assembly, _ = self.run('native/disassembly', ['otool', '-tvV', native], False)
        else:
            self.run('native/linkage', ['ldd', native], False)
            code, assembly, _ = self.run('native/disassembly', ['objdump', '-d', '--demangle', native], False)
        if code == 0:
            self.focused_disassembly(assembly)
        self.note('native/execution-path.txt',
                  'CPU control called setUseOpenCL(false) before ORB.\n'
                  'opencl-observe is a separate process and does not prove the default path.\n')


def main(output):
    harness = Harness(output)
    status = 0
    try:
        harness.execute()
    except Exception as exc:
        harness.note('prerequisite-failure.txt', str(exc))
        if harness.first_failure is None:
            harness.first_failure = dict(classification='PREREQUISITE_FAILED', message=str(exc))
        status = 1
    return harness.manifest(status)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: orb_r3e_harness.py OUTPUT_DIR')
    sys.exit(main(sys.argv[1]))

