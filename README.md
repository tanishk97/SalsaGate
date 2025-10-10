# SalsaGate

SalsaGate is a teaching repository for demonstrating how modern supply-chain
controls prevent tampering in static site deployments. The project contains two
contrasting GitHub Actions workflows: a "normal" pipeline that relies on manual
approval, and a hardened pipeline that produces signed artifacts, SLSA
provenance, and automated verification.

## Why SalsaGate?

Attackers frequently target the gap between human approval and deployment. By
comparing the two pipelines in this repository you can observe exactly how an
artifact can be modified after a human approves it, and how cryptographic
verification closes that window of opportunity.

## Repository Layout

| Path | Description |
| --- | --- |
| `.github/workflows/` | GitHub Actions definitions for the insecure and hardened pipelines |
| `infra/` | Example AWS policies and IAM role documents for running the trust workflow |
| `trust-service/` | Optional Lambda verifier that enforces promotion rules |
| `images/logo1.png` | Project logo used in presentations |

## Pipelines

### 00-normal-pipeline (Tamper Demonstration)

This workflow intentionally highlights the weakness of relying on a manual
approver:

1. Builds a tarball (`site-<sha>.tgz`) from the static `dist/` directory.
2. Uploads the artifact and pauses for approval in the `manual-approval`
   environment.
3. After approval, downloads the artifact, displays the original contents, and
   then tampers with `index.html` before re-packaging the tarball.
4. Prints a new checksum to show that the artifact has changed even though the
   manual gate succeeded.

Use this workflow when teaching why artifact integrity cannot be delegated to a
person alone.

### 01-build-attest (Trusted Build)

The secure build pipeline introduces cryptographic assurances:

- Generates the same site tarball as the insecure workflow.
- Produces an SPDX SBOM and minimal SLSA provenance file.
- Signs the tarball with Sigstore `cosign` and uploads the bundle (tarball,
  signature, certificate, provenance, and SBOM) to an S3 staging bucket.

### 02-verify-promote (Verification & Release)

A manually triggered workflow that validates and, optionally, promotes the
signed artifact:

1. Downloads the bundle from the staging bucket.
2. Verifies both the signature and SLSA attestation with `cosign` blob commands.
3. When `promote` is set to `true`, copies the tarball to the website bucket
   while tagging it `trust=verified` so that the bucket policy permits
   deployment.

## Optional Trust Service

`trust-service/` contains a containerized AWS Lambda function that performs the
same checks automatically whenever a new object lands in the staging bucket. The
function can write results to DynamoDB, apply verification tags, and even copy
verified artifacts to production.

### Environment Variables

- `LEDGER_TABLE` – DynamoDB table name for audit entries.
- `WEBSITE_BUCKET` – Destination bucket for promotion.
- `OIDC_ISSUER` – Expected OIDC issuer (defaults to
  `https://token.actions.githubusercontent.com`).

## AWS Prerequisites

Before running the trusted workflow set up the following resources (replace the
placeholders in the JSON documents with your values):

1. **Staging and Website Buckets** – See `infra/bucket-policy-website.json` for
   the zero-trust website bucket policy.
2. **OIDC IAM Role** – Provision the role defined in `infra/iam-gha-oidc-role.json`
   and store the ARN for use in GitHub Actions secrets.
3. **EventBridge/Lambda Triggers** – Optional automation using
   `infra/eventbridge-s3-notification.json` and the Lambda verifier.

## Running the Demo

1. Fork the repository and configure the required GitHub Secrets (AWS account,
   bucket names, OIDC role ARN, etc.).
2. Push a commit to `main` and observe the `00-normal-pipeline` run. Approve the
   environment and note that the artifact checksum changes afterward.
3. Trigger `01-build-attest` and `02-verify-promote` to see the signed workflow
   in action.
4. Optionally deploy the Lambda trust service to enforce verification
   automatically.

## Verification Cheat Sheet

```bash
# After downloading artifacts from the staging bucket
cosign verify-blob \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp "https://github.com/.+" \
  --signature site-<sha>.tgz.sig \
  --certificate site-<sha>.tgz.pem \
  site-<sha>.tgz

cosign verify-blob-attestation \
  --type slsaprovenance \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp "https://github.com/.+" \
  --bundle site-<sha>.tgz.attestation.sigstore \
  site-<sha>.tgz
```

## Additional Resources

- [Sigstore Documentation](https://docs.sigstore.dev/)
- [SLSA Framework](https://slsa.dev/)
- [GitHub Actions Environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

