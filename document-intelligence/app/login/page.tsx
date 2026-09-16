'use client'

import { FormEvent, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const router = useRouter()

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('')
    const response = await fetch('/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ password }) })
    if (response.ok) router.replace('/')
    else setError('Invalid access password.')
    setBusy(false)
  }

  return <main className="shell" style={{ maxWidth: 520 }}>
    <div className="panel" style={{ marginTop: '14vh' }}>
      <div className="eyebrow">Private archive</div>
      <h1 style={{ marginTop: 5 }}>Document Intelligence</h1>
      <p className="subtle">Sign in to access your document archive and automation queue.</p>
      <form onSubmit={submit}>
        <input className="search" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Access password" autoFocus />
        <button className="uploadButton" disabled={busy || !password} type="submit">{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>
      {error && <p style={{ color: '#b42318' }}>{error}</p>}
    </div>
  </main>
}
