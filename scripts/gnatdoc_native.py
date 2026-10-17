"""Strict reader for the native GNATdoc 26.0.0 HTML backend output.

Only the observed page shape is accepted: one index with Compilation Units
and Tagged Types lists, and one page per package with an entity table of
contents, an optional package description and h4 declaration sections.
Unknown structure fails instead of being interpreted permissively.
"""
from __future__ import annotations

import dataclasses
import html.parser
from pathlib import Path


class NativeError(ValueError):
    """Native output differs from the qualified GNATdoc page shape."""


@dataclasses.dataclass
class Event:
    kind: str  # start, end, data
    tag: str = ""
    attributes: dict[str, str | None] = dataclasses.field(default_factory=dict)
    text: str = ""


class _Collector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[Event] = []

    def handle_starttag(self, tag, attrs):
        self.events.append(Event("start", tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.events.append(Event("start", tag, dict(attrs)))
        self.events.append(Event("end", tag))

    def handle_endtag(self, tag):
        self.events.append(Event("end", tag))

    def handle_data(self, data):
        self.events.append(Event("data", text=data))

    def handle_comment(self, data):
        raise NativeError("unexpected HTML comment in native output")

    def handle_pi(self, data):
        raise NativeError("unexpected processing instruction in native output")


def events(text: str) -> list[Event]:
    collector = _Collector()
    collector.feed(text)
    collector.close()
    return collector.events


def normalize(text: str) -> str:
    return " ".join(text.split())


@dataclasses.dataclass
class Section:
    anchor: str
    name: str
    code: str
    description: str
    groups: dict[str, list[tuple[str | None, str]]]


@dataclasses.dataclass
class Page:
    file: str
    package: str
    entities: list[tuple[str, str, str]]  # category, name, anchor
    description: str | None
    sections: list[Section]
    ids: list[str]
    links: list[str]
    tags: set[str]
    attributes: set[str]


@dataclasses.dataclass
class Index:
    units: list[tuple[str, str]]  # package, page
    tagged: list[tuple[str, str]]  # qualified name, href
    links: list[str]
    ids: list[str]


_PAGE_TAGS = {"html", "link", "body", "h1", "h2", "h3", "h4", "h5", "ul", "li", "a",
              "p", "pre", "code", "dl", "dt", "dd"}
_INDEX_TAGS = {"html", "link", "body", "div", "ul", "li", "a", "h2", "iframe"}


def _text(items: list[Event]) -> str:
    return normalize(" ".join(e.text for e in items if e.kind == "data"))


def read_index(path: Path) -> Index:
    stream = events(path.read_text(encoding="utf-8"))
    unknown = {e.tag for e in stream if e.kind == "start"} - _INDEX_TAGS
    if unknown:
        raise NativeError(f"{path.name}: unexpected tags {sorted(unknown)}")
    units: list[tuple[str, str]] = []
    tagged: list[tuple[str, str]] = []
    links: list[str] = []
    ids = [e.attributes["id"] for e in stream if e.kind == "start" and "id" in e.attributes]
    section = None
    position = 0
    while position < len(stream):
        event = stream[position]
        if event.kind == "start" and event.tag == "h2":
            section = event.attributes.get("id")
        if event.kind == "start" and event.tag == "a":
            href = event.attributes.get("href") or ""
            links.append(href)
            end = next(i for i in range(position, len(stream))
                       if stream[i].kind == "end" and stream[i].tag == "a")
            label = _text(stream[position + 1:end])
            if event.attributes.get("target") == "document-content":
                if section == "compilation-units":
                    units.append((label, href))
                elif section == "tagged-types":
                    tagged.append((label, href))
                else:
                    raise NativeError(f"{path.name}: link outside known index lists")
            position = end
        position += 1
    if not units:
        raise NativeError(f"{path.name}: no compilation units")
    return Index(units, tagged, links, ids)


def read_page(path: Path) -> Page:
    stream = events(path.read_text(encoding="utf-8"))
    tags = {e.tag for e in stream if e.kind == "start"}
    unknown = tags - _PAGE_TAGS
    if unknown:
        raise NativeError(f"{path.name}: unexpected tags {sorted(unknown)}")
    attributes = {f"{e.tag}.{name}" for e in stream if e.kind == "start"
                  for name in e.attributes}
    ids = [e.attributes["id"] for e in stream if e.kind == "start" and "id" in e.attributes]
    links = [e.attributes.get("href") or "" for e in stream
             if e.kind == "start" and e.tag in ("a", "link")]
    h1 = [i for i, e in enumerate(stream) if e.kind == "start" and e.tag == "h1"]
    if len(h1) != 1:
        raise NativeError(f"{path.name}: expected exactly one h1")
    package = _text(stream[h1[0] + 1:_close(stream, h1[0], "h1")])
    entities: list[tuple[str, str, str]] = []
    description = None
    sections: list[Section] = []
    position = _close(stream, h1[0], "h1") + 1
    mode = None
    category = None
    while position < len(stream):
        event = stream[position]
        if event.kind == "start" and event.tag == "h2":
            end = _close(stream, position, "h2")
            mode = _text(stream[position + 1:end])
            if mode not in ("Entities", "Description"):
                raise NativeError(f"{path.name}: unexpected h2 {mode!r}")
            if mode == "Description":
                stop = _next_start(stream, end, "h4")
                description = _text(stream[end + 1:stop])
                position = stop
                continue
            position = end
        elif event.kind == "start" and event.tag == "h3":
            if mode != "Entities":
                raise NativeError(f"{path.name}: h3 outside the entity list")
            end = _close(stream, position, "h3")
            category = _text(stream[position + 1:end])
            position = end
        elif event.kind == "start" and event.tag == "a" and mode == "Entities":
            end = _close(stream, position, "a")
            href = event.attributes.get("href") or ""
            if not href.startswith("#"):
                raise NativeError(f"{path.name}: entity link {href!r} is not local")
            entities.append((category or "", _text(stream[position + 1:end]), href[1:]))
            position = end
        elif event.kind == "start" and event.tag == "h4":
            stop = _next_start(stream, position + 1, "h4")
            sections.append(_section(path, stream, position, stop))
            mode = "Sections"
            position = stop
            continue
        position += 1
    return Page(path.name, package, entities, description, sections, ids, links,
                tags, attributes)


def _close(stream: list[Event], start: int, tag: str) -> int:
    for index in range(start + 1, len(stream)):
        if stream[index].kind == "end" and stream[index].tag == tag:
            return index
    raise NativeError(f"unterminated <{tag}>")


def _next_start(stream: list[Event], start: int, tag: str) -> int:
    for index in range(start, len(stream)):
        if stream[index].kind == "start" and stream[index].tag == tag:
            return index
    return len(stream)


def _section(path: Path, stream: list[Event], start: int, stop: int) -> Section:
    anchor = stream[start].attributes.get("id")
    if not anchor:
        raise NativeError(f"{path.name}: h4 without id")
    heading_end = _close(stream, start, "h4")
    name = _text(stream[start + 1:heading_end])
    pre = _next_start(stream, heading_end, "pre")
    if pre != heading_end + 1 or stream[pre].attributes.get("class") != "ada-code-snippet":
        raise NativeError(f"{path.name}: {name}: missing ada-code-snippet")
    pre_end = _close(stream, pre, "pre")
    code = "".join(e.text for e in stream[pre + 1:pre_end] if e.kind == "data")
    first_h5 = _next_start(stream, pre_end, "h5")
    first_h5 = min(first_h5, stop)
    description = _text(stream[pre_end + 1:first_h5])
    groups: dict[str, list[tuple[str | None, str]]] = {}
    position = first_h5
    while position < stop:
        event = stream[position]
        if event.kind == "start" and event.tag == "h5":
            end = _close(stream, position, "h5")
            title = _text(stream[position + 1:end])
            if title in groups:
                raise NativeError(f"{path.name}: {name}: duplicate {title}")
            dl = end + 1
            if dl >= stop or stream[dl].kind != "start" or stream[dl].tag != "dl":
                raise NativeError(f"{path.name}: {name}: {title} without a list")
            dl_end = _close(stream, dl, "dl")
            groups[title] = _entries(path, name, stream[dl + 1:dl_end])
            position = dl_end
        elif event.kind == "data" and event.text.strip():
            raise NativeError(f"{path.name}: {name}: unexpected text after members")
        position += 1
    return Section(anchor, name, code, description, groups)


def _entries(path: Path, name: str, items: list[Event]) -> list[tuple[str | None, str]]:
    entries: list[tuple[str | None, str]] = []
    term: str | None = None
    position = 0
    while position < len(items):
        event = items[position]
        if event.kind == "start" and event.tag in ("dt", "dd"):
            stop = next((i for i in range(position + 1, len(items))
                         if items[i].kind == "start" and items[i].tag in ("dt", "dd")),
                        len(items))
            text = _text(items[position + 1:stop])
            if event.tag == "dt":
                if term is not None:
                    raise NativeError(f"{path.name}: {name}: dt without dd")
                term = text
            else:
                entries.append((term, text))
                term = None
            position = stop
            continue
        position += 1
    if term is not None:
        raise NativeError(f"{path.name}: {name}: dt without dd")
    return entries


def read_site(api: Path) -> tuple[Index, dict[str, Page]]:
    index = read_index(api / "index.html")
    pages = {}
    for package, href in index.units:
        if "/" in href or "#" in href or not href.endswith(".html"):
            raise NativeError(f"unsupported package page reference {href!r}")
        page = read_page(api / href)
        if page.package != package:
            raise NativeError(f"{href}: h1 {page.package!r} differs from index {package!r}")
        pages[package] = page
    return index, pages
