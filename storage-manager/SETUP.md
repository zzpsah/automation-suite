# One-time setup

## Backblaze B2

Create a private bucket named `Education-Dept-Files` and an application key restricted to that bucket. Required access: read, write, and list. Obtain the S3-compatible endpoint from the B2 bucket/account information.

## Google Drive

Backup folder:
`11o-qvIo-C5UW6yr5hDScrWQ4uOHIw6Pk`

The Google Drive connector is not assumed. Automation uses Google Drive API OAuth credentials so the workflow remains independent of ChatGPT connectors.

Create an OAuth client in a Google Cloud project, authorize Drive access once, and store the resulting refresh token as a GitHub secret. Do not put client secrets or refresh tokens in source code or chat.

## GitHub Actions secrets

Add these repository secrets:

`B2_KEY_ID`
`B2_APPLICATION_KEY`
`B2_BUCKET_NAME`
`B2_S3_ENDPOINT`
`GOOGLE_DRIVE_FOLDER_ID`
`GOOGLE_CLIENT_ID`
`GOOGLE_CLIENT_SECRET`
`GOOGLE_REFRESH_TOKEN`

After these are present, workflows can operate without interactive login for each file.

## Free-first policy

Use only free-tier allowances. No paid storage tier or Cloudflare R2 dependency is required. Monitor usage and fail safely rather than silently enabling paid services.
