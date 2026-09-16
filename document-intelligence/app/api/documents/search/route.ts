import { NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET(request: Request) {
  try {
    const q = new URL(request.url).searchParams.get('q')?.trim() || ''
    const db = supabaseAdmin()
    let query = db.from('documents').select('id,original_filename,document_type,subject,issuing_authority,document_date,status').order('created_at', { ascending: false }).limit(50)
    if (q) query = query.or(`original_filename.ilike.%${q}%,subject.ilike.%${q}%,issuing_authority.ilike.%${q}%,document_type.ilike.%${q}%`)
    const { data, error } = await query
    if (error) throw error
    return NextResponse.json({ documents: data || [] })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Search failed' }, { status: 500 })
  }
}
