import { NextRequest, NextResponse } from 'next/server'
import { createHmac, timingSafeEqual } from 'node:crypto'

function valid(value: string | undefined) {
  const secret = process.env.AUTH_SECRET
  if (!secret || secret.length < 32 || !value) return false
  const [payload, signature] = value.split('.')
  if (!payload || !signature || Number(payload) < Date.now()) return false
  const expected = createHmac('sha256', secret).update(payload).digest('hex')
  if (signature.length !== expected.length) return false
  return timingSafeEqual(Buffer.from(signature), Buffer.from(expected))
}

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === '/login' || request.nextUrl.pathname.startsWith('/api/auth')) return NextResponse.next()
  if (request.nextUrl.pathname.startsWith('/api/') || request.nextUrl.pathname === '/') {
    if (!valid(request.cookies.get('di_session')?.value)) {
      if (request.nextUrl.pathname.startsWith('/api/')) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  return NextResponse.next()
}

export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] }
