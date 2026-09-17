export type AutomationState = 'queued' | 'running' | 'blocked' | 'failed' | 'completed'

export type PortalContext = {
  sessionKey: string
  baseUrl: string
}

export type FieldValue = string | number | boolean | null

export interface PortalAdapter {
  readonly key: string
  readonly displayName: string
  login(context: PortalContext): Promise<void>
  navigate(context: PortalContext, target: string): Promise<void>
  fill(context: PortalContext, fields: Record<string, FieldValue>): Promise<void>
  upload(context: PortalContext, field: string, fileKey: string): Promise<void>
  validate(context: PortalContext): Promise<{ ok: boolean; issues: string[] }>
  submit(context: PortalContext): Promise<{ reference?: string; blocked?: 'otp' | 'captcha' | 'security_key' }>
  captureResult(context: PortalContext): Promise<Record<string, unknown>>
}

export class PortalBlockedError extends Error {
  constructor(public readonly reason: 'otp' | 'captcha' | 'security_key', message = `Portal requires ${reason}`) {
    super(message)
    this.name = 'PortalBlockedError'
  }
}
