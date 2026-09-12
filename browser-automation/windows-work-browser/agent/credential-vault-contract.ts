export interface CredentialRef {
  id: string;
  origin: string;
  username?: string;
}

export interface CredentialUseRequest {
  credentialId: string;
  origin: string;
  purpose: string;
}

export interface CredentialVault {
  list(origin?: string): Promise<ReadonlyArray<CredentialRef>>;
  use(request: CredentialUseRequest): Promise<{ ok: boolean; sessionRef?: string; error?: string }>;
  remove(credentialId: string): Promise<void>;
}

/**
 * Implementations must use Windows DPAPI/Credential Manager or an equivalent
 * OS-backed secret store. Raw passwords/tokens are never returned to the AI,
 * persisted in task state, or written to evidence logs.
 */
