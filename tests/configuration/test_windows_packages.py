"""Focused policy regression for the managed MSYS2 upgrade transaction.

This checks command semantics, not Windows execution or mirror consistency.
"""
from pathlib import Path
import re
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[2]


def package_steps(text):
    """Extract the package steps without requiring a general YAML library."""
    result = []
    for block in re.split(r"(?m)^      - ", text)[1:]:
        if "exec -- pacman" in block:
            result.append(block)
    return result


def check_package_sequence(text):
    steps = package_steps(text)
    commands = []
    for step in steps:
        if not re.search(r"(?m)^        shell: pwsh$", step):
            raise ValueError("upgrade parent must be outside managed MSYS2")
        lines = step.splitlines()
        for index, line in enumerate(lines):
            if "exec -- pacman" not in line:
                continue
            words = shlex.split(line.strip())
            if words[:5] != ["alr", "-n", "exec", "--", "pacman"]:
                raise ValueError("must use noninteractive Alire-managed pacman")
            if index + 1 == len(lines) or not re.fullmatch(
                    r'\s*if \(\$LASTEXITCODE -ne 0\) \{ throw "[^"\n]+" \}',
                    lines[index + 1]):
                raise ValueError("must propagate every package command failure")
            args = words[5:]
            short = "".join(arg[1:] for arg in args
                            if arg.startswith("-") and not arg.startswith("--"))
            long = {arg for arg in args if arg.startswith("--")}
            if long & {"--nodeps", "--assume-installed"} or "d" in short:
                raise ValueError("dependency checks must not be bypassed")
            flags = set(short)
            for option, flag in (("--sync", "S"), ("--refresh", "y"),
                                 ("--sysupgrade", "u"), ("--database", "D"),
                                 ("--check", "k")):
                if option in long:
                    flags.add(flag)
            packages = {arg for arg in args if not arg.startswith("-")}
            commands.append((flags, packages, step))
    if len(commands) != 4:
        raise ValueError("require two upgrades, install, dependency check")
    for flags, packages, _ in commands[:2]:
        if flags != {"S", "y", "u"} or packages:
            raise ValueError("must synchronize and fully upgrade")
    if commands[0][2] == commands[1][2]:
        raise ValueError("core and full upgrade require separate steps")
    if commands[2][0] != {"S"} or commands[2][1] != {
            "mingw-w64-x86_64-opencv", "mingw-w64-x86_64-gcc",
            "mingw-w64-x86_64-pkg-config"}:
        raise ValueError("install required MinGW64 packages without refresh")
    if commands[3][0] != {"D", "k"} or commands[3][1]:
        raise ValueError("check local database dependency consistency")
    if "msys2: true" not in text or "alire-project/setup-alire@" not in text:
        raise ValueError("preserve Alire-managed MSYS2 setup")


class WindowsPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / ".github/workflows/windows-post-merge.yml").read_text()

    def test_current_sequence(self):
        check_package_sequence(self.text)

    def test_equivalent_full_upgrade_forms(self):
        for flags in ("-Suy", "--sync --refresh --sysupgrade"):
            with self.subTest(flags=flags):
                check_package_sequence(self.text.replace("-Syu", flags))

    def test_partial_upgrade_rejected(self):
        for flags in ("-Sy", "--sync --refresh", "-Su"):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                check_package_sequence(self.text.replace("-Syu", flags, 1))

    def test_no_refresh_during_install(self):
        with self.assertRaises(ValueError):
            check_package_sequence(self.text.replace("-S --noconfirm", "-Sy --noconfirm"))

    def test_required_packages_and_environment(self):
        for token in ("mingw-w64-x86_64-opencv", "mingw-w64-x86_64-gcc",
                      "mingw-w64-x86_64-pkg-config", "msys2: true", "alr -n"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                check_package_sequence(self.text.replace(token, "omitted"))
        with self.assertRaises(ValueError):
            check_package_sequence(self.text.replace("shell: pwsh", "shell: bash"))

    def test_failures_and_consistency_check_required(self):
        for line in self.text.splitlines():
            if "$LASTEXITCODE -ne 0" in line:
                with self.subTest(line=line), self.assertRaises(ValueError):
                    check_package_sequence(self.text.replace(line, ""))
        with self.assertRaises(ValueError):
            check_package_sequence(self.text.replace("pacman -Dk", "pacman -Q"))
        for option in ("--nodeps", "--assume-installed anything"):
            with self.subTest(option=option), self.assertRaises(ValueError):
                check_package_sequence(self.text.replace("-Syu", f"-Syu {option}", 1))

    def test_existing_failure_artifact_preserved(self):
        self.assertIn("failure() && steps.consumer.outcome == 'failure'", self.text)
        self.assertIn("windows-consumer-resolution-${{ github.sha }}", self.text)
        self.assertIn("retention-days: 14", self.text)
        self.assertIn("if-no-files-found: error", self.text)
        for name in ("installed-projects.log", "installed-build.log",
                     "installed-resolution.log", "relocated-projects.log",
                     "relocated-build.log", "relocated-resolution.log",
                     "path-audit-failure.log", "prefix-a/share/gpr/**/*.gpr",
                     "relocated-longer-prefix-b/share/gpr/**/*.gpr"):
            self.assertIn(name, self.text)


if __name__ == "__main__":
    unittest.main()