import { NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET(request: Request) {
  try {
    const q = new URL(request.url).searchParams.get('q')?.trim() || ''
    const db = supabaseAdmin()
    if (!q) {
      const { data, error } = await db.from('documents').select('id,original_filename,document_type,subject,issuing_authority,document_date,status').order('created_at', { ascending: false }).limit(50)
      if (error) throw error
      return NextResponse.json({ documents: data || [] })
    }
    const { data, error } = await db.rpc('search_documents', { search_query: q })
    if (error) throw error
    return NextResponse.json({ documents: (data || []).map(({ rank: _rank, ...doc }: { rank: number } & Document) => doc) })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Search failed' }, { status: 500 })
  }
}

type Document = {
  id: string
  original_filename: string
  document_type: string | null
  subject: string | null
  issuing_authority: string | null
  document_date: string | null
  status: string
}
