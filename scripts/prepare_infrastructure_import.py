"""Validate recorded infrastructure and render local-only import review artifacts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[1]
STACKS = ("web", "dnssec-key", "dns")
IDENTIFIERS = {
    "AWS::S3::Bucket": ("BucketName",),
    "AWS::S3::BucketPolicy": ("Bucket",),
    "AWS::CloudFront::Distribution": ("Id",),
    "AWS::CloudFront::CloudFrontOriginAccessIdentity": ("Id",),
    "AWS::KMS::Key": ("KeyId",),
    "AWS::KMS::Alias": ("AliasName",),
    "AWS::Route53::HostedZone": ("Id",),
    "AWS::Route53::DNSSEC": ("HostedZoneId",),
    "AWS::Route53::KeySigningKey": ("HostedZoneId", "Name"),
}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if not isinstance(key, str) or key in result:
            raise ValueError(f"Invalid or duplicate key: {key!r}")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML loader which refuses duplicate keys, including merge keys."""


def yaml_mapping(loader, node):
    return unique_pairs((loader.construct_object(key, deep=True),
                         loader.construct_object(value, deep=True))
                        for key, value in node.value)


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, yaml_mapping)


def parse_json(text):
    return json.loads(text, object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"Invalid JSON constant: {value}")))


def repo_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("Manifest paths must be nonempty repository-relative paths")
    root = Path(root).resolve()
    path = (root / value).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Path escapes repository or is not a file: {value}")
    return path


def reject_transforms(value, ancestors=None):
    """Reject inline macros and cyclic YAML structures without following aliases forever."""
    if not isinstance(value, (dict, list)):
        return
    ancestors = set() if ancestors is None else ancestors
    if id(value) in ancestors:
        raise ValueError("Cyclic template structures are unsupported")
    ancestors.add(id(value))
    try:
        if isinstance(value, dict) and ("Transform" in value or "Fn::Transform" in value):
            raise ValueError("Template transforms are unsupported")
        for child in value.values() if isinstance(value, dict) else value:
            reject_transforms(child, ancestors)
    finally:
        ancestors.remove(id(value))


def validate_stack(template, mappings, expected):
    """Require exact, retained resource coverage and recorded physical identities."""
    reject_transforms(template)
    if not isinstance(template, dict) or set(template) - {
        "AWSTemplateFormatVersion", "Description", "Metadata", "Mappings", "Conditions", "Resources"
    }:
        raise ValueError("Unsupported template sections (including Parameters, Outputs or Transform)")
    resources = template.get("Resources")
    if not isinstance(resources, dict) or not resources:
        raise ValueError("Resources must be a nonempty object")
    if not isinstance(expected, dict) or set(expected) != set(resources):
        raise ValueError("Expected physical IDs must exactly cover resources")
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("Import mapping must be a nonempty list")
    seen = set()
    for item in mappings:
        if not isinstance(item, dict) or set(item) != {
            "ResourceType", "LogicalResourceId", "ResourceIdentifier"
        }:
            raise ValueError("Malformed import mapping entry")
        logical = item["LogicalResourceId"]
        if not isinstance(logical, str) or logical in seen or logical not in resources:
            raise ValueError("Duplicate or unexpected logical resource ID")
        seen.add(logical)
        resource = resources[logical]
        if not isinstance(resource, dict):
            raise ValueError("Resource must be an object")
        kind = resource.get("Type")
        if not isinstance(kind, str) or kind not in IDENTIFIERS or item["ResourceType"] != kind:
            raise ValueError("Unsupported or mismatched resource type")
        if any(resource.get(key) != "Retain" for key in ("DeletionPolicy", "UpdateReplacePolicy")):
            raise ValueError("Both retention policies must be Retain")
        identifier = item["ResourceIdentifier"]
        keys = IDENTIFIERS[kind]
        if not isinstance(identifier, dict) or set(identifier) != set(keys):
            raise ValueError("Incorrect resource identifier schema")
        if any(not isinstance(identifier[key], str) or not identifier[key] for key in keys):
            raise ValueError("Resource identifiers must be nonempty strings")
        if not isinstance(expected[logical], str) or "|".join(identifier[key] for key in keys) != expected[logical]:
            raise ValueError(f"Physical identity differs from inventory: {logical}")
    if seen != set(resources):
        raise ValueError("Missing import mappings")


def validate_policy(policy):
    if not isinstance(policy, dict) or set(policy) != {"Statement"}:
        raise ValueError("Malformed stack policy")
    statements = policy["Statement"]
    if not isinstance(statements, list) or not statements:
        raise ValueError("Missing stack policy statements")
    allowed, denied = set(), set()
    for statement in statements:
        if not isinstance(statement, dict) or set(statement) != {"Effect", "Action", "Resource", "Principal"}:
            raise ValueError("Unsupported stack policy statement")
        if statement["Resource"] != "*" or statement["Principal"] != "*":
            raise ValueError("Stack policy must cover all resources and principals")
        actions = statement["Action"]
        actions = [actions] if isinstance(actions, str) else actions
        if not isinstance(actions, list) or not actions or any(not isinstance(a, str) for a in actions):
            raise ValueError("Invalid stack policy actions")
        if statement["Effect"] == "Allow" and set(actions) <= {"Update:*"}:
            allowed.update(actions)
        elif statement["Effect"] == "Deny" and set(actions) <= {"Update:Replace", "Update:Delete"}:
            denied.update(actions)
        else:
            raise ValueError("Unsupported stack policy effect or actions")
    if allowed != {"Update:*"} or denied != {"Update:Replace", "Update:Delete"}:
        raise ValueError("Stack policy must allow updates and explicitly deny replacement and deletion")


def load_inventory(root=ROOT):
    """Load only the fixed production manifest, without environment overrides."""
    manifest = parse_json(repo_path(root, "infrastructure/environments/production.json").read_text())
    if not isinstance(manifest, dict) or set(manifest) != {"account_id", "observed_at", "stack_policy", "order", "stacks"}:
        raise ValueError("Malformed production manifest")
    if manifest["account_id"] != "995361647121" or manifest["order"] != list(STACKS):
        raise ValueError("Unexpected account or stack order")
    observed = datetime.strptime(manifest["observed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if not isinstance(manifest["stacks"], dict) or set(manifest["stacks"]) != set(STACKS):
        raise ValueError("Unexpected stacks")
    validate_policy(parse_json(repo_path(root, manifest["stack_policy"]).read_text()))
    loaded = {}
    for name in STACKS:
        stack = manifest["stacks"][name]
        if not isinstance(stack, dict) or set(stack) != {"stack_name", "region", "template", "resources_to_import", "expected_physical_ids"}:
            raise ValueError("Malformed stack configuration")
        if stack["stack_name"] != f"svpsouthruislip-{name}" or stack["region"] != ("us-east-1" if name == "dnssec-key" else "eu-west-1"):
            raise ValueError("Unexpected stack name or region")
        template_path = repo_path(root, stack["template"])
        template_body = template_path.read_bytes()
        mapping_body = repo_path(root, stack["resources_to_import"]).read_bytes()
        mappings = parse_json(mapping_body.decode("utf-8"))
        validate_stack(yaml.load(template_body, Loader=UniqueLoader), mappings, stack["expected_physical_ids"])
        loaded[name] = dict(stack, template_body=template_body, mapping_body=mapping_body,
                            mappings=mappings, template_path=template_path)
    return manifest, observed, loaded


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render(root, name, output_dir, change_set_name, now=None):
    """Create a private, non-overwriting local review bundle; never invoke AWS."""
    if not isinstance(change_set_name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,127}", change_set_name):
        raise ValueError("Change-set name must start with an ASCII letter and contain at most 128 ASCII letters, digits or hyphens")
    if name not in STACKS:
        raise ValueError("Unknown stack")
    manifest, observed, stacks = load_inventory(root)
    stack = stacks[name]
    request = {
        "StackName": stack["stack_name"], "ChangeSetName": change_set_name,
        "ChangeSetType": "IMPORT", "Description": "Local review of recorded infrastructure import; not execution approval",
        "TemplateBody": stack["template_body"].decode("utf-8"),
        "ResourcesToImport": stack["mappings"], "ClientToken": str(uuid.uuid4()),
    }
    artifacts = {"request.json": json_bytes(request), "template.yaml": stack["template_body"],
                 "resources-to-import.json": stack["mapping_body"]}
    now = now or datetime.now(timezone.utc)
    summary = {"account_id": manifest["account_id"], "region": stack["region"],
               "stack_name": stack["stack_name"], "observed_at": manifest["observed_at"],
               "inventory_age_seconds": (now - observed).total_seconds(),
               "generated_at": now.isoformat(),
               "warning": "Recorded inventory only; no fresh AWS verification or execution approval. Negative age means inventory timestamp is in the future.",
               "next_step": "Review all artifacts and read the infrastructure import runbook before any separately authorized action.",
               "sha256": {key: hashlib.sha256(value).hexdigest() for key, value in artifacts.items()}}
    artifacts["review-summary.json"] = json_bytes(summary)
    # Open each ancestor without following symlinks; retain directory descriptors
    # so concurrent renames cannot redirect writes to another directory.
    output = Path(os.path.abspath(output_dir))
    fd = os.open(output.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in output.parts[1:-1]:
            try:
                os.mkdir(component, mode=0o700, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        os.mkdir(output.name, mode=0o700, dir_fd=fd)
        child = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        os.close(fd)
        fd = child
        os.fchmod(fd, 0o700)
        for filename, body in artifacts.items():
            file_fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(file_fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(body)
    finally:
        os.close(fd)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stack", choices=STACKS)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--change-set-name", required=True)
    args = parser.parse_args()
    try:
        summary = render(ROOT, args.stack, args.output_dir, args.change_set_name)
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as error:
        parser.exit(1, f"Import preparation failed: {error}\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
