"""Production adoption safety baseline, not a timeless post-migration contract.

These offline checks preserve the observed legacy configuration during import.
Deliberate post-migration changes require a separately reviewed new baseline;
passing tests neither refreshes AWS observations nor approves execution.
"""

from collections import Counter
import hashlib
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_infrastructure_import as tools


class ProductionInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.observed, cls.stacks = tools.load_inventory(ROOT)
        cls.templates = {
            name: yaml.load(stack["template_body"], Loader=tools.UniqueLoader)
            for name, stack in cls.stacks.items()
        }
        cls.evidence = tools.parse_json(
            (ROOT / "infrastructure/verification/template-summaries.json").read_text()
        )
        cls.dns = yaml.load((ROOT / "infrastructure/dns/records.yaml").read_bytes(),
                            Loader=tools.UniqueLoader)

    def test_exact_adoption_resource_boundaries(self):
        expected = {
            "web": {
                "SiteBucket": "AWS::S3::Bucket",
                "RedirectBucket": "AWS::S3::Bucket",
                "SiteBucketPolicy": "AWS::S3::BucketPolicy",
                "LegacyOriginAccessIdentity": "AWS::CloudFront::CloudFrontOriginAccessIdentity",
                "SiteDistribution": "AWS::CloudFront::Distribution",
            },
            "dnssec-key": {"DnssecKey": "AWS::KMS::Key", "DnssecKeyAlias": "AWS::KMS::Alias"},
            "dns": {
                "SiteHostedZone": "AWS::Route53::HostedZone",
                "SiteKeySigningKey": "AWS::Route53::KeySigningKey",
                "SiteDnssec": "AWS::Route53::DNSSEC",
            },
        }
        self.assertEqual(set(self.stacks), set(expected))
        self.assertEqual([len(self.templates[name]["Resources"]) for name in tools.STACKS], [5, 2, 3])
        for name, types in expected.items():
            with self.subTest(stack=name):
                actual = {logical: resource["Type"]
                          for logical, resource in self.templates[name]["Resources"].items()}
                # Exact equality also excludes native record sets, certificates,
                # new access/cache policies, custom resources and nested stacks.
                self.assertEqual(actual, types)

    def test_recorded_template_evidence_and_identifier_groupings(self):
        self.assertEqual(self.evidence["account_id"], "995361647121")
        self.assertEqual(self.evidence["account_id"], self.manifest["account_id"])
        self.assertIs(self.evidence["change_sets_created"], False)
        self.assertIs(self.evidence["execution_approved"], False)
        self.assertEqual(set(self.evidence["templates"]), set(self.stacks))
        regions = {"web": "eu-west-1", "dnssec-key": "us-east-1", "dns": "eu-west-1"}
        for name, stack in self.stacks.items():
            with self.subTest(stack=name):
                recorded = self.evidence["templates"][name]
                self.assertEqual(recorded["region"], regions[name])
                self.assertEqual(recorded["region"], stack["region"])
                body = stack["template_body"]
                self.assertEqual(body, stack["template_path"].read_bytes())
                self.assertEqual(len(body), recorded["template_bytes"])
                self.assertEqual(hashlib.sha256(body).hexdigest(), recorded["template_sha256"])
                self.assertEqual(recorded["validate_template"]["Parameters"], [])
                self.assertNotIn("Parameters", self.templates[name])
                self.assertEqual(recorded["validate_template"]["Description"], self.templates[name]["Description"])
                expected = Counter(
                    (mapping["LogicalResourceId"], mapping["ResourceType"],
                     tuple(sorted(mapping["ResourceIdentifier"])))
                    for mapping in stack["mappings"]
                )
                actual = Counter()
                for group in recorded["resource_identifier_summaries"]:
                    # GetTemplateSummary represents the KSK composite as one
                    # comma-separated entry; it denotes two identifier fields.
                    fields = [field.strip() for entry in group["ResourceIdentifiers"]
                              for field in entry.split(",")]
                    self.assertTrue(fields)
                    self.assertTrue(all(fields))
                    self.assertEqual(len(fields), len(set(fields)))
                    self.assertTrue(group["LogicalResourceIds"])
                    for logical in group["LogicalResourceIds"]:
                        actual[(logical, group["ResourceType"], tuple(sorted(fields)))] += 1
                self.assertEqual(actual, expected)
                self.assertEqual(sum(actual.values()), len(self.templates[name]["Resources"]))

    def test_dns_baseline_structure(self):
        zone = "svpsouthruislip.org.uk."
        self.assertEqual(self.dns["HostedZoneId"], "Z3SM1DWWC45TX")
        self.assertEqual(self.dns["ZoneName"], zone)
        self.assertIs(self.dns["ManagedByCloudFormation"], False)
        self.assertEqual(self.dns["ObservedAt"], self.manifest["observed_at"])
        self.assertEqual(set(self.dns["ZoneManagedTypes"]), {"NS", "SOA"})
        records = self.dns["ResourceRecordSets"]
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 11)
        identities = []
        for record in records:
            with self.subTest(record=record["Name"], kind=record["Type"]):
                name = record["Name"]
                self.assertTrue(name == zone or name.endswith("." + zone))
                identities.append((name.lower(), record["Type"], record.get("SetIdentifier")))
                if "AliasTarget" in record:
                    self.assertNotIn("TTL", record)
                    self.assertNotIn("ResourceRecords", record)
                    alias = record["AliasTarget"]
                    self.assertEqual(alias["HostedZoneId"], "Z2FDTNDATAQYW2")
                    self.assertEqual(alias["DNSName"], "d1myhs7tjj0y6f.cloudfront.net.")
                    self.assertIs(alias["EvaluateTargetHealth"], False)
                else:
                    self.assertIs(type(record["TTL"]), int)
                    self.assertGreater(record["TTL"], 0)
                    values = record["ResourceRecords"]
                    self.assertIsInstance(values, list)
                    self.assertTrue(values)
                    for value in values:
                        self.assertEqual(set(value), {"Value"})
                        self.assertIsInstance(value["Value"], str)
                        self.assertTrue(value["Value"])
        self.assertEqual(len(identities), len(set(identities)))
        self.assertNotIn("AAAA", {record["Type"] for record in records})

    def test_dns_managed_mail_and_validation_records_preserved(self):
        zone = self.dns["ZoneName"]
        records = {(record["Name"], record["Type"]): record
                   for record in self.dns["ResourceRecordSets"]}
        def values(name, kind):
            return {entry["Value"] for entry in records[(name, kind)]["ResourceRecords"]}
        self.assertEqual(values(zone, "NS"), {
            "ns-2007.awsdns-58.co.uk.", "ns-509.awsdns-63.com.",
            "ns-1040.awsdns-02.org.", "ns-535.awsdns-02.net.",
        })
        self.assertEqual(values(zone, "SOA"), {
            "ns-2007.awsdns-58.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"
        })
        self.assertEqual(values(zone, "MX"), {
            "10 in1-smtp.messagingengine.com", "20 in2-smtp.messagingengine.com"
        })
        self.assertEqual(values(zone, "TXT"), {'"v=spf1 include:spf.messagingengine.com ?all"'})
        expected_cnames = {
            f"fm{index}._domainkey.{zone}": {f"fm{index}.svpsouthruislip.org.uk.dkim.fmhosted.com"}
            for index in (1, 2, 3)
        }
        expected_cnames.update({
            "www." + zone: {"svpsouthruislip.org.uk"},
            "_d08e569883a73681ff154aff2e5d549f." + zone: {
                "_05703d9e8dd3247d18ac1ce37507e9a8.nhqijqilxf.acm-validations.aws."
            },
            "_764c2cf2fdef9013cd040433f49fcd2d.www." + zone: {
                "_275923ecfb009e12f1a23af863548feb.nhqijqilxf.acm-validations.aws."
            },
        })
        actual_cnames = {name: values(name, kind) for name, kind in records if kind == "CNAME"}
        self.assertEqual(actual_cnames, expected_cnames)
        self.assertEqual(Counter(record["Type"] for record in self.dns["ResourceRecordSets"]),
                         Counter({"A": 1, "MX": 1, "NS": 1, "SOA": 1, "TXT": 1, "CNAME": 6}))

    def test_legacy_website_and_cloudfront_boundaries(self):
        resources = self.templates["web"]["Resources"]
        site = resources["SiteBucket"]["Properties"]
        redirect = resources["RedirectBucket"]["Properties"]
        block_keys = {"BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"}
        self.assertEqual(site["AccessControl"], "Private")
        self.assertEqual(site["PublicAccessBlockConfiguration"], dict.fromkeys(block_keys, False))
        self.assertEqual(redirect["PublicAccessBlockConfiguration"], dict.fromkeys(block_keys, True))
        for properties in (site, redirect):
            self.assertNotIn("OwnershipControls", properties)
            self.assertNotIn("VersioningConfiguration", properties)
        self.assertEqual(redirect["WebsiteConfiguration"]["RedirectAllRequestsTo"],
                         {"HostName": "svpsouthruislip.org.uk", "Protocol": "http"})
        config = resources["SiteDistribution"]["Properties"]["DistributionConfig"]
        self.assertEqual(len(config["Origins"]), 1)
        origin = config["Origins"][0]
        self.assertEqual(origin["DomainName"], "svpsouthruislip.org.uk.s3-website-eu-west-1.amazonaws.com")
        self.assertEqual(origin["CustomOriginConfig"]["OriginProtocolPolicy"], "http-only")
        self.assertNotIn("S3OriginConfig", origin)
        self.assertNotIn("OriginAccessControlId", origin)
        behavior = config["DefaultCacheBehavior"]
        self.assertEqual(behavior["TargetOriginId"], origin["Id"])
        self.assertEqual([behavior[key] for key in ("MinTTL", "DefaultTTL", "MaxTTL")], [600, 3600, 86400])
        self.assertEqual(behavior["ForwardedValues"], {"QueryString": True, "Cookies": {"Forward": "none"}})
        self.assertNotIn("CachePolicyId", behavior)
        self.assertNotIn("OriginRequestPolicyId", behavior)
        self.assertFalse(config.get("CacheBehaviors"))
        certificate = config["ViewerCertificate"]
        self.assertEqual(certificate["MinimumProtocolVersion"], "TLSv1.1_2016")
        self.assertEqual(certificate["AcmCertificateArn"],
                         "arn:aws:acm:us-east-1:995361647121:certificate/719a94fe-dad7-4dbf-9a1d-cbad2afc96b7")

    def test_existing_signing_key_and_dnssec_dependency(self):
        key = self.templates["dnssec-key"]["Resources"]["DnssecKey"]["Properties"]
        self.assertIs(key["Enabled"], True)
        self.assertEqual(key["KeySpec"], "ECC_NIST_P256")
        self.assertEqual(key["KeyUsage"], "SIGN_VERIFY")
        resources = self.templates["dns"]["Resources"]
        ksk = resources["SiteKeySigningKey"]["Properties"]
        self.assertEqual(ksk["Status"], "ACTIVE")
        self.assertEqual(ksk["Name"], "svpsouthruislip")
        self.assertEqual(ksk["HostedZoneId"], {"Ref": "SiteHostedZone"})
        self.assertEqual(ksk["KeyManagementServiceArn"],
                         "arn:aws:kms:us-east-1:995361647121:key/944105a2-c852-4c4f-a0f2-a0f1b91344c9")
        self.assertEqual(resources["SiteDnssec"]["DependsOn"], "SiteKeySigningKey")
        self.assertEqual(resources["SiteDnssec"]["Properties"]["HostedZoneId"], {"Ref": "SiteHostedZone"})


if __name__ == "__main__":
    unittest.main()
