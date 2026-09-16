import { NextRequest, NextResponse } from 'next/server'

function hex(buffer: ArrayBuffer) {
  return Array.from(new Uint8Array(buffer)).map(byte => byte.toString(16).padStart(2, '0')).join('')
}

async function valid(value: string | undefined) {
  const secret = process.env.AUTH_SECRET
  if (!secret || secret.length < 32 || !value) return false
  const [payload, signature] = value.split('.')
  if (!payload || !signature || Number(payload) < Date.now()) return false
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
  return crypto.subtle.verify('HMAC', key, new Uint8Array(signature.match(/.{2}/g)?.map(h => parseInt(h, 16)) || []), new TextEncoder().encode(payload))
}

export async function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === '/login' || request.nextUrl.pathname.startsWith('/api/auth')) return NextResponse.next()
  if (request.nextUrl.pathname.startsWith('/api/') || request.nextUrl.pathname === '/') {
    if (!(await valid(request.cookies.get('di_session')?.value))) {
      if (request.nextUrl.pathname.startsWith('/api/')) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  return NextResponse.next()
}

export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] }
