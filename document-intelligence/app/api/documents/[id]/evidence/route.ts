import { GetObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'
import { r2Client, bucket } from '@/lib/r2'

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params
    const { data, error } = await supabaseAdmin().from('documents').select('source_key').eq('id', id).single()
    if (error || !data) return NextResponse.json({ error: 'Document not found' }, { status: 404 })
    const url = await getSignedUrl(r2Client(), new GetObjectCommand({ Bucket: bucket(), Key: data.source_key }), { expiresIn: 300 })
    return NextResponse.redirect(url)
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unable to open evidence' }, { status: 500 })
  }
}
