"""Focused, fail-closed Windows boundary step contract, not general YAML parsing."""
from pathlib import Path
import re


def check_windows_boundary(text):
    # Routing remains checked separately by workflow_topology.py.
    blocks = re.split(r"(?m)^      - ", text)[1:]
    for name, step_id, command in (
        ("Qualify Windows production and fault native boundaries", "native-boundary",
         "sh scripts/run_windows_native_boundary.sh . obj/windows-native-boundary"),
        ("Qualify immutable 0.1.0 release native boundaries", None,
         "sh scripts/qualify_windows_release.sh obj/windows-release-boundary"),
    ):
        identity = f"        id: {step_id}\n" if step_id else ""
        expected = f"name: {name}\n{identity}        run: {command}\n"
        matches = [block for block in blocks if block.startswith(f"name: {name}\n")]
        if len(matches) != 1 or matches[0].rstrip() != expected.rstrip():
            raise ValueError(f"mandatory unconditional Windows qualification step changed: {name}")
    # Evidence upload runs whenever qualification started and must then find
    # its reports; it is skipped only when an earlier step prevented the start.
    upload = [block for block in blocks
              if block.startswith("name: Preserve Windows native-boundary diagnostics\n")]
    started = ("        if: ${{ always() && contains(fromJSON('[\"success\",\"failure\","
               "\"cancelled\"]'), steps.native-boundary.outcome) }}\n")
    if (len(upload) != 1 or started not in upload[0]
            or len(re.findall(r"(?m)^        if:", upload[0])) != 1
            or "          if-no-files-found: error\n" not in upload[0]
            or "continue-on-error" in upload[0]):
        raise ValueError("Windows boundary diagnostics must upload, fail-closed, once qualification starts")
    if re.search(r"(?m)^    (?:if|continue-on-error|strategy):", text):
        raise ValueError("Windows qualification job cannot be conditional, optional or matrix-filtered")
    if "    defaults:\n      run:\n        shell: bash\n" not in text:
        raise ValueError("Windows boundary shell must propagate failures through bash")
    checkout = "      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n"
    if checkout not in text:
        raise ValueError("Windows release qualification requires full Git history")
    if "name: windows-native-boundary-${{ github.sha }}" not in text:
        raise ValueError("Windows boundary diagnostics must be preserved")


def check_windows_boundary_file(root: Path):
    check_windows_boundary((root / ".github/workflows/windows-post-merge.yml").read_text())