import { NextResponse } from 'next/server'
import { createSession, sessionCookie } from '@/lib/auth'

export async function POST(request: Request) {
  const body = await request.json().catch(() => null) as { password?: string } | null
  const configured = process.env.APP_PASSWORD
  if (!configured) return NextResponse.json({ error: 'APP_PASSWORD is not configured' }, { status: 503 })
  if (!body?.password || body.password !== configured) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 })
  const response = NextResponse.json({ ok: true })
  response.cookies.set(sessionCookie, createSession(), { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', maxAge: 60 * 60 * 12, path: '/' })
  return response
}
