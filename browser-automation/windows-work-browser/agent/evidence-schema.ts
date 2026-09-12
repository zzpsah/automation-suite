export interface EvidenceRecord {
  actionId: string;
  timestamp: string;
  capability: string;
  risk: string;
  policy: "allowed" | "approval_required" | "denied";
  executor: "playwright" | "cdp" | "windows-native" | "service";
  outcome: "success" | "failure" | "skipped";
  verification?: {
    method: string;
    passed: boolean;
    summary: string;
  };
  artifacts?: Array<{
    type: "screenshot" | "dom" | "download" | "file" | "pdf" | "log";
    reference: string;
    sha256?: string;
  }>;
  error?: {
    code: string;
    recoverable: boolean;
  };
}

/** Evidence must contain references, never secret values or raw credentials. */
export function assertSafeEvidence(record: EvidenceRecord): void {
  const serialized = JSON.stringify(record).toLowerCase();
  for (const forbidden of ["password", "secret", "access_token", "refresh_token", "client_secret"]) {
    if (serialized.includes(forbidden)) {
      throw new Error(`Unsafe evidence field detected: ${forbidden}`);
    }
  }
}
