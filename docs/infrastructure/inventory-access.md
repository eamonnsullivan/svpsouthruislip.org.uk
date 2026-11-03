# Read-only configuration access for infrastructure adoption

## Current status: all ten adopted and verified; read supplement still present

On 2026-11-02, the human administrator provisioned the scoped supplement and the AWS MCP session successfully read the previously denied S3, CloudFront, ACM and KMS configurations. The session still assumes `AWSReservedSSO_ViewOnlyAccess_473dc8eafd445510` in account `995361647121`; MCP remains ViewOnly. Templates and import identifiers are validated. The human prepared the web change set and enabled termination protection, then paused. On 2026-11-03, fresh checks, login and review exports were verified; only after separate approval and explicit immediate-policy timing acknowledgement did the human execute the exact web import. All five original resources reached `IMPORT_COMPLETE` and passed full post-import verification, including human native drift exports validated at 10:09:24Z. Termination protection and the installed stack policy are verified. See [web completion evidence](../../infrastructure/verification/web-import-completion.json) and [review/pause history](../../infrastructure/verification/web-change-set-review.json).

MCP was denied six CloudFormation deep-read APIs: `DescribeChangeSet`, `GetTemplate`, `DescribeEvents`, `DescribeStackEvents`, `DescribeStackDriftDetectionStatus` and `DescribeStackResourceDrifts`. The human supplied administrator exports through profile `AdministratorAccess-995361647121`; MCP privileges were not expanded. Native `GetStackPolicy` permission was not tested, so no denial is asserted. MCP independently observed overall `IN_SYNC`, four resource results `IN_SYNC`, expected BucketPolicy `NOT_CHECKED`, and termination protection enabled at 09:56:03Z.

**Adoption verification is complete for all ten original resources**, `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`; all batches are `IMPORT_COMPLETE_VERIFIED`, `fully_verified: true`. See [aggregate acceptance](../../infrastructure/verification/adoption-completion.json), [key completion](../../infrastructure/verification/dnssec-key-import-completion.json) and [DNS completion](../../infrastructure/verification/dns-import-completion.json). Human administrator exports supplied deep-read evidence without expanding MCP privileges; all AWS writes were separately approved human actions. The assistant remained read-only. Dated approval/pause and batch history is retained in the [historical runbook](import-runbook.md) and JSON evidence. Do not repeat completed create/import/waiter/policy-install/drift steps or overwrite private evidence.

Full DNS drift exports passed review at `2026-11-03T14:54:03.563240Z`: `DETECTION_COMPLETE`, `IN_SYNC`, zero drifted resources and no differences across all resolved modeled DNS properties, without pagination gaps. Final read-only AWS/public checks matched. Eight supported resources are `IN_SYNC`; unsupported BucketPolicy/KMS Alias were directly checked. Native coverage is non-exhaustive and health checks are point-in-time, not continuous zero-outage proof. The final refresh did not repeat the earlier full hosting audit or installed-policy APIs; previous verified readbacks remain evidence.

No AWS write is required for adoption. The read supplement is **still present**, and its removal is neither performed nor authorized. Any later removal requires separate human approval, removing only the supplement's additions while preserving unrelated permission statements. The publication/configuration freeze remains until explicitly released by the human; normal updates require separate planning/review. Completion does not authorize publication, commits/pushes, configuration changes or IAM work. Current follow-up is human review of completion and optional later operational decisions; records, certificate, delegation/DS, registrar and shared IAM remain external and untouched.

The original blocker was insufficient configuration-read access. `AccessDenied` was never treated as evidence that a configuration was absent. The full verified baseline is now in [inventory.md](inventory.md).

The supplement is [`infrastructure/permissions/inventory-read-only.json`](../../infrastructure/permissions/inventory-read-only.json). It is an IAM policy for inventory, **not a CloudFormation template**, and does not grant import or execution permissions.

## What has been established

These are point-in-time AWS MCP observations, not deployment approval:

| Item | Observed value |
| --- | --- |
| Account | `995361647121` |
| Live CloudFront distribution | `E2ZXKXV2U7OYGL`, `d1myhs7tjj0y6f.cloudfront.net`, enabled and deployed |
| CloudFront aliases | `svpsouthruislip.org.uk`, `www.svpsouthruislip.org.uk` |
| Origin | `svpsouthruislip.org.uk.s3-website-eu-west-1.amazonaws.com`, custom HTTP-only origin |
| Existing viewer certificate | `arn:aws:acm:us-east-1:995361647121:certificate/719a94fe-dad7-4dbf-9a1d-cbad2afc96b7` |
| Site/related buckets | `svpsouthruislip.org.uk`, `www.svpsouthruislip.org.uk`, legacy `aws-website-southruislipsaintvincentdepaulsociety-3sps9` |
| Legacy OAI | `E1H05UTZYYPBPP`; confirmed referenced by the site's existing bucket policy, not its website origin |
| Hosted zone | `Z3SM1DWWC45TX`, public, comment `SVP's domain`, no tags |
| DNS records | 11 records, including zone NS/SOA, web alias, Fastmail MX/SPF/DKIM, and two ACM validation records |
| DNSSEC | `SIGNING`; KSK `svpsouthruislip`, `ACTIVE` |
| DNSSEC key | `arn:aws:kms:us-east-1:995361647121:key/944105a2-c852-4c4f-a0f2-a0f1b91344c9` |
| DS reported by Route 53 | `3666 13 2 749A1CBE44DB67CB2955ADF5D3AA274EF2D8C47CC88E0DFBC97032A5D60FD4AB` |
| Initial CloudFormation ownership snapshot (2026-11-02) | No target-site resources found in active stacks across all 17 enabled Regions at that time; existing blog/audit stacks are separate. The five web resources are now imported and verified. |

`ListDistributions` is not a replacement for `GetDistributionConfig`: for example, the listing does not supply every distribution-level setting. The required full configuration reads have now succeeded. The legacy bucket was included only to investigate scope; a separate distribution, `E138N95OLHYZXP`, is disabled, has no aliases, and references that bucket in `us-east-1`. Both legacy resources remain outside adoption. See the full [verified inventory](inventory.md) for settings and explicit exclusions.

## Access boundary

The supplement grants:

- Bucket-level configuration reads for the three exact bucket ARNs above; **no `s3:GetObject`, object-version reads, or bucket content listing**.
- Full configuration reads for only the live distribution and candidate OAI.
- Key metadata, policy, rotation status and tag reads for only the exact DNSSEC key; **no decryption, signing, grants, policy changes, or key lifecycle operations**.
- Certificate metadata/tag reads for only the existing viewer certificate; no private-key export.
- Account S3 public-access-block settings; alias names and key associations across account `995361647121` in `us-east-1`; and template/identifier validation in `eu-west-1` and `us-east-1`. These wildcard grants require a session in account `995361647121`. `ValidateTemplate`, account public-access settings and alias discovery need `Resource: "*"`. `GetTemplateSummary` uses it here for new inline templates, but this also permits summaries of unrelated existing stacks in those two Regions. Summaries can reveal parameter definitions/defaults and resource metadata. These are metadata reads, not resource mutations; review and approve this exposure before provisioning.

Treat collected configurations as private: policies, tags and CloudFront custom headers may contain sensitive values. Do not commit raw inventory or paste credentials into chat. Review/redact evidence before publication.

This is an additive allow policy. It neither removes existing permissions nor overrides explicit denies, permissions boundaries, SCPs, or KMS key-policy restrictions. KMS may still deny reads even after the supplement is provisioned; if so, stop and diagnose rather than changing the signing key or blindly broadening access. Domain registration/contact reads are deliberately excluded; registration, delegation and parent DS will be checked separately without changing them.

## Historical human setup procedure; not authorization to repeat

The supplement was already provisioned. Do not repeat setup or remove access without separate human approval. The only change described in this historical procedure is to access permissions. **Do not change website resources, DNS, signing state, certificate, bucket public access, ownership controls, or key policy.**

The existing `.github/workflows/publish.yml` publishes site contents on every push to `main`, including infrastructure-only changes. Keep this preparation off `main` during the inventory/import freeze; do not trigger an unrelated content deployment while establishing the production baseline.

### 1. Review the supplement

Open the JSON file locally. Check the account and exact resource ARNs against the table above. There must be no resource-write action, `iam:PassRole`, object-read permission, or KMS data-plane permission. Keep an existing copy of the permission set's configuration for restoration.

The permission set may be assigned to other people or accounts. Check its assignments before changing it: everyone assigned that permission set in this account receives the added configuration-read access. Coordinate with the Identity Center administrator if it is shared.

### 2. Open the permission set as an administrator

1. Sign in to the AWS Organizations management account or delegated IAM Identity Center administrator account with a session authorized to administer permission sets. Do not try to perform this through the view-only MCP session.
2. Open <https://console.aws.amazon.com/singlesignon/> in the Region where IAM Identity Center is configured. The current MCP role does not reveal that Region; use the existing Identity Center setup rather than assuming the website's Region.
3. Navigate to **Multi-account permissions → Permission sets → ViewOnlyAccess**. Confirm this is the permission set assigned to your user for account `995361647121` and producing the observed reserved role.
4. Under **Inline policy**, choose **Edit** (or the add-inline-policy action if none exists).

**Do not edit the protected `AWSReservedSSO_…` IAM role directly.** Identity Center manages that role.

### 3. Merge, save, and reprovision

- If there is no inline policy, paste the complete supplement.
- If an inline policy already exists, first save its complete original JSON privately. Append the supplement's `Statement` entries to the existing `Statement` array, preserving the existing policy version and every existing statement. Do not replace the existing policy, paste one JSON object inside another, or duplicate an existing `Sid`.
- Keep the existing AWS managed `ViewOnlyAccess` policy attached.
- Review the console's validation findings. Resolve actual policy errors before saving; do not add broad `ReadOnlyAccess` or administrator permissions as a workaround.
- Choose **Save changes**. Check that the updated permission set is successfully provisioned to account `995361647121`. If the console reports accounts needing reprovisioning, use its **Update/Reprovision** action for the intended account and wait for success. Interface labels can vary; a saved permission-set definition without successful account provisioning is insufficient.

If policy-size limits or shared assignments prevent a safe inline merge, stop and have the administrator arrange a dedicated scoped read-only assignment. Do not discard existing statements to make room.

### 4. Refresh the read-only session

Refresh your existing SSO login if needed, then reconnect/restart the AWS MCP connection in ECA so subsequent calls use the intended permission set. IAM policy propagation may take a short time. Do not paste AWS credentials, SSO tokens, or private keys into chat or repository files.

Tell the assistant: **“Read-only supplement provisioned; retry inventory.”** The assistant will retry the previously denied reads, verify account/session identity, and report any remaining denies before preparing import templates.

### 5. Remove temporary extra access later

Verification is complete, but the supplement remains present and removal is not authorized now. Only after separate human approval may an administrator remove these added statement SIDs, reprovision, and verify both that the added configuration reads are denied again and that existing view-only access still works. Restore the original inline policy only if no unrelated changes have occurred since its backup; otherwise restoration could erase legitimate newer statements. Do not remove unrelated prior statements. Keeping the supplement for ongoing drift/configuration review is a separate access decision.

## Historical adoption procedure; operational decisions remain separate

All preparation, execution and verification phases are complete. The [import runbook](import-runbook.md) is historical reference, not a remaining task list; do not rerun adoption. No further AWS write is required. Human review of completion and any later freeze-release, maintenance or additions-only access-removal decision require separate approval.

AWS primary-source support research is recorded in [`import-research.md`](import-research.md).

## Sources

- AWS MCP read-only calls: `sts:GetCallerIdentity`; `ec2:DescribeRegions`; `cloudformation:ListStacks`/`ListStackResources` across enabled Regions; S3 and CloudFront list/configuration attempts; Route 53 zone/record/DNSSEC reads. Denied configuration reads are recorded as unknown, not absent.
- [IAM Identity Center custom permissions and inline policies](https://docs.aws.amazon.com/singlesignon/latest/userguide/permissionsetcustom.html): Identity Center provisions inline policies into assigned-account roles.
- [AWS guidance for protected AWSReservedSSO roles](https://repost.aws/knowledge-center/identity-center-aws-reserved-sso): modify the originating permission set in Identity Center, not the reserved IAM role.
- [Predecessor adoption implementation](https://github.com/eamonnsullivan/eamonnsullivan.co.uk/tree/f91f1b68bece8705fea1a0ab11ee3a8d13fc3815): historical import tooling/runbooks; current maintenance templates include later changes and must not be copied as a live baseline.
