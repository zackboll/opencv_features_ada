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

    def test_wrong_tag_source_tree_and_version_are_rejected(self):
        approved = support.approval()
        provenance = {
            "repository": approved["repository"], "source_commit": approved["revision"],
            "git_tree": approved["tree"], "release_version": approved["version"],
            "annotated_tag": {"name": approved["tag"], "object_sha": approved["tag_object"],
                              "peeled_commit": approved["revision"], "peeled_tree": approved["tree"]},
            "archive_identities": {"wheel": {k: approved["wheel"][k]
                                              for k in ("name", "bytes", "sha256", "members")}},
            "assets": {approved["wheel"]["name"]: {
                "sha256": approved["wheel"]["sha256"], "bytes": approved["wheel"]["bytes"]}},
        }
        support.verify_release_provenance(provenance)
        for key in ("source_commit", "git_tree", "release_version"):
            altered = dict(provenance, **{key: "wrong"})
            with self.subTest(key=key), self.assertRaises(support.SupportError):
                support.verify_release_provenance(altered)
        for key in ("name", "object_sha", "peeled_commit", "peeled_tree"):
            altered = dict(provenance, annotated_tag=dict(provenance["annotated_tag"], **{key: "wrong"}))
            with self.subTest(key=key), self.assertRaises(support.SupportError):
                support.verify_release_provenance(altered)

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
        self.assertEqual(support.run(str(tool), "--version").stdout.strip(), "0.1.0")
        self.assertEqual(record["version"], "0.1.0")
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
        for key, value in (("revision", "0" * 40), ("version", "0.1.0.dev0"),
                           ("tag_object", "0" * 40), ("wheel_sha256", "0" * 64)):
            with self.subTest(provenance=key):
                try:
                    record_path.write_text(json.dumps(dict(record, **{key: value})))
                    with self.assertRaises(support.SupportError):
                        support.verified_tool(self.environment)
                finally:
                    record_path.write_bytes(original_record)
        support.verified_tool(self.environment)

    def test_development_module_and_metadata_are_rejected(self):
        package = support.installed_package(self.environment)
        for path, old, new in (
                (package / "__init__.py", b'"0.1.0"', b'"0.1.0.dev0"'),
                (package.parent / "ada_gnatdoc_enhancer-0.1.0.dist-info/METADATA",
                 b"Version: 0.1.0\n", b"Version: 0.1.0.dev0\n")):
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
    def test_only_release_version_transition_is_accepted(self):
        import shutil
        import compare_gnatdoc_release as comparison
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old, new = root / "old", root / "new"
            shutil.copytree(Path(os.environ["FEATURES_ENHANCED_SITE"]), old)
            shutil.copytree(old, new)
            manifest = old / "api/presentation.json"
            manifest.write_text(manifest.read_text().replace(
                '"enhancer_version": "0.1.0"', '"enhancer_version": "0.1.0.dev0"'))
            report = comparison.compare(old, new)
            self.assertEqual(report["census"]["release"]["resolved_references"], 248)
            for path, addition in ((new / "index.html", "<!-- semantic drift -->"),
                                   (new / "api/presentation.json", "\n")):
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