"""Source-owned release identity and installed-byte security controls."""
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import gnatdoc_enhancer_support as support


class ReleaseTests(unittest.TestCase):
    def test_wrong_wheel_hash_is_rejected_before_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "wrong.whl"
            wheel.write_bytes(b"not the official wheel")
            with mock.patch.object(support.venv.EnvBuilder, "create") as create:
                with self.assertRaisesRegex(support.SupportError, "wheel SHA-256"):
                    support.verify_wheel(wheel)
                create.assert_not_called()

    @staticmethod
    def provenance():
        """A minimal record in the v0.1.5 release-provenance schema."""
        approved = support.approval()
        wheel = approved["wheel"]
        return {
            "schema_version": 1, "release_version": approved["version"],
            "expected_source_commit": approved["revision"], "expected_source_tree": approved["tree"],
            "archives": {
                "wheel": {"name": wheel["name"], "bytes": wheel["bytes"], "sha256": wheel["sha256"],
                          "members": {k: {"bytes": 1, "sha256": v} for k, v in wheel["members"].items()}},
                "sdist": {"sha256": approved["sdist_sha256"]}},
            "distribution_content_audit": {
                "version": approved["version"], "runtime_dependencies": [],
                "wheel_record_hashes_and_sizes_verified": True,
                "module_asset_sha256": {k: v for k, v in wheel["members"].items()
                                        if k.startswith("ada_gnatdoc_enhancer/")}},
        }

    def test_wrong_tag_source_tree_and_version_are_rejected(self):
        provenance = self.provenance()
        support.verify_release_provenance(provenance)
        for key, value in (("expected_source_commit", "0" * 40), ("expected_source_tree", "0" * 40),
                           ("release_version", "0.1.0"), ("schema_version", 2)):
            with self.subTest(key=key), self.assertRaises(support.SupportError):
                support.verify_release_provenance(dict(provenance, **{key: value}))
        def altered(change):
            record = json.loads(json.dumps(provenance))
            change(record)
            return record
        member = "ada_gnatdoc_enhancer/cli.py"
        for label, change in (
                ("wheel digest", lambda r: r["archives"]["wheel"].update(sha256="0" * 64)),
                ("wheel name", lambda r: r["archives"]["wheel"].update(
                    name="ada_gnatdoc_enhancer-0.1.0-py3-none-any.whl")),
                ("member digest", lambda r: r["archives"]["wheel"]["members"][member].update(
                    sha256="0" * 64)),
                ("extra member", lambda r: r["archives"]["wheel"]["members"].update(
                    {"ada_gnatdoc_enhancer/extra.py": {"bytes": 1, "sha256": "0" * 64}})),
                ("sdist digest", lambda r: r["archives"]["sdist"].update(sha256="0" * 64)),
                ("audit version", lambda r: r["distribution_content_audit"].update(version="0.1.0")),
                ("runtime dependency", lambda r: r["distribution_content_audit"].update(
                    runtime_dependencies=["requests"])),
                ("unverified RECORD", lambda r: r["distribution_content_audit"].update(
                    wheel_record_hashes_and_sizes_verified=False)),
                ("module digest", lambda r: r["distribution_content_audit"][
                    "module_asset_sha256"].update({member: "0" * 64}))):
            with self.subTest(label=label), self.assertRaises(support.SupportError):
                support.verify_release_provenance(altered(change))

    def test_sha256sums_must_list_exactly_the_approved_archives(self):
        approved = support.approval()
        lines = [f"{approved['wheel']['sha256']}  {approved['wheel']['name']}",
                 f"{approved['sdist_sha256']}  ada_gnatdoc_enhancer-{approved['version']}.tar.gz",
                 f"{approved['provenance_sha256']}  release-provenance.json"]
        support.verify_sha256sums("\n".join(lines) + "\n")
        for label, text in (("tampered digest", "\n".join(["0" * 64 + lines[0][64:]] + lines[1:])),
                            ("missing archive", "\n".join(lines[:2])),
                            ("extra archive", "\n".join(lines + ["0" * 64 + "  extra.whl"])),
                            ("duplicate", "\n".join(lines + lines[:1])),
                            ("malformed", "\n".join(lines).replace("  ", " ", 1))):
            with self.subTest(label=label), self.assertRaises(support.SupportError):
                support.verify_sha256sums(text)

    def test_wheel_record_tampering_is_rejected(self):
        name = support.dist_info() + "/RECORD"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.whl"
            data = b"print()\n"
            digest = support.base64.urlsafe_b64encode(
                hashlib.sha256(data).digest()).rstrip(b"=").decode()
            good = f"ada_gnatdoc_enhancer/x.py,sha256={digest},{len(data)}\n{name},,\n"
            for label, record, ok in (
                    ("valid", good, True),
                    ("wrong digest", good.replace(digest, "A" * len(digest)), False),
                    ("wrong size", good.replace(f",{len(data)}", ",99"), False),
                    ("unlisted member", f"{name},,\n", False),
                    ("listed absent member", good + "ada_gnatdoc_enhancer/y.py,sha256=x,1\n", False),
                    ("hashed RECORD", good.replace(f"{name},,", f"{name},sha256=x,1"), False)):
                with self.subTest(label=label):
                    with zipfile.ZipFile(path, "w") as wheel:
                        wheel.writestr("ada_gnatdoc_enhancer/x.py", data)
                        wheel.writestr(name, record)
                    with zipfile.ZipFile(path) as wheel:
                        if ok:
                            support.verify_record(wheel)
                        else:
                            with self.assertRaises(support.SupportError):
                                support.verify_record(wheel)

    def test_unapproved_redirects_are_rejected(self):
        for url in ("http://github.com/a", "https://evil.example/a",
                    "https://github.com.evil.example/a", "https://github.com:8443/a",
                    "https://user@github.com/a"):
            with self.subTest(url=url), self.assertRaises(support.SupportError):
                support.validate_download_url(url)

    def test_incomplete_and_altered_downloads_are_rejected(self):
        for data, status, length in ((b"short", 200, "6"), (b"excess!", 200, "7"),
                                     (b"wrong!", 200, "6"), (b"right!", 206, "6")):
            with self.subTest(data=data, status=status), tempfile.TemporaryDirectory() as directory:
                response = mock.MagicMock()
                response.__enter__.return_value = response
                response.url = "https://release-assets.githubusercontent.com/asset"
                response.read.return_value = data
                response.status = status
                response.headers = {"Content-Length": length}
                opener = mock.Mock()
                opener.open.return_value = response
                with mock.patch.object(support.urllib.request, "build_opener", return_value=opener):
                    with self.assertRaises(support.SupportError):
                        support.download_release("test", Path(directory) / "out",
                                                 hashlib.sha256(b"right!").hexdigest(), 6)
                    self.assertFalse((Path(directory) / "out").exists())

    def test_unexpected_and_duplicate_wheel_members_are_rejected_even_after_hash_check(self):
        # Bypass only the outer digest to reach the independent member gate.
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "test.whl"
                with zipfile.ZipFile(path, "w") as wheel:
                    wheel.writestr("unexpected.py", "unsafe")
                    if duplicate:
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", UserWarning)
                            wheel.writestr("unexpected.py", "unsafe")
                approved = support.approval()
                approved["wheel"]["sha256"] = support.sha256(path)
                approved["wheel"]["bytes"] = path.stat().st_size
                with mock.patch.object(support, "approval", return_value=approved):
                    with self.assertRaisesRegex(support.SupportError, "unexpected wheel members"):
                        support.verify_wheel(path)

    def test_independent_git_tag_mismatch_is_rejected(self):
        wrong = mock.Mock(stdout="0" * 40 + "\n")
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(support, "run", return_value=wrong):
                with self.assertRaisesRegex(support.SupportError, "tag/source"):
                    support.verify_tag(Path(directory) / "git")


@unittest.skipUnless(os.environ.get("FEATURES_ENHANCER_VENV"), "set FEATURES_ENHANCER_VENV")
class InstalledReleaseTests(unittest.TestCase):
    def setUp(self):
        self.environment = Path(os.environ["FEATURES_ENHANCER_VENV"])

    def test_official_installation_is_accepted(self):
        tool, record = support.verified_tool(self.environment)
        self.assertEqual(support.run(str(tool), "--version").stdout.strip(), "0.1.5")
        self.assertEqual(record["version"], "0.1.5")
        self.assertEqual(record["revision"], "0120bee2f2455e4c832d1d5ddae0a4cb03cb9477")
        self.assertEqual(record["wheel_sha256"], support.approval()["wheel"]["sha256"])

    def test_installed_mutations_and_rewritten_same_run_hashes_are_rejected(self):
        package = support.installed_package(self.environment)
        site = package.parent
        record_path = self.environment / support.PROVENANCE
        original_record = record_path.read_bytes()
        record = json.loads(original_record)
        cases = [(package / "cli.py", b"\n# altered module\n"),
                 (package / "assets/gnatdoc-theme.css", b"\n/* altered */\n"),
                 (package / "assets/gnatdoc-navigation.js", b"\n// altered\n"),
                 (self.environment / "release-provenance.json", b"\n"),
                 (self.environment / "bin/gnatdoc-enhancer", b"\n# altered launcher\n"),
                 (site / "markdown_it/main.py", b"\n# altered renderer\n"),
                 (site / "mdurl/_parse.py", b"\n# altered renderer\n")]
        for path, addition in cases:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                try:
                    path.write_bytes(original + addition)
                    # Rewriting the mutable receipt cannot authorize modified code.
                    rewritten = json.loads(original_record)
                    relative = path.relative_to(package).as_posix() if path.is_relative_to(package) else None
                    if relative:
                        rewritten["files"][relative] = support.sha256(path)
                    record_path.write_text(json.dumps(rewritten))
                    with self.assertRaises(support.SupportError):
                        support.verified_tool(self.environment)
                finally:
                    path.write_bytes(original)
                    record_path.write_bytes(original_record)
        for key, value in (("revision", "0" * 40), ("version", "0.1.0"),
                           ("tag_object", "0" * 40), ("wheel_sha256", "0" * 64)):
            with self.subTest(provenance=key):
                try:
                    record_path.write_text(json.dumps(dict(record, **{key: value})))
                    with self.assertRaises(support.SupportError):
                        support.verified_tool(self.environment)
                finally:
                    record_path.write_bytes(original_record)
        support.verified_tool(self.environment)

    def test_other_version_module_and_metadata_are_rejected(self):
        package = support.installed_package(self.environment)
        for path, old, new in (
                (package / "__init__.py", b'"0.1.5"', b'"0.1.0"'),
                (package / "__init__.py", b'"0.1.5"', b'"0.1.6.dev0"'),
                (package.parent / support.dist_info() / "METADATA",
                 b"Version: 0.1.5\n", b"Version: 0.1.0\n")):
            original = path.read_bytes()
            try:
                self.assertIn(old, original)
                path.write_bytes(original.replace(old, new))
                with self.assertRaises(support.SupportError):
                    support.verified_tool(self.environment)
            finally:
                path.write_bytes(original)


@unittest.skipUnless(os.environ.get("FEATURES_ENHANCED_SITE"), "set FEATURES_ENHANCED_SITE")
class OutputComparisonTests(unittest.TestCase):
    def test_only_the_reviewed_release_transition_is_accepted(self):
        import shutil
        import compare_gnatdoc_release as comparison
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old, new = root / "old", root / "new"
            shutil.copytree(Path(os.environ["FEATURES_ENHANCED_SITE"]), new)
            shutil.copytree(new, old)
            # Reconstruct the v0.1.0 bytes from the reviewed fixture-free inputs.
            index = old / "api/index.html"
            index.write_text(index.read_text().replace(comparison.NEW_LABEL, comparison.OLD_LABEL))
            navigation = old / comparison.NAVIGATION
            navigation.write_bytes(b"0.1.0 navigation")
            manifest = old / "api/presentation.json"
            text = manifest.read_text()
            for value, replacement in (
                    (f'"enhancer_version": "{comparison.NEW_VERSION}"',
                     f'"enhancer_version": "{comparison.OLD_VERSION}"'),
                    (support.sha256(new / "api/index.html"), support.sha256(index)),
                    (comparison.NEW_NAVIGATION, support.sha256(navigation))):
                self.assertEqual(text.count(value), 1, value)
                text = text.replace(value, replacement)
            manifest.write_text(text)
            with mock.patch.object(comparison, "OLD_NAVIGATION", support.sha256(navigation)):
                report = comparison.compare(old, new)
                self.assertEqual(report["census"]["release"]["resolved_references"], 248)
                self.assertEqual(sorted(k for k, v in report["files"].items()
                                        if v["classification"] != "byte-identical"),
                                 comparison.CHANGED)
                for path, addition in ((new / "index.html", "<!-- semantic drift -->"),
                                       (new / "api/index.html", "<!-- semantic drift -->"),
                                       (new / "api/presentation.json", "\n"),
                                       (new / comparison.NAVIGATION, "\n// drift\n")):
                    original = path.read_text()
                    try:
                        path.write_text(original + addition)
                        with self.assertRaises(support.SupportError):
                            comparison.compare(old, new)
                    finally:
                        path.write_text(original)
                (new / "unexpected.html").write_text("unexpected")
                with self.assertRaises(support.SupportError):
                    comparison.compare(old, new)
