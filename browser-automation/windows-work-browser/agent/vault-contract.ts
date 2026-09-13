export type SecretKind = "login" | "api-key" | "token" | "certificate";

export interface VaultEntryRef {
  id: string;
  label: string;
  kind: SecretKind;
  origin?: string;
}

export interface CredentialLease {
  leaseId: string;
  entryId: string;
  capability: "use-credential";
  expiresAt: string;
}

/**
 * Secret values never cross this interface into model-visible task state or
 * evidence. Platform adapters may use Windows DPAPI/Credential Manager or a
 * separately encrypted store; callers receive only an opaque lease.
 */
export interface CredentialVault {
  listEntries(): Promise<VaultEntryRef[]>;
  createLease(entryId: string, taskId: string, expiresAt: string): Promise<CredentialLease>;
  useLease(lease: CredentialLease, target: string): Promise<{ ok: boolean; summary: string }>;
  revokeLease(leaseId: string): Promise<void>;
}

export function assertCredentialLease(lease: CredentialLease, now = new Date()): void {
  if (!lease.leaseId || !lease.entryId) throw new Error("Credential lease is incomplete.");
  if (lease.capability !== "use-credential") throw new Error("Invalid credential lease capability.");
  if (new Date(lease.expiresAt).getTime() <= now.getTime()) {
    throw new Error("Credential lease has expired.");
  }
}
