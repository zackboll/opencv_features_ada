#!/usr/bin/env python3
"""Index focused text evidence only; never upload binaries or full environments."""
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(sys.argv[1])
records = [dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
           for p in sorted(root.rglob('*')) if p.suffix in ('.log', '.txt')]
(root / 'manifest.json').write_text(json.dumps(dict(
    tested_sha=os.environ.get('GITHUB_SHA', 'local'),
    run_id=os.environ.get('GITHUB_RUN_ID', 'local'),
    probe_exit_status=int(sys.argv[2]),
    disposition='PLATFORM_EVIDENCE_PENDING',
    note='Passing probes require separate native-build and source-version review.',
    files=records), indent=2) + '\n')