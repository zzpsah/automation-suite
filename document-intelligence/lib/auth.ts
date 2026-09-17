import { createHmac, timingSafeEqual } from 'node:crypto'
import { cookies } from 'next/headers'

const COOKIE = 'di_session'
const ttlSeconds = 60 * 60 * 12

function secret() {
  const value = process.env.AUTH_SECRET
  if (!value || value.length < 32) throw new Error('AUTH_SECRET must be at least 32 characters')
  return value
}

function sign(value: string) {
  return createHmac('sha256', secret()).update(value).digest('hex')
}

export function createSession() {
  const payload = `${Date.now() + ttlSeconds * 1000}`
  return `${payload}.${sign(payload)}`
}

export function validSession(value: string | undefined) {
  if (!value) return false
  const [payload, signature] = value.split('.')
  if (!payload || !signature || Number(payload) < Date.now()) return false
  const expected = sign(payload)
  if (signature.length !== expected.length) return false
  return timingSafeEqual(Buffer.from(signature), Buffer.from(expected))
}

export async function requireSession() {
  const store = await cookies()
  return validSession(store.get(COOKIE)?.value)
}

export const sessionCookie = COOKIE
