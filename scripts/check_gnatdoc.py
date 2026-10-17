#!/usr/bin/env python3
"""Features-owned GNATdoc qualification: inventory, anchors, warnings, coverage.

Subcommands (all exit 1 with a diagnostic on failure):

  inventory  Source-backed public declaration inventory compared exactly with
             docs/gnatdoc-declarations.json (a public API freeze for documentation
             changes). --capture writes the file only when it is absent.
  site       Strict native site validation: file inventory, packages, internal
             exclusion, local links/fragments, stylesheet identity, one native
             section per source declaration, and anchors compared exactly with
             docs/gnatdoc-native-anchors.json.
  warnings   Stable, line-independent warning identities compared with a
             ceiling baseline: new warnings fail; resolved ones are reported
             as stale and fail only with --strict.
  coverage   Rendered versus meaningfully documented elements, with the same
             ceiling-baseline policy for undocumented elements.
  all        Run every check with the repository default paths.
  markdown   Print Markdown tables from the generated JSON reports.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gnatdoc_native as native  # noqa: E402
import gnatdoc_source as source  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = "GNATdoc 26.0.0 (20260415)"
DECLARATIONS = "docs/gnatdoc-declarations.json"
ANCHORS = "docs/gnatdoc-native-anchors.json"
WARNINGS = "docs/gnatdoc-warning-baseline.txt"
COVERAGE = "docs/gnatdoc-coverage-baseline.txt"
GROUPS = {"parameter": "Parameters", "return": "Return Value",
          "field": "Record fields", "literal": "Enumeration Literal"}
DECLARATION_WORDS = 3
MEMBER_WORDS = 2


class CheckError(ValueError):
    pass


def _json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _write_absent(path: Path, text: str) -> None:
    if path.exists():
        raise CheckError(f"{path} exists; baselines are only captured when absent")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _report(path: Path | None, value) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json(value), encoding="utf-8")


# --------------------------------------------------------------------------
# Declaration inventory

def public(specs: dict[str, source.Specification]) -> dict[str, source.Specification]:
    return {name: spec for name, spec in specs.items() if spec.visibility == "public"}


def declarations_inventory(specs) -> dict:
    owned = source.ownership_types(specs)
    packages = {}
    for name, spec in sorted(public(specs).items()):
        items = []
        for declaration in spec.declarations:
            items.append({
                "identity": declaration.identity,
                "name": declaration.name,
                "kind": declaration.kind,
                "category": declaration.category,
                "signature": declaration.signature,
                "members": [{key: value for key, value in vars(member).items()
                             if value is not None} for member in declaration.members],
                "ownership_sensitive": source.ownership_sensitive(declaration, owned),
            })
        packages[name] = {"source": spec.relative, "declarations": items}
    internal = {name: spec.relative for name, spec in sorted(specs.items())
                if spec.visibility == "internal"}
    return {"schema_version": 1, "public_packages": packages, "internal_units": internal}


def evidence_inventory(specs) -> dict:
    """Line, hash and existing-comment evidence; generated, never committed."""
    result = declarations_inventory(specs)
    for name, spec in specs.items():
        entry = result["public_packages"].get(name)
        if entry is None:
            continue
        entry["sha256"] = spec.sha256
        entry["description_block"] = spec.description_lines
        for item, declaration in zip(entry["declarations"], spec.declarations):
            item["line"] = declaration.line
            item["existing_comment"] = declaration.comment_lines
            item["comment_shared_with_package"] = (
                declaration.comment_start is not None
                and declaration.comment_start == spec.description_start)
    result["internal_sha256"] = {spec.relative: spec.sha256 for spec in specs.values()
                                 if spec.visibility == "internal"}
    return result


def check_inventory(root: Path, expected: Path, capture: bool, report: Path | None) -> dict:
    specs = source.specifications(root)
    actual = declarations_inventory(specs)
    _report(report, evidence_inventory(specs))
    if capture:
        _write_absent(expected, _json(actual))
    recorded = json.loads(expected.read_text(encoding="utf-8"))
    if recorded != actual:
        differences = _differences(recorded, actual)
        raise CheckError("public declaration inventory changed:\n  " + "\n  ".join(differences))
    total = sum(len(p["declarations"]) for p in actual["public_packages"].values())
    return {"packages": len(actual["public_packages"]), "declarations": total,
            "internal_units": len(actual["internal_units"])}


def _differences(recorded: dict, actual: dict) -> list[str]:
    def flat(value):
        result = {}
        for package, entry in value.get("public_packages", {}).items():
            result[f"package {package}"] = entry.get("source")
            for item in entry.get("declarations", []):
                result[item["identity"]] = json.dumps(item, sort_keys=True)
        for unit, path in value.get("internal_units", {}).items():
            result[f"internal {unit}"] = path
        return result
    old, new = flat(recorded), flat(actual)
    lines = [f"removed: {key}" for key in sorted(old.keys() - new.keys())]
    lines += [f"added: {key}" for key in sorted(new.keys() - old.keys())]
    lines += [f"changed: {key}" for key in sorted(old.keys() & new.keys()) if old[key] != new[key]]
    return lines or ["schema or ordering differs"]


# --------------------------------------------------------------------------
# Native site

def _native_signature(code: str) -> str:
    return source.code_signature(source.code(source.lex(code)))


def match_sections(specs, pages) -> dict[str, tuple[native.Page, native.Section]]:
    """Map every public source declaration to exactly one native section."""
    matched: dict[str, tuple[native.Page, native.Section]] = {}
    for name, spec in public(specs).items():
        page = pages.get(name)
        if page is None:
            raise CheckError(f"public package {name} has no native page")
        remaining = list(page.sections)
        for declaration in spec.declarations:
            candidates = [s for s in remaining if s.name == declaration.name
                          and _native_signature(s.code) == declaration.signature]
            if len(candidates) != 1:
                raise CheckError(
                    f"{declaration.identity}: expected one native section, found "
                    f"{len(candidates)}")
            remaining.remove(candidates[0])
            matched[declaration.identity] = (page, candidates[0])
        if remaining:
            raise CheckError(f"{name}: native sections without source declarations: "
                             f"{[s.name for s in remaining]}")
    return matched


def anchors_manifest(api: Path, specs, index, pages, matched) -> dict:
    return {
        "schema_version": 1,
        "generator": GENERATOR,
        "stylesheet_sha256": hashlib.sha256((api / "gnatdoc.css").read_bytes()).hexdigest(),
        "packages": {name: {"page": page.file, "source": specs[name].relative}
                     for name, page in sorted(pages.items())},
        "declarations": {identity: {"page": page.file, "anchor": section.anchor}
                         for identity, (page, section) in sorted(matched.items())},
        "tagged_types": sorted(f"{label} {href}" for label, href in index.tagged),
    }


def validate_site(api: Path, specs, index, pages) -> None:
    if api.is_symlink() or not api.is_dir():
        raise CheckError(f"{api} is not a native output directory")
    expected = {"index.html", "gnatdoc.css"} | {page.file for page in pages.values()}
    present = set()
    for path in api.iterdir():
        if path.is_symlink() or not path.is_file():
            raise CheckError(f"unexpected non-file site entry {path.name}")
        present.add(path.name)
    if present != expected:
        raise CheckError(f"site file inventory differs: extra {sorted(present - expected)}, "
                         f"missing {sorted(expected - present)}")
    packages = sorted(public(specs))
    units = sorted(name for name, _ in index.units)
    if units != packages:
        raise CheckError(f"native packages {units} differ from public sources {packages}")
    for name, spec in specs.items():
        if spec.visibility == "internal" and name in pages:
            raise CheckError(f"internal unit {name} was published")
    if any(".Internal" in name or name.startswith("OpenCV.Core") for name in units):
        raise CheckError("internal or Core packages appear in the native index")
    if len(units) != len(set(units)):
        raise CheckError("duplicate compilation units in the index")
    for href in index.links:
        _check_link(api, "index.html", href, pages)
    declared = {d.qualified for s in public(specs).values() for d in s.declarations
                if d.category == "private" and "tagged" in d.signature.split()}
    if sorted(label for label, _ in index.tagged) != sorted(declared):
        raise CheckError("tagged-type index differs from public tagged declarations")
    for page in pages.values():
        if len(page.ids) != len(set(page.ids)):
            raise CheckError(f"{page.file}: duplicate ids")
        if sorted((n, a) for _, n, a in page.entities) != sorted(
                (s.name, s.anchor) for s in page.sections):
            raise CheckError(f"{page.file}: entity list differs from declaration sections")
        for href in page.links:
            _check_link(api, page.file, href, pages)
        if "a.target" in page.attributes or any(
                attribute.endswith((".style", ".src", ".onclick", ".onload"))
                for attribute in page.attributes):
            raise CheckError(f"{page.file}: unexpected active or styled attributes")


def _check_link(api: Path, origin: str, href: str, pages) -> None:
    if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("//"):
        raise CheckError(f"{origin}: external URL {href!r}")
    target, _, fragment = href.partition("#")
    target = target or origin
    if target == "gnatdoc.css" and not fragment:
        return
    if "/" in target or not (api / target).is_file():
        raise CheckError(f"{origin}: unresolved link {href!r}")
    if fragment:
        page = next((p for p in pages.values() if p.file == target), None)
        if target == "index.html":
            ids = native.read_index(api / target).ids
        elif page is None:
            raise CheckError(f"{origin}: fragment into unknown page {href!r}")
        else:
            ids = page.ids
        if fragment not in ids:
            raise CheckError(f"{origin}: unresolved fragment {href!r}")


def check_site(root: Path, api: Path, anchors: Path, capture: bool) -> dict:
    specs = source.specifications(root)
    index, pages = native.read_site(api)
    validate_site(api, specs, index, pages)
    matched = match_sections(specs, pages)
    manifest = anchors_manifest(api, specs, index, pages, matched)
    if capture:
        _write_absent(anchors, _json(manifest))
    recorded = json.loads(anchors.read_text(encoding="utf-8"))
    if recorded != manifest:
        changed = sorted(key for key in set(recorded) | set(manifest)
                         if recorded.get(key) != manifest.get(key))
        detail = []
        if "declarations" in changed:
            old, new = recorded.get("declarations", {}), manifest["declarations"]
            detail = [f"{k}: {old.get(k)} -> {new.get(k)}"
                      for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
        raise CheckError(f"native anchors/identities changed in {changed}:\n  "
                         + "\n  ".join(detail))
    return {"packages": len(pages), "sections": len(matched),
            "files": len(list(api.iterdir()))}


# --------------------------------------------------------------------------
# Warnings

_WARNING = re.compile(r"^(?P<file>[^:\s]+):(?P<line>\d+):(?P<column>\d+): warning: (?P<message>.+)$")


def _declaration_at(spec: source.Specification, line: int, column: int) -> tuple[str, str]:
    """(scope, signature) of the declaration whose defining name is at line:column."""
    tokens = source.code(spec.tokens)
    position = next((i for i, t in enumerate(tokens)
                     if t.line == line and t.column == column), None)
    if position is None or tokens[position].kind != "identifier":
        raise CheckError(f"{spec.relative}:{line}:{column}: warning is not at a name")
    if line == spec.header_line or (position > 0 and tokens[position - 1].text.lower() == "package"
                                    and tokens[position - 1].line == spec.header_line):
        return spec.package, "package"
    start = position
    while start > 0 and tokens[start - 1].text.lower() not in (";", "is", "private"):
        start -= 1
    end = position
    depth = 0
    while end < len(tokens):
        text = tokens[end].text.lower()
        if text in ("(", "["):
            depth += 1
        elif text in (")", "]"):
            depth -= 1
        elif (text == "record" and depth == 0
              and tokens[end - 1].text.lower() != "end"
              and not (tokens[end - 1].text.lower() == "null")):
            while not (tokens[end].text.lower() == "record"
                       and tokens[end - 1].text.lower() == "end"):
                end += 1
        elif text == ";" and depth == 0:
            break
        end += 1
    signature = source.code_signature(tokens[start:end + 1])
    return f"{spec.package}.{tokens[position].text}", signature


def warning_identities(log: str, specs) -> list[dict]:
    by_file = {Path(spec.relative).name: spec for spec in specs.values()}
    result = []
    for raw in log.splitlines():
        if not raw.strip():
            continue
        match = _WARNING.match(raw)
        if match is None:
            raise CheckError(f"unclassified GNATdoc diagnostic: {raw}")
        spec = by_file.get(match["file"])
        if spec is None:
            raise CheckError(f"warning outside the Features specifications: {raw}")
        line, column = int(match["line"]), int(match["column"])
        scope, signature = _declaration_at(spec, line, column)
        if spec.visibility == "internal":
            region = "internal-unit"
        elif spec.private_line is not None and line > spec.private_line:
            region = "private-part"
        else:
            region = "public"
        result.append({"identity": f"{match['file']}: {scope}: {signature}: {match['message']}",
                       "region": region, "raw": raw})
    return result


def check_warnings(root: Path, log: Path, baseline: Path, capture: bool, strict: bool,
                   report: Path | None) -> dict:
    specs = source.specifications(root)
    warnings = warning_identities(log.read_text(encoding="utf-8"), specs)
    actual = collections.Counter(w["identity"] for w in warnings)
    if capture:
        _write_absent(baseline, "".join(f"{i}\n" for i in sorted(actual.elements())))
    recorded = collections.Counter(baseline.read_text(encoding="utf-8").splitlines())
    added = sorted((actual - recorded).elements())
    stale = sorted((recorded - actual).elements())
    regions = collections.Counter(w["region"] for w in warnings)
    summary = {"raw": len(warnings), "regions": dict(sorted(regions.items())),
               "baseline": sum(recorded.values()), "new": added, "stale": stale}
    _report(report, {**summary, "warnings": warnings})
    if added:
        raise CheckError("new GNATdoc warnings:\n  " + "\n  ".join(added))
    if strict and stale:
        raise CheckError("stale warning baseline entries:\n  " + "\n  ".join(stale))
    return summary


# --------------------------------------------------------------------------
# Coverage

def coverage_elements(specs, pages, matched) -> list[dict]:
    elements = []
    for name, spec in sorted(public(specs).items()):
        page = pages[name]
        shared = {d.comment_start for d in spec.declarations} & {spec.description_start}
        package_text = source.normalize(" ".join(spec.description_lines))
        rendered = page.description is not None
        element = {"package": name, "identity": f"{name}|package|description",
                   "category": "package", "rendered": rendered}
        element.update(_credit(page.description or "", package_text, DECLARATION_WORDS,
                               bool(shared) and spec.description_start is not None,
                               spec.description_start is not None))
        elements.append(element)
        for declaration in spec.declarations:
            page_, section = matched[declaration.identity]
            docs = source.split_tags(declaration.comment_lines)
            block_shared = (declaration.comment_start is not None
                            and declaration.comment_start == spec.description_start)
            has_block = declaration.comment_start is not None
            element = {"package": name, "identity": f"{declaration.identity}|description",
                       "category": declaration.kind, "rendered": True}
            element.update(_credit(section.description, docs.description, DECLARATION_WORDS,
                                   block_shared, has_block))
            if docs.duplicates:
                element.update(documented=False, reason=f"duplicate tags {docs.duplicates}")
            elements.append(element)
            elements.extend(_members(name, declaration, section, docs, block_shared, has_block))
            _check_exceptions(declaration, section, docs)
    return elements


def _members(package, declaration, section, docs, block_shared, has_block) -> list[dict]:
    result = []
    expected = collections.defaultdict(list)
    for member in declaration.members:
        expected[GROUPS[member.kind]].append(member)
    actual_groups = {k: v for k, v in section.groups.items() if k != "Raised exceptions"}
    if set(actual_groups) != set(expected):
        raise CheckError(f"{declaration.identity}: native member groups "
                         f"{sorted(actual_groups)} differ from {sorted(expected)}")
    for group, members in expected.items():
        entries = actual_groups[group]
        if len(entries) != len(members):
            raise CheckError(f"{declaration.identity}: {group} count differs")
        for member, (term, text) in zip(members, entries):
            if member.kind != "return" and (term or "").lower() != member.name.lower():
                raise CheckError(f"{declaration.identity}: native {group} {term!r} "
                                 f"differs from source {member.name!r}")
            tag = {"parameter": "param", "field": "field", "literal": "enum",
                   "return": "return"}[member.kind]
            key = (tag, member.name.lower() if member.name else None)
            suffix = "return" if member.kind == "return" else f"{member.kind}:{member.name}"
            element = {"package": package, "identity": f"{declaration.identity}|{suffix}",
                       "category": member.kind, "rendered": True}
            element.update(_credit(text, docs.tags.get(key, ""), MEMBER_WORDS,
                                   block_shared, has_block and key in docs.tags))
            result.append(element)
    return result


def _check_exceptions(declaration, section, docs) -> None:
    rendered = section.groups.get("Raised exceptions", [])
    tagged = {name: text for (tag, name), text in docs.tags.items() if tag == "exception"}
    actual = {(term or "").lower(): text for term, text in rendered}
    if set(actual) != set(tagged):
        raise CheckError(f"{declaration.identity}: rendered exceptions {sorted(actual)} "
                         f"differ from @exception tags {sorted(tagged)}")
    for name, text in tagged.items():
        if source.normalize(actual[name]) != text:
            raise CheckError(f"{declaration.identity}: @exception {name} text differs")


def _credit(rendered: str, attached: str, words: int, shared: bool, has_source: bool) -> dict:
    rendered = source.normalize(rendered)
    if not rendered:
        return {"documented": False, "reason": "no rendered prose"}
    if not has_source:
        return {"documented": False, "reason": "rendered prose without an attached source block"}
    if shared:
        return {"documented": False,
                "reason": "source block is shared by the package description and a declaration"}
    if rendered != attached:
        return {"documented": False, "reason": "rendered prose differs from attached source"}
    if not source.meaningful(rendered, words):
        return {"documented": False, "reason": f"fewer than {words} words besides SPDX"}
    return {"documented": True}


def coverage_summary(elements: list[dict]) -> dict:
    def tally(items):
        return {"elements": len(items), "rendered": sum(e["rendered"] for e in items),
                "documented": sum(e["documented"] for e in items)}
    by_package = collections.defaultdict(list)
    by_category = collections.defaultdict(list)
    for element in elements:
        by_package[element["package"]].append(element)
        by_category[element["category"]].append(element)
    total = tally(elements)
    total["percent"] = round(100.0 * total["documented"] / total["elements"], 4)
    return {"total": total,
            "packages": {k: tally(v) for k, v in sorted(by_package.items())},
            "categories": {k: tally(v) for k, v in sorted(by_category.items())}}


def check_coverage(root: Path, api: Path, baseline: Path, capture: bool, strict: bool,
                   report: Path | None) -> dict:
    specs = source.specifications(root)
    index, pages = native.read_site(api)
    matched = match_sections(specs, pages)
    elements = coverage_elements(specs, pages, matched)
    gaps = sorted(e["identity"] for e in elements if not e["documented"])
    if len(gaps) != len(set(gaps)):
        raise CheckError("duplicate coverage identities")
    if capture:
        _write_absent(baseline, "".join(f"{gap}\n" for gap in gaps))
    recorded = baseline.read_text(encoding="utf-8").splitlines()
    added = sorted(set(gaps) - set(recorded))
    stale = sorted(set(recorded) - set(gaps))
    summary = coverage_summary(elements)
    summary.update(new_gaps=added, stale_baseline=stale, baseline=len(recorded))
    _report(report, {**summary, "elements": elements})
    if added:
        raise CheckError("new documentation gaps:\n  " + "\n  ".join(added))
    if strict and stale:
        raise CheckError("stale coverage baseline entries:\n  " + "\n  ".join(stale))
    return summary


# --------------------------------------------------------------------------
# Markdown summary of the generated reports (CI step summary and records)

def markdown(reports: Path) -> str:
    coverage = json.loads((reports / "coverage.json").read_text(encoding="utf-8"))
    warnings = json.loads((reports / "warnings.json").read_text(encoding="utf-8"))
    total = coverage["total"]
    lines = ["| Package | Elements | Rendered | Documented |", "| --- | ---: | ---: | ---: |"]
    for name, tally in coverage["packages"].items():
        lines.append(f"| `{name}` | {tally['elements']} | {tally['rendered']} | "
                     f"{tally['documented']} |")
    lines += ["", f"Total: {total['elements']} elements; {total['rendered']} rendered; "
              f"{total['documented']} documented ({total['percent']}%); "
              f"{total['elements'] - total['documented']} gaps.", "",
              "| Element category | Elements | Rendered | Documented |",
              "| --- | ---: | ---: | ---: |"]
    for name, tally in coverage["categories"].items():
        lines.append(f"| {name} | {tally['elements']} | {tally['rendered']} | "
                     f"{tally['documented']} |")
    reasons = collections.Counter(e.get("reason") for e in coverage["elements"]
                                  if not e["documented"])
    lines += ["", "| Gap reason | Count |", "| --- | ---: |"]
    lines += [f"| {reason} | {count} |" for reason, count in sorted(reasons.items())]
    regions = ", ".join(f"{count} {region}" for region, count in warnings["regions"].items())
    lines += ["", f"Warnings: {warnings['raw']} raw ({regions}); new: {len(warnings['new'])}; "
              f"stale baseline entries: {len(warnings['stale'])}.",
              f"Coverage baseline: {coverage['baseline']} gaps; new: "
              f"{len(coverage['new_gaps'])}; stale: {len(coverage['stale_baseline'])}."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("inventory", "site", "warnings", "coverage", "all",
                                            "markdown"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--api", type=Path, help="native GNATdoc output (default _site/api)")
    parser.add_argument("--log", type=Path, help="GNATdoc log (default obj/docs/gnatdoc.log)")
    parser.add_argument("--reports", type=Path, help="report directory (default obj/docs)")
    parser.add_argument("--capture", action="store_true",
                        help="create absent baselines from the current output")
    parser.add_argument("--strict", action="store_true",
                        help="also fail on stale (resolved) baseline entries")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    api = args.api or root / "_site/api"
    log = args.log or root / "obj/docs/gnatdoc.log"
    reports = args.reports or root / "obj/docs"
    if args.command == "markdown":
        print(markdown(reports), end="")
        return 0
    commands = (["inventory", "site", "warnings", "coverage"]
                if args.command == "all" else [args.command])
    try:
        for command in commands:
            if command == "inventory":
                result = check_inventory(root, root / DECLARATIONS, args.capture,
                                         reports / "inventory.json")
            elif command == "site":
                result = check_site(root, api, root / ANCHORS, args.capture)
            elif command == "warnings":
                result = check_warnings(root, log, root / WARNINGS, args.capture, args.strict,
                                        reports / "warnings.json")
            else:
                result = check_coverage(root, api, root / COVERAGE, args.capture, args.strict,
                                        reports / "coverage.json")
            print(f"PASS {command}: {json.dumps(result, sort_keys=True)}")
    except (CheckError, source.SourceError, native.NativeError, OSError,
            json.JSONDecodeError) as error:
        print(f"FAIL {command}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
