# GCS Secrets Scanner Setup Guide

This guide documents the automated secrets scanning workflow that monitors the public GCS bucket `gs://viral-references/` for accidentally deployed credentials.

## Overview

The secrets scanner runs:
- **After every deployment** (triggered automatically when the deploy workflow completes)
- **Weekly on Sundays at midnight UTC** (scheduled cron job)
- **On-demand** (manual trigger via GitHub Actions)

## Prerequisites

**None!** The bucket is public, so no authentication or service account setup is required.

## Setup

The workflow is ready to use immediately after merging. No additional setup steps are needed.

## Verification

Test the workflow after merging:

1. **Manual Trigger Test**: Go to Actions tab → "Scan GCS Bucket for Secrets" → Run workflow
2. **Verify Public Access**: Confirm the bucket is publicly accessible:
   ```bash
   gcloud storage ls gs://viral-references/
   ```

## Workflow Details

- **Workflow File**: `.github/workflows/scan-gcs-secrets.yml`
- **Scanner**: gitleaks v2 (GitHub Action)
- **Scope**: Entire bucket (all paths: `main/`, version tags like `1.0.0/`, etc.)
- **On Detection**: Workflow fails and appears in Actions tab
- **Authentication**: None required (bucket is public)

## Handling False Positives

If the scanner detects false positives (e.g., high-entropy strings in TSV data files):

1. Create a `.gitleaks.toml` configuration file in the repository root
2. Add allowlist patterns for known false positives
3. Update the workflow to use the custom config

Example `.gitleaks.toml`:
```toml
[allowlist]
description = "Allow high-entropy strings in TSV data files"
paths = [
  '''\.tsv$''',
]
```

## Security Notes

- **Public Bucket**: The bucket is already publicly readable, so no additional access is granted
- **Ephemeral Storage**: Downloaded bucket contents are stored in GitHub runner temp directory (automatically cleaned up)
- **Audit Trail**: All workflow runs are logged in GitHub Actions
- **No Credentials**: No service account or credentials are used by the workflow

## Troubleshooting

### Workflow Fails with "Permission Denied"
- Verify the bucket is still publicly accessible:
  ```bash
  gcloud storage ls gs://viral-references/
  ```
- If bucket permissions changed, the workflow may need to be updated to use authentication

### No Scans After Deployment
- Verify `workflow_run` trigger is configured correctly
- Check that deploy workflow name matches: "Deploy to Google Cloud Storage"
- Ensure the deploy workflow completed successfully

### Scanner Not Running on Schedule
- Cron schedule is in UTC (Sunday 00:00 UTC)
- Check Actions tab for scheduled runs
- GitHub Actions may have a delay of a few minutes for scheduled workflows

## Related Documentation

- [gitleaks GitHub Action](https://github.com/gitleaks/gitleaks-action)
- [GCP Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [GitHub Actions workflow_run trigger](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
