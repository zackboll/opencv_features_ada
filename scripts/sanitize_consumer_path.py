"""Remove source-stage search directories, never rewrite diagnostic logs.

Windows input may be native semicolon-separated or shell colon-separated.
Output is a shell PATH; cygpath resolves aliases while source paths still exist.
"""
import argparse
import posixpath
import subprocess
import sys
from pathlib import Path


def split_path(value, windows=False):
    value = value.rstrip("\r\n")
    if windows and ";" in value:
        return value.split(";")
    # A colon after a single drive letter at the start of an entry is not
    # a delimiter. Also support mixed /c/... and C:/... shell spellings.
    if windows:
        entries = []
        start = 0
        for index, character in enumerate(value):
            drive = (index == start + 1 and value[start].isalpha()
                     and value[index + 1:index + 2] in ("/", "\\"))
            if character == ":" and not drive:
                entries.append(value[start:index])
                start = index + 1
        return entries + [value[start:]]
    return value.split(":")


def cygpath(option, value):
    return subprocess.check_output(["cygpath", option, "--", value], text=True).strip()


def windows_canonical(value):
    # -l expands 8.3 names; run before hiding candidate/dependency sources.
    return cygpath("-aml", value)


def sanitize(value, roots, windows=False, canonical=None, shell_path=None):
    if canonical is None:
        canonical = windows_canonical if windows else posixpath.abspath
    if shell_path is None:
        shell_path = (lambda p: cygpath("-u", p)) if windows else (lambda p: p)

    def key(path):
        path = canonical(path)
        if windows:
            path = path.replace("\\", "/").casefold()
        return posixpath.normpath(path).rstrip("/")

    forbidden = [key(root) for root in roots]
    retained = []
    for entry in split_path(value, windows):
        # Empty entries imply cwd, which becomes the consumer directory.
        # Do not retain an implicit lookup inherited from the source stage.
        if not entry:
            continue
        normalized = key(entry)
        if any(normalized == root or normalized.startswith(root + "/")
               for root in forbidden):
            continue
        retained.append(shell_path(canonical(entry)))
    if not retained:
        raise ValueError("PATH sanitization removed every search directory")
    if any(":" in entry for entry in retained):
        raise ValueError("shell PATH entries must not contain colons")
    return ":".join(retained)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--windows", action="store_true")
    parser.add_argument("--remove", action="append", required=True)
    args = parser.parse_args()
    value = args.input.read_text()
    result = sanitize(value, args.remove, args.windows)
    representation = ("native-semicolon" if args.windows and ";" in value
                      else "shell-colon")
    print(f"Consumer PATH capture format={representation}; "
          "output=shell-colon; source/prefix entries removed", file=sys.stderr)
    print(result)


if __name__ == "__main__":
    main()