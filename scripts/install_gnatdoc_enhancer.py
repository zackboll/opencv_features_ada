#!/usr/bin/env python3
"""Install the pinned ada-gnatdoc-enhancer from a local Git checkout.

The revision must equal the reviewed pin in gnatdoc_enhancer_support.py. The
package is built from ``git archive`` of that commit (never a branch or a
working tree) into a new virtual environment, and every installed module and
asset is compared with the commit's Git blobs. A provenance record is written
into the environment for scripts/enhance_docs.py to re-check.
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
    parser.add_argument("--checkout", type=Path, required=True,
                        help="ada-gnatdoc-enhancer Git checkout containing the revision")
    parser.add_argument("--venv", type=Path, required=True, help="new environment directory")
    parser.add_argument("--revision", default=support.PINNED_REVISION)
    args = parser.parse_args(argv)
    if args.revision != support.PINNED_REVISION:
        print(f"FAIL: only the reviewed revision {support.PINNED_REVISION} is authorized",
              file=sys.stderr)
        return 1
    try:
        tool = support.install(args.checkout.resolve(), args.revision, args.venv.resolve())
    except (support.SupportError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: installed {tool} from {args.revision}; installed files equal Git blobs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
