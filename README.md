# SalsaGate Trust Pipeline

This repo demonstrates end-to-end artifact trust for a static site using
Sigstore `cosign`, SLSA provenance, a staging bucket, and an optional
verifier Lambda .

## One-time AWS setup

1. Create two S3 buckets:
   - `STAGING_BUCKET` – temporary storage for build outputs.
   - `WEBSITE_BUCKET` – public site bucket.
2. Apply the policy in [`infra/bucket-policy-website.json`](infra/bucket-policy-website.json)
   to the website bucket so only objects tagged `trust=verified` can be uploaded.
3. Create an IAM role using [`infra/iam-gha-oidc-role.json`](infra/iam-gha-oidc-role.json)
   and note the ARN for `ROLE_ARN`.
4. *(Optional)* Create a DynamoDB table for the ledger and deploy the Lambda
   container in [`trust-service`](trust-service). Add an S3 trigger or Lambda URL
   and use [`infra/eventbridge-s3-notification.json`](infra/eventbridge-s3-notification.json)
   if you want automatic verification on upload.

Replace the TODO placeholders (`<REPLACE_ME>`, `<ACCOUNT_ID>`) in the workflows
and infra snippets with your actual values.

## Workflows

### 01-build-attest
Triggered on pushes to `main`.
1. Builds a tarball `site-<sha>.tgz` (creates a placeholder `dist/index.html` if
   nothing exists).
2. Generates an SPDX JSON SBOM.
3. Writes a minimal SLSA predicate `provenance.json`.
4. Installs cosign and signs/attests the tarball using blob commands.
5. Uploads the tarball, signature, certificate, attestation bundle, SBOM, and
   provenance file to the staging bucket.

### 02-verify-promote
Manual `workflow_dispatch` with `object_key` input (e.g., `site-<sha>.tgz`).
1. Downloads the artifact bundle from staging.
2. Verifies the signature and SLSA attestation with cosign blob commands.
3. If `promote` is `true`, copies the tarball to the website bucket with the
   tag `trust=verified` so the bucket policy permits it.

## Notes

- The workflows deliberately use `cosign` **blob** subcommands instead of image
  commands to avoid Docker Hub authentication issues.
- You can swap the manual `provenance.json` step with
  [`actions/attest-build-provenance@v1`](https://github.com/actions/attest-build-provenance)
  if you prefer a richer SLSA provenance.
- All AWS access uses OIDC; no long-lived credentials are stored in GitHub.
