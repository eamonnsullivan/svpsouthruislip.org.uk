# Existing infrastructure adoption

This directory records the completed, verified **in-place CloudFormation adoption** of ten existing production resources into three stacks. It is not a new-site deployment or a modernization project. Preserve resource identities, website behavior, publishing access, DNS records, certificate, delegation and signing material.

Read the [verified inventory](../docs/infrastructure/inventory.md), [primary-source import research](../docs/infrastructure/import-research.md) and [import runbook](../docs/infrastructure/import-runbook.md) before any cloud operation. The runbook owns preparation, approval, execution and recovery procedures; the commands below are local checks only.

**All ten original resources are adopted and fully verified**: web (5), DNSSEC-key (2), DNS (3). Status: `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`; all three batches are `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`. See [aggregate acceptance](verification/adoption-completion.json), [web completion](verification/web-import-completion.json), [key completion](verification/dnssec-key-import-completion.json) and [DNS completion](verification/dns-import-completion.json). Original identities, protections, installed-policy readbacks, retained templates/events, direct configuration and supported native drift passed. Eight supported resources are `IN_SYNC`; unsupported BucketPolicy/KMS Alias were directly checked. Key and zone tags remain empty; only the two web buckets have the previously verified CloudFormation system tags. No physical resources were replaced or deleted.

Final DNS drift exports passed full review at `2026-11-03T14:54:03.563240Z`; final ownership/signing/configuration reads and public checks also matched. These are point-in-time observations, not exhaustive native-drift coverage or continuous zero-outage proof. The final refresh did not repeat the earlier full hosting audit or installed-policy APIs; previous verified readbacks remain evidence. Approval/pause history and exact ARNs remain in the [historical runbook](../docs/infrastructure/import-runbook.md) and batch JSON.

No further AWS writes are required for adoption. All adoption create/import/waiter/policy-install/drift commands are historical reference only; do not repeat them. All AWS writes were separately approved human actions; the assistant remained read-only. Verification conditions are met, but publication/configuration freeze remains until an explicit human decision to resume maintenance/publication. No normal update, commit/push, configuration change or IAM supplement removal is authorized by completion. The [read supplement](../docs/infrastructure/inventory-access.md) remains present; any later removal needs separate human approval and must remove only its additions, preserving unrelated statements.

## Artifacts

The [production manifest](environments/production.json) fixes account `995361647121`, stack order, Regions, input paths and expected physical IDs.

| Order | Proposed stack | Region | Template | Explicit import map | Resources |
| --- | --- | --- | --- | --- | --- |
| 1 | `svpsouthruislip-web` | `eu-west-1` | [web.yaml](templates/web.yaml) | [web.json](imports/web.json) | Two buckets, bucket policy, existing OAI, distribution (5) |
| 2 | `svpsouthruislip-dnssec-key` | `us-east-1` | [dnssec-key.yaml](templates/dnssec-key.yaml) | [dnssec-key.json](imports/dnssec-key.json) | Original KMS key and alias (2) |
| 3 | `svpsouthruislip-dns` | `eu-west-1` | [dns.yaml](templates/dns.yaml) | [dns.json](imports/dns.json) | Public zone, existing KSK, DNSSEC (3) |

Supporting files:

- [Aggregate completion](verification/adoption-completion.json) and [key](verification/dnssec-key-import-completion.json)/[DNS](verification/dns-import-completion.json) batch evidence: accepted identities, protections, templates/events, native drift, direct configuration and point-in-time health checks.
- [DNS baseline](dns/records.yaml): all 11 observed record sets, including NS/SOA, mail and certificate validation. **Not an apply/prune input or CloudFormation template.** Zone import does not adopt records.
- [Template verification](verification/template-summaries.json): read-only AWS summary/validation results, identifier groupings, byte counts and hashes for these exact templates.
- [Stack policy](stack-policy.json): allows updates while denying `Update:Replace` and `Update:Delete`; must be attached and verified at the runbook's post-import gate.
- [Scoped read-access policy](permissions/inventory-read-only.json): inventory access supplement, not a deployment template or import/execution grant.
- [Pinned dependencies](requirements.txt), [tooling tests](tests/test_import_tools.py) and [production baseline tests](tests/test_production_inventory.py).
- [Offline checker](../scripts/check_infrastructure.py) and [local review renderer](../scripts/prepare_infrastructure_import.py).

Templates have no initial Outputs or Parameters. Every imported resource has `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain`. KSK import requires both `HostedZoneId` and `Name` in one identifier object, not a joined input key or physical ID.

## Offline checks

Run from the repository root using Python **3.10+** (Python 3.14 was available during preparation). First-time dependency installation requires access to the configured package source; with the existing environment installed, checks do not need AWS or network access. Do not reinstall merely to review documentation offline.

```bash
python3 -m venv .venv-infrastructure
.venv-infrastructure/bin/python -m pip install -r infrastructure/requirements.txt
PATH="$PWD/.venv-infrastructure/bin:$PATH" .venv-infrastructure/bin/python scripts/check_infrastructure.py
.venv-infrastructure/bin/python -m unittest discover -s infrastructure/tests -v
```

The checker validates manifest paths, exact retained resource/map coverage, recorded identities and policy shape, then runs installed `cfn-lint` for each template's actual Region, failing on warnings. Tests additionally check recorded template hashes and summary groupings, DNS records, preservation of legacy hosting/signing settings, and renderer safety. They are adoption-baseline checks, not a timeless prohibition on separately approved future changes. They do not compare fresh AWS properties, establish permissions, back up content or prove operational health. A site build is unnecessary for documentation-only changes.

Keep the existing root `.gitignore` entries for `/.venv-infrastructure/` and `/infrastructure/work/`; do not commit private review bundles or raw configuration dumps.

## Local review bundles

The renderer makes files only; it never contacts AWS or submits a change set. The web example below is a historical/reusable procedure reference, not a current instruction: web adoption is complete. Do not regenerate its bundle for reimport or rerun its execution. For a separately approved future review, the renderer requires a new output directory; it must not overwrite `infrastructure/work/web-review1`:

```bash
.venv-infrastructure/bin/python scripts/prepare_infrastructure_import.py web \
  --output-dir infrastructure/work/web-review1 \
  --change-set-name SVP-Web-Import-Review-1
```

It creates a private `0700` directory and `0600` files:

- `request.json`: an explicit `IMPORT` request with embedded template and mappings, no extra stack tags.
- `template.yaml` and `resources-to-import.json`: exact recorded inputs.
- `review-summary.json`: account, Region, timestamps, inventory age and artifact hashes.

It refuses an existing output directory and symlink traversal rather than overwriting prior evidence. Choose another new directory for a later review. Other accepted stack arguments are `dnssec-key` and `dns`; follow manifest order and use distinct review directories/names. A bundle is a **recorded snapshot, not fresh cloud verification or approval**. Even change-set preparation creates AWS control-plane state and requires separate authorization. Do not submit the generated request merely because rendering succeeded.

## Operating precautions

- Freeze unrelated publication while establishing and adopting the baseline. The [existing publish workflow](../.github/workflows/publish.yml) runs on **every push to `main`**, including infrastructure-only changes, and publishes with `--acl public-read`. Do not merge or publish during the freeze. No new infrastructure workflow is introduced.
- Preserve the public-ACL S3 website custom origin. The retained OAI bucket policy does not secure that endpoint. A private bucket ACL is not a change to public object ACLs. Do not introduce `BucketOwnerEnforced`, OAC, policy tightening, TLS/cache changes or an HTTPS redirect-bucket target during adoption.
- Keep all DNS records and the existing ACM certificate external. Do not create native record sets to force adoption, alter mail/validation records, change delegation/DS, or replace/export signing material. Leave disabled legacy hosting, shared IAM/OIDC, audit and unrelated resources untouched; see the inventory's scope boundaries.
- Require fresh full configuration and all-enabled-Region ownership checks before separately authorized preparation. Compare semantic service properties, tags, policies and alias targets directly; neither import validation nor `IN_SYNC` proves full equality. BucketPolicy and KMS Alias have no native drift support. A denied read remains a blocking unknown.
- Accept only the exact approved import-only resource plan: no creates, modifications, removals or replacements. Review all change-set pages and validation findings. Do not use ordinary `deploy`, `CREATE`, auto-import or delete/recreate as adoption shortcuts. No extra stack tags; metadata/tag calls can change ETags even when serving configuration is unchanged.
- Verify termination protection **before execution**. Immediately after `IMPORT_COMPLETE`, attach/read back the stack policy before normal updates. The [predecessor review](https://github.com/eamonnsullivan/eamonnsullivan.co.uk/blob/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815/docs/infrastructure/web-change-set-review.md) observed a policy-setting failure in review state; this timing is conservative operational evidence, not a universal documented AWS restriction.
- Both Retain attributes preserve physical resources in their respective cases; they **do not prevent replacement, reference changes or interruption**. Termination protection blocks stack deletion, not normal updates. Those adoption verification gates are now satisfied; normal updates still require separate planning/review and explicit human release of the freeze.

The goal is no-disruption adoption based on the [prior blog migration](https://github.com/eamonnsullivan/eamonnsullivan.co.uk/blob/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815/docs/infrastructure/adoption-completion.md), not a guarantee of zero risk. Use the runbook's explicit approval gates rather than treating predecessor success, local validation or retention as execution authority.
