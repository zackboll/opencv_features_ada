"""Shared support for the pinned ada-gnatdoc-enhancer: installation and checks.

The enhancer is a documentation-only tool, installed from the SHA-256-approved
official release wheel into a private virtual environment. Installed modules,
metadata and assets must equal the independently approved wheel members. The native
comparison here is independent of the enhancer's own ``verify`` operation.
"""
from __future__ import annotations

import hashlib
import email.parser
import html.parser
import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINNED_REVISION = "4ee95e8c95b8c7f54397a07e3e1c507783c115aa"
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


def approval() -> dict:
    """Features-owned trust root, never supplied by a download or receipt."""
    return json.loads((ROOT / "docs/gnatdoc-enhancer-release.json").read_text())


def validate_download_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in
            {"github.com", "release-assets.githubusercontent.com"} or
            parsed.port not in (None, 443) or parsed.username or parsed.password):
        raise SupportError("unapproved download URL")


class _ReleaseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_download_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_release(name: str, destination: Path, digest: str, size: int) -> None:
    approved = approval()
    url = f"{approved['repository']}/releases/download/{approved['tag']}/{name}"
    validate_download_url(url)
    opener = urllib.request.build_opener(_ReleaseRedirect)
    with opener.open(url, timeout=60) as response:
        validate_download_url(response.url)
        data = response.read(size + 1)
        if response.status != 200 or len(data) != size:
            raise SupportError(f"incomplete or oversized release download: {name}")
        if response.headers.get("Content-Length") not in (None, str(size)):
            raise SupportError(f"incorrect release Content-Length: {name}")
    if hashlib.sha256(data).hexdigest() != digest:
        raise SupportError(f"release SHA-256 mismatch: {name}")
    destination.write_bytes(data)


def verify_wheel(path: Path) -> dict:
    expected = approval()["wheel"]
    if sha256(path) != expected["sha256"]:
        raise SupportError("wheel SHA-256 differs from Features-owned approval")
    if path.stat().st_size != expected["bytes"]:
        raise SupportError("wheel size differs")
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected["members"]):
            raise SupportError("unexpected wheel members")
        for member in wheel.infolist():
            if member.is_dir() or (member.external_attr >> 16) & 0o170000 not in (0, 0o100000):
                raise SupportError("non-regular wheel member")
            if hashlib.sha256(wheel.read(member)).hexdigest() != expected["members"][member.filename]:
                raise SupportError("wheel member identity differs")
        metadata = email.parser.BytesParser().parsebytes(
            wheel.read("ada_gnatdoc_enhancer-0.1.0.dist-info/METADATA"))
        if metadata["Name"] != "ada-gnatdoc-enhancer" or metadata["Version"] != "0.1.0":
            raise SupportError("incorrect wheel metadata")
        if metadata.get_all("Requires-Dist", []) != [
                'markdown-it-py==3.0.0; extra == "guides"', 'mdurl==0.1.2; extra == "guides"']:
            raise SupportError("unexpected core dependencies")
    return expected


def verify_release_provenance(record: dict) -> None:
    approved = approval()
    tag = {"name": approved["tag"], "object_sha": approved["tag_object"],
           "peeled_commit": approved["revision"], "peeled_tree": approved["tree"]}
    if (any(record.get(k) != approved[v] for k, v in (
            ("repository", "repository"), ("source_commit", "revision"),
            ("git_tree", "tree"), ("release_version", "version"))) or
            any(record.get("annotated_tag", {}).get(k) != v for k, v in tag.items()) or
            record.get("archive_identities", {}).get("wheel") != {
                k: approved["wheel"][k] for k in ("name", "bytes", "sha256", "members")} or
            record.get("assets", {}).get(approved["wheel"]["name"]) != {
                k: approved["wheel"][k] for k in ("bytes", "sha256")}):
        raise SupportError("release provenance does not match approved tag/source/archive identity")


def verify_tag(directory: Path) -> None:
    """Fetch into a new Git database; do not trust mutable local tags/checkouts."""
    approved = approval()
    run("git", "init", "--quiet", str(directory))
    run("git", "-c", "http.followRedirects=false", "-C", str(directory), "fetch", "--quiet", "--no-tags",
        approved["repository"] + ".git", "refs/tags/" + approved["tag"])
    actual = run("git", "-C", str(directory), "rev-parse", "FETCH_HEAD",
                 "FETCH_HEAD^{commit}", "FETCH_HEAD^{tree}").stdout.split()
    kind = run("git", "-C", str(directory), "cat-file", "-t", "FETCH_HEAD").stdout.strip()
    if actual != [approved["tag_object"], approved["revision"], approved["tree"]] or kind != "tag":
        raise SupportError("incorrect annotated tag/source identity")


def install(environment: Path, requirements: Path | None = None) -> Path:
    """Acquire and verify official artifacts before creating the isolated venv."""
    approved = approval()
    if environment.exists():
        raise SupportError(f"{environment} must not exist")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        wheel = temporary / approved["wheel"]["name"]
        download_release(wheel.name, wheel, approved["wheel"]["sha256"], approved["wheel"]["bytes"])
        verify_wheel(wheel)
        manifest = temporary / "release-provenance.json"
        download_release(manifest.name, manifest, approved["provenance_sha256"], 707651)
        verify_release_provenance(json.loads(manifest.read_text()))
        verify_tag(temporary / "git")
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / "bin/python"
        run(str(python), "-I", "-m", "pip", "install", "--quiet", "--no-deps", "--no-index", str(wheel))
        (environment / manifest.name).write_bytes(manifest.read_bytes())
    if requirements is not None:
        run(str(python), "-I", "-m", "pip", "install", "--quiet", "--no-deps", "--require-hashes",
            "--only-binary=:all:", "-r", str(requirements))
    # A fixed Features-owned launcher is independently rechecked too. Pip's
    # generated wrapper varies across pip versions; it is not a trust root.
    (environment / "bin/gnatdoc-enhancer").write_bytes(launcher(environment))
    record = installation_identity(environment)
    (environment / PROVENANCE).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return verified_tool(environment)[0]


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
    # Locate without importing unverified package code.
    site = Path(run(str(environment / "bin/python"), "-I", "-c",
                    "import sysconfig;print(sysconfig.get_path('purelib'))").stdout.strip())
    if not site.resolve().is_relative_to(environment.resolve()):
        raise SupportError("package directory escapes isolated environment")
    return site / "ada_gnatdoc_enhancer"


def package_hashes(package: Path) -> dict[str, str]:
    return {name: digest for name, digest in tree_hashes(package).items()
            if "__pycache__" not in name}


def verified_tool(environment: Path, revision: str = PINNED_REVISION) -> tuple[Path, dict]:
    """Recheck against source-owned identities, not just a mutable receipt."""
    if revision != PINNED_REVISION:
        raise SupportError(f"requested revision {revision} is not {PINNED_REVISION}")
    record = json.loads((environment / PROVENANCE).read_text())
    if record != installation_identity(environment):
        raise SupportError("incorrect installation provenance")
    return environment / "bin/gnatdoc-enhancer", record


def launcher(environment: Path) -> bytes:
    return (f"#!{environment}/bin/python -IB\n"
            "from ada_gnatdoc_enhancer.cli import main\n"
            "raise SystemExit(main())\n").encode()


def approved_installed_files(site: Path, expected: dict[str, str]) -> None:
    """Exact regular member bytes, plus only pip's installation bookkeeping.

    Bytecode caches are discarded before any package import, so unapproved pyc
    files cannot bypass the Python-source comparison.
    """
    top_names = {name.split('/')[0] for name in expected}
    actual = {}
    for top in sorted(top_names):
        directory = site / top
        if directory.is_symlink():
            raise SupportError("installed package is a symbolic link")
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise SupportError("installed member is a symbolic link")
            if path.is_file() and "__pycache__" not in path.parts:
                relative = path.relative_to(site).as_posix()
                if directory.name.endswith(".dist-info") and path.name in {
                        "RECORD", "INSTALLER", "REQUESTED", "direct_url.json"}:
                    continue
                actual[relative] = sha256(path)
        for cache in directory.rglob("__pycache__"):
            shutil.rmtree(cache)
    checked = {name: digest for name, digest in expected.items() if not name.endswith("/RECORD")}
    if actual != checked:
        raise SupportError("installed files changed from independently approved wheel members")


def installation_identity(environment: Path) -> dict:
    approved = approval()
    package = installed_package(environment)
    members = approved["wheel"]["members"]
    approved_installed_files(package.parent, members)
    files = {name.removeprefix("ada_gnatdoc_enhancer/"): digest
             for name, digest in members.items() if name.startswith("ada_gnatdoc_enhancer/")}
    if package_hashes(package) != files:
        raise SupportError("installed enhancer files changed")
    renderer = installed_renderer(environment)
    renderer_files = {}
    if renderer and renderer != {k: v["version"] for k, v in approved["renderers"].items()}:
        raise SupportError("incorrect installed guide renderer")
    for name in renderer:
        expected = approved["renderers"][name]["members"]
        approved_installed_files(package.parent, expected)
        renderer_files.update(expected)
    for name, directory in (("markdown-it-py", "markdown_it"), ("mdurl", "mdurl")):
        if name not in renderer and (package.parent / directory).exists():
            raise SupportError("unrecorded guide renderer package")
    metadata = package.parent / "ada_gnatdoc_enhancer-0.1.0.dist-info"
    direct = metadata / "direct_url.json"
    if direct.exists():
        origin = json.loads(direct.read_text())
        if (origin.get("dir_info") or origin.get("vcs_info") or
                origin.get("archive_info", {}).get("hashes", {}).get("sha256") != approved["wheel"]["sha256"]):
            raise SupportError("incorrect non-editable wheel installation origin")
    manifest = environment / "release-provenance.json"
    if sha256(manifest) != approved["provenance_sha256"]:
        raise SupportError("installed release provenance SHA-256 differs")
    verify_release_provenance(json.loads(manifest.read_text()))
    tool = environment / "bin/gnatdoc-enhancer"
    if tool.is_symlink() or tool.read_bytes() != launcher(environment):
        raise SupportError("installed launcher changed")
    versions = json.loads(run(str(environment / "bin/python"), "-I", "-B", "-c",
                             "import ada_gnatdoc_enhancer as a, importlib.metadata as m,json;"
                             "print(json.dumps([a.__version__,m.version('ada-gnatdoc-enhancer')]))").stdout)
    if versions != [approved["version"], approved["version"]] or \
            run(str(tool), "--version").stdout.strip() != approved["version"]:
        raise SupportError("incorrect installed enhancer version")
    return {k: approved[k] for k in ("schema_version", "repository", "tag", "tag_object",
                                     "revision", "tree", "version")} | {
        "wheel_sha256": approved["wheel"]["sha256"],
        "release_provenance_sha256": approved["provenance_sha256"],
        "files": files, "distribution_files": members, "guide_renderer": renderer,
        "renderer_files": renderer_files, "launcher_sha256": hashlib.sha256(launcher(environment)).hexdigest()}


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
