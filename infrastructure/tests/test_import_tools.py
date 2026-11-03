"""Offline import tooling tests using isolated representative infrastructure fixtures."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import prepare_infrastructure_import as tools
import check_infrastructure as checker


class ImportToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifest = {
            "account_id": "995361647121", "observed_at": "2026-11-02T15:56:41Z",
            "stack_policy": "infrastructure/stack-policy.json",
            "order": list(tools.STACKS), "stacks": {},
        }
        groups = {
            "web": [
                ("SiteBucket", "AWS::S3::Bucket", {"BucketName": "svpsouthruislip.org.uk"}),
                ("RedirectBucket", "AWS::S3::Bucket", {"BucketName": "www.svpsouthruislip.org.uk"}),
                ("SiteBucketPolicy", "AWS::S3::BucketPolicy", {"Bucket": "svpsouthruislip.org.uk"}),
                ("LegacyOriginAccessIdentity", "AWS::CloudFront::CloudFrontOriginAccessIdentity", {"Id": "E1H05UTZYYPBPP"}),
                ("SiteDistribution", "AWS::CloudFront::Distribution", {"Id": "E2ZXKXV2U7OYGL"}),
            ],
            "dnssec-key": [
                ("DnssecKey", "AWS::KMS::Key", {"KeyId": "944105a2-c852-4c4f-a0f2-a0f1b91344c9"}),
                ("DnssecKeyAlias", "AWS::KMS::Alias", {"AliasName": "alias/svpsouthruislipkey"}),
            ],
            "dns": [
                ("SiteHostedZone", "AWS::Route53::HostedZone", {"Id": "Z3SM1DWWC45TX"}),
                ("SiteKeySigningKey", "AWS::Route53::KeySigningKey", {"HostedZoneId": "Z3SM1DWWC45TX", "Name": "svpsouthruislip"}),
                ("SiteDnssec", "AWS::Route53::DNSSEC", {"HostedZoneId": "Z3SM1DWWC45TX"}),
            ],
        }
        self.templates, self.mappings = {}, {}
        for name, entries in groups.items():
            self.templates[name] = {"Resources": {
                logical: {"Type": kind, "DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain", "Properties": {}}
                for logical, kind, _ in entries}}
            self.mappings[name] = [dict(LogicalResourceId=logical, ResourceType=kind, ResourceIdentifier=identifier)
                                   for logical, kind, identifier in entries]
            self.manifest["stacks"][name] = {
                "stack_name": f"svpsouthruislip-{name}",
                "region": "us-east-1" if name == "dnssec-key" else "eu-west-1",
                "template": f"infrastructure/templates/{name}.yaml",
                "resources_to_import": f"infrastructure/imports/{name}.json",
                "expected_physical_ids": {logical: "|".join(identifier[key] for key in tools.IDENTIFIERS[kind])
                                          for logical, kind, identifier in entries},
            }
            self.write(f"infrastructure/templates/{name}.yaml", yaml.safe_dump(self.templates[name]))
            self.write(f"infrastructure/imports/{name}.json", json.dumps(self.mappings[name]))
        self.policy = {"Statement": [
            {"Effect": "Allow", "Action": "Update:*", "Resource": "*", "Principal": "*"},
            {"Effect": "Deny", "Action": ["Update:Replace", "Update:Delete"], "Resource": "*", "Principal": "*"},
        ]}
        self.write("infrastructure/stack-policy.json", json.dumps(self.policy))
        self.save_manifest()

    def write(self, relative, body):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)

    def save_manifest(self):
        self.write("infrastructure/environments/production.json", json.dumps(self.manifest))

    def validate(self, name="web", template=None, mappings=None):
        tools.validate_stack(self.templates[name] if template is None else template,
                             self.mappings[name] if mappings is None else mappings,
                             self.manifest["stacks"][name]["expected_physical_ids"])

    def test_render_all_stacks_and_artifact_integrity(self):
        for name, count in zip(tools.STACKS, (5, 2, 3)):
            with self.subTest(stack=name):
                output = self.root / f"review-{name}"
                summary = tools.render(self.root, name, output, "Review-1",
                                       datetime(2026, 11, 3, tzinfo=timezone.utc))
                request = json.loads((output / "request.json").read_text())
                self.assertEqual(set(request), {"StackName", "ChangeSetName", "ChangeSetType", "Description",
                                                "TemplateBody", "ResourcesToImport", "ClientToken"})
                self.assertEqual(request["ChangeSetType"], "IMPORT")
                self.assertEqual(len(request["ResourcesToImport"]), count)
                self.assertEqual(request["ResourcesToImport"], self.mappings[name])
                template = (self.root / self.manifest["stacks"][name]["template"]).read_bytes()
                self.assertEqual(request["TemplateBody"].encode(), template)
                self.assertEqual((output / "template.yaml").read_bytes(), template)
                mapping = (self.root / self.manifest["stacks"][name]["resources_to_import"]).read_bytes()
                self.assertEqual((output / "resources-to-import.json").read_bytes(), mapping)
                self.assertEqual(summary, json.loads((output / "review-summary.json").read_text()))
                for filename, digest in summary["sha256"].items():
                    self.assertEqual(hashlib.sha256((output / filename).read_bytes()).hexdigest(), digest)
                self.assertEqual(summary["account_id"], "995361647121")
                self.assertEqual(summary["region"], self.manifest["stacks"][name]["region"])
                self.assertGreater(summary["inventory_age_seconds"], 0)
                self.assertIn("no fresh AWS verification", summary["warning"])
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
                for path in output.iterdir():
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                before = (output / "request.json").read_bytes()
                with self.assertRaises(FileExistsError):
                    tools.render(self.root, name, output, "Review-2")
                self.assertEqual((output / "request.json").read_bytes(), before)

    def test_invalid_names_leave_no_output(self):
        for name in ("", "1bad", "Bad_name", "Bad name", "Äbad", "a" * 129, "Good\n"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                tools.render(self.root, "web", self.root / "review", name)
        self.assertFalse((self.root / "review").exists())

    def test_mapping_shape_coverage_and_type(self):
        cases = [[], {}, self.mappings["web"][:-1], self.mappings["web"] + [self.mappings["web"][0]]]
        for field, value in (("LogicalResourceId", "Unexpected"), ("ResourceType", "AWS::KMS::Key"),
                             ("ResourceIdentifier", {"Id": "wrong"}), ("ResourceIdentifier", {"BucketName": "wrong"}),
                             ("ResourceIdentifier", {"BucketName": 123}), ("Extra", True)):
            mappings = deepcopy(self.mappings["web"])
            mappings[0][field] = value
            cases.append(mappings)
        for mappings in cases:
            with self.subTest(mappings=mappings), self.assertRaises(ValueError):
                self.validate(mappings=mappings)

    def test_composite_identity_order(self):
        mappings = deepcopy(self.mappings["dns"])
        mappings[1]["ResourceIdentifier"]["Name"] = "wrong"
        with self.assertRaises(ValueError):
            self.validate("dns", mappings=mappings)

    def test_template_safety(self):
        inline = deepcopy(self.templates["web"])
        inline["Resources"]["SiteBucket"]["Properties"] = {"Fn::Transform": {"Name": "Macro"}}
        cases = [{"Resources": {}}, [], inline]
        for section in ("Outputs", "Parameters", "Transform"):
            template = deepcopy(self.templates["web"])
            template[section] = {}
            cases.append(template)
        for field, value in (("DeletionPolicy", None), ("UpdateReplacePolicy", "Delete"),
                             ("Type", "AWS::CloudFormation::Stack"), ("Type", "Custom::Resource"),
                             ("Type", "AWS::Unknown::Resource")):
            template = deepcopy(self.templates["web"])
            template["Resources"]["SiteBucket"][field] = value
            cases.append(template)
        for template in cases:
            with self.subTest(template=template), self.assertRaises(ValueError):
                self.validate(template=template)

    def test_duplicate_keys_and_unsafe_yaml(self):
        for text in ('{"a": 1, "a": 2}', '{"a": {"b": 1, "b": 2}}', '{"a": NaN}'):
            with self.assertRaises(ValueError):
                tools.parse_json(text)
        for text in ("Resources: {}\nResources: {}", "a: {b: 1, b: 2}", "!!python/object:builtins.object {}",
                     "a: &a {x: 1}\nb: {<<: *a, x: 2}"):
            with self.assertRaises((ValueError, yaml.YAMLError)):
                yaml.load(text, Loader=tools.UniqueLoader)

    def test_manifest_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "template.yaml"
            target.write_text(yaml.safe_dump(self.templates["web"]))
            (self.root / "escape.yaml").symlink_to(target)
            for value in (str(target), "../outside.yaml", "escape.yaml"):
                with self.subTest(path=value), self.assertRaises((ValueError, OSError)):
                    tools.repo_path(self.root, value)
        self.manifest["stacks"]["web"]["template"] = "../outside.yaml"
        self.save_manifest()
        with self.assertRaises((ValueError, OSError)):
            tools.load_inventory(self.root)

    def test_output_symlinks_rejected(self):
        target = self.root / "target"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target, target_is_directory=True)
        for output in (link, link / "review"):
            with self.subTest(output=output), self.assertRaises(OSError):
                tools.render(self.root, "web", output, "Review")
        self.assertEqual(list(target.iterdir()), [])
        dangling = self.root / "dangling"
        dangling.symlink_to(self.root / "absent")
        with self.assertRaises(OSError):
            tools.render(self.root, "web", dangling, "Review")

    def test_policy_fail_closed(self):
        tools.validate_policy(self.policy)
        for mutate in (
            lambda p: p["Statement"].pop(),
            lambda p: p["Statement"][1].update(Action="Update:Delete"),
            lambda p: p["Statement"][1].update(Resource="LogicalResourceId/SiteBucket"),
            lambda p: p["Statement"][0].update(Principal="someone"),
            lambda p: p["Statement"][1].update(Condition={}),
        ):
            policy = deepcopy(self.policy)
            mutate(policy)
            with self.assertRaises(ValueError):
                tools.validate_policy(policy)

    def test_checker_regions_and_nonzero(self):
        calls = []
        def runner(command, check):
            calls.append(command)
            self.assertFalse(check)
            return SimpleNamespace(returncode=0)
        checker.check(self.root, runner=runner, executable="local-cfn-lint")
        self.assertEqual([call[call.index("--regions") + 1] for call in calls],
                         ["eu-west-1", "us-east-1", "eu-west-1"])
        self.assertEqual(len(calls), 3)
        with self.assertRaises(ValueError):
            checker.check(self.root, runner=lambda *a, **kw: SimpleNamespace(returncode=2), executable="local-cfn-lint")
        with patch.object(checker.shutil, "which", return_value=None), self.assertRaisesRegex(ValueError, "not installed"):
            checker.check(self.root)

    def test_malformed_real_input_is_rejected_before_lint(self):
        self.write("infrastructure/imports/web.json", '[{"LogicalResourceId":"SiteBucket","LogicalResourceId":"Other"}]')
        with self.assertRaises(ValueError):
            checker.check(self.root, runner=lambda *a, **kw: self.fail("Linter must not run"), executable="unused")


if __name__ == "__main__":
    unittest.main()
