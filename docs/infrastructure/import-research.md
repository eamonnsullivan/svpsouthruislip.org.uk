# Manual CloudFormation import: support and adoption safety

## Scope and conclusion

This research concerns adopting the existing `svpsouthruislip.org.uk` resources **in place**, using explicit manual `IMPORT` change sets, not auto-import, IaC generation, a rebuild, or a cross-account migration. AWS documentation was retrieved during this research; support should be rechecked immediately before preparation. No live account inventory, identifier-summary request, change-set preparation, or resource mutation was performed. AWS access was limited to MCP documentation search/read. GitHub predecessor evidence was retrieved with `gh`.

Repository `AGENTS.md`, `docs/agents/domain.md`, and `README.md` were inspected first. This remains a research note, not execution authority; the original research-only activity above is unchanged. Subsequent live inventory, template/identifier verification and all three separately approved human imports are now complete. **All ten original resources are adopted and fully verified: `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`.** Each batch is `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`; see [aggregate acceptance](../../infrastructure/verification/adoption-completion.json), [web](../../infrastructure/verification/web-import-completion.json), [key](../../infrastructure/verification/dnssec-key-import-completion.json) and [DNS](../../infrastructure/verification/dns-import-completion.json) completion evidence. The [inventory](inventory.md), [identifier evidence](../../infrastructure/verification/template-summaries.json) and [historical runbook](import-runbook.md) retain scope, approvals/pause history and exact identities.

Final DNS drift exports passed full review at `2026-11-03T14:54:03.563240Z`: `DETECTION_COMPLETE`, `IN_SYNC`, zero drifted resources and all complete resolved modeled expected/actual DNS properties equal, without pagination gaps. Final read-only AWS/public checks matched. Eight supported resources are `IN_SYNC`; unsupported BucketPolicy/KMS Alias were directly checked. Native drift is non-exhaustive and point-in-time public checks do not prove continuous zero outage. Installed-policy readbacks were verified earlier; the final refresh did not repeat policy APIs or the earlier full hosting audit. Receipt mtime is not exact policy API installation time or proof of the attachment gap. Key and zone tags remain empty; only the two web buckets retain expected CloudFormation system tags. No physical resources were replaced or deleted, and the assistant performed no AWS writes.

No further AWS writes or adoption gates remain. All adoption commands are historical reference only; do not repeat create/import/waiter/policy-install/drift steps. The eleven records, certificate, delegation/DS, registrar and shared IAM remain external and untouched. Verification completion does not release the publication/configuration freeze: the human must explicitly decide whether to resume publication/maintenance, and normal updates require separate planning/review. The [read supplement](inventory-access.md) is still present; any later removal needs separate human approval and additions-only changes preserving unrelated permission statements. No publication, commit/push, configuration or IAM work is authorized by completion.

**Recommendation:** adopt only confirmed, site-owned, supported resources, in separately approved batches. Keep existing DNS records and the ACM certificate external initially. Preserve serving configuration, identities, delegation, DS records, signing material, and publishing permissions. Import success is not evidence that the template matches production.

## 1. Current manual-import support

Source: AWS [Resource type support](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html), introductory text and resource table [S1]. The complete page was retrieved: 79,291 characters, `start_index=0`, `end_index=79291`, `truncated=false`. Absences below were checked against that complete table, not search snippets.

> “The following table lists AWS resource types that currently support import, drift detection, and infrastructure as code (IaC) generator operations.”

> “A resource that supports resource import could also support auto-import.”

Thus the **Import** column is the relevant support evidence; auto-import is a separate capability, not a prerequisite or substitute.

| Resource type | Manual import evidence [S1] | Native drift [S1] | Expected identifier-map fields; provenance below |
| --- | --- | --- | --- |
| `AWS::S3::Bucket` | Yes | Yes | `BucketName` |
| `AWS::S3::BucketPolicy` | Yes | No | `Bucket` (bucket name) |
| `AWS::CloudFront::Distribution` | Yes | Yes | `Id` (distribution ID) |
| `AWS::CloudFront::CloudFrontOriginAccessIdentity` | Yes | Yes | `Id` (OAI ID, not canonical user ID) |
| `AWS::Route53::HostedZone` | Yes | Yes | `Id` (zone ID) |
| `AWS::Route53::KeySigningKey` | Yes | Yes | **Both** `HostedZoneId` and `Name` |
| `AWS::Route53::DNSSEC` | Yes | Yes | `HostedZoneId` |
| `AWS::Route53::RecordSet` | Not listed; no documented manual-import support established | Not listed | Not established; do not invent mappings |
| `AWS::Route53::RecordSetGroup` | Not listed; no documented manual-import support established | Not listed | Not established; do not invent mappings |
| `AWS::KMS::Key` | Yes | Yes | `KeyId` (key ID) |
| `AWS::KMS::Alias` | Yes | No | `AliasName` (including `alias/` prefix) |
| `AWS::CertificateManager::Certificate` | Not listed; no documented manual-import support established | Not listed | Not established; certificate ARN remains an external reference |

The table lists `AWS::CertificateManager::Account` and `AWS::ACMPCA::Certificate`; neither is `AWS::CertificateManager::Certificate`. Importing certificate material into ACM is not importing an existing ACM resource into CloudFormation. AWS also warns that this table “is not an exhaustive list of AWS resources.” Consequently, absence is reported precisely as **not listed / support not established**, not an invented explicit `No` cell or proof of permanent impossibility. Do not include absent types in an adoption request without new authoritative support evidence.

Hosted-zone adoption does not establish ownership of individual record sets. Keep a separately reviewed record inventory and ownership boundary; do not delete/recreate records to force adoption. The predecessor explicitly retained records outside its imported zone [P3].

## 2. Identifiers: verify the actual template, not copied mappings

AWS [manual import — Resource identifiers](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/import-resources-manually.html) [S2] explicitly identifies an S3 bucket by `BucketName` and says:

> “Alternatively, you can get the identifier properties for the resources you're importing by calling the get-template-summary CLI command…”

AWS's [new-stack CLI walkthrough](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-new-stack.html) [S3] begins with `get-template-summary`, then builds entries containing `ResourceType`, `LogicalResourceId`, and a `ResourceIdentifier` object.

**Required project gate:** obtain fresh `GetTemplateSummary` results for every actual final template in its proposed account/Region, review `ResourceIdentifierSummaries`, and separately corroborate every identifier value through live configuration reads. Cover every logical ID, including multiple resources grouped under one type. Repeat after removing Outputs or changing templates. This project gate follows AWS's documented discovery method; it is not a claim that AWS requires a separate summary call before every API import.

Except for AWS's explicit S3 example, the expected fields in the table above come from the predecessor's successful account-side `GetTemplateSummary` and live-identity verification [P1], **not a new schema/API verification for this site**. Never copy its resource values. `GetTemplateSummary` does not prove property equality, ownership across all Regions, import permission sufficiency, or successful future execution. The predecessor notes it does not accept production parameter values; compare those separately [P1].

The predecessor recorded this exact KSK summary:

> `"ResourceIdentifiers": ["HostedZoneId,Name"]`

This means a composite identifier: supply **two keys**, `HostedZoneId` and `Name`, in the same `ResourceIdentifier` object. Do not supply one key named `HostedZoneId,Name`, treat the fields as alternatives, or use the joined physical ID `zone|name` as the import map. The predecessor's joined physical ID was completion evidence, not the input mapping [P1, P3]. Subsequent site-specific `GetTemplateSummary` results confirmed these mappings for the actual templates on 2026-11-02; see [saved identifier evidence](../../infrastructure/verification/template-summaries.json). Refresh after any template change.

## 3. What import validates—and what it does not

AWS [manual import — Resource import validation / Considerations](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/import-resources-manually.html) [S2] says validation checks existence, required properties and schema-valid values, and ownership by another stack in the same Region. Global resources need additional ownership discovery:

> “…some resource types aren't Region-specific, such as IAM roles, Route 53 hosted zones, or CloudFront distributions. For these types, make sure that the resource isn't already managed by a stack in another Region before importing it.”

Most importantly:

> “CloudFormation doesn't check that the template configuration matches the actual configuration of resource properties.”

> “Import operations don't allow new resource creations, resource deletions, or changes to property configurations.”

A schema-valid but inaccurate template can therefore import successfully and create a dangerous baseline for later updates. Compare full service configuration before import; do not substitute defaults or security improvements for unknown live values. Keep creation, deletion, OAI/OAC conversion, policy tightening, DNS edits, key changes, and certificate replacement out of the adoption batch.

Each imported resource must have `DeletionPolicy`; AWS permits any valid value, but **this adoption should require `Retain`**, plus `UpdateReplacePolicy: Retain` [S2, S5, S6]. Existing-stack resources must remain unchanged. AWS's existing-stack walkthrough additionally states that stack-level tags are applied at import execution [S4]; review tags explicitly rather than promising that import has no metadata effects whatsoever.

### Retention and protection are different controls

- **`DeletionPolicy: Retain`:** preserves the physical resource when deleting the stack or removing its definition during an update. It is not the control for an old instance replaced during an update. AWS: “This capability doesn't apply to resources whose physical instance is replaced during stack update operations” [S5]. Retention-based detachment changes ownership and needs its own approved recovery procedure; it is not an automatic undo.
- **`UpdateReplacePolicy: Retain`:** retains the **old** physical instance if a later update replaces it. AWS: “CloudFormation creates the replacement resource first, and then changes references from other dependent resources to point to the replacement resource.” Retention removes the old resource from CloudFormation's scope; it does **not** prevent replacement, reference switching, interruption, or continued charges [S6].
- **Termination protection:** blocks stack deletion, not normal resource updates or replacements. It differs from disabling rollback [S8].
- **Stack policy:** protects resources during updates. A policy denying replacement/deletion is an additional safeguard, not a substitute for retained resources, change-set review, IAM restrictions, or backups [S9].

### Drift is a limited diagnostic

AWS recommends drift detection after import and before subsequent stack operations [S2]. The support table explicitly says **no native drift detection for BucketPolicy and KMS Alias** [S1]; compare those directly, including the alias target and policy contents.

AWS's drift-limitations section [S7] states:

> “CloudFormation only determines drift for property values that are explicitly set, either through the stack template or by specifying template parameters. This doesn’t include default values for resource properties.”

Unsupported resources are `NOT_CHECKED`; `IN_SYNC` is not comprehensive proof of matching configuration or operational health. Supplement drift with full direct comparisons, unchanged physical IDs, DNS/DS/delegation/signing checks, certificate association, public HTTP/HTTPS checks, and publishing-path verification. Neither drift nor retained infrastructure is a backup of bucket contents or signing material.

## 4. Outputs failure and protection timing

### Outputs: supported AWS guidance, also reproduced by predecessor

AWS [change-set errors — Modified output error](https://repost.aws/knowledge-center/cloudformation-change-set-errors) [S10] explicitly describes creating a new resource-import stack with Outputs and quotes:

> “There was an error creating this change set. As part of the import operation, you cannot modify or add [Outputs]”

> “The Outputs sections in both templates must be the same.”

For a new **manual** import stack, omit convenience Outputs. For an existing stack, preserve its Outputs unchanged. Add Outputs only through a separately reviewed normal update after adoption/protection. AWS's alternative auto-import suggestion does not change the scope of this research. The predecessor's first preparation failed on Outputs; removing Outputs and refreshing summary evidence allowed corrected preparation [P1, P2].

### Termination protection in `REVIEW_IN_PROGRESS`: AWS-supported

AWS [Protect CloudFormation stacks from being deleted](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html) [S8] says:

> “You can set termination protection on a stack with any status except DELETE_IN_PROGRESS or DELETE_COMPLETE.”

Therefore `REVIEW_IN_PROGRESS` is eligible. After preparing the new import change set, enable and verify termination protection **before execution**. Console path: **Stack actions → Edit termination protection → Enable → Save** [S8]. This is a separately authorized metadata mutation, not a read-only check.

### Stack policy timing: predecessor observation, not an AWS status guarantee

The predecessor reports that `SetStackPolicy` failed explicitly because the stack was `REVIEW_IN_PROGRESS`; it corrected the wizard to wait for `IMPORT_COMPLETE`, then attach/read back the policy immediately, before any normal update [P2]. Its final completion evidence records active protections [P3].

AWS documents policies that prevent updates and the `SetStackPolicy` operation [S9, S11]. **An authoritative AWS statement specifically enumerating `REVIEW_IN_PROGRESS` as ineligible for `SetStackPolicy` was not obtained.** Do not mislabel the predecessor's runtime observation as an AWS-documented status rule. Use its conservative ordering as the proposed operational gate: retained import-only plan and termination protection first; separately approved execution; wait for `IMPORT_COMPLETE`; immediately attach and verify the intended stack policy; no normal updates in the gap. If attachment fails, stop and preserve evidence—do not create dummy resources, duplicate stacks, or ordinary updates to work around it.

## 5. Operator flow and safe review boundary

These are researched future operator steps, **not authorization to perform them**. Preparing a change set creates CloudFormation control-plane state, even when it does not yet adopt resources. Protection changes and execution need separate approval. No commands were executed in this research.

### New stack through the console [S3]

1. Confirm account, role, stack Region, ownership and fresh inventory. Use **Create stack → With existing resources (import resources)**, not ordinary resource creation.
2. Read **Import overview**; provide the reviewed template by file upload or S3 URL.
3. On **Identify resources**, supply verified identifier properties and actual values, including composite mappings.
4. Set reviewed parameters on **Specify stack details**. AWS says choosing **Next** automatically creates a change set.
5. Pause at review. Inspect exact import actions, template, identifiers, parameters, tags, validation findings and protections. **Choosing “Import resources” executes the change set**, not merely another preview. Do not click until separately authorized.
6. After authorized execution, wait for `IMPORT_COMPLETE`, verify identities, attach/read back the stack policy using the timing above, then complete configuration, supported drift and operational verification.

### New stack through the CLI/API [S3]

AWS's documented sequence is `get-template-summary` → compose explicit JSON `ResourcesToImport` entries → `create-change-set` with **`--change-set-type IMPORT`** and **`--resources-to-import`** → `describe-change-set` → separately authorized `execute-change-set`. Use a new intended stack name and reviewed template/parameters; do not first run ordinary `create-stack`, `deploy`, or an auto-import workflow. JSON mappings can be provided through a `file://` input; inline YAML is not supported for `--resources-to-import`.

At the original research stage, no executable production command was supplied here because this site's identifiers, account, Region, approved stack boundaries and request had not yet been inventoried. Subsequent inventory and the completed web batch are linked above; current separately gated procedures belong in the runbook. AWS's new-stack walkthrough contains exact example syntax [S3].

### Review checklist before any execution

- Confirm exact stack/change-set ARNs and template version; inspect all pages of `DescribeChangeSet`. AWS describes this API as returning inputs and the changes that will occur **if** executed [S13]. Require `CREATE_COMPLETE` and execution `AVAILABLE`, not merely successful request submission.
- Require exactly the approved resources with **`Import`** actions and intended physical identities. Reject `Add`, `Modify`, `Remove`, replacements, unexpected resources, parameter/tag changes, nested stacks or auto-import. Review both Retain attributes, references, no added Outputs, capabilities and intended rollback behavior.
- Read back the prepared template with `GetTemplate`; compare to the reviewed artifact. Confirm no resources have yet been adopted into the new review stack; the predecessor observed an empty `REVIEW_IN_PROGRESS` stack at this stage [P2]. Do not treat that observation as a universal status guarantee for every flow.
- Read operation/validation events, including warnings. `DescribeEvents` is a **current CloudFormation API**, distinct from `DescribeStackEvents`: AWS's first-party article documents change-set validation events and operation IDs [S12], and its SDK reference shows `ChangeSetName`, `StackName`, `OperationId`, `NextToken`, and optional `Filters.FailedEvents` [S11]. Inspect all returned pages, not only a failed-events filter.
- Review `VALIDATION_ERROR`, `ValidationFailureMode`, `ValidationStatus`, `ValidationStatusReason`, and `ValidationPath` when returned. AWS explains that **WARN** can allow successful change-set creation despite a failed check; **FAIL** prevents execution [S12]. Thus `CREATE_COMPLETE` alone is insufficient.
- Use the SDK/API's `ChangeSetName` (the change-set ARN may be supplied) or installed CLI model's equivalent. The AWS article inconsistently shows both `--change-set-id` and `--change-set-name`; do not blindly copy its first command. Verify the installed tool's model/help before use [S11, S12].
- No documentation obtained guarantees every pre-deployment validation applies to every manual-import resource/Region. Empty findings are not proof of property equality or exhaustive safety. If the API is unavailable or denied, record that gap and stop the review gate rather than claim validation passed or expand permissions silently.
- Verify termination protection before execution and explicitly accept the post-import policy timing. Keep reviewers unable to execute; approve the exact plan, not a broad deployment permission.

## 6. Questions requiring live inventory or operator decisions

1. Which account, partition, enabled Regions, operator/reviewer identities and stack Regions are intended? Do any existing stacks in **any enabled Region** already own these resources, including global CloudFront/Route 53 resources?
2. What are the actual site/redirect buckets, their Regions and complete configurations/policies? Which OAI/OAC, distribution, cache/origin/request/response policies, functions, logging resources and other dependencies are used or shared?
3. What are the full distribution configuration, origin type, aliases and certificate ARN/Region? Which certificate renewal/validation records must remain untouched?
4. What is the authoritative hosted-zone ID, all record sets (including mail, NS/SOA, validation and routing policies), registrar delegation and parent DS state? Is DNSSEC enabled, and what are KSK names/status, backing KMS ARN, key policy/grants and alias targets? Are any shared with other zones/sites?
5. What does fresh `GetTemplateSummary` return for every final proposed template? Do composite KSK fields and all other identifier fields still match the expected mappings, with separately verified live values?
6. Which resources are exclusively site-owned and approved for adoption? Are DNS records, certificate, registrar, shared IAM/OIDC and shared dependencies explicitly excluded? What batch/stack boundaries reflect actual Regions and ownership?
7. What tags and unmodeled service properties exist? Which properties can be represented faithfully, and which require explicitly documented exceptions/direct checks?
8. What are the approved execution role, audit evidence, rollback/recovery procedure, content backups, protection policy, maintenance window and baseline health tests? Who accepts the short post-import stack-policy gap?

**Unavailable in this research:** actual site inventory and identifiers; current account-side schemas/summary outputs; final stack boundaries; permission sufficiency; live API availability; complete per-property drift coverage; a documented AWS `SetStackPolicy` review-state restriction; proof that import or recovery will succeed. None should be inferred from the predecessor's successful adoption.

## Sources

### Authoritative AWS sources

- **[S1]** Resource type support, complete table: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html
- **[S2]** Manual import, Resource identifiers / Resource import validation / Considerations: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/import-resources-manually.html
- **[S3]** Creating a stack from existing resources, console and CLI walkthroughs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-new-stack.html
- **[S4]** Importing into an existing stack, console step 8 / CLI step 5 (tags): https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-existing-stack.html
- **[S5]** DeletionPolicy attribute: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-attribute-deletionpolicy.html
- **[S6]** UpdateReplacePolicy attribute: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-attribute-updatereplacepolicy.html
- **[S7]** AWS Cloud Operations Blog, Limitations: https://aws.amazon.com/blogs/mt/implementing-an-alarm-to-automatically-detect-drift-in-aws-cloudformation-stacks/
- **[S8]** Protect stacks from deletion, eligible statuses and console procedure: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html
- **[S9]** Prevent updates to stack resources: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html
- **[S10]** AWS re:Post Knowledge Center, Modified output error: https://repost.aws/knowledge-center/cloudformation-change-set-errors
- **[S11]** Official AWS SDK for PHP CloudFormation reference, `DescribeEvents` request syntax and `SetStackPolicy`: https://docs.aws.amazon.com/aws-sdk-php/v3/api/api-cloudformation-2010-05-15.html
- **[S12]** AWS DevOps & Developer Productivity Blog, Understanding Validation Modes / Review validation results / New DescribeEvents API: https://aws.amazon.com/blogs/devops/accelerate-infrastructure-development-with-cloudformation-pre-deployment-validation-and-simplified-troubleshooting/
- **[S13]** Official Botocore `describe_change_set` reference, request syntax and response status values: https://docs.aws.amazon.com/botocore/latest/reference/services/cloudformation/client/describe_change_set.html

### Predecessor evidence—not AWS documentation or this site's inventory

All references are pinned to original commit `f91f1b68bece8705fea1a0ab11ee3a8d13fc3815` in `eamonnsullivan/eamonnsullivan.co.uk`, retrieved through GitHub's API using `gh`:

- **[P1]** Import mapping verification, exact fields, composite KSK, refresh after Outputs removal: https://github.com/eamonnsullivan/eamonnsullivan.co.uk/blob/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815/docs/infrastructure/import-mapping-verification.md
- **[P2]** Web change-set review, Outputs failure, successful event inspection, termination protection and observed `SetStackPolicy` restriction: https://github.com/eamonnsullivan/eamonnsullivan.co.uk/blob/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815/docs/infrastructure/web-change-set-review.md
- **[P3]** Adoption completion, original identities and records remaining external: https://github.com/eamonnsullivan/eamonnsullivan.co.uk/blob/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815/docs/infrastructure/adoption-completion.md
