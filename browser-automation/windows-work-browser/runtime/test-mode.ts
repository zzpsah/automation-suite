const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

/**
 * Test mode is intentionally narrower than production bypasses.
 * It can be enabled only for CI/test fixtures and cannot authorize
 * arbitrary native execution or real external side effects.
 */
export function isTestMode(): boolean {
  return process.env.DEVOS_TEST_MODE === "1";
}

export function assertTestMode(): void {
  if (!isTestMode()) throw new Error("This operation is restricted to DEVOS_TEST_MODE=1.");
}

export function assertLoopbackUrl(raw: string): URL {
  const url = new URL(raw);
  if (!LOOPBACK_HOSTS.has(url.hostname)) {
    throw new Error(`Test mode permits only loopback targets; rejected ${url.hostname}.`);
  }
  return url;
}

export function testApprovalToken(): string {
  assertTestMode();
  return "TEST_APPROVAL_ONLY";
}
