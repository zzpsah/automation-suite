'use client'

import { useEffect, useRef, useState } from 'react'

type DocumentRow = {
  id: string
  original_filename: string
  document_type: string | null
  subject: string | null
  issuing_authority: string | null
  document_date: string | null
  status: string
}

export default function Home() {
  const input = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState('')
  const [docs, setDocs] = useState<DocumentRow[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function search(value = query) {
    const response = await fetch(`/api/documents/search?q=${encodeURIComponent(value)}`)
    if (!response.ok) return
    const data = await response.json() as { documents: DocumentRow[] }
    setDocs(data.documents)
  }

  useEffect(() => { void search('') }, [])

  async function upload(files: FileList | null) {
    if (!files?.length) return
    setBusy(true)
    setMessage(`Uploading ${files.length} document${files.length > 1 ? 's' : ''}…`)
    try {
      for (const file of Array.from(files)) {
        const presign = await fetch('/api/documents/upload-url', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ filename: file.name, contentType: file.type || 'application/pdf', size: file.size }),
        })
        if (!presign.ok) throw new Error((await presign.json()).error || 'Unable to prepare upload')
        const signed = await presign.json() as { url: string; key: string }
        const put = await fetch(signed.url, { method: 'PUT', headers: { 'content-type': file.type || 'application/pdf' }, body: file })
        if (!put.ok) throw new Error(`Upload failed for ${file.name}`)
        const register = await fetch('/api/documents', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ key: signed.key, filename: file.name, contentType: file.type || 'application/pdf', size: file.size }),
        })
        if (!register.ok) throw new Error((await register.json()).error || `Registration failed for ${file.name}`)
      }
      setMessage('Uploaded. Processing has been queued.')
      await search('')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Upload failed')
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="logo">DI</div>
          <div><div className="eyebrow">DevOS</div><h1>Document Intelligence</h1></div>
        </div>
        <span className="subtle">Evidence-first archive · OCR · AI · automation</span>
      </header>

      <section className="grid">
        <div className="panel hero">
          <div style={{ fontSize: 42 }}>📄</div>
          <h2>Drop your letters here</h2>
          <p className="subtle">PDFs, scanned letters and images are preserved unchanged before processing.</p>
          <label className="uploadButton">
            {busy ? 'Processing upload…' : '+ Upload documents'}
            <input ref={input} type="file" accept="application/pdf,image/*" multiple disabled={busy} onChange={e => void upload(e.target.files)} />
          </label>
          {message && <p className="subtle">{message}</p>}
        </div>

        <div className="panel">
          <div className="eyebrow">Automation model</div>
          <h2 style={{ marginTop: 5 }}>Only exceptions reach you</h2>
          <p className="subtle">Upload → OCR → contextual extraction → validation → search → portal worker. OTP, CAPTCHA and uncertain fields become explicit review tasks.</p>
          <div className="note">The original file is the evidence source. OCR and AI outputs are derived layers and can never overwrite it.</div>
        </div>
      </section>

      <section className="panel" style={{ marginTop: 18 }}>
        <div className="stats">
          <div className="stat"><span>Total documents</span><strong>{docs.length}</strong></div>
          <div className="stat"><span>Needs review</span><strong>{docs.filter(d => d.status === 'review_required').length}</strong></div>
          <div className="stat"><span>Queued / processing</span><strong>{docs.filter(d => !['verified','completed'].includes(d.status)).length}</strong></div>
        </div>
      </section>

      <section className="panel" style={{ marginTop: 18 }}>
        <div className="eyebrow">Knowledge archive</div>
        <h2 style={{ margin: '4px 0 14px' }}>Search documents</h2>
        <input className="search" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') void search() }} placeholder="Search subject, authority, memo number, school, person or content…" />
        <div className="list">
          {docs.length === 0 && <div className="note">No documents indexed yet. Upload the supplied transfer-order PDF to create the first real regression record.</div>}
          {docs.map(doc => (
            <article className="doc" key={doc.id}>
              <div><h3>{doc.subject || doc.original_filename}</h3><p>{doc.issuing_authority || 'Authority pending'} · {doc.document_date || 'Date pending'} · {doc.document_type || 'Type pending'}</p><p style={{ marginTop: 4 }}>{doc.original_filename}</p></div>
              <span className={`badge ${doc.status === 'verified' ? 'success' : doc.status === 'review_required' ? 'warning' : ''}`}>{doc.status.replaceAll('_', ' ')}</span>
            </article>
          ))}
        </div>
      </section>
      <div className="footer">Original evidence is immutable · derived data is versioned · portal actions remain auditable</div>
    </main>
  )
}
