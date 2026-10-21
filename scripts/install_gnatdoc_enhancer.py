#!/usr/bin/env python3
"""Install the independently approved official enhancer v0.1.0 release wheel.

HTTPS downloads, annotated tag/source identity, archive digest, provenance and
every wheel member are checked before installation. Subsequent invocations of
enhance_docs.py recheck installed bytes against Features-owned identities.
--with-guides installs the existing hash-pinned optional Markdown wheels.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gnatdoc_enhancer_support as support  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--venv", type=Path, required=True, help="new environment directory")
    parser.add_argument("--revision", default=support.PINNED_REVISION)
    parser.add_argument("--with-guides", action="store_true",
                        help="also install docs/gnatdoc-guides-requirements.txt (hash-pinned)")
    args = parser.parse_args(argv)
    if args.revision != support.PINNED_REVISION:
        print(f"FAIL: only the reviewed revision {support.PINNED_REVISION} is authorized",
              file=sys.stderr)
        return 1
    try:
        requirements = (support.ROOT / "docs/gnatdoc-guides-requirements.txt"
                        if args.with_guides else None)
        tool = support.install(args.venv.resolve(), requirements)
    except (support.SupportError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: installed {tool} from official v0.1.0; approved wheel and installed bytes verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
