"""Shared support for the pinned ada-gnatdoc-enhancer: installation and checks.

The enhancer is a documentation-only tool. It is installed from an exact,
reviewed Git revision into a private virtual environment, and every
installed module and asset must equal that revision's Git blobs. The native
comparison here is independent of the enhancer's own ``verify`` operation.
"""
from __future__ import annotations

import hashlib
import html.parser
import json
import re
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINNED_REVISION = "23cf51d3765e7b3f68411e25a57f52f4c0efc7e1"
PROVENANCE = "gnatdoc-enhancer-provenance.json"


class SupportError(RuntimeError):
    pass


def run(*command: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SupportError(f"{' '.join(command)} failed:\n{result.stdout}{result.stderr}")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(directory: Path) -> dict[str, str]:
    return {p.relative_to(directory).as_posix(): sha256(p)
            for p in sorted(directory.rglob("*")) if p.is_file()}


def public_specifications(root: Path = ROOT) -> list[str]:
    """The explicit public specification list of docs_api.gpr."""
    text = (root / "docs_api.gpr").read_text()
    block = re.search(r"for Source_Files use\s*\((.*?)\);", text, re.S)
    if block is None:
        raise SupportError("docs_api.gpr has no explicit Source_Files list")
    return re.findall(r'"([^"]+\.ads)"', block[1])


def stage_public_sources(destination: Path, root: Path = ROOT) -> list[str]:
    """Byte-identical copies of the documented specifications only.

    The enhancer discovers sources recursively, and src/internal holds
    non-private internal units that are never published.
    """
    if destination.exists():
        raise SupportError(f"{destination} must not exist")
    destination.mkdir(parents=True)
    specs = public_specifications(root)
    for spec in specs:
        (destination / spec).write_bytes((root / "src" / spec).read_bytes())
        if sha256(destination / spec) != sha256(root / "src" / spec):
            raise SupportError(f"staged {spec} differs")
    return specs


def install(checkout: Path, revision: str, environment: Path,
            requirements: Path | None = None) -> Path:
    """Install the exact revision into a new virtual environment.

    Returns the gnatdoc-enhancer executable. Writes a provenance record with
    the installed file hashes, each proven equal to the revision's Git blob.
    ``requirements`` optionally installs hash-pinned guide renderer wheels.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SupportError("the enhancer revision must be a full commit SHA")
    resolved = run("git", "-C", str(checkout), "rev-parse",
                   f"{revision}^{{commit}}").stdout.strip()
    if resolved != revision:
        raise SupportError(f"{revision} resolves to {resolved}")
    if environment.exists():
        raise SupportError(f"{environment} must not exist")
    source = environment.with_name(environment.name + "-source")
    if source.exists():
        raise SupportError(f"{source} must not exist")
    source.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(checkout), "archive", revision],
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(source)], input=archive, check=True)
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / "bin/python"
    run(str(python), "-m", "pip", "install", "--quiet", "--no-deps", str(source))
    package = installed_package(environment)
    listed = run("git", "-C", str(checkout), "ls-tree", "-r", "--name-only", revision,
                 "src/ada_gnatdoc_enhancer").stdout.split()
    expected = {}
    for path in listed:
        blob = subprocess.run(["git", "-C", str(checkout), "show", f"{revision}:{path}"],
                              check=True, capture_output=True).stdout
        expected[path.removeprefix("src/ada_gnatdoc_enhancer/")] = \
            hashlib.sha256(blob).hexdigest()
    installed = package_hashes(package)
    if installed != expected:
        raise SupportError("installed enhancer differs from the reviewed revision")
    renderer = {}
    if requirements is not None:
        run(str(python), "-m", "pip", "install", "--quiet", "--no-deps", "--require-hashes",
            "--only-binary=:all:", "-r", str(requirements))
        renderer = installed_renderer(environment)
    tool = environment / "bin/gnatdoc-enhancer"
    version = run(str(tool), "--version").stdout.strip()
    (environment / PROVENANCE).write_text(json.dumps(
        {"revision": revision, "version": version, "files": installed,
         "guide_renderer": renderer}, indent=2, sort_keys=True) + "\n")
    return tool


def installed_renderer(environment: Path) -> dict[str, str]:
    """Installed Markdown renderer distributions, if any."""
    output = run(str(environment / "bin/python"), "-I", "-c",
                 "import importlib.metadata as m,json\n"
                 "r={}\n"
                 "for n in ('markdown-it-py','mdurl'):\n"
                 "  try: r[n]=m.version(n)\n"
                 "  except m.PackageNotFoundError: pass\n"
                 "print(json.dumps(r))").stdout
    return json.loads(output)


def installed_package(environment: Path) -> Path:
    return Path(run(str(environment / "bin/python"), "-I", "-c",
                    "import ada_gnatdoc_enhancer,os;"
                    "print(os.path.dirname(ada_gnatdoc_enhancer.__file__))").stdout.strip())


def package_hashes(package: Path) -> dict[str, str]:
    return {name: digest for name, digest in tree_hashes(package).items()
            if "__pycache__" not in name}


def verified_tool(environment: Path, revision: str = PINNED_REVISION) -> tuple[Path, dict]:
    """Re-check an installed environment against its recorded provenance."""
    record = json.loads((environment / PROVENANCE).read_text())
    if record["revision"] != revision:
        raise SupportError(f"installed enhancer {record['revision']} is not {revision}")
    if package_hashes(installed_package(environment)) != record["files"]:
        raise SupportError("installed enhancer files changed after installation")
    if installed_renderer(environment) != record.get("guide_renderer", {}):
        raise SupportError("installed guide renderer changed after installation")
    return environment / "bin/gnatdoc-enhancer", record


def enhancer(tool: Path, command: str, root: Path, config: str, site: Path, *extra: str,
             check: bool = True):
    result = run(str(tool), command, "--source-root", str(root), "--config", config,
                 "--site", str(site), *extra, check=check)
    return json.loads(result.stdout) if result.returncode == 0 else result


class _Collect(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.references, self.scripts, self.headings, self.code = [], [], [], [], []
        self._heading = None
        self._code = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        self.references += [attrs[k] for k in ("href", "src") if attrs.get(k) is not None]
        if tag == "script":
            self.scripts.append(attrs.get("src"))
        if tag in ("h1", "h4"):
            self._heading = (tag, attrs.get("id"), [])
        if tag == "code" and self._code is None:
            self._code = []

    def handle_endtag(self, tag):
        if self._heading and tag == self._heading[0]:
            self.headings.append((self._heading[0], self._heading[1], "".join(self._heading[2])))
            self._heading = None
        if tag == "code" and self._code is not None:
            self.code.append("".join(self._code))
            self._code = None

    def handle_data(self, data):
        if self._heading:
            self._heading[2].append(data)
        if self._code is not None:
            self._code.append(data)


def collect(path: Path) -> _Collect:
    collector = _Collect()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def compare_native(pristine: Path, enhanced: Path) -> dict:
    """Independent native-preservation, link and URL comparison of api/ dirs."""
    errors = []
    before = {p.name for p in pristine.iterdir()}
    after = {p.name for p in enhanced.iterdir()}
    if before - after:
        errors.append(f"removed native files {sorted(before - after)}")
    if sha256(pristine / "gnatdoc.css") != sha256(enhanced / "gnatdoc.css"):
        errors.append("native gnatdoc.css changed")
    external, unresolved, scripts = [], [], {}
    for name in sorted(after):
        if not name.endswith(".html"):
            continue
        page = collect(enhanced / name)
        scripts[name] = page.scripts
        for reference in page.references:
            if re.match(r"^[a-z][a-z0-9+.-]*:|^//", reference, re.I):
                external.append(f"{name}: {reference}")
                continue
            target, _, fragment = reference.partition("#")
            target = target.split("?", 1)[0] or name
            if "/" in target or not (enhanced / target).is_file():
                unresolved.append(f"{name}: {reference}")
            elif fragment and target.endswith(".html") and \
                    fragment not in collect(enhanced / target).ids:
                unresolved.append(f"{name}: {reference}")
        if name in before:
            native = collect(pristine / name)
            for label, ok in (("headings", native.headings == page.headings),
                              ("ids", set(native.ids) <= set(page.ids)),
                              ("hrefs", set(native.references) <= set(page.references)),
                              ("code text", native.code == page.code)):
                if not ok:
                    errors.append(f"{name}: native {label} not preserved")
    if external:
        errors.append(f"external URLs {external}")
    if unresolved:
        errors.append(f"unresolved local links {unresolved}")
    return {"errors": errors, "added_files": sorted(after - before),
            "scripts": {k: v for k, v in scripts.items() if v}}


def check_site_links(site: Path) -> dict:
    """Resolve every local reference of every HTML page under a site root.

    Relative paths may climb only to the site root; external URLs, missing
    files and missing fragments are reported. Scripts are listed per page.
    """
    errors, scripts = [], {}
    root = site.resolve()
    pages = sorted(p for p in site.rglob("*.html"))
    for path in pages:
        page = collect(path)
        relative = path.relative_to(site).as_posix()
        if page.scripts:
            scripts[relative] = page.scripts
        for reference in page.references:
            if re.match(r"^[a-z][a-z0-9+.-]*:|^//", reference, re.I):
                errors.append(f"{relative}: external URL {reference}")
                continue
            target, _, fragment = reference.partition("#")
            target = target.split("?", 1)[0]
            destination = (path.parent / target).resolve() if target else path.resolve()
            if not destination.is_relative_to(root) or not destination.is_file():
                errors.append(f"{relative}: unresolved {reference}")
            elif fragment and destination.suffix == ".html" and \
                    fragment not in collect(destination).ids:
                errors.append(f"{relative}: unresolved fragment {reference}")
    return {"errors": errors, "pages": len(pages), "scripts": scripts}
