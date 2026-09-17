import { S3Client } from '@aws-sdk/client-s3'

export function r2Client() {
  const account = process.env.R2_ACCOUNT_ID
  const accessKeyId = process.env.R2_ACCESS_KEY_ID
  const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY
  if (!account || !accessKeyId || !secretAccessKey) throw new Error('R2 storage environment is incomplete')
  return new S3Client({
    region: 'auto',
    endpoint: `https://${account}.r2.cloudflarestorage.com`,
    credentials: { accessKeyId, secretAccessKey },
  })
}

export function bucket() {
  const value = process.env.R2_BUCKET
  if (!value) throw new Error('R2_BUCKET is not configured')
  return value
}
