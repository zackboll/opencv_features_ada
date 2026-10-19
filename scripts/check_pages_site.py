#!/usr/bin/env python3
"""Qualify the enhanced site as the GitHub Pages artifact of the project site.

Run after scripts/enhance_docs.py. The site is published unchanged at
https://zackboll.github.io/opencv_features_ada/, so every reference must work
under the /opencv_features_ada/ prefix. Errors (exit 1):

* the file inventory differs from the reviewed one (native pages and stylesheet
  from docs/gnatdoc-native-anchors.json, enhancer files from
  docs/gnatdoc-enhanced-assets.json, guides from docs/site-map.json), or from
  the files and hashes that enhance_docs.py verified in this build;
* a symbolic link, hidden name, special file or non-site file type (no
  Markdown, Ada, project or script sources) is present;
* a reference is absolute, scheme-relative or root-relative, uses <base> or a
  meta refresh, or does not resolve under the prefix to a published file and,
  for HTML targets, an existing fragment; JavaScript contains a URL literal;
* a file contains a build path or credential-like text;
* with --archive: the uploaded Pages tar is not byte-identical to the site.

Publication readiness (not an error): every HTML page needs a non-empty
<title>. Pages without one are reported as deployment blockers, and
publication_ready is written to --github-output for the deployment job.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import stat
import sys
import tarfile
import urllib.parse
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
PAGES_URL = "https://zackboll.github.io/opencv_features_ada/"
SUFFIXES = {".html", ".css", ".js", ".json"}
URL_ATTRIBUTES = {"href", "src", "srcset", "action", "formaction", "poster", "data", "cite",
                  "background", "manifest", "longdesc", "usemap", "xlink:href"}
CREDENTIALS = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}|"
                         r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)|@import\s+(['\"])(.*?)\3", re.I)
# Independently SHA-256'd from Git blob
# 23cf51d3765e7b3f68411e25a57f52f4c0efc7e1:
# src/ada_gnatdoc_enhancer/assets/gnatdoc-navigation.js.
# This is source-owned policy, NEVER read from presentation.json or the
# output-side enhancement report. The full reviewed script uses the sole
# slash literal at line 103 as state.url.href.lastIndexOf('/'), not a URL.
# Authorize those exact bytes only; do not strip expressions or neighboring
# text and do not attempt to parse arbitrary JavaScript with a regex.
APPROVED_NAVIGATION = "api/gnatdoc-navigation.js"
APPROVED_NAVIGATION_SHA256 = "b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd"


class PagesError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.references, self.styles, self.problems = set(), [], [], []
        self.title, self.lang = None, None
        self._title = self._style = None

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value is not None:
                self.ids.add(value)
            elif name == "srcset" and value:
                self.references += [item.split()[0] for item in value.split(",") if item.split()]
            elif name in URL_ATTRIBUTES and value is not None:
                self.references.append(value)
            elif name == "style" and value:
                self.styles.append(value)
        attributes = dict(attrs)
        if tag == "html":
            self.lang = attributes.get("lang")
        if tag == "base":
            self.problems.append("<base> changes reference resolution")
        if tag == "meta" and (attributes.get("http-equiv") or "").lower() == "refresh":
            self.problems.append("meta refresh redirect")
        if tag == "title":
            self._title = ""
        if tag == "style":
            self._style = ""

    def handle_endtag(self, tag):
        if tag == "title" and self._title is not None:
            self.title, self._title = self._title.strip(), None
        if tag == "style" and self._style is not None:
            self.styles.append(self._style)
            self._style = None

    def handle_data(self, data):
        if self._title is not None:
            self._title += data
        if self._style is not None:
            self._style += data


def expected_files(root: Path = ROOT) -> set[str]:
    """The reviewed inventory: native API site plus the enhancer's added files."""
    anchors = json.loads((root / "docs/gnatdoc-native-anchors.json").read_text())
    assets = json.loads((root / "docs/gnatdoc-enhanced-assets.json").read_text())
    site_map = json.loads((root / "docs/site-map.json").read_text())
    return ({"api/index.html", "api/gnatdoc.css"}
            | {"api/" + package["page"] for package in anchors["packages"].values()}
            | set(assets["added_files"]) | {guide["path"] for guide in site_map["guides"]}
            | {site_map["home"], site_map["stylesheet"]})


def routes(root: Path = ROOT) -> list[str]:
    """Site-relative routes: home, API index, every guide and every package page."""
    anchors = json.loads((root / "docs/gnatdoc-native-anchors.json").read_text())
    site_map = json.loads((root / "docs/site-map.json").read_text())
    return (["", "api/index.html"] + [guide["path"] for guide in site_map["guides"]]
            + ["api/" + anchors["packages"][name]["page"] for name in sorted(anchors["packages"])])


def read_site(site: Path, errors: list[str]) -> dict[str, bytes]:
    """Regular files of the site; links, hidden names and special files are errors."""
    if site.is_symlink() or not site.is_dir():
        raise PagesError(f"{site} is not a directory")
    files = {}
    for directory, subdirectories, names in os.walk(site):
        for name in sorted(subdirectories + names):
            path = Path(directory) / name
            relative = path.relative_to(site).as_posix()
            if name.startswith("."):
                errors.append(f"hidden name {relative}")
            if path.is_symlink():
                errors.append(f"symbolic link {relative}")
            elif name in names:
                if not stat.S_ISREG(path.lstat().st_mode):
                    errors.append(f"special file {relative}")
                else:
                    files[relative] = path.read_bytes()
        subdirectories[:] = [d for d in subdirectories if not (Path(directory) / d).is_symlink()]
    return files


def read_archive(archive: Path) -> dict[str, bytes]:
    """Regular files of an uploaded Pages tar, by normalized site-relative path."""
    files = {}
    with tarfile.open(archive, "r:") as tar:
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts
            if member.name.startswith("/") or ".." in parts:
                raise PagesError(f"archive member {member.name} escapes the site")
            name = PurePosixPath(*[p for p in parts if p != "."]).as_posix() if parts else "."
            if member.isdir():
                continue
            if not member.isfile():
                raise PagesError(f"archive member {member.name} is not a regular file")
            if name in files:
                raise PagesError(f"archive member {name} is duplicated")
            files[name] = tar.extractfile(member).read()
    return files


def resolve(page: str, reference: str, files: dict[str, bytes], ids: dict[str, set[str]]) -> \
        str | None:
    """Resolve a reference as the browser would at PAGES_URL; return an error or None."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", reference, re.I) or reference.startswith(("/", "\\")) \
            or "\\" in reference:
        return f"{page}: absolute or root-relative reference {reference}"
    base = urllib.parse.urlsplit(PAGES_URL)
    target = urllib.parse.urlsplit(urllib.parse.urljoin(PAGES_URL + page, reference))
    if (target.scheme, target.netloc) != (base.scheme, base.netloc) or \
            not target.path.startswith(base.path):
        return f"{page}: {reference} resolves outside {PAGES_URL}"
    relative = urllib.parse.unquote(target.path[len(base.path):])
    if relative == "" or relative.endswith("/"):
        relative += "index.html"
    if relative not in files:
        return f"{page}: {reference} has no published file {relative}"
    fragment = urllib.parse.unquote(target.fragment)
    if fragment and relative.endswith(".html") and fragment not in ids[relative]:
        return f"{page}: {reference} has no fragment in {relative}"
    return None


def check(site: Path, expected: set[str], site_routes: list[str], enhancement: dict | None = None,
          archive: Path | None = None) -> dict:
    errors: list[str] = []
    files = read_site(site, errors)
    if set(files) != expected:
        errors.append(f"inventory: missing {sorted(expected - set(files))}, "
                      f"unexpected {sorted(set(files) - expected)}")
    hashes = {name: sha256(data) for name, data in sorted(files.items())}
    if enhancement is not None and hashes != enhancement.get("enhanced_site"):
        errors.append("the site differs from the files and hashes verified by enhance_docs.py")
    for name in files:
        if PurePosixPath(name).suffix not in SUFFIXES:
            errors.append(f"unpublishable file type {name}")
    leaks = {str(ROOT)} | {os.environ.get(v, "") for v in
                           ("HOME", "RUNNER_TEMP", "GITHUB_WORKSPACE", "RUNNER_WORKSPACE")}
    for name, data in files.items():
        text = data.decode("utf-8", "replace")
        if any(len(path) > 1 and path in text for path in leaks):
            errors.append(f"{name} contains a build path")
        if CREDENTIALS.search(text):
            errors.append(f"{name} contains credential-like text")
    pages = {}
    for name in sorted(n for n in files if n.endswith(".html")):
        page = _Page()
        page.feed(files[name].decode("utf-8"))
        page.close()
        pages[name] = page
    ids = {name: page.ids for name, page in pages.items()}
    references = fragments = 0
    for name, page in pages.items():
        errors += [f"{name}: {problem}" for problem in page.problems]
        found = page.references + [m[2] or m[4] for style in page.styles
                                   for m in CSS_URL.finditer(style)]
        for reference in found:
            references += 1
            fragments += "#" in reference
            if (error := resolve(name, reference, files, ids)) is not None:
                errors.append(error)
    for name in sorted(n for n in files if n.endswith(".css")):
        for match in CSS_URL.finditer(files[name].decode("utf-8")):
            references += 1
            if (error := resolve(name, match[2] or match[4], files, ids)) is not None:
                errors.append(error)
    for name in sorted(n for n in files if n.endswith(".js")):
        if name == APPROVED_NAVIGATION:
            if hashes[name] != APPROVED_NAVIGATION_SHA256:
                errors.append(f"{name}: JavaScript differs from the reviewed immutable Git blob")
        elif re.search(r"://|[\"'`]/", files[name].decode("utf-8")):
            errors.append(f"{name}: JavaScript contains an absolute or root-relative URL literal")
    for route in site_routes:
        if (error := resolve("", route, files, ids)) is not None:
            errors.append(f"route {error}")
    report = {"base_url": PAGES_URL, "files": hashes, "html_pages": len(pages),
              "references": references, "fragment_references": fragments,
              "routes": {PAGES_URL + route: route or "index.html" for route in site_routes}}
    if archive is not None:
        uploaded = read_archive(archive)
        if uploaded != files:
            errors.append(f"uploaded archive differs: missing {sorted(set(files) - set(uploaded))}, "
                          f"unexpected {sorted(set(uploaded) - set(files))}, changed "
                          f"{sorted(n for n in set(files) & set(uploaded) if files[n] != uploaded[n])}")
        report["archive"] = {"files": len(uploaded), "identical": uploaded == files}
    untitled = [name for name, page in pages.items() if not page.title]
    report.update(titles={name: page.title for name, page in pages.items()},
                  pages_without_title=untitled,
                  pages_without_lang=[name for name, page in pages.items() if not page.lang],
                  blockers=[f"{len(untitled)} of {len(pages)} HTML pages have no <title>: "
                            + ", ".join(untitled)] if untitled else [],
                  errors=errors)
    report["publication_ready"] = not errors and not untitled
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", type=Path, default=ROOT / "_site-enhanced")
    parser.add_argument("--enhancement", type=Path, default=ROOT / "obj/docs/enhancement.json",
                        help="report of scripts/enhance_docs.py for this site")
    parser.add_argument("--archive", type=Path, help="tar built by upload-pages-artifact")
    parser.add_argument("--report", type=Path, default=ROOT / "obj/docs/pages.json")
    parser.add_argument("--github-output", type=Path,
                        help="append publication_ready and blockers (GitHub Actions)")
    args = parser.parse_args(argv)
    try:
        enhancement = json.loads(args.enhancement.read_text())
        report = check(args.site.resolve(), expected_files(), routes(), enhancement, args.archive)
    except (PagesError, OSError, KeyError, UnicodeError, json.JSONDecodeError,
            tarfile.TarError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.github_output is not None:
        with args.github_output.open("a") as output:
            output.write(f"publication_ready={str(report['publication_ready']).lower()}\n"
                         f"blockers={'; '.join(report['blockers'] + report['errors'])}\n")
    if report["errors"]:
        print("FAIL:\n  " + "\n  ".join(report["errors"]), file=sys.stderr)
        return 1
    archive = " uploaded archive identical;" if args.archive is not None else ""
    print(f"PASS: {len(report['files'])} files ({report['html_pages']} pages); "
          f"{report['references']} references and {len(report['routes'])} routes resolve under "
          f"{PAGES_URL};{archive} publication "
          + ("ready" if report["publication_ready"] else "BLOCKED: " + "; ".join(report["blockers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
