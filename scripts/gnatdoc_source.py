"""Source-backed model of the public Features specifications for GNATdoc.

This is deliberately not a general Ada front end. It lexes Ada 2022 tokens
(comments, string and character literals, compound delimiters) and parses only
the visible-part declaration forms used by the public Features API. Any other
visible construct fails closed so that coverage is never silently skipped.

The comment model reproduces the GNATdoc 26.0.0 ``--style leading`` behaviour
observed in docs/gnatdoc-foundation.md: a declaration owns the contiguous
comment-only lines directly above it; the package description is the block
directly after ``package X is`` when present, otherwise the nearest block
above the ``package`` keyword.
"""
from __future__ import annotations

import dataclasses
import hashlib
import re
from pathlib import Path

PUBLIC_DIRECTORY = "src"
INTERNAL_DIRECTORY = "src/internal"
TAGS = ("param", "return", "field", "enum", "exception")
SPDX = re.compile(r"SPDX-License-Identifier:\s*\S+")


class SourceError(ValueError):
    """An unsupported or malformed specification construct."""


@dataclasses.dataclass(frozen=True)
class Token:
    kind: str  # identifier, number, string, character, delimiter, comment
    text: str
    line: int
    column: int


_COMPOUND = ("=>", "..", "**", ":=", "/=", ">=", "<=", "<<", ">>", "<>")
_SINGLE = "&'()*+,-./:;<=>|@[]"
_NUMBER = re.compile(
    r"\d[\d_]*(?:#[0-9A-Fa-f_.]+#)?(?:\.[\d_]+)?(?:[Ee][+-]?\d[\d_]*)?")
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def lex(text: str) -> list[Token]:
    """Return all tokens, including comments, with one-based positions."""
    tokens: list[Token] = []
    for number, line in enumerate(text.splitlines(), start=1):
        position = 0
        while position < len(line):
            character = line[position]
            column = position + 1
            if character in " \t\f\v\r":
                position += 1
            elif line.startswith("--", position):
                tokens.append(Token("comment", line[position + 2:], number, column))
                break
            elif character == '"':
                end = position + 1
                while True:
                    end = line.find('"', end)
                    if end < 0:
                        raise SourceError(f"unterminated string at {number}:{column}")
                    if line.startswith('""', end):
                        end += 2
                        continue
                    break
                tokens.append(Token("string", line[position:end + 1], number, column))
                position = end + 1
            elif (character == "'" and position + 2 < len(line)
                  and line[position + 2] == "'"
                  and not (tokens and tokens[-1].line == number
                           and (tokens[-1].kind == "identifier"
                                or tokens[-1].text in (")", "]")))):
                tokens.append(Token("character", line[position:position + 3], number, column))
                position += 3
            elif match := _IDENTIFIER.match(line, position):
                tokens.append(Token("identifier", match[0], number, column))
                position = match.end()
            elif match := _NUMBER.match(line, position):
                tokens.append(Token("number", match[0], number, column))
                position = match.end()
            elif line[position:position + 2] in _COMPOUND:
                tokens.append(Token("delimiter", line[position:position + 2], number, column))
                position += 2
            elif character in _SINGLE:
                tokens.append(Token("delimiter", character, number, column))
                position += 1
            else:
                raise SourceError(f"unsupported character {character!r} at {number}:{column}")
    return tokens


def code(tokens: list[Token]) -> list[Token]:
    return [token for token in tokens if token.kind != "comment"]


def canonical(texts: list[str]) -> str:
    """Join token texts with one canonical spacing, independent of layout."""
    result = ""
    previous = ""
    for text in texts:
        if not result:
            result = text
        elif text in (",", ";", ")", ".", "'") or previous in ("(", ".", "'"):
            result += text
        else:
            result += " " + text
        previous = text
    return result


def code_signature(tokens: list[Token]) -> str:
    """Canonical comment-free declaration text without the final semicolon."""
    texts = [token.text for token in tokens]
    if texts and texts[-1] == ";":
        texts = texts[:-1]
    return canonical(texts)


@dataclasses.dataclass
class Member:
    kind: str  # parameter, return, field, literal
    name: str | None
    subtype: str | None = None
    mode: str | None = None
    default: str | None = None


@dataclasses.dataclass
class Declaration:
    package: str
    name: str
    kind: str  # type, subtype, function, procedure
    category: str  # enumeration, record, array, range, private, subprogram...
    signature: str
    line: int
    column: int
    end_line: int
    members: list[Member]
    comment_start: int | None = None
    comment_lines: list[str] = dataclasses.field(default_factory=list)

    @property
    def qualified(self) -> str:
        return f"{self.package}.{self.name}"

    @property
    def identity(self) -> str:
        return f"{self.qualified}|{self.kind}|{self.signature}"


@dataclasses.dataclass
class Specification:
    path: Path
    relative: str
    package: str
    visibility: str  # public or internal
    header_line: int
    private_line: int | None
    end_line: int
    declarations: list[Declaration]
    description_start: int | None
    description_lines: list[str]
    sha256: str
    lines: list[str]
    tokens: list[Token]


class _Cursor:
    def __init__(self, tokens: list[Token], path: str):
        self.tokens = tokens
        self.index = 0
        self.path = path

    def peek(self, offset: int = 0) -> Token | None:
        position = self.index + offset
        return self.tokens[position] if position < len(self.tokens) else None

    def word(self, offset: int = 0) -> str:
        token = self.peek(offset)
        return token.text.lower() if token else ""

    def take(self, expected: str | None = None) -> Token:
        token = self.peek()
        if token is None:
            raise SourceError(f"{self.path}: unexpected end of file")
        if expected is not None and token.text.lower() != expected:
            raise SourceError(
                f"{self.path}:{token.line}:{token.column}: expected {expected!r}, "
                f"found {token.text!r}")
        self.index += 1
        return token

    def name(self) -> Token:
        token = self.take()
        if token.kind != "identifier":
            raise SourceError(f"{self.path}:{token.line}:{token.column}: expected a name")
        return token

    def until(self, stops: tuple[str, ...]) -> list[Token]:
        """Tokens up to (not including) a stop word at parenthesis depth 0."""
        result: list[Token] = []
        depth = 0
        while True:
            token = self.peek()
            if token is None:
                raise SourceError(f"{self.path}: unterminated declaration")
            lowered = token.text.lower()
            if depth == 0 and lowered in stops:
                return result
            if lowered in ("(", "["):
                depth += 1
            elif lowered in (")", "]"):
                depth -= 1
                if depth < 0:
                    return result
            result.append(self.take())

    def fail(self, message: str) -> SourceError:
        token = self.peek()
        where = f"{token.line}:{token.column}" if token else "EOF"
        return SourceError(f"{self.path}:{where}: {message}")


_MODES = ("in", "out", "aliased", "access", "not", "null")


def _parameters(cursor: _Cursor) -> list[Member]:
    cursor.take("(")
    members: list[Member] = []
    while True:
        names = [cursor.name().text]
        while cursor.word() == ",":
            cursor.take(",")
            names.append(cursor.name().text)
        cursor.take(":")
        mode: list[str] = []
        while cursor.word() in _MODES:
            mode.append(cursor.take().text.lower())
        subtype = canonical([t.text for t in cursor.until((":=", ";", ")"))])
        default = None
        if cursor.word() == ":=":
            cursor.take(":=")
            default = canonical([t.text for t in cursor.until((";", ")"))])
        for name in names:
            members.append(Member("parameter", name, subtype, " ".join(mode) or "in", default))
        if cursor.word() == ";":
            cursor.take(";")
            continue
        cursor.take(")")
        return members


def _components(cursor: _Cursor) -> list[Member]:
    members: list[Member] = []
    while cursor.word() != "end":
        if cursor.word() == "null":
            cursor.take("null")
            cursor.take(";")
            continue
        if cursor.word() == "case":
            raise cursor.fail("variant records are not supported by the inventory")
        names = [cursor.name().text]
        while cursor.word() == ",":
            cursor.take(",")
            names.append(cursor.name().text)
        cursor.take(":")
        if cursor.word() == "aliased":
            cursor.take("aliased")
        subtype = canonical([t.text for t in cursor.until((":=", ";"))])
        default = None
        if cursor.word() == ":=":
            cursor.take(":=")
            default = canonical([t.text for t in cursor.until((";",))])
        cursor.take(";")
        members.extend(Member("field", name, subtype, None, default) for name in names)
    cursor.take("end")
    cursor.take("record")
    return members


def _declaration(cursor: _Cursor, package: str) -> Declaration:
    start = cursor.index
    first = cursor.peek()
    word = cursor.word()
    members: list[Member] = []
    if word in ("overriding", "not"):
        raise cursor.fail("overriding indicators are not supported in the visible part")
    if word in ("function", "procedure"):
        kind = word
        cursor.take()
        name = cursor.name()
        if cursor.word() == "(":
            members = _parameters(cursor)
        if kind == "function":
            cursor.take("return")
            result = canonical([t.text for t in cursor.until((";", "is", "with", "renames"))])
            members.append(Member("return", None, result))
        if cursor.word() != ";":
            raise cursor.fail("aspects, renamings and expression functions are unsupported")
        cursor.take(";")
        category = "subprogram"
    elif word in ("type", "subtype"):
        kind = word
        cursor.take()
        name = cursor.name()
        if cursor.word() == "(":
            raise cursor.fail("discriminated types are not supported by the inventory")
        cursor.take("is")
        if kind == "subtype":
            category = "subtype"
            cursor.until((";",))
            cursor.take(";")
        elif cursor.word() == "(":
            category = "enumeration"
            cursor.take("(")
            while True:
                literal = cursor.take()
                if literal.kind != "identifier":
                    raise cursor.fail("character enumeration literals are unsupported")
                members.append(Member("literal", literal.text))
                if cursor.word() == ",":
                    cursor.take(",")
                    continue
                cursor.take(")")
                break
            cursor.take(";")
        else:
            prefix: list[str] = []
            while cursor.word() in ("abstract", "tagged", "limited"):
                prefix.append(cursor.take().text.lower())
            if cursor.word() == "record":
                cursor.take("record")
                members = _components(cursor)
                category = "record"
            elif cursor.word() == "null" and cursor.word(1) == "record":
                cursor.take("null")
                cursor.take("record")
                category = "record"
            elif cursor.word() == "private":
                cursor.take("private")
                category = "private"
            elif not prefix and cursor.word() == "range":
                category = "range"
                cursor.until((";",))
            elif not prefix and cursor.word() == "mod":
                category = "modular"
                cursor.until((";",))
            elif not prefix and cursor.word() == "array":
                category = "array"
                cursor.until((";",))
            else:
                raise cursor.fail(f"unsupported type definition starting {cursor.word()!r}")
            if cursor.word() == "with":
                raise cursor.fail("aspects are not supported by the inventory")
            cursor.take(";")
    else:
        raise cursor.fail(f"unsupported visible declaration starting {word!r}")
    tokens = cursor.tokens[start:cursor.index]
    return Declaration(package, name.text, kind, category, code_signature(tokens),
                       first.line, name.column, tokens[-1].line, members)


def _comment_text(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("--"):
        return None
    text = stripped[2:]
    return text[2:] if text.startswith("  ") else text.lstrip()


def _block_above(lines: list[str], line: int) -> tuple[int | None, list[str]]:
    """The contiguous comment-only lines directly above one-based ``line``."""
    collected: list[str] = []
    current = line - 1
    while current >= 1 and _comment_text(lines[current - 1]) is not None:
        collected.insert(0, _comment_text(lines[current - 1]))
        current -= 1
    return (current + 1 if collected else None), collected


def _block_below(lines: list[str], line: int) -> tuple[int | None, list[str]]:
    collected: list[str] = []
    current = line + 1
    while current <= len(lines) and _comment_text(lines[current - 1]) is not None:
        collected.append(_comment_text(lines[current - 1]))
        current += 1
    return (line + 1 if collected else None), collected


def parse(path: Path, root: Path) -> Specification:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tokens = lex(text)
    relative = path.relative_to(root).as_posix()
    cursor = _Cursor(code(tokens), relative)
    while cursor.word() in ("with", "private", "limited", "use"):
        if cursor.word() == "private" and cursor.word(1) == "package":
            raise cursor.fail("private library units are not supported under src/")
        cursor.until((";",))
        cursor.take(";")
    header = cursor.take("package")
    names = [cursor.name().text]
    while cursor.word() == ".":
        cursor.take(".")
        names.append(cursor.name().text)
    package = ".".join(names)
    if cursor.word() != "is":
        raise cursor.fail("generic instances and renamings are not supported")
    is_token = cursor.take("is")
    visibility = "internal" if relative.startswith(INTERNAL_DIRECTORY + "/") else "public"
    declarations: list[Declaration] = []
    private_line = None
    if visibility == "public":
        while cursor.word() not in ("private", "end"):
            declarations.append(_declaration(cursor, package))
        if cursor.word() == "private":
            private_line = cursor.peek().line
    end_line = max(token.line for token in cursor.tokens)
    for declaration in declarations:
        declaration.comment_start, declaration.comment_lines = _block_above(
            lines, declaration.line)
    start, block = _block_below(lines, is_token.line)
    if start is None:
        current = header.line - 1
        while current >= 1 and not lines[current - 1].strip():
            current -= 1
        start, block = _block_above(lines, current + 1)
    return Specification(path, relative, package, visibility, header.line, private_line,
                         end_line, declarations, start, block,
                         hashlib.sha256(path.read_bytes()).hexdigest(), lines, tokens)


def specifications(root: Path) -> dict[str, Specification]:
    """All library-unit specifications under src/ and src/internal/."""
    result: dict[str, Specification] = {}
    paths = sorted((root / PUBLIC_DIRECTORY).glob("*.ads")) + sorted(
        (root / INTERNAL_DIRECTORY).glob("*.ads"))
    for path in paths:
        specification = parse(path, root)
        if specification.package in result:
            raise SourceError(f"duplicate library unit {specification.package}")
        result[specification.package] = specification
    if not any(s.visibility == "public" for s in result.values()):
        raise SourceError("no public specifications")
    return result


@dataclasses.dataclass
class Documentation:
    description: str
    tags: dict[tuple[str, str | None], str]
    duplicates: list[tuple[str, str | None]]


def split_tags(lines: list[str]) -> Documentation:
    """Separate free description text from GNATdoc @tags in a comment block."""
    description: list[str] = []
    tags: dict[tuple[str, str | None], list[str]] = {}
    duplicates: list[tuple[str, str | None]] = []
    current: list[str] = description
    for line in lines:
        match = re.match(r"\s*@(\w+)\b\s*(.*)$", line)
        if match and match[1] in TAGS:
            rest = match[2]
            name = None
            if match[1] != "return":
                parts = rest.split(None, 1)
                name = parts[0] if parts else ""
                rest = parts[1] if len(parts) > 1 else ""
            key = (match[1], name.lower() if name else None)
            if key in tags:
                duplicates.append(key)
            tags[key] = [rest]
            current = tags[key]
        else:
            current.append(line)
    return Documentation(normalize(" ".join(description)),
                         {key: normalize(" ".join(value)) for key, value in tags.items()},
                         duplicates)


def normalize(text: str) -> str:
    return " ".join(text.split())


def meaningful(text: str, minimum_words: int) -> bool:
    """A mechanical floor, not a semantic-quality judgement."""
    words = re.findall(r"[A-Za-z0-9][\w'./-]*", SPDX.sub("", text))
    return len(words) >= minimum_words


def ownership_types(specs: dict[str, Specification]) -> dict[str, str]:
    """Public limited/controlled types and Core Mat, keyed by simple name."""
    result = {"OpenCV.Core.Mat": "Core-owned native matrix wrapper"}
    for spec in specs.values():
        for declaration in spec.declarations:
            if declaration.category == "private" and " limited " in f" {declaration.signature} ":
                result[declaration.name] = f"limited private type {declaration.qualified}"
    return result


def ownership_sensitive(declaration: Declaration, owned: dict[str, str]) -> list[str]:
    if declaration.category != "subprogram":
        return []
    reasons = []
    for member in declaration.members:
        subtype = member.subtype or ""
        for name, description in owned.items():
            if subtype == name or subtype.endswith("." + name):
                role = "result" if member.kind == "return" else f"{member.mode} {member.name}"
                reasons.append(f"{role}: {description}")
    return reasons
