import { NextResponse } from 'next/server'
import { createHash } from 'node:crypto'
import { supabaseAdmin } from '@/lib/supabase'

export async function POST(request: Request) {
  try {
    const body = await request.json() as { key?: string; filename?: string; contentType?: string; size?: number }
    if (!body.key || !body.filename) return NextResponse.json({ error: 'key and filename are required' }, { status: 400 })
    const sourceHash = createHash('sha256').update(body.key).digest('hex')
    const { data, error } = await supabaseAdmin().from('documents').insert({
      source_key: body.key,
      original_filename: body.filename,
      content_type: body.contentType || 'application/pdf',
      byte_size: body.size || null,
      source_key_hash: sourceHash,
      status: 'queued',
    }).select('id,original_filename,status').single()
    if (error) throw error
    return NextResponse.json({ document: data }, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unable to register document' }, { status: 500 })
  }
}
