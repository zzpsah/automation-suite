export type VerificationMethod =
  | "dom"
  | "url"
  | "window"
  | "file"
  | "download"
  | "clipboard"
  | "screenshot"
  | "custom";

export interface Postcondition {
  id: string;
  method: VerificationMethod;
  description: string;
  expected: Record<string, unknown>;
}

export interface VerificationResult {
  postconditionId: string;
  passed: boolean;
  observed?: Record<string, unknown>;
  summary: string;
}

export interface Verifier {
  verify(postcondition: Postcondition): Promise<VerificationResult>;
}

/** Side effects are not considered complete until their declared postcondition passes. */
export function assertVerified(result: VerificationResult): void {
  if (!result.passed) throw new Error(`Verification failed: ${result.summary}`);
}
