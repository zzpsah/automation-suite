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
 * The only model-facing credential capability is the opaque `use-credential`
 * operation: raw passwords/tokens are never returned to the AI, persisted in
 * task state, or written to evidence logs.
 *
 * Implementations must use Windows DPAPI/Credential Manager or an equivalent
 * OS-backed secret store. `use-credential` must not expose secret material.
 */
export const CREDENTIAL_CAPABILITY = "use-credential" as const;
