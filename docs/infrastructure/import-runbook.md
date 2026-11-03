# Import the existing SVP website without rebuilding it

## Status and operating boundary

**WEB DONE — do not recreate, reimport or rerun its execution.** All five original web resources reached `IMPORT_COMPLETE` on **2026-11-03 at 09:31:25.802Z** and passed identity, protection, deployed-template, full direct configuration, native drift and point-in-time public health verification. See [web completion evidence](../../infrastructure/verification/web-import-completion.json). This completes only the five-resource web batch, not the ten-resource migration.

**ALL THREE BATCHES DONE — `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`. All ten original resources are adopted and fully verified; each batch is `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`.** See [aggregate acceptance](../../infrastructure/verification/adoption-completion.json), [key completion](../../infrastructure/verification/dnssec-key-import-completion.json) and [DNS completion](../../infrastructure/verification/dns-import-completion.json). Original IDs, termination protection, installed-policy readbacks, retained templates/events, direct configuration and supported native drift checks passed. Eight supported resources are `IN_SYNC`; unsupported BucketPolicy and KMS Alias were directly checked. Final public checks matched, but native drift is not exhaustive and point-in-time health is not continuous zero-outage proof.

No import, preparation, execution, policy-install or drift gate remains. No further AWS writes are required for adoption. All AWS writes were separately approved human actions; the assistant remained read-only. The existing configuration/publication freeze remains until the human explicitly decides whether to resume publication/maintenance; normal updates must be separately planned/reviewed. Completion does not authorize commits/pushes, configuration changes or IAM supplement removal. The supplement is still present; any later removal needs separate approval and must preserve unrelated permission statements. Current follow-up is human review of completion and optional later operational decisions, not mandatory executable work.

The templates describe ten existing resources initially observed on **2026-11-02**. Local lint/tests and AWS `GetTemplateSummary`/`ValidateTemplate` passed. Preserve the earlier pause in [web review history](../../infrastructure/verification/web-change-set-review.json): fresh checks and administrator exports were reviewed on 2026-11-03, then the human separately approved the exact web execution and explicitly acknowledged immediate post-import policy timing. Termination protection was enabled before execution and remains enabled; the installed policy is verified. See also [inventory](inventory.md), [AWS support research](import-research.md), and [identifier evidence](../../infrastructure/verification/template-summaries.json).

**Stages 2–9 and the console alternative are HISTORICAL REFERENCE ONLY. Do not repeat completed create/import/execution/waiter/policy-install/drift commands, reuse change-set ARNs or regenerate private bundles. Never paste or run this whole book.** Stage 9 preserves dated approval/evidence history and final acceptance; earlier OFF, unowned, review-state and pending observations describe their timestamps, not current status.

This procedure is designed to adopt resource ownership without changing serving configuration. It is not an unconditional zero-disruption guarantee: CloudFormation does not verify property equality during import, and import can apply CloudFormation ownership/tag metadata. Every gate below matters.

**The assistant's AWS MCP remains read-only. All AWS CLI commands below are for a separately authenticated human operator. Do not grant the MCP change-set creation or execution permissions.** Permission-set changes completed earlier authorized configuration reads only, not deployment. Do not use the shared `S3Access` publishing role for this migration.

Do not paste this document into a shell or rerun its completed stages. Never substitute ordinary `create-stack`, `deploy`, an `UPDATE` change set, auto-import, or delete/recreate for explicit `IMPORT`.

## 1. Agree scope, freeze, and recovery readiness

Use account **`995361647121`** and exactly these three independent stacks, in order:

| Batch | Stack name | Region | Template | Mapping | Count |
| --- | --- | --- | --- | --- | --- |
| Web first | `svpsouthruislip-web` | `eu-west-1` | `infrastructure/templates/web.yaml` | `infrastructure/imports/web.json` | 5 |
| Signing key second | `svpsouthruislip-dnssec-key` | `us-east-1` | `infrastructure/templates/dnssec-key.yaml` | `infrastructure/imports/dnssec-key.json` | 2 |
| Zone/signing last | `svpsouthruislip-dns` | `eu-west-1` | `infrastructure/templates/dns.yaml` | `infrastructure/imports/dns.json` | 3 |

The DNS template references the original KMS ARN literally; there are no new exports, parameters, certificate requests, records, keys, distributions, or buckets. All ten definitions have `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain`. Initial templates deliberately have **no Outputs**.

Keep all eleven DNS records, ACM certificate, registration/delegation/parent DS, shared IAM/OIDC, audit stack, mail infrastructure and disabled legacy website outside adoption. Hosted-zone import does not adopt records. The DNS YAML is a read-only baseline, not a change batch.

Before proceeding:

- Agree a quiet window and one human responsible for execution, health checks, and recovery. Keep source/assets and existing configuration backups available. Do not enable versioning or change backup/key settings as part of adoption.
- Freeze console configuration edits and website publication while establishing/rechecking the baseline. **Every push to `main` runs the existing S3 publication workflow, even an infrastructure-only merge.** Do not push to `main`, merge or publish during the freeze; do not perform normal stack updates. No automatic infrastructure workflow has been added.
- Keep public object ACLs, bucket ownership/public-access settings, the HTTP S3 website origin, legacy OAI/policy, redirect protocol, TLS minimum, TTLs, and certificate unchanged. Security modernization is later, separate work.
- Confirm access to the existing account audit trail if audit evidence is required. Do not create a second trail or new logging infrastructure as an import prerequisite.
- Read the recovery section before execution. Retention is neither a backup nor a replacement-prevention mechanism. Termination protection blocks stack deletion, not updates; the supplied stack policy blocks resource replacement/removal during later updates.

**Gate:** scope/window and the short post-import stack-policy attachment gap are understood. This does not authorize execution of an as-yet-unreviewed change set.

## 2. Inspect files and prepare a local review bundle

Run from the repository root. Python 3.10+ is required; Python 3.14 was used for verification. This workspace's `.venv-infrastructure` has already been prepared: use it without recreating it with a different interpreter. On a fresh checkout, the first two commands below create/install the isolated environment; with the existing environment, run only the last two checks. Do not install packages system-wide:

```bash
python3 -m venv .venv-infrastructure
.venv-infrastructure/bin/python -m pip install -r infrastructure/requirements.txt
PATH="$PWD/.venv-infrastructure/bin:$PATH" .venv-infrastructure/bin/python scripts/check_infrastructure.py
.venv-infrastructure/bin/python -m unittest discover -s infrastructure/tests -v
```

The check rejects duplicate keys, unsafe import mappings, unsupported scope, missing retention, Outputs/Parameters, and an inadequate stack policy. Regional `cfn-lint` also runs. Bucket-local `W3045` exceptions preserve observed legacy private bucket ACLs; they are not global lint suppression.

Generate **only the web bundle first**:

```bash
.venv-infrastructure/bin/python scripts/prepare_infrastructure_import.py web --output-dir infrastructure/work/web-review1 --change-set-name svpsouthruislip-web-import-review1
```

If this exact directory was already generated, inspect it instead of rerunning the command. The renderer intentionally refuses an existing directory. A revision needs a new directory and change-set name; do not overwrite a reviewed bundle or reuse an earlier failed request/token.

Inspect all four generated files:

- `request.json`: explicit `ChangeSetType: IMPORT`, intended stack/name, complete template, five exact mappings, unique client token. No service role, stack tags, capabilities, auto-import or nested-stack setting is requested.
- `template.yaml`: byte-for-byte copy of the reviewed web template.
- `resources-to-import.json`: byte-for-byte copy of the mapping.
- `review-summary.json`: account/Region, inventory timestamp/age, and SHA256 hashes of those three artifacts.

The bundle is local only: directory mode `0700`, files `0600`; `infrastructure/work/` is ignored by Git. Hashes bind files to review; they do not prove AWS is unchanged, that you have the correct operator session, or that execution is approved. Treat configuration/event output as private and review before publishing it.

## 3. Fresh read-only preflight and operator identity

Ask the assistant to recheck live configuration and ownership immediately before preparation. Repeat before every batch and again before execution if anything changed or the review was delayed. The initial inventory is not a perpetual authorization.

Preflight must confirm:

1. Account and every original ID match [`production.json`](../../infrastructure/environments/production.json). Search all enabled Regions for existing stack ownership, including global CloudFront/Route 53 resources. The chosen new stack must not already own anything. A leftover review/failed stack needs diagnosis, not a new arbitrary name.
2. Full bucket configuration/policy/ACL, distribution configuration/tags, OAI comment, certificate association, KMS metadata/policy/alias target, zone/records and signing state still match. Distinguish expected `NoSuch…` configuration absence from `AccessDenied` or an unread response. Unknown means stop.
3. All DNS records match the read-only baseline; parent DS and delegation match; KMS key is enabled and KSK active. Check the blog remains healthy too.
4. Template hashes and identifier evidence match the exact bundle. Refresh `GetTemplateSummary` after any template change; never silently update evidence hashes without repeating AWS verification. Do not edit generated `request.json` after approval.

In your **existing human administrator CLI profile**, authenticate and verify identity. Replace the placeholder profile name; do not share credential material:

```bash
export AWS_PROFILE=your-existing-human-administrator-profile
aws sso login --profile "$AWS_PROFILE"
aws sts get-caller-identity --profile "$AWS_PROFILE" --no-cli-pager
```

Use your established authentication instead of `sso login` if the profile is not SSO-based. `Account` must be `995361647121`; verify the `Arn` is the intended human administrator role. Do not change the MCP profile. Stop on a different account or unexpected role.

For the first batch, set these non-secret shell variables:

```bash
REGION=eu-west-1
STACK=svpsouthruislip-web
REVIEW_DIR=infrastructure/work/web-review1
```

Verify the exact copied template through AWS and save private evidence:

```bash
aws cloudformation get-template-summary --template-body "file://$REVIEW_DIR/template.yaml" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/template-summary.json"
aws cloudformation validate-template --template-body "file://$REVIEW_DIR/template.yaml" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/template-validation.json"
```

Review every returned logical ID and identifier field against the mapping. KSK's later summary reports `HostedZoneId,Name`: its mapping needs **separate `HostedZoneId` and `Name` keys**, not one comma-containing key. Template validation is not proof of property equality, exclusive ownership or import permission sufficiency.

**STOP:** resolve all preflight mismatches/denies before creating a change set. Do not broaden permissions or change production to make a template match.

## 4. Human authorization: create the web IMPORT change set only

This is the first CloudFormation control-plane write. It creates review state; it must not yet adopt resources or change their serving settings. Obtain approval for **preparation only**.

```bash
aws cloudformation create-change-set --cli-input-json "file://$REVIEW_DIR/request.json" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/create-change-set.json"
```

If this fails, stop. Preserve the request/error; inspect whether a review stack/change set exists. Do not retry as `CREATE`, change resource names, delete resources, add Outputs, or execute any other change set.

On success, share the returned **change-set ARN (`Id`) and `StackId`** with the assistant. These are identifiers, not credentials. Copy them into `CHANGE_SET_ARN` and `STACK_ARN` in your shell only after checking account, Region and stack. Do not guess or select the most recent unrelated change set.

**STOP HERE. Do not execute.** The assistant can inspect through read-only MCP; if any required inspection read is denied, arrange a separate scoped read-only fix or provide privately collected evidence. Successful creation is not review approval.

## 5. Review the entire prepared plan and validation events

The reviewer should use the exact returned ARN, not a mutable name alone. These optional human inspection commands produce the same evidence for review:

```bash
aws cloudformation wait change-set-create-complete --stack-name "$STACK_ARN" --change-set-name "$CHANGE_SET_ARN" --region "$REGION" --profile "$AWS_PROFILE"
aws cloudformation describe-change-set --stack-name "$STACK_ARN" --change-set-name "$CHANGE_SET_ARN" --include-property-values --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/change-set.json"
aws cloudformation get-template --stack-name "$STACK_ARN" --change-set-name "$CHANGE_SET_ARN" --template-stage Original --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/prepared-template.json"
aws cloudformation describe-events --stack-name "$STACK_ARN" --change-set-name "$CHANGE_SET_ARN" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/validation-events.json"
```

Use a current AWS CLI that supports `describe-events`; its option is `--change-set-name`. If your installed model lacks this operation/option, stop and update the tooling or use the supported MCP/API. Do not omit validation review. Do not use `--no-paginate`, `--max-items`, or a query/filter that hides findings. Read every API page; an outstanding `NextToken`/marker is a review gap. Include successful and warning events, not just failed events.

Acceptance checklist:

- Change-set status **`CREATE_COMPLETE`**, execution status **`AVAILABLE`**, intended account/Region/stack/name/ARN. The submitted request is `IMPORT`; some description responses do not echo that request field.
- Exactly five resource changes for web, all **`Action: Import`**, with these types/physical IDs. No missing/duplicate/unexpected logical IDs:

  | Logical ID | Type suffix | Physical ID |
  | --- | --- | --- |
  | `SiteBucket` | `S3::Bucket` | `svpsouthruislip.org.uk` |
  | `RedirectBucket` | `S3::Bucket` | `www.svpsouthruislip.org.uk` |
  | `SiteBucketPolicy` | `S3::BucketPolicy` | `svpsouthruislip.org.uk` |
  | `LegacyOriginAccessIdentity` | `CloudFront::CloudFrontOriginAccessIdentity` | `E1H05UTZYYPBPP` |
  | `SiteDistribution` | `CloudFront::Distribution` | `E2ZXKXV2U7OYGL` |

- **No `Add`, `Modify`, `Remove`, replacement (`True` or `Conditional`), drift reversion, nested stacks or auto-import.** Reject unexpected deployment modes, capabilities, service roles, parameters or stack tags. No new management tags were requested; service ownership metadata may still be applied during import.
- Prepared `TemplateBody` matches the reviewed YAML semantically, with both Retain attributes and no Outputs. Confirm the create response/request/description all refer to the same artifact and ARN.
- Review `DescribeEvents` validation/operation events: no unresolved warnings/errors, `VALIDATION_ERROR`, failed `ValidationStatus`, or unexplained `ValidationFailureMode`, `ValidationStatusReason` or `ValidationPath`. A WARN-mode check can allow change-set creation despite a failed validation. Empty findings are not comprehensive proof of safety.
- New stack remains **`REVIEW_IN_PROGRESS`**, with no adopted resources yet. Do not read an empty resource list as successful import.
- Refresh the live serving/signing/configuration baseline if the review was delayed. Standard AWS text asking you to verify template/live equality is a reminder, not proof AWS performed that comparison.

**Gate:** reviewer records the exact request/template hashes, change-set/stack ARNs, all import actions, validation findings and remaining limitations. This still does not authorize execution.

## 6. Enable termination protection; agree policy timing

Before execution, have the human administrator enable termination protection on the new review stack:

```bash
aws cloudformation update-termination-protection --enable-termination-protection --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --no-cli-pager
aws cloudformation describe-stacks --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager
```

Verify `EnableTerminationProtection: true`, `REVIEW_IN_PROGRESS`, and unchanged available import plan. Console alternative: select the intended stack → **Stack actions → Edit termination protection → Enable → Save**.

The predecessor attempted `SetStackPolicy` during `REVIEW_IN_PROGRESS` and AWS rejected it. Do not work around this with a normal update or dummy resource. The agreed sequence is:

1. Retain policies in the reviewed import template and termination protection **before execution**.
2. Separately authorized execution of the exact import change-set ARN.
3. Wait for `IMPORT_COMPLETE`.
4. **Immediately attach/read back the supplied stack policy before any normal update.**

Acknowledge this timing explicitly. If post-import policy attachment fails, stop all further updates/import batches until diagnosed. Do not disable protection to make progress.

## 7. Separate human approval: execute exactly one reviewed change set

**This changes CloudFormation ownership. Execute only after the reviewer and human operator approve this exact ARN, plan and protection state. Do not infer approval from “continue,” earlier access-policy work, or successful change-set creation.**

Re-describe the exact change set and stack immediately before execution. If plan, live configuration, identity, availability or protections changed, return to review. The human operator then runs:

```bash
aws cloudformation execute-change-set --change-set-name "$CHANGE_SET_ARN" --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --no-cli-pager
aws cloudformation wait stack-import-complete --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE"
```

Do not disable rollback or run multiple batches together. Monitor stack events and public health. A waiter timeout is not permission to execute again or delete anything; inspect the actual status/events.

Only after **`IMPORT_COMPLETE`**, apply and read back the reviewed protection policy:

```bash
aws cloudformation set-stack-policy --stack-name "$STACK_ARN" --stack-policy-body file://infrastructure/stack-policy.json --region "$REGION" --profile "$AWS_PROFILE"
aws cloudformation get-stack-policy --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager > "$REVIEW_DIR/installed-stack-policy.json"
```

The installed document must semantically equal `infrastructure/stack-policy.json`: allow updates, explicitly deny `Update:Replace` and `Update:Delete` for every resource/principal. No normal stack update is allowed in the gap before this is verified.

## 8. Verify identity, configuration, drift and health

Before proceeding to another batch:

- Confirm `IMPORT_COMPLETE`, termination protection still enabled, exact stack policy installed, and the original physical IDs in `ListStackResources`/`DescribeStackResources`. Compare against the manifest; resource names staying similar is not enough.
- Read the deployed original template and compare with the approved artifact, including retention. Preserve import events/request hashes privately. Expected service-owned metadata/tag events are not automatically a serving-configuration change; compare actual configuration rather than ETag or event keywords alone.
- Re-read all directly relevant service settings/policies/tags. For web, verify both buckets, policy, OAI, full distribution configuration, existing certificate/validation and publisher compatibility. Do not publish a test deployment or invalidate caches to test import.
- For the key batch, verify the **original key ID/ARN**, enabled state, spec/usage/origin, exact policy and alias target; never export, rotate, replace or re-create signing material. For DNS, verify the same hosted zone, nameservers, records, KSK/key linkage/public key/DS and continuous `SIGNING`/`ACTIVE` state.
- Have the human run supported native drift detection after import. `DetectStackDrift` schedules a metadata operation; it is a separately authorized human action, not a read-only MCP action. Poll its detection status to completion, then review all resource drift details. Require no unexplained drift before proceeding.

Example drift initiation (copy its returned detection ID for the next command):

```bash
aws cloudformation detect-stack-drift --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --no-cli-pager
```

Then inspect using the returned ID:

```bash
aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id "$DRIFT_DETECTION_ID" --region "$REGION" --profile "$AWS_PROFILE" --no-cli-pager
aws cloudformation describe-stack-resource-drifts --stack-name "$STACK_ARN" --region "$REGION" --profile "$AWS_PROFILE" --output json --no-cli-pager
```

Drift covers only supported, explicitly modeled properties. Bucket policies and KMS aliases lack native drift support: compare them directly. `NOT_CHECKED` is not `IN_SYNC`; an overall `IN_SYNC` is not an exhaustive health/configuration check.

Repeat public DNS/HTTP checks without altering resources:

| URL/check | Baseline |
| --- | --- |
| `http://svpsouthruislip.org.uk/` | 301 to the HTTPS apex; do not follow redirects when checking this status |
| `https://svpsouthruislip.org.uk/` | 200 |
| `https://www.svpsouthruislip.org.uk/` | 200; no server-side www redirect |
| `https://svpsouthruislip.org.uk/foodbank/` | 200 |
| `https://svpsouthruislip.org.uk/feed.xml` | 200 |
| `https://svpsouthruislip.org.uk/posts-output/2020-03-21-foodbank-changes/` | 200 HTML alias, not HTTP 301 |
| `https://svpsouthruislip.org.uk/__svp-import-nonexistent-check__` | 403; do not incidentally convert error behavior |
| `https://eamonnsullivan.co.uk/` | 200, unchanged other-site health |
| Public NS/delegation | Same four nameservers as `infrastructure/dns/records.yaml` |
| Parent DS | `3666 13 2 749A1CBE44DB67CB2955ADF5D3AA274EF2D8C47CC88E0DFBC97032A5D60FD4AB` |

Compare all eleven records, including mail, NS/SOA and certificate validation, without pruning or reapplying the baseline. Registrar contact/renewal administration remains outside this work. Record the approved batch outcome before continuing.

## 9. Repeat the entire gated procedure for key, then DNS

**Final acceptance: all ten original resources are adopted and fully verified; `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`.** Web, key and DNS batches are `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`; see [aggregate completion](../../infrastructure/verification/adoption-completion.json). There is no next import or drift gate and no further AWS write required for adoption. Do not repeat completed operations. Human review of completion and any explicit later decision about resuming publication/maintenance or removing only the read-supplement additions are separate from adoption acceptance; the freeze remains in force.

The following 2026-11-03 history preserves separate approvals, pause/review evidence and limitations. Earlier unowned/OFF/pending states are historical snapshots, superseded by final acceptance. The human separately approved key preparation, protection and exact-ARN execution; see [key preflight/approval history](../../infrastructure/verification/dnssec-key-preflight.json) and [key plan review](../../infrastructure/verification/dnssec-key-change-set-review.json). After “Pause here”, “resume” and fresh checks, the human separately selected “Approve key preparation only” before creation at 11:03:41.020 UTC; main/independent full review passed at 11:16:05 UTC. Protection was off at the 11:16 historical checkpoint, then separately approved (“Approve protection only”) at `2026-11-03T11:26:58.153170Z` and verified true at 11:31 UTC before execution. These are historical facts, not current instructions or ownership status.

The following completed collection is **historical/reference, not an instruction to repeat exports**. Leave all three private files unchanged. The main agent read each in full and objectively verified them at `2026-11-03T11:40:30.127784Z`:

- `pre-execution-identity.json` (`GetCallerIdentity`): expected account `995361647121`, role `AWSReservedSSO_AdministratorAccess_cb7450173a83f9aa`, session `eamonn`.
- `pre-execution-change-set.json` (`DescribeChangeSet --include-property-values`): entire fresh plan semantically equals the earlier full review, including the same exact ARNs, two original-resource Import actions, all options and AfterContexts; `CREATE_COMPLETE`/`AVAILABLE`.
- `pre-execution-stack.json` (`DescribeStacks`): exactly matches the protected review, `REVIEW_IN_PROGRESS`, protection true, no tags, service role or parameters, and rollback not disabled. Reviewed bundle/template/policy hashes are unchanged.

Independent read-only MCP at `2026-11-03T11:41:04.245739Z–11:41:12.301185Z` checked all 17 enabled Regions and six active stacks/resources without denials or pagination gaps. The original key/alias remain unowned without ownership conflict; the exact key review has zero resources, protection true and the same available change set. Key metadata/policy/tags, aliases/dates, all three zones' KSK dependencies, this site's eleven records and zone NS remain unchanged, with `SIGNING`/`ACTIVE`. Web remains `IMPORT_COMPLETE`, protection true, original five IDs and no pending changes. Public HEAD/`dig` checks at `2026-11-03T11:41:00.416150Z–11:41:01.223959Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. These are point-in-time checks, not continuous monitoring; this refresh was not a full web-service audit.

Validation alone was not execution approval. The human subsequently selected **“Approve key import and immediate policy”**, recorded at `2026-11-03T11:47:14.168775Z`, satisfying stage 7's separate approval gate **only for the exact existing two-resource key Import change set and stack ARNs above**. The human acknowledged the security risk and short policy gap, continuing publication/configuration freeze and existing backups/recovery-access readiness. The human subsequently performed that exact Import and supplied receipts; the installed key stack policy is now read back and verified. The assistant performs no AWS writes.

The following human execution sequence is **historical/reference only**, not the current step. Do not repeat execution, the waiter or policy installation:

1. Immediately re-read the expected human identity, full exact-ARN plan (including property values) and protected review stack; stop on any mismatch, unavailable plan or changed condition. Preserve existing private exports unchanged.
2. Hash-guard the reviewed `infrastructure/stack-policy.json` before execution.
3. Human executes **only** `arn:aws:cloudformation:us-east-1:995361647121:changeSet/svpsouthruislip-dnssec-key-import-review1/dff31c49-152e-41d5-9aa6-2c5e3a9de62d` for stack `arn:aws:cloudformation:us-east-1:995361647121:stack/svpsouthruislip-dnssec-key/3a4af620-d776-11f1-b694-0e765133f371`, then waits for `IMPORT_COMPLETE`.
4. Immediately after successful completion, recheck the reviewed policy hash, install that policy and read it back. No normal update is allowed in this short policy gap.
5. Stop for mandatory identity, protection, policy, template, direct configuration and health verification before any DNS batch can be considered.

On execution, waiter or policy failure, **STOP and inspect actual state**. Never retry execution, delete/recreate resources or disable DNSSEC to make progress. Approval does not authorize DNS-batch actions, normal updates or publication. Keep the freeze; delayed or changed conditions require refreshed checks and renewed review.

### Key import completion and verification (2026-11-03)

The [key completion evidence](../../infrastructure/verification/dnssec-key-import-completion.json) records `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`, and binds all 25 private artifact hashes. This accepts the two-resource key batch, not completion of the ten-resource migration.

The main agent and independent security reviewer read all 13 events: one historical review event and 12 execution events. Operation `99125cc8-e2ef-45d5-9aac-55f203fcd842` ran from `11:56:23.535Z` to stack `IMPORT_COMPLETE` at `11:57:30.436Z`. Both original physical IDs completed import, with no failures, rollback, resource creates/deletes or replacements. Tag UPDATE events were part of import; alias tagging was `SKIPPED` to avoid replacement, not an actual replacement. Actual KMS key tags remain `[]`.

The installed stack-policy readback equals the reviewed policy byte-for-byte and semantically, SHA-256 `d20d0e9d6091176ca4eca646d40fcf851996a1382341a05d9fb554b0f6aee5ff`. The deployed Original template is 1,885 bytes, byte-identical with SHA-256 `4a30bf614da037aa9a0dc4a6a737147177c30ecaf266de41e9dfd2b1ae68ebaa`, both Retain attributes and no Outputs. Policy readback file mtime `11:57:58.268096Z` is not the policy API installation time or proof of the exact gap; the immediate sequence was human-approved, and readback is verified without claiming a measured attachment interval.

Fresh read-only MCP at `2026-11-03T12:01:02.107113Z–12:01:10.212110Z` checked all 17 enabled Regions and six active stacks/resources without denials or unconsumed pagination. The exact key stack is `IMPORT_COMPLETE`, protection true, with the approved executed ChangeSetId, both original IDs now owned only by that stack and no pending key change sets. Original key metadata, enabled state, spec/usage/origin, policy, dates and empty tags are unchanged; alias target and creation/update dates are unchanged. All three zones' KSK dependencies, site eleven records, zone NS, public key and DS remain unchanged with `SIGNING`/`ACTIVE`. Web remains `IMPORT_COMPLETE`, protection true and original five IDs unchanged; no new drift detection or full web-service audit was performed.

Public HEAD/`dig` checks at `2026-11-03T12:02:06.212438Z–12:02:06.970567Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. These checks are point-in-time, not continuous monitoring.

The human separately selected **“Approve key drift check only”** at `2026-11-03T12:10:48.153276Z`, then scheduled one detection, `e98b3970-d77f-11f1-86e4-12ffd5f8a705`. Both full human exports were verified at `2026-11-03T12:19:44.279781Z`, mode `0600`, with no unconsumed pagination. Exact-stack/detection status is `DETECTION_COMPLETE`, `IN_SYNC`, `DriftedStackResourceCount=0`, timestamp `12:13:00.423Z`. Resource detail contains exactly the original `DnssecKey` (`AWS::KMS::Key`, `944105a2-c852-4c4f-a0f2-a0f1b91344c9`), `IN_SYNC`, `PropertyDifferences=[]`, timestamp `12:13:01.077Z`; expected JSON equals actual JSON and every modeled key-template property, including policy. Receipt hashes remain in the completion evidence rather than duplicated here.

Final direct reads at `2026-11-03T12:20:13.340870Z–12:20:16.036369Z` confirm the unsupported alias's original target/dates, no additional alias, unchanged key metadata/policy/enabled state/spec/usage/origin/single-Region/empty tags, stack protection/executed change set/original IDs and no pending changes. All three zones' KSK dependencies, site eleven records, signing/public key/DS remain unchanged, `SIGNING`/`ACTIVE`, with no denials or pagination gaps. Final public HEAD/`dig` checks at `12:20:35.511686–12:20:36.184618Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. Native `IN_SYNC` is not exhaustive; direct checks supply unsupported alias coverage. These are point-in-time checks, not continuous monitoring or a new full web-service audit.

**The human selected “Approve DNS protection only” at `2026-11-03T13:35:23.046154Z`. Human protection receipts are now verified, stage 6 complete. Fresh pre-execution exports are fully validated. The human selected “Approve DNS import and immediate policy” at `2026-11-03T14:02:02.810949Z`, after presentation of the exact ARN/three original resources, policy gap, metadata effects and no-zero-outage-guarantee caveat. This confirms the short gap is understood, publication/configuration freeze continues and existing backups/recovery access are ready. The human performed that exact Import; installed DNS policy readback and subsequent full drift/final checks are now verified. DNS acceptance is complete; the following timestamps retain historical preparation/review observations.** The human selected **“Approve DNS preparation only”** at `2026-11-03T12:40:40.189234Z`, after review of exactly three original resources, account `995361647121`, Region `eu-west-1`, review-state-only scope and identity/freeze conditions. Approval binds request SHA-256 `ba9e6736a1fb51c05a2f3292c951144886f6ddab0e2421642193774f5063caaa`; see [DNS preflight/approval evidence](../../infrastructure/verification/dns-preflight.json). Status is `IMPORT_COMPLETE_VERIFIED`. Main-agent review of `infrastructure/work/dns-review1/operator-identity.json` at `2026-11-03T12:47:09.954520Z` confirmed the expected administrator account/role/session. The human then created review state at `2026-11-03T12:56:17.345Z`; the actual private create response was mode/hash verified at `12:57:49.465839Z`, with reviewed bundle hashes unchanged. Fresh MCP at `12:57:19.669962–12:57:23.998376Z` confirmed `CREATE_COMPLETE`/`AVAILABLE`, no nested stacks, stack `REVIEW_IN_PROGRESS`, zero resources, termination protection false, no tags/parameters/service role, `STANDARD` mode and rollback enabled. Original zone/nameservers/eleven records, KSK/key linkage/public key/DS/dates, key configuration and all three zones' KSK dependencies match, `SIGNING`/`ACTIVE`, without denied reads or pagination gaps. Full review of all three private exports passed at `2026-11-03T13:15:10.033325Z`, including independent security review; see [DNS review evidence](../../infrastructure/verification/dns-change-set-review.json). Fresh MCP at `13:15:21.023210–13:15:24.788607Z` confirmed the same `CREATE_COMPLETE`/`AVAILABLE` plan, `REVIEW_IN_PROGRESS`, zero resources, protection false and unchanged zone/records/signing/key dependencies without denials or pagination gaps. No public checks were repeated at the 13:15 review checkpoint. Main fully read the mode-`0600` protection receipts (update/readback mtimes `13:41:33.667906Z`/`13:41:34.313215Z`) and verified them at `2026-11-03T13:43:16.994631Z`. Fresh independent MCP at `13:42:48.198015–13:42:59.728957Z` checked all 17 enabled Regions and all seven active stacks/resources: exact DNS review `REVIEW_IN_PROGRESS`, protection true, zero adopted resources, no tags/parameters/service role or disabled rollback, same `CREATE_COMPLETE`/`AVAILABLE` change set; original DNS resources remain unowned without conflict. Zone/nameservers/eleven records, KSK/key linkage/public key/DS/dates, all three zones' KSK dependencies and key metadata/policy/alias/empty tags are unchanged, `SIGNING`/`ACTIVE`, without denials or pagination gaps. Web/key retain completion/protection/original seven IDs, no pending change sets and prior `IN_SYNC`; no new drift detection or installed-policy readback was performed. Public HEAD/`dig` at `13:43:16.162454–13:43:16.994631Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. These checks are point-in-time, not continuous monitoring or a new full web-service audit. All three fresh human pre-execution exports were fully read and objectively verified at `2026-11-03T13:52:59.917932Z`: expected administrator identity, whole three-Import plan/options/contexts semantically equal to the full review, `CREATE_COMPLETE`/`AVAILABLE`, and whole stack equal to protected review, `REVIEW_IN_PROGRESS`/protection true/no tags, parameters or role/rollback enabled. Reviewed bundle/template/policy hashes are unchanged. Fresh MCP at `13:53:03.484951–13:53:14.944590Z` rechecked all 17 enabled Regions/seven active stacks/resources, unchanged protected zero-resource DNS review, original DNS/signing/key configuration and unowned targets without conflict, denials or pagination gaps. Web/key retain completion/protection/original seven IDs, no pending change sets and prior `IN_SYNC`; installed policies were not reread and no drift detection initiated. Public checks at `13:53:36.551407–13:53:37.028596Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. These are point-in-time checks, not continuous monitoring or a new full web-service audit. Validation alone was not approval; the human's subsequent explicit approval now authorizes only this exact three-resource Import and immediate policy sequence. That approved sequence is now complete; DNS policy readback matches the reviewed policy. The single separately approved metadata-only drift detection and detailed export review are complete; no normal update or publication authority follows. The local bundle is not an AWS change set. Do not repeat completed web/key execution, policy-install or drift steps, retry known denied deep MCP reads, expand access or repair drift automatically. Keep records, signing, certificate, registrar and shared IAM unchanged. Those separate DNS preparation/review/protection/execution/verification gates are now complete; normal updates and publication stay frozen pending an explicit human decision.

The following command records how the local bundle was generated. **Do not rerun it into the existing directory.** On a fresh checkout without that private directory, generate a new bundle only after fresh preflight and review its new hashes/token:

```bash
.venv-infrastructure/bin/python scripts/prepare_infrastructure_import.py dnssec-key --output-dir infrastructure/work/dnssec-key-review1 --change-set-name svpsouthruislip-dnssec-key-import-review1
```

Historical key review/verification used `REGION=us-east-1`, `STACK=svpsouthruislip-dnssec-key`, `REVIEW_DIR=infrastructure/work/dnssec-key-review1` and the same exact returned stack ARN above; do not prepare another key change set. Completed preparation/protection/pre-execution/export/import/waiter/policy-install steps are historical reference, not permission to repeat them. The two original imported resources are:

- `DnssecKey` → `944105a2-c852-4c4f-a0f2-a0f1b91344c9` (`AWS::KMS::Key`).
- `DnssecKeyAlias` → `alias/svpsouthruislipkey` (`AWS::KMS::Alias`).

### DNS completion and final acceptance (2026-11-03)

Use stack ARN `arn:aws:cloudformation:eu-west-1:995361647121:stack/svpsouthruislip-dns/f56141d0-d785-11f1-bd48-0affd18eb563` and change-set ARN `arn:aws:cloudformation:eu-west-1:995361647121:changeSet/svpsouthruislip-dns-import-review1/e6ec8301-f991-40b3-a8e7-8222221cd267`. Using those same exact ARNs, `eu-west-1` and the same human administrator profile, the following private files in `infrastructure/work/dns-review1/` were collected and fully validated. This list is historical reference, not an instruction to repeat or overwrite:

- `pre-execution-identity.json`: fresh `GetCallerIdentity`.
- `pre-execution-change-set.json`: complete `DescribeChangeSet --include-property-values`, all pages without filters/truncation.
- `pre-execution-stack.json`: fresh `DescribeStacks`, including protection.

**DNS status: `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`.** See [DNS import checkpoint](../../infrastructure/verification/dns-import-completion.json). All eight human receipts passed main byte/hash/stat validation and independent security review. All 17 events (one historical, 16 execution) were read: operation `b6c1439f-bf36-4fbe-9f14-5bb04897d2f9` ran `2026-11-03T14:13:00.637Z–14:13:33.672Z`; all three original IDs reached `IMPORT_COMPLETE`, with no failure, rollback, resource create/delete or replacement. Import-tag UPDATE events are metadata; KSK/DNSSEC tagging was skipped to avoid replacement, not an actual replacement. DNSSEC's absent `UPDATE_IN_PROGRESS` is not contradictory; actual zone tags remain `[]`.

Installed policy decoded bytes and semantics match reviewed SHA-256 `d20d0e9d6091176ca4eca646d40fcf851996a1382341a05d9fb554b0f6aee5ff`. Readback mtime `14:14:03.290142Z` is not exact policy API installation time or proof of the gap. Deployed Original template is 1,059 bytes, byte-identical SHA-256 `3587af1b6aa1cb5cdef74da7abcdf079d99e00982de5c452c3774057eabf5f2b`, both Retain attributes, no Outputs/Parameters, same KMS literal/KSK dependency.

Full AWS reads at `2026-11-03T14:18:49.536381Z–14:19:07.690553Z` covered all 17 Regions/seven stacks/resources: all three SVP stacks `IMPORT_COMPLETE`, protection true, ten original IDs/executed change sets, no pending changes or ownership conflicts. Main objectively compared responses with templates/baselines at `14:21:23.266708Z`: DNS/signing/all three zones' KSK dependencies/KMS policy+metadata+tags/alias and full S3/CloudFront/OAI/ACM hosting configuration match. Of 90 calls, 78 succeeded and 12 returned expected optional `NoSuch…` absences; no denials or pagination gaps. Web/key installed policies were not reread; DNS human installed-policy readback is verified. Public checks at `14:21:23.241920–14:21:23.884753Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. These checks are point-in-time, not continuous monitoring.

**The human selected “Approve DNS drift check only” at `2026-11-03T14:37:20.670673Z` and initiated ONE detection.** Actual `detect-stack-drift.json` returned `285d2d10-d795-11f1-90eb-02ffea08c925`; mode `0600`, mtime `2026-11-03T14:45:05.249922Z`, receipt/hash verified at `14:46:20.287310Z`. Fresh MCP at `14:45:59.367441–14:46:03.229259Z` confirmed exact stack `IMPORT_COMPLETE`, protection true, three original IDs/executed change set/no pending changes and stack/all three DNS resource drift metadata `IN_SYNC`, LastCheck `14:45:05.546Z`. Original zone/records/signing/key dependencies remain unchanged, `SIGNING`/`ACTIVE`, without denials or pagination gaps. At that 14:46 checkpoint, only metadata was available. Both full mode-`0600` exports were subsequently read and objectively verified at `2026-11-03T14:54:03.563240Z`: exact stack/detection `285d2d10-d795-11f1-90eb-02ffea08c925`, `DETECTION_COMPLETE`, `IN_SYNC`, `DriftedStackResourceCount=0`, timestamp `14:45:05.249Z`, no pagination gaps. Exactly the three original types/physical IDs are `IN_SYNC`, all `PropertyDifferences=[]`, and all expected/actual JSON equals the complete resolved modeled DNS properties: zone name/comment, KSK zone/name/ACTIVE/original KMS ARN, and DNSSEC zone. Receipt hashes and per-resource timestamps are bound in [DNS completion evidence](../../infrastructure/verification/dns-import-completion.json).

Final AWS reads at `2026-11-03T14:54:33.447857Z–14:54:42.295237Z` checked all 17 enabled Regions/seven stacks/resources: all three site stacks `IMPORT_COMPLETE`, protection true, all ten original IDs/executed change sets, no pending changes/conflicts and DNS's three resources `IN_SYNC`. Original zone/empty tags/four nameservers/eleven records/KSK dates, key linkage/public key/DS, all three zones' KSK dependencies and KMS metadata/policy/alias/empty tags match, `SIGNING`/`ACTIVE`, without denials or pagination gaps. This refresh did not repeat the earlier full 90-call hosting audit or installed-policy APIs; previous verified readbacks remain evidence. Final public checks at `14:55:07.826326–14:55:08.894265Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. Point-in-time results do not prove continuous zero outage; native `IN_SYNC` remains non-exhaustive.

**All ten resources are now fully verified; no further adoption operation or evidence gate remains.** Eight supported resources are `IN_SYNC`; unsupported BucketPolicy/KMS Alias were directly checked. Do not schedule again, repeat create/import/waiter/policy installs, remediate, expand privileges or retry known denied deep MCP reads. Publication/configuration freeze remains until an explicit human decision; normal updates require separate planning/review. The read supplement is still present, not removed; any later removal needs separate approval and additions-only changes preserving unrelated statements. The eleven records, certificate, delegation/DS, registrar and shared IAM remain external and untouched. The following completed original review exports are historical reference, not instructions to repeat or overwrite:

- `change-set.json`: complete `DescribeChangeSet --include-property-values` for both exact ARNs.
- `prepared-template.json`: `GetTemplate` with stage `Original` for both exact ARNs.
- `validation-events.json`: complete `DescribeEvents` for both exact ARNs.

Review accepted exactly three original-resource Imports and the complete 1,059-byte template, byte-identical to request/bundle/source (SHA-256 `3587af1b6aa1cb5cdef74da7abcdf079d99e00982de5c452c3774057eabf5f2b`), with both Retain attributes, no Outputs/Parameters/tags/service role/auto-import/nesting/record sets/new keys/replacements. KSK dependency and literal original KMS ARN are preserved. AfterContext `HostedZoneId` marked `KNOWN_AFTER_APPLY` resolves through Ref to the explicitly pinned original zone; it is not live-property equality proof. Both exact-operation `CREATE_CHANGESET` events (`IN_PROGRESS`/`SUCCEEDED`) returned no validation findings or pagination gaps, not exhaustive safety proof. Keep private evidence unchanged. Do not rerun creation, use ordinary deploy, delete/recreate resources or alter DNS/signing. Protection enablement/readback is complete and verified; the exact-ARN human execution and policy sequence are now complete, not to be repeated. The following preflight/generation details are historical checkpoints, not current creation instructions.

Read-only AWS preflight at `2026-11-03T12:32:15.775829Z–12:32:24.848693Z` confirmed the correct ViewOnly account `995361647121`, all 17 enabled Regions/six active stacks/resources, web/key completion/protection/original IDs and prior `IN_SYNC`, with no pending change sets. At that preflight checkpoint, the three DNS targets below were unowned and no intended `svpsouthruislip-dns` stack existed; the later review stack owned zero resources before the separately approved import; it now owns the three original resources. Zone metadata, no tags/VPC associations, four nameservers, eleven records, original KSK dates/public key/DS/key ARN and all three zones' signing dependencies match; site signing is `SIGNING`/`ACTIVE`, key/policy/alias unchanged. The exact 1,059-byte DNS template passed `GetTemplateSummary`/`ValidateTemplate` in `eu-west-1`; KSK mapping uses separate `HostedZoneId` and `Name` fields, not a joined input.

Public checks at `12:32:59.892950–12:33:00.366864Z` matched all eight statuses, redirect, root-object ETag, public NS, authoritative parent DS/delegation and KSK. Full hosting reads at `12:33:02.008728–12:33:12.170279Z` matched both buckets' configuration/ACL/encryption/public blocks/optional absences and expected existing CloudFormation tags, full CloudFront configuration/tags, OAI and ACM validation; bucket/KMS policies were checked in the first window. Only known optional `NoSuch…` absences occurred, with no denials or pagination gaps. These are point-in-time checks. Independent local DNS review passed: exact manifest/template/map, both Retain attributes, no Outputs/Parameters/record sets, KSK dependency and literal original KMS ARN preserved.

The local-only `infrastructure/work/dns-review1/` bundle was generated at `2026-11-03T12:34:09.241048Z` for change-set name `svpsouthruislip-dns-import-review1`; hashes are bound in the DNS checkpoint. Directory `0700`, files `0600`, Git-ignored; local rendering itself created no AWS review state. **Do not regenerate or overwrite it or repeat the later completed human creation. Maintain the freeze.** The following renderer command is historical generation reference, not a current instruction:

```bash
.venv-infrastructure/bin/python scripts/prepare_infrastructure_import.py dns --output-dir infrastructure/work/dns-review1 --change-set-name svpsouthruislip-dns-import-review1
```

The intended DNS context is `REGION=eu-west-1`, `STACK=svpsouthruislip-dns`, `REVIEW_DIR=infrastructure/work/dns-review1`. Preparation, identity/full-plan review, protection, exact-ARN human import and installed-policy readback are complete. Native drift and final verification are complete; no create/execute/waiter/policy-install/drift rerun or broader update authority is granted. The three original imported resources are:

- `SiteHostedZone` → `Z3SM1DWWC45TX` (`AWS::Route53::HostedZone`).
- `SiteKeySigningKey` → `Z3SM1DWWC45TX|svpsouthruislip` (`AWS::Route53::KeySigningKey`; mapping uses the two separate fields).
- `SiteDnssec` → `Z3SM1DWWC45TX` (`AWS::Route53::DNSSEC`).

**Clear the previous batch's `CHANGE_SET_ARN` and `STACK_ARN` before copying new values.** Region/stack variables alone do not select a new change set safely. Never execute a stale ARN from another batch.

All three batches are verified/protected and completion/original-ID evidence is recorded. The verification condition is met, but ending the configuration/publication freeze still requires an explicit human decision; normal updates must be separately planned/reviewed. Do not rename logical IDs, remove Retain attributes or bypass stack policies casually. Keep external records/certificate ownership explicit. The supplement remains present; [later access removal](inventory-access.md) requires separate human approval, removing only its additions while preserving unrelated permission changes. No IAM work is authorized now.

## Failure and recovery: do not improvise

- **Before execution:** a failed/rejected change set is not successful adoption. Save errors and inspect stack/change-set existence, status, resources and events. Do not delete a stack merely because its name exists. Any cleanup of empty control-plane review state needs its own review and human approval; no physical resource deletion is part of this procedure.
- **During import or rollback:** stop subsequent batches and all normal updates. Inspect `IMPORT_*` status/events and ownership of every original physical ID across enabled Regions. Wait for active operations to settle when appropriate. Do not assume rollback detached every resource or left all ownership unchanged. `IMPORT_ROLLBACK_FAILED` requires a targeted recovery plan, not repeated execution or re-import of all mappings.
- **If serving/signing changes:** keep original distribution aliases/origin, bucket settings/policy/objects, certificate, nameservers, KSK/KMS key and parent DS intact. Do not disable DNSSEC, deactivate/delete a KSK, schedule key deletion, change parent DS, replace certificates, move aliases, or recreate buckets/zones as a shortcut. Escalate with exact events/current configuration and approve the smallest corrective plan separately.
- **If drift/policy verification fails:** do not ask CloudFormation to “fix” drift automatically. Compare template to actual state and decide whether evidence/template needs correction or a later, separately reviewed resource change is appropriate.
- Retain-based detachment is not an automatic undo. Do not delete any imported stack, remove resource definitions, or turn off termination protection to escape an error without resource-by-resource recovery review.

Share stack/change-set ARNs, statuses and relevant redacted errors—not credentials, tokens, private keys or unreviewed secret-bearing configuration. The assistant can help diagnose through read-only AWS access at each stop.

## Console alternative for preparation

If CLI preparation is unfamiliar, the documented console flow is:

1. Confirm account `995361647121`, select the intended stack Region, and open **CloudFormation → Create stack → With existing resources (import resources)**. Do not choose ordinary new-resource creation.
2. Upload the reviewed template. Supply exact resource identifiers from its matching JSON mapping; use the table's stack name and no added stack tags/parameters/service role.
3. Proceed through **Specify stack details**. Choosing **Next** creates a change set. **Stop at review.** The final **Import resources** button executes; do not click it yet.
4. Record/share the review stack and change-set ARNs. Complete stages 5–6 and obtain separate stage-7 approval. The policy readback, drift and direct-configuration checks still apply; use the established CLI/API or supported console facilities rather than inventing a workaround.

AWS primary sources and predecessor-specific observations, including Outputs failure and policy timing, are linked in [import research](import-research.md). No predecessor resource values or later security/tag/cache changes are imported into this site's baseline.
