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

The checker validates manifest paths, exact retained resource/map coverage, recorded identities and policy shape, then runs installed `cfn-lint` for each template's actual Region, failing on warnings. Tests additionally check the recorded template summary groupings (the recorded size and hash are historical evidence of what was imported, so they are not compared with the current template), DNS records, preservation of legacy hosting/signing settings, and renderer safety. They are adoption-baseline checks, not a timeless prohibition on separately approved future changes. They do not compare fresh AWS properties, establish permissions, back up content or prove operational health. A site build is unnecessary for documentation-only changes.

Keep the existing root `.gitignore` entries for `/.venv-infrastructure/` and `/infrastructure/work/`; do not commit private review bundles or raw configuration dumps.

## Update a stack

Use this workflow for an existing stack. It uses the AWS CLI throughout, so each
step can be copied, reviewed and repeated. Pushing to `main` publishes the site
but does not deploy infrastructure; templates only reach AWS through these
steps.

1. **Sign in and confirm the baseline.** Use [production.json](environments/production.json)
   to find the stack name, region and template, then set them once for the
   session. Run from the repository root.

   ```bash
   export AWS_PROFILE=AdministratorAccess-995361647121
   aws sso login

   STACK=svpsouthruislip-web
   REGION=eu-west-1
   TEMPLATE=infrastructure/templates/web.yaml

   aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
     --query 'Stacks[0].{Status:StackStatus,TerminationProtection:EnableTerminationProtection,Role:RoleARN,Drift:DriftInformation.StackDriftStatus}'
   ```

   Expect a `*_COMPLETE` status, termination protection `true`, no role and
   `IN_SYNC` drift. The stack policy should deny `Update:Replace` and
   `Update:Delete`; check it with
   `aws cloudformation get-stack-policy --region "$REGION" --stack-name "$STACK"`.
   Then confirm the only difference between the deployed and local templates is
   the one you intend:

   ```bash
   aws cloudformation get-template --region "$REGION" --stack-name "$STACK" \
     --template-stage Original --query TemplateBody --output text \
     | diff - "$TEMPLATE"
   ```

2. **Edit and validate locally.** Edit the template and review the diff. Run
   both checks in [Validating](#validating) and resolve failures before creating
   a change set. These stacks have no parameters, so there is nothing to carry
   over.
3. **Create an update change set.** Name it after the change. Leave out
   `--role-arn`, `--parameters`, `--capabilities` and stack-level `--tags` so the
   stack keeps its existing options. Creating a change set does not change any
   resource.

   ```bash
   CHANGE_SET=$STACK-add-domain-tag   # unique per attempt; pick a descriptive name

   aws cloudformation create-change-set --region "$REGION" --stack-name "$STACK" \
     --change-set-name "$CHANGE_SET" --change-set-type UPDATE \
     --description "Add Domain tag to SiteBucket" \
     --template-body "file://$TEMPLATE"

   aws cloudformation wait change-set-create-complete --region "$REGION" \
     --stack-name "$STACK" --change-set-name "$CHANGE_SET"
   ```

   If the wait fails, read the reason, fix the template and create a new change
   set under a new name:

   ```bash
   aws cloudformation describe-change-set --region "$REGION" --stack-name "$STACK" \
     --change-set-name "$CHANGE_SET" --query '{Status:Status,Reason:StatusReason}'
   aws cloudformation delete-change-set --region "$REGION" --stack-name "$STACK" \
     --change-set-name "$CHANGE_SET"
   ```

   A change set that finds no differences also ends in `FAILED`, with the reason
   "didn't contain changes".
4. **Inspect the plan.** Read the full list and require only changes that match
   the template diff.

   ```bash
   aws cloudformation describe-change-set --region "$REGION" --stack-name "$STACK" \
     --change-set-name "$CHANGE_SET" \
     --query '{Status:Status,Execution:ExecutionStatus,Changes:Changes[].ResourceChange.{Action:Action,Id:LogicalResourceId,Type:ResourceType,Replacement:Replacement,Scope:Scope}}'
   ```

   Expect `CREATE_COMPLETE` and `AVAILABLE`. For a tag change, expect a single
   `Modify` of the affected resource with `Scope` `["Tags"]` and `Replacement`
   `False`. Stop if there are unexpected additions, removals or modifications.
   For existing resources, treat `Replacement` of `True` or `Conditional` as a
   stop: do not execute until replacement has been separately reviewed and
   explicitly approved. The stack policy blocks replacement and deletion as a
   backstop, not as a substitute for this review.
5. **Execute the plan.** After approval of that exact change set, execute it and
   wait. Never override the stack policy to get past a failure.

   ```bash
   aws cloudformation execute-change-set --region "$REGION" --stack-name "$STACK" \
     --change-set-name "$CHANGE_SET"
   aws cloudformation wait stack-update-complete --region "$REGION" --stack-name "$STACK"
   ```

   On failure, inspect the recent stack events and review recovery against
   actual state. Never delete or recreate resources as a shortcut.

   ```bash
   aws cloudformation describe-stack-events --region "$REGION" --stack-name "$STACK" \
     --max-items 20 \
     --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
     --output table
   ```
6. **Verify.** Confirm the stack is `UPDATE_COMPLETE`, check the changed
   setting directly, then run a drift check:

   ```bash
   aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
     --query 'Stacks[0].StackStatus'
   aws s3api get-bucket-tagging --region "$REGION" --bucket svpsouthruislip.org.uk

   DRIFT_ID=$(aws cloudformation detect-stack-drift --region "$REGION" \
     --stack-name "$STACK" --query StackDriftDetectionId --output text)
   aws cloudformation describe-stack-drift-detection-status --region "$REGION" \
     --stack-drift-detection-id "$DRIFT_ID" \
     --query '{Status:DetectionStatus,Drift:StackDriftStatus,Drifted:DriftedStackResourceCount}'
   ```

   Repeat the drift status call until `DetectionStatus` is
   `DETECTION_COMPLETE`; expect `IN_SYNC`. Bucket policies and KMS aliases do
   not support drift detection, so compare them directly. Also verify original
   resource IDs and website and DNS behaviour where relevant.
