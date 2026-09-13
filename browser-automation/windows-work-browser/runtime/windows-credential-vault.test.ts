import test from "node:test";
import assert from "node:assert/strict";
import { WindowsCredentialVault } from "./windows-credential-vault";

test("Windows vault fails closed off Windows", async () => {
  const vault = new WindowsCredentialVault();
  if (process.platform !== "win32") {
    await assert.rejects(
      () => vault.save("test", "https://example.com", "synthetic-secret"),
      /requires Windows/i,
    );
  }
});

test("vault use never returns plaintext secret", async () => {
  const vault = new WindowsCredentialVault();
  if (process.platform !== "win32") return;
  await vault.save("test", "https://example.com", "synthetic-secret", "alice");
  const result = await vault.use({ credentialId: "test", origin: "https://example.com", purpose: "login" });
  assert.equal(result.ok, true);
  assert.equal("secret" in result, false);
  assert.match(result.sessionRef ?? "", /^cred-session-/);
  assert.ok(vault.getProtectedBlobForNativeBridge("test"));
  assert.equal(vault.getProtectedBlobForNativeBridge("missing"), undefined);
});
