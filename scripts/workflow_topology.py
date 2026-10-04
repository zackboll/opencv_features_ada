"""Fail-closed checks of workflow routing, without a general YAML dependency.

Only trigger metadata and job/runner declarations are parsed. Trigger metadata
supports block mappings/sequences, flow mappings/sequences, quoted scalars and
comments. Anchors, tags, aliases, multiline scalars and expressions there are
deliberately rejected: changing routing syntax requires reviewing this checker.
Step scripts are opaque; they cannot be mistaken for workflow declarations.
"""
from pathlib import Path
import re


def tokens(text):
    pattern = r'''\s*(?:('(?:[^']|'')*'|"(?:[^"\\]|\\.)*"|[^\s\[\]{},:#]+)|([\[\]{},:])|(#.*$))'''
    result = []
    position = 0
    while position < len(text.rstrip()):
        match = re.match(pattern, text[position:])
        if not match:
            raise ValueError(f"unsupported routing syntax: {text}")
        position += match.end()
        if match[3]:
            break
        result.append(match[1] or match[2])
    return result


def scalar(token):
    if token.startswith("'"):
        return token[1:-1].replace("''", "'")
    if token.startswith('"'):
        import json
        return json.loads(token)
    if not re.fullmatch(r"[A-Za-z0-9_./*-]+", token):
        raise ValueError(f"unsupported routing scalar: {token}")
    return token


def flow(items):
    def value():
        if not items:
            raise ValueError("incomplete routing value")
        token = items.pop(0)
        if token not in {"[", "{"}:
            return scalar(token)
        mapping = token == "{"
        end = "}" if mapping else "]"
        result = {} if mapping else []
        while items and items[0] != end:
            if mapping:
                key = scalar(items.pop(0))
                if not items or items.pop(0) != ":" or key in result:
                    raise ValueError("invalid/duplicate routing key")
                if not items:
                    raise ValueError("incomplete routing mapping")
                result[key] = None if items[0] in {",", end} else value()
            else:
                result.append(value())
            if items and items[0] != end:
                if items.pop(0) != ",":
                    raise ValueError("missing routing separator")
        if not items or items.pop(0) != end:
            raise ValueError("unterminated routing collection")
        return result
    result = value()
    if items:
        raise ValueError("extra routing tokens")
    return result


def sections(text):
    result = {}
    current = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[:len(line) - len(line.lstrip())]:
            raise ValueError("tabs in workflow indentation")
        if not line.startswith(" "):
            parts = tokens(line)
            if len(parts) < 2 or parts[1] != ":":
                raise ValueError("workflow must use top-level block mappings")
            current = scalar(parts[0])
            if current in result:
                raise ValueError("duplicate workflow section")
            result[current] = (parts[2:], [])
        else:
            if current is None:
                raise ValueError("missing workflow section")
            result[current][1].append(line)
    return result


def triggers(section):
    inline, lines = section
    if inline:
        if lines:
            raise ValueError("mixed block/flow triggers")
        return flow(inline.copy())
    entries = [(len(line) - len(line.lstrip()), tokens(line.strip()))
               for line in lines]
    def block(position, indent):
        sequence = entries[position][1][0] == "-"
        result = [] if sequence else {}
        while position < len(entries) and entries[position][0] == indent:
            parts = entries[position][1]
            position += 1
            if sequence:
                if parts[0] != "-":
                    raise ValueError("mixed routing mapping/sequence")
                result.append(flow(parts[1:].copy()))
            else:
                if len(parts) < 2 or parts[1] != ":":
                    raise ValueError("invalid routing mapping")
                key = scalar(parts[0])
                if key in result:
                    raise ValueError("duplicate trigger key")
                if parts[2:]:
                    result[key] = flow(parts[2:].copy())
                elif position < len(entries) and entries[position][0] > indent:
                    result[key], position = block(position, entries[position][0])
                else:
                    result[key] = None
        return result, position
    if not entries:
        raise ValueError("empty workflow triggers")
    result, position = block(0, entries[0][0])
    if position != len(entries):
        raise ValueError("unsupported trigger indentation")
    return result


def check_topology(cross_text, windows_text, compatibility_text):
    cross = sections(cross_text)
    windows = sections(windows_text)
    compatibility = sections(compatibility_text)
    for workflow, expected in ((cross, {"pull_request", "push", "workflow_dispatch"}),
                               (windows, {"push"}),
                               (compatibility, {"workflow_dispatch"})):
        events = triggers(workflow["on"])
        names = set(events) if isinstance(events, (dict, list)) else {events}
        if names != expected:
            raise ValueError(f"unexpected workflow triggers: {names}, expected {expected}")
        if "push" in expected:
            if not isinstance(events, dict) or events["push"] != {"branches": ["main"]}:
                raise ValueError("push must target main only, without path/tag filters")
    inline, lines = cross["jobs"]
    if inline or not lines:
        raise ValueError("PR jobs must use block mappings")
    indent = min(len(line) - len(line.lstrip()) for line in lines)
    jobs = {}
    current = None
    for line in lines:
        level = len(line) - len(line.lstrip())
        if level == indent:
            parts = tokens(line.strip())
            if len(parts) != 2 or parts[1] != ":":
                raise ValueError("PR job declarations must be block mappings")
            current = scalar(parts[0])
            if current in jobs:
                raise ValueError("duplicate PR job")
            jobs[current] = []
        else:
            jobs[current].append((level, line.strip()))
    expected = {"repository-checks": "ubuntu-24.04", "linux": "ubuntu-24.04",
                "macos": "macos-14", "linux-sanitizers": "ubuntu-24.04"}
    if set(jobs) != set(expected):
        raise ValueError("PR workflow must contain repository-checks, linux, macos, linux-sanitizers only")
    for name, body in jobs.items():
        level = min(indent for indent, _ in body)
        runners = []
        for indent, line in body:
            if indent != level:
                continue
            parts = tokens(line)
            if parts[:2] == ["runs-on", ":"]:
                runners.append(flow(parts[2:].copy()))
            if parts[:2] == ["strategy", ":"]:
                raise ValueError("PR runner matrices require topology review")
        if runners != [expected[name]]:
            raise ValueError(f"unexpected PR runner for {name}: {runners}")


def check_workflows(directory: Path):
    check_topology(*( (directory / name).read_text() for name in
                    ("cross-platform.yml", "windows-post-merge.yml",
                     "opencv-compatibility.yml")))