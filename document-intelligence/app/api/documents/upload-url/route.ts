import { PutObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { NextResponse } from 'next/server'
import { randomUUID } from 'node:crypto'
import { r2Client, bucket } from '@/lib/r2'

const allowed = new Set(['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/webp'])
const maxBytes = 25 * 1024 * 1024

export async function POST(request: Request) {
  try {
    const body = await request.json() as { filename?: string; contentType?: string; size?: number }
    const filename = body.filename?.trim()
    const contentType = body.contentType || 'application/pdf'
    const size = Number(body.size || 0)
    if (!filename || filename.length > 180) return NextResponse.json({ error: 'Invalid filename' }, { status: 400 })
    if (!allowed.has(contentType)) return NextResponse.json({ error: 'Only PDF/JPEG/PNG/TIFF/WebP files are supported' }, { status: 415 })
    if (!Number.isFinite(size) || size <= 0 || size > maxBytes) return NextResponse.json({ error: 'Maximum upload size is 25 MB' }, { status: 413 })
    const safeName = filename.replace(/[^a-zA-Z0-9._-]/g, '_')
    const key = `original/${new Date().toISOString().slice(0, 10)}/${randomUUID()}-${safeName}`
    const url = await getSignedUrl(r2Client(), new PutObjectCommand({ Bucket: bucket(), Key: key, ContentType: contentType, ContentLength: size }), { expiresIn: 900 })
    return NextResponse.json({ url, key })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unable to prepare upload' }, { status: 500 })
  }
}
