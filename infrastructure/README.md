# Existing infrastructure adoption

This directory records the completed, verified **in-place CloudFormation adoption** of ten existing production resources into three stacks. 

## Artifacts

The [production manifest](environments/production.json) fixes account `995361647121`, stack order, Regions, input paths and expected physical IDs.

| Order | Proposed stack | Region | Template | Explicit import map | Resources |
| --- | --- | --- | --- | --- | --- |
| 1 | `svpsouthruislip-web` | `eu-west-1` | [web.yaml](templates/web.yaml) | [web.json](imports/web.json) | Two buckets, bucket policy, existing OAI, distribution (5) |
| 2 | `svpsouthruislip-dnssec-key` | `us-east-1` | [dnssec-key.yaml](templates/dnssec-key.yaml) | [dnssec-key.json](imports/dnssec-key.json) | Original KMS key and alias (2) |
| 3 | `svpsouthruislip-dns` | `eu-west-1` | [dns.yaml](templates/dns.yaml) | [dns.json](imports/dns.json) | Public zone, existing KSK, DNSSEC (3) |

Templates have no initial Outputs or Parameters. Every imported resource has `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain`. KSK import requires both `HostedZoneId` and `Name` in one identifier object, not a joined input key or physical ID.

## Validating

Run from the repository root using Python **3.10+** (Python 3.14 was available during preparation). First-time dependency installation requires access to the configured package source; with the existing environment installed, checks do not need AWS or network access. Do not reinstall merely to review documentation offline.

```bash
python3 -m venv .venv-infrastructure
.venv-infrastructure/bin/python -m pip install -r infrastructure/requirements.txt
PATH="$PWD/.venv-infrastructure/bin:$PATH" .venv-infrastructure/bin/python scripts/check_infrastructure.py
.venv-infrastructure/bin/python -m unittest discover -s infrastructure/tests -v
```

The checker validates manifest paths, exact retained resource/map coverage, recorded identities and policy shape, then runs installed `cfn-lint` for each template's actual Region, failing on warnings. Tests additionally check recorded template hashes and summary groupings, DNS records, preservation of legacy hosting/signing settings, and renderer safety. They are adoption-baseline checks, not a timeless prohibition on separately approved future changes. They do not compare fresh AWS properties, establish permissions, back up content or prove operational health. A site build is unnecessary for documentation-only changes.

Keep the existing root `.gitignore` entries for `/.venv-infrastructure/` and `/infrastructure/work/`; do not commit private review bundles or raw configuration dumps.

## Update a stack

Use this workflow for an existing stack:

1. **Confirm the baseline.** Use [production.json](environments/production.json)
   to identify the stack name, region, template, and parameters. In the AWS
   console, confirm live state.
2. **Edit and validate locally.** Edit the corresponding template and review the
   diff. From the repository root, run both commands in [Validate changes](#validate-changes)
   above. Resolve failures before preparing a change set. Keep the stack's
   existing parameters unless the requested change requires otherwise.
3. **Create an update change set in the console.** Open CloudFormation, select
   the stack's region, choose the existing stack, then choose **Stack actions →
   Create a change set**. For a modified local template, choose **Replace
   existing template → Upload a template file** and select the corresponding
   template. This replaces the template document, not the AWS resources. Enter
   a descriptive change-set name and purpose. Retain current parameter values.
4. **Keep stack options unchanged.** Preserve the existing service role, rollback
   configuration, stack policy, notifications, and termination protection.
   Review any capability or role requirementy. Leave other options unchanged
   unless the requested update
   requires them and their effects have been reviewed.
5. **Wait and inspect.** Submit the change set and wait for `CREATE_COMPLETE`.
   Open its **Changes** tab and inspect the full resource list and property-level
   changes. Require only changes intended by the template diff. Stop if there
   are unexpected additions, removals, or replacements. For existing resources,
   treat `Replacement: True` or `Conditional` as a stop: do not execute until
   replacement has been separately reviewed and explicitly approved. If change
   set creation fails, fix the reported issue and create a new change set.
6. **Execute the plan.** After approval of that exact plan, execute it and wait for
   `UPDATE_COMPLETE`. Verify affected settings, original resource IDs, website
   and DNS behaviour, and audit delivery where relevant. Run supported drift
   checks; compare bucket policies and KMS aliases directly. On failure, inspect
   stack events and review recovery against actual state—never delete or
   recreate resources as a shortcut.


