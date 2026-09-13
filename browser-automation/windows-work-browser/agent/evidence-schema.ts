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

const SECRET_KEYS = new Set([
  "password",
  "secret",
  "access_token",
  "refresh_token",
  "client_secret",
  "authorization",
  "cookie",
  "set-cookie",
]);

function assertNoSecretKeys(value: unknown, path = "evidence"): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertNoSecretKeys(item, `${path}[${index}]`));
    return;
  }

  if (!value || typeof value !== "object") return;

  for (const [key, child] of Object.entries(value)) {
    if (SECRET_KEYS.has(key.toLowerCase())) {
      throw new Error(`Unsafe evidence field key detected at ${path}.${key}`);
    }
    assertNoSecretKeys(child, `${path}.${key}`);
  }
}

/**
 * Evidence may describe a password-related workflow, but it may not contain
 * secret-bearing fields. Values are inspected by schema/key, not substring,
 * so legitimate summaries such as "password form opened" remain valid.
 */
export function assertSafeEvidence(record: EvidenceRecord): void {
  assertNoSecretKeys(record);
}
